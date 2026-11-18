"""页面冒烟测试：验证各模块页面、筛选条件与导出接口可正常工作。

用法：
    python scripts/smoke_test.py
"""
import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django  # noqa: E402

django.setup()

from django.test import Client  # noqa: E402

from herbs.models import Herb  # noqa: E402
from inbound.models import InboundOrder  # noqa: E402
from outbound.models import OutboundOrder  # noqa: E402

PAGES = [
    "/", "/herbs/", "/herbs/create/", "/herbs/categories/", "/herbs/categories/create/",
    "/inbound/", "/inbound/create/", "/outbound/", "/outbound/create/",
    "/inventory/stock/", "/inventory/batches/", "/inventory/stats/",
    "/inventory/ledger/", "/inventory/logs/",
    "/accounts/users/", "/accounts/users/create/", "/accounts/roles/",
    "/accounts/roles/create/", "/accounts/menus/", "/accounts/menus/create/",
    "/accounts/profile/",
]

FILTERED = [
    "/herbs/?q=黄&sort=-stock&stock=low",
    "/herbs/?category=1&status=active",
    "/inbound/?status=confirmed&start=2026-01-01&end=2026-12-31",
    "/outbound/?status=pending&q=中药房",
    "/inventory/stock/?q=参&stock=low&expiry=180",
    "/inventory/batches/?expiring=90",
    "/inventory/ledger/?biz_type=out",
    "/inventory/logs/?module=outbound",
    "/accounts/users/?q=admin&role=1",
]

EXPORTS = [
    "/herbs/export/?fmt=xlsx",
    "/inventory/stock/export/?fmt=csv",
    "/inventory/ledger/export/?fmt=xlsx",
    "/inbound/export/?fmt=xlsx",
    "/outbound/export/?fmt=csv",
]


def main():
    herb = Herb.objects.first()
    inbound = InboundOrder.objects.first()
    outbound = OutboundOrder.objects.first()
    pages = PAGES + [
        f"/herbs/{herb.pk}/", f"/herbs/{herb.pk}/edit/",
        f"/inbound/{inbound.pk}/", f"/outbound/{outbound.pk}/",
        f"/outbound/{OutboundOrder.objects.filter(status='draft').first().pk}/edit/"
        if OutboundOrder.objects.filter(status="draft").exists() else "/outbound/",
    ]

    failures = []

    # 未登录页面
    anonymous = Client()
    for path in ["/accounts/login/", "/accounts/register/"]:
        response = anonymous.get(path)
        ok = response.status_code == 200
        print(f"[{'OK ' if ok else 'ERR'}] {response.status_code} {path}（未登录）")
        if not ok:
            failures.append((path, response.status_code))

    # 未登录访问业务页应跳转登录
    response = anonymous.get("/herbs/")
    ok = response.status_code == 302 and "/accounts/login/" in response["Location"]
    print(f"[{'OK ' if ok else 'ERR'}] {response.status_code} /herbs/（未登录应跳转登录）")
    if not ok:
        failures.append(("/herbs/ anonymous", response.status_code))

    client = Client()
    assert client.login(username="admin", password="admin123"), "管理员登录失败"
    for path in pages:
        response = client.get(path)
        ok = response.status_code == 200
        print(f"[{'OK ' if ok else 'ERR'}] {response.status_code} {path}")
        if not ok:
            failures.append((path, response.status_code))

    print("-" * 60)
    for path in FILTERED:
        response = client.get(path)
        ok = response.status_code == 200
        print(f"[{'OK ' if ok else 'ERR'}] {response.status_code} {path}（筛选）")
        if not ok:
            failures.append((path, response.status_code))

    for path in EXPORTS:
        response = client.get(path)
        ok = response.status_code == 200 and len(response.content) > 500
        print(f"[{'OK ' if ok else 'ERR'}] {response.status_code} {path}（{len(response.content)} 字节）")
        if not ok:
            failures.append((path, response.status_code))

    # 权限校验：普通员工访问用户管理应返回 403
    client2 = Client()
    assert client2.login(username="staff", password="staff123"), "普通员工登录失败"
    response = client2.get("/accounts/users/")
    ok = response.status_code == 403
    print(f"[{'OK ' if ok else 'ERR'}] {response.status_code} "
          f"/accounts/users/（普通员工应被拒绝）")
    if not ok:
        failures.append(("/accounts/users/ (staff)", response.status_code))

    print()
    total = len(pages) + len(FILTERED) + len(EXPORTS) + 3
    if failures:
        print(f"存在 {len(failures)} 个异常：{failures}")
        sys.exit(1)
    print(f"全部 {total} 项检查通过")


if __name__ == "__main__":
    main()
