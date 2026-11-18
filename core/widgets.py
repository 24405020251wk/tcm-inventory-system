"""自定义下拉组件：把药材单价、批次所属药材带入 option，便于前端联动。"""
from django import forms


class HerbSelect(forms.Select):
    def create_option(self, name, value, label, selected, index, subindex=None, attrs=None):
        option = super().create_option(name, value, label, selected, index, subindex, attrs)
        instance = getattr(value, "instance", None)
        if instance is not None:
            option["attrs"]["data-price"] = str(instance.price)
            option["attrs"]["data-unit"] = instance.unit
            option["attrs"]["data-stock"] = str(instance.total_stock)
        return option


class BatchSelect(forms.Select):
    def create_option(self, name, value, label, selected, index, subindex=None, attrs=None):
        option = super().create_option(name, value, label, selected, index, subindex, attrs)
        instance = getattr(value, "instance", None)
        if instance is not None:
            option["attrs"]["data-herb"] = str(instance.herb_id)
            option["attrs"]["data-remaining"] = str(instance.remaining_quantity)
        return option
