// I1. Binary search (basic)
// I1. 二分查找（基础版）

// Given an ascending sorted array nums and a target value,
// return its index if found, otherwise return -1.
// 给定一个升序数组 nums 和一个目标值 target，
// 如果 target 存在于数组中，返回它的下标；否则返回 -1。

// - Input: [1, 3, 5, 7, 9], 3;
// - Output: 1 (an index);

// -----------------------------------------------------------------------------
//  1. multi-value(s)
// -----------------------------------------------------------------------------

function leftBoundary(nums: number[], target: number): number {
    let left = 0;
    let right = nums.length - 1;
    let first = -1;

    while (left <= right) {
        const half = Math.floor((left + right) / 2) 
        if (nums[half]! >= target) { // shrink to the leftside for first target, if possible
            first = half; // update the current answer
            right = half - 1;
        } else { // expand to the rightside 
            left = half + 1;
        }
    }
    return first;
}

function rightBoundary(nums: number[], target: number): number {
    let left = 0;
    let right = nums.length - 1;
    let last = -1;

    while (left <= right) {
        const half = Math.floor((left + right) / 2) 
        if (nums[half]! <= target) { // expand to the rightside for first target, if possible
            last = half; // update the current answer
            left = half + 1;
        } else { // shrink to the leftside 
            right = half - 1;
        }
    }
    return last;
}

function extractAllIndices(nums: number[], target: number): number[] {
    const first = leftBoundary(nums, target);
    const last = rightBoundary(nums, target);

     // edge case
    if (first === -1) return [];

    const res: number[] = [];

    for (let i = first; i <= last; i++) {
        res.push(i);
    }
    return res;
}

console.log(extractAllIndices([1,3,5,7,9,9,9],9));
console.log(extractAllIndices([],0));
console.log(extractAllIndices([0,3,5,7,9,9],0));

// -----------------------------------------------------------------------------
//  2. > target  or >= target or < target or <= target
// -----------------------------------------------------------------------------

// extra variant ("> target" case):  
// Problem: Given an ascending array nums and a target, 
// return the index of the first element that is strictly greater than target; if no such element exists, return -1.  
// 题目：给定一个升序数组 nums 和整数 target，返回数组中第一个严格大于 target 的元素下标；如果不存在，返回 -1。  
// Template: use condition `if (nums[mid] > target) 
// { ans = mid; right = mid - 1; } else { left = mid + 1; }` 
// so that the answer range forms F F F T T T, and binary search finds the first T.  
// 模板：维护「nums[mid] > target」这一布尔条件形成 F F F T T T 的单调性，用二分在区间 [0, n-1] 上查找第一个为 T 的位置。

// -----------------------------------------------------------------------------
//  2. > target
// -----------------------------------------------------------------------------

function leftBoundaryGreater(nums: number[], target: number) {
    let left = 0;
    let right = nums.length - 1;
    // since no index has a number less than 0 
    let first = -1;

    while (left <= right) {
        const half = Math.floor((left + right) / 2);
        if (nums[half]! > target) {
            first = half;
            right = half - 1; // move left
        } else {
            left = half + 1;
        }
    }
    return first;
}

function extractAllIndicesGreater(nums: number[], target: number): number[] {
    const first = leftBoundaryGreater(nums, target);
    if (first === -1) return [];

    const res: number[] = [];
    for (let i = first; i < nums.length; i++) {
        res.push(i);
    }
    return res;
}

console.log(extractAllIndicesGreater([1,3,5,7,9,9,9],6));
console.log(extractAllIndicesGreater([],0));
console.log(extractAllIndicesGreater([0,3,5,7,9,9],0));

