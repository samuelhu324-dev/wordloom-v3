// A1. 最短子数组长度 ≥ target（数组 + 滑动窗口）
// A1. The shortest subarray length ≥ target (array + sliding window)

// 给定一个只包含正整数的数组 nums 和一个正整数 target，
// 请返回和 大于等于 target 的 最短连续子数组 的长度；
// 如果不存在这样的子数组，返回 0。

// Given an array nums of positive integers and a positive integer target,
// return the length of the shortest contiguous subarray whose sum is at least target.
// If no such subarray exists, return 0.

// 示例：
// 输入：nums = [2,3,2,2,4,3], target = 7
// 输出：2（因为 [4,3] 的和为 7，长度最短为 2）
// Example:
// Input: nums = [2,3,2,2,4,3], target = 7
// Output: 2 (the subarray [4,3] has sum 7 and length 2, which is minimal)

// -----------------------------------------------------------------------------
// 1) sum = target 
// -----------------------------------------------------------------------------

function shortestSubarrayLength_Equal(nums: number[], target: number): number {

    let sum = 0;
    let shortestLength = Infinity;
    let left = 0;

    for (let right = 0; right < nums.length; right++) {
        
        sum += nums[right]!;

        while (sum > target) {
            sum -= nums[left]!;
            left++;
        }

        if (sum === target) {
            const currentLength = right - left + 1;
            shortestLength = Math.min(shortestLength, currentLength)
            // or
            // if (shortestLength > currentLength) shortestLength = currentLength;
        }
        
    }

    return shortestLength;
}

console.log(shortestSubarrayLength_Equal([1,1,6,1,3],3));
console.log(shortestSubarrayLength_Equal([1,1,6,1,1,3],2));

// -----------------------------------------------------------------------------
// 2) sum >= target 
// -----------------------------------------------------------------------------

function shortestSubarrayLength_GreaterEqual(nums: number[], target: number): number {

    let sum = 0;
    let shortestLength = Infinity;
    let left = 0;

    for (let right = 0; right < nums.length; right++) {

        sum += nums[right]!;

        while (sum >= target) {
            
            const currentLength = right - left + 1
            shortestLength = Math.min(shortestLength, currentLength)
            sum -= nums[left]!;
            left++;
        }
    }

    return shortestLength;
}

console.log(shortestSubarrayLength_GreaterEqual([1,1,6,1,3],3));
console.log(shortestSubarrayLength_GreaterEqual([1,1,6,1,1,3],2));
