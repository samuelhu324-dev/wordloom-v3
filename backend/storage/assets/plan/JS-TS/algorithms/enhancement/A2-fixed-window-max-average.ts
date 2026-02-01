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
// 1) given length return average
// -----------------------------------------------------------------------------

function maxAverageFixedLength(nums: number[], k: number): number {
    let left = 0;
    let sum = nums[0]!;
    let maxAverage = -Infinity;

    for (let right = 1; right < nums.length; right++) {
        sum += nums[right]!;
        
        const currLength = right - left + 1;
        if (currLength === k) {
            const average = sum / k;
            maxAverage = Math.max(average, maxAverage);

            sum -= nums[left]!;
            left++;
        } 
    }

    return maxAverage;
}

console.log(maxAverageFixedLength([1,12,-5,-6,50,3],4));

// -----------------------------------------------------------------------------
// 2) given target average(<=) return fixed length;
// -----------------------------------------------------------------------------

function maxLengthFixedAverage(nums: number[], target: number): number{
    
    let left = 0;
    let sum = 0;
    let maxLength = 0;

    for (let right = 0; right < nums.length; right++) {
        sum += nums[right]!;

        const average = sum / right - left + 1;
        while (left <= right && average > target) {
            sum -= nums[left]!;
            left++;
        }

         const currLength = right - left + 1;
         maxLength = Math.max(currLength, maxLength);
    }
    return maxLength;
}

console.log(maxLengthFixedAverage([1,12,-5,-6,50,3],2));
