from . import utils
from fastapi import FastAPI, Request, Response
from opencensus.ext.azure.log_exporter import AzureLogHandler
from opencensus.extension.azure.functions import OpenCensusExtension
from opencensus.trace import config_integration
from uuid import uuid4, UUID
import azure.functions as func
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
api = FastAPI(title="items", version=APP_VERSION)
# Init tracing
OpenCensusExtension.configure()
config_integration.trace_integrations(["logging"])


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


async def main(req: func.HttpRequest, context: func.Context) -> func.HttpResponse:
    api.tracer = context.tracer
    return await func.AsgiMiddleware(api).handle_async(req, context)
