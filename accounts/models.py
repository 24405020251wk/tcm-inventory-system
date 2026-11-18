from django.contrib.auth.models import AbstractUser
from django.db import models
from django.urls import NoReverseMatch, reverse


class Menu(models.Model):
    """功能菜单，同时作为接口权限的载体（接口权限用 api_scope 标识）。"""

    GROUP_CHOICES = [
        ("工作台", "工作台"),
        ("业务管理", "业务管理"),
        ("库存管理", "库存管理"),
        ("系统管理", "系统管理"),
    ]

    code = models.CharField("权限编码", max_length=50, unique=True,
                            help_text="如 herb.list，用于视图权限校验")
    name = models.CharField("菜单名称", max_length=50)
    group_name = models.CharField("所属分组", max_length=20, choices=GROUP_CHOICES,
                                  default="业务管理")
    url_name = models.CharField("路由名称", max_length=80, blank=True,
                                help_text="Django URL name，如 herbs:list")
    icon = models.CharField("图标", max_length=40, default="bi-circle")
    api_scope = models.CharField("接口权限标识", max_length=120, blank=True,
                                 help_text="如 GET:/herbs/、POST:/herbs/create/")
    sort = models.IntegerField("排序", default=10)
    is_active = models.BooleanField("启用", default=True)
    created_at = models.DateTimeField("创建时间", auto_now_add=True)

    class Meta:
        verbose_name = "菜单权限"
        verbose_name_plural = "菜单权限"
        ordering = ["group_name", "sort", "id"]

    def __str__(self):
        return f"{self.name}（{self.code}）"

    @property
    def url(self):
        if not self.url_name:
            return ""
        try:
            return reverse(self.url_name)
        except NoReverseMatch:
            return ""


class Role(models.Model):
    """角色：菜单权限的集合。"""

    name = models.CharField("角色名称", max_length=50, unique=True)
    code = models.CharField("角色编码", max_length=50, unique=True)
    description = models.CharField("角色说明", max_length=200, blank=True)
    is_active = models.BooleanField("启用", default=True)
    menus = models.ManyToManyField(Menu, through="RoleMenu", related_name="roles",
                                   verbose_name="菜单权限", blank=True)
    created_at = models.DateTimeField("创建时间", auto_now_add=True)

    class Meta:
        verbose_name = "角色"
        verbose_name_plural = "角色"
        ordering = ["id"]

    def __str__(self):
        return self.name


class RoleMenu(models.Model):
    """角色-菜单关联表。"""

    role = models.ForeignKey(Role, on_delete=models.CASCADE, verbose_name="角色",
                             related_name="role_menus")
    menu = models.ForeignKey(Menu, on_delete=models.CASCADE, verbose_name="菜单",
                             related_name="role_menus")
    created_at = models.DateTimeField("授权时间", auto_now_add=True)

    class Meta:
        verbose_name = "角色菜单授权"
        verbose_name_plural = "角色菜单授权"
        unique_together = ("role", "menu")

    def __str__(self):
        return f"{self.role.name} - {self.menu.name}"


class User(AbstractUser):
    """自定义用户：在 Django 内置用户基础上扩展角色与联系方式。"""

    real_name = models.CharField("姓名", max_length=50, blank=True)
    phone = models.CharField("手机号", max_length=20, blank=True)
    department = models.CharField("所属部门", max_length=50, blank=True)
    role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True, blank=True,
                             verbose_name="角色", related_name="users")

    class Meta:
        verbose_name = "用户"
        verbose_name_plural = "用户"
        ordering = ["-date_joined"]

    def __str__(self):
        return self.real_name or self.username

    @property
    def display_name(self):
        return self.real_name or self.username

    @property
    def role_name(self):
        if self.is_superuser:
            return "超级管理员"
        return self.role.name if self.role else "未分配"

    def save(self, *args, **kwargs):
        if not self.real_name:
            self.real_name = self.username
        super().save(*args, **kwargs)
