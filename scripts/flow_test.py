"""业务流程联调测试：入库 → 批次 → 领用 → 审核 → 库存扣减。

用法：
    python scripts/flow_test.py
"""
import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django  # noqa: E402

django.setup()

from django.test import Client  # noqa: E402

from core.models import OperationLog  # noqa: E402
from herbs.models import Herb  # noqa: E402
from inbound.models import InboundOrder  # noqa: E402
from inventory.models import StockLedger  # noqa: E402
from outbound.models import OutboundOrder  # noqa: E402


def formset_payload(prefix, rows):
    data = {
        f"{prefix}-TOTAL_FORMS": str(len(rows) + 1),
        f"{prefix}-INITIAL_FORMS": "0",
        f"{prefix}-MIN_NUM_FORMS": "1",
        f"{prefix}-MAX_NUM_FORMS": "20",
    }
    for index, row in enumerate(rows):
        for key, value in row.items():
            data[f"{prefix}-{index}-{key}"] = str(value)
    return data


def main():
    herb = Herb.objects.get(code="YC-0001")
    before = herb.total_stock
    print(f"测试药材：{herb.name}，初始库存 {before} {herb.unit}")

    keeper = Client()
    assert keeper.login(username="keeper", password="keeper123")
    approver = Client()
    assert approver.login(username="approver", password="approve123")

    # 1. 创建入库单（自动批号）
    payload = {
        "supplier": "联调测试供应商",
        "inbound_date": "2026-11-12",
        "remark": "自动化测试",
    }
    payload.update(formset_payload("items", [{
        "herb": herb.pk, "batch_no": "", "production_date": "2026-06-01",
        "expiry_date": "2027-06-01", "quantity": "10", "unit_price": "66",
    }]))
    response = keeper.post("/inbound/create/", payload)
    assert response.status_code == 302, f"入库单创建失败：{response.status_code}"
    order = InboundOrder.objects.filter(supplier="联调测试供应商").latest("id")
    print(f"✓ 入库单创建成功：{order.order_no}，状态 {order.get_status_display()}")

    # 2. 确认入库
    response = keeper.post(f"/inbound/{order.pk}/confirm/")
    assert response.status_code == 302
    order.refresh_from_db()
    assert order.status == "confirmed", "入库确认失败"
    batch = order.items.first().batch
    assert batch is not None and batch.remaining_quantity == 10, "批次未正确生成"
    herb.refresh_from_db()
    assert herb.total_stock == before + 10, f"库存未增加：{herb.total_stock}"
    print(f"✓ 确认入库成功：批次 {batch.batch_no}，剩余 {batch.remaining_quantity}，"
          f"库存 {herb.total_stock}")

    # 3. 创建领用单并提交
    payload = {
        "department": "中药房",
        "purpose": "联调测试领用",
        "apply_date": "2026-11-12",
        "exception_note": "",
        "remark": "",
    }
    payload.update(formset_payload("items", [{
        "herb": herb.pk, "batch": "", "quantity": "4", "remark": "测试",
    }]))
    response = keeper.post("/outbound/create/", payload)
    assert response.status_code == 302, f"出库单创建失败：{response.status_code}"
    out_order = OutboundOrder.objects.filter(purpose="联调测试领用").latest("id")
    keeper.post(f"/outbound/{out_order.pk}/submit/")
    out_order.refresh_from_db()
    assert out_order.status == "pending", "提交审核失败"
    print(f"✓ 领用单提交审核：{out_order.order_no}，状态 {out_order.get_status_display()}")

    # 4. 仓管员无审核权限
    response = keeper.post(f"/outbound/{out_order.pk}/approve/", {"approve_remark": "越权"})
    assert response.status_code == 403, f"权限校验失败：{response.status_code}"
    print("✓ 仓管员审核被拒绝（403），权限控制生效")

    # 5. 审核通过 → 扣减库存
    stock_before_out = herb.total_stock
    response = approver.post(f"/outbound/{out_order.pk}/approve/",
                             {"approve_remark": "同意领用"})
    assert response.status_code == 302
    out_order.refresh_from_db()
    assert out_order.status == "approved", "审核状态未更新"
    herb.refresh_from_db()
    assert herb.total_stock == stock_before_out - 4, f"库存扣减异常：{herb.total_stock}"
    ledger = StockLedger.objects.filter(ref_no=out_order.order_no, biz_type="out").first()
    assert ledger is not None and ledger.change_qty == -4
    print(f"✓ 审核通过扣减库存：{stock_before_out} → {herb.total_stock}，流水号 {ledger.ref_no}")

    # 6. 库存不足校验
    payload = {
        "department": "中药房", "purpose": "超量领用测试", "apply_date": "2026-11-12",
        "exception_note": "", "remark": "",
    }
    payload.update(formset_payload("items", [{
        "herb": herb.pk, "batch": "", "quantity": "999999", "remark": "",
    }]))
    keeper.post("/outbound/create/", payload)
    big_order = OutboundOrder.objects.filter(purpose="超量领用测试").latest("id")
    keeper.post(f"/outbound/{big_order.pk}/submit/")
    response = approver.post(f"/outbound/{big_order.pk}/approve/",
                             {"approve_remark": "测试"}, follow=True)
    big_order.refresh_from_db()
    assert big_order.status == "pending", "库存不足仍审核通过，业务校验失败"
    print("✓ 库存不足时审核被拦截，单据仍为待审核")

    # 7. 清理测试数据
    big_order.delete()
    out_order.items.all().delete()
    out_order.delete()
    batch.delete()
    order.items.all().delete()
    order.delete()
    StockLedger.objects.filter(ref_no__in=[out_order.order_no, order.order_no]).delete()
    print("✓ 测试数据已清理")

    print(f"\n操作日志条数：{OperationLog.objects.count()}（业务操作已留痕）")
    print("业务流程联调全部通过 ✅")


if __name__ == "__main__":
    main()
