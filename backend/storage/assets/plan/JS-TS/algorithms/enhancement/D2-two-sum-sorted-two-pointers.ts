// D2. Two sum in a sorted array (two pointers)
// D2. 有序数组的两数之和（双指针）

// Given an ascending sorted array nums and a target value target,
// find indices of the two numbers such that their sum is target.
// It is guaranteed that there is exactly one solution.
// 给定升序数组 nums 和目标值 target，找出两个数的下标，使得它们的和等于 target。
// 假设一定存在且唯一。

// Indices here are 0‑based.
// 这里下标用 0 开始。

// -----------------------------------------------------------------------------
// 1) Two pointers from both ends / 两端双指针
// -----------------------------------------------------------------------------

function twoSumSorted(nums: number[], target: number): [number, number] | [] {
  let left = 0;
  let right = nums.length - 1;

  while (left < right) {
    const sum = nums[left]! + nums[right]!;

    if (sum === target) {
      return [left, right];
    } else if (sum < target) {
      left++;
    } else {
      right--;
    }
  }

  // If no solution exists (in a variant without guarantee)
  // 若题目不保证有解，可以返回空数组
  return [];
  
}

// 2) Self‑test / 自测

console.log(twoSumSorted([1, 2, 4, 6, 10], 8));  // [1,3]
console.log(twoSumSorted([1, 3, 5, 9, 10], 13)); // [1,3]

// -----------------------------------------------------------------------------
// 3) Complexity / 复杂度
// -----------------------------------------------------------------------------
// Time 时间：O(n)  每个指针最多走一遍
// Space 空间：O(1)  只用常数个变量
