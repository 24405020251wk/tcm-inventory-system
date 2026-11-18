"""一键初始化演示数据：菜单、角色、用户、药材档案、入库批次、出库单。

用法：
    python manage.py init_demo          # 首次初始化
    python manage.py init_demo --reset  # 清空业务数据后重建（保留迁移表）
"""
import datetime as dt
import random
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from accounts.models import Menu, Role, RoleMenu, User
from herbs.models import Herb, HerbCategory
from inbound.models import Batch, InboundItem, InboundOrder
from inventory.models import StockLedger
from outbound.models import OutboundItem, OutboundOrder

MENUS = [
    # code, 名称, 分组, 路由名, 图标, 接口权限标识, 排序
    ("dashboard", "工作台", "工作台", "core:dashboard", "bi-grid-1x2", "GET:/", 10),
    ("herb.list", "药材档案", "业务管理", "herbs:list", "bi-journal-medical", "GET:/herbs/", 10),
    ("inbound.list", "入库管理", "业务管理", "inbound:list", "bi-box-arrow-in-down", "GET:/inbound/", 20),
    ("outbound.list", "领用出库", "业务管理", "outbound:list", "bi-box-arrow-up", "GET:/outbound/", 30),
    ("outbound.approve", "出库审核", "业务管理", "", "bi-check2-square", "POST:/outbound/<id>/approve/", 40),
    ("inventory.stock", "库存查询", "库存管理", "inventory:stock", "bi-box-seam", "GET:/inventory/stock/", 10),
    ("inventory.stats", "统计分析", "库存管理", "inventory:stats", "bi-bar-chart-line", "GET:/inventory/stats/", 20),
    ("inventory.log", "操作日志", "库存管理", "inventory:logs", "bi-clock-history", "GET:/inventory/logs/", 30),
    ("system.user", "用户管理", "系统管理", "accounts:user_list", "bi-people", "GET:/accounts/users/", 10),
    ("system.role", "角色权限", "系统管理", "accounts:role_list", "bi-shield-lock", "GET:/accounts/roles/", 20),
    ("system.menu", "菜单管理", "系统管理", "accounts:menu_list", "bi-list-nested", "GET:/accounts/menus/", 30),
]

ROLES = {
    "superadmin": ("超级管理员", "拥有全部功能权限", None),  # None 表示全部菜单
    "keeper": ("仓管员", "负责档案维护、入库登记与库存查询",
               ["dashboard", "herb.list", "inbound.list", "outbound.list",
                "inventory.stock", "inventory.stats"]),
    "approver": ("审核员", "负责出库审核与统计查看",
                 ["dashboard", "outbound.list", "outbound.approve",
                  "inventory.stock", "inventory.stats"]),
    "staff": ("普通员工", "仅可查看工作台并提交领用申请",
              ["dashboard", "outbound.list"]),
}

CATEGORIES = [
    ("根茎类", "root", 10), ("花叶类", "flower", 20), ("果实种子类", "fruit", 30),
    ("全草类", "whole", 40), ("菌藻类", "fungus", 50),
]

HERBS = [
    # 编码, 名称, 拼音, 分类, 规格, 单位, 产地, 保质期, 下限, 单价
    ("YC-0001", "黄芪", "huangqi", "根茎类", "统货", "kg", "甘肃陇西", 730, 50, 68),
    ("YC-0002", "当归", "danggui", "根茎类", "一级", "kg", "甘肃岷县", 730, 30, 96),
    ("YC-0003", "党参", "dangshen", "根茎类", "统货", "kg", "山西长治", 540, 30, 74),
    ("YC-0004", "甘草", "gancao", "根茎类", "切片", "kg", "内蒙古", 730, 40, 42),
    ("YC-0005", "白术", "baizhu", "根茎类", "统货", "kg", "浙江磐安", 720, 25, 58),
    ("YC-0006", "茯苓", "fuling", "菌藻类", "白片", "kg", "云南普洱", 900, 20, 45),
    ("YC-0007", "金银花", "jinyinhua", "花叶类", "一级", "kg", "河南封丘", 365, 15, 210),
    ("YC-0008", "菊花", "juhua", "花叶类", "统货", "kg", "安徽亳州", 365, 15, 88),
    ("YC-0009", "枸杞子", "gouqizi", "果实种子类", "宁夏统货", "kg", "宁夏中宁", 540, 20, 76),
    ("YC-0010", "陈皮", "chenpi", "果实种子类", "三年陈", "kg", "广东新会", 1080, 20, 120),
    ("YC-0011", "麦冬", "maidong", "根茎类", "统货", "kg", "四川绵阳", 540, 20, 92),
    ("YC-0012", "丹参", "danshen", "根茎类", "切片", "kg", "山东临沂", 720, 25, 54),
    ("YC-0013", "薄荷", "bohe", "全草类", "统货", "kg", "江苏南通", 365, 10, 36),
    ("YC-0014", "益母草", "yimucao", "全草类", "统货", "kg", "河北安国", 365, 10, 28),
]


class Command(BaseCommand):
    help = "初始化中药材库存与批次管理系统的演示数据"

    def add_arguments(self, parser):
        parser.add_argument("--reset", action="store_true", help="清空业务数据后重新生成")

    @transaction.atomic
    def handle(self, *args, **options):
        if options["reset"]:
            StockLedger.objects.all().delete()
            OutboundItem.objects.all().delete()
            OutboundOrder.objects.all().delete()
            InboundItem.objects.all().delete()
            InboundOrder.objects.all().delete()
            Batch.objects.all().delete()
            Herb.objects.all().delete()
            HerbCategory.objects.all().delete()
            self.stdout.write(self.style.WARNING("已清空业务数据"))

        menus = self._seed_menus()
        roles = self._seed_roles(menus)
        self._seed_users(roles)
        self._seed_herbs()
        self._seed_inbound()
        self._seed_outbound()
        self._seed_logs()

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("演示数据初始化完成！"))
        self.stdout.write("  管理员   admin    / admin123")
        self.stdout.write("  仓管员   keeper   / keeper123")
        self.stdout.write("  审核员   approver / approve123")
        self.stdout.write("  普通员工 staff    / staff123")
        self.stdout.write("")
        self.stdout.write("启动服务：python manage.py runserver")

    # ------------------------------------------------------------------
    def _seed_menus(self):
        menus = {}
        for code, name, group, url_name, icon, api_scope, sort in MENUS:
            menu, _ = Menu.objects.update_or_create(
                code=code,
                defaults={"name": name, "group_name": group, "url_name": url_name,
                          "icon": icon, "api_scope": api_scope, "sort": sort,
                          "is_active": True},
            )
            menus[code] = menu
        self.stdout.write(f"菜单：{len(menus)} 项")
        return menus

    def _seed_roles(self, menus):
        roles = {}
        for code, (name, description, codes) in ROLES.items():
            role, _ = Role.objects.update_or_create(
                code=code,
                defaults={"name": name, "description": description, "is_active": True},
            )
            RoleMenu.objects.filter(role=role).delete()
            target = menus.values() if codes is None else [menus[c] for c in codes if c in menus]
            RoleMenu.objects.bulk_create([RoleMenu(role=role, menu=m) for m in target])
            roles[code] = role
        self.stdout.write(f"角色：{len(roles)} 个")
        return roles

    def _seed_users(self, roles):
        accounts = [
            ("admin", "系统管理员", "13800000001", "信息科", roles["superadmin"], "admin123", True),
            ("keeper", "李仓储", "13800000002", "仓储部", roles["keeper"], "keeper123", False),
            ("approver", "王审核", "13800000003", "药剂科", roles["approver"], "approve123", False),
            ("staff", "赵医师", "13800000004", "中医内科", roles["staff"], "staff123", False),
        ]
        for username, real_name, phone, dept, role, password, is_super in accounts:
            user, created = User.objects.get_or_create(
                username=username,
                defaults={"real_name": real_name, "phone": phone, "department": dept,
                          "role": role, "is_staff": is_super, "is_superuser": is_super},
            )
            if created:
                user.set_password(password)
                user.save()
            else:
                user.real_name = real_name
                user.phone = phone
                user.department = dept
                user.role = role
                user.is_superuser = is_super
                user.is_staff = is_super
                user.save()
        self.stdout.write(f"用户：{len(accounts)} 个")

    def _seed_herbs(self):
        if Herb.objects.exists():
            self.stdout.write("药材档案已存在，跳过")
            return
        categories = {}
        for name, code, sort in CATEGORIES:
            category, _ = HerbCategory.objects.get_or_create(
                code=code, defaults={"name": name, "sort": sort})
            categories[name] = category
        for code, name, pinyin, cat, spec, unit, origin, days, min_stock, price in HERBS:
            Herb.objects.create(
                code=code, name=name, pinyin=pinyin, category=categories[cat],
                spec=spec, unit=unit, origin=origin, shelf_life_days=days,
                min_stock=Decimal(str(min_stock)), price=Decimal(str(price)),
                storage_condition="阴凉干燥处，防潮防蛀",
            )
        self.stdout.write(f"药材档案：{len(HERBS)} 种")

    def _inbound_orders(self):
        today = dt.date.today()
        keeper = User.objects.get(username="keeper")
        plans = [
            ("亳州中药材批发有限公司", today - dt.timedelta(days=75), [
                ("YC-0001", 200, 62), ("YC-0002", 120, 92), ("YC-0004", 150, 40),
            ]),
            ("陇西参茸药材行", today - dt.timedelta(days=45), [
                ("YC-0003", 100, 70), ("YC-0005", 80, 56), ("YC-0011", 90, 88),
            ]),
            ("安国市本草药业", today - dt.timedelta(days=18), [
                ("YC-0006", 60, 43), ("YC-0012", 70, 52), ("YC-0013", 40, 34),
            ]),
            ("宁夏中宁枸杞合作社", today - dt.timedelta(days=5), [
                ("YC-0009", 80, 72), ("YC-0010", 50, 116),
            ]),
        ]
        orders = []
        seq = 1
        for supplier, inbound_date, items in plans:
            order = InboundOrder.objects.create(
                order_no=f"RK{inbound_date:%Y%m%d}{seq:03d}",
                supplier=supplier, inbound_date=inbound_date, operator=keeper,
                remark="示范数据", status="draft",
            )
            seq += 1
            for idx, (code, qty, price) in enumerate(items, start=1):
                herb = Herb.objects.get(code=code)
                production = inbound_date - dt.timedelta(days=random.randint(20, 120))
                expiry = production + dt.timedelta(days=herb.shelf_life_days)
                InboundItem.objects.create(
                    order=order, herb=herb,
                    batch_no=f"PC{production:%Y%m%d}-{herb.code}-{idx}",
                    production_date=production, expiry_date=expiry,
                    quantity=Decimal(str(qty)), unit_price=Decimal(str(price)),
                )
            order.confirm(keeper)
            StockLedger.objects.filter(ref_no=order.order_no).update(
                created_at=timezone.make_aware(
                    dt.datetime.combine(inbound_date, dt.time(9, 30))
                ) if timezone.is_aware(timezone.now()) else dt.datetime.combine(
                    inbound_date, dt.time(9, 30))
            )
            orders.append(order)
        self.stdout.write(f"入库单：{len(orders)} 张（已确认）")
        return orders

    def _seed_inbound(self):
        if InboundOrder.objects.exists():
            self.stdout.write("入库单已存在，跳过")
            return
        self._inbound_orders()

    def _seed_outbound(self):
        if OutboundOrder.objects.exists():
            self.stdout.write("出库单已存在，跳过")
            return
        today = dt.date.today()
        approver = User.objects.get(username="approver")
        staff = User.objects.get(username="staff")

        plans = [
            # 部门, 用途, 申请日期, 明细[(药材, 数量)], 状态, 异常备注
            ("中药房", "门诊调剂常规备货", today - dt.timedelta(days=60),
             [("YC-0001", 30), ("YC-0004", 25)], "approved", ""),
            ("制剂室", "院内制剂生产", today - dt.timedelta(days=30),
             [("YC-0002", 18), ("YC-0003", 12)], "approved", ""),
            ("中医内科", "专家门诊用药", today - dt.timedelta(days=3),
             [("YC-0007", 5), ("YC-0009", 8)], "pending", "其中 1kg 包装破损，需换货"),
            ("教学实验中心", "中药鉴定实验课", today - dt.timedelta(days=1),
             [("YC-0013", 6), ("YC-0014", 4)], "draft", ""),
            ("中药房", "夏季防暑方调剂", today - dt.timedelta(days=12),
             [("YC-0008", 6), ("YC-0010", 4)], "pending", ""),
        ]

        seq = 1
        for dept, purpose, apply_date, items, status, exception in plans:
            order = OutboundOrder.objects.create(
                order_no=f"CK{apply_date:%Y%m%d}{seq:03d}",
                department=dept, purpose=purpose, applicant=staff,
                apply_date=apply_date, exception_note=exception,
                remark="示范数据" if status != "draft" else "草稿待完善",
            )
            seq += 1
            for code, qty in items:
                herb = Herb.objects.get(code=code)
                OutboundItem.objects.create(order=order, herb=herb,
                                            quantity=Decimal(str(qty)))
            if status in ("pending", "approved"):
                order.submit()
            if status == "approved":
                order.approve(approver, "同意领用，请规范使用")
                ledgers = StockLedger.objects.filter(ref_no=order.order_no)
                stamp = dt.datetime.combine(apply_date, dt.time(14, 20))
                if timezone.is_aware(timezone.now()):
                    stamp = timezone.make_aware(stamp)
                ledgers.update(created_at=stamp, operator=approver)
                OutboundOrder.objects.filter(pk=order.pk).update(
                    approve_time=stamp, created_at=stamp - dt.timedelta(hours=4))
        self.stdout.write(f"出库单：{len(plans)} 张（含已出库、待审核、草稿）")

    def _seed_logs(self):
        """生成与业务单据对应的历史操作日志，便于演示「全程留痕」。"""
        from core.models import OperationLog

        if OperationLog.objects.exists():
            self.stdout.write("操作日志已存在，跳过")
            return

        created = []
        for order in InboundOrder.objects.filter(status="confirmed").order_by("inbound_date"):
            log = OperationLog.objects.create(
                user=order.operator, username=order.operator.username, module="inbound",
                action="确认入库", target=order.order_no,
                detail=f"供应商 {order.supplier}，生成批次 {order.items.count()} 个",
                ip="127.0.0.1",
            )
            stamp = dt.datetime.combine(order.inbound_date, dt.time(9, 35))
            OperationLog.objects.filter(pk=log.pk).update(created_at=stamp)
            created.append(log.pk)

        for order in OutboundOrder.objects.filter(status="approved").order_by("apply_date"):
            log = OperationLog.objects.create(
                user=order.approver, username=order.approver.username, module="outbound",
                action="审核通过并出库", target=order.order_no,
                detail=f"{order.department} 领用，扣减批次库存",
                ip="127.0.0.1",
            )
            if order.approve_time:
                OperationLog.objects.filter(pk=log.pk).update(created_at=order.approve_time)
            created.append(log.pk)

        admin = User.objects.filter(username="admin").first()
        if admin:
            log = OperationLog.objects.create(
                user=admin, username="admin", module="auth",
                action="登录系统", target="admin", ip="127.0.0.1",
            )
            OperationLog.objects.filter(pk=log.pk).update(
                created_at=timezone.now() - dt.timedelta(hours=2))
        self.stdout.write(f"操作日志：{len(created) + 1} 条")
