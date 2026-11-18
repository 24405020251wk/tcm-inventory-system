from decimal import Decimal

from django.contrib import messages
from django.db.models import DecimalField, F, Q, Sum, Value
from django.db.models.functions import Coalesce
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from core.permissions import menu_required
from core.utils import export_response, log_action, paginate

from .forms import HerbCategoryForm, HerbForm
from .models import Herb, HerbCategory

STOCK_FIELD = DecimalField(max_digits=14, decimal_places=2)


def with_stock(queryset=None):
    """给药材查询集附加实时库存注解，支持按库存排序。"""
    queryset = queryset if queryset is not None else Herb.objects.all()
    return queryset.annotate(
        stock=Coalesce(
            Sum("batches__remaining_quantity", filter=Q(batches__status="active")),
            Value(Decimal("0")),
            output_field=STOCK_FIELD,
        )
    )


def _filtered(request):
    herbs = with_stock().select_related("category")
    keyword = request.GET.get("q", "").strip()
    category_id = request.GET.get("category", "")
    status = request.GET.get("status", "")
    stock_flag = request.GET.get("stock", "")
    sort = request.GET.get("sort", "code")

    if keyword:
        herbs = herbs.filter(
            Q(name__icontains=keyword) | Q(code__icontains=keyword)
            | Q(pinyin__icontains=keyword) | Q(origin__icontains=keyword)
        )
    if category_id:
        herbs = herbs.filter(category_id=category_id)
    if status:
        herbs = herbs.filter(status=status)
    if stock_flag == "low":
        herbs = herbs.filter(stock__lt=F("min_stock"), stock__gt=0)
    elif stock_flag == "zero":
        herbs = herbs.filter(stock__lte=0)
    elif stock_flag == "enough":
        herbs = herbs.filter(stock__gte=F("min_stock"))

    sort_map = {
        "code": "code", "-code": "-code",
        "name": "name", "-name": "-name",
        "stock": "stock", "-stock": "-stock",
        "created": "-created_at",
    }
    herbs = herbs.order_by(sort_map.get(sort, "code"), "id")
    return herbs, {
        "keyword": keyword,
        "category_id": category_id,
        "status": status,
        "stock_flag": stock_flag,
        "sort": sort,
    }


@menu_required("herb.list")
def herb_list(request):
    herbs, filters = _filtered(request)
    page_obj, querystring = paginate(request, herbs, 10)
    return render(request, "herbs/herb_list.html", {
        "page_obj": page_obj,
        "querystring": querystring,
        "categories": HerbCategory.objects.all(),
        "filters": filters,
        "total": herbs.count(),
    })


@menu_required("herb.list")
def herb_detail(request, pk):
    herb = get_object_or_404(Herb, pk=pk)
    batches = herb.batches.order_by("expiry_date", "id")
    ledgers = herb.ledgers.select_related("batch", "operator")[:20]
    inbound_items = herb.inbound_items.select_related("order")[:10]
    outbound_items = herb.outbound_items.select_related("order")[:10]
    return render(request, "herbs/herb_detail.html", {
        "herb": herb,
        "batches": batches,
        "ledgers": ledgers,
        "inbound_items": inbound_items,
        "outbound_items": outbound_items,
    })


@menu_required("herb.list")
def herb_form(request, pk=None):
    instance = get_object_or_404(Herb, pk=pk) if pk else None
    form = HerbForm(request.POST or None, instance=instance)
    if request.method == "POST" and form.is_valid():
        herb = form.save()
        log_action(request, "herb", "编辑药材档案" if instance else "新增药材档案",
                   target=f"{herb.name}（{herb.code}）")
        messages.success(request, "药材档案保存成功")
        return redirect("herbs:detail", pk=herb.pk)
    return render(request, "herbs/herb_form.html", {
        "form": form,
        "instance": instance,
        "categories": HerbCategory.objects.all(),
    })


@menu_required("herb.list")
@require_POST
def herb_delete(request, pk):
    herb = get_object_or_404(Herb, pk=pk)
    if herb.batches.exists() or herb.inbound_items.exists() or herb.outbound_items.exists():
        messages.error(request, "该药材已有入库/出库业务数据，不能删除，可改为停用")
        return redirect("herbs:detail", pk=pk)
    name = f"{herb.name}（{herb.code}）"
    herb.delete()
    log_action(request, "herb", "删除药材档案", target=name)
    messages.success(request, "药材档案已删除")
    return redirect("herbs:list")


@menu_required("herb.list")
def herb_export(request):
    herbs, _ = _filtered(request)
    fmt = request.GET.get("fmt", "xlsx")
    headers = ["药材编码", "药材名称", "拼音码", "分类", "规格", "单位", "产地",
               "保质期(天)", "库存下限", "参考单价", "当前库存", "库存状态", "状态"]
    rows = []
    for herb in herbs:
        rows.append([
            herb.code, herb.name, herb.pinyin, herb.category.name, herb.spec, herb.unit,
            herb.origin, herb.shelf_life_days, herb.min_stock, herb.price,
            herb.stock, herb.stock_status, herb.get_status_display(),
        ])
    log_action(request, "herb", "导出药材档案", detail=f"共 {len(rows)} 条，格式 {fmt}")
    return export_response("中药材档案", headers, rows, fmt)


# ----------------------------- 分类管理 -----------------------------
@menu_required("herb.list")
def category_list(request):
    return render(request, "herbs/category_list.html", {
        "categories": HerbCategory.objects.all(),
        "form": HerbCategoryForm(),
    })


@menu_required("herb.list")
def category_form(request, pk=None):
    instance = get_object_or_404(HerbCategory, pk=pk) if pk else None
    form = HerbCategoryForm(request.POST or None, instance=instance)
    if request.method == "POST" and form.is_valid():
        category = form.save()
        log_action(request, "herb", "保存药材分类", target=category.name)
        messages.success(request, "分类保存成功")
        return redirect("herbs:category_list")
    return render(request, "herbs/category_form.html", {"form": form, "instance": instance})


@menu_required("herb.list")
@require_POST
def category_delete(request, pk):
    category = get_object_or_404(HerbCategory, pk=pk)
    if category.herbs.exists():
        messages.error(request, "该分类下还有药材，无法删除")
    else:
        category.delete()
        messages.success(request, "分类已删除")
    return redirect("herbs:category_list")
