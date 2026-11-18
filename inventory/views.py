from datetime import date, timedelta
from decimal import Decimal

from django.db.models import F, Q, Sum
from django.db.models.functions import TruncMonth
from django.shortcuts import render

from core.models import OperationLog
from core.permissions import menu_required
from core.utils import export_response, log_action, paginate, parse_date
from herbs.models import Herb, HerbCategory
from herbs.views import with_stock
from inbound.models import Batch
from inventory.models import StockLedger


@menu_required("inventory.stock")
def stock_list(request):
    herbs = with_stock().select_related("category")
    keyword = request.GET.get("q", "").strip()
    category_id = request.GET.get("category", "")
    stock_flag = request.GET.get("stock", "")
    expiry_days = request.GET.get("expiry", "")

    if keyword:
        herbs = herbs.filter(Q(name__icontains=keyword) | Q(code__icontains=keyword)
                             | Q(pinyin__icontains=keyword))
    if category_id:
        herbs = herbs.filter(category_id=category_id)
    if stock_flag == "low":
        herbs = herbs.filter(stock__lt=F("min_stock"), stock__gt=0)
    elif stock_flag == "zero":
        herbs = herbs.filter(stock__lte=0)
    if expiry_days:
        deadline = date.today() + timedelta(days=int(expiry_days))
        herbs = herbs.filter(
            batches__status="active", batches__remaining_quantity__gt=0,
            batches__expiry_date__lte=deadline,
        ).distinct()

    herbs = herbs.order_by("code")
    total_value = sum((h.stock * h.price for h in herbs), Decimal("0"))
    page_obj, querystring = paginate(request, herbs, 10)
    return render(request, "inventory/stock_list.html", {
        "page_obj": page_obj,
        "querystring": querystring,
        "categories": HerbCategory.objects.all(),
        "keyword": keyword,
        "category_id": category_id,
        "stock_flag": stock_flag,
        "expiry_days": expiry_days,
        "total": herbs.count(),
        "total_value": total_value,
    })


@menu_required("inventory.stock")
def stock_export(request):
    herbs = with_stock().select_related("category").order_by("code")
    fmt = request.GET.get("fmt", "xlsx")
    headers = ["药材编码", "药材名称", "分类", "规格", "单位", "当前库存", "库存下限",
               "库存状态", "参考单价", "库存金额"]
    rows = [[h.code, h.name, h.category.name, h.spec, h.unit, h.stock, h.min_stock,
             h.stock_status, h.price, h.stock * h.price] for h in herbs]
    log_action(request, "inventory", "导出库存台账", detail=f"共 {len(rows)} 条")
    return export_response("库存台账", headers, rows, fmt)


@menu_required("inventory.stock")
def batch_list(request):
    batches = Batch.objects.select_related("herb").filter(remaining_quantity__gt=0)
    keyword = request.GET.get("q", "").strip()
    herb_id = request.GET.get("herb", "")
    expiring = request.GET.get("expiring", "")
    if keyword:
        batches = batches.filter(Q(batch_no__icontains=keyword)
                                 | Q(herb__name__icontains=keyword))
    if herb_id:
        batches = batches.filter(herb_id=herb_id)
    if expiring:
        batches = batches.filter(expiry_date__lte=date.today() + timedelta(days=int(expiring)))
    batches = batches.order_by("expiry_date", "id")
    page_obj, querystring = paginate(request, batches, 10)
    return render(request, "inventory/batch_list.html", {
        "page_obj": page_obj,
        "querystring": querystring,
        "keyword": keyword,
        "herb_id": herb_id,
        "expiring": expiring,
        "herbs": Herb.objects.filter(status="active").order_by("code"),
        "today": date.today(),
        "total": batches.count(),
    })


def _stats_data():
    """统计数据集：优先使用 pandas 做汇总清洗，环境缺失时回退到纯 Python。"""
    today = date.today()
    herbs = list(with_stock().select_related("category").all())

    # 用 pandas 完成「按分类汇总 + 库存 Top10」的数据清洗与聚合
    rows = [{
        "category": h.category.name,
        "name": h.name,
        "stock": float(h.stock),
        "price": float(h.price),
        "min_stock": float(h.min_stock),
        "amount": float(h.stock * h.price),
    } for h in herbs]
    try:
        import pandas as pd

        df = pd.DataFrame(rows, columns=["category", "name", "stock", "price",
                                         "min_stock", "amount"])
        category_series = (
            df.groupby("category")["stock"].sum().sort_values(ascending=False)
        )
        top_df = df.sort_values("stock", ascending=False).head(10)
        category_labels = category_series.index.tolist()
        category_values = [round(float(v), 2) for v in category_series.tolist()]
        top_herbs = top_df[["name", "stock"]].to_dict("records")
        total_stock = round(float(df["stock"].sum()), 2)
        total_value = round(float(df["amount"].sum()), 2)
    except Exception:  # pandas 未安装时回退
        category_map = {}
        for herb in herbs:
            category_map[herb.category.name] = category_map.get(
                herb.category.name, Decimal("0")) + herb.stock
        category_map = dict(sorted(category_map.items(), key=lambda kv: kv[1], reverse=True))
        category_labels = list(category_map.keys())
        category_values = [float(v) for v in category_map.values()]
        top_herbs = [{"name": h.name, "stock": float(h.stock)}
                     for h in sorted(herbs, key=lambda x: x.stock, reverse=True)[:10]]
        total_stock = float(sum((h.stock for h in herbs), Decimal("0")))
        total_value = float(sum((h.stock * h.price for h in herbs), Decimal("0")))

    low_stock = [h for h in herbs if h.stock < h.min_stock][:10]

    expiring_batches = Batch.objects.select_related("herb").filter(
        status="active", remaining_quantity__gt=0,
        expiry_date__isnull=False,
        expiry_date__lte=today + timedelta(days=90),
    ).order_by("expiry_date")[:20]

    months = []
    for i in range(5, -1, -1):
        year, month = today.year, today.month - i
        while month <= 0:
            month += 12
            year -= 1
        months.append(f"{year}-{month:02d}")

    ledger_qs = StockLedger.objects.filter(
        created_at__date__gte=(today.replace(day=1) - timedelta(days=185))
    )
    monthly_rows = (
        ledger_qs.annotate(month=TruncMonth("created_at"))
        .values("month", "biz_type")
        .annotate(qty=Sum("change_qty"))
        .order_by("month")
    )
    trend = {m: {"in": 0.0, "out": 0.0} for m in months}
    for row in monthly_rows:
        key = row["month"].strftime("%Y-%m")
        if key in trend:
            value = float(row["qty"] or 0)
            if row["biz_type"] == "out":
                trend[key]["out"] += abs(value)
            else:
                trend[key]["in"] += value

    data = {
        "category": {"labels": category_labels, "values": category_values},
        "top": {"labels": [row["name"] for row in top_herbs],
                "values": [round(float(row["stock"]), 2) for row in top_herbs]},
        "trend": {
            "labels": months,
            "in": [trend[m]["in"] for m in months],
            "out": [trend[m]["out"] for m in months],
        },
        "summary": {
            "herb_count": len(herbs),
            "total_stock": total_stock,
            "total_value": total_value,
            "low_count": len(low_stock),
            "expiring_count": len(expiring_batches),
        },
    }
    return data, low_stock, expiring_batches


@menu_required("inventory.stats")
def stats(request):
    data, low_stock, expiring_batches = _stats_data()
    return render(request, "inventory/stats.html", {
        "data": data,
        "summary": data["summary"],
        "low_stock": low_stock,
        "expiring_batches": expiring_batches,
    })


@menu_required("inventory.stock")
def ledger_list(request):
    ledgers = StockLedger.objects.select_related("herb", "batch", "operator")
    keyword = request.GET.get("q", "").strip()
    biz_type = request.GET.get("biz_type", "")
    start = parse_date(request.GET.get("start"))
    end = parse_date(request.GET.get("end"))
    herb_id = request.GET.get("herb", "")

    if keyword:
        ledgers = ledgers.filter(Q(herb__name__icontains=keyword)
                                 | Q(ref_no__icontains=keyword))
    if biz_type:
        ledgers = ledgers.filter(biz_type=biz_type)
    if herb_id:
        ledgers = ledgers.filter(herb_id=herb_id)
    if start:
        ledgers = ledgers.filter(created_at__date__gte=start)
    if end:
        ledgers = ledgers.filter(created_at__date__lte=end)

    page_obj, querystring = paginate(request, ledgers, 15)
    return render(request, "inventory/ledger_list.html", {
        "page_obj": page_obj,
        "querystring": querystring,
        "keyword": keyword,
        "biz_type": biz_type,
        "start": request.GET.get("start", ""),
        "end": request.GET.get("end", ""),
        "herb_id": herb_id,
        "herbs": Herb.objects.order_by("code"),
        "biz_choices": StockLedger.BIZ_CHOICES,
        "total": ledgers.count(),
    })


@menu_required("inventory.stock")
def ledger_export(request):
    ledgers = StockLedger.objects.select_related("herb", "batch", "operator").all()
    fmt = request.GET.get("fmt", "xlsx")
    headers = ["时间", "药材", "批次", "业务类型", "变动数量", "变动前", "变动后",
               "关联单号", "操作人", "备注"]
    rows = [[
        l.created_at.strftime("%Y-%m-%d %H:%M"), l.herb.name,
        l.batch.batch_no if l.batch else "", l.get_biz_type_display(),
        l.change_qty, l.before_qty, l.after_qty, l.ref_no,
        l.operator.display_name if l.operator else "", l.remark,
    ] for l in ledgers]
    log_action(request, "inventory", "导出库存流水", detail=f"共 {len(rows)} 条")
    return export_response("库存流水", headers, rows, fmt)


@menu_required("inventory.log")
def log_list(request):
    logs = OperationLog.objects.select_related("user").all()
    keyword = request.GET.get("q", "").strip()
    module = request.GET.get("module", "")
    start = parse_date(request.GET.get("start"))
    end = parse_date(request.GET.get("end"))
    if keyword:
        logs = logs.filter(Q(username__icontains=keyword) | Q(action__icontains=keyword)
                           | Q(target__icontains=keyword))
    if module:
        logs = logs.filter(module=module)
    if start:
        logs = logs.filter(created_at__date__gte=start)
    if end:
        logs = logs.filter(created_at__date__lte=end)

    page_obj, querystring = paginate(request, logs, 15)
    return render(request, "inventory/log_list.html", {
        "page_obj": page_obj,
        "querystring": querystring,
        "keyword": keyword,
        "module": module,
        "start": request.GET.get("start", ""),
        "end": request.GET.get("end", ""),
        "modules": OperationLog.MODULE_CHOICES,
        "total": logs.count(),
    })
