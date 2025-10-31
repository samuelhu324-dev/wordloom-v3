export type Tag = {
  id: string;
  name: string;
  color: string;
  icon?: string | null;
  description?: string | null;
  count: number;
  createdAt?: string | null;
  updatedAt?: string | null;
};

export type Note = {
  id: string;
  title: string | null;
  text: string;
  status: string;
  priority: number; // 重要程度 1-5
  urgency?: number; // 紧急程度 1-5
  usageLevel?: number; // 日用程度 1-5
  usageCount?: number; // 使用次数（自动计数）
  tags: string[]; // 标签名称数组（保留向后兼容）
  tagsRel?: Tag[]; // 新的标签对象数组（包含颜色、描述等）
  bookshelfId?: string | null; // 所属 Bookshelf ID（可选）
  dueAt?: string | null;
  createdAt?: string | null;
  updatedAt?: string | null;
};

export type NoteListParams = {
  q?: string;
  tag?: string;
  status?: string;
  sort?: string;
  limit?: number;
  offset?: number;
};