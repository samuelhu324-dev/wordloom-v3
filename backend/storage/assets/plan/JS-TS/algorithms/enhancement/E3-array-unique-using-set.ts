// E3. Remove duplicates from array while preserving order (Set)
// E3. 数组去重并保持原顺序（Set）

// Given an array of numbers, return a new array with duplicates removed,
// keeping the order of first occurrence.
// 给定一个数字数组，返回去重后的新数组，保留元素第一次出现的顺序。

// Example: [2, 3, 2, 2, 1] → [2, 3, 1]

// -----------------------------------------------------------------------------
// 1) For‑loop + Set / for 循环 + Set
// -----------------------------------------------------------------------------

function uniqueWithSet(nums: number[]): number[] {
  const seen = new Set<number>();
  const result: number[] = [];

  for (const num of nums) {
    if (!seen.has(num)) {
      seen.add(num);
      result.push(num);
    }
  }

  return result;
}

// 2) Self‑test / 自测

console.log(uniqueWithSet([2, 3, 2, 2, 1])); // [2,3,1]
console.log(uniqueWithSet([4, 3, 4, 3]));   // [4,3]

// -----------------------------------------------------------------------------
// 3) Complexity / 复杂度
// -----------------------------------------------------------------------------
// Time 时间：O(n)  一次线性扫描
// Space 空间：O(k)  Set + 结果数组，k 为不同元素个数，k ≤ n
