from django.contrib import messages
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from core.permissions import menu_required
from core.utils import log_action, paginate

from .forms import LoginForm, MenuForm, RegisterForm, RoleForm, UserForm
from .models import Menu, Role, User


# ----------------------------- 认证 -----------------------------
def login_view(request):
    if request.user.is_authenticated:
        return redirect("core:dashboard")
    form = LoginForm(request, data=request.POST or None)
    if request.method == "POST":
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            log_action(request, "auth", "登录系统", target=user.username)
            messages.success(request, f"欢迎回来，{user.display_name}！")
            return redirect(request.GET.get("next") or "core:dashboard")
        messages.error(request, "账号或密码错误，或账号已被停用")
    return render(request, "accounts/login.html", {"form": form})


def logout_view(request):
    if request.user.is_authenticated:
        log_action(request, "auth", "退出系统", target=request.user.username)
        logout(request)
    messages.info(request, "已安全退出")
    return redirect("accounts:login")


def register_view(request):
    if request.user.is_authenticated:
        return redirect("core:dashboard")
    form = RegisterForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save(commit=False)
        user.role = Role.objects.filter(code="staff", is_active=True).first()
        user.save()
        log_action(request, "auth", "注册账号", target=user.username,
                   detail=f"角色：{user.role_name}")
        messages.success(request, "注册成功，请使用新账号登录")
        return redirect("accounts:login")
    return render(request, "accounts/register.html", {"form": form})


# ----------------------------- 用户管理 -----------------------------
@menu_required("system.user")
def user_list(request):
    keyword = request.GET.get("q", "").strip()
    role_id = request.GET.get("role", "")
    users = User.objects.select_related("role").all()
    if keyword:
        users = users.filter(
            Q(username__icontains=keyword)
            | Q(real_name__icontains=keyword)
            | Q(phone__icontains=keyword)
        )
    if role_id:
        users = users.filter(role_id=role_id)
    page_obj, querystring = paginate(request, users, 10)
    return render(request, "accounts/user_list.html", {
        "page_obj": page_obj,
        "querystring": querystring,
        "keyword": keyword,
        "role_id": role_id,
        "roles": Role.objects.all(),
        "total": users.count(),
    })


@menu_required("system.user")
def user_form(request, pk=None):
    instance = get_object_or_404(User, pk=pk) if pk else None
    form = UserForm(request.POST or None, instance=instance)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        action = "编辑用户" if instance else "新增用户"
        log_action(request, "user", action, target=user.username,
                   detail=f"角色：{user.role_name}，状态：{'启用' if user.is_active else '停用'}")
        messages.success(request, f"{action}成功")
        return redirect("accounts:user_list")
    return render(request, "accounts/user_form.html", {"form": form, "instance": instance})


@menu_required("system.user")
@require_POST
def user_toggle(request, pk):
    user = get_object_or_404(User, pk=pk)
    if user == request.user:
        messages.error(request, "不能停用当前登录账号")
        return redirect("accounts:user_list")
    if user.is_superuser:
        messages.error(request, "不能停用超级管理员")
        return redirect("accounts:user_list")
    user.is_active = not user.is_active
    user.save(update_fields=["is_active"])
    log_action(request, "user", "启用账号" if user.is_active else "停用账号", target=user.username)
    messages.success(request, f"账号 {user.username} 已{'启用' if user.is_active else '停用'}")
    return redirect("accounts:user_list")


@menu_required("system.user")
@require_POST
def user_reset_password(request, pk):
    user = get_object_or_404(User, pk=pk)
    user.set_password("Tcm@123456")
    user.save(update_fields=["password"])
    log_action(request, "user", "重置密码", target=user.username)
    messages.success(request, f"已将 {user.username} 的密码重置为 Tcm@123456")
    return redirect("accounts:user_list")


# ----------------------------- 角色管理 -----------------------------
@menu_required("system.role")
def role_list(request):
    roles = Role.objects.prefetch_related("menus", "users").all()
    return render(request, "accounts/role_list.html", {"roles": roles})


@menu_required("system.role")
def role_form(request, pk=None):
    instance = get_object_or_404(Role, pk=pk) if pk else None
    form = RoleForm(request.POST or None, instance=instance)
    if request.method == "POST" and form.is_valid():
        role = form.save()
        log_action(request, "role", "编辑角色" if instance else "新增角色", target=role.name,
                   detail="菜单：" + "、".join(role.menus.values_list("name", flat=True)))
        messages.success(request, "角色权限保存成功")
        return redirect("accounts:role_list")

    if request.method == "POST":
        selected_ids = set(int(i) for i in request.POST.getlist("menus") if i.isdigit())
    elif instance:
        selected_ids = set(instance.menus.values_list("id", flat=True))
    else:
        selected_ids = set()

    menus_by_group = {}
    for menu in Menu.objects.filter(is_active=True).order_by("group_name", "sort"):
        menus_by_group.setdefault(menu.group_name, []).append(menu)

    return render(request, "accounts/role_form.html", {
        "form": form,
        "instance": instance,
        "selected_ids": selected_ids,
        "menus_by_group": menus_by_group,
    })


@menu_required("system.role")
@require_POST
def role_delete(request, pk):
    role = get_object_or_404(Role, pk=pk)
    if role.users.exists():
        messages.error(request, "该角色下还有用户，无法删除")
        return redirect("accounts:role_list")
    name = role.name
    role.delete()
    log_action(request, "role", "删除角色", target=name)
    messages.success(request, f"角色「{name}」已删除")
    return redirect("accounts:role_list")


# ----------------------------- 菜单管理 -----------------------------
@menu_required("system.menu")
def menu_list(request):
    menus = Menu.objects.all().order_by("group_name", "sort")
    return render(request, "accounts/menu_list.html", {"menus": menus})


@menu_required("system.menu")
def menu_form(request, pk=None):
    instance = get_object_or_404(Menu, pk=pk) if pk else None
    form = MenuForm(request.POST or None, instance=instance)
    if request.method == "POST" and form.is_valid():
        menu = form.save()
        log_action(request, "role", "编辑菜单" if instance else "新增菜单", target=menu.name)
        messages.success(request, "菜单保存成功")
        return redirect("accounts:menu_list")
    return render(request, "accounts/menu_form.html", {"form": form, "instance": instance})


# ----------------------------- 个人中心 -----------------------------
@login_required
def profile(request):
    form = PasswordChangeForm(request.user, request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        update_session_auth_hash(request, user)
        log_action(request, "user", "修改密码", target=user.username)
        messages.success(request, "密码修改成功")
        return redirect("accounts:profile")
    return render(request, "accounts/profile.html", {"form": form})
