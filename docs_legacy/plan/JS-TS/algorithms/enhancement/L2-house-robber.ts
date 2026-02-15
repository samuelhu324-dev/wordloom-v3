// L2. House Robber
// L2. 打家劫舍 I

// You are a robber who wants to rob houses along a street.
// Adjacent houses cannot be robbed on the same night. Each house has a certain amount of money.
// Return the maximum amount you can rob.
// 一条街上有多间房，相邻的房子不能同时偷，每间房有一定金额，求能偷到的最大金额。

// -----------------------------------------------------------------------------
// 1) 思路 / idea
// -----------------------------------------------------------------------------
// 
// 1. State definition
//    Use dynamic programming,
//    - Let dp[i] be the maximum money you can rob from houses 0..i
//      Note: House i may or may not be robbed, 
//            just the optimal result of first i + 1 houses
// 2. Transition: 
//    two choices for house i
//    - No robbery of house i 
//      - Then the best you can do is exactly the best from 0..i-1
//      - gain = dp[i-1]
//    - Robbery of hosue i
//      - Then you are not allowed to rob i-1
//        so you combine the best from 0..i-2 with nums[i]
//        gain = dp[i-2] + nums[i]
// 3. Base cases:
//    - Only one: dp[0] = nums[0]
//    - Two houses 0, 1: either rob 0 or 1, take the bigger one:
//      dp[1] = max(nums[0],nums[1])
// 4. Answer & Complexity
//    - Fill dp from i = 2 to n - 1 ; the answer is dp[n-1]
//    - Since dp[i] only depends on dp[i-1] and dp[i-2]
//    - we can keep just two variables:
//      prev2 = dp[i-2], prev1 = dp[i-1]
//      cur = max(prev1, prev2 + nums[i])
//    - Time: O(n)
//    - Exra space: O(1) with the two-variable optimization
//
// 1. 状态定义
//    用动态规划
//    - 设 dp[i] 为你可以从第 0..i 间房能偷到最多的钱数
//      注意： “第 i 间房可以偷，也可以不偷”，只是“前 i + 1 间房的最优结果”
// 2. 状态转移：
//    偷第 i 间房两种选择
//    - 不偷第 i 间房
//      - 那么偷所能及的最佳方案恰好是从第 0 间偷到第 i-1 间的最佳方案
//      - 收益 = dp[i-1]
//    - 偷第 i 间房
//      - 那么不可以偷第 i-1 间
//      - 只好兼具 第 0 间 .. i-2 间的最佳方案与 nums[i]
//      - 收益 = dp[i-2] + nums[i]
// 3. 初始条件：
//    - 只有一间房 0 时：dp[0] = nums[0]
//    - 有两间房 0,1 时：
//      要么偷 0 ，要么偷 1 ，取较大：dp[1] = max(nums[0],nums[1])
// 4. 答案和复杂度
//    - 从第 i = 2 推到第 n - 1 ;答案就是 dp[n-1]
//    - 每个 dp[i] 只依赖 dp[i-1] 和 dp[i-2]
//      所以可以留下两个变量：
//      prev2 = dp[i-2], prev1 = dp[i-1]
//      cur = max(prev1, prev2 + nums[i])
//    - 时间: O(n)
//    - 额外空间: O(1) (用两个变量实现)

function rob(nums: number[]): number {
  const n = nums.length;
  if (n === 0) return 0;
  if (n === 1) return nums[0]!;

  let prev2 = nums[0]!;
  let prev1 = Math.max(nums[0]!, nums[1]!);

  for (let i = 2; i < n; i++) {
    // dp[i] = max(dp[i-1], dp[i-2] + nums[i])
    const curr = Math.max(prev1, prev2 + nums[i]!); // dp[i]
    // prepared for next run
    prev2 = prev1; // dp[i-2] = dp[i-1]
    prev1 = curr   // dp[i-1] = dp[i]
  }

  return prev1; // dp[n-1]
} 

console.log(rob([9,7,5,3,1,8]));


