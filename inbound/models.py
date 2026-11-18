from datetime import date, timedelta
from decimal import Decimal

from django.conf import settings
from django.db import models, transaction
from django.db.models import Sum
from django.utils import timezone

from herbs.models import Herb


class Batch(models.Model):
    """批次：库存的最小追溯单元，出库按批次先进先出/近效期先出。"""

    STATUS_CHOICES = [
        ("active", "在库"),
        ("exhausted", "已用完"),
        ("expired", "已过期"),
    ]

    batch_no = models.CharField("批次号", max_length=50, unique=True)
    herb = models.ForeignKey(Herb, on_delete=models.PROTECT, verbose_name="药材",
                             related_name="batches")
    production_date = models.DateField("生产日期", null=True, blank=True)
    expiry_date = models.DateField("有效期至", null=True, blank=True)
    quantity = models.DecimalField("入库数量", max_digits=12, decimal_places=2,
                                   default=Decimal("0"))
    remaining_quantity = models.DecimalField("剩余数量", max_digits=12, decimal_places=2,
                                             default=Decimal("0"))
    unit_price = models.DecimalField("入库单价（元）", max_digits=12, decimal_places=2,
                                     default=Decimal("0"))
    supplier = models.CharField("供应商", max_length=80, blank=True)
    status = models.CharField("批次状态", max_length=10, choices=STATUS_CHOICES,
                              default="active")
    created_at = models.DateTimeField("入库时间", auto_now_add=True)

    class Meta:
        verbose_name = "库存批次"
        verbose_name_plural = "库存批次"
        ordering = ["expiry_date", "id"]
        indexes = [models.Index(fields=["herb", "status"])]

    def __str__(self):
        return self.batch_no

    @property
    def amount(self):
        return self.quantity * self.unit_price

    @property
    def is_near_expiry(self):
        if not self.expiry_date:
            return False
        return self.expiry_date <= date.today() + timedelta(days=90)

    @property
    def is_expired(self):
        return bool(self.expiry_date and self.expiry_date < date.today())


class InboundOrder(models.Model):
    """入库单（学生 3）。"""

    STATUS_CHOICES = [
        ("draft", "草稿"),
        ("confirmed", "已入库"),
        ("cancelled", "已作废"),
    ]

    order_no = models.CharField("入库单号", max_length=40, unique=True)
    supplier = models.CharField("供应商", max_length=80)
    inbound_date = models.DateField("入库日期")
    operator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
                                 verbose_name="经办人", related_name="inbound_orders")
    status = models.CharField("状态", max_length=10, choices=STATUS_CHOICES, default="draft")
    remark = models.CharField("备注", max_length=200, blank=True)
    created_at = models.DateTimeField("创建时间", auto_now_add=True)
    confirmed_at = models.DateTimeField("确认时间", null=True, blank=True)

    class Meta:
        verbose_name = "入库单"
        verbose_name_plural = "入库单"
        ordering = ["-created_at"]

    def __str__(self):
        return self.order_no

    @property
    def total_quantity(self):
        return self.items.aggregate(t=Sum("quantity"))["t"] or Decimal("0")

    @property
    def total_amount(self):
        return sum((item.amount for item in self.items.all()), Decimal("0"))

    @property
    def status_class(self):
        return {"draft": "secondary", "confirmed": "success", "cancelled": "danger"}.get(
            self.status, "secondary"
        )

    @transaction.atomic
    def confirm(self, user=None):
        """确认入库：生成批次并写入库存流水，保证业务与库存一致。"""
        from inventory.models import StockLedger

        if self.status != "draft":
            raise ValueError("只有草稿状态的入库单可以确认")
        if not self.items.exists():
            raise ValueError("入库单没有明细，无法确认")

        for item in self.items.select_related("herb"):
            batch = Batch.objects.create(
                batch_no=item.batch_no,
                herb=item.herb,
                production_date=item.production_date,
                expiry_date=item.expiry_date,
                quantity=item.quantity,
                remaining_quantity=item.quantity,
                unit_price=item.unit_price,
                supplier=self.supplier,
            )
            item.batch = batch
            item.save(update_fields=["batch"])
            StockLedger.objects.create(
                herb=item.herb,
                batch=batch,
                biz_type="in",
                change_qty=item.quantity,
                before_qty=item.herb.total_stock - item.quantity,
                after_qty=item.herb.total_stock,
                ref_no=self.order_no,
                operator=user or self.operator,
                remark="入库确认",
            )
        self.status = "confirmed"
        self.confirmed_at = timezone.now()
        self.save(update_fields=["status", "confirmed_at"])


class InboundItem(models.Model):
    """入库明细。"""

    order = models.ForeignKey(InboundOrder, on_delete=models.CASCADE, verbose_name="入库单",
                              related_name="items")
    herb = models.ForeignKey(Herb, on_delete=models.PROTECT, verbose_name="药材",
                             related_name="inbound_items")
    batch_no = models.CharField("批次号", max_length=50, blank=True)
    production_date = models.DateField("生产日期", null=True, blank=True)
    expiry_date = models.DateField("有效期至", null=True, blank=True)
    quantity = models.DecimalField("入库数量", max_digits=12, decimal_places=2)
    unit_price = models.DecimalField("单价（元）", max_digits=12, decimal_places=2,
                                     default=Decimal("0"))
    batch = models.ForeignKey(Batch, on_delete=models.SET_NULL, null=True, blank=True,
                              verbose_name="关联批次", related_name="inbound_items")

    class Meta:
        verbose_name = "入库明细"
        verbose_name_plural = "入库明细"
        ordering = ["id"]

    def __str__(self):
        return f"{self.order.order_no} - {self.herb.name}"

    @property
    def amount(self):
        return self.quantity * self.unit_price
