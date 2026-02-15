// 题 7：有序数组的两数之和（Two Pointers）
// Problem 7: Two Sum in a Sorted Array (Two Pointers)

// 给定一个升序排列的整数数组 nums 和一个目标值 target，
// 找出和为 target 的两个数的下标（假设一定存在且唯一）。
// Given an ascending (sorted) integer array nums and a target value target,
// find the indices of the two numbers whose sum equals target
// (it is guaranteed that there is exactly one solution).

// - 输入：nums = [1,2,4,6,10], target = 8 → 输出 [1,3]（2 + 6）。
// - 要求：
//   1) 时间复杂度 O(n)；
//   2) 不使用额外数组复制。
// - Example: nums = [1,2,4,6,10], target = 8 → output [1,3] (2 + 6).
// - Constraints:
//   1) Time complexity O(n);
//   2) Do not use an extra copied array.

// 1) 思路 | Idea:

function SumSorted(nums: number[], target: number): number[] {

// 1. 初始 left = 0, right = nums.length - 1
// 1. Initialize left = 0, right = nums.length - 1

    let left = 0;
    let right = nums.length - 1;

// 2. 每一步看这两位置的和：sum = nums[left] + nums[right]
// 并在指针交叉之前找到解：left < right
// 2. Look at the sum: sum = nums[left] + nums[right] at each step
// and find the solution before the pointers cross: left < right

    while (left < right) {
        
        // sum will be recomputed at each run
        const sum = nums[left]! + nums[right]!;

// 3. 利用有序条件
// 3. Make use of the sorted condition

//    3.1 如果 sum > target: 因为数组是升序，所以 nums[right]是当前最大的候选数
//    想让和变小，只能把右指针左移：right--
//    3.1 If sum > target: since array is ascending, 
//    nums[right] is the largest among current candidates
//    to maker the sum smaller, what you can do is to move right pointer left: right --

        if (sum > target) {
            right--;

//   3.2 如果 sum < target: 当前和太小，
//   想让和变大，就把指针左指针右边移：left++ ，换成更大的数
//   3.2 If sum < target: the current sum is too small
//   To make it larger, just move left point right: left++ for a bigger number

        } else if (sum < target) {
            left++;

//   3.3 如果 sum === target：找到答案，直接返回 [left, right] 
//   3.3 If sum === target: found the answer; return [left, right] directly.

        } else {
            return [left, right];
        }

    }

// 4. 如果题目不保证有解，循环后可以 return []
// 4. If the problem didn't guarantee a solution, 
// after the loop the return [] is available.

return [];

}

// 5. 自测
// 5. Self-test

console.log(SumSorted([1, 3, 5, 9, 10], 13));
console.log(SumSorted([1, 3, 5, 9, 10], 19));

// 2) 复杂度 | Complexity
// 时间：指针最多各走一遍，整体 O(n)
// 空间：只用了固定数量变量 (left, right, sum) O(1) 额外空间
// Time: each pointer moves at mosr across the array once: O(n)
// Space: only a few scalar variables are used: O(1) extra space

// 3) 练习 | Practice

function SumSorted2(nums: number[], target: number): number[] {
    
    // We can set the variables as follows 
    // since the numbers are sorted in ascending order
    let left = 0;
    let right = nums.length -1;

    while (left < right) {

        // At each run, sum will be refreshed as a new number
        // so the while loop must contain the sum variable
        const sum = nums[left]! + nums[right]!;

        if (sum < target) {
            left++;
        } else if (sum > target) {
            right--;
        } else {
            return [left, right];
        }
    }
return [];
}

console.log(SumSorted2([1, 3, 5, 9, 10], 13));
console.log(SumSorted2([1, 3, 5, 9, 10], 19));
