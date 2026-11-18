from django.conf import settings
from django.db import models


class OperationLog(models.Model):
    """系统操作日志：记录关键业务动作，便于追溯（学生 5 功能点 ③）。"""

    MODULE_CHOICES = [
        ("auth", "登录认证"),
        ("user", "用户管理"),
        ("role", "角色权限"),
        ("herb", "药材档案"),
        ("inbound", "入库管理"),
        ("outbound", "出库管理"),
        ("inventory", "库存管理"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="操作人",
        related_name="operation_logs",
    )
    username = models.CharField("操作人账号", max_length=150, blank=True)
    module = models.CharField("模块", max_length=20, choices=MODULE_CHOICES, default="inventory")
    action = models.CharField("操作", max_length=100)
    target = models.CharField("操作对象", max_length=150, blank=True)
    detail = models.TextField("详细说明", blank=True)
    ip = models.GenericIPAddressField("IP 地址", null=True, blank=True)
    created_at = models.DateTimeField("操作时间", auto_now_add=True)

    class Meta:
        verbose_name = "操作日志"
        verbose_name_plural = "操作日志"
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["module", "created_at"])]

    def __str__(self):
        return f"{self.username} {self.action} {self.target}"
