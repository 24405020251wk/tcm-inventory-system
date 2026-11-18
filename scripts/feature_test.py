"""验证学生 4 功能点③（附件上传）与学生 5 功能点③（打印页面）。

运行：.venv\\Scripts\\python.exe scripts/feature_test.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django  # noqa: E402

django.setup()

from django.core.files.uploadedfile import SimpleUploadedFile  # noqa: E402
from django.test import Client  # noqa: E402

from inbound.models import InboundOrder  # noqa: E402
from outbound.models import OutboundAttachment, OutboundOrder  # noqa: E402

ok = 0
fail = 0


def check(label, condition, extra=""):
    global ok, fail
    if condition:
        ok += 1
        print(f"  [OK]   {label}")
    else:
        fail += 1
        print(f"  [FAIL] {label} {extra}")


def main():
    client = Client()
    assert client.login(username="admin", password="admin123"), "admin 登录失败"

    outbound = OutboundOrder.objects.first()
    inbound = InboundOrder.objects.first()
    print(f"用例对象：出库单 {outbound.order_no} / 入库单 {inbound.order_no}\n")

    print("一、打印页面")
    for name, url, keyword in [
        ("出库单打印", f"/outbound/{outbound.pk}/print/", "中药材领用出库单"),
        ("入库单打印", f"/inbound/{inbound.pk}/print/", "中药材入库单"),
    ]:
        resp = client.get(url)
        html = resp.content.decode("utf-8")
        check(f"{name} 返回 200", resp.status_code == 200, f"实际 {resp.status_code}")
        check(f"{name} 含标题「{keyword}」", keyword in html)
        check(f"{name} 含打印按钮", "window.print()" in html)
        check(f"{name} 含签字栏", "签字" in html)

    print("\n二、附件上传")
    before = OutboundAttachment.objects.filter(order=outbound).count()
    upload = SimpleUploadedFile("领用凭证.txt", "现场领用凭证测试".encode("utf-8"),
                                content_type="text/plain")
    resp = client.post(f"/outbound/{outbound.pk}/attachments/upload/",
                       {"file": upload, "title": "自动化测试附件"})
    after = OutboundAttachment.objects.filter(order=outbound).count()
    check("上传后重定向", resp.status_code == 302, f"实际 {resp.status_code}")
    check("附件记录 +1", after == before + 1, f"{before} -> {after}")

    att = OutboundAttachment.objects.filter(order=outbound).first()
    if att:
        check("文件已落盘", os.path.exists(att.file.path))
        check("文件名正确", att.filename == "领用凭证.txt", att.filename)
        check("大小可读", att.size_display.endswith(("B", "KB", "MB")), att.size_display)

        detail = client.get(f"/outbound/{outbound.pk}/")
        check("详情页显示附件", "领用凭证.txt" in detail.content.decode("utf-8"))

    print("\n三、附件类型校验")
    bad = SimpleUploadedFile("恶意.exe", b"MZ", content_type="application/octet-stream")
    resp = client.post(f"/outbound/{outbound.pk}/attachments/upload/",
                       {"file": bad, "title": "非法类型"})
    rejected = not OutboundAttachment.objects.filter(title="非法类型").exists()
    check("拒绝 .exe 附件", rejected and resp.status_code == 302)

    print("\n四、附件删除")
    if att:
        resp = client.post(f"/outbound/{outbound.pk}/attachments/{att.pk}/delete/")
        check("删除后重定向", resp.status_code == 302)
        check("记录已删除", not OutboundAttachment.objects.filter(pk=att.pk).exists())
        check("物理文件已删除", not os.path.exists(att.file.path))

    print(f"\n结果：通过 {ok} 项，失败 {fail} 项")
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
