// Cover Placeholder Generator
// 仅占位策略：根据 title + id 生成稳定颜色与字符/图形
// Sunset: 若未来接入真实封面上传，保留此方法用于回退。

const PALETTE = [
  '#1E3A8A', '#065F46', '#7C2D12', '#5B21B6', '#0C4A6E', '#9D174D', '#374151', '#4D7C0F', '#78350F', '#2563EB', '#BE185D', '#0F766E'
];

// 简单 FNV-1a 哈希
function hash(input: string): number {
  let h = 0x811c9dc5;
  for (let i = 0; i < input.length; i++) {
    h ^= input.charCodeAt(i);
    h = (h * 0x01000193) >>> 0;
  }
  return h >>> 0;
}

export interface CoverPlaceholder {
  bgColor: string;
  glyph: string; // 目前使用首字母，可扩展为几何形状
}

export interface CoverPlaceholderOptions {
  seed?: string;
}

export function generateCoverPlaceholder(title: string, idOrOptions?: string | CoverPlaceholderOptions): CoverPlaceholder {
  const normalizedTitle = (title || 'Book').trim() || 'Book';
  let seed: string;
  if (typeof idOrOptions === 'string') {
    seed = `${normalizedTitle}|${idOrOptions}`;
  } else if (idOrOptions && typeof idOrOptions === 'object' && idOrOptions.seed) {
    seed = idOrOptions.seed;
  } else {
    seed = normalizedTitle;
  }

  const key = seed.toLowerCase();
  const h = hash(key);
  const color = PALETTE[h % PALETTE.length];
  const glyph = (normalizedTitle[0] || 'B').toUpperCase();
  return { bgColor: color, glyph };
}

// 提供一个渲染帮助（可选）
// 原 .ts 文件中不再包含 JSX；如需渲染请在 .tsx 中自行调用 generateCoverPlaceholder。
