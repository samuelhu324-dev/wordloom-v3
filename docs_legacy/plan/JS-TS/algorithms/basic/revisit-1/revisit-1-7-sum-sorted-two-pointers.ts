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

function SumSorted(nums: number[], target: number): number[] | null{
    let left = 0;
    let right = nums.length - 1;

    while (left < right) {

// Q&A1 - sum needs to be recomputed in two pointers problem.

        const sum = nums[left]! + nums[right]!;
        if (sum > target) {
            right --;
        } else if (sum < target) {
            left ++;
        } else {

// Q&A2 - let result: number[] = [] -- result.push(left, right); -- return [];
            return [left, right];
        }
    }
    return null;
}

// self-test:
console.log(SumSorted([1, 2, 4, 6, 10], 8));
console.log(SumSorted([1, 4, 7, 8], 5));
