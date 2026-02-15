// A0. Minimum difference pair (array + sorting)
// A0. 最小差值对（数组 + 排序）

// Given an integer array nums (length ≥ 2), return the minimum absolute
// difference between any two distinct elements.
// 给定整数数组 nums（长度 ≥ 2），返回任意两个不同元素之间的最小绝对差值。

// Example: [3, 8, 2] → |3 - 2| = 1

// -----------------------------------------------------------------------------
// 1) Sort + scan adjacent elements / 排序 + 扫描相邻元素
// -----------------------------------------------------------------------------

function minDiffPair(nums: number[]): number {
  if (nums.length < 2) {
    throw new Error("Array must contain at least two elements");
  }

  const arr = [...nums].sort((a, b) => a - b);

  let ans = Infinity;

  for (let i = 1; i < arr.length; i++) {
    const diff = arr[i]! - arr[i - 1]!;
    if (diff < ans) ans = diff;
  }

  return ans;
}

// 2) Self‑test / 自测

console.log(minDiffPair([2, 7, 9, -1, 3]));
console.log(minDiffPair([-1, 0, 1, 2]));
console.log(minDiffPair([-1, -3, 5, 3, 2]));

// -----------------------------------------------------------------------------
// 3) Complexity / 复杂度
// -----------------------------------------------------------------------------
// Time 时间：O(n log n)  主要来自排序
// Space 空间：O(n)       用于排序时的拷贝（如果允许原地排序则为 O(1) 额外空间）
