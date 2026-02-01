// L1. Climbing Stairs
// L1. 爬楼梯

// You are climbing a staircase. It takes n steps to reach the top.
// Each time you can climb 1 or 2 steps. 
// In how many distinct ways can you climb to the top?
// 爬 n 阶楼梯，每次可以爬 1 或 2 阶，问有多少种不同爬法。

// -----------------------------------------------------------------------------
// 1. Fibonacci 
// -----------------------------------------------------------------------------

function climbStairs(n: number): number {

  if (n <= 2) return n;

  let prev2 = 1; // f(i-2)
  let prev1 = 2; // f(i-1)

  for (let i = 3; i <= n; i++) {
    const curr = prev1 + prev2; // f(i)
    prev2 = prev1;
    prev1 = curr;
  }

  return prev1;
}

console.log(climbStairs(5));

// -----------------------------------------------------------------------------
// 2. recursion + memo 
// -----------------------------------------------------------------------------

// -----------------------------------------------------------------------------
// 1) Idea / 思路
// -----------------------------------------------------------------------------

// 1. Define f(n) = ways to reach step n
// 2. Transition: last move is either 1 or 2 steps ->
//    f(n) = f(n - 1) + f(n - 2).
// 3. Plain recursion will recompute the same f(k) many times.
// 4. Use an array memo where memo[n] stores the already-computed result of f(n)
//    On each call:
//    - If n <= 2 , directly return n (base cases).
//    - If memo[n] is not undefined, return it (hit cache).
//    - Otherwise, compute f(n-1) + f(n-2), store into memo[n], then return it.

// 1. 定义 f(n) 为“到步骤 n 的走法”
// 2. 转变：最后一步要么走 1 阶 要么走 2 阶；
// 3. 纯递归会重算同个 f(k) 很多次
// 4. 用数组 memo 其中 memo[n] 存 已经计算好的的 f(n) 结果
//    每次一调用：
//    - 若 n <= 2，直接地就返回 n (基本情况)
//    - 若 memo[n] 不是 undefined ，返回 (命中缓存)
//    - 否则，计算 f(n-1) + f(n-2) ，存进 memo[n] ，然后返回

function climbStairsmemo(n: number, memo: number[]): number {
  // f(1) = 1 [1]; f(2) = 2 [1,1] [2]
  if (n <= 2) return n;
  // cache memo[n] for call back (from left to right)
  if (memo[n] !== undefined) return memo[n];

  memo[n] = climbStairsmemo(n-1, memo) + climbStairsmemo(n-2, memo);

  return memo[n];
} 

console.log(climbStairsmemo(5,[]));
console.log(climbStairsmemo(8,[]));

// -----------------------------------------------------------------------------
// 3. DP 
// -----------------------------------------------------------------------------

function climbStairsDP(n: number): number {
  if (n <= 2) return n;

  const dp: number[] = [];
  dp[1] = 1;
  dp[2] = 2;

  for (let i = 3; i <= n; i++) {
    dp[i] = dp[i - 1]! + dp[i - 2]!;
  }
  return dp[n]!;
}
