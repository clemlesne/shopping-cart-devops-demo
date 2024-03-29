from .models.exception import ExceptionModel, ExceptionDetailModel
from fastapi import Request, Response
from fastapi.encoders import jsonable_encoder
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from google.rpc import code_pb2
from opencensus.trace.attributes_helper import COMMON_ATTRIBUTES
from opencensus.trace.span import SpanKind
from opencensus.trace.status import Status
import logging
import traceback
from dotenv import load_dotenv


load_dotenv()

HTTP_CLIENT_PROTOCOL = COMMON_ATTRIBUTES["HTTP_CLIENT_PROTOCOL"]
HTTP_HOST = COMMON_ATTRIBUTES["HTTP_HOST"]
HTTP_METHOD = COMMON_ATTRIBUTES["HTTP_METHOD"]
HTTP_PATH = COMMON_ATTRIBUTES["HTTP_PATH"]
HTTP_REQUEST_SIZE = COMMON_ATTRIBUTES["HTTP_REQUEST_SIZE"]
HTTP_STATUS_CODE = COMMON_ATTRIBUTES["HTTP_STATUS_CODE"]
HTTP_URL = COMMON_ATTRIBUTES["HTTP_URL"]
HTTP_USER_AGENT = COMMON_ATTRIBUTES["HTTP_USER_AGENT"]

logger = logging.getLogger(__name__)


async def handle_exception(req: Request, exc: Exception, detailed=False) -> Response:
    http_code = exc.status_code if hasattr(exc, "status_code") else 500
    status_code = proto_error_code_from_http(http_code)
    status_details = (
        str(jsonable_encoder(exc.errors()))
        if hasattr(exc, "errors")
        else exc.detail
        if hasattr(exc, "detail")
        else traceback.format_exc()
    )
    exception_id = None
    class_name = type(exc).__name__
    status_message = str(exc)

    logger.exception(exc)

    if req.app.tracer:
        with req.app.tracer.span("exception") as span:
            exception_id = span.span_id

            span.status = Status(
                code=status_code,
                details=status_details,
                message=status_message,
            )

    model = ExceptionModel(
        exception=ExceptionDetailModel(
            code=http_code,
            details=status_details if detailed else None,
            id=exception_id,
            message=status_message,
            type=class_name,
        ),
    )

    return JSONResponse(
        content=jsonable_encoder(model),
        headers=exc.headers if hasattr(exc, "headers") else None,
        status_code=http_code,
    )


async def setup_trace_context(req: Request, next) -> Response:
    with req.app.tracer.span("main") as span:
        span.span_kind = SpanKind.SERVER

        req.app.tracer.add_attribute_to_current_span(
            attribute_key=HTTP_CLIENT_PROTOCOL, attribute_value=req.url.scheme
        )
        if hasattr(req.client, "host"):
            req.app.tracer.add_attribute_to_current_span(
                attribute_key=HTTP_HOST, attribute_value=req.client.host
            )
        req.app.tracer.add_attribute_to_current_span(
            attribute_key=HTTP_METHOD, attribute_value=req.method
        )
        req.app.tracer.add_attribute_to_current_span(
            attribute_key=HTTP_PATH, attribute_value=req.url.path
        )
        req.app.tracer.add_attribute_to_current_span(
            attribute_key=HTTP_URL, attribute_value=str(req.url)
        )
        if "content-length" in req.headers:
            req.app.tracer.add_attribute_to_current_span(
                attribute_key=HTTP_REQUEST_SIZE,
                attribute_value=req.headers["content-length"],
            )
        if "user-agent" in req.headers:
            req.app.tracer.add_attribute_to_current_span(
                attribute_key=HTTP_USER_AGENT,
                attribute_value=req.headers["user-agent"],
            )

        res = await next(req)
        http_code = res.status_code

        req.app.tracer.add_attribute_to_current_span(
            attribute_key=HTTP_STATUS_CODE, attribute_value=http_code
        )

        status = Status(code=proto_error_code_from_http(http_code))
        span.status = status

        return res


"""
See: https://opencensus.io/tracing/span/status/#2
See: https://github.com/encode/starlette/blob/ea70fd57b286824350da88c6d484c32bdf31627a/starlette/status.py
"""


def proto_error_code_from_http(status: int) -> int:
    if status >= 200 or status < 300:
        return code_pb2.OK
    if status == 400:
        return code_pb2.INVALID_ARGUMENT
    if status == 401:
        return code_pb2.UNAUTHENTICATED
    if status == 403:
        return code_pb2.PERMISSION_DENIED
    if status == 404:
        return code_pb2.NOT_FOUND
    if status == 409:
        return code_pb2.ALREADY_EXISTS
    if status == 429:
        return code_pb2.RESOURCE_EXHAUSTED
    if status == 499:
        return code_pb2.CANCELLED
    if status == 500:
        return code_pb2.INTERNAL
    if status == 501:
        return code_pb2.UNIMPLEMENTED
    if status == 503:
        return code_pb2.UNAVAILABLE
    if status == 504:
        return code_pb2.DEADLINE_EXCEEDED
    return code_pb2.UNKNOWN
