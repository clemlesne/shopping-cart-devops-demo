from . import utils
from .models.cart import CartModel, CartPaginateModel
from .models.readiness import ReadinessModel, ReadinessCheckModel, Status
from azure.cosmos import CosmosClient
from azure.cosmos.exceptions import CosmosResourceNotFoundError
from azure.identity import DefaultAzureCredential
from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.exceptions import RequestValidationError
from opencensus.ext.azure.log_exporter import AzureLogHandler
from opencensus.ext.azure.trace_exporter import AzureExporter
from opencensus.trace import config_integration
from opencensus.trace.samplers import AlwaysOnSampler
from opencensus.trace.tracer import Tracer
from pydantic.error_wrappers import ValidationError
from redis import Redis
from starlette.exceptions import HTTPException as StarletteHTTPException
from typing import List, Optional
from uuid import UUID, uuid4
import logging
import os


APP_VERSION = os.getenv("APP_VERSION")
REDIS_HOST = os.getenv("REDIS_HOST")
REDIS_PORT = os.getenv("REDIS_PORT")
REDIS_USERNAME = os.getenv("REDIS_USERNAME")
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")
REDIS_DB = os.getenv("REDIS_DB")
APPLICATIONINSIGHTS_CONNECTION_STRING = os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING")
COSMOS_DB_URI = os.getenv("COSMOS_DB_URI")
COSMOS_DB_CONTAINER = "cart"

# Init logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
try:
    logging.getLogger().addHandler(AzureLogHandler(connection_string=APPLICATIONINSIGHTS_CONNECTION_STRING))
    azure_log_handler = True
except Exception as exc:
    logger.exception(exc)
    azure_log_handler = False

# Init FastAPI
api = FastAPI(title="cart", version=APP_VERSION)

# Init tracing
try:
    config_integration.trace_integrations(["logging", "threading"])
    api.tracer = Tracer(exporter=AzureExporter(connection_string=APPLICATIONINSIGHTS_CONNECTION_STRING), sampler=AlwaysOnSampler())
except Exception as exc:
    logger.exception(exc)
    api.tracer = None

# Cosmos DB
try:
    az_credentials = DefaultAzureCredential()
    dbclient = CosmosClient(COSMOS_DB_URI, credential=az_credentials, consistency_level="Session").get_database_client("shopping-cart-devops-demo").get_container_client(COSMOS_DB_CONTAINER)
except Exception as exc:
    logger.exception(exc)
    dbclient = None

# Redis DB
try:
    cacheclient = Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, username=REDIS_USERNAME, password=REDIS_PASSWORD, ssl=True, decode_responses=True)
except Exception as exc:
    logger.exception(exc)
    cacheclient = None


@api.middleware("http")
async def trace_context(req: Request, next) -> Response:
    return await utils.setup_trace_context(req, next)


@api.exception_handler(RequestValidationError)
@api.exception_handler(StarletteHTTPException)
async def validation_exception_handler(req, exc):
    return await utils.handle_exception(req, exc, detailed=True)


@api.exception_handler(Exception)
async def validation_exception_handler(req, exc):
    return await utils.handle_exception(req, exc)


@api.get("/health/liveness", status_code=204)
async def health_liveness_get() -> None:
    return None


@api.get("/health/readiness")
async def health_readiness_get():
    # Test the cache with a transaction (insert, read, delete)
    try:
        key = str(uuid4())
        value = "test"
        cacheclient.set(key, value)
        assert value == cacheclient.get(key)
        cacheclient.delete(key)
        assert None == cacheclient.get(key)
        cache_check = Status.OK
    except Exception as exc:
        logger.exception(exc)
        cache_check = Status.FAIL

    # Test database with a transaction (insert, read, delete)
    try:
        key = str(uuid4())
        document = { "id": key, "test": "test" }
        dbclient.upsert_item(document)
        assert "test" == dbclient.read_item(item=key, partition_key=key)["test"]
        dbclient.delete_item(item=key, partition_key=key)
        try:
            dbclient.read_item(item=key, partition_key=key)
        except CosmosResourceNotFoundError:
            database_check = Status.OK
    except Exception as exc:
        logger.exception(exc)
        database_check = Status.FAIL

    monitoring_logger_check = Status.FAIL if not azure_log_handler else Status.OK
    monitoring_logger_tracer = Status.FAIL if not api.tracer else Status.OK

    model = ReadinessModel(
        status = Status.OK,
        checks = [
            ReadinessCheckModel(
                id = "startup",
                status = Status.OK,
            ),
            ReadinessCheckModel(
                id = "database",
                status = database_check
            ),
            ReadinessCheckModel(
                id = "cache",
                status = cache_check
            ),
            ReadinessCheckModel(
                id = "monitoring-logger",
                status = monitoring_logger_check
            ),
            ReadinessCheckModel(
                id = "monitoring-tracer",
                status = monitoring_logger_tracer
            ),
        ],
    )

    for check in model.checks:
        if check.status != Status.OK:
            model.status = Status.FAIL
            break

    return model


@api.get("/")
async def cart_get_all(next: Optional[str] = None) -> CartPaginateModel:
    cache_prefix = "all"

    try:
        res = cacheclient.get(f"{cache_prefix}-{next}")

        if res:
            logging.debug("Items found in the cache, using them")
            return CartPaginateModel.parse_raw(res)
    except Exception as exc:
        logger.exception(exc)

    res = dbclient.query_items(
        query=f"SELECT * FROM {COSMOS_DB_CONTAINER} c WHERE c.id > @next ORDER BY c.id OFFSET 0 LIMIT 100",
        parameters=[
            {
                "name": "@next",
                "value": next if next else "",
            }
        ],
        enable_cross_partition_query=True,
    )

    items = []
    for raw in list(res):
        try:
            items.append(CartModel.parse_obj(raw))
        except ValidationError:
            logger.debug("Corrupted item detected, ignoring it")

    model = CartPaginateModel(
        items = items,
        next = items[len(items) - 1].id if len(items) > 0 else None,
    )
    cacheclient.set(f"{cache_prefix}-{next}", model.json(), ex=5) # Expires in 5 seconds
    return model


@api.get("/{cart_id}")
async def cart_get_single(cart_id: UUID) -> CartModel:
    try:
        res = cacheclient.get(str(cart_id))

        if res:
            logging.debug("Item found in the cache, using it")
            return CartModel.parse_raw(res)
    except Exception as exc:
        logger.exception(exc)

    logging.debug("Item not stored in cache, sourcing it from the database")

    try:
        res = dbclient.read_item(item=str(cart_id), partition_key=str(cart_id))
        model = CartModel.parse_obj(res)
        cacheclient.set(str(cart_id), model.json())
        return model
    except CosmosResourceNotFoundError:
        raise HTTPException(status_code=404, detail="Item not found")


@api.delete("/{cart_id}", status_code=204)
async def cart_delete_single(cart_id: UUID) -> None:
    try:
        dbclient.delete_item(item=str(cart_id), partition_key=str(cart_id))
    except CosmosResourceNotFoundError:
        raise HTTPException(status_code=404, detail="Item not found")

    try:
        cacheclient.delete(str(cart_id))
        logging.debug("Item deleted from cache")
    except Exception as exc:
        logger.exception(exc)

    return None


@api.post("/", status_code=201)
async def cart_post_single(item: CartModel) -> CartModel:
    item.id = str(uuid4())
    res = dbclient.upsert_item(item.dict())
    model = CartModel.parse_obj(res)

    try:
        res = cacheclient.set(str(model.id), model.json())
        logging.debug("Item stored in cache")
    except Exception as exc:
        logger.exception(exc)

    return model
