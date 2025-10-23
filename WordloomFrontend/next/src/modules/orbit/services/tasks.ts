// src/modules/orbit/services/tasks.ts
import { ORBIT_API_BASE } from "@/lib/apiBase";
import type { Task, TaskDomain, TaskPriority, TaskStatus } from "../domain/types";

type Query = {
  q?: string;
  status?: TaskStatus;
  priority?: TaskPriority;
  domain?: TaskDomain;
  // 不要再有 order_by / order 的默认值
};

function toQuery(q?: Query) {
  const p = new URLSearchParams();
  if (!q) return "";
  Object.entries(q).forEach(([k, v]) => {
    if (v !== undefined && v !== null && v !== "") p.set(k, String(v));
  });
  const s = p.toString();
  return s ? `?${s}` : "";
}

async function http<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${ORBIT_API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(text || res.statusText);
  }
  if (res.status === 204) return undefined as unknown as T;
  return res.json();
}

export async function listTasks(q?: Query) {
  return http<Task[]>(`/tasks${toQuery(q)}`);
}

export async function createTask(body: Partial<Task>) {
  return http<Task>(`/tasks`, { method: "POST", body: JSON.stringify(body) });
}
