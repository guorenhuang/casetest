import { useEffect, useState } from 'react'
import {
  Button,
  Card,
  Form,
  Input,
  Select,
  Space,
  Table,
  Tag,
  Typography,
  message,
} from 'antd'

const { Title, Text } = Typography

const api = (path, opts = {}) =>
  fetch(path, {
    ...opts,
    headers: { 'Content-Type': 'application/json', ...opts.headers },
  }).then(async (r) => {
    const text = await r.text()
    let data
    try {
      data = text ? JSON.parse(text) : null
    } catch {
      data = text
    }
    if (!r.ok) throw new Error(data?.detail || data?.error || r.statusText)
    return data
  })

export default function App() {
  const [plans, setPlans] = useState([])
  const [userId, setUserId] = useState('user_demo_001')
  const [orders, setOrders] = useState([])
  const [loading, setLoading] = useState(false)
  const [form] = Form.useForm()

  const loadPlans = () => api('/api/plans').then(setPlans)

  const refreshOrders = () => {
    if (!userId.trim()) return
    setLoading(true)
    api(`/api/orders?user_id=${encodeURIComponent(userId)}`)
      .then(setOrders)
      .catch((e) => message.error(String(e.message)))
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    loadPlans().catch((e) => message.error('加载套餐失败: ' + e.message))
  }, [])

  useEffect(() => {
    refreshOrders()
  }, [userId])

  const onCreate = async (v) => {
    try {
      await api('/api/orders', {
        method: 'POST',
        body: JSON.stringify({
          user_id: v.user_id,
          plan_id: v.plan_id,
          idempotency_key: `ui-${Date.now()}-${Math.random().toString(36).slice(2)}`,
        }),
      })
      message.success('订单已创建')
      form.resetFields(['plan_id'])
      refreshOrders()
    } catch (e) {
      message.error(String(e.message))
    }
  }

  const statusColor = (s) =>
    ({ pending: 'gold', paid: 'blue', active: 'green', expired: 'default', refunded: 'red' }[s] ||
      'default')

  const columns = [
    { title: '订单号', dataIndex: ['order', 'id'], key: 'oid', ellipsis: true },
    {
      title: '订单状态',
      key: 'os',
      render: (_, row) => (
        <Tag color={statusColor(row.order?.status)}>{row.order?.status}</Tag>
      ),
    },
    {
      title: '订阅状态',
      key: 'ss',
      render: (_, row) => (
        <Tag color={statusColor(row.subscription?.status)}>{row.subscription?.status}</Tag>
      ),
    },
    {
      title: '周期截止',
      dataIndex: ['subscription', 'current_period_end'],
      key: 'end',
      render: (v) => v || '—',
    },
    {
      title: '操作',
      key: 'act',
      width: 220,
      render: (_, row) => (
        <Space wrap>
          <Button
            size="small"
            onClick={() =>
              api(`/api/orders/${row.order.id}`)
                .then((d) => {
                  message.success('已刷新')
                  setOrders((prev) =>
                    prev.map((o) => (o.order.id === d.order.id ? d : o))
                  )
                })
                .catch((e) => message.error(e.message))
            }
          >
            刷新
          </Button>
          <Button
            size="small"
            onClick={() => {
              const evt = `evt_ui_${row.order.id.replace(/[^a-zA-Z0-9]/g, '')}`
              const body = {
                id: evt,
                object: 'event',
                type: 'checkout.session.completed',
                data: {
                  object: {
                    id: 'cs_ui_' + row.order.id,
                    object: 'checkout.session',
                    metadata: { order_id: row.order.id },
                  },
                },
              }
              const raw = JSON.stringify(body)
              const ts = Math.floor(Date.now() / 1000)
              const secret =
                import.meta.env.VITE_STRIPE_WEBHOOK_SECRET ||
                'whsec_test_local_default_secret'
              const enc = new TextEncoder()
              const part1 = enc.encode(`${ts}.`)
              const part2 = enc.encode(raw)
              const signedBytes = new Uint8Array(part1.length + part2.length)
              signedBytes.set(part1)
              signedBytes.set(part2, part1.length)
              window.crypto.subtle
                .importKey(
                  'raw',
                  enc.encode(secret),
                  { name: 'HMAC', hash: 'SHA-256' },
                  false,
                  ['sign']
                )
                .then((k) =>
                  window.crypto.subtle.sign('HMAC', k, signedBytes)
                )
                .then((buf) => {
                  const sig = Array.from(new Uint8Array(buf))
                    .map((b) => b.toString(16).padStart(2, '0'))
                    .join('')
                  return fetch('/webhooks/stripe', {
                    method: 'POST',
                    headers: {
                      'Content-Type': 'application/json',
                      'Stripe-Signature': `t=${ts},v1=${sig}`,
                    },
                    body: raw,
                  })
                })
                .then(async (r) => {
                  const j = await r.json()
                  if (!r.ok) throw new Error(j.detail || j.error || r.statusText)
                  message.success('Stripe Webhook 已投递')
                  refreshOrders()
                })
                .catch((e) => message.error(String(e)))
            }}
          >
            模拟 Stripe
          </Button>
          <Button
            size="small"
            danger
            onClick={() =>
              api(`/api/orders/${row.order.id}/expire`, { method: 'POST' })
                .then(() => {
                  message.success('已置为到期演示')
                  refreshOrders()
                })
                .catch((e) => message.error(e.message))
            }
          >
            演示到期
          </Button>
        </Space>
      ),
    },
  ]

  return (
    <div style={{ maxWidth: 1120, margin: '0 auto', padding: 24 }}>
      <Title level={3} style={{ marginTop: 0 }}>
        短剧后台 · 会员订阅
      </Title>
      <Text type="secondary">
        Python API + SQLite；Webhook 使用 Stripe 风格验签与 Apple ASN 字段；详见项目 README。
      </Text>

      <Card title="新建订单" style={{ marginTop: 16 }}>
        <Form
          form={form}
          layout="vertical"
          onFinish={onCreate}
          initialValues={{ user_id: userId, plan_id: 'plan_monthly' }}
        >
          <Form.Item name="user_id" label="用户 ID" rules={[{ required: true }]}>
            <Input onChange={(e) => setUserId(e.target.value)} />
          </Form.Item>
          <Form.Item name="plan_id" label="套餐" rules={[{ required: true }]}>
            <Select
              options={plans.map((p) => ({
                value: p.id,
                label: `${p.name} · ${(p.price_cents / 100).toFixed(2)} ${
                  p.currency
                } · ${p.duration_days} 天（库存 ${p.stock_remaining}）`,
              }))}
            />
          </Form.Item>
          <Button type="primary" htmlType="submit">
            创建订单
          </Button>
        </Form>
      </Card>

      <Card title="我的订单" style={{ marginTop: 16 }}>
        <Space style={{ marginBottom: 12 }}>
          <Input
            style={{ width: 240 }}
            value={userId}
            onChange={(e) => setUserId(e.target.value)}
            addonBefore="user_id"
          />
          <Button onClick={refreshOrders} loading={loading}>
            刷新列表
          </Button>
        </Space>
        <Table
          rowKey={(r) => r.order.id}
          loading={loading}
          columns={columns}
          dataSource={orders}
          pagination={{ pageSize: 6 }}
        />
      </Card>
    </div>
  )
}
