// I1. Binary search (basic)
// I1. 二分查找（基础版）

// Given an ascending sorted array nums and a target value,
// return its index if found, otherwise return -1.
// 给定一个升序数组 nums 和一个目标值 target，
// 如果 target 存在于数组中，返回它的下标；否则返回 -1。

// - Input: [1, 3, 5, 7, 9], 3;
// - Output: 1 (an index);

// -----------------------------------------------------------------------------
// 1. tie-break: unique value
// -----------------------------------------------------------------------------

function binarySearch_Unique(nums: number[], target: number): number {
    
    let left = 0;
    let right = nums.length - 1;

    while (left <= right) {

        // middle is an index of numbers
        // Note: this is index, not length (so + 1 is not required here)
        const middle = Math.floor((left + right) / 2); 
        const num = nums[middle]!;

        if (target < num) { // left-side
            right = middle - 1;
        } else if (target > num) { // right-side
            left = middle + 1;
        } else {
            return middle;
        }
    }
    return -1;
}

console.log(binarySearch_Unique([1,3,5,7,9],1));
console.log(binarySearch_Unique([1,3,5,7,9],9));

// -----------------------------------------------------------------------------
// 2. no tie-break: multi-value(s)
// -----------------------------------------------------------------------------

// -----------------------------------------------------------------------------
// 1) Core idea / 核心思路 
// -----------------------------------------------------------------------------
//  
// 目标：在升序数组 nums 中，target 可能出现多次
//      返回所有 nums[i] === target 的下标，例如：
//       - nums = [1,3,5,7,9,9,9], target = 9
//       - 结果：[4,5,6]
//
// 直接从头扫一遍当然可以，但复杂度是 O(n)
// 我们用二分把它拆成两步，每步 O(log n)
//  
// Goal: In the ascending array nums, target can appear multi-times. 
//       Return all indices where nums[i] === target, e.g:
//       - nums = [1,3,5,7,9,9,9], target = 9
//       - result：[4,5,6]
//
// Of course it's okay to scan it from start, but complexity is O(n)
// If we use binary search to split it into two steps. Each is O(log n)

// 1. Binary search for the leftmost occurrence (left boundary first)
//    - Similar to standard binary search, but when nums[mid] === target:
//      - write ans = mid down;
//      - keep searching left: right = mid - 1
//    - Since we always shrink to the left after a hit, 
//      the last kept is the index after the leftmost hit.
//    - If the final ans === -1, no target; return [] directly.
// 
// 1. 二分找最左边的 target (左边界 first)
//    - 和普通二分类似，只是当遇到 nums[mid] === target 时
//      - 先把 ans = mid 记下来 
//      - 然后继续往左边找：right = mid - 1
//    - 因为“每次命中都往左缩”，最后留下的就是最左那次命中的下标
//    - 如果最终 ans === -1，就没有 target，直接返回 []

function findFirst(nums: number[], target: number): number {
    let left = 0, right = nums.length - 1;
    let ans = -1;

    while (left <= right) {
        const mid = Math.floor((left + right) / 2);
        const val = nums[mid]!;
        if (val >= target) {
            if (val === target) ans = mid;
            right = mid - 1; // shrink to leftside -> find the min indices, if existed
        } else {
            left = mid + 1;
        }
    }
    return ans;
}

// 2. Binary search for the rightmost occurrence (right boundary last)
//    - Likewise, when nums[mid] === target this time   
//      - ans = mid
//      - then keep searching right: left = mid + 1
//    - Since we shrink to the right after a hit, 
//      the last kept is the index after the rightmost hit 
// 2. 二分找最右边的 target (右边界 last)
//    - 同理，这次当 nums[mid] === target 时：
//      - 先 ans = mid
//      - 再继续往右找：left = mid + 1
//    - 因为“每次命中都往右缩”，最后留下的是最右那次命中的下标

function findLast(nums: number[], target: number): number {
    let left = 0, right = nums.length - 1;
    let ans = -1;
    
    while (left <= right) {
        const mid = Math.floor((left + right) / 2);
        const val = nums[mid]!;
        if (val <= target) {
            if (val === target) ans = mid; 
            left = mid + 1; // shrink to rightside -> find the max indices, if existed
        } else {
            right = mid - 1;
        }
    }
    return ans;
}

// 3. Collect all indices between them
//    - If first = L and last = R, valid indices are L, L+1, ... R
//    - Push them into a result array
// 3. 收集所有这之间的下标
//    - 如果 first = L 而 last = R，符合条件的下标就是 L，L+1，.... R
//    - 推入一个结果数组

function binarySearch_Multi(nums: number[], target: number): number[]{
    const first = findFirst(nums, target);
    if (first === -1) return [];

    const last = findLast(nums, target);
    const res: number[] = [];
    for (let i = first; i <= last; i++) res.push(i);
    return res;
}

// 4. Self-test
// 4. 自测

console.log(binarySearch_Multi([1,3,5,7,9,9,9],9));

// 5. Complexity
//    - For left boundary: O(log n)
//    - For right boundary: O(log n)
//    - Collect indices: O(k), k is how many times target appears
//    - Total: O(log n + k), faster than a full linear scan O(n)
//      when k is small relative to n
// 5. 复杂度
//    - 找左边界：O(log n)
//    - 找有边界：O(log n)
//    - 收集下标：O(k)，k 是 target 出现次数
//    - 总计：O(log n + k)，相对于 n k 小的时候比线性扫描 O(n) 快

// -----------------------------------------------------------------------------
// 2) Practice / 练习
// -----------------------------------------------------------------------------


function firstIndex2(nums: number[], target: number): number{

    let left = 0;
    let right = nums.length - 1;
    let first = -1;

    while (left <= right) {
        // mid is an index!
        const mid = Math.floor((left + right) / 2); 
        const val = nums[mid]!;
        if (val >= target) { // shrink to the left for minimum index
            if (val === target) first = mid;
            right = mid - 1;
        } else {
            left = mid + 1;
        }
            
    }
    return first;
}

function lastIndex2(nums: number[], target: number): number{

    let left = 0;
    let right = nums.length - 1;
    let last = -1;

    while (left <= right) {
        // mid is an index!
        const mid = Math.floor((left + right) / 2); 
        const val = nums[mid]!;
        if (val <= target) { // shrink to the right for maximum index
            if (val === target) last = mid;
            left = mid + 1;
        } else {
            right = mid - 1;
        }
            
    }
    return last;
}

// Collect all indices between first and last
function binarySearch_Multi2(nums: number[], target: number): number[] {

    const first = firstIndex2(nums, target);
    const last = lastIndex2(nums, target);
    
    if (first === -1) return [];

    const results: number[] = [];
    
    for (let i = first; i <= last; i++) {
        results.push(i);
    }

    return results;

}

console.log(binarySearch_Multi2([1,3,5,7,9,9,9,9],9));