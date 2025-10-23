// next/src/modules/orbit/domain/types.ts
// —— Orbit 公共类型定义（与后端模型对齐） ——

// Task 枚举
export type TaskStatus = 'todo' | 'doing' | 'done' | 'archived';
export type TaskPriority = 'low' | 'normal' | 'high' | 'urgent';
export type TaskDomain = 'dev' | 'translate' | 'research' | 'study';

export interface Task {
  id: number;
  title: string;
  note?: string | null;
  status: TaskStatus;
  priority: TaskPriority;
  domain: TaskDomain;
  source_id?: number | null;
  entry_id?: number | null;
  due_at?: string | null;        // ISO 字符串
  completed_at?: string | null;  // ISO 字符串
  created_at: string;            // ISO 字符串
  updated_at?: string;           // ISO 字符串
}

// Memo
export interface Memo {
  id: number;
  text: string;
  tags?: string | null;
  linked_source_id?: number | null;
  linked_entry_id?: number | null;
  created_at: string; // ISO 字符串
  updated_at?: string; // ISO 字符串
}

// Stat
export interface Stat {
  id: number;
  metric: string;
  value: number;
}
