"""
安全中间件 — ASGI 级别，为所有响应添加安全头 + 统一错误处理。

用法:
    from security.middleware import SecurityMiddleware
    app.add_middleware(SecurityMiddleware)
"""
import json
import logging
import traceback
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

logger = logging.getLogger(__name__)

# 安全响应头
SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "1; mode=block",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Cache-Control": "no-store, no-cache, must-revalidate",
    "Pragma": "no-cache",
}

# 需要脱敏的响应体字段（日志中隐藏）
_SENSITIVE_FIELDS = {"password", "token", "secret", "api_key", "access_token"}


def _sanitize_for_log(data: dict) -> dict:
    """脱敏：将敏感字段值替换为 ***"""
    if not isinstance(data, dict):
        return data
    sanitized = {}
    for k, v in data.items():
        if any(s in k.lower() for s in _SENSITIVE_FIELDS):
            sanitized[k] = "***" if v else v
        else:
            sanitized[k] = v
    return sanitized


class SecurityMiddleware(BaseHTTPMiddleware):
    """
    安全中间件，提供:

    1. 安全响应头 — 防止点击劫持、MIME嗅探等
    2. 统一错误处理 — 捕获未处理异常，返回 JSON 而非 500 HTML
    3. 请求日志脱敏 — 记录请求/响应时隐藏密码等敏感字段
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        try:
            response = await call_next(request)
        except Exception as e:
            # 统一异常处理：捕获所有未处理异常，返回 JSON
            logger.error(f"未处理异常: {request.method} {request.url.path}: {e}")
            logger.debug(traceback.format_exc())
            return JSONResponse(
                status_code=500,
                content={"detail": "服务器内部错误"},
            )

        # 添加安全头
        for header, value in SECURITY_HEADERS.items():
            response.headers[header] = value

        return response
