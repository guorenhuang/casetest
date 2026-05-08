import { useCallback, useEffect, useMemo, useState } from "react";
import {
  App as AntApp,
  Button,
  Card,
  Form,
  Input,
  InputNumber,
  Popconfirm,
  Space,
  Table,
  Typography,
  message,
} from "antd";
import type { ColumnsType } from "antd/es/table";
import {
  DeleteOutlined,
  DownloadOutlined,
  PlusOutlined,
  ThunderboltOutlined,
} from "@ant-design/icons";

const { Title, Paragraph } = Typography;

export type Shot = {
  id: number;
  shot_no: number;
  scene: string;
  action: string;
  mood: string;
  camera: string;
  notes: string;
  english_prompt: string;
  created_at?: string | null;
};

async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(path, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers || {}),
    },
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || res.statusText);
  }
  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

function downloadText(filename: string, text: string, mime: string) {
  const blob = new Blob([text], { type: mime });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

function toCsv(rows: Shot[]): string {
  const headers = [
    "shot_no",
    "scene",
    "action",
    "mood",
    "camera",
    "notes",
    "english_prompt",
  ];
  const esc = (s: string) => `"${String(s).replace(/"/g, '""')}"`;
  const lines = [
    headers.join(","),
    ...rows.map((r) =>
      [
        r.shot_no,
        r.scene,
        r.action,
        r.mood,
        r.camera,
        r.notes,
        r.english_prompt,
      ]
        .map((c) => esc(String(c)))
        .join(",")
    ),
  ];
  return "\uFEFF" + lines.join("\n");
}

export default function App() {
  const [shots, setShots] = useState<Shot[]>([]);
  const [loading, setLoading] = useState(false);
  const [busyId, setBusyId] = useState<number | null>(null);
  const [tableEpoch, setTableEpoch] = useState(0);
  const [form] = Form.useForm<{
    shot_no: number;
    scene: string;
    action: string;
    mood: string;
    camera: string;
    notes: string;
  }>();

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const data = await api<Shot[]>("/api/shots");
      setShots(data);
      setTableEpoch((e) => e + 1);
    } catch (e) {
      message.error((e as Error).message || "加载失败");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const nextShotNo = useMemo(() => {
    if (!shots.length) return 1;
    return Math.max(...shots.map((s) => s.shot_no)) + 1;
  }, [shots]);

  useEffect(() => {
    form.setFieldsValue({ shot_no: nextShotNo });
  }, [form, nextShotNo]);

  const onSeed = async () => {
    try {
      await api("/api/seed-demo", { method: "POST" });
      message.success("已载入示例分镜（SQLite 已写入）");
      await load();
    } catch (e) {
      message.error((e as Error).message);
    }
  };

  const onAdd = async () => {
    try {
      const v = await form.validateFields();
      await api<Shot>("/api/shots", {
        method: "POST",
        body: JSON.stringify({ ...v, english_prompt: "" }),
      });
      await load();
      form.setFieldsValue({
        scene: "",
        action: "",
        mood: "",
        camera: "",
        notes: "",
      });
      message.success("已新增一行");
    } catch (e) {
      if (e && typeof e === "object" && "errorFields" in e) return;
      message.error((e as Error).message);
    }
  };

  const onSaveCell = async (id: number, patch: Partial<Shot>) => {
    await api<Shot>(`/api/shots/${id}`, {
      method: "PATCH",
      body: JSON.stringify(patch),
    });
    await load();
  };

  const onGenerate = async (id: number) => {
    setBusyId(id);
    try {
      await api<Shot>(`/api/shots/${id}/generate-prompt`, { method: "POST" });
      message.success("已生成/更新英文 prompt");
      await load();
    } catch (e) {
      message.error((e as Error).message);
    } finally {
      setBusyId(null);
    }
  };

  const onDelete = async (id: number) => {
    try {
      await api(`/api/shots/${id}`, { method: "DELETE" });
      message.success("已删除");
      await load();
    } catch (e) {
      message.error((e as Error).message);
    }
  };

  const onExportJson = () => {
    downloadText(
      "storyboard-prompts.json",
      JSON.stringify(shots, null, 2),
      "application/json"
    );
    message.success("已导出 JSON");
  };

  const onExportCsv = () => {
    downloadText("storyboard-prompts.csv", toCsv(shots), "text/csv;charset=utf-8");
    message.success("已导出 CSV");
  };

  const columns: ColumnsType<Shot> = [
    {
      title: "#",
      dataIndex: "shot_no",
      width: 72,
      render: (v: number, record) => (
        <InputNumber
          min={1}
          value={v}
          size="small"
          className="w-full"
          onChange={(n) => {
            const nv = typeof n === "number" ? n : record.shot_no;
            void onSaveCell(record.id, { shot_no: nv });
          }}
        />
      ),
    },
    {
      title: "场景",
      dataIndex: "scene",
      width: 140,
      render: (v, record) => (
        <Input.TextArea
          autoSize={{ minRows: 1, maxRows: 4 }}
          defaultValue={v}
          onBlur={(e) => {
            if (e.target.value !== v) void onSaveCell(record.id, { scene: e.target.value });
          }}
        />
      ),
    },
    {
      title: "动作/表演",
      dataIndex: "action",
      width: 160,
      render: (v, record) => (
        <Input.TextArea
          autoSize={{ minRows: 1, maxRows: 5 }}
          defaultValue={v}
          onBlur={(e) => {
            if (e.target.value !== v) void onSaveCell(record.id, { action: e.target.value });
          }}
        />
      ),
    },
    {
      title: "情绪/光色",
      dataIndex: "mood",
      width: 120,
      render: (v, record) => (
        <Input.TextArea
          autoSize={{ minRows: 1, maxRows: 4 }}
          defaultValue={v}
          onBlur={(e) => {
            if (e.target.value !== v) void onSaveCell(record.id, { mood: e.target.value });
          }}
        />
      ),
    },
    {
      title: "机位/镜头",
      dataIndex: "camera",
      width: 120,
      render: (v, record) => (
        <Input.TextArea
          autoSize={{ minRows: 1, maxRows: 4 }}
          defaultValue={v}
          onBlur={(e) => {
            if (e.target.value !== v) void onSaveCell(record.id, { camera: e.target.value });
          }}
        />
      ),
    },
    {
      title: "备注",
      dataIndex: "notes",
      width: 100,
      render: (v, record) => (
        <Input.TextArea
          autoSize={{ minRows: 1, maxRows: 3 }}
          defaultValue={v}
          onBlur={(e) => {
            if (e.target.value !== v) void onSaveCell(record.id, { notes: e.target.value });
          }}
        />
      ),
    },
    {
      title: "English prompt",
      dataIndex: "english_prompt",
      render: (v, record) => (
        <Input.TextArea
          autoSize={{ minRows: 2, maxRows: 8 }}
          defaultValue={v}
          onBlur={(e) => {
            if (e.target.value !== v)
              void onSaveCell(record.id, { english_prompt: e.target.value });
          }}
        />
      ),
    },
    {
      title: "操作",
      width: 160,
      fixed: "right",
      render: (_, record) => (
        <Space direction="vertical" size="small">
          <Button
            type="primary"
            size="small"
            icon={<ThunderboltOutlined />}
            loading={busyId === record.id}
            onClick={() => void onGenerate(record.id)}
          >
            AI 生成
          </Button>
          <Popconfirm title="确认删除该行？" onConfirm={() => void onDelete(record.id)}>
            <Button size="small" danger icon={<DeleteOutlined />}>
              删除
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <AntApp>
      <div style={{ padding: 24, maxWidth: 1400, margin: "0 auto" }}>
        <Title level={3} style={{ marginTop: 0 }}>
          分镜表 → 英文美术 Prompt
        </Title>
        <Paragraph type="secondary">
          选题 <strong>(b)</strong>：表格维护分镜字段，SQLite 持久化；可单行调用模型生成英文 prompt（无
          API Key 时使用内置模板）；支持一键导出 JSON / CSV。
        </Paragraph>

        <Space wrap style={{ marginBottom: 16 }}>
          <Button onClick={() => void load()} loading={loading}>
            刷新
          </Button>
          <Button onClick={() => void onSeed()}>加载示例分镜</Button>
          <Button icon={<DownloadOutlined />} onClick={onExportJson}>
            导出 JSON
          </Button>
          <Button icon={<DownloadOutlined />} onClick={onExportCsv}>
            导出 CSV
          </Button>
        </Space>

        <Card title="新增分镜行" size="small" style={{ marginBottom: 16 }}>
          <Form
            form={form}
            layout="inline"
            initialValues={{ shot_no: 1, scene: "", action: "", mood: "", camera: "", notes: "" }}
          >
            <Form.Item name="shot_no" label="镜号" rules={[{ required: true }]}>
              <InputNumber min={1} />
            </Form.Item>
            <Form.Item name="scene" label="场景">
              <Input style={{ width: 160 }} />
            </Form.Item>
            <Form.Item name="action" label="动作">
              <Input style={{ width: 180 }} />
            </Form.Item>
            <Form.Item name="mood" label="情绪">
              <Input style={{ width: 140 }} />
            </Form.Item>
            <Form.Item name="camera" label="机位">
              <Input style={{ width: 140 }} />
            </Form.Item>
            <Form.Item name="notes" label="备注">
              <Input style={{ width: 120 }} />
            </Form.Item>
            <Form.Item>
              <Button type="primary" icon={<PlusOutlined />} onClick={() => void onAdd()}>
                添加
              </Button>
            </Form.Item>
          </Form>
        </Card>

        <Table<Shot>
          key={tableEpoch}
          rowKey="id"
          loading={loading}
          dataSource={shots}
          columns={columns}
          scroll={{ x: 1200 }}
          pagination={false}
          bordered
          size="small"
        />
      </div>
    </AntApp>
  );
}
