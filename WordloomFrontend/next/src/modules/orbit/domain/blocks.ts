/**
 * Block 系统 - 内容块定义和工具函数
 * 支持多种 block 类型，每个 block 独立管理
 */

import { v4 as uuidv4 } from 'uuid';

/**
 * Block 类型定义
 */
export type BlockType =
  | 'paragraph'
  | 'heading'
  | 'image'
  | 'link'
  | 'checkpoint'
  | 'table'
  | 'code'
  | 'quote'
  | 'text';

/**
 * Block 内容基础类型
 */
export interface BlockContent {
  [key: string]: any;
}

/**
 * Paragraph Block
 */
export interface ParagraphBlockContent extends BlockContent {
  text: string;
}

/**
 * Heading Block
 */
export interface HeadingBlockContent extends BlockContent {
  text: string;
  level: 1 | 2 | 3 | 4 | 5 | 6;
}

/**
 * Image Block
 */
export interface ImageBlockContent extends BlockContent {
  url: string;
  description?: string; // 图片描述（包括替代文本和描述的合并）
  alt?: string; // 已弃用，向后兼容
  caption?: string; // 已弃用，向后兼容
  displayWidth?: number; // 图片显示宽度（像素）
}

/**
 * Link Block
 */
export interface LinkBlockContent extends BlockContent {
  url: string;
  title?: string;
  description?: string;
}

/**
 * Checkpoint Block
 */
export interface CheckpointBlockContent extends BlockContent {
  checkpointId: string; // 关联的checkpoint ID
}

/**
 * Table Block
 */
export interface TableBlockContent extends BlockContent {
  rows: string[][];
}

/**
 * Code Block
 */
export interface CodeBlockContent extends BlockContent {
  code: string;
  language?: string;
}

/**
 * Quote Block
 */
export interface QuoteBlockContent extends BlockContent {
  text: string;
  author?: string;
}

/**
 * 通用 Block 接口
 */
export interface Block<T extends BlockContent = BlockContent> {
  id: string;
  type: BlockType;
  content: T;
  order: number;
  createdAt?: string;
  updatedAt?: string;
}

/**
 * 特定类型的 Block 接口
 */
export type ParagraphBlock = Block<ParagraphBlockContent>;
export type HeadingBlock = Block<HeadingBlockContent>;
export type ImageBlock = Block<ImageBlockContent>;
export type LinkBlock = Block<LinkBlockContent>;
export type CheckpointBlock = Block<CheckpointBlockContent>;
export type TableBlock = Block<TableBlockContent>;
export type CodeBlock = Block<CodeBlockContent>;
export type QuoteBlock = Block<QuoteBlockContent>;

/**
 * Note 内容结构
 */
export interface NoteContent {
  blocks: Block[];
  version: string; // 版本号，便于未来迁移
}

/**
 * Block 工厂函数 - 创建不同类型的 block
 */
export function createBlock<T extends BlockType>(
  type: T,
  content: any,
  order: number = 0
): Block {
  const now = new Date().toISOString();
  return {
    id: uuidv4(),
    type,
    content,
    order,
    createdAt: now,
    updatedAt: now,
  };
}

/**
 * 创建 Paragraph Block
 */
export function createParagraphBlock(text: string = '', order: number = 0): ParagraphBlock {
  return createBlock('paragraph', { text }, order) as ParagraphBlock;
}

/**
 * 创建 Checkpoint Block
 */
export function createCheckpointBlock(checkpointId: string, order: number = 0): CheckpointBlock {
  // CheckpointBlock 保存 checkpoint ID，用于关联和加载数据
  return createBlock('checkpoint', { checkpointId }, order) as CheckpointBlock;
}

/**
 * 创建 Heading Block
 */
export function createHeadingBlock(
  text: string = '',
  level: 1 | 2 | 3 | 4 | 5 | 6 = 2,
  order: number = 0
): HeadingBlock {
  return createBlock('heading', { text, level }, order) as HeadingBlock;
}

/**
 * 创建 Image Block
 */
export function createImageBlock(
  url: string,
  description: string = '',
  order: number = 0
): ImageBlock {
  return createBlock('image', { url, description }, order) as ImageBlock;
}

/**
 * 创建 Link Block
 */
export function createLinkBlock(
  url: string,
  title: string = '',
  order: number = 0
): LinkBlock {
  return createBlock('link', { url, title, description: '' }, order) as LinkBlock;
}

/**
 * 创建 Quote Block
 */
export function createQuoteBlock(
  text: string = '',
  author: string = '',
  order: number = 0
): QuoteBlock {
  return createBlock('quote', { text, author }, order) as QuoteBlock;
}

/**
 * 创建 Code Block
 */
export function createCodeBlock(
  code: string = '',
  language: string = 'javascript',
  order: number = 0
): CodeBlock {
  return createBlock('code', { code, language }, order) as CodeBlock;
}

/**
 * 创建 Table Block
 */
export function createTableBlock(
  rows: string[][] = [['', ''], ['', '']],
  order: number = 0
): TableBlock {
  return createBlock('table', { rows }, order) as TableBlock;
}

/**
 * 创建 Text Block (Markdown 文本块)
 */
export function createTextBlock(text: string = '', order: number = 0): Block {
  return createBlock('text', { text }, order);
}

/**
 * 清理 HTML 标签，转换为纯文本
 */
function stripHtmlTags(html: string): string {
  if (!html) return '';
  return html
    .replace(/<[^>]*>/g, '')           // 移除所有 HTML 标签
    .replace(/&lt;/g, '<')              // 转换 HTML 实体
    .replace(/&gt;/g, '>')
    .replace(/&amp;/g, '&')
    .replace(/&quot;/g, '"')
    .replace(/&#39;/g, "'")
    .replace(/&nbsp;/g, ' ')            // 非断行空格转为普通空格
    .trim();
}

/**
 * 从 Markdown 转换为 NoteContent
 * （简单实现，未来可扩展）
 */
export function markdownToNoteContent(markdown: string): NoteContent {
  if (!markdown) {
    console.log('[markdownToNoteContent] markdown 为空');
    return { blocks: [], version: '1.0' };
  }

  console.log('[markdownToNoteContent] 开始解析，markdown长度:', markdown.length, '内容预览:', markdown.substring(0, 50));

  const blocks: Block[] = [];
  const lines = markdown.split('\n');
  console.log('[markdownToNoteContent] 分割为', lines.length, '行');

  let order = 0;
  let i = 0;

  while (i < lines.length) {
    const line = lines[i];

    // 先检查特殊格式（不要清理HTML），再清理
    // 处理检查点块 (<!-- CHECKPOINT_MARKER:checkpointId -->)
    if (line.includes('CHECKPOINT_MARKER')) {
      // 提取 checkpoint ID
      const match = line.match(/CHECKPOINT_MARKER:([a-f0-9-]+)/);
      if (match && match[1]) {
        console.log('[markdownToNoteContent] 找到checkpoint:', match[1]);
        blocks.push(createCheckpointBlock(match[1], order++));
      }
      i++;
      continue;
    }

    // 处理图片 - 尝试多种格式
    // 标准markdown: ![description](url)
    let imageMatch = line.match(/!\[([^\]]*)\]\(([^)]+)\)/);
    if (imageMatch) {
      const description = imageMatch[1] || '';
      const url = imageMatch[2];
      console.log('[markdownToNoteContent] 找到image block:', url);
      blocks.push(createImageBlock(url, description, order++));
      i++;
      continue;
    }

    // 尝试识别纯URL行 (以 http:// 或 https:// 开头)
    if (line.trim().startsWith('http://') || line.trim().startsWith('https://')) {
      console.log('[markdownToNoteContent] 找到URL行作为image block:', line.trim());
      blocks.push(createImageBlock(line.trim(), '', order++));
      i++;
      continue;
    }

    // 现在清理 HTML 标签以检查其他格式
    const cleanedLine = stripHtmlTags(line);

    if (!cleanedLine) {
      // 跳过空行
      i++;
      continue;
    }

    // 处理代码块 (```language)
    if (cleanedLine.startsWith('```')) {
      const language = cleanedLine.slice(3).trim() || 'javascript';
      const codeLines: string[] = [];
      i++;
      while (i < lines.length && !lines[i].startsWith('```')) {
        codeLines.push(lines[i]);
        i++;
      }
      blocks.push(createCodeBlock(codeLines.join('\n'), language, order++));
      i++; // 跳过结束的 ```
      continue;
    }

    // 处理标题
    if (cleanedLine.startsWith('# ')) {
      blocks.push(createHeadingBlock(cleanedLine.slice(2), 1, order++));
    } else if (cleanedLine.startsWith('## ')) {
      blocks.push(createHeadingBlock(cleanedLine.slice(3), 2, order++));
    } else if (cleanedLine.startsWith('### ')) {
      blocks.push(createHeadingBlock(cleanedLine.slice(4), 3, order++));
    } else if (cleanedLine.trim().startsWith('> ')) {
      blocks.push(createQuoteBlock(cleanedLine.slice(2), '', order++));
    } else {
      blocks.push(createParagraphBlock(cleanedLine, order++));
    }
    i++;
  }

  console.log('[markdownToNoteContent] 解析完成，生成了', blocks.length, '个blocks');

  return {
    blocks,
    version: '1.0',
  };
}

/**
 * 从 NoteContent 转换为 Markdown
 */
export function noteContentToMarkdown(content: NoteContent): string {
  return content.blocks
    .map((block) => {
      switch (block.type) {
        case 'paragraph':
          return (block as ParagraphBlock).content.text;
        case 'heading': {
          const heading = block as HeadingBlock;
          return `${'#'.repeat(heading.content.level)} ${heading.content.text}`;
        }
        case 'quote':
          return `> ${(block as QuoteBlock).content.text}`;
        case 'code': {
          const code = block as CodeBlock;
          return `\`\`\`${code.content.language}\n${code.content.code}\n\`\`\``;
        }
        case 'image': {
          const img = block as ImageBlock;
          // 使用 description 作为主要描述字段（向后兼容 alt 和 caption）
          const desc = img.content.description || img.content.alt || img.content.caption || '';
          return `![${desc}](${img.content.url})`;
        }
        case 'link': {
          const link = block as LinkBlock;
          return `[${link.content.title}](${link.content.url})`;
        }
        case 'checkpoint': {
          // CheckpointBlock 保存 checkpoint ID
          const cp = block as CheckpointBlock;
          if (cp.content.checkpointId) {
            return `<!-- CHECKPOINT_MARKER:${cp.content.checkpointId} -->`;
          }
          return '';
        }
        case 'table':
          return `<!-- Table Block -->`;
        default:
          return '';
      }
    })
    .join('\n\n');
}

/**
 * 获取 block 的文本预览（用于搜索/显示）
 */
export function getBlockPreview(block: Block, maxLength: number = 100): string {
  switch (block.type) {
    case 'paragraph':
      return (block as ParagraphBlock).content.text.slice(0, maxLength);
    case 'heading':
      return `# ${(block as HeadingBlock).content.text}`.slice(0, maxLength);
    case 'quote':
      return `> ${(block as QuoteBlock).content.text}`.slice(0, maxLength);
    case 'checkpoint':
      return `📋 检查点`;
    case 'image': {
      // 包括图片描述在预览中
      const img = block as ImageBlock;
      const desc = img.content.description || img.content.alt || img.content.caption || '图片';
      return `🖼️ ${desc}`.slice(0, maxLength);
    }
    case 'link':
      return `🔗 ${(block as LinkBlock).content.title || (block as LinkBlock).content.url}`;
    case 'code':
      return `\`\`\` ${(block as CodeBlock).content.language || 'code'}`;
    case 'table':
      return '📊 表格';
    default:
      return '未知块';
  }
}

/**
 * 验证 Block 的有效性
 */
export function validateBlock(block: Block): boolean {
  if (!block.id || !block.type) return false;

  switch (block.type) {
    case 'paragraph':
      return typeof (block as ParagraphBlock).content.text === 'string';
    case 'heading':
      return typeof (block as HeadingBlock).content.text === 'string'
        && [1, 2, 3, 4, 5, 6].includes((block as HeadingBlock).content.level);
    case 'checkpoint':
      return typeof (block as CheckpointBlock).content.checkpointId === 'string';
    case 'image':
      return typeof (block as ImageBlock).content.url === 'string';
    case 'link':
      return typeof (block as LinkBlock).content.url === 'string';
    default:
      return true;
  }
}

/**
 * 从 blocks 中提取第一张图片的 URL（用作 Note 预览图）
 */
export function getFirstImageUrl(blocks: Block[]): string | null {
  for (const block of blocks) {
    if (block.type === 'image') {
      const imageBlock = block as ImageBlock;
      if (imageBlock.content.url) {
        return imageBlock.content.url;
      }
    }
  }
  return null;
}

/**
 * 将 blocks 数组序列化为 JSON 字符串
 * 用于存储在 Note.blocksJson 字段中
 */
export function serializeBlocks(blocks: Block[]): string {
  try {
    return JSON.stringify(blocks);
  } catch (error) {
    console.error('Error serializing blocks:', error);
    return JSON.stringify([]);
  }
}

/**
 * 将 JSON 字符串反序列化为 blocks 数组
 * 用于从 Note.blocksJson 字段加载
 */
export function deserializeBlocks(blocksJson: string | null | undefined): Block[] {
  if (!blocksJson) {
    return [];
  }
  try {
    const parsed = JSON.parse(blocksJson);
    if (Array.isArray(parsed)) {
      return parsed.filter(validateBlock);
    }
    return [];
  } catch (error) {
    console.error('Error deserializing blocks:', error);
    return [];
  }
}

/**
 * 获取 blocks 的总文本内容（用于搜索或预览）
 */
export function getBlocksFullText(blocks: Block[]): string {
  return blocks
    .map((block) => {
      switch (block.type) {
        case 'paragraph':
          return (block as ParagraphBlock).content.text;
        case 'heading':
          return (block as HeadingBlock).content.text;
        case 'quote':
          return (block as QuoteBlock).content.text;
        case 'code':
          return (block as CodeBlock).content.code;
        case 'checkpoint':
          return '[checkpoint]';
        case 'image': {
          const img = block as ImageBlock;
          return img.content.description || img.content.url || '';
        }
        case 'link':
          return (block as LinkBlock).content.title || (block as LinkBlock).content.url;
        case 'table':
          return '[table]';
        default:
          return '';
      }
    })
    .filter((text) => text.length > 0)
    .join('\n');
}

