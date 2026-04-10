import contextvars
import logging
import uuid

_request_id_ctx = contextvars.ContextVar("request_id", default="-")


class RequestIDMiddleware:
    """Attach a per-request ID to request object and logging context."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        token = _request_id_ctx.set(request_id)
        request.request_id = request_id
        try:
            response = self.get_response(request)
        finally:
            _request_id_ctx.reset(token)

        response["X-Request-ID"] = request_id
        return response


class RequestIDLogFilter(logging.Filter):
    """Inject request_id into log records to trace API requests."""

    def filter(self, record):
        record.request_id = _request_id_ctx.get()
        return True
