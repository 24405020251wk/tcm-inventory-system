from django.conf import settings
from django.db import models

from herbs.models import Herb
from inbound.models import Batch


class StockLedger(models.Model):
    """库存流水：所有入库、出库、调整都会留痕，支撑可追溯闭环。"""

    BIZ_CHOICES = [
        ("in", "入库"),
        ("out", "出库"),
        ("adjust", "盘点调整"),
    ]

    herb = models.ForeignKey(Herb, on_delete=models.PROTECT, verbose_name="药材",
                             related_name="ledgers")
    batch = models.ForeignKey(Batch, on_delete=models.SET_NULL, null=True, blank=True,
                              verbose_name="批次", related_name="ledgers")
    biz_type = models.CharField("业务类型", max_length=10, choices=BIZ_CHOICES)
    change_qty = models.DecimalField("变动数量", max_digits=12, decimal_places=2,
                                     help_text="入库为正，出库为负")
    before_qty = models.DecimalField("变动前库存", max_digits=12, decimal_places=2, default=0)
    after_qty = models.DecimalField("变动后库存", max_digits=12, decimal_places=2, default=0)
    ref_no = models.CharField("关联单号", max_length=40, blank=True)
    operator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                 null=True, blank=True, verbose_name="操作人",
                                 related_name="stock_ledgers")
    remark = models.CharField("备注", max_length=200, blank=True)
    created_at = models.DateTimeField("发生时间", auto_now_add=True)

    class Meta:
        verbose_name = "库存流水"
        verbose_name_plural = "库存流水"
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["herb", "created_at"])]

    def __str__(self):
        return f"{self.get_biz_type_display()} {self.herb.name} {self.change_qty}"
