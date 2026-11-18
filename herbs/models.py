from decimal import Decimal

from django.db import models
from django.db.models import Sum
from django.urls import reverse


class HerbCategory(models.Model):
    """中药材分类，如 根茎类、花叶类、果实种子类。"""

    name = models.CharField("分类名称", max_length=50, unique=True)
    code = models.CharField("分类编码", max_length=30, unique=True)
    sort = models.IntegerField("排序", default=10)
    remark = models.CharField("备注", max_length=200, blank=True)

    class Meta:
        verbose_name = "药材分类"
        verbose_name_plural = "药材分类"
        ordering = ["sort", "id"]

    def __str__(self):
        return self.name


class Herb(models.Model):
    """中药材档案（学生 2 的核心数据表）。"""

    STATUS_CHOICES = [("active", "启用"), ("inactive", "停用")]

    code = models.CharField("药材编码", max_length=30, unique=True,
                            help_text="系统内唯一，如 YC-0001")
    name = models.CharField("药材名称", max_length=60)
    pinyin = models.CharField("拼音助记码", max_length=60, blank=True)
    category = models.ForeignKey(HerbCategory, on_delete=models.PROTECT,
                                 verbose_name="所属分类", related_name="herbs")
    spec = models.CharField("规格", max_length=60, blank=True,
                            help_text="如 统货 / 一级 / 切片")
    unit = models.CharField("计量单位", max_length=10, default="kg")
    origin = models.CharField("产地", max_length=60, blank=True)
    shelf_life_days = models.IntegerField("保质期（天）", default=730)
    storage_condition = models.CharField("贮藏条件", max_length=100, blank=True,
                                         default="阴凉干燥处")
    min_stock = models.DecimalField("库存下限", max_digits=12, decimal_places=2,
                                    default=Decimal("10"))
    price = models.DecimalField("参考单价（元）", max_digits=12, decimal_places=2,
                                default=Decimal("0"))
    status = models.CharField("状态", max_length=10, choices=STATUS_CHOICES, default="active")
    remark = models.CharField("备注", max_length=200, blank=True)
    created_at = models.DateTimeField("创建时间", auto_now_add=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        verbose_name = "中药材档案"
        verbose_name_plural = "中药材档案"
        ordering = ["code"]
        indexes = [models.Index(fields=["name"]), models.Index(fields=["pinyin"])]

    def __str__(self):
        return f"{self.name}（{self.code}）"

    @property
    def total_stock(self):
        result = self.batches.filter(status="active").aggregate(
            total=Sum("remaining_quantity")
        )
        return result["total"] or Decimal("0")

    @property
    def stock_value(self):
        return self.total_stock * self.price

    @property
    def stock_status(self):
        stock = self.total_stock
        if stock <= 0:
            return "缺货"
        if stock < self.min_stock:
            return "低库存"
        return "正常"

    @property
    def stock_status_class(self):
        return {"缺货": "danger", "低库存": "warning"}.get(self.stock_status, "success")

    def get_absolute_url(self):
        return reverse("herbs:detail", args=[self.pk])
