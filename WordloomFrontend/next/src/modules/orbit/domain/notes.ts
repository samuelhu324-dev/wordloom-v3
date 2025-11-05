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
  summary?: string | null; // 新增：Note 摘要/描述
  summary_zh?: string | null; // 后端返回的摘要（蛇形命名）
  text: string;
  blocksJson?: string | null; // 新增：JSON格式的blocks存储
  status: string;
  priority: number; // 重要程度 1-5
  urgency?: number; // 紧急程度 1-5
  usageLevel?: number; // 日用程度 1-5
  usageCount?: number; // 使用次数（自动计数）
  tags: string[]; // 标签名称数组（保留向后兼容）
  tagsRel?: Tag[]; // 新的标签对象数组（包含颜色、描述等）
  tags_rel?: Tag[]; // 后端返回的标签对象数组（蛇形命名）
  bookshelfId?: string | null; // 所属 Bookshelf ID（可选）
  bookshelf_id?: string | null; // 后端返回的 Bookshelf ID（蛇形命名）
  dueAt?: string | null;
  createdAt?: string | null;
  updatedAt?: string | null;
  storagePath?: string; // 固定存储路径
  storage_path?: string; // 后端返回的存储路径（蛇形命名）
  previewImage?: string; // 首张图片用于预览
  preview_image?: string; // 后端返回的预览图片（蛇形命名）
  previewText?: string; // 预览文本
  preview_text?: string; // 后端返回的预览文本（蛇形命名）
  bookshelfTag?: { id: string; name: string; color?: string; icon?: string } | null; // 书架标签
  bookshelf_tag?: { id: string; name: string; color?: string; icon?: string } | null; // 后端返回的书架标签（蛇形命名）
  isPinned?: boolean; // 是否置顶
  is_pinned?: boolean; // 后端返回的置顶标记（蛇形命名）
  pinnedAt?: string | null; // 置顶时间
  pinned_at?: string | null; // 后端返回的置顶时间（蛇形命名）
  cover_image_url?: string | null; // 封面图 URL
  cover_image_display_width?: number; // 封面图显示宽度
};

export type NoteListParams = {
  q?: string;
  tag?: string;
  status?: string;
  sort?: string;
  limit?: number;
  offset?: number;
};