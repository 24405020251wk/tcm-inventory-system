from django.contrib import messages
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from core.permissions import menu_required
from core.utils import export_response, gen_order_no, log_action, paginate, parse_date
from herbs.models import Herb

from .forms import OutboundAttachmentForm, OutboundItemFormSet, OutboundOrderForm
from .models import OutboundAttachment, OutboundOrder


@menu_required("outbound.list")
def outbound_list(request):
    orders = OutboundOrder.objects.select_related("applicant", "approver").all()
    keyword = request.GET.get("q", "").strip()
    status = request.GET.get("status", "")
    start = parse_date(request.GET.get("start"))
    end = parse_date(request.GET.get("end"))

    if keyword:
        orders = orders.filter(
            Q(order_no__icontains=keyword) | Q(department__icontains=keyword)
            | Q(purpose__icontains=keyword)
        )
    if status:
        orders = orders.filter(status=status)
    if start:
        orders = orders.filter(apply_date__gte=start)
    if end:
        orders = orders.filter(apply_date__lte=end)

    page_obj, querystring = paginate(request, orders, 10)
    return render(request, "outbound/outbound_list.html", {
        "page_obj": page_obj,
        "querystring": querystring,
        "keyword": keyword,
        "status": status,
        "start": request.GET.get("start", ""),
        "end": request.GET.get("end", ""),
        "status_choices": OutboundOrder.STATUS_CHOICES,
        "total": orders.count(),
    })


@menu_required("outbound.list")
def outbound_detail(request, pk):
    order = get_object_or_404(
        OutboundOrder.objects.select_related("applicant", "approver")
        .prefetch_related("items__herb", "items__batch", "attachments__uploaded_by"),
        pk=pk,
    )
    return render(request, "outbound/outbound_detail.html", {
        "order": order,
        "attachment_form": OutboundAttachmentForm(),
    })


@menu_required("outbound.list")
@require_POST
def attachment_upload(request, pk):
    """出库单附件上传（学生 4 功能点③ 附件上传）。"""
    order = get_object_or_404(OutboundOrder, pk=pk)
    form = OutboundAttachmentForm(request.POST, request.FILES)
    if form.is_valid():
        attachment = form.save(commit=False)
        attachment.order = order
        attachment.uploaded_by = request.user
        attachment.save()
        log_action(request, "outbound", "上传附件", target=order.order_no,
                   detail=attachment.filename)
        messages.success(request, f"附件 {attachment.filename} 上传成功")
    else:
        first = next(iter(form.errors.values()))[0] if form.errors else "附件上传失败"
        messages.error(request, str(first))
    return redirect("outbound:detail", pk=pk)


@menu_required("outbound.list")
@require_POST
def attachment_delete(request, pk, att_id):
    order = get_object_or_404(OutboundOrder, pk=pk)
    attachment = get_object_or_404(OutboundAttachment, pk=att_id, order=order)
    name = attachment.filename
    attachment.file.delete(save=False)
    attachment.delete()
    log_action(request, "outbound", "删除附件", target=order.order_no, detail=name)
    messages.success(request, f"附件 {name} 已删除")
    return redirect("outbound:detail", pk=pk)


@menu_required("outbound.list")
def outbound_print(request, pk):
    """打印用页面（学生 5 功能点③ 打印页面）。"""
    order = get_object_or_404(
        OutboundOrder.objects.select_related("applicant", "approver")
        .prefetch_related("items__herb", "items__batch", "attachments"),
        pk=pk,
    )
    log_action(request, "outbound", "打印出库单", target=order.order_no)
    return render(request, "outbound/outbound_print.html", {"order": order})


@menu_required("outbound.list")
@transaction.atomic
def outbound_form(request, pk=None):
    instance = get_object_or_404(OutboundOrder, pk=pk) if pk else None
    if instance and instance.status not in ("draft", "rejected"):
        messages.error(request, "只有草稿或已驳回的单据可以编辑")
        return redirect("outbound:detail", pk=instance.pk)

    if request.method == "POST":
        form = OutboundOrderForm(request.POST, instance=instance)
        formset = OutboundItemFormSet(request.POST, instance=instance)
        if form.is_valid() and formset.is_valid():
            order = form.save(commit=False)
            if not order.pk:
                order.order_no = gen_order_no("CK")
                order.applicant = request.user
            if order.status == "rejected":
                order.status = "draft"
            order.save()
            formset.instance = order
            formset.save()
            log_action(request, "outbound", "编辑出库单" if instance else "创建出库单",
                       target=order.order_no,
                       detail=f"领用部门 {order.department}，明细 {order.items.count()} 条")
            messages.success(request, "出库单保存成功，提交后进入审核流程")
            return redirect("outbound:detail", pk=order.pk)
    else:
        form = OutboundOrderForm(instance=instance)
        formset = OutboundItemFormSet(instance=instance)

    herbs = Herb.objects.filter(status="active").order_by("code")
    return render(request, "outbound/outbound_form.html", {
        "form": form,
        "formset": formset,
        "instance": instance,
        "herbs": herbs,
        "herb_prices": {str(h.pk): float(h.price) for h in herbs},
    })


@menu_required("outbound.list")
@require_POST
def outbound_submit(request, pk):
    order = get_object_or_404(OutboundOrder, pk=pk)
    try:
        order.submit()
        log_action(request, "outbound", "提交出库审核", target=order.order_no)
        messages.success(request, "已提交审核，请等待审核人处理")
    except ValueError as exc:
        messages.error(request, str(exc))
    return redirect("outbound:detail", pk=pk)


@menu_required("outbound.approve")
@require_POST
def outbound_approve(request, pk):
    order = get_object_or_404(OutboundOrder, pk=pk)
    remark = request.POST.get("approve_remark", "")
    try:
        order.approve(request.user, remark)
        log_action(request, "outbound", "审核通过并出库", target=order.order_no,
                   detail=f"审核意见：{remark or '无'}，数量 {order.total_quantity}")
        messages.success(request, f"出库单 {order.order_no} 已审核通过，库存已扣减")
    except ValueError as exc:
        messages.error(request, str(exc))
    return redirect("outbound:detail", pk=pk)


@menu_required("outbound.approve")
@require_POST
def outbound_reject(request, pk):
    order = get_object_or_404(OutboundOrder, pk=pk)
    remark = request.POST.get("approve_remark", "").strip()
    if not remark:
        messages.error(request, "驳回时必须填写审核意见")
        return redirect("outbound:detail", pk=pk)
    try:
        order.reject(request.user, remark)
        log_action(request, "outbound", "驳回出库申请", target=order.order_no, detail=remark)
        messages.warning(request, "单据已驳回，申请人可修改后重新提交")
    except ValueError as exc:
        messages.error(request, str(exc))
    return redirect("outbound:detail", pk=pk)


@menu_required("outbound.list")
@require_POST
def outbound_cancel(request, pk):
    order = get_object_or_404(OutboundOrder, pk=pk)
    if order.status not in ("draft", "pending", "rejected"):
        messages.error(request, "已出库的单据不能作废")
        return redirect("outbound:detail", pk=pk)
    order.status = "cancelled"
    order.save(update_fields=["status"])
    log_action(request, "outbound", "作废出库单", target=order.order_no)
    messages.success(request, "出库单已作废")
    return redirect("outbound:detail", pk=pk)


@menu_required("outbound.list")
def outbound_export(request):
    orders = OutboundOrder.objects.select_related("applicant", "approver").all()
    fmt = request.GET.get("fmt", "xlsx")
    headers = ["出库单号", "领用部门", "用途", "申请人", "申请日期", "状态",
               "审核人", "审核时间", "审核意见", "总数量", "异常备注"]
    rows = [[
        o.order_no, o.department, o.purpose, o.applicant.display_name, o.apply_date,
        o.get_status_display(), o.approver.display_name if o.approver else "",
        o.approve_time.strftime("%Y-%m-%d %H:%M") if o.approve_time else "",
        o.approve_remark, o.total_quantity, o.exception_note,
    ] for o in orders]
    log_action(request, "outbound", "导出出库单", detail=f"共 {len(rows)} 条")
    return export_response("出库单明细", headers, rows, fmt)
