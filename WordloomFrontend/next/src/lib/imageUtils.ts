/**
 * 从 HTML 内容中提取第一张图片的 src
 */
export function extractFirstImageFromHtml(html: string): string | null {
  if (!html) return null;
  const match = html.match(/<img[^>]+src=["']([^"']+)["']/);
  const url = match ? match[1] : null;
  console.log("提取的图片 URL:", url);
  return url;
}

/**
 * 从 HTML 内容中提取第一句话（非空行）
 * @param html HTML 内容
 * @param maxLength 最大长度（超过会截断并加省略号）
 */
export function extractFirstSentenceFromHtml(html: string, maxLength: number = 100): string | null {
  if (!html) return null;

  // 移除 HTML 标签
  const text = html
    .replace(/<[^>]*>/g, "") // 移除所有 HTML 标签
    .replace(/&nbsp;/g, " ") // 替换 HTML 空格
    .replace(/&lt;/g, "<")
    .replace(/&gt;/g, ">")
    .replace(/&quot;/g, '"')
    .replace(/&#39;/g, "'")
    .replace(/&amp;/g, "&"); // 最后处理 &amp 防止重复转义

  // 按行分割，过滤空行
  const lines = text
    .split("\n")
    .map((line) => line.trim())
    .filter((line) => line.length > 0);

  if (lines.length === 0) return null;

  // 获取第一行
  let firstSentence = lines[0];

  // 截断超长文本
  if (firstSentence.length > maxLength) {
    firstSentence = firstSentence.substring(0, maxLength).trim() + "...";
  }

  return firstSentence;
}