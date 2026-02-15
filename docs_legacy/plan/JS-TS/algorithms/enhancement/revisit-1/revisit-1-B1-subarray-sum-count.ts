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

// 1) 思路 / Idea:
// 1. 把前缀和 pre[i] 定义为从下标 0 到 i 的元素和
// 2. 任意区间 [l..r] 的和为：sum(l, r) = pre[r] - pre[l - 1]
// 3. 想要 sum[l, r] = target，等价于：pre[l - 1] = pre[r] - target
// 4. 当前右端点 r，如果我们知道每个前缀和在r之前出现过多少次， 
// 那么下标数 i = l - 1 满足 pre[i] = pre[r] - target 恰好是 以 r 结尾、和为 target 的子数组数
// 1. Define prefix sum pre[i] as the sum of elements from index 0 to 1
// 2. For any range [l..r], its sum is: sum(l, r) = pre[r] - pre[l - 1]
// 3. Try sum[l, r] = target, which is equivalent to: pre[l - 1] = pre[r] - target
// 4. For the current right endpoint r, if we know how many times each prefix sum
// has appeared before r, then the number of indices i = l - 1 satisfying
// pre[i] = pre[r] - target is exactly the number of subarrays ending at r with sum target.

// 5. 所以做法是：
//   5.1 维护一个 Map<prefixSum, count> ，表示“这个前缀和至今为止之前出现过多少次”
//   5.2 一边跑的时候扫描一次数组，一边更新前缀和和答案

// 5. So what to do:
//   5.1 Maintain a Map<prefixSum, count>, 
//   representing "how many times this prefix sum has appeared so far"
//   5.2 Update the prefix sum and the answer on the fly, while scanning the array once.

// 2) 步骤 / Steps:

function sumSubarrayCount(nums: number[], target: number): number {

// 1. 初始化 Map：
//   1.1 把前缀和 0 记录一次：prefixum.set(0, 1) 代表“空前缀”
//   1.2 这应对的是 子数组开头为 下标 0 的情况； 
// 1. Initialize the Map:
//   1.1 Set prefix 0 once: prefixsum.set(0, 1), representing "an empty prefix"
//   1.2 This handles cases where the subarray starts from index 0

    const prefixsum = new Map<number, number>();
    prefixsum.set(0, 1);
    let count = 0;
    let sum = 0;

// 2. 单次过一遍数组
// 2. One single pass over subarray

//   2.1 更新当前前缀和：sum+ = num
//   2.2 计算所需的“头部前缀和”：need = sum - target
//   2.3 prefixsum 中查 need 之前出现了几次：count += prefixsum.get(need) ?? 0;
//   2.4 把当前 sum 写回 prefixsum，给未来留位置: 
//   2.1 Update current prefix sum: sum += num
//   2.2 Compute the required "front of prefix sum": need = sum - target
//   2.3 Look up how many times need appeared before: count += prefixsum.get(need) ?? 0; 
//   2.4 Write the current sum back to prefixsum for future positions.

    for (const num of nums) {
        sum += num;
        const need = sum - target;
        count += prefixsum.get(need) ?? 0;
        prefixsum.set(sum, (prefixsum.get(sum) ?? 0) + 1);
    }

// 3. 返 count 返回答案：即所有和为 target 的子数组个数
// 3. Return the answer as count：i.e. the total number of subarrays 
// whose sum equals target.

return count;

}

// 4. 自测：
// 4. Self-test：

console.log(sumSubarrayCount([1, 3, 4, 3, 1, 5], 6)); // postive
console.log(sumSubarrayCount([2, -2, 3, -3, 0, 1, -1, 2, 3, -5, 1, 0], 0)); 
// positive + negative + 0

// 3) 复杂度 / Complexity:
//   3.1 时间：过一遍数组，每步是 Map 的读写，平均 O(1) → 总体 O(n)。
//   3.2 空间：最多存下 n + 1 个不同的前缀和 → O(n)
//   3.1 Time: One pass over the subarray. Each step is reading and writing of Map
//   with an average of O(1) → a total of O(n)
//   3.2 Space: Store at best n + 1 prefix sums → O(n)

// 4) 练习 / Practice:

function sumSubarrayCount2(nums: number[], target: number): number {

    // a Map named prefixsum with prefix sum and its frequency
    const prefixsum = new Map<number, number>();
    // Initialize the prefixsum with (0, 1)
    // that means the prefix sum of 0 appeared just once
    prefixsum.set(0, 1);

    let sum = 0;
    let count = 0;

    for (const num of nums) {
        // sum = pre[r]: the rear part [0, r]
        sum += num;
        // 1. target = sum[l, r]: the middle part [l, r]
        // 2. need = pre[l]: the front part [0, l]
        // Given the target and sum, we can find its need logically!
        const need = sum - target;
        // Get the current index i from the prefixsum.
        // This is the number of current possible ranges.
        count += prefixsum.get(need) ?? 0;
        // Remember current sum and its frequency for future call(s) of index i.
        prefixsum.set(sum, (prefixsum.get(sum) ?? 0) + 1);
    }

return count;

}

console.log(sumSubarrayCount2([1, 3, 4, 3, 1, 5], 6)); // postive
console.log(sumSubarrayCount2([2, -2, 3, -3, 0, 1, -1, 2, 3, -5, 1, 0], 0)); 
// positive + negative + 0
