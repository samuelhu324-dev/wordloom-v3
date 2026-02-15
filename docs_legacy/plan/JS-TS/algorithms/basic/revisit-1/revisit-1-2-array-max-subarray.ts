// 题 2：连续子数组的最大和（Kadane 算法）
// Problem 2: Maximum Subarray Sum (Kadane's Algorithm)

// 方法一：动态规划 Kadane 算法
// Approach 1: Dynamic Programming – Kadane's Algorithm

// 描述：给定一个整数数组 nums ，找到一个具有最大和的连续子数组
// （子数组最少包含一个元素），返回其最大和。
// Description: Given an integer array nums, find a contiguous subarray
// (containing at least one element) which has the largest sum and return that sum.

function MaxSubArray(nums: number[]): number {

// 1. 取第一个元素作为初始值，使用 ! 告诉 TS 这里一定有值
// 1. Take the first element as the initial value; 
// use ! to tell TS that there is definitely a value here.

// Q&A1 - Correct brace range (especially for if)

    if (nums.length < 1) {
        throw new Error('nums must be non-empty with at least 1 element in its arrary')
    }

// Q2 - Rules of "!" / Why use const in the original version? 
// / Rules of const x = nums[i] in consecutive rounds.
// 第 1 轮：{ const x = nums[1]; } - 只在这一轮的花括号里存在
// 第 2 轮：{ const x = nums[2]; } - 这是另一个全新的 x，和上一轮那个无关
// Round 1: { const x = nums[1]; } - exists only inside the braces of this iteration.
// Round 2: { const x = nums[2]; } - this is a brand‑new x, unrelated to the previous one.

    let curr = nums[0]!;
    let best = nums[0]!;

    for (let i = 1; i < nums.length; i++) {

        const x = nums[i]!;
// 2. 确定连续和与当前nums[i]谁大，更大的赋值给curr；
// 2. Decide which is larger, the running sum plus nums[i] or nums[i] itself, 
// and assign the larger one to curr.
// 3. 然后把 curr 与 best 比较，维护全局最大值；
// 3. Then compare curr with best to maintain the global maximum.
        curr = Math.max (x, curr + x);

        if (curr > best) {
            best = curr;
        }
    }

  return best
    
}

// 4. self-test

console.log(MaxSubArray([0, -2, 1, 4, 5]))

// 方法二：显式 DP 数组
// Approach 2: Explicit DP array

// 描述：使用一个 dp 数组来存储以每个位置结尾的最大子数组和。
// Description: Use a dp array 
// to store the maximum subarray sum ending at each position.

function MaxSubArrayDP(nums: number[]): number {
    if (nums.length < 1) {
        throw new Error('Cannot be computed using less than 1 number!')
    }

// 1.  开一个和 nums 一样长的 dp 数组，避免 “可能为 undefined” 报错
// 1. Create a dp array with the same length as nums 
// to avoid “possibly undefined” errors.

// Q&A3 - Array vs literal and .fill method
// const a = new Array(5);      // [empty × 5]
// a.fill(0);                   // [0, 0, 0, 0, 0]
// const b = [1, 2, 3, 4, 5];
// b.fill(9, 1, 4);             // 下标 1 到 3 填 9 -> [1, 9, 9, 9, 5]
// b.fill(9, 1, 4);            // Fill indexes 1 to 3 with 9 -> [1, 9, 9, 9, 5]

    const dp: number[] = new Array(nums.length);

// 2. 以第 0 个元素结尾的最大和，就是它自己
// 2. The maximum sum of a subarray ending at index 0 
// is just nums[0] itself.

    dp[0] = nums[0]!;
    let best = nums[0]!;

    for (let i = 1; i < nums.length; i++) {
        const x = nums[i]!;

// 3. 连续求和与当前值比较后更大的值；
// 3. Compare the running sum with the current value and take the larger one.
// 4. 进而与全局最大比较，再更新：
// 4. Then compare with the global maximum and update it.

        dp[i] = Math.max(x, x + dp[i-1]!);

        if (dp[i]! > best) {
            best = dp[i]!;
        }
    }

    return best
}

// 5. self-test:

console.log(MaxSubArrayDP([-2, -2, 4, -1, 5]));


