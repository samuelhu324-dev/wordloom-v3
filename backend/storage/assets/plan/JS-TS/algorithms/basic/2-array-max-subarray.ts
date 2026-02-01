// 题 2：连续子数组的最大和（Kadane 算法）
// 方法一：动态规划 Kadane 算法
// 描述：给定一个整数数组 nums ，找到一个具有最大和的连续子数组
// （子数组最少包含一个元素），返回其最大和。

function maxSubArray(nums: number[]): number {
  if (nums.length === 0) {
    throw new Error('nums must be non-empty');
  }

  // 取第一个元素作为初始值，使用 ! 告诉 TS 这里一定有值
  const first = nums[0]!;
  let curr = first;
  let best = first;

  for (let i = 1; i < nums.length; i++) {
    const x = nums[i]!; // 同样用 ! 消掉 number | undefined

    // 要么把 x 接在前面的子数组后面（curr + x）
    // 要么从 x 重新开始一段新的子数组
    curr = Math.max(x, curr + x);

    // 更新全局最大
    if (curr > best) {
      best = curr;
    }
  }

  return best;
}

// 简单自测
console.log(maxSubArray([-2, 1, -3, 4, -1, 2, 1, -5, 4])); // 6，对应 [4,-1,2,1]
console.log(maxSubArray([1]));                             // 1
console.log(maxSubArray([5, 4, -1, 7, 8]));   


// 方法二：显式 DP 数组
// 描述：使用一个 dp 数组来存储以每个位置结尾的最大子数组和。

function maxSubArrayDP(nums: number[]): number {
  if (nums.length === 0) {
    throw new Error('nums must be non-empty');
  }

  // 开一个和 nums 一样长的 dp 数组，避免 “可能为 undefined” 报错
  const dp: number[] = new Array(nums.length);

  dp[0] = nums[0]!;      // 以第 0 个元素结尾的最大和，就是它自己
  let best = dp[0]!;     // 当前全局最大

  for (let i = 1; i < nums.length; i++) {
    const x = nums[i]!;
    const prev = dp[i - 1]!;          // 上一个位置的 dp，一定已经被填过

    dp[i] = Math.max(x, prev + x);    // 状态转移：接上去 vs 重新开始

    if (dp[i]! > best) {
      best = dp[i]!;
    }
  }

  return best;
}

// 简单自测
console.log(maxSubArrayDP([-2, 1, -3, 4, -1, 2, 1, -5, 4])); // 6
console.log(maxSubArrayDP([1]));                             // 1
console.log(maxSubArrayDP([5, 4, -1, 7, 8]));                // 23

// 方法三：暴力枚举
// 描述：枚举所有子数组，计算它们的和，找出最大值。

function maxSubArrayBrute(nums: number[]): number {
  if (nums.length === 0) {
    throw new Error('nums must be non-empty');
  }

  let best = nums[0]!;

  for (let i = 0; i < nums.length; i++) {
    let sum = 0;
    for (let j = i; j < nums.length; j++) {
      sum += nums[j]!;
      if (sum > best) {
        best = sum;
      }
    }
  }

  return best;
}

console.log(maxSubArrayBrute([-2, 1, -3, 4, -1, 2, 1, -5, 4])); // 6



