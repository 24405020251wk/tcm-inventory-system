"""公网部署辅助中间件。

本地开发用 127.0.0.1，公网部署时域名是平台随机分配的，无法提前写进
CSRF_TRUSTED_ORIGINS。这里在开启 DYNAMIC_CSRF_ORIGINS 时，把当前请求的
来源域名动态补进白名单，避免登录/提交表单被 CSRF 拦成 403。
"""

from urllib.parse import urlsplit

from django.conf import settings


class DynamicCSRFTrustedOriginsMiddleware:
    """把请求实际来源域名加入 CSRF 信任列表（仅部署环境启用）。"""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if getattr(settings, "DYNAMIC_CSRF_ORIGINS", False):
            origin = self._origin_of(request)
            if origin and origin not in settings.CSRF_TRUSTED_ORIGINS:
                settings.CSRF_TRUSTED_ORIGINS.append(origin)
        return self.get_response(request)

    @staticmethod
    def _origin_of(request):
        origin = request.META.get("HTTP_ORIGIN")
        if origin:
            return origin.rstrip("/")
        referer = request.META.get("HTTP_REFERER")
        if referer:
            parts = urlsplit(referer)
            if parts.scheme and parts.netloc:
                return f"{parts.scheme}://{parts.netloc}"
        return ""
