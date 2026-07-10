import time
from uuid import uuid4

from fastapi import Request
from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response


class RequestProcessingTimeMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, header_name: str = "X-Process-Time"):
        super().__init__(app)
        self.header_name = header_name

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        start_time = time.perf_counter()

        request_id = request.headers.get("x-request-id") or uuid4().hex
        user_ip = (request.headers.get("x-forwarded-for") or request.client.host).split(",")[0]
        idempotency_key = request.headers.get("Idempotency-Key")

        with logger.contextualize(request_id=request_id, user_ip=user_ip):
            url = f"{request.url.path}{f'?{request.url.query}' if request.url.query else ''}"
            logger.info(f"BEGIN: {request.method} {url}")

            request.state.request_id = request_id
            request.state.idempotency_key = idempotency_key

            response = await call_next(request)

            duration_ms = (time.perf_counter() - start_time) * 1000
            duration_str = "{0:.2f}".format(duration_ms)
            logger.info(
                f"END: {request.method} {url}, completed_in={duration_str} ms, status_code= {response.status_code}"
            )

            # Добавляем время обработки в заголовок ответа
            response.headers[self.header_name] = duration_str

            return response
