// A2. Maximum average of a fixed-size window (array + sliding window)
// A2. 固定窗口最大平均值（数组 + 滑动窗口）

// Given an integer array nums and a positive integer k,
// find the maximum average value among all contiguous subarrays of length exactly k,
// and return that average as a number.
// 给定一个整数数组 nums 和一个正整数 k，
// 请找出所有长度恰好为 k 的连续子数组中，平均值最大的那个平均值，返回这个平均值（number）。

// 示例：
// 输入：nums = [1,12,-5,-6,50,3], k = 4
// 输出：12.75（子数组 [12,-5,-6,50] 的平均值最大）
// Example:
// Input: nums = [1,12,-5,-6,50,3], k = 4
// Output: 12.75 (the subarray [12,-5,-6,50] has the maximum average)

// -----------------------------------------------------------------------------
// 1. given length return average
// -----------------------------------------------------------------------------

// -----------------------------------------------------------------------------
// 1) idea / 思路
// -----------------------------------------------------------------------------

// 
// 1. Goal: Among all contiguous subarrays of length exactly k, 
//          find the one with the maximum average
// 2. Core: a fixed-size sliding window:
//          - Compute the sum of the first k elements, for an initial window sum,
//            and initialize maxAverage = sum / k
//          - Cut down the leftmost element that slides out of the window:
//            sum -= nums[left], then left++
//          - This runs in O(n) time and O(1) extra space, because we reuse the 
//            the running sum instead of recomputing it from scratch
// 3. This runs in O(n) time and O(1) extra space, becasue we reuse the running sum
//    instead of recomputing it from scratch
// 
// 1. 目标：在所有长度恰好为 k 的连续子数组里，找到平均值最大的那个
// 2. 核心：滑动窗口大小固定
//          - 计算前 k 个元素的和，得到初始窗口总和，求出 maxAverage = sum / k 的初始值
//          - 把滑出窗口的左端元素减掉：sum -= nums[left]，然后 left++
//          - 这时窗口 [left,right] 的长度仍然是 k ，用 sum / k 更新最大平均值
// 3. 这一趟跑 O(n) 时间 和 O(1) 空间，因为复用累加的和，没有从头重新算起
//

function maxAverageFixedLength(nums: number[], k: number): number {
    
    let left = 0;
    let maxAverage = -Infinity;
    let sum = 0;

    for (let right = 0; right < nums.length; right++) {

        sum += nums[right]!;

        const currLength = right - left + 1;
        // if (currLength > k)
        if (currLength === k) {
            const average = sum / k;
            maxAverage = Math.max(maxAverage,average)
            // keep 4 elements in the array
            sum -= nums[left]!;
            left++
        }
    }

    return maxAverage;
}

console.log(maxAverageFixedLength([1,12,-5,-6,50,3],4));

// -----------------------------------------------------------------------------
// 2. given target average(<=) return fixed length;
// -----------------------------------------------------------------------------

// -----------------------------------------------------------------------------
// 1) idea / 思路
// -----------------------------------------------------------------------------

// 
// 1. Goal: Among all contiguous subarrays, find the maximum length of a subarray
//          whose average is <= target
// 2. Core: a variable-size sliding window
//          - Expanding the window by moving right 
//          - and adding nums[right] to sum
//          - the window [left,right] is already the longest one ending at right
//            with average <= target, when we exit from the window;
//            update maxLength with its length
//          - note that average should be written as sum / (right - left + 1) 
//            (with parentheses!)
// 
// 1. 目标：在所有连续子数组中，找到平均值 <= target 子数组的最大长度
// 2. 核心：滑动窗口大小可变
//          - 向右移动并把 nums[right] 添加到 sum 可以扩张窗口
//          - 退出 while 时，窗口 [left,right] 已经是 “以 right 结尾且平均值
//            <= target 的最长窗口”，用其长度更新 maxLength
//          - 注意平均值要写成：sum / (right - left + 1) （有括号）
// 

function maxLengthFixedAverage(nums: number[], target: number): number{
    
    let left = 0;
    let maxLength = 0;
    let sum = 0;

    for (let right = 0; right < nums.length; right++) {
        sum += nums[right]!;

        const average = sum / (right - left + 1);
        while (left <= right && average > target) {
            sum -= nums[right]!;
            left++;
        }

        // currLength is the length without average > target 
        const currLength = right - left + 1;
        maxLength = Math.max(currLength, maxLength);
    }

    return maxLength;
}

console.log(maxLengthFixedAverage([1,12,-5,-6,50,3],2));
