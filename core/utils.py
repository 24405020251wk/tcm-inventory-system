"""通用工具：单号生成、CSV/Excel 导出、分页、操作日志。"""
import csv
import datetime as dt
import random
from decimal import Decimal

from django.db.models import QuerySet
from django.http import HttpResponse

from .models import OperationLog


def gen_order_no(prefix: str) -> str:
    """生成业务单号，如 RK20261112-8351。"""
    stamp = dt.datetime.now().strftime("%Y%m%d%H%M%S")
    return f"{prefix}{stamp}{random.randint(100, 999)}"


def to_decimal(value, default="0") -> Decimal:
    try:
        return Decimal(str(value))
    except Exception:
        return Decimal(default)


def client_ip(request):
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def log_action(request, module, action, target="", detail=""):
    """写入操作日志，失败不影响主流程。"""
    try:
        user = getattr(request, "user", None)
        OperationLog.objects.create(
            user=user if getattr(user, "is_authenticated", False) else None,
            username=getattr(user, "username", "") or "匿名",
            module=module,
            action=action,
            target=str(target)[:150],
            detail=detail,
            ip=client_ip(request),
        )
    except Exception:  # pragma: no cover - 日志失败不阻断业务
        pass


def _table_rows(rows):
    for row in rows:
        yield ["" if cell is None else cell for cell in row]


def export_csv(filename: str, headers, rows) -> HttpResponse:
    response = HttpResponse(content_type="text/csv; charset=utf-8-sig")
    response["Content-Disposition"] = f'attachment; filename="{filename}.csv"'
    response.write("\ufeff")
    writer = csv.writer(response)
    writer.writerow(headers)
    for row in _table_rows(rows):
        writer.writerow(row)
    return response


def export_excel(filename: str, headers, rows) -> HttpResponse:
    """使用 openpyxl 导出 xlsx；未安装时降级为 CSV。"""
    try:
        from openpyxl import Workbook
        from openpyxl.styles import Alignment, Font, PatternFill
    except ImportError:
        return export_csv(filename, headers, rows)

    wb = Workbook()
    ws = wb.active
    ws.title = filename[:31]
    ws.append(list(headers))
    for cell in ws[1]:
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill("solid", fgColor="2F6B4F")
        cell.alignment = Alignment(horizontal="center", vertical="center")
    for row in rows:
        ws.append(["" if cell is None else cell for cell in row])
    for idx, header in enumerate(headers, start=1):
        width = max(12, min(30, len(str(header)) * 2 + 8))
        ws.column_dimensions[ws.cell(row=1, column=idx).column_letter].width = width
    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = f'attachment; filename="{filename}.xlsx"'
    wb.save(response)
    return response


def export_response(filename, headers, rows, fmt="xlsx"):
    if fmt == "csv":
        return export_csv(filename, headers, rows)
    return export_excel(filename, headers, rows)


def paginate(request, queryset: QuerySet, per_page: int = 10):
    """简单分页，返回 (page_obj, querystring)。"""
    from django.core.paginator import Paginator

    paginator = Paginator(queryset, per_page)
    page_obj = paginator.get_page(request.GET.get("page"))
    params = request.GET.copy()
    params.pop("page", None)
    querystring = params.urlencode()
    return page_obj, querystring


def parse_date(value):
    if not value:
        return None
    for fmt in ("%Y-%m-%d", "%Y/%m/%d"):
        try:
            return dt.datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    return None


def date_range_filter(qs, field, start, end):
    if start:
        qs = qs.filter(**{f"{field}__gte": start})
    if end:
        qs = qs.filter(**{f"{field}__lte": end})
    return qs
