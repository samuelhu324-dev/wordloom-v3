// A1. 最短子数组长度 ≥ target（数组 + 滑动窗口）
// A1. The shortest subarray length ≥ target (array + sliding window)

// 给定一个只包含正整数的数组 nums 和一个正整数 target，
// 请返回和 大于等于 target 的 最短连续子数组 的长度；
// 如果不存在这样的子数组，返回 0。

// Given an array nums of positive integers and a positive integer target,
// return the length of the shortest contiguous subarray whose sum is at least target.
// If no such subarray exists, return 0.

// 示例：
// 输入：nums = [2,3,1,2,4,3], target = 7
// 输出：2（因为 [4,3] 的和为 7，长度最短为 2）
// Example:
// Input: nums = [2,3,1,2,4,3], target = 7
// Output: 2 (the subarray [4,3] has sum 7 and length 2, which is minimal)

// [2,3,1,2,4,3]

// 1) Key Oberservation | 关键观察：
// 1. 数组里都是正整数：一旦把一个数加入窗口，和只增不减
// 1. Everything in the array is positive numbers: once a number is added into the window, 
// sum can only increase.
// 2. 子数组必须连续：自然而然地用一个窗口 [left, right] 表示当前连续区间
// 2. Subarray must be contiguous: Naturally represent the current range 
// with a window [left, right]

// 1） Core Idea: Slidng Window | 核心思路：滑动窗口
// 维护一个窗口 [left, right] and its sum; 
// Maintain a window [left, right] and its sum;

function shortestSubarraySum(nums: number[], target: number): number {

// 1. 初始化：left = 0，sum = 0，res = Infinity
// 1. Initialize: left = 0, sum = 0, res = Inifinity

    let left = 0;
    let sum = 0;
    let res = Infinity;

// 2. 从 0 到 n - 1 迭代：
// 扩大窗口：sum += nums[right]
// 2. Iterate right from 0 to n - 1:
// expand the window: sum += nums[right]

    for (let right = 0; right < nums.length; right++) {
        sum += nums[right]!;

// 3. While the current window is valid (sum >= target): 
//   3.1 Update the answer: res = Math.min(res, right - left + 1)
//   3.2 Remove nums[left] from sum:
//   3.3 Then try to shrink the window from the left: left++
// 3. 当前窗口合法的时候 (sum >= target) :
//   3.1 更新答案：res = Math.min(res, right - left + 1)
//   3.2 把 nums[left] 移出 sum：sum -= nums[left]
//   3.3 然后从左边缩小一下窗口：left++

        while (sum >= target) {
            res = Math.min(res, right - left + 1);
            sum -= nums[left]!;
            left++;
        }
    }

// 4. 循环后：如果 res 还是 Inifinity，就返回 0 ；否则返回 res
// 4. After the loop: If res is still Infinity, return 0; Otherwise return res

    return res === Infinity ? 0 : res;

}

// 5. 自测
// 5. Self-test

console.log(shortestSubarraySum([2,3,1,2,4,3], 7));
console.log(shortestSubarraySum([2,3,1,2,4,3,11,8,2,1], 10));

// 3) 复杂度 | Complexity:
// 1. 最多一次把每个元素添加进窗口并最多移除一次
// 2. 时间：O(n)，空间：O(1)
// 1. Each element is added to the window at most once and removed at most once;
// 2. Time: O(n), Space: O(1).

// 4) 练习 | Practice:

function shortestSubarraySum2(nums: number[], target: number): number {

    let sum = 0;
    let left = 0;
    let shortestlength = Infinity;

    // Start (before going through the while for the first time) 
    // or continue (after passing over the while) 
    // to increase window's boundary from right until (sum >= target)
    for (let right = 0; right < nums.length; right++) {
        sum += nums[right]!;

        // Stop expanding to right side if:
        while (sum >= target) {

            // 1. + 1 means the length is counted from 1, unlike index from 0
            // 2. The determinator below can compare 
            // the shortestlength with the currentlength (right - left + 1)
            const currentlength = right - left + 1;
            shortestlength = Math.min(shortestlength, currentlength);

            // Shrink the window from the left:
            // 1. First Remove the sum from left
            // 2. Then narrow the range using left++
            sum -= nums[left]!;
            left++;
        }
    }

return shortestlength;

}

console.log(shortestSubarraySum2([2,3,1,2,4,3], 7));
console.log(shortestSubarraySum2([2,3,1,2,4,3,11,8,2,1], 10));