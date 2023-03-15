from . import utils
from fastapi import FastAPI, Request, Response
from fastapi.exceptions import RequestValidationError
from opencensus.ext.azure.log_exporter import AzureLogHandler
from opencensus.extension.azure.functions import OpenCensusExtension
from opencensus.trace import config_integration
from starlette.exceptions import HTTPException as StarletteHTTPException
from uuid import uuid4, UUID
import azure.functions as func
import logging
import os


APP_VERSION = os.getenv("APP_VERSION")

# Init logging
logging.basicConfig(level=logging.INFO)
logging.getLogger().addHandler(AzureLogHandler())
logger = logging.getLogger(__name__)
# Init FastAPI
api = FastAPI(title="items", version=APP_VERSION)
bp = func.Blueprint().AsgiFunctionApp(app=api, http_auth_level=func.AuthLevel.ANONYMOUS)
# Init tracing
OpenCensusExtension.configure()  # Set up "api.tracer"
config_integration.trace_integrations(["logging"])


@api.middleware("http")
async def trace_context(req: Request, next) -> Response:
    return await utils.setup_trace_context(req, next)


@api.exception_handler(RequestValidationError)
@api.exception_handler(StarletteHTTPException)
async def validation_exception_handler(req, exc):
    return await utils.handle_exception(req, exc)


@api.middleware("http")
async def add_version_header(request: Request, call_next):
    response = await call_next(request)
    response.headers["x-app-version"] = APP_VERSION
    return response


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
