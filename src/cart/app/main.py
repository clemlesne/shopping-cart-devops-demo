from . import utils
from fastapi import FastAPI, Request, Response
from opencensus.ext.azure.log_exporter import AzureLogHandler
from opencensus.ext.azure.trace_exporter import AzureExporter
from opencensus.trace import config_integration
from opencensus.trace.samplers import AlwaysOnSampler
from opencensus.trace.tracer import Tracer
from uuid import uuid4, UUID
import logging
import os


APP_VERSION = os.getenv("APP_VERSION")
APPLICATIONINSIGHTS_CONNECTION_STRING = os.getenv(
    "APPLICATIONINSIGHTS_CONNECTION_STRING"
)

# Init logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
# Init FastAPI
api = FastAPI(title="cart", version=APP_VERSION)
# Init tracing
config_integration.trace_integrations(["logging", "threading"])
api.tracer = Tracer(exporter=AzureExporter(), sampler=AlwaysOnSampler())


if not APPLICATIONINSIGHTS_CONNECTION_STRING:
    logger.warn(
        "Azure Application Insights disabled, no APPLICATIONINSIGHTS_CONNECTION_STRING env var defined"
    )

else:
    handler = AzureLogHandler()
    logging.getLogger().addHandler(handler)

    @api.middleware("http")
    async def trace_context(req: Request, next) -> Response:
        return await utils.setup_trace_context(req, next, api)


@api.get("/", status_code=501)
async def root_get():
    return None


@api.get("/health/liveness")
async def health_liveness_get():
    return None


@api.get("/health/readiness")
async def health_readiness_get():
    return {
        "status": "ok",
        "checks": [
            {
                "id": "server-startup",
                "status": "ok",
            },
        ],
    }


@api.get("/{cart_id}", status_code=200)
async def cart_get(cart_id: UUID):
    return {
        "id": cart_id,
        "items": [
            {
                "id": uuid4(),
                "quantity": 1,
            },
            {
                "id": uuid4(),
                "quantity": 2,
            },
        ],
    }
