// B1. 统计和为 target 的子数组个数（数组 + 前缀和 + Map）
// B1. Count subarrays with sum equal to target (array + prefix sum + Map)

// 给定一个整数数组 nums（可以包含负数、零、正数）和一个整数 target，
// 请返回和等于 target 的连续子数组的个数。

// Given an integer array nums (can contain negative, zero, and positive values)
// and an integer target, return the number of contiguous subarrays whose sum equals target.

// 示例：
// 输入：nums = [1,1,1], target = 2
// 输出：2（子数组 [1,1] 有两段）
// Example:
// Input: nums = [1,1,1], target = 2
// Output: 2 (there are two subarrays [1,1] whose sum is 2)


function subarraySumCount(nums: number[], target: number): number {

    // key: prefix sum; value: its frequency
    // Note: key is not an "index"[i] !
    const frequency = new Map<number, number>()
    frequency.set(0, 1);
    let prefixsum = 0;
    let count = 0;

    for (const num of nums) {
        // 1. prefixsum = prefix[i]
        // 2. target = sum(j, i]
        // 3. prefix[i] - prefix[j] = sum(j, i]
        //    thus: prefix[j] = prefix[i] - sum(j, i]
        //    need = prefix[j] 
        //    0 <= j < i <= n
         prefixsum += num;
         const need = prefixsum - target;
         count += frequency.get(need) ?? 0;
         frequency.set(prefixsum, (frequency.get(prefixsum) ?? 0) + 1)
    }

    return count;

}

console.log(subarraySumCount([1, 1, 2, 2, 4], 4)); // 3
console.log(subarraySumCount([1, 1, 2], 2)); // 2
console.log(subarraySumCount([1, -1, 0, 2, -2], 0)); // 6
