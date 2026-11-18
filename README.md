# 中药材库存与批次管理系统

> 课程实践项目 · Python + Django + MySQL + Bootstrap + ECharts
> 覆盖「药材档案 → 入库批次 → 领用出库 → 库存查询统计」的完整可追溯业务闭环。

---

## 一、快速开始（PyCharm）

### 1. 打开项目

PyCharm → `File → Open`，选择本目录 `tcm_inventory_system`（**不是**它的上级目录）。

### 2. 配置解释器

项目已自带虚拟环境 `.venv`（Python 3.13 + Django 5.2）。

`File → Settings → Project: tcm_inventory_system → Python Interpreter → Add Interpreter → Add Local Interpreter → Existing`，
选择：

```
tcm_inventory_system\.venv\Scripts\python.exe
```

> 如果拷贝到其他电脑没有 `.venv`，在 PyCharm 底部 `Terminal` 执行：
>
> ```bash
> python -m venv .venv
> .venv\Scripts\activate
> pip install -r requirements.txt
> ```

### 3. 开启 Django 支持（PyCharm 专业版）

`Settings → Languages & Frameworks → Django`：

- 勾选 `Enable Django Support`
- Django project root：项目根目录
- Settings：`config/settings.py`
- Manage script：`manage.py`

社区版无需此步，直接用终端命令即可。

### 4. 初始化数据库

在 PyCharm Terminal（已激活 `.venv`）执行：

```bash
python manage.py migrate
python manage.py init_demo
```

`init_demo` 会创建菜单、角色、4 个演示账号、14 种药材、4 张已确认入库单和 5 张不同状态的出库单。

### 5. 运行

- 方式一：`python manage.py runserver`
- 方式二：PyCharm 右上角运行配置选择 `tcm_inventory_system`（PyCharm 会自动识别 `manage.py`）

浏览器访问 <http://127.0.0.1:8000>。

### 6. 演示账号

| 账号 | 密码 | 角色 | 可见功能 |
| --- | --- | --- | --- |
| `admin` | `admin123` | 超级管理员 | 全部功能 + Django 后台 `/admin/` |
| `keeper` | `keeper123` | 仓管员 | 档案、入库、出库申请、库存、统计 |
| `approver` | `approve123` | 审核员 | 出库审核、库存、统计 |
| `staff` | `staff123` | 普通员工 | 工作台、提交领用申请 |

---

## 二、功能与分工（5 人团队）

| 学生 | 功能模块 | 交付的功能点 | 主要代码 |
| --- | --- | --- | --- |
| 学生 1 | 用户与权限 | ① 注册 / 登录 / 退出 ② 角色与菜单权限 ③ 角色、菜单与接口权限配置 | `accounts/`、`core/permissions.py` |
| 学生 2 | 中药材档案 | ① 档案新增 ② 编辑、删除、详情 ③ 列表分页、筛选、排序、导出 | `herbs/` |
| 学生 3 | 入库与批次 | ① 入库单创建 ② 明细维护 ③ 查询与状态查看、批次生成 | `inbound/` |
| 学生 4 | 领用与出库 | ① 领用单创建 ② 审核 / 状态流转 ③ 异常备注、历史追溯 | `outbound/` |
| 学生 5 | 库存与统计 | ① 多条件查询 ② 统计图表 ③ 操作日志、导出打印 | `inventory/`、`core/` |

权限点与菜单一一对应（`Menu.code`），视图通过 `@menu_required("herb.list")` 校验，无权限返回 403 页面。

---

## 三、技术栈

- **后端**：Python 3.13、Django 5.2（MTV、ORM、Form/FormSet、模板继承）
- **数据库**：默认 SQLite（开箱即用），可一键切换 MySQL 8（PyMySQL 驱动）
- **前端**：Django Template + Bootstrap 5.3 + Bootstrap Icons + 原生 JavaScript
- **数据处理**：Pandas 做分类汇总与 Top10 统计，openpyxl 导出 Excel
- **可视化**：ECharts 5.5（分类占比、库存 Top10、出入库趋势）
- **安全**：CSRF 防护、密码哈希、登录校验、菜单级权限、操作日志审计

---

## 四、目录结构

```
tcm_inventory_system/
├── manage.py                 # 入口
├── requirements.txt
├── config/                   # 项目配置
│   ├── settings.py           # 数据库可在 SQLite / MySQL 间切换
│   └── urls.py
├── core/                     # 工作台、日志、权限装饰器、导出工具、演示数据命令
│   ├── permissions.py
│   ├── utils.py
│   ├── widgets.py
│   └── management/commands/init_demo.py
├── accounts/                 # 学生 1：用户 / 角色 / 菜单 / 登录注册
├── herbs/                    # 学生 2：药材档案与分类
├── inbound/                  # 学生 3：入库单、明细、批次
├── outbound/                 # 学生 4：领用单、审核流转
├── inventory/                # 学生 5：库存查询、批次、统计、流水、日志
├── templates/                # 全部页面模板（base.html 统一布局）
├── static/css|js             # 主题样式与表单联动脚本
├── scripts/                  # 冒烟测试、业务流程联调脚本
├── sql/tcm_inventory.sql     # MySQL 建表脚本（参考）
└── docs/                     # 数据库设计、功能说明、测试用例、分工说明
```

---

## 五、切换到 MySQL

1. 创建数据库（字符集必须为 `utf8mb4`）：

```sql
CREATE DATABASE tcm_inventory DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
```

2. 设置环境变量后启动（Windows PowerShell 示例）：

```powershell
$env:DB_ENGINE="mysql"
$env:DB_NAME="tcm_inventory"
$env:DB_USER="root"
$env:DB_PASSWORD="你的密码"
$env:DB_HOST="127.0.0.1"
$env:DB_PORT="3306"
python manage.py migrate
python manage.py init_demo
python manage.py runserver
```

PyCharm 中可在 `Run → Edit Configurations → Environment variables` 里配置同样的变量，避免每次手动设置。

也可参考 `sql/tcm_inventory.sql` 了解业务表结构（推荐仍以 `migrate` 建表为准）。

---

## 六、自测脚本

```bash
python scripts/smoke_test.py   # 22 项页面可访问性 + 权限校验
python scripts/flow_test.py    # 入库 → 批次 → 领用 → 审核 → 扣减库存 全链路
```

两个脚本均在当前演示库上运行，`flow_test.py` 结束时会自动清理测试数据。

---

## 七、开机自启与后台常驻

演示或验收时最常遇到的坑是：关掉命令行窗口，网站就打不开了（`runserver` 是前台进程，窗口关掉进程就没了）。项目根目录提供了一组脚本解决这个问题：

| 脚本 | 作用 | 说明 |
| --- | --- | --- |
| **`打开系统.bat`** | **日常就用这个** | 双击后静默启动服务并自动打开浏览器，全程无窗口 |
| `start_server.vbs` | 只启动、不开浏览器 | 通过 `serve.bat` 静默拉起服务，日志写入 `logs\server.log` |
| `serve.bat` | 底层启动脚本 | 清空 `PYTHONPATH`、重定向日志，由上面两个脚本调用 |
| `stop_server.bat` | 停止服务 | 自动查找占用 8000 端口的进程并结束 |
| `install_autostart.bat` | **安装开机自启** | 在「启动」文件夹写入一个启动项，下次登录 Windows 自动起服务（已默认装好） |
| `uninstall_autostart.bat` | 取消开机自启 | 删除上述启动项 |
| `watchdog.vbs` | 看门狗本体 | 无窗口常驻，每 60 秒检查 8000 端口，掉了立刻拉起；每次检查写一行 `OK` 或 `DOWN -> restarting` 到 `logs\watchdog.log` |
| `install_watchdog.bat` | **安装看门狗（推荐）** | 在「启动」文件夹写入第二个启动项并立即启动守护进程；**不需要管理员权限，不依赖计划任务** |
| `uninstall_watchdog.bat` | 卸载看门狗 | 删除自启项并结束守护进程 |
| `watchdog_batch.bat` | 看门狗的批处理版（备用） | 当 VBS 被安全策略拦截时使用；需要一个命令行窗口常开 |
| `run.bat` | 前台调试启动 | 会保留黑色窗口并自动打开浏览器，想实时看日志用这个 |

日常使用：双击 `打开系统.bat` 即可（它会同时拉起服务和看门狗）。开机自启 + 看门狗装好之后，连这一步都可以省掉——开机自动起来，中途挂了 60 秒内自动恢复，直接访问 <http://127.0.0.1:8000/> 就行。

验证守护进程是否在工作：

```bash
# 正常情况每 60 秒会多一行 OK
type logs\watchdog.log
```

排查启动失败时先看日志：

```bash
# 查看后台服务日志
type logs\server.log
```

> 注意：`serve.bat` 里有一行 `set "PYTHONPATH="`，用于清除本机被污染的环境变量，请勿删除，否则会报 `No module named 'encodings'`。

---

## 八、常见问题

| 问题 | 处理方式 |
| --- | --- |
| `ModuleNotFoundError: No module named 'django'` | 解释器选错，确认使用 `.venv\Scripts\python.exe`，或执行 `pip install -r requirements.txt` |
| 页面中文乱码 | 确认数据库字符集 `utf8mb4`，浏览器编码 UTF-8 |
| 端口 8000 被占用 | `python manage.py runserver 8001` |
| 统计页图表空白 | ECharts 走 CDN，需联网；离线可把 `echarts.min.js` 下载到 `static/js/` 后改引用 |
| 想重置演示数据 | `python manage.py init_demo --reset`（会清空业务数据，保留账号） |
| pandas 安装慢或失败 | 可先跳过，统计功能有纯 Python 兜底；或使用国内镜像 `-i https://pypi.tuna.tsinghua.edu.cn/simple` |

---

## 九、验收对照

- ① 不同角色登录并按其权限操作 —— 见权限矩阵与 403 页面
- ② 新增药材 → 关联入库与批次 → 领用与出库状态处理 —— 见 `scripts/flow_test.py`
- ③ 多条件检索、查看统计、导出记录 —— 见库存查询 / 统计分析 / 各列表导出
- 可运行源码、`requirements.txt`、数据库脚本、URL 与视图说明、测试用例 —— 见本文件与 `docs/`

---

## 十、公网访问（异地演示）

本地 `127.0.0.1:8000` 只有本机能开。要在别的城市、别的网络、手机 4G 上打开，需要把项目发布到公网。项目已内置发布支持，改动只有三处：

| 文件 | 作用 |
| --- | --- |
| `core/middleware.py` | 公网域名不固定，按请求来源动态补 CSRF 白名单，避免外网登录报 403 |
| `config/settings.py` | 新增 `DYNAMIC_CSRF_ORIGINS` 开关与 `CSRF_TRUSTED_ORIGINS` 环境变量支持 |
| `start.sh` | 发布环境的启动入口：`migrate` → `init_demo`（幂等） → 监听 `0.0.0.0:$PORT` |

发布用脚本 `scripts/sync_deploy.py` 生成干净目录（剔除 190MB 的 `.venv`），再上传：

```bash
python scripts/sync_deploy.py     # 生成同级目录 deploy_web/
```

发布后访问的是云端沙箱里的实例，**与本机是否开机无关**；本地开发照旧用 `run.bat` / `打开系统.bat`。

> 注意：发布用的是演示库，重新发布会把线上数据重置为演示数据；公网可访问时演示账号用的是极简口令（与本地一致），不要往里放真实数据，正式使用请先在「个人中心」改掉。
