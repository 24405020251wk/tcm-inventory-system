import datetime as dt

from django import forms
from django.forms import inlineformset_factory

from core.widgets import BatchSelect, HerbSelect
from herbs.models import Herb
from inbound.models import Batch

from .models import OutboundAttachment, OutboundItem, OutboundOrder

# 附件大小上限 5MB，允许的类型（图片 + PDF + Office 常见格式）
MAX_UPLOAD_MB = 5
ALLOWED_SUFFIXES = (".png", ".jpg", ".jpeg", ".gif", ".webp", ".pdf",
                    ".doc", ".docx", ".xls", ".xlsx", ".txt")


class OutboundAttachmentForm(forms.ModelForm):
    """出库单附件上传（学生 4 功能点③）。"""

    class Meta:
        model = OutboundAttachment
        fields = ("file", "title")
        widgets = {
            "file": forms.ClearableFileInput(attrs={"class": "form-control form-control-sm"}),
            "title": forms.TextInput(attrs={"class": "form-control form-control-sm",
                                            "placeholder": "附件说明，如 领用凭证、现场照片"}),
        }

    def clean_file(self):
        upload = self.cleaned_data["file"]
        name = (upload.name or "").lower()
        if not name.endswith(ALLOWED_SUFFIXES):
            raise forms.ValidationError("仅支持图片、PDF、Office 文档或 txt 文件")
        if upload.size > MAX_UPLOAD_MB * 1024 * 1024:
            raise forms.ValidationError(f"单个附件不能超过 {MAX_UPLOAD_MB} MB")
        return upload


class OutboundOrderForm(forms.ModelForm):
    class Meta:
        model = OutboundOrder
        fields = ("department", "purpose", "apply_date", "exception_note", "remark")
        widgets = {
            "department": forms.TextInput(attrs={"class": "form-control",
                                                 "placeholder": "如 中药房 / 制剂室"}),
            "purpose": forms.TextInput(attrs={"class": "form-control",
                                              "placeholder": "如 门诊调剂、教学实验"}),
            "apply_date": forms.DateInput(attrs={"class": "form-control", "type": "date"},
                                          format="%Y-%m-%d"),
            "exception_note": forms.Textarea(attrs={"class": "form-control", "rows": 2,
                                                    "placeholder": "破包、短缺、应急领用等异常说明"}),
            "remark": forms.TextInput(attrs={"class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["apply_date"].initial = dt.date.today()
        self.fields["apply_date"].input_formats = ["%Y-%m-%d"]


class OutboundItemForm(forms.ModelForm):
    class Meta:
        model = OutboundItem
        fields = ("herb", "batch", "quantity", "remark")
        widgets = {
            "herb": HerbSelect(attrs={"class": "form-select herb-select"}),
            "batch": BatchSelect(attrs={"class": "form-select batch-select"}),
            "quantity": forms.NumberInput(attrs={"class": "form-control qty",
                                                 "step": "0.01", "min": "0.01"}),
            "remark": forms.TextInput(attrs={"class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["herb"].queryset = Herb.objects.filter(status="active").order_by("code")
        self.fields["herb"].empty_label = "选择药材"
        self.fields["batch"].queryset = Batch.objects.filter(
            status="active", remaining_quantity__gt=0
        ).select_related("herb").order_by("expiry_date")
        self.fields["batch"].empty_label = "系统自动（近效期优先）"
        self.fields["batch"].required = False
        self.initial["quantity"] = None

    def clean_quantity(self):
        qty = self.cleaned_data["quantity"]
        if qty is not None and qty <= 0:
            raise forms.ValidationError("领用数量必须大于 0")
        return qty

    def clean(self):
        cleaned = super().clean()
        herb, batch = cleaned.get("herb"), cleaned.get("batch")
        if herb and batch and batch.herb_id != herb.pk:
            self.add_error("batch", "所选批次与药材不匹配")
        return cleaned


OutboundItemFormSet = inlineformset_factory(
    OutboundOrder,
    OutboundItem,
    form=OutboundItemForm,
    extra=3,
    can_delete=True,
    min_num=1,
    validate_min=True,
    max_num=20,
)
