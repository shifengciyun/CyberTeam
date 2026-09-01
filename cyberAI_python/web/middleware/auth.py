"""
认证中间件 — 对受保护路由自动校验 JWT Token。

白名单路径无需认证（登录/注册/静态资源/docs）。
从 Authorization: Bearer <token> 头提取并验证。
"""
import logging
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from security.token import TokenManager

logger = logging.getLogger(__name__)

# 不需要认证的路径前缀
WHITELIST_PREFIXES = (
    "/api/auth/login",
    "/api/auth/register",
    "/docs",
    "/openapi.json",
    "/static",
    "/favicon.ico",
)


class AuthMiddleware(BaseHTTPMiddleware):
    """
    请求级认证中间件。

    原理:
    1. 检查路径是否在白名单中 → 是则放行
    2. 从 Authorization 头提取 Bearer token
    3. 用 TokenManager.verify_token() 校验签名+过期
    4. 校验通过 → 将用户信息注入 request.state.user → 放行
    5. 校验失败 → 返回 401

    注意: 本中间件提供"全局兜底"认证。各 router 也可以用
    Depends(HTTPBearer()) 做更细粒度的认证（两者不冲突）。
    """

    def __init__(self, app, token_manager: TokenManager = None):
        super().__init__(app)
        self.token_manager = token_manager

    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        # 白名单路径放行
        if any(path.startswith(prefix) for prefix in WHITELIST_PREFIXES):
            return await call_next(request)

        # 静态文件放行
        if path.startswith("/static") or path.endswith((".css", ".js", ".ico", ".png")):
            return await call_next(request)

        # 提取 token
        auth_header = request.headers.get("authorization", "")
        if not auth_header.startswith("Bearer "):
            # 没有 token → 交给 router 层处理（router 有自己的 Depends 校验）
            return await call_next(request)

        token = auth_header[7:]  # 去掉 "Bearer "

        # 校验 token
        if self.token_manager:
            payload = self.token_manager.verify_token(token)
            if payload is None:
                return JSONResponse(
                    status_code=401,
                    content={"detail": "Token 无效或已过期"},
                )
            # 将用户信息注入 request.state，后续 router 可以直接用
            request.state.user = payload
        else:
            logger.warning("AuthMiddleware: token_manager 未配置，跳过校验")

        return await call_next(request)
