// -----------------------------------------------------------------------------
// AB1. 最短子数组长度 ≥ target（可含负数 / 0 / 正数 + 前缀和 + 单调队列）
// AB1. The shortest subarray length ≥ target 
// (available for negative / zero / positive numbers + prefix sum + monotonic deque)
// -----------------------------------------------------------------------------

// 题目：
// 给定一个可以包含负数、零、正数的整数数组 nums，以及一个整数 target，
// 请返回“和 大于等于 target 的 最短连续子数组”的长度；
// 如果不存在这样的子数组，返回 0。

// Problem:
// Given an integer array nums that may contain negative, zero, and positive values,
// and an integer target, return the length of the shortest contiguous subarray
// whose sum is at least target. If no such subarray exists, return 0.

// 示例：
// 输入：nums = [2, -1, 2], target = 3
// 输出：3  （整个区间 [2, -1, 2] 的和为 3，是唯一满足的子数组，长度为 3）

// Example:
// Input:  nums = [2, -1, 2], target = 3
// Output: 3  (the only subarray with sum ≥ 3 is [2, -1, 2], whose length is 3)

// -----------------------------------------------------------------------------
// 1) 关键观察 / Key observations
// -----------------------------------------------------------------------------
//
// 1. 允许负数时，经典“滑动窗口（双指针）”会失效：
//    - 扩大右端点时，sum 可能变大也可能变小；
//    - 缩小左端点时，sum 也可能变大也可能变小；
//    无法用简单的 while 条件来保证不漏掉最优解。
//
// 2. 换一个视角：用“前缀和 + 下标”来描述所有子数组。
//    定义前缀和：pre[i] = nums[0] + ... + nums[i - 1]  （注意是到 i-1）
//    那么任意子数组 (j, i] = nums[j] ... nums[i - 1] 的和为：
//        sum(j, i] = pre[i] - pre[j]
//
//    我们需要：pre[i] - pre[j] >= target
//    等价于：  pre[j] <= pre[i] - target
//
// 3. 我们想找到“对每个 i，所有满足 pre[j] <= pre[i] - target 的最小 i - j”。
//    为了 O(n) 完成这个目标：
//    - 按 i 从左到右遍历前缀和；
//    - 用一个“前缀和值单调递增”的下标队列（单调队列 / monotonic deque）
//      来维护一批“潜在的 j 候选”。
//
// -----------------------------------------------------------------------------
// 2) 核心思路 / Core idea: prefix sum + monotonic deque
// -----------------------------------------------------------------------------
//
// 算法逻辑（中文）：
// 1. 先构建前缀和 pre[0..n]，其中 pre[0] = 0。
// 2. 维护一个双端队列 deque，里面存的是“前缀和的下标”，并保证：
//    - 对于队列中的下标 j1 < j2 < ...，有 pre[j1] < pre[j2] < ...   （前缀和严格递增）
// 3. 对于每一个 i 从 0 到 n：
//    3.1 先尝试从队头开始“更新答案 + 弹出”：
//        只要当前前缀和 pre[i] 与队头 j 满足：
//             pre[i] - pre[j] >= target
//        那么 (j, i] 就是一个合法子数组，其长度为 i - j，更新答案；
//        同时，这个 j 之后再也不会更优（以后 i 只会更大），可以从队头弹出。
//    3.2 再维护队列单调性，从队尾开始：
//        只要 pre[队尾] >= pre[i]，说明这个“旧下标”永远不如当前 i 好，
//        因为：用更大的前缀和去做“左端点”只会让区间和更小 / 更难 ≥ target，
//        直接把这些下标从队尾弹出。
//    3.3 把当前下标 i 入队（从队尾 push）。
//
// Algorithm (English):
// 1. Build prefix sums pre[0..n] with pre[0] = 0.
// 2. Maintain a deque of indices of prefix sums such that
//    j1 < j2 < ... and pre[j1] < pre[j2] < ... (pre is strictly increasing on the deque).
// 3. For each i from 0 to n:
//    3.1 While the current pre[i] can form a valid subarray with the front index j:
//        if pre[i] - pre[j] >= target, then (j, i] is a valid subarray, length = i - j;
//        update the answer and pop this j from the front.
//    3.2 To keep the deque monotonic, while the tail index k has pre[k] >= pre[i],
//        pop it from the back, because k will never be better than i as a left boundary.
//    3.3 Push the current index i to the back.
//
// 最终，答案是遍历过程中的最小长度；若始终没有合法子数组，则返回 0。
// Finally, the answer is the minimal length found during the scan;
// if no valid subarray exists, return 0.

// -----------------------------------------------------------------------------
// 3) 实现 / Implementation
// -----------------------------------------------------------------------------

function shortestSubarraySumWithNegatives(nums: number[], target: number): number {
    const n = nums.length;
    const pre = new Array<number>(n + 1);
    pre[0] = 0;

    for (let i = 0; i < n; i++) {
        pre[i + 1] = pre[i]! + nums[i]!;
    }

    // 双端队列，存的是前缀和的下标
    // Deque storing indices of prefix sums
    const deque: number[] = [];

    let res = Infinity;

    for (let i = 0; i <= n; i++) {
        const curr = pre[i]!;

        // 3.1 从队头尝试更新答案：pre[i] - pre[deque[0]] >= target
        //     While the front index gives a valid subarray, update result and pop it.
        while (deque.length > 0 && curr - pre[deque[0]!]! >= target) {
            const j = deque.shift()!;
            res = Math.min(res, i - j);
        }

        // 3.2 维护前缀和单调递增：从队尾弹出所有 pre[tail] >= pre[i]
        //     Maintain monotonicity: remove all indices with pre[tail] >= pre[i].
        while (deque.length > 0 && pre[deque[deque.length - 1]!]! >= curr) {
            deque.pop();
        }

        // 3.3 当前下标 i 入队
        //     Push current index.
        deque.push(i);
    }

    // 若 res 仍为 Infinity，说明不存在满足条件的子数组
    // If res is still Infinity, no valid subarray exists.
    return res === Infinity ? 0 : res;
}

// -----------------------------------------------------------------------------
// 4) 自测 / Self-test
// -----------------------------------------------------------------------------

console.log(shortestSubarraySumWithNegatives([2, -1, 2], 3));              // 3
console.log(shortestSubarraySumWithNegatives([1, 2, 3, 4], 6));           // 2  -> [2,4] or [3,4]
console.log(shortestSubarraySumWithNegatives([1, -1, 5, -2, 3], 3));      // 1  -> [5] or [3] etc.
console.log(shortestSubarraySumWithNegatives([2, -1, 2, -2, 3], 3));      // 1  -> [2, -1, 2] len 3; [3] len 1
console.log(shortestSubarraySumWithNegatives([-1, -2, -3], 1));           // 0  -> no such subarray

// -----------------------------------------------------------------------------
// 5) 练习版本 / Practice version
// -----------------------------------------------------------------------------

function shortestSubarraySumWithNegatives2(nums: number[], target: number): number {
    const n = nums.length;
    const pre = new Array<number>(n + 1);
    pre[0] = 0;

    for (let i = 0; i < n; i++) {
        pre[i + 1] = pre[i]! + nums[i]!;
    }

    const deque: number[] = [];
    let best = Infinity;

    for (let i = 0; i <= n; i++) {
        const curr = pre[i]!;

        while (deque.length > 0 && curr - pre[deque[0]!]! >= target) {
            const j = deque.shift()!;
            best = Math.min(best, i - j);
        }

        while (deque.length > 0 && pre[deque[deque.length - 1]!]! >= curr) {
            deque.pop();
        }

        deque.push(i);
    }

    return best === Infinity ? 0 : best;
}

console.log(shortestSubarraySumWithNegatives2([2, -1, 2], 3));
console.log(shortestSubarraySumWithNegatives2([1, 2, 3, 4], 6));
console.log(shortestSubarraySumWithNegatives2([1, -1, 5, -2, 3], 3));
console.log(shortestSubarraySumWithNegatives2([-1, -2, -3], 1));