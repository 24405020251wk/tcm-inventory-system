"""配置文件包：启用 PyMySQL 作为 MySQL 驱动（免编译）。"""
try:
    import pymysql

    pymysql.install_as_MySQLdb()
except ImportError:  # 未安装 PyMySQL 时忽略，使用 SQLite 不受影响
    pass
