// I1. Binary search (basic)
// I1. 二分查找（基础版）

// Given an ascending sorted array nums and a target value,
// return its index if found, otherwise return -1.
// 给定一个升序数组 nums 和一个目标值 target，
// 如果 target 存在于数组中，返回它的下标；否则返回 -1。

// - Input: [1, 3, 5, 7, 9], 3;
// - Output: 1 (an index);
//
// -----------------------------------------------------------------------------
// 1) 核心思想 / Core idea:
// -----------------------------------------------------------------------------
//
// -----------------------------------------------------------------------------
// 0. tie-break: value that we take is unique
// -----------------------------------------------------------------------------
//
// 1. Use Binary Search
//    - In an ordered array, look at the middle element each time.
//      then remove the half "impossible with the target"
//      Just keep looking up for it in the remaining half
//    - Instead of looking for it one-by-one from start to end (O(n))
//      Binary search narrows them down to a half each time with complexity of O(log n)
// 1. 用二分查找
//    - 在有序数组里，每次都看中间元素，然后把"不可能包含目标值的那一半"移除，
//      只在剩下的一半里继续查找
//    - 相比从头到尾一个个找 (O(n))，二分每次缩减一半，复杂度为 O(log n)

function binarySearch(nums: number[], target: number): number {

// 2. Core Variables
//    - left: left boundary (inclusive)
//    - right: right boundary (inclusive)
//    - Hold up an invariant: if target exsits, it must be within [left, right]
// 2. 核心变量
//    - left：当前搜索区间的左边界（含左边界）
//    - right：当前搜索区间的右边界（含有边界）
//    - 保持一个不变式：目标若存在，一定在区间 [left, right] 之内

    let left = 0;
    let right = nums.length - 1;
    
    while (left <= right) {

// 3. Middle Point:
//    - mid：the mid index of the current range
//    - val：the mid value
// 3. 中点：
//    - mid：当前区间中点下标
//    - val：中点的值

        const mid = Math.floor((right + left) / 2);
        const val = nums[mid]!;
        
// 4. For comparison of val with target:
//    - If val === target: found the target; return mid directly
//    - If val < target: target can only be on the larger side in value → left = mid + 1 
//    - If val > target: target can only be on the smaller side in value → right = mid - 1
//    - Loops stop when left > right → search range is empty → target not found → return -1
// 4. 把 val 和 target 比较：
//    - val === target的话，找到了目标，直接返回 mid
//    - val < target的话，目标只可能在较大的那一边（右半区）
//    - val > target的话，目标只可能在较小的那一边（左半区）
//    - left > right 时候循环停止 → 搜索区间为空 → 目标找不到 → 返回 -1

        if (val === target) {
            return mid;
        } else if (val < target) {
            left = mid + 1; // preserve the second half → or shrink the second half
        } else {
            right = mid - 1; // preserve the first half → or shrink the first half
        }
    }
    return -1;
}

// 5. 自测
// 5. Self-test
console.log(binarySearch([1, 3, 5, 7, 9, 9], 9));
console.log(binarySearch([1, 3, 5, 7, 9], 1));

// -----------------------------------------------------------------------------
// 2) Complexity/ 复杂度
// -----------------------------------------------------------------------------

// 1. Time: O(log n) remove half of a range each loop
// 2. Space: O(1) use ony a few variables
// 1. 时间：O(log n) 每循环移除区间一半
// 2. 空间：O(1) 只使用几个变量

