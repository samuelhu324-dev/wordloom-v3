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
// 1) 核心思路 / Core idea: Kadane's algorithm with indices
// -----------------------------------------------------------------------------
//
// 1. 线性扫描数组，只维护一个“极小的状态”，不回头：
// 1. Scan the array linearly. Maintain only a tiny state and never look back:
// 
// 2. 每个位置 i，我们只关心：以 i 结尾的“最佳子数组”的和 currSum，以及起点 currStart
// 2. For each position i, we care only about:
//    The best subarray ending at i: its sum currSum and start index currStart.
//  
// 3. 有了“当前以 i 结尾的最佳组”，再去和“整个所有位置的最佳组”比较: bestSum, bestStart, bestEnd
// 3. With the best subarray ending at i, compare it with the best over all positions
//    so far: bestSum, bestStart, bestEnd.
// 
//
function maxSumSubarray(nums: number[]): number[] {
    
    if (nums.length === 0) return [];
//
// -----------------------------------------------------------------------------
// 2) 状态定义 / State definition
// -----------------------------------------------------------------------------
//
// 1. currSum：必须以下标 i 结尾的连续子数组最大和
// 1. currSum: maximum sum of a contiguous subarray that must end at index i
// 
// 2. currStart：那段子数组的起点下标
// 2. currStart: start index of that subarray.
// 
// 3. bestSum：目前为止遇到的“全局最大和”
// 3. bestSum: global max subarray sum seen so far.
// 
// 4. bestStart, bestEnd: 对应 bestSum 那段子数组的起止下标。
// 4. bestStart, bestEnd: start/end indices of that subarray corresponding to bestSum
//
    let currSum = nums[0]!;
    let currStart = 0;

    let bestSum = nums[0]!;
    let bestStart = 0;
    let bestEnd = 0;

// -----------------------------------------------------------------------------
// 3) 状态转移 / Transition (Kadane)
// -----------------------------------------------------------------------------
//
// Reach i currently, and element is x = nums[i]
// 当前来到 i ，元素是 x = nums[i]
//  
// 1. 决定要不要扩展之前的子数组 或者 在 i 的位置重开一个新的
//   - 如果扩展之前的组数组没在 x 的位置新开一个好，我们重设；
//   - 否则我们扩展
// 1. Decide whether to extend the previous subarray or start a new one at i;
//   - If extending the previous subarray is worse than starting fresh at x, we rest
//   - otherwise we extend

    for (let i = 1; i < nums.length; i++) {
        const x = nums[i]!;
        if (currSum + x < x) {
            currSum = x;
            currStart = i;
        } else {
            currSum += x;
        }

// 2. 用当前子数组更新“全局最优”
//   - 如果 currSum > bestSum → 必须更新；
//   - 如果 currSum === bestSum → 选更短的子数组就能“破局”
// 2. Use the current subarray to update "the global best"
//   - If currSum > bestSum → must update it
//   - If currSum === bestSum, we “break ties” by choosing the shorter subarray

        const currLen = i - currStart + 1;
        const bestLen = bestEnd - bestStart + 1;

        if (currSum > bestSum ||
            (currSum === bestSum && currLen < bestLen)
        ) {
            bestSum = currSum;
            bestStart = currStart;
            bestEnd = i;
        }

    }

// -----------------------------------------------------------------------------
// 4) 结果构造 / Build the answer
// -----------------------------------------------------------------------------
// 最后，已知全局最佳区间为 [bestStart, bestEnd];
//   - 用 slice 按 左闭右开 [start, end) 规则剪出来即可
// At the end，known that the global best range as pbestStart, bestEnd]
//   - Use slice [start, endExclusive) to cut out the subarray 
//     according to (left-closed, right-open):

    return nums.slice(bestStart, bestEnd + 1);

}

// -----------------------------------------------------------------------------
// 5) 测试 / Test:
// -----------------------------------------------------------------------------

console.log(maxSumSubarray([1, -1, 5, 6, 7])); 
console.log(maxSumSubarray([1, -5, 5, 6, -7]));

// -----------------------------------------------------------------------------
// 6) 练习 / Practice: find the longest/smallest range/length
// -----------------------------------------------------------------------------

function maxSumSubarray2(nums: number[]): number[] {
    // No element in an array
    if (nums.length === 0) return [];

    let currSum = nums[0]!;
    let currStart = 0;

    let bestSum = nums[0]!;
    let bestStart = 0;
    let bestEnd = 0;

    for (let i = 1; i < nums.length; i++) {
        
        const x = nums[i]!;
        // If currSum < current number
        // That means a new start at x!
        if (currSum + x < x) {
            currSum = x;
            currStart = i;
            // otherwise continue expanding the currSum with x
        } else {
            currSum += x;
        }

        // i = the rear index , currStart = the front index
        // + 1 means the result is a length, rather than an index
        const currLength = i - currStart + 1;
        const bestLength = bestEnd - bestStart + 1;

        if (currSum > bestSum 
            // we choose the shortest length here if two subarray gives same maximum
            // you can modify it to find a longest one, try it!
            || currSum === bestSum && currLength < bestLength
        ) {
            bestSum = currSum;
            bestStart = currStart;
            bestEnd = i;
        }
    }
    return nums.slice(bestStart, bestEnd + 1);
}

console.log(maxSumSubarray2([1, -1, 5, 6, 7])); 
console.log(maxSumSubarray2([1, -5, 5, 6, 0]));

// -----------------------------------------------------------------------------
// 7)  Extra / 补充：select all possible max-sum subarrays
// -----------------------------------------------------------------------------

function allMaxSumSubarrays(nums: number[]): number[][] {
    if (nums.length === 0) return [];

    let currSum = nums[0]!;
    let currStart = 0;

    let bestSum = nums[0]!;
    const ranges: Array<[number, number]> = [[0, 0]];

    for (let i = 1; i < nums.length; i++) {
        const x = nums[i]!;

        if (currSum + x < x) {
            currSum =  x;
            currStart = i;
        } else {
            currSum += x;
        }

        if (currSum > bestSum) {
            bestSum = currSum;
            ranges.length = 0;
            ranges.push([currStart, i]);
        } else if (currSum === bestSum) {
            ranges.push([currStart, i]);
        }
    }
    // 把 ranges: Array<[l, r]> 映射成
    // Array<nums.slice(l, r+1)>，也就是 number[][]
    return ranges.map(([l, r]) => nums.slice(l, r + 1));

}

console.log(allMaxSumSubarrays([1, -1, 5, 6, 7])); 
console.log(allMaxSumSubarrays([1, -5, 5, 6, 0]));

// -----------------------------------------------------------------------------
// 8)  Extra Pratice / 补充练习：
// -----------------------------------------------------------------------------

function allMaxSumSubarrays2(nums: number[]): number[][] {
    if (nums.length === 0) return [];

    let currSum = nums[0]!;
    let currStart = 0;

    let bestSum = nums[0]!;
    const bestArray: Array<[number, number]> = [[0, 1]];

    for (let i = 1; i < nums.length; i++) {
        const x = nums[i]!;
        if (currSum + x < x) {
            currSum = x;
            currStart = i;
        } else {
            currSum += x;
        }

        if (currSum > bestSum) {
            bestSum = currSum;
            // Empty the bestArray
            bestArray.length = 0;
            // Push a new tuple to the bestArray
            bestArray.push([currStart, i]);
        } else if (currSum === bestSum) {
            bestArray.push([currStart, i]);
        }
    }
    // In bestArray, map each tuple for indices into acutal tuple with numbers using slice.
    return bestArray.map(([l, r]) => nums.slice(l, r +1))
}

console.log(allMaxSumSubarrays2([1, -1, 5, 6, 7])); 
console.log(allMaxSumSubarrays2([1, -5, 5, 6, 0]));