from django.contrib import messages
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from core.permissions import menu_required
from core.utils import export_response, gen_order_no, log_action, paginate, parse_date
from herbs.models import Herb

from .forms import InboundItemFormSet, InboundOrderForm
from .models import Batch, InboundOrder


def _form_context(form, formset, instance):
    herbs = Herb.objects.filter(status="active").order_by("code")
    return {
        "form": form,
        "formset": formset,
        "instance": instance,
        "herbs": herbs,
        "herb_prices": {str(h.pk): float(h.price) for h in herbs},
    }


def _next_batch_no(herb, inbound_date, used=None):
    """生成批次号：PC+日期+药材编码，冲突时追加序号。"""
    used = used or set()
    base = f"PC{inbound_date:%Y%m%d}-{herb.code}"
    candidate, seq = base, 1
    while candidate in used or Batch.objects.filter(batch_no=candidate).exists():
        seq += 1
        candidate = f"{base}-{seq}"
    used.add(candidate)
    return candidate


@menu_required("inbound.list")
def inbound_list(request):
    orders = InboundOrder.objects.select_related("operator").all()
    keyword = request.GET.get("q", "").strip()
    status = request.GET.get("status", "")
    start = parse_date(request.GET.get("start"))
    end = parse_date(request.GET.get("end"))

    if keyword:
        orders = orders.filter(Q(order_no__icontains=keyword) | Q(supplier__icontains=keyword))
    if status:
        orders = orders.filter(status=status)
    if start:
        orders = orders.filter(inbound_date__gte=start)
    if end:
        orders = orders.filter(inbound_date__lte=end)

    page_obj, querystring = paginate(request, orders, 10)
    return render(request, "inbound/inbound_list.html", {
        "page_obj": page_obj,
        "querystring": querystring,
        "keyword": keyword,
        "status": status,
        "start": request.GET.get("start", ""),
        "end": request.GET.get("end", ""),
        "status_choices": InboundOrder.STATUS_CHOICES,
        "total": orders.count(),
    })


@menu_required("inbound.list")
def inbound_detail(request, pk):
    order = get_object_or_404(InboundOrder.objects.select_related("operator"), pk=pk)
    return render(request, "inbound/inbound_detail.html", {"order": order})


@menu_required("inbound.list")
def inbound_print(request, pk):
    """打印用页面（学生 5 功能点③ 打印页面）。"""
    order = get_object_or_404(
        InboundOrder.objects.select_related("operator").prefetch_related("items__herb", "items__batch"),
        pk=pk,
    )
    log_action(request, "inbound", "打印入库单", target=order.order_no)
    return render(request, "inbound/inbound_print.html", {"order": order})


@menu_required("inbound.list")
@transaction.atomic
def inbound_form(request, pk=None):
    instance = get_object_or_404(InboundOrder, pk=pk) if pk else None
    if instance and instance.status != "draft":
        messages.error(request, "只有草稿状态的入库单可以编辑")
        return redirect("inbound:detail", pk=instance.pk)

    if request.method == "POST":
        form = InboundOrderForm(request.POST, instance=instance)
        formset = InboundItemFormSet(request.POST, instance=instance)
        if form.is_valid() and formset.is_valid():
            # 校验同一张单内批次号是否重复
            manual_nos = [
                f.cleaned_data.get("batch_no")
                for f in formset.forms
                if f.cleaned_data and not f.cleaned_data.get("DELETE") and f.cleaned_data.get("batch_no")
            ]
            if len(manual_nos) != len(set(manual_nos)):
                messages.error(request, "同一入库单内批次号不能重复")
                return render(request, "inbound/inbound_form.html",
                              _form_context(form, formset, instance))
            conflict = list(Batch.objects.filter(batch_no__in=manual_nos)
                            .values_list("batch_no", flat=True))
            if conflict:
                messages.error(request, f"批次号已存在：{'、'.join(conflict)}，请更换或留空自动生成")
                return render(request, "inbound/inbound_form.html",
                              _form_context(form, formset, instance))
            order = form.save(commit=False)
            if not order.pk:
                order.order_no = gen_order_no("RK")
                order.operator = request.user
            order.save()
            formset.instance = order
            items = formset.save(commit=False)
            used = set()
            for obj in formset.deleted_objects:
                obj.delete()
            # 先收集本单已填写的批次号，避免同一单内重复
            for item in items:
                if item.batch_no:
                    used.add(item.batch_no)
            for item in items:
                if not item.batch_no:
                    item.batch_no = _next_batch_no(item.herb, order.inbound_date, used)
                item.order = order
                item.save()
            log_action(request, "inbound", "编辑入库单" if instance else "创建入库单",
                       target=order.order_no,
                       detail=f"供应商 {order.supplier}，明细 {order.items.count()} 条")
            messages.success(request, "入库单保存成功，确认后自动生成批次库存")
            return redirect("inbound:detail", pk=order.pk)
    else:
        form = InboundOrderForm(instance=instance)
        formset = InboundItemFormSet(instance=instance)

    return render(request, "inbound/inbound_form.html",
                  _form_context(form, formset, instance))


@menu_required("inbound.list")
@require_POST
def inbound_confirm(request, pk):
    order = get_object_or_404(InboundOrder, pk=pk)
    try:
        order.confirm(request.user)
        log_action(request, "inbound", "确认入库", target=order.order_no,
                   detail=f"生成批次 {order.items.count()} 个，数量 {order.total_quantity}")
        messages.success(request, f"入库单 {order.order_no} 已确认，批次库存已生成")
    except ValueError as exc:
        messages.error(request, str(exc))
    return redirect("inbound:detail", pk=pk)


@menu_required("inbound.list")
@require_POST
def inbound_cancel(request, pk):
    order = get_object_or_404(InboundOrder, pk=pk)
    if order.status == "confirmed":
        messages.error(request, "已入库的单据不能作废，请通过出库或盘点调整处理")
        return redirect("inbound:detail", pk=pk)
    order.status = "cancelled"
    order.save(update_fields=["status"])
    log_action(request, "inbound", "作废入库单", target=order.order_no)
    messages.success(request, "入库单已作废")
    return redirect("inbound:detail", pk=pk)


@menu_required("inbound.list")
def inbound_export(request):
    orders = InboundOrder.objects.select_related("operator").all()
    fmt = request.GET.get("fmt", "xlsx")
    headers = ["入库单号", "供应商", "入库日期", "经办人", "状态", "明细数", "总数量", "总金额", "备注"]
    rows = [[
        o.order_no, o.supplier, o.inbound_date, o.operator.display_name,
        o.get_status_display(), o.items.count(), o.total_quantity, o.total_amount, o.remark,
    ] for o in orders]
    log_action(request, "inbound", "导出入库单", detail=f"共 {len(rows)} 条")
    return export_response("入库单明细", headers, rows, fmt)
