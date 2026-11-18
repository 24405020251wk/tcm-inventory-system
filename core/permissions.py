"""基于「角色 - 菜单」的访问控制。

设计说明（对应学生 1 的功能点 ②③）：
- 每个菜单项代表一个可访问的功能入口，code 形如 `herb.list`；
- 角色勾选菜单后，该角色下所有用户即获得对应权限；
- 超级管理员（superuser）默认拥有全部权限，便于教学演示与后台维护。
"""
from functools import wraps

from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied
from django.shortcuts import render


def menu_codes(user):
    """获取用户拥有的菜单编码集合。"""
    if not getattr(user, "is_authenticated", False):
        return set()
    if user.is_superuser:
        from accounts.models import Menu

        return set(Menu.objects.values_list("code", flat=True))
    role = getattr(user, "role", None)
    if not role:
        return set()
    return set(role.menus.values_list("code", flat=True))


def can(user, code: str) -> bool:
    if not getattr(user, "is_authenticated", False):
        return False
    if user.is_superuser:
        return True
    role = getattr(user, "role", None)
    return bool(role and role.menus.filter(code=code).exists())


def menu_required(code: str):
    """视图装饰器：校验菜单权限。"""

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect_to_login(request.get_full_path())
            if can(request.user, code):
                return view_func(request, *args, **kwargs)
            return render(
                request,
                "403.html",
                {"required_code": code},
                status=403,
            )

        return _wrapped

    return decorator


def role_required(*role_codes):
    """按角色编码限制访问（用于审批等敏感操作）。"""

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect_to_login(request.get_full_path())
            role = getattr(request.user, "role", None)
            if request.user.is_superuser or (role and role.code in role_codes):
                return view_func(request, *args, **kwargs)
            raise PermissionDenied("当前角色无权执行该操作")

        return _wrapped

    return decorator
