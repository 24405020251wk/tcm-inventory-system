from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from core.models import OperationLog
from herbs.views import with_stock
from inbound.models import Batch, InboundOrder
from outbound.models import OutboundOrder


@login_required
def dashboard(request):
    today = date.today()
    herbs = list(with_stock().select_related("category").all())
    active_batches = Batch.objects.filter(status="active", remaining_quantity__gt=0)

    total_stock = sum((h.stock for h in herbs), Decimal("0"))
    total_value = sum((h.stock * h.price for h in herbs), Decimal("0"))
    low_stock = [h for h in herbs if h.stock < h.min_stock]

    category_map = {}
    for herb in herbs:
        category_map[herb.category.name] = category_map.get(
            herb.category.name, Decimal("0")) + herb.stock
    top_herbs = sorted(herbs, key=lambda h: h.stock, reverse=True)[:8]

    context = {
        "herb_count": len(herbs),
        "batch_count": active_batches.count(),
        "total_stock": total_stock,
        "total_value": total_value,
        "low_stock_count": len(low_stock),
        "expiring_count": active_batches.filter(
            expiry_date__isnull=False,
            expiry_date__lte=today + timedelta(days=30),
        ).count(),
        "pending_count": OutboundOrder.objects.filter(status="pending").count(),
        "today_inbound": InboundOrder.objects.filter(status="confirmed",
                                                     inbound_date=today).count(),
        "today_outbound": OutboundOrder.objects.filter(status="approved",
                                                       approve_time__date=today).count(),
        "recent_inbound": InboundOrder.objects.select_related("operator")[:5],
        "recent_outbound": OutboundOrder.objects.select_related("applicant")[:5],
        "recent_logs": OperationLog.objects.select_related("user")[:8],
        "low_stock": low_stock[:6],
        "chart": {
            "category": {
                "labels": list(category_map.keys()),
                "values": [float(v) for v in category_map.values()],
            },
            "top": {
                "labels": [h.name for h in top_herbs],
                "values": [float(h.stock) for h in top_herbs],
            },
        },
    }
    return render(request, "core/dashboard.html", context)
