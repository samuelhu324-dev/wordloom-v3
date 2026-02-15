// 题 5：第一个不重复的字符（Map）
// 给定字符串 s，找到第一个在字符串中只出现一次的字符，返回它的下标；如果不存在，返回 -1。

function firstUniqChar(s: string): number {
  const freq = new Map<string, number>();

  // 第一次遍历：统计频次

  // 第二次遍历：找第一个频次为 1 的字符

  for (const char of s) {
    freq.set(char, (freq.get(char) ?? 0) + 1);
  };

  for (let i = 0; i < s.length; i++) {
    if (freq.get(s[i]!) === 1) {
        return i;
    }
  }

  return -1;
}


// 简单自测
console.log(firstUniqChar('leetcode'));     // 0
console.log(firstUniqChar('loveleetcode')); // 2
console.log(firstUniqChar('aabb'));         // -1