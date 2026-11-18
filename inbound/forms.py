import datetime as dt

from django import forms
from django.forms import inlineformset_factory

from core.widgets import HerbSelect
from herbs.models import Herb

from .models import InboundItem, InboundOrder


class InboundOrderForm(forms.ModelForm):
    class Meta:
        model = InboundOrder
        fields = ("supplier", "inbound_date", "remark")
        widgets = {
            "supplier": forms.TextInput(attrs={"class": "form-control",
                                               "placeholder": "如 亳州中药材批发有限公司"}),
            "inbound_date": forms.DateInput(attrs={"class": "form-control", "type": "date"},
                                            format="%Y-%m-%d"),
            "remark": forms.TextInput(attrs={"class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["inbound_date"].initial = dt.date.today()
        self.fields["inbound_date"].input_formats = ["%Y-%m-%d"]


class InboundItemForm(forms.ModelForm):
    class Meta:
        model = InboundItem
        fields = ("herb", "batch_no", "production_date", "expiry_date", "quantity", "unit_price")
        widgets = {
            "herb": HerbSelect(attrs={"class": "form-select herb-select"}),
            "batch_no": forms.TextInput(attrs={"class": "form-control batch-no",
                                               "placeholder": "留空自动生成"}),
            "production_date": forms.DateInput(attrs={"class": "form-control", "type": "date"},
                                               format="%Y-%m-%d"),
            "expiry_date": forms.DateInput(attrs={"class": "form-control", "type": "date"},
                                           format="%Y-%m-%d"),
            "quantity": forms.NumberInput(attrs={"class": "form-control qty", "step": "0.01",
                                                 "min": "0.01"}),
            "unit_price": forms.NumberInput(attrs={"class": "form-control price",
                                                   "step": "0.01", "min": "0"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["herb"].queryset = Herb.objects.filter(status="active").order_by("code")
        self.fields["herb"].empty_label = "选择药材"
        # 清空模型默认值，避免空白行被判定为「已修改」
        for name in ("quantity", "unit_price", "batch_no"):
            self.initial[name] = None
        for name in ("production_date", "expiry_date"):
            self.fields[name].input_formats = ["%Y-%m-%d"]

    def clean(self):
        cleaned = super().clean()
        qty = cleaned.get("quantity")
        if qty is not None and qty <= 0:
            self.add_error("quantity", "数量必须大于 0")
        prod, exp = cleaned.get("production_date"), cleaned.get("expiry_date")
        if prod and exp and exp <= prod:
            self.add_error("expiry_date", "有效期必须晚于生产日期")
        return cleaned


InboundItemFormSet = inlineformset_factory(
    InboundOrder,
    InboundItem,
    form=InboundItemForm,
    extra=3,
    can_delete=True,
    min_num=1,
    validate_min=True,
    validate_max=True,
    max_num=20,
)
