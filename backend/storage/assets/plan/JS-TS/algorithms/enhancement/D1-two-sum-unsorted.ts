// D1. 无序数组的两数之和（数组 + Map）
// D1. Two-sum in an unsorted array (array + Map)

// 给定一个无序整数数组 nums 和一个目标值 target，
// 请返回和为 target 的两个不同元素的下标，顺序任意；
// 如果不存在这样的两个数，返回空数组 []。

// Given an unsorted integer array nums and an integer target,
// return the indices of two distinct elements whose sum is target (in any order).
// If no such pair exists, return an empty array [].

// 示例：
// 输入：nums = [3,2,4], target = 6
// 输出：[1,2]（因为 nums[1] + nums[2] = 2 + 4 = 6）
// Example:
// Input: nums = [3,2,4], target = 6
// Output: [1,2] (since nums[1] + nums[2] = 2 + 4 = 6)

// -----------------------------------------------------------------------------
// tie-break 版 / tie-break version with unique result
// -----------------------------------------------------------------------------

function sumUnsortedArray(nums: number[], target: number): number[] {
    const indexMap = new Map<number, number>();
    
    for (let i = 0; i < nums.length; i++) {
        const x = nums[i]!;
        const y = target - x;

        if (indexMap.has(y)) return [i, indexMap.get(y)!]

        indexMap.set(x, i);
    }
    
return [];

}

console.log(sumUnsortedArrayCount([3,2,4], 6))

// -----------------------------------------------------------------------------
// Count 版 / Count version
// -----------------------------------------------------------------------------

function sumUnsortedArrayCount(nums: number[], target: number): number {
    const indexMap = new Map<number, number>();
    let count = 0;
    
    for (let i = 0; i < nums.length; i++) {
        const x = nums[i]!;
        const y = target - x;

        if (indexMap.has(y)) {
            count += 1;
        }

        indexMap.set(x, i);
    }

return count;

}

console.log(sumUnsortedArrayCount([3,2,4,4], 6))

// -----------------------------------------------------------------------------
// All Pairs 版 / All Pairs version
// -----------------------------------------------------------------------------

function sumUnsortedArrayPair(nums: number[], target: number): number[][] {
    const indexMap = new Map<number, number>();
    const pair = new Array<[number, number]>();
    
    for (let i = 0; i < nums.length; i++) {
        const x = nums[i]!;
        const y = target - x;

        if (indexMap.has(y)) {
            pair.push([indexMap.get(y)!, i]);
        }

        indexMap.set(x, i);
    }
    
return pair;

}

console.log(sumUnsortedArrayPair([3,2,4,4], 6));