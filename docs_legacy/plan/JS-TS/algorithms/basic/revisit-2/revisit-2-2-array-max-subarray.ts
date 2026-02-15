// 题 2：连续子数组的最大和（Kadane 算法）
// Problem 2: Maximum Subarray Sum (Kadane's Algorithm)

// 给定一个整数数组 nums，找到一个非空连续子数组，使得这个子数组的和最大，并返回这个和。
// Given an integer array nums, find a non-empty contiguous subarray,
// making the sum of this subarray maximized, and return the sum.

//  - 输入：nums: number[]
//  - 输出：number
//  - Input: nums: number[]
//  - Output: number

function maxSubarraySum(nums: number[]): number {

    if (nums.length < 0) throw new Error('An Empty Array');

    let curr = 0;
    let best = 0;

    for (let i = 0; i < nums.length; i++) {
        
        curr = Math.max(nums[i]!, curr + nums[i]!);

        if (curr > best) {
            best = curr;
        }
    }
    return best;
}

console.log(maxSubarraySum([-2, 1, -3, 4, 0, 1, -1, -2, 5]));
console.log(maxSubarraySum([-2,1,-3,4,-1,2,1,-5,4]));



//  - 示例：[-2,1,-3,4,-1,2,1,-5,4] → 最大和子数组是 [4,-1,2,1]，和为 6。
//  - Example: [-2, 1, -3, 4, -1, 2, 1, -5, 4]
//  → the maximum-sum subarray is [4, -1, 2, 1], and the sum is 6.

// 方法一：Kadane 动态规划算法（MaxSubArray）
// Approach 1: Kadane’s Dynamic Programming Algorithm (MaxSubArray)

// 1) 思路 | Idea: 
// 该算法关心，每个下标i，恰好在 nums[i]结尾的、相邻的连续子数组的最大和
// This algorithm is concerned with, for each index i, the maximum sum of
// a contiguous subarray that ends exactly at nums[i].

// 2) 状态含义 | State meaning：
// curr：下标 i 结尾的最大连续子数组和
// curr: the consecutive maximum subarray sum ending at index i.
// best：目前为止遇到的全局最大子数组和
// best: the global maximum subarray sum seen so far.

// 3) 转移 | Transition:
// 到新元素 x = nums[i]时，有两种选择
// We have two options when we reach a new element x = nums[i]
// 1. 接在之前的子数组后面：curr + x
// 1. Attach it to the previous subarray: curr + x
// 2. x 本身的位置新建一个子数组：
// 2. Start a new subarray from x itself
// 因而 | Therefore
// curr = Math.max(x, curr + x)

// 4) 步骤 | Steps:

function MaxSubArray(nums: number[]): number {

// 1. 若数组为空则抛错。
// 1. If the array is empty, throw an error.

    if (nums.length === 0) {
        throw new Error('Nothing in this array.')
    }

// 2. 初始 curr 和 best 的值为 nums[0]
// 2. Initlize both curr and best with nums[0]

    let curr = nums[0]!;
    let best = nums[0]!;

// 3. 先是下标1，每个 x = nums[i]:
// 3. Starting from index 1, for each x = nums[i]:

    for (let i = 1; i < nums.length; i++) {

// 3.1 计算 curr = Math.max(x, curr + x).
// 3.1 Compute curr = Math.max(x, curr + x).

        const x = nums[i]!;
        curr = Math.max(x, x + curr);

// 3.2 再更新全局最大值：if (curr > best) best = curr
// 3.2 and update the global maximum: if (curr > best) best = curr

        if (best < curr) best = curr;

    }

// 4. 循环后，返回 best。
// 4. Return best after the loop.

return best;

}

// 5. 测试
// 5. Test

console.log(MaxSubArray([5, -2, 3, 0, 5, 10]));
console.log(MaxSubArray([1, 3, 5, 11, -11, 4, 6, 7]));

// 4) 复杂度 | Complexity:

// 时间时间 O(n)，空间 O(1)。
// Time O(n), space O(1).

// 5) 练习 | Practice:

function MaxSubArray1(nums: number[]): number {
    
    if (nums.length < 0) {
        throw new Error('Nothing here.');
    } 

    // curr: the current consecutive maximum sum
    let curr = nums[0]!;
    // best: the global maximum sum that we should maintain
    let best = nums[0]!;

    for (let i = 1; i < nums.length; i++) {
        const x = nums[i]!;
        // if "the current value" is greater than "the current + the previous",
        // chose the former (it starts a new array "x")
        // ; else, the latter (it picks up where the curr has been computed "x + curr").
        curr = Math.max(x, x + curr);

        if (best < curr) best = curr; 

    }

return best;

}

console.log(MaxSubArray1([5, 3, 2, -1, 5]));
console.log(MaxSubArray1([-1, 0, 2, 1, 1]));

// 方法二：显式 DP 数组
// Approach 2: Explicit DP array

// 1) 思路 | Idea: 
// 和方法一一样，只是我们明确地储存数组 dp 中每个下标结尾的子数组最大和。
// Same idea as Approach 1, just that we explicitly store the maximum subarray sum
// ending at each index in an array dp.

// 2) 状态含义 | State meaning：
// dp[i]：以下标 i 结尾的最大连续子数组和。
// dp[i]: the maximum sum of a consecutive subarray that ends at index i.

// 3) 转移 | Transition:
// 和Kadane一样, dp[0] = nums[0]; i ≥ 1：dp[i] = Math.max(nums[i], nums[i] + dp[i - 1])
// Same as Kadane, dp[0] = nums[0]; i ≥ 1：dp[i] = Math.max(nums[i], nums[i] + dp[i - 1])

// 4) 步骤 | Steps:

function MaxSubArrayDP(nums: number[]): number {

// 1. 若数组为空则抛错
// 1. If the array is empty, throw an error.

    if (nums.length < 0) {
        throw new Error('Invalid Array.')
    }

// 2. 创建长度 nums.length 的 dp 数组
// 2. Create a dp array of length nums.length

    const dp = Array(nums.length);

// 3. 初始化：dp[0] = nums[0]，并把 best = nums[0] 设为全局最大值
// 3. Initilzation: dp[0] = nums[0], and set best = nums[0] 
// as the current global maximum.

    dp[0] = nums[0]!;
    let best = nums[0]!;

// 4. 下标 1 开头，每个 i：
// 4. From index 1 to the end, for each i:

    for (let i = 1; i < nums.length; i++) {

// 4.1 计算 dp[i] = Math.max(nums[i], nums[i] + dp[i -1]);
// 4.1 Compute dp[i] = Math.max(nums[i], nums[i] + dp[i -1])

        dp[i] = Math.max(nums[i]!, nums[i] + dp[i -1]);

// 4.2 用 dp[i] 更新全局最大值
// 4.2 Update the global maximum using dp[i]

        if (dp[i] > best) best = dp[i];

    }

// 5. 遍历后返回 best
// 5. Return best after the traversal

return best;

}

// 6. 自测
// 6. Self-test

console.log(MaxSubArrayDP([2, 1, 5, 0, -1, 10]));
console.log(MaxSubArrayDP([2, 1, 5, 0, -1]));

// 4) 复杂度 | Complexity:

// 时间 O(n)，空间 O(n)（由于有明确的dp 数组）
// Time O(n), space O(n) (due to the explicit dp array)

// 5) 练习 | Practive:

function MaxSubArrayDP2(nums: number[]): number {
    if (nums.length < 0) {
        throw new Error('Oops, NOT AN ARRAY!');
    }

    // This is an array (dp) designed to store explicit maximum sum from the loop
    const dp = Array(nums.length);
    // We should initialize the dp with nums[0] as index 0's value!
    dp[0] = nums[0]!;
    // In the meantime, a global maximum sum should be maintaimed.
    let best = nums[0]!;

    for (let i = 1; i < nums.length; i++) {
        // Compare the current sum with its index and the previous
        // Creates a new array or continue summing up.
        dp[i] = Math.max(nums[i]!, nums[i] + dp[0]);

        if (dp[i] > best) best = dp[i];
    }

return best;

}

console.log(MaxSubArrayDP2([1, 5, 9, -10, 10]));
console.log(MaxSubArrayDP2([-5, 7, 9, -12, 1, 3, 5, 7]));