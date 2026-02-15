// 题 2：连续子数组的最大和（Kadane 算法）
// Problem 2: Maximum Subarray Sum (Kadane's Algorithm)

// 给定一个整数数组 nums，找到一个非空连续子数组，使得这个子数组的和最大，并返回数组。
// Given an integer array nums, find a non-empty contiguous subarray,
// making the sum of this subarray maximized, and return this subarray.

//  - 输入：nums: number[]
//  - 输出：number[]
//  - Input: nums: number[]
//  - Output: number[]

// tie-break 有三：
// 1. 返回长度最大的区间（或长度）；2. 返回长度最小的区间（或长度）；3. 返回所有区间（或所有长度）；
// 不算 tie-break 规则：1. 返回最大的和；

// -----------------------------------------------------------------------------
// 1) the longest range
// -----------------------------------------------------------------------------

function maxSubarraySum(nums: number[]): number[] {
    
    let curr = 0;
    // start: currstart; end: i
    let currStart = 0;

    let best = -Infinity;
    let bestStart = 0;
    let bestEnd = 0;

    for (let i = 0; i < nums.length; i++) {

        const x = nums[i]!;
        curr += x;

        if (x > curr + x) {
            curr = x;
            currStart = i
        }

        const currLength = i - currStart + 1;
        const bestLength = bestEnd - bestStart + 1;

        if (curr > best) {
            best = curr;
            bestStart = currStart;
            bestEnd = i;
        } else if (curr === best && currLength > bestLength) {
            bestStart = currStart;
            bestEnd = i;
        }
    }
    return nums.slice(bestStart, bestEnd + 1);
}

console.log(maxSubarraySum([-1,0,5,3,-1,5]));
console.log(maxSubarraySum([1,0,5,3,-1,5]));
console.log(maxSubarraySum([1,2,-1,4,0]));


// -----------------------------------------------------------------------------
// 2) all ranges
// -----------------------------------------------------------------------------

function maxSubarraySum_All(nums: number[]): number[][] {
    
    if (nums.length === 0) return[]
    
    let curr = 0;
    // start: currstart; end: i
    let currStart = 0;

    let best = -Infinity;
    let bestStart = 0;
    let bestEnd = 0;

    // [index, index] -> [j, i]
    const bestArray: Array<[number,number]> = [[0, 1]];

    for (let i = 0; i < nums.length; i++) {

        const x = nums[i]!;
        curr += x;

        if (x > curr + x) {
            curr = x;
            currStart = i
        }

        if (curr > best) {
            best = curr;
            bestArray.length = 0;
            bestArray.push([currStart, i]);
        } else if (curr === best) {
            bestArray.push([currStart, i]);
        }
    }
    return bestArray.map(([l,r]) => nums.slice(l, r+1))
}

console.log(maxSubarraySum_All([-1,0,5,3,-1,5]));
console.log(maxSubarraySum_All([1,0,5,3,-1,5]));
console.log(maxSubarraySum_All([1,2,-1,4,0]));
