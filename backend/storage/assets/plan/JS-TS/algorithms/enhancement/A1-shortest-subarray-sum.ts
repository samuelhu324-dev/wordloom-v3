// A1. 最短子数组长度 ≥ target（数组 + 滑动窗口）
// A1. The shortest subarray length ≥ target (array + sliding window)

// 给定一个只包含正整数的数组 nums 和一个正整数 target，
// 请返回和 大于等于 target 的 最短连续子数组 的长度；
// 如果不存在这样的子数组，返回 0。

// Given an array nums of positive integers and a positive integer target,
// return the length of the shortest contiguous subarray whose sum is at least target.
// If no such subarray exists, return 0.

// 示例：
// 输入：nums = [2,3,1,2,4,3], target = 7
// 输出：2（因为 [4,3] 的和为 7，长度最短为 2）
// Example:
// Input: nums = [2,3,1,2,4,3], target = 7
// Output: 2 (the subarray [4,3] has sum 7 and length 2, which is minimal)

// [2,3,1,2,4,3]

function Shortestlength(nums: number[], target: number): number {

  if (nums.length < 1) throw new Error('At least length of 1')

    let shortestLength = Infinity;
    let current = 0;
    let countLength = 0;
      
      for (let i = 0; i < nums.length; i++) {

        current += nums[i]!;
        countLength += 1;

        if (countLength < shortestLength 
          && current >= target) {

          shortestLength = countLength;
          // Reset the current and countLength to 0 for next count
          current = 0;
          countLength = 0;
        }
        
      }

  return Infinity ? 0 : shortestLength;

    }

console.log(Shortestlength([1, 2, 4, 4, 7, 12], 9));
console.log(Shortestlength([1, 2, 4, 4, 7], 9));

// 问题有三个：

// 1. 不是“滑动”窗口，只是“从头重新计数”

// 每当你发现 current >= target 时，就把 current 和 countLength 都清零。
// 这会丢掉前面一部分元素，没办法考虑“跨过这个位置的更短子数组”。
// 例如：[2,3,1,2,4,3] target=7，正确答案是 [4,3]（从索引 4 开始）。
// 你的代码在前面累加超过 7 时就清零，根本看不到后面跨区间的情况。

// 2. return Infinity ? 0 : shortestLength 永远返回 0

// 这里判断的是字面量 Infinity，它永远是 truthy，所以函数永远返回 0。
// 你想写的是：shortestLength === Infinity ? 0 : shortestLength。

// 3. 没有“窗口左边界”的概念

// 你只有一个 i，相当于“右指针”，没有单独的 left 去缩小窗口长度，所以谈不上“滑动窗口”。

// 经典解法：

function shortestLength(nums: number[], target: number): number {
  if (nums.length === 0) return 0;

  let left = 0;
  let sum = 0;
  let res = Infinity;

  // 扩大窗口：
  // 1. 没到while前：开始增加右边
  // 2. 循环过while后：继续增加右边

  for (let right = 0; right < nums.length; right++){
    sum += nums[right]!; 

    // 停止增加右边，开始去掉左边
    while (sum >= target) {
      res = Math.min(res, right - left + 1);

      // 缩小窗口：去掉左边
      sum -= nums[left]!; 
      left++; 
    }
  }

  return res === Infinity ? 0 : res;
  
}

console.log(shortestLength([2, 3, 1, 2, 4, 3], 7)); // 2 -> [4,3]
console.log(shortestLength([1, 2, 4, 4, 7, 12], 9)); // 1 [9]
console.log(shortestLength([1, 2, 4, 4, 7], 20)); // 0

