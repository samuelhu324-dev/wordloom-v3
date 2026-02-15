//
// -----------------------------------------------------------------------------
// AB1. The shortest subarray length ≥ target 
// (available for negative / zero / positive numbers + prefix sum + monotonic deque)c
// AB1. 最短子数组长度 ≥ target（可含负数 / 0 / 正数 + 前缀和 + 单调队列）
// -----------------------------------------------------------------------------
//
// Problem:
// Given an integer array nums that may contain negative, zero, and positive values,
// and an integer target, return the length of the shortest contiguous subarray
// whose sum is at least target. If no such subarray exists, return 0.
//
// 题目：
// 给定一个可以包含负数、零、正数的整数数组 nums，以及一个整数 target，
// 请返回“和 大于等于 target 的 最短连续子数组”的个数；
// 如果不存在这样的子数组，返回 0。
//
// Example: 
// Input: nums = [2,-1,2], target = 3
// Output: 3 (the only subarray with sum ≥ 3 is [2,-1,2], whose length is 3)
// 示例：
// 输入：nums = [2,-1,2], target = 3
// 输出：3（整个区间 [2,-1,2] 的和为 3，是唯一满足的子数组，长度为 3）
//

function SubarrayAll(nums: number[], target: number): number {
    
    if (nums.length === 0) throw new Error('invalid array');

    // prefix[0] = 0
    const prefixsum: number[] = [0];
    let sum = 0;
    // cannot be 0; 0 is included as "length"
    let answer = Infinity;

    for (let i = 0; i < nums.length; i++) {
        sum += nums[i]!;
        prefixsum.push(sum);
    }

    const deque: number[] = [];

    // each i is an index of its prefixsum;
    for (let i = 0; i < prefixsum.length; i++) {

        const curr = prefixsum[i]!;
   
        while (deque.length > 0 && curr - prefixsum[deque[0]!]! >= target) {    
            const j = deque.shift()!;
            answer = Math.min(answer, i - j);
        }

        while (deque.length > 0 && curr <= prefixsum[deque[deque.length - 1]!]!) {
            deque.pop();
        }

        deque.push(i);
    }

    return answer === Infinity ? 0 : answer;
}

console.log(SubarrayAll([1,-1,2,3],3));
console.log(SubarrayAll([1,3,-3,5,7],13))
