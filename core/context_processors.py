"""模板全局上下文：侧边栏菜单、权限集合、系统信息。"""
from .permissions import menu_codes


def site_context(request):
    user = getattr(request, "user", None)
    if not getattr(user, "is_authenticated", False):
        return {"SITE_NAME": "中药材库存与批次管理系统"}

    codes = menu_codes(user)
    from accounts.models import Menu

    menus = (
        Menu.objects.filter(is_active=True, code__in=codes)
        .exclude(url_name="")
        .order_by("group_name", "sort", "id")
    )
    grouped = {}
    for menu in menus:
        grouped.setdefault(menu.group_name or "其他", []).append(menu)

    return {
        "SITE_NAME": "中药材库存与批次管理系统",
        "SITE_SHORT": "中药材库存管理",
        "menu_groups": grouped,
        "menu_codes": codes,
        "current_path": request.path,
    }
