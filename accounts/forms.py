from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from .models import Menu, Role, User


class LoginForm(AuthenticationForm):
    username = forms.CharField(
        label="账号",
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "请输入账号",
                                      "autofocus": True}),
    )
    password = forms.CharField(
        label="密码",
        widget=forms.PasswordInput(attrs={"class": "form-control", "placeholder": "请输入密码"}),
    )


class RegisterForm(UserCreationForm):
    real_name = forms.CharField(label="姓名", max_length=50,
                                widget=forms.TextInput(attrs={"class": "form-control"}))
    phone = forms.CharField(label="手机号", max_length=20, required=False,
                            widget=forms.TextInput(attrs={"class": "form-control"}))
    department = forms.CharField(label="部门", max_length=50, required=False,
                                 widget=forms.TextInput(attrs={"class": "form-control"}))

    class Meta:
        model = User
        fields = ("username", "real_name", "phone", "department")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].widget.attrs.update(
            {"class": "form-control", "placeholder": "4-20 位字母或数字"}
        )
        self.fields["password1"].widget.attrs.update({"class": "form-control"})
        self.fields["password2"].widget.attrs.update({"class": "form-control"})
        self.fields["username"].help_text = "登录账号，注册后不可修改"
        self.fields["password1"].help_text = "至少 6 位，不能与账号过于相似"


class UserForm(forms.ModelForm):
    password = forms.CharField(
        label="登录密码", required=False,
        widget=forms.PasswordInput(attrs={"class": "form-control", "autocomplete": "new-password"}),
        help_text="新增用户必填；编辑时留空表示不修改密码",
    )

    class Meta:
        model = User
        fields = ("username", "real_name", "phone", "department", "role", "is_active")
        widgets = {
            "username": forms.TextInput(attrs={"class": "form-control"}),
            "real_name": forms.TextInput(attrs={"class": "form-control"}),
            "phone": forms.TextInput(attrs={"class": "form-control"}),
            "department": forms.TextInput(attrs={"class": "form-control"}),
            "role": forms.Select(attrs={"class": "form-select"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["role"].queryset = Role.objects.filter(is_active=True)
        self.fields["role"].empty_label = "请选择角色"
        self.fields["is_active"].widget.attrs.update({"class": "form-check-input"})

    def clean(self):
        cleaned = super().clean()
        if not self.instance.pk and not cleaned.get("password"):
            self.add_error("password", "新增用户必须设置初始密码")
        return cleaned

    def save(self, commit=True):
        user = super().save(commit=False)
        password = self.cleaned_data.get("password")
        if password:
            user.set_password(password)
        if commit:
            user.save()
        return user


class RoleForm(forms.ModelForm):
    menus = forms.ModelMultipleChoiceField(
        label="菜单权限",
        queryset=Menu.objects.filter(is_active=True).order_by("group_name", "sort"),
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={"class": "menu-checkbox"}),
    )

    class Meta:
        model = Role
        fields = ("name", "code", "description", "is_active")
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "code": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.TextInput(attrs={"class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields["menus"].initial = self.instance.menus.all()

    def save(self, commit=True):
        role = super().save(commit=commit)
        if commit:
            from .models import RoleMenu

            RoleMenu.objects.filter(role=role).delete()
            RoleMenu.objects.bulk_create(
                [RoleMenu(role=role, menu=menu) for menu in self.cleaned_data["menus"]]
            )
        return role


class MenuForm(forms.ModelForm):
    class Meta:
        model = Menu
        fields = ("code", "name", "group_name", "url_name", "icon", "api_scope",
                  "sort", "is_active")
        widgets = {
            "code": forms.TextInput(attrs={"class": "form-control"}),
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "group_name": forms.Select(attrs={"class": "form-select"}),
            "url_name": forms.TextInput(attrs={"class": "form-control"}),
            "icon": forms.TextInput(attrs={"class": "form-control"}),
            "api_scope": forms.TextInput(attrs={"class": "form-control"}),
            "sort": forms.NumberInput(attrs={"class": "form-control"}),
        }
