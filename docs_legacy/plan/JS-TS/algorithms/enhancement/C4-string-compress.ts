// C4. String compression (runs of repeated chars)
// C4. 压缩字符串（连续相同字符压缩）

// Given a string s containing only letters, compress every run of consecutive
// identical characters into "char + count"; when count is 1, the number can be omitted.
// 输入只包含字母的字符串 s，把每一段连续相同字符压缩成 "字符 + 次数"，次数为 1 时可省略。
// 例如："aaabbc" → "a3b2c"，"abcd" → "abcd"。

// -----------------------------------------------------------------------------
// 1) Two‑pointers over runs / 双指针扫描每一段
// -----------------------------------------------------------------------------

function compressString(s: string): string {
  const res: string[] = [];
  let i = 0;

  while (i < s.length) {
    const ch = s[i]!;
    let j = i + 1;
    let count = 1;

    while (j < s.length && s[j] === ch) {
      count++;
      j++;
    }

    // count > 1 时拼上次数，否则只保留字符本身
    res.push(count > 1 ? ch + String(count) : ch);

    i = j; // 下一段从 j 开始
  }

  return res.join("");
}

// 2) Self‑test / 自测

console.log(compressString("aaabbc"));        // "a3b2c"
console.log(compressString("abcd"));         // "abcd"
console.log(compressString("aaaavsswwwqqqa"));

// -----------------------------------------------------------------------------
// 3) Complexity / 复杂度
// -----------------------------------------------------------------------------
// Time 时间：O(n)  只线性扫描一遍
// Space 空间：O(n)  结果字符串所需空间
