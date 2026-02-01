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
// [1, 3, 4, 3, 1, 5] target: 6 > 3

function countSubarraySum(nums: number[], target: number): number{

    // key: num; value: count;
    const subarray = new Map<number, number>();
    let sum = 0;

    for (const num of nums) {
        if (num < target) {
            sum += num;
        } else if (num > target) {
            sum = num;
        } else {
            subarray.set(target, (subarray.get(target)! ?? 0) + 1);
            sum = num;
        }
            if (sum === target && num !== sum) {
            // Store the new contiguous num (key) with its count (value)
            subarray.set(target, (subarray.get(target)! ?? 0) + 1);
            sum = num;
        }
        }

    const count = subarray.get(target)!;
    return count;
        
    }

console.log(countSubarraySum([1, 1, 1], 2)); //2 
console.log(countSubarraySum([1, 3, 2, 3, 1, 5], 6)); //3 
console.log(countSubarraySum([1, 2, 3], 3)); // 2 
console.log(countSubarraySum([1, -1, 1, 1], 2)); // 2 

// 问题：
// if / else 多不多跟复杂度几乎没关系
// 你现在这版：一个 for (const num of nums)，每轮做几个常数次 if 判断 
// → 时间复杂度 O(n)，空间上 Map 里几乎只有一个 key target → O(1)
// 标准前缀和 + Map 解法：同样一个 for 循环 → 时间复杂度也是 O(n)
// Map 里最多存 n 个不同的前缀和 → 空间 O(n)。
// 区别不在复杂度，而在：

// 标准解法利用：
// sum[j] - sum[i] = target ⇔ sum[i] = sum[j] - target
// 所以可以一次性数出“对当前前缀和有贡献的所有起点”，不会漏掉。

function countSubarraySum2(nums: number[], target: number): number {
    const prefixCount = new Map<number, number>();
    prefixCount.set(0, 1);      // 和为 0 的前缀出现 1 次（空前缀）

    let sum = 0;
    let count = 0;

    for (const num of nums) {
        sum += num;             // ① 当前的前缀和 pre[j]

        const need = sum - target;           // ② 需要的 pre[i] = sum - target
        count += prefixCount.get(need) ?? 0; // ③ 把所有满足 pre[i]=need 的 i 计进答案
        // “满足 pre[i] = need 的所有 i” = “所有能和当前 j 组成一个合法子数组 [i+1..j] 的起点前一位”；
        // 它们一个 i 对应一个区间，所以这些 i 的数量就是“本轮新增加的区间数”。

        // 对于当前这个 r，在所有 更早的位置 i < j 里，
        // 有多少个满足 pre[i] = need？
        // 每个这样的 i 都j对应一个区间 [i+1 .. j]，它的和等于 target。
        // 相当于：j
        // 每次固定一个 j，Map 告诉你：
        // “以 j 结尾、和为 target 的区间有 X 个”，j
        // 然后把 X 加到 count 里。

        prefixCount.set(          // ④ 把当前 pre[j] 写进表里，供后面使用
            sum,
            (prefixCount.get(sum) ?? 0) + 1
        );
    } 
    return count;
}

// 练习 | Practice
function countSubarraySum3(nums: number[], target: number): number {

    const subarray = new Map<number, number>();
    // update the initial key and value as 0 and 1 respectively;
    subarray.set(0, 1);
    // sum = prefix(j), which represents the only pointer we should maintain
    let sum = 0;
    // i, which can be added up as the loop goes through all valid conditions
    let count = 0;

    for (const num of nums) {
        // prefix(j) = nums[0] + ... nums[j]. Treat it as your right pointer
        sum += num;
        // prefix(i) = result (the required range) - prefix(j)
        const need = sum - target;
        // get the i from the prefix(i) and add them up (if possible)
        count += subarray.get(need) ?? 0;
        // Set the prefix(j) and its i (the index and also the possible combination(s))
        subarray.set(sum, (subarray.get(sum) ?? 0) + 1);
    }

    return count;

}

console.log(countSubarraySum3([1,-1,0,2,-2,2], 0)); // 7
console.log(countSubarraySum3([1,-1,0,2,-2,2], 2)); // 7