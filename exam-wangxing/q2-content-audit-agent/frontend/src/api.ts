export type Evidence = { type: string; id: string | null; detail: string };

export async function auditBatch(
  payload: Record<string, unknown>,
): Promise<
  Array<{
    id: string;
    verdict: string;
    reasons: Evidence[];
    combined_text_sample: string;
  }>
> {
  const r = await fetch('/api/audit', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!r.ok) {
    throw new Error(await r.text());
  }
  const j = await r.json();
  return j.results ?? [];
}

export async function fetchRules(): Promise<Record<string, unknown>[]> {
  const r = await fetch('/api/rules');
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}

export async function saveRule(rule: Record<string, unknown>) {
  const r = await fetch('/api/rules', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(rule),
  });
  if (!r.ok) throw new Error(await r.text());
}

export async function deleteRule(ruleId: string) {
  const r = await fetch(`/api/rules/${encodeURIComponent(ruleId)}`, { method: 'DELETE' });
  if (!r.ok) throw new Error(await r.text());
}

export async function reimportYaml() {
  const r = await fetch('/api/rules/reimport-yaml', { method: 'POST' });
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}
