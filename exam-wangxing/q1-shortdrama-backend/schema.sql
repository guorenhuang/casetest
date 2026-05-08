-- Q1 短剧会员订阅 — SQLite 表结构（订单 / 订阅 / 支付事件 + 套餐库存）
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS plans (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    price_cents INTEGER NOT NULL,
    currency TEXT NOT NULL DEFAULT 'cny',
    duration_days INTEGER NOT NULL,
    stock_remaining INTEGER NOT NULL DEFAULT 1000
);

CREATE TABLE IF NOT EXISTS orders (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    plan_id TEXT NOT NULL REFERENCES plans(id),
    idempotency_key TEXT NOT NULL,
    status TEXT NOT NULL,
    amount_cents INTEGER NOT NULL,
    currency TEXT NOT NULL DEFAULT 'cny',
    channel_hint TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE (idempotency_key)
);

CREATE INDEX IF NOT EXISTS idx_orders_user ON orders(user_id);
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);

CREATE TABLE IF NOT EXISTS subscriptions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id TEXT NOT NULL UNIQUE REFERENCES orders(id) ON DELETE CASCADE,
    user_id TEXT NOT NULL,
    status TEXT NOT NULL,
    current_period_start TEXT,
    current_period_end TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_subs_user ON subscriptions(user_id);

-- 幂等去重：同一渠道 + 外部事件 ID 唯一；Stripe: evt_*, Apple: notificationUUID / transaction id
CREATE TABLE IF NOT EXISTS payment_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    channel TEXT NOT NULL CHECK (channel IN ('stripe', 'apple')),
    provider_event_id TEXT NOT NULL,
    order_id TEXT REFERENCES orders(id),
    idempotency_key TEXT,
    signature_valid INTEGER NOT NULL DEFAULT 0,
    raw_payload TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE (channel, provider_event_id)
);

CREATE INDEX IF NOT EXISTS idx_payment_order ON payment_events(order_id);

-- 种子套餐
INSERT OR IGNORE INTO plans (id, name, price_cents, currency, duration_days, stock_remaining)
VALUES
    ('plan_monthly', '月度 VIP', 1800, 'cny', 30, 500),
    ('plan_quarterly', '季度 VIP', 4800, 'cny', 90, 300),
    ('plan_yearly', '年度 VIP', 16800, 'cny', 365, 100);
