from fastapi import FastAPI
from fastapi import Request, Response
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from opencensus.trace.attributes_helper import COMMON_ATTRIBUTES
from opencensus.trace.span import SpanKind
import logging


ERROR_MESSAGE = COMMON_ATTRIBUTES["ERROR_MESSAGE"]
ERROR_NAME = COMMON_ATTRIBUTES["ERROR_NAME"]
HTTP_CLIENT_PROTOCOL = COMMON_ATTRIBUTES["HTTP_CLIENT_PROTOCOL"]
HTTP_HOST = COMMON_ATTRIBUTES["HTTP_HOST"]
HTTP_METHOD = COMMON_ATTRIBUTES["HTTP_METHOD"]
HTTP_PATH = COMMON_ATTRIBUTES["HTTP_PATH"]
HTTP_REQUEST_SIZE = COMMON_ATTRIBUTES["HTTP_REQUEST_SIZE"]
HTTP_STATUS_CODE = COMMON_ATTRIBUTES["HTTP_STATUS_CODE"]
HTTP_URL = COMMON_ATTRIBUTES["HTTP_URL"]
HTTP_USER_AGENT = COMMON_ATTRIBUTES["HTTP_USER_AGENT"]

logger = logging.getLogger(__name__)


async def setup_trace_context(req: Request, next, api: FastAPI) -> Response:
    with api.tracer.span("main") as span:
        span.span_kind = SpanKind.SERVER

        api.tracer.add_attribute_to_current_span(
            attribute_key=HTTP_CLIENT_PROTOCOL, attribute_value=req.url.scheme
        )
        if hasattr(req.client, "host"):
            api.tracer.add_attribute_to_current_span(
                attribute_key=HTTP_HOST, attribute_value=req.client.host
            )
        api.tracer.add_attribute_to_current_span(
            attribute_key=HTTP_METHOD, attribute_value=req.method
        )
        api.tracer.add_attribute_to_current_span(
            attribute_key=HTTP_PATH, attribute_value=req.url.path
        )
        api.tracer.add_attribute_to_current_span(
            attribute_key=HTTP_URL, attribute_value=str(req.url)
        )
        if "content-length" in req.headers:
            api.tracer.add_attribute_to_current_span(
                attribute_key=HTTP_REQUEST_SIZE,
                attribute_value=req.headers["content-length"],
            )
        if "user-agent" in req.headers:
            api.tracer.add_attribute_to_current_span(
                attribute_key=HTTP_USER_AGENT,
                attribute_value=req.headers["user-agent"],
            )

        try:
            res = await next(req)
        except Exception as exc:
            return await handle_json_exception(exc, api)

        api.tracer.add_attribute_to_current_span(
            attribute_key=HTTP_STATUS_CODE, attribute_value=res.status_code
        )

        return res


async def handle_json_exception(exc: Exception, api: FastAPI) -> Response:
    error_message = exc.errors() if hasattr(exc, "errors") else "Internal Server Error"
    error_name = exc.status_code if hasattr(exc, "status_code") else 500

    logger.exception(exc)

    api.tracer.add_attribute_to_current_span(
        attribute_key=ERROR_MESSAGE, attribute_value=error_message
    )
    api.tracer.add_attribute_to_current_span(
        attribute_key=ERROR_NAME, attribute_value=error_name
    )

    return JSONResponse(
        status_code=error_name,
        content=jsonable_encoder(
            {
                "exception": {
                    "code": error_name,
                    "detail": error_message,
                }
            }
        ),
    )
