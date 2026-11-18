-- =============================================================
-- 中药材库存与批次管理系统 · MySQL 8 建表脚本（参考）
-- 说明：推荐直接执行 `python manage.py migrate` 由 Django 建表；
--       本脚本用于数据库结构说明、课程报告附录或手工建库对照。
-- 字符集：utf8mb4，存储引擎：InnoDB
-- =============================================================

CREATE DATABASE IF NOT EXISTS `tcm_inventory`
    DEFAULT CHARACTER SET utf8mb4
    COLLATE utf8mb4_general_ci;

USE `tcm_inventory`;

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- -------------------------------------------------------------
-- 1. 角色
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `accounts_role` (
    `id`          bigint       NOT NULL AUTO_INCREMENT,
    `name`        varchar(50)  NOT NULL COMMENT '角色名称',
    `code`        varchar(50)  NOT NULL COMMENT '角色编码',
    `description` varchar(200) NOT NULL DEFAULT '' COMMENT '角色说明',
    `is_active`   tinyint(1)   NOT NULL DEFAULT 1 COMMENT '是否启用',
    `created_at`  datetime     NOT NULL COMMENT '创建时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_role_name` (`name`),
    UNIQUE KEY `uk_role_code` (`code`)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COMMENT = '角色';

-- -------------------------------------------------------------
-- 2. 菜单 / 权限点
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `accounts_menu` (
    `id`         bigint       NOT NULL AUTO_INCREMENT,
    `code`       varchar(50)  NOT NULL COMMENT '权限编码，如 herb.list',
    `name`       varchar(50)  NOT NULL COMMENT '菜单名称',
    `group_name` varchar(20)  NOT NULL DEFAULT '业务管理' COMMENT '菜单分组',
    `url_name`   varchar(80)  NOT NULL DEFAULT '' COMMENT 'Django 路由名',
    `icon`       varchar(40)  NOT NULL DEFAULT 'bi-circle' COMMENT '图标类名',
    `api_scope`  varchar(120) NOT NULL DEFAULT '' COMMENT '接口权限标识',
    `sort`       int          NOT NULL DEFAULT 10 COMMENT '排序',
    `is_active`  tinyint(1)   NOT NULL DEFAULT 1 COMMENT '是否启用',
    `created_at` datetime     NOT NULL,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_menu_code` (`code`)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COMMENT = '菜单与权限点';

-- -------------------------------------------------------------
-- 3. 用户
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `accounts_user` (
    `id`           bigint       NOT NULL AUTO_INCREMENT,
    `password`     varchar(128) NOT NULL COMMENT '密码哈希',
    `last_login`   datetime     NULL,
    `is_superuser` tinyint(1)   NOT NULL DEFAULT 0,
    `username`     varchar(150) NOT NULL COMMENT '登录账号',
    `first_name`   varchar(150) NOT NULL DEFAULT '',
    `last_name`    varchar(150) NOT NULL DEFAULT '',
    `email`        varchar(254) NOT NULL DEFAULT '',
    `is_staff`     tinyint(1)   NOT NULL DEFAULT 0,
    `is_active`    tinyint(1)   NOT NULL DEFAULT 1 COMMENT '是否启用',
    `date_joined`  datetime     NOT NULL,
    `real_name`    varchar(50)  NOT NULL DEFAULT '' COMMENT '姓名',
    `phone`        varchar(20)  NOT NULL DEFAULT '' COMMENT '手机号',
    `department`   varchar(50)  NOT NULL DEFAULT '' COMMENT '部门',
    `role_id`      bigint       NULL COMMENT '角色',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_user_username` (`username`),
    KEY `idx_user_role` (`role_id`),
    CONSTRAINT `fk_user_role` FOREIGN KEY (`role_id`) REFERENCES `accounts_role` (`id`) ON DELETE SET NULL
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COMMENT = '用户';

-- -------------------------------------------------------------
-- 4. 角色-菜单授权
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `accounts_rolemenu` (
    `id`         bigint   NOT NULL AUTO_INCREMENT,
    `role_id`    bigint   NOT NULL,
    `menu_id`    bigint   NOT NULL,
    `created_at` datetime NOT NULL,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_role_menu` (`role_id`, `menu_id`),
    KEY `idx_rolemenu_menu` (`menu_id`),
    CONSTRAINT `fk_rolemenu_role` FOREIGN KEY (`role_id`) REFERENCES `accounts_role` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_rolemenu_menu` FOREIGN KEY (`menu_id`) REFERENCES `accounts_menu` (`id`) ON DELETE CASCADE
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COMMENT = '角色菜单授权';

-- -------------------------------------------------------------
-- 5. 药材分类
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `herbs_herbcategory` (
    `id`     bigint      NOT NULL AUTO_INCREMENT,
    `name`   varchar(50) NOT NULL COMMENT '分类名称',
    `code`   varchar(30) NOT NULL COMMENT '分类编码',
    `sort`   int         NOT NULL DEFAULT 10,
    `remark` varchar(200) NOT NULL DEFAULT '',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_category_name` (`name`),
    UNIQUE KEY `uk_category_code` (`code`)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COMMENT = '药材分类';

-- -------------------------------------------------------------
-- 6. 中药材档案
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `herbs_herb` (
    `id`                bigint        NOT NULL AUTO_INCREMENT,
    `code`              varchar(30)   NOT NULL COMMENT '药材编码',
    `name`              varchar(60)   NOT NULL COMMENT '药材名称',
    `pinyin`            varchar(60)   NOT NULL DEFAULT '' COMMENT '拼音助记码',
    `category_id`       bigint        NOT NULL COMMENT '分类',
    `spec`              varchar(60)   NOT NULL DEFAULT '' COMMENT '规格',
    `unit`              varchar(10)   NOT NULL DEFAULT 'kg',
    `origin`            varchar(60)   NOT NULL DEFAULT '' COMMENT '产地',
    `shelf_life_days`   int           NOT NULL DEFAULT 730 COMMENT '保质期（天）',
    `storage_condition` varchar(100)  NOT NULL DEFAULT '阴凉干燥处',
    `min_stock`         decimal(12,2) NOT NULL DEFAULT 10.00 COMMENT '库存下限',
    `price`             decimal(12,2) NOT NULL DEFAULT 0.00 COMMENT '参考单价',
    `status`            varchar(10)   NOT NULL DEFAULT 'active' COMMENT 'active/inactive',
    `remark`            varchar(200)  NOT NULL DEFAULT '',
    `created_at`        datetime      NOT NULL,
    `updated_at`        datetime      NOT NULL,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_herb_code` (`code`),
    KEY `idx_herb_name` (`name`),
    KEY `idx_herb_pinyin` (`pinyin`),
    KEY `idx_herb_category` (`category_id`),
    CONSTRAINT `fk_herb_category` FOREIGN KEY (`category_id`) REFERENCES `herbs_herbcategory` (`id`) ON DELETE RESTRICT
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COMMENT = '中药材档案';

-- -------------------------------------------------------------
-- 7. 入库单
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `inbound_inboundorder` (
    `id`           bigint      NOT NULL AUTO_INCREMENT,
    `order_no`     varchar(40) NOT NULL COMMENT '入库单号',
    `supplier`     varchar(80) NOT NULL COMMENT '供应商',
    `inbound_date` date        NOT NULL COMMENT '入库日期',
    `operator_id`  bigint      NOT NULL COMMENT '经办人',
    `status`       varchar(10) NOT NULL DEFAULT 'draft' COMMENT 'draft/confirmed/cancelled',
    `remark`       varchar(200) NOT NULL DEFAULT '',
    `created_at`   datetime    NOT NULL,
    `confirmed_at` datetime    NULL,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_inbound_no` (`order_no`),
    KEY `idx_inbound_operator` (`operator_id`),
    CONSTRAINT `fk_inbound_operator` FOREIGN KEY (`operator_id`) REFERENCES `accounts_user` (`id`) ON DELETE RESTRICT
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COMMENT = '入库单';

-- -------------------------------------------------------------
-- 8. 库存批次
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `inbound_batch` (
    `id`                 bigint        NOT NULL AUTO_INCREMENT,
    `batch_no`           varchar(50)   NOT NULL COMMENT '批次号',
    `herb_id`            bigint        NOT NULL,
    `production_date`    date          NULL,
    `expiry_date`        date          NULL,
    `quantity`           decimal(12,2) NOT NULL DEFAULT 0.00 COMMENT '入库数量',
    `remaining_quantity` decimal(12,2) NOT NULL DEFAULT 0.00 COMMENT '剩余数量',
    `unit_price`         decimal(12,2) NOT NULL DEFAULT 0.00,
    `supplier`           varchar(80)   NOT NULL DEFAULT '',
    `status`             varchar(10)   NOT NULL DEFAULT 'active' COMMENT 'active/exhausted/expired',
    `created_at`         datetime      NOT NULL,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_batch_no` (`batch_no`),
    KEY `idx_batch_herb_status` (`herb_id`, `status`),
    CONSTRAINT `fk_batch_herb` FOREIGN KEY (`herb_id`) REFERENCES `herbs_herb` (`id`) ON DELETE RESTRICT
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COMMENT = '库存批次';

-- -------------------------------------------------------------
-- 9. 入库明细
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `inbound_inbounditem` (
    `id`              bigint        NOT NULL AUTO_INCREMENT,
    `order_id`        bigint        NOT NULL,
    `herb_id`         bigint        NOT NULL,
    `batch_no`        varchar(50)   NOT NULL DEFAULT '' COMMENT '批次号（空则自动生成）',
    `production_date` date          NULL,
    `expiry_date`     date          NULL,
    `quantity`        decimal(12,2) NOT NULL,
    `unit_price`      decimal(12,2) NOT NULL DEFAULT 0.00,
    `batch_id`        bigint        NULL COMMENT '确认后关联批次',
    PRIMARY KEY (`id`),
    KEY `idx_item_order` (`order_id`),
    KEY `idx_item_herb` (`herb_id`),
    KEY `idx_item_batch` (`batch_id`),
    CONSTRAINT `fk_item_order` FOREIGN KEY (`order_id`) REFERENCES `inbound_inboundorder` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_item_herb` FOREIGN KEY (`herb_id`) REFERENCES `herbs_herb` (`id`) ON DELETE RESTRICT,
    CONSTRAINT `fk_item_batch` FOREIGN KEY (`batch_id`) REFERENCES `inbound_batch` (`id`) ON DELETE SET NULL
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COMMENT = '入库明细';

-- -------------------------------------------------------------
-- 10. 出库单
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `outbound_outboundorder` (
    `id`             bigint       NOT NULL AUTO_INCREMENT,
    `order_no`       varchar(40)  NOT NULL COMMENT '出库单号',
    `department`     varchar(60)  NOT NULL COMMENT '领用部门',
    `purpose`        varchar(120) NOT NULL DEFAULT '' COMMENT '领用用途',
    `applicant_id`   bigint       NOT NULL COMMENT '申请人',
    `apply_date`     date         NOT NULL COMMENT '申请日期',
    `status`         varchar(10)  NOT NULL DEFAULT 'draft' COMMENT 'draft/pending/approved/rejected/cancelled',
    `approver_id`    bigint       NULL COMMENT '审核人',
    `approve_time`   datetime     NULL,
    `approve_remark` varchar(200) NOT NULL DEFAULT '' COMMENT '审核意见',
    `exception_note` text         NOT NULL COMMENT '异常备注',
    `remark`         varchar(200) NOT NULL DEFAULT '',
    `created_at`     datetime     NOT NULL,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_outbound_no` (`order_no`),
    KEY `idx_outbound_applicant` (`applicant_id`),
    KEY `idx_outbound_approver` (`approver_id`),
    CONSTRAINT `fk_outbound_applicant` FOREIGN KEY (`applicant_id`) REFERENCES `accounts_user` (`id`) ON DELETE RESTRICT,
    CONSTRAINT `fk_outbound_approver` FOREIGN KEY (`approver_id`) REFERENCES `accounts_user` (`id`) ON DELETE SET NULL
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COMMENT = '出库单';

-- -------------------------------------------------------------
-- 11. 出库明细
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `outbound_outbounditem` (
    `id`       bigint        NOT NULL AUTO_INCREMENT,
    `order_id` bigint        NOT NULL,
    `herb_id`  bigint        NOT NULL,
    `batch_id` bigint        NULL COMMENT '指定批次，空则近效期优先',
    `quantity` decimal(12,2) NOT NULL,
    `remark`   varchar(120)  NOT NULL DEFAULT '',
    PRIMARY KEY (`id`),
    KEY `idx_oitem_order` (`order_id`),
    KEY `idx_oitem_herb` (`herb_id`),
    KEY `idx_oitem_batch` (`batch_id`),
    CONSTRAINT `fk_oitem_order` FOREIGN KEY (`order_id`) REFERENCES `outbound_outboundorder` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_oitem_herb` FOREIGN KEY (`herb_id`) REFERENCES `herbs_herb` (`id`) ON DELETE RESTRICT,
    CONSTRAINT `fk_oitem_batch` FOREIGN KEY (`batch_id`) REFERENCES `inbound_batch` (`id`) ON DELETE SET NULL
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COMMENT = '出库明细';

-- -------------------------------------------------------------
-- 12. 库存流水
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `inventory_stockledger` (
    `id`         bigint        NOT NULL AUTO_INCREMENT,
    `herb_id`    bigint        NOT NULL,
    `batch_id`   bigint        NULL,
    `biz_type`   varchar(10)   NOT NULL COMMENT 'in/out/adjust',
    `change_qty` decimal(12,2) NOT NULL COMMENT '变动数量（入库正、出库负）',
    `before_qty` decimal(12,2) NOT NULL DEFAULT 0.00,
    `after_qty`  decimal(12,2) NOT NULL DEFAULT 0.00,
    `ref_no`     varchar(40)   NOT NULL DEFAULT '' COMMENT '关联单号',
    `operator_id` bigint       NULL,
    `remark`     varchar(200)  NOT NULL DEFAULT '',
    `created_at` datetime      NOT NULL,
    PRIMARY KEY (`id`),
    KEY `idx_ledger_herb_time` (`herb_id`, `created_at`),
    KEY `idx_ledger_batch` (`batch_id`),
    KEY `idx_ledger_operator` (`operator_id`),
    CONSTRAINT `fk_ledger_herb` FOREIGN KEY (`herb_id`) REFERENCES `herbs_herb` (`id`) ON DELETE RESTRICT,
    CONSTRAINT `fk_ledger_batch` FOREIGN KEY (`batch_id`) REFERENCES `inbound_batch` (`id`) ON DELETE SET NULL,
    CONSTRAINT `fk_ledger_operator` FOREIGN KEY (`operator_id`) REFERENCES `accounts_user` (`id`) ON DELETE SET NULL
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COMMENT = '库存流水';

-- -------------------------------------------------------------
-- 13. 操作日志
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `core_operationlog` (
    `id`         bigint       NOT NULL AUTO_INCREMENT,
    `user_id`    bigint       NULL,
    `username`   varchar(150) NOT NULL DEFAULT '' COMMENT '操作人账号快照',
    `module`     varchar(20)  NOT NULL DEFAULT 'inventory',
    `action`     varchar(100) NOT NULL,
    `target`     varchar(150) NOT NULL DEFAULT '',
    `detail`     text         NOT NULL,
    `ip`         char(39)     NULL,
    `created_at` datetime     NOT NULL,
    PRIMARY KEY (`id`),
    KEY `idx_log_module_time` (`module`, `created_at`),
    KEY `idx_log_user` (`user_id`),
    CONSTRAINT `fk_log_user` FOREIGN KEY (`user_id`) REFERENCES `accounts_user` (`id`) ON DELETE SET NULL
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COMMENT = '操作日志';

SET FOREIGN_KEY_CHECKS = 1;

-- -------------------------------------------------------------
-- 初始化菜单（与 init_demo 命令一致）
-- -------------------------------------------------------------
INSERT IGNORE INTO `accounts_menu`
(`code`, `name`, `group_name`, `url_name`, `icon`, `api_scope`, `sort`, `is_active`, `created_at`)
VALUES
('dashboard',        '工作台',   '工作台',   'core:dashboard',     'bi-grid-1x2',          'GET:/',                              10, 1, NOW()),
('herb.list',        '药材档案', '业务管理', 'herbs:list',         'bi-journal-medical',   'GET:/herbs/',                        10, 1, NOW()),
('inbound.list',     '入库管理', '业务管理', 'inbound:list',       'bi-box-arrow-in-down', 'GET:/inbound/',                      20, 1, NOW()),
('outbound.list',    '领用出库', '业务管理', 'outbound:list',      'bi-box-arrow-up',      'GET:/outbound/',                     30, 1, NOW()),
('outbound.approve', '出库审核', '业务管理', '',      'bi-check2-square',     'POST:/outbound/<id>/approve/',       40, 1, NOW()),
('inventory.stock',  '库存查询', '库存管理', 'inventory:stock',    'bi-box-seam',          'GET:/inventory/stock/',              10, 1, NOW()),
('inventory.stats',  '统计分析', '库存管理', 'inventory:stats',    'bi-bar-chart-line',    'GET:/inventory/stats/',              20, 1, NOW()),
('inventory.log',    '操作日志', '库存管理', 'inventory:logs',     'bi-clock-history',     'GET:/inventory/logs/',               30, 1, NOW()),
('system.user',      '用户管理', '系统管理', 'accounts:user_list', 'bi-people',            'GET:/accounts/users/',               10, 1, NOW()),
('system.role',      '角色权限', '系统管理', 'accounts:role_list', 'bi-shield-lock',       'GET:/accounts/roles/',               20, 1, NOW()),
('system.menu',      '菜单管理', '系统管理', 'accounts:menu_list', 'bi-list-nested',       'GET:/accounts/menus/',               30, 1, NOW());

-- 提示：账号、角色与演示业务数据请执行 `python manage.py init_demo` 生成，
-- 其中包含密码哈希，直接用 SQL 插入明文密码无法登录。
