from decimal import Decimal
import os

from django.conf import settings
from django.db import models, transaction
from django.db.models import F, Sum

from herbs.models import Herb
from inbound.models import Batch


class OutboundOrder(models.Model):
    """领用出库单（学生 4）。状态流转：草稿 → 待审核 → 已出库 / 已驳回。"""

    STATUS_CHOICES = [
        ("draft", "草稿"),
        ("pending", "待审核"),
        ("approved", "已出库"),
        ("rejected", "已驳回"),
        ("cancelled", "已作废"),
    ]

    order_no = models.CharField("出库单号", max_length=40, unique=True)
    department = models.CharField("领用部门", max_length=60)
    purpose = models.CharField("领用用途", max_length=120, blank=True)
    applicant = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
                                  verbose_name="申请人", related_name="outbound_orders")
    apply_date = models.DateField("申请日期")
    status = models.CharField("状态", max_length=10, choices=STATUS_CHOICES, default="draft")
    approver = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                 null=True, blank=True, verbose_name="审核人",
                                 related_name="approved_orders")
    approve_time = models.DateTimeField("审核时间", null=True, blank=True)
    approve_remark = models.CharField("审核意见", max_length=200, blank=True)
    exception_note = models.TextField("异常备注", blank=True,
                                      help_text="记录破损、短缺、应急领用等异常情况")
    remark = models.CharField("备注", max_length=200, blank=True)
    created_at = models.DateTimeField("创建时间", auto_now_add=True)

    class Meta:
        verbose_name = "出库单"
        verbose_name_plural = "出库单"
        ordering = ["-created_at"]

    def __str__(self):
        return self.order_no

    @property
    def total_quantity(self):
        return self.items.aggregate(t=Sum("quantity"))["t"] or Decimal("0")

    @property
    def status_class(self):
        return {
            "draft": "secondary",
            "pending": "warning",
            "approved": "success",
            "rejected": "danger",
            "cancelled": "dark",
        }.get(self.status, "secondary")

    def submit(self):
        if self.status != "draft":
            raise ValueError("只有草稿可以提交审核")
        if not self.items.exists():
            raise ValueError("请先添加领用明细")
        self.status = "pending"
        self.save(update_fields=["status"])

    @transaction.atomic
    def approve(self, user, remark=""):
        """审核通过：按近效期优先扣减批次库存，并写库存流水。"""
        from django.utils import timezone

        from inventory.models import StockLedger

        if self.status != "pending":
            raise ValueError("只有待审核的单据可以审核")

        for item in self.items.select_related("herb"):
            herb = Herb.objects.select_for_update().get(pk=item.herb_id)
            stock = herb.total_stock
            if stock < item.quantity:
                raise ValueError(
                    f"【{herb.name}】库存不足，当前库存 {stock}{herb.unit}，"
                    f"申请 {item.quantity}{herb.unit}"
                )
            need = item.quantity
            batches = Batch.objects.select_for_update().filter(
                herb=herb, status="active", remaining_quantity__gt=0
            ).order_by(F("expiry_date").asc(nulls_last=True), "id")
            if item.batch_id:
                batches = batches.filter(pk=item.batch_id)

            for batch in batches:
                if need <= 0:
                    break
                take = min(need, batch.remaining_quantity)
                batch.remaining_quantity -= take
                if batch.remaining_quantity <= 0:
                    batch.status = "exhausted"
                batch.save(update_fields=["remaining_quantity", "status"])
                need -= take
                StockLedger.objects.create(
                    herb=herb,
                    batch=batch,
                    biz_type="out",
                    change_qty=-take,
                    before_qty=herb.total_stock + take,
                    after_qty=herb.total_stock,
                    ref_no=self.order_no,
                    operator=user,
                    remark=f"出库领用：{self.department}",
                )
            if need > 0:
                raise ValueError(f"【{herb.name}】批次可用库存不足，请调整明细")

        self.status = "approved"
        self.approver = user
        self.approve_time = timezone.now()
        self.approve_remark = remark
        self.save(update_fields=["status", "approver", "approve_time", "approve_remark"])

    def reject(self, user, remark=""):
        if self.status != "pending":
            raise ValueError("只有待审核的单据可以驳回")
        from django.utils import timezone

        self.status = "rejected"
        self.approver = user
        self.approve_time = timezone.now()
        self.approve_remark = remark
        self.save(update_fields=["status", "approver", "approve_time", "approve_remark"])


class OutboundItem(models.Model):
    """出库明细。batch 为空表示由系统按近效期自动扣减。"""

    order = models.ForeignKey(OutboundOrder, on_delete=models.CASCADE, verbose_name="出库单",
                              related_name="items")
    herb = models.ForeignKey(Herb, on_delete=models.PROTECT, verbose_name="药材",
                             related_name="outbound_items")
    batch = models.ForeignKey(Batch, on_delete=models.SET_NULL, null=True, blank=True,
                              verbose_name="指定批次", related_name="outbound_items")
    quantity = models.DecimalField("领用数量", max_digits=12, decimal_places=2)
    remark = models.CharField("明细备注", max_length=120, blank=True)

    class Meta:
        verbose_name = "出库明细"
        verbose_name_plural = "出库明细"
        ordering = ["id"]

    def __str__(self):
        return f"{self.order.order_no} - {self.herb.name}"


class OutboundAttachment(models.Model):
    """出库单附件（学生 4 功能点③：异常备注、附件上传与历史记录追溯）。"""

    order = models.ForeignKey(OutboundOrder, on_delete=models.CASCADE,
                              verbose_name="出库单", related_name="attachments")
    file = models.FileField("附件", upload_to="outbound/%Y%m/")
    title = models.CharField("附件说明", max_length=80, blank=True)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                    null=True, blank=True, verbose_name="上传人",
                                    related_name="outbound_attachments")
    uploaded_at = models.DateTimeField("上传时间", auto_now_add=True)

    class Meta:
        verbose_name = "出库附件"
        verbose_name_plural = "出库附件"
        ordering = ["-uploaded_at"]

    def __str__(self):
        return self.title or self.filename

    @property
    def filename(self):
        return os.path.basename(self.file.name)

    @property
    def size_display(self):
        """自动换算单位，避免小文件显示成 0.0 KB。"""
        try:
            size = self.file.size
        except (OSError, ValueError):
            return "—"
        if size < 1024:
            return f"{size} B"
        if size < 1024 * 1024:
            return f"{round(size / 1024, 1)} KB"
        return f"{round(size / 1024 / 1024, 2)} MB"

    @property
    def is_image(self):
        return self.filename.lower().endswith((".png", ".jpg", ".jpeg", ".gif", ".webp"))
