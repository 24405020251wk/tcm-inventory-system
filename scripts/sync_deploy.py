"""把项目同步到一个干净的发布目录（剔除 .venv、日志、缓存），供公网部署使用。

用法：
    python scripts/sync_deploy.py

产物目录：与本项目同级的 deploy_web/
之所以不直接发布项目根目录：项目里的 .venv 有 190MB（Windows 版解释器），
上传到 Linux 沙箱毫无用处且会拖慢甚至拖挂部署。
"""

import shutil
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
TARGET = PROJECT.parent / "deploy_web"

# 需要发布的目录 / 文件（相对项目根）
INCLUDE_DIRS = [
    "config", "core", "accounts", "herbs", "inbound", "outbound", "inventory",
    "templates", "static",
]
INCLUDE_FILES = ["manage.py", "start.sh", "db.sqlite3"]

IGNORE = shutil.ignore_patterns(
    "__pycache__", "*.pyc", "*.pyo", ".DS_Store", "*.log", "staticfiles", ".venv",
)

# 发布环境只装必要依赖：pandas 体积大，统计页有纯 Python 兜底实现，故不装
DEPLOY_REQUIREMENTS = """\
Django>=5.2,<6.0
openpyxl>=3.1
"""


def main():
    if TARGET.exists():
        shutil.rmtree(TARGET)
    TARGET.mkdir(parents=True)

    for name in INCLUDE_DIRS:
        src = PROJECT / name
        if not src.is_dir():
            print(f"[skip] 目录不存在: {name}")
            continue
        shutil.copytree(src, TARGET / name, ignore=IGNORE)

    for name in INCLUDE_FILES:
        src = PROJECT / name
        if not src.exists():
            print(f"[skip] 文件不存在: {name}")
            continue
        shutil.copy2(src, TARGET / name)

    (TARGET / "requirements.txt").write_text(DEPLOY_REQUIREMENTS, encoding="utf-8")

    total = sum(f.stat().st_size for f in TARGET.rglob("*") if f.is_file())
    count = sum(1 for f in TARGET.rglob("*") if f.is_file())
    print(f"[ok] {TARGET}")
    print(f"     文件 {count} 个，合计 {total / 1024:.0f} KB")
    return 0


if __name__ == "__main__":
    sys.exit(main())
