from django import forms

from .models import Herb, HerbCategory


class HerbCategoryForm(forms.ModelForm):
    class Meta:
        model = HerbCategory
        fields = ("name", "code", "sort", "remark")
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "code": forms.TextInput(attrs={"class": "form-control"}),
            "sort": forms.NumberInput(attrs={"class": "form-control"}),
            "remark": forms.TextInput(attrs={"class": "form-control"}),
        }


class HerbForm(forms.ModelForm):
    class Meta:
        model = Herb
        fields = ("code", "name", "pinyin", "category", "spec", "unit", "origin",
                  "shelf_life_days", "storage_condition", "min_stock", "price",
                  "status", "remark")
        widgets = {
            "code": forms.TextInput(attrs={"class": "form-control", "placeholder": "如 YC-0001"}),
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "pinyin": forms.TextInput(attrs={"class": "form-control", "placeholder": "如 huangqi"}),
            "category": forms.Select(attrs={"class": "form-select"}),
            "spec": forms.TextInput(attrs={"class": "form-control"}),
            "unit": forms.TextInput(attrs={"class": "form-control"}),
            "origin": forms.TextInput(attrs={"class": "form-control"}),
            "shelf_life_days": forms.NumberInput(attrs={"class": "form-control"}),
            "storage_condition": forms.TextInput(attrs={"class": "form-control"}),
            "min_stock": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "price": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "status": forms.Select(attrs={"class": "form-select"}),
            "remark": forms.TextInput(attrs={"class": "form-control"}),
        }

    def clean_min_stock(self):
        value = self.cleaned_data["min_stock"]
        if value is not None and value < 0:
            raise forms.ValidationError("库存下限不能为负数")
        return value
