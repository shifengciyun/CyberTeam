"""
限流中间件 — 令牌桶算法，按 IP + 路径维度限流。

原理:
- 每个 (IP, path_prefix) 维护一个令牌桶
- 每秒补充 rate 个令牌，最多持有 capacity 个
- 请求消耗一个令牌，桶空则返回 429

用法: 在 app.py 中 app.add_middleware(RateLimitMiddleware, limit=60, window=60)
"""
import time
import logging
from collections import defaultdict
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)


class _TokenBucket:
    """单个令牌桶"""

    __slots__ = ("capacity", "rate", "tokens", "last_refill")

    def __init__(self, capacity: int, rate: float):
        self.capacity = capacity
        self.rate = rate            # 每秒补充的令牌数
        self.tokens = float(capacity)
        self.last_refill = time.monotonic()

    def consume(self, now: float = None) -> bool:
        """尝试消费一个令牌，返回是否成功"""
        now = now or time.monotonic()
        # 补充令牌
        elapsed = now - self.last_refill
        self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)
        self.last_refill = now

        if self.tokens >= 1.0:
            self.tokens -= 1.0
            return True
        return False

    @property
    def retry_after(self) -> float:
        """返回需要等待的秒数"""
        if self.tokens >= 1.0:
            return 0.0
        return max(0.1, (1.0 - self.tokens) / self.rate)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    令牌桶限流中间件。

    参数:
        limit: 窗口期内最大请求数（桶容量）
        window: 窗口期秒数（令牌补充速率 = limit / window）
        cleanup_interval: 多久清理一次过期桶（秒）

    维度: IP + 路径前两级（如 /api/chat → /api/chat）
    """

    def __init__(self, app, limit: int = 60, window: int = 60,
                 cleanup_interval: int = 300):
        super().__init__(app)
        self.limit = limit
        self.rate = limit / window  # 令牌/秒
        self.cleanup_interval = cleanup_interval
        self.buckets: dict[str, _TokenBucket] = defaultdict(
            lambda: _TokenBucket(limit, self.rate)
        )
        self._last_cleanup = time.monotonic()

    def _get_key(self, request: Request) -> str:
        """生成限流 key: IP + 路径前缀"""
        client_ip = request.client.host if request.client else "unknown"
        # 取路径前两级作为维度（/api/chat → /api/chat）
        parts = request.url.path.strip("/").split("/")
        prefix = "/".join(parts[:2]) if len(parts) >= 2 else request.url.path
        return f"{client_ip}:{prefix}"

    def _maybe_cleanup(self):
        """定期清理长时间未使用的桶，防止内存泄漏"""
        now = time.monotonic()
        if now - self._last_cleanup < self.cleanup_interval:
            return
        self._last_cleanup = now
        expired_keys = [
            key for key, bucket in self.buckets.items()
            if now - bucket.last_refill > self.cleanup_interval
        ]
        for key in expired_keys:
            del self.buckets[key]
        if expired_keys:
            logger.debug(f"清理了 {len(expired_keys)} 个过期限流桶")

    async def dispatch(self, request: Request, call_next):
        # 管理员/健康检查不限流
        path = request.url.path
        if path in ("/health", "/docs", "/openapi.json") or path.startswith("/static"):
            return await call_next(request)

        self._maybe_cleanup()

        key = self._get_key(request)
        bucket = self.buckets[key]

        if not bucket.consume():
            retry_after = int(bucket.retry_after) + 1
            logger.warning(f"限流触发: {key}, retry_after={retry_after}s")
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "请求过于频繁，请稍后再试",
                    "retry_after": retry_after,
                },
                headers={"Retry-After": str(retry_after)},
            )

        return await call_next(request)
