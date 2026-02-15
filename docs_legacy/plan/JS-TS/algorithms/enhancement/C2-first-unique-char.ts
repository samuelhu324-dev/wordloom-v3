// C2. First unique character in a string (Map)
// C2. 字符串中的第一个不重复字符（Map）

// Given a string s, find the first character that appears exactly once
// and return its index. If no such character exists, return -1.
// 给定字符串 s，找到第一个在字符串中只出现一次的字符，返回它的下标；如果不存在，返回 -1。

// -----------------------------------------------------------------------------
// 1) Two‑pass + Map / 两次遍历 + Map
// -----------------------------------------------------------------------------

function firstUniqueChar(s: string): number {
  // 1. Count frequencies / 统计频次
  const freq = new Map<string, number>();

  for (const ch of s) {
    freq.set(ch, (freq.get(ch) ?? 0) + 1);
  }

  // 2. Second pass: find the first char whose count is 1
  // 2. 第二遍：找到第一个频次为 1 的字符
  for (let i = 0; i < s.length; i++) {
    if (freq.get(s[i]!) === 1) return i;
  }

  return -1;
}

// 3) Self‑test / 自测

console.log(firstUniqueChar("loveleetcode")); // 2
console.log(firstUniqueChar("aabb"));        // -1

// -----------------------------------------------------------------------------
// 2) Complexity / 复杂度
// -----------------------------------------------------------------------------
// Time 时间：O(n)  两次线性扫描
// Space 空间：O(k)  用于 Map 中不同字符的个数，k ≤ n
