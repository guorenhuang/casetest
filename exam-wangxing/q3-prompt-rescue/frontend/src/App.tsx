import "./App.css";

import {
  Alert,
  Button,
  Card,
  Checkbox,
  Divider,
  Form,
  Input,
  Layout,
  Modal,
  Select,
  Space,
  Table,
  Tabs,
  Tag,
  Typography,
  message,
} from "antd";
import type { ColumnsType } from "antd/es/table";
import {
  useCallback,
  useEffect,
  useMemo,
  useState,
} from "react";
import client from "./api";

const { Header, Content } = Layout;
const { TextArea } = Input;
const { Paragraph, Text } = Typography;

type Meta = {
  broken_prompt_template: string;
  llm_configured: boolean;
  export_dir: string;
};

type Observation = {
  id: number;
  plot: string;
  topic: string | null;
  raw_output: string;
  model_name: string | null;
  used_real_llm: number;
  created_at: string;
};

type IssueRow = {
  id: number;
  issue_key: string;
  title: string | null;
  phenomenon: string;
  evidence: string;
  why_problem: string;
  sort_order: number;
};

type TranscriptRow = {
  id: number;
  role: string;
  content: string;
  strategy_note: number;
  created_at: string;
};

type MappingRow = {
  id: number;
  issue_key: string;
  change_summary: string;
};

type BeforeAfterRow = {
  id: number;
  label: string | null;
  plot: string;
  before_output: string;
  after_output: string;
  notes: string | null;
  created_at: string;
};

const PRESETS: { topic: string; plot: string }[] = [
  {
    topic: "甜宠",
    plot: "电梯里误会霸总是快递员，三句话内反转成甲方；全程办公室。",
  },
  {
    topic: "悬疑",
    plot: "雨夜老宅，女主收到十年前失踪父亲的短信，只能回答是否。",
  },
  {
    topic: "复仇",
    plot: "豪门宴上，被换肾的养女当场播放手术录音，全场静音十秒。",
  },
  {
    topic: "穿越",
    plot: "古装宫女醒来发现手中是 iPhone 闹钟，御花园直播社死。",
  },
  {
    topic: "家庭伦理",
    plot: "婆婆把婚房过户给外甥，儿媳拿出婚前公证与缴费记录当庭对质。",
  },
];

export default function App() {
  const [meta, setMeta] = useState<Meta | null>(null);
  const [obs, setObs] = useState<Observation[]>([]);
  const [issues, setIssues] = useState<IssueRow[]>([]);
  const [transcript, setTranscript] = useState<TranscriptRow[]>([]);
  const [fixedContent, setFixedContent] = useState("");
  const [mappings, setMappings] = useState<
    { issue_key: string; change_summary: string }[]
  >([]);
  const [ba, setBa] = useState<BeforeAfterRow[]>([]);
  const [loading, setLoading] = useState(false);

  const refreshAll = useCallback(async () => {
    const [m, o, i, t, f, b] = await Promise.all([
      client.get<Meta>("/api/meta"),
      client.get<Observation[]>("/api/observations"),
      client.get<IssueRow[]>("/api/issues"),
      client.get<TranscriptRow[]>("/api/transcript"),
      client.get<{ content: string; mappings: MappingRow[] }>(
        "/api/fixed-prompt",
      ),
      client.get<BeforeAfterRow[]>("/api/before-after"),
    ]);
    setMeta(m.data);
    setObs(o.data);
    setIssues(i.data);
    setTranscript(t.data);
    setFixedContent(f.data.content);
    setMappings(
      f.data.mappings.map((x) => ({
        issue_key: x.issue_key,
        change_summary: x.change_summary,
      })),
    );
    setBa(b.data);
  }, []);

  useEffect(() => {
    void refreshAll().catch((e: unknown) =>
      message.error(String((e as Error)?.message ?? e)),
    );
  }, [refreshAll]);

  const obsColumns: ColumnsType<Observation> = useMemo(
    () => [
      { title: "ID", dataIndex: "id", width: 56 },
      {
        title: "题材",
        dataIndex: "topic",
        width: 100,
        render: (t: string | null) => t || "—",
      },
      {
        title: "模型",
        dataIndex: "model_name",
        width: 140,
        render: (_: unknown, r) => (
          <Space wrap>
            <span>{r.model_name}</span>
            {r.used_real_llm ? <Tag color="green">real</Tag> : <Tag>mock</Tag>}
          </Space>
        ),
      },
      {
        title: "剧情摘要",
        render: (_: unknown, r: Observation) => (
          <Paragraph ellipsis={{ rows: 2 }} style={{ margin: 0 }}>
            {r.plot}
          </Paragraph>
        ),
      },
      { title: "时间", dataIndex: "created_at", width: 180 },
    ],
    [],
  );

  const issueColumns: ColumnsType<IssueRow> = useMemo(
    () => [
      { title: "Key", dataIndex: "issue_key", width: 72 },
      { title: "标题", dataIndex: "title", width: 140 },
      {
        title: "现象",
        dataIndex: "phenomenon",
        render: (t: string) => (
          <Paragraph ellipsis={{ rows: 2 }} style={{ margin: 0 }}>
            {t}
          </Paragraph>
        ),
      },
      {
        title: "证据",
        dataIndex: "evidence",
        render: (t: string) => (
          <Paragraph ellipsis={{ rows: 2 }} style={{ margin: 0 }}>
            {t}
          </Paragraph>
        ),
      },
      {
        title: "操作",
        width: 96,
        render: (_: unknown, r) => (
          <Button
            type="link"
            danger
            onClick={async () => {
              await client.delete(`/api/issues/${r.id}`);
              message.success("已删除");
              await refreshAll();
            }}
          >
            删除
          </Button>
        ),
      },
    ],
    [refreshAll],
  );

  return (
    <Layout className="app-layout">
      <Header className="app-header">
        <div className="brand">Q3 Prompt 救火 · 诊断工作台</div>
        <Space wrap>
          <Text type="secondary">
            交付导出目录：<Text code>{meta?.export_dir}</Text>
          </Text>
          {meta?.llm_configured ? (
            <Tag color="green">已配置 OPENAI API（真实推理）</Tag>
          ) : (
            <Tag>未配置密钥 · 使用可复现 mock 输出</Tag>
          )}
        </Space>
      </Header>
      <Content className="app-content">
        <Alert
          className="flow-alert"
          type="info"
          showIcon
          message="硬性流程：R1 先跑≥5条观测写入 observations → R2 issues（现象+证据+为何）→ R3 transcript 体现逼问策略 → R4 fixed_prompt + 映射 → R5 ≥2 组 before/after → 导出 md。"
        />
        <Tabs
          destroyInactiveTabPane={false}
          items={[
            {
              key: "obs",
              label: "① 观测 R1",
              children: (
                <Space direction="vertical" size="middle" style={{ width: "100%" }}>
                  <Card size="small" title="待诊断 Prompt（试卷原样）">
                    <pre className="prompt-block">{meta?.broken_prompt_template}</pre>
                  </Card>
                  <Card
                    size="small"
                    title="运行新观测（勿立刻改 prompt；先积累原始输出）"
                    extra={
                      <Space wrap>
                        <Button
                          loading={loading}
                          onClick={async () => {
                            setLoading(true);
                            try {
                              const res = await client.post("/api/seed/demo", {
                                include_transcript_templates: true,
                              });
                              message.success(
                                `演示数据：runs +${res.data.created_runs} · issues +${res.data.created_issues} · before/after +${res.data.created_before_after ?? 0}`,
                              );
                              await refreshAll();
                            } catch (e: unknown) {
                              message.error(String((e as Error)?.message ?? e));
                            } finally {
                              setLoading(false);
                            }
                          }}
                        >
                          一键演示数据（≥5 剧情 + 4 issues）
                        </Button>
                      </Space>
                    }
                  >
                    <Form
                      layout="vertical"
                      onFinish={async (v: { plot: string; topic?: string }) => {
                        setLoading(true);
                        try {
                          await client.post("/api/observations/run", {
                            plot: v.plot,
                            topic: v.topic || null,
                          });
                          message.success("已记录一次运行");
                          await refreshAll();
                        } catch (e: unknown) {
                          message.error(String((e as Error)?.message ?? e));
                        } finally {
                          setLoading(false);
                        }
                      }}
                    >
                      <Form.Item
                        name="topic"
                        label="题材标签（自行区分甜宠/悬疑等）"
                      >
                        <Input placeholder="例：甜宠" />
                      </Form.Item>
                      <Form.Item
                        name="plot"
                        label="剧情"
                        rules={[{ required: true, message: "请输入剧情" }]}
                      >
                        <TextArea rows={4} />
                      </Form.Item>
                      <Space wrap>
                        <Button type="primary" htmlType="submit" loading={loading}>
                          用坏 Prompt 跑一轮
                        </Button>
                        {PRESETS.map((p) => (
                          <Button
                            key={p.topic}
                            onClick={() => {
                              Modal.confirm({
                                title: `填充「${p.topic}」示例剧情？`,
                                onOk: async () => {
                                  setLoading(true);
                                  try {
                                    await client.post("/api/observations/run", {
                                      plot: p.plot,
                                      topic: p.topic,
                                    });
                                    message.success("已记录");
                                    await refreshAll();
                                  } finally {
                                    setLoading(false);
                                  }
                                },
                              });
                            }}
                          >
                            快速：{p.topic}
                          </Button>
                        ))}
                      </Space>
                    </Form>
                  </Card>
                  <Card size="small" title={`观测记录（${obs.length}）`}>
                    <Table<Observation>
                      rowKey="id"
                      size="small"
                      columns={obsColumns}
                      dataSource={obs}
                      pagination={{ pageSize: 8 }}
                      expandable={{
                        expandedRowRender: (r) => (
                          <pre className="raw-out">{r.raw_output}</pre>
                        ),
                      }}
                    />
                  </Card>
                </Space>
              ),
            },
            {
              key: "issues",
              label: "② 问题清单 R2",
              children: (
                <Card
                  size="small"
                  title="issues.md 每条需：现象 + 证据片段 + 为何是问题（≥4 条）"
                  extra={
                    <Button onClick={() => void refreshAll()}>刷新</Button>
                  }
                >
                  <Form
                    layout="vertical"
                    onFinish={async (v: Record<string, string | number>) => {
                      await client.post("/api/issues", {
                        issue_key: String(v.issue_key),
                        title: v.title ? String(v.title) : null,
                        phenomenon: String(v.phenomenon),
                        evidence: String(v.evidence),
                        why_problem: String(v.why_problem),
                        sort_order: Number(v.sort_order ?? 0),
                      });
                      message.success("已添加");
                      await refreshAll();
                    }}
                  >
                    <Space wrap style={{ width: "100%" }} align="start">
                      <Form.Item
                        name="issue_key"
                        label="Issue ID"
                        rules={[{ required: true }]}
                        style={{ minWidth: 120 }}
                      >
                        <Input placeholder="I-5" />
                      </Form.Item>
                      <Form.Item name="title" label="短标题" style={{ minWidth: 200 }}>
                        <Input />
                      </Form.Item>
                      <Form.Item name="sort_order" label="排序" initialValue={0}>
                        <Input type="number" />
                      </Form.Item>
                    </Space>
                    <Form.Item
                      name="phenomenon"
                      label="现象"
                      rules={[{ required: true }]}
                    >
                      <TextArea rows={2} />
                    </Form.Item>
                    <Form.Item
                      name="evidence"
                      label="证据片段（可指向某次 Run #id）"
                      rules={[{ required: true }]}
                    >
                      <TextArea rows={2} />
                    </Form.Item>
                    <Form.Item
                      name="why_problem"
                      label="为何是问题"
                      rules={[{ required: true }]}
                    >
                      <TextArea rows={2} />
                    </Form.Item>
                    <Button type="primary" htmlType="submit">
                      添加问题
                    </Button>
                  </Form>
                  <Divider />
                  <Table<IssueRow>
                    rowKey="id"
                    size="small"
                    columns={issueColumns}
                    dataSource={issues}
                  />
                </Card>
              ),
            },
            {
              key: "transcript",
              label: "③ 协同诊断 R3",
              children: (
                <Card
                  size="small"
                  title="transcript.md：记录「逼出真问题」的策略，不要停留在「挺好」"
                  extra={
                    <Button
                      danger
                      onClick={async () => {
                        await client.delete("/api/transcript");
                        message.success("已清空");
                        await refreshAll();
                      }}
                    >
                      清空
                    </Button>
                  }
                >
                    <Form
                      layout="inline"
                      onFinish={async (v: {
                        role: "user" | "assistant" | "coach";
                        content: string;
                        strategy?: boolean;
                      }) => {
                        await client.post("/api/transcript", {
                          role: v.role,
                          content: v.content,
                          strategy_note: Boolean(v.strategy),
                        });
                        await refreshAll();
                      }}
                    >
                      <Form.Item
                        name="role"
                        initialValue="coach"
                        rules={[{ required: true }]}
                      >
                        <Select
                          style={{ width: 160 }}
                          options={[
                            { value: "coach", label: "coach（协作逼问）" },
                            { value: "user", label: "user" },
                            { value: "assistant", label: "assistant" },
                          ]}
                        />
                      </Form.Item>
                    <Form.Item
                      name="content"
                      rules={[{ required: true }]}
                      style={{ flex: 1, minWidth: 280 }}
                    >
                      <TextArea rows={2} placeholder="要求对方引用 observations 行号/片段，而非泛泛评价" />
                    </Form.Item>
                    <Form.Item name="strategy" valuePropName="checked">
                      <Checkbox>策略标记</Checkbox>
                    </Form.Item>
                    <Button type="primary" htmlType="submit">
                      追加一条
                    </Button>
                  </Form>
                  <Divider />
                  {transcript.map((t) => (
                    <Card
                      key={t.id}
                      size="small"
                      style={{ marginBottom: 8 }}
                      title={
                        <Space>
                          <Tag>{t.role}</Tag>
                          {t.strategy_note ? <Tag color="purple">策略</Tag> : null}
                          <Text type="secondary">{t.created_at}</Text>
                        </Space>
                      }
                    >
                      <Paragraph style={{ margin: 0, whiteSpace: "pre-wrap" }}>
                        {t.content}
                      </Paragraph>
                    </Card>
                  ))}
                </Card>
              ),
            },
            {
              key: "fixed",
              label: "④ 修复映射 R4",
              children: (
                <Space direction="vertical" size="middle" style={{ width: "100%" }}>
                  <Card size="small" title="fixed_prompt.md：新 prompt 文本">
                    <TextArea
                      rows={18}
                      value={fixedContent}
                      onChange={(e) => setFixedContent(e.target.value)}
                    />
                    <Button
                      type="primary"
                      style={{ marginTop: 12 }}
                      onClick={async () => {
                        await client.put("/api/fixed-prompt", {
                          content: fixedContent,
                        });
                        message.success("已保存 prompt");
                      }}
                    >
                      保存 Prompt
                    </Button>
                  </Card>
                  <Card size="small" title="改动 ↔ Issue 映射（禁笼统一锅端）">
                    <Form
                      layout="vertical"
                      onFinish={async () => {
                        await client.put("/api/fixed-prompt/mappings", mappings);
                        message.success("映射已保存");
                        await refreshAll();
                      }}
                    >
                      {mappings.map((row, idx) => (
                        <Space
                          key={`${row.issue_key}-${idx}`}
                          style={{ width: "100%", marginBottom: 8 }}
                          align="start"
                        >
                          <Input
                            style={{ width: 100 }}
                            value={row.issue_key}
                            onChange={(e) => {
                              const next = [...mappings];
                              next[idx] = { ...next[idx], issue_key: e.target.value };
                              setMappings(next);
                            }}
                          />
                          <TextArea
                            style={{ flex: 1 }}
                            value={row.change_summary}
                            onChange={(e) => {
                              const next = [...mappings];
                              next[idx] = {
                                ...next[idx],
                                change_summary: e.target.value,
                              };
                              setMappings(next);
                            }}
                          />
                          <Button
                            onClick={() =>
                              setMappings(mappings.filter((_, i) => i !== idx))
                            }
                          >
                            删
                          </Button>
                        </Space>
                      ))}
                      <Space>
                        <Button
                          onClick={() =>
                            setMappings([
                              ...mappings,
                              { issue_key: "I-", change_summary: "" },
                            ])
                          }
                        >
                          新增一行
                        </Button>
                        <Button type="primary" htmlType="submit">
                          保存映射表
                        </Button>
                      </Space>
                    </Form>
                  </Card>
                </Space>
              ),
            },
            {
              key: "ba",
              label: "⑤ 对比 R5",
              children: (
                <Card
                  size="small"
                  title="before_after.md：≥2 组（可用「自动生成」基于当前 fixed prompt）"
                  extra={
                    <Button onClick={() => void refreshAll()}>刷新</Button>
                  }
                >
                  <Form
                    layout="vertical"
                    onFinish={async (v: { plot: string; label?: string }) => {
                      setLoading(true);
                      try {
                        await client.post("/api/before-after/generate", {
                          plot: v.plot,
                          label: v.label || null,
                        });
                        message.success("已生成一组 before/after");
                        await refreshAll();
                      } finally {
                        setLoading(false);
                      }
                    }}
                  >
                    <Form.Item name="label" label="组标签">
                      <Input placeholder="例：JSON 可解析性" />
                    </Form.Item>
                    <Form.Item
                      name="plot"
                      label="剧情"
                      rules={[{ required: true }]}
                    >
                      <TextArea rows={3} />
                    </Form.Item>
                    <Button type="primary" htmlType="submit" loading={loading}>
                      自动生成（坏 prompt vs 当前 fixed）
                    </Button>
                  </Form>
                  <Divider />
                  {ba.map((row) => (
                    <Card
                      key={row.id}
                      size="small"
                      style={{ marginBottom: 12 }}
                      title={
                        <Space>
                          <Text strong>{row.label || `组 #${row.id}`}</Text>
                          <Button
                            size="small"
                            danger
                            onClick={async () => {
                              await client.delete(`/api/before-after/${row.id}`);
                              await refreshAll();
                            }}
                          >
                            删除
                          </Button>
                        </Space>
                      }
                    >
                      <Paragraph type="secondary" style={{ whiteSpace: "pre-wrap" }}>
                        Plot: {row.plot}
                      </Paragraph>
                      {row.notes ? (
                        <Paragraph type="secondary">备注：{row.notes}</Paragraph>
                      ) : null}
                      <Divider orientation="left">Before</Divider>
                      <pre className="raw-out">{row.before_output}</pre>
                      <Divider orientation="left">After</Divider>
                      <pre className="raw-out">{row.after_output}</pre>
                    </Card>
                  ))}
                </Card>
              ),
            },
            {
              key: "export",
              label: "交付导出",
              children: (
                <Card size="small" title="写入 exam-libraries/q3-prompt-rescue/*.md">
                  <Button
                    type="primary"
                    loading={loading}
                    onClick={async () => {
                      setLoading(true);
                      try {
                        const res = await client.post<{
                          export_dir: string;
                          written: Record<string, string>;
                          warnings: string[];
                        }>("/api/export/markdown");
                        const w = res.data.warnings ?? [];
                        if (w.length) {
                          Modal.warning({
                            title: "导出完成，但未满足全部硬性检查时给出提示",
                            content: (
                              <ul>
                                {w.map((x) => (
                                  <li key={x}>{x}</li>
                                ))}
                              </ul>
                            ),
                          });
                        } else {
                          message.success("导出完成，硬性检查通过");
                        }
                      } finally {
                        setLoading(false);
                      }
                    }}
                  >
                    导出五份 Markdown
                  </Button>
                  <Paragraph type="secondary" style={{ marginTop: 12 }}>
                    文件：
                    observations.md · issues.md · fixed_prompt.md · before_after.md ·
                    transcript.md
                  </Paragraph>
                </Card>
              ),
            },
          ]}
        />
      </Content>
    </Layout>
  );
}
