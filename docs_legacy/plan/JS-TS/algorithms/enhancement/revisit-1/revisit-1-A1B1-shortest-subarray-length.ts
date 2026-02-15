// -----------------------------------------------------------------------------
// AB1. 最短子数组长度 ≥ target（可含负数 / 0 / 正数 + 前缀和 + 单调队列）
// AB1. The shortest subarray length ≥ target 
// (available for negative / zero / positive numbers + prefix sum + monotonic deque)
// -----------------------------------------------------------------------------
// 题目：
// 给定一个可以包含负数、零、正数的整数数组 nums，以及一个整数 target，
// 请返回“和 大于等于 target 的 最短连续子数组”的长度；
// 如果不存在这样的子数组，返回 0。
//
// Problem:
// Given an integer array nums that may contain negative, zero, and positive values,
// and an integer target, return the length of the shortest contiguous subarray
// whose sum is at least target. If no such subarray exists, return 0.
//
// 示例：
// 输入：nums = [2, -1, 2], target = 3
// 输出：3  （整个区间 [2, -1, 2] 的和为 3，是唯一满足的子数组，长度为 3）
//
// Example:
// Input:  nums = [2, -1, 2], target = 3
// Output: 3  (the only subarray with sum ≥ 3 is [2, -1, 2], whose length is 3)
//
// -----------------------------------------------------------------------------
// 1) 关键观察 / Key observations
// -----------------------------------------------------------------------------
//
// 1. 允许负数时，经典“滑动窗口（双指针）”会失效：
//    - 扩大右端点可能增大或减少sum；
//    - 缩小左端点也可能增大或减小sum；
//    无法靠简单的 while 条件来保证不漏掉最优解。
// 1. When negatives numbers are allowed, the classic "sliding window (two pointers)"
//    will break:
//    - Extending the right boundary may incrase or decrease the sum;
//    - Shrinking the left bounary may also increase or decrease the sum;
//    We cannot rely on a simple while-condition to ensure no optimal answer be missed.
//
// 2. 换个视角：
//    用“前缀和 + 下标”就能描述所有子数组
//    - 定义前缀和：pre[i] = nums[0] + ... + nums[i - 1] (注意：加到 i-1 )
//    - 然后任意子数组 (j, i] = nums[j] ... nums[i - 1], its sum is:    
//      sum(j, i] = pre[i] - pre[j]
//    - 我们要：pre[i] - pre[j] >= target
//    - 等同于：pre[j] <= pre[i] - target
// 2. Switch perspective: 
//    describe all subarrays using "prefix sums + indices".
//    - Define prefix sums: pre[i] = nums[0] + ... nums[i - 1] (note: up to i-1)
//    - Then for any subarrays (j, i] = nums[j] ... nums[i - 1]，其和为：
//      sum(j, i] = pre[i] - pre[j]
//    - We need:    pre[i] - pre[j] >= target
//    - Equivalent: pre[j] <= pre[i] - target
//
// -----------------------------------------------------------------------------
// 2) 核心思路 / Core idea: prefix sum + monotonic deque
// -----------------------------------------------------------------------------
//
function shortestSubarraySumWithNegatives(nums: number[], target: number): number {

// 1. 先构建前缀和 pre[0..n] 其中 pre[0] = 0
// 2. 再维护一个双端队列 deque ，里面存的是“前缀和的下标”
//    j1 才 < j2 < ...，pre[j1] 才 < pre[j2] < ... (队列前缀和严格递增)
// 1. Build prefix sums pre[0..n] with pre[0] = 0
// 2. and maintain a deque of indices of prefix sums such that 
//    j1 < j2 < ... and pre[j1] < pre[j2] < ... (pre is strcitly increasing on the deque)

    // const pre: number[] = [];
    // pre[0] = 0;
    // const pre = [1];
    const n = nums.length;
    const pre = new Array<number>(n + 1);
    pre[0] = 0;

    for (let i = 0; i < nums.length; i++) {
        pre[i + 1] = pre[i]! + nums[i]!;
    }

    const deque: number[] = [];
    let res = Infinity;

    for (let i = 0; i <= n; i++) {
        const curr = pre[i]!;

// 3. 每个 i 从 0 到 n:
//   3.1 先从队头“更新一下答案 + 弹出”
//       - 只要当前前缀和 pre[i] 可以与队头 下标 j 形成符合条件的子数组：
//         pre[i] - pre[j] >= target
//       - 那么 (j, i] 就是一个符合条件的子数组，其长度为 i - j，更新答案；
//       - 同时，这个 j 之后再也不会更优（i 只会更大）可以从队头弹出
// 3. For each i from 0 to n:
//   3.1 Try to update the answer and pop this j from the front
//       - as long as the current pre[i] can form a valid subarray with the front index j:
//         pre[i] - pre[j] >= target
//       - Then (j, i] is a valid subarray with length = i - j; update the answer
//       - at the same time, this j won't be optimal any longer (due to an augmentation in i)
//         it can be poped from the front.

        // pre[i] - pre[j] >= sum[i, j]
        while (deque.length > 0 && curr - pre[deque[0]!]! >= target) {
            const j = deque.shift()!;
            res = Math.min(res, i - j);
        }

//   3.2 要保持队伍单调性，尾部下标的 pre[k] >= pre[i] 的时候：
//       - 则从后面弹出；k 永远不会比 左端点的 i 好；
//       - 因为更大的前缀和充当左端点会让
//         - 区间更长（下标恒定递增）
//         - 区间和更小（pre[i] - pre[k] ↑ = sum[i, k] ↓）
//   3.2 To keep the deque monotonic, while the tail index has pre[k] >= pre[i],
//        - pop it from the back; k will never be better than i as a left boudnary
//        - where the larger prefix sum serve as will make
//          - a range longer (index has an constant increase)
//          - a sum of range smaller (pre[i] - pre[k] ↑ = sum[i, k] ↓)

        // pre[k] >= pre[i]; k as some tail index
        // pre[i] - pre[k] >= target; so the smaller the pre[k], the better
        // and it is required to keep monotonic
        while (deque.length > 0 && pre[deque[deque.length - 1]!]! >= curr) {
            const j = deque.pop()!;
        }

        deque.push(i);
    }
    
return res;

}

console.log(shortestSubarraySumWithNegatives([2, -1, 2], 3));              // 3
console.log(shortestSubarraySumWithNegatives([1, 2, 3, 4], 6));           // 2  -> [2,4] or [3,4]
console.log(shortestSubarraySumWithNegatives([1, -1, 5, -2, 3], 3));      // 1  -> [5] or [3] etc.
console.log(shortestSubarraySumWithNegatives([2, -1, 2, -2, 3], 3));      // 2  -> [2, -1, 2] len 3; [3] len 1
console.log(shortestSubarraySumWithNegatives([-1, -2, -3], 1));           // 0  -> no such subarray

// -----------------------------------------------------------------------------
// 2) 练习 / Practice
// -----------------------------------------------------------------------------

