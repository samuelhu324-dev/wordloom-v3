// L1. Climbing Stairs
// L1. 爬楼梯

// You are climbing a staircase. It takes n steps to reach the top.
// Each time you can climb 1 or 2 steps. 
// In how many distinct ways can you climb to the top?
// 爬 n 阶楼梯，每次可以爬 1 或 2 阶，问有多少种不同爬法。

// -----------------------------------------------------------------------------
// 1. Fibonacci 
// -----------------------------------------------------------------------------

function climbingStairs_Fibonacci(n: number) {
    // With 1 step left: [1] 
    let prev1 = 1;
    // With 2 steps left: [1,1] [2]
    let prev2 = 2;

    for (let i = 2; i < n; i++) {
        // in case of mixing values like these: 
        // prev2 = prev1 + prev2
        // prev1 = prev2
        // and that's where const curr = prev1 + prev2 comes in
        const curr = prev1 + prev2; 
        prev1 = prev2; // for[i - 2] = f[i - 1]
        prev2 = curr // for[i] = f[i -1]
    }
    return prev2;
}

console.log(climbingStairs_Fibonacci(5));
console.log(climbingStairs_Fibonacci(8));


// -----------------------------------------------------------------------------
// 2. recursion + memo 
// -----------------------------------------------------------------------------

function climbingStairs_memo(n: number, memo: number[]): number {
    // two cases: 1) one left - [1]; 2) two left - [1,1] [2]
    if (n <= 2) return n;
    if (memo[n] !== undefined) return memo[n];

    // with each memo[n] stored in the array,
    // you may want to call them back later for climbingStairs_memo(n - 2, memo)
    // to avoid superfluous computations
    memo[n] = climbingStairs_memo(n - 1, memo) + climbingStairs_memo(n - 2, memo);
    return memo[n]; 
}

console.log(climbingStairs_memo(5,[]));
console.log(climbingStairs_memo(8,[]));