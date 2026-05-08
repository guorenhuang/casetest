import { useEffect, useState } from 'react';
import {
  Alert,
  Button,
  Drawer,
  Form,
  Input,
  InputNumber,
  Layout,
  Popconfirm,
  Select,
  Space,
  Switch,
  Table,
  Tabs,
  Tag,
  Typography,
  message,
} from 'antd';
import type { ColumnsType } from 'antd/es/table';

import rawDataset from '../../dataset.json';
import type { Evidence } from './api';
import { auditBatch, deleteRule as apiDeleteRule, fetchRules, reimportYaml, saveRule } from './api';

const { Header, Content } = Layout;
const { Paragraph, Title, Text } = Typography;

const dataset = rawDataset as {
  comments: Array<{ id: string; text: string; image_urls?: string[] }>;
};

function verdictTag(v: string) {
  if (v === 'pass') return <Tag color="green">pass</Tag>;
  if (v === 'review') return <Tag color="gold">review</Tag>;
  if (v === 'block') return <Tag color="red">block</Tag>;
  return <Tag>{v}</Tag>;
}

export default function App() {
  const [busy, setBusy] = useState(false);
  const [auditRows, setAuditRows] = useState<Array<Record<string, unknown>>>([]);
  const [useLlm, setUseLlm] = useState(false);
  const [customJson, setCustomJson] = useState(
    JSON.stringify({ comments: dataset.comments }, null, 2),
  );

  async function submitDataset() {
    setBusy(true);
    try {
      const comments = dataset.comments ?? [];
      const results = await auditBatch({
        comments: comments.map((c) => ({
          id: c.id,
          text: c.text,
          image_urls: c.image_urls ?? [],
        })),
        use_llm: useLlm,
      });
      setAuditRows(results);
      message.success(`已返回 ${results.length} 条`);
    } catch (e) {
      message.error(String(e));
    } finally {
      setBusy(false);
    }
  }

  async function submitCustomJson() {
    setBusy(true);
    try {
      const parsed = JSON.parse(customJson) as { comments?: unknown[] };
      const arr = Array.isArray(parsed.comments)
        ? parsed.comments
        : (parsed as unknown as unknown[]);
      const results = await auditBatch({
        comments: arr.map((c: any) => ({
          id: String(c.id),
          text: String(c.text ?? ''),
          image_urls: c.image_urls ?? [],
        })),
        use_llm: useLlm,
      });
      setAuditRows(results);
      message.success(`已返回 ${results.length} 条`);
    } catch (e) {
      message.error(String(e));
    } finally {
      setBusy(false);
    }
  }

  const columns: ColumnsType<Record<string, unknown>> = [
    { title: 'ID', dataIndex: 'id', width: 90 },
    {
      title: '结论',
      dataIndex: 'verdict',
      width: 100,
      render: (v: string) => verdictTag(v),
    },
    {
      title: '证据',
      key: 'reasons',
      render: (_, record) => {
        const reasons = (record.reasons as Evidence[]) ?? [];
        return (
          <ul style={{ margin: 0, paddingLeft: 18 }}>
            {reasons.map((r, idx) => (
              <li key={idx}>
                <Text code>{r.type}</Text> · <Text>{r.id}</Text>: {r.detail}
              </li>
            ))}
          </ul>
        );
      },
    },
    {
      title: '截断预览',
      dataIndex: 'combined_text_sample',
      ellipsis: true,
      width: 280,
    },
  ];

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Header style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <Title level={4} style={{ margin: 0, color: '#fff' }}>
          评论审核 Agent（规则 + OCR + LLM 可降级）
        </Title>
        <Text style={{ color: 'rgba(255,255,255,0.7)' }}>
          SQLite 外置规则 · Ant Design · FastAPI
        </Text>
      </Header>
      <Content
        style={{ padding: '16px 20px 40px', maxWidth: 1200, margin: '0 auto', width: '100%' }}
      >
        <Alert
          type="info"
          showIcon
          style={{ marginBottom: 12 }}
          message="开发：先 `python src/run_server.py` 再 `npm run dev`（Vite 代理 /api）。"
        />
        <Tabs
          defaultActiveKey="audit"
          items={[
            {
              key: 'audit',
              label: '批量审核',
              children: (
                <Space direction="vertical" style={{ width: '100%' }} size="middle">
                  <Space wrap>
                    <Button type="primary" loading={busy} onClick={() => submitDataset()}>
                      跑内置 dataset.json
                    </Button>
                    <Switch
                      checkedChildren="启用 LLM"
                      unCheckedChildren="仅规则"
                      checked={useLlm}
                      onChange={(v) => setUseLlm(v)}
                    />
                    <Text type="secondary">未配置 Key 时请关闭 LLM，逻辑仍可跑通。</Text>
                  </Space>
                  <Space direction="vertical" style={{ width: '100%' }}>
                    <Text strong>自定义 JSON（含 comments 数组）</Text>
                    <Input.TextArea rows={10} value={customJson} onChange={(e) => setCustomJson(e.target.value)} />
                    <Button loading={busy} onClick={() => submitCustomJson()}>
                      提交审核
                    </Button>
                  </Space>
                  <Table
                    rowKey="id"
                    columns={columns}
                    dataSource={auditRows}
                    pagination={{ pageSize: 8 }}
                  />
                </Space>
              ),
            },
            {
              key: 'rules',
              label: '规则（SQLite）',
              children: <RulesPanel />,
            },
          ]}
        />
      </Content>
    </Layout>
  );
}

function RulesPanel() {
  const [open, setOpen] = useState(false);
  const [form] = Form.useForm();
  const [dump, setDump] = useState('[]');

  async function reload() {
    const rules = await fetchRules();
    setDump(JSON.stringify(rules, null, 2));
  }

  useEffect(() => {
    reload().catch((e) => message.error(String(e)));
  }, []);

  return (
    <Space direction="vertical" style={{ width: '100%' }} size="middle">
      <Space wrap>
        <Button onClick={() => reload().then(() => message.success('已刷新')).catch((e) => message.error(String(e)))}>
          拉取规则
        </Button>
        <Button
          onClick={async () => {
            try {
              const r = await reimportYaml();
              message.success(`已从 rules.yaml 导入 ${r.upserted} 条`);
              await reload();
            } catch (e) {
              message.error(String(e));
            }
          }}
        >
          从 rules.yaml 重导入
        </Button>
        <Button type="primary" onClick={() => setOpen(true)}>
          新增 / 编辑（单条）
        </Button>
      </Space>
      <Paragraph type="secondary">
        规则落库在 <Text code>data/audit.db</Text>，通过此页或 REST 增删改；业务代码只读配置执行匹配。
      </Paragraph>
      <Input.TextArea rows={16} value={dump} readOnly />
      <Drawer
        title="规则（upsert）"
        open={open}
        onClose={() => setOpen(false)}
        width={520}
        destroyOnClose
      >
        <Form
          form={form}
          layout="vertical"
          initialValues={{
            kind: 'regex',
            action: 'review',
            priority: 50,
            enabled: true,
            configText: '{}',
          }}
          onFinish={async (v) => {
            try {
              const rule = {
                id: v.id,
                kind: v.kind,
                action: v.action,
                priority: v.priority,
                description: v.description ?? '',
                enabled: v.enabled,
                config: JSON.parse(v.configText || '{}'),
              };
              await saveRule(rule);
              message.success('已保存');
              setOpen(false);
              await reload();
            } catch (e) {
              message.error(String(e));
            }
          }}
        >
          <Form.Item name="id" label="ID" rules={[{ required: true }]}>
            <Input placeholder="UNIQUE_RULE_ID" />
          </Form.Item>
          <Form.Item name="kind" label="kind" rules={[{ required: true }]}>
            <Select
              options={[
                { value: 'lexicon', label: 'lexicon' },
                { value: 'regex', label: 'regex' },
                { value: 'digit_sequence', label: 'digit_sequence' },
              ]}
            />
          </Form.Item>
          <Form.Item name="action" label="action" rules={[{ required: true }]}>
            <Select
              options={[
                { value: 'block', label: 'block' },
                { value: 'review', label: 'review' },
              ]}
            />
          </Form.Item>
          <Form.Item name="priority" label="priority（越小越先评估）">
            <InputNumber style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="description" label="description">
            <Input />
          </Form.Item>
          <Form.Item name="enabled" label="enabled" valuePropName="checked">
            <Switch />
          </Form.Item>
          <Form.Item name="configText" label="config (JSON)" rules={[{ required: true }]}>
            <Input.TextArea rows={8} placeholder='{"pattern":"..."}' />
          </Form.Item>
          <Space>
            <Button htmlType="submit" type="primary">
              保存
            </Button>
            <Popconfirm
              title="确认删除？"
              onConfirm={async () => {
                try {
                  const id = form.getFieldValue('id');
                  if (!id) {
                    message.warning('先填 ID');
                    return;
                  }
                  await apiDeleteRule(id);
                  message.success('已删除');
                  setOpen(false);
                  await reload();
                } catch (e) {
                  message.error(String(e));
                }
              }}
            >
              <Button danger>按 ID 删除</Button>
            </Popconfirm>
          </Space>
        </Form>
      </Drawer>
    </Space>
  );
}
