// 题 1：最小差值对（数组 + 排序）
// Problem 1: Minimum Difference Pair (Array + Sorting)

// 给定一个整数数组 nums，请返回任意两个不同元素之间的最小绝对差值。
// Given an integer array nums, return the minimum absolute difference 
// between any two different elements.

// - 输入：nums: number[]，长度 ≥ 2
// - Input: nums: number[], length ≥ 2

// - 输出：number
// - Output: number

// - 示例：[3, 8, 2] → 最小差值是 |3-2| = 1，返回 1。
// - Example: [3, 8, 2] → the minimum difference is |3 - 2| = 1, return 1.

// - 要求：时间复杂度只可小于 O(n²)。
// - Requirement: The time complexity should be strictly better than O(n²) if possible.

// 方法一：排序 + 遍历相邻元素
// Approach 1: Sort + scan adjacent elements

function minDiffSorted(nums: number[]): number {

    if (nums.length < 2) throw new Error('Invalid Array');

    // with the original array sorted, other orders related to nums
    // won't be polluted or changed.
    const sorted = [...nums].sort((a, b) => a - b)

    // a benchmark to compare it with the every diff the machine calculates
    let mindiff = Infinity;

    // the loop started from i = 1, where it can confirm that
    // the correct order rule is put in place (no reversal rules for order in TS)
    for (let i = 1; i < sorted.length; i++) {

        // find-the-current-difference = current number - previous number
        const curr = sorted[i]!;
        const prev = sorted[i - 1]!;
        const diff = curr - prev;

        // small enough to be updated as a new mindiff?
        if (diff < mindiff) mindiff = diff;
    }

// return the number mindiff as the loop ends
return mindiff;

}

console.log(minDiffSorted([1, 4, 9, 2, -1, 0]));
console.log(minDiffSorted([12, 4, 9, 35, 15, 0]));


// 方法二：使用 Set 存储已访问元素 / 双重for循环
// Approach 2： Store elements visited using Set / Double-for-loops

function minDiffSet(nums: number[]): number{

    if (nums.length < 2) throw new Error('Always keep two numbers in an ARRAY!');

    const visited = new Set<number>();
    let mindiff = Infinity;

    // first run: the function will skip the nested loop
    // and append/add the new num to the visited set.
    // subsequent run(s): compute the absolute value with numbers visited/seen
    // then compare them

    for (const num of nums) {

        for (const v of visited) {
            
            const diff = Math.abs(num - v);
            if (diff < mindiff) mindiff = diff;

        }
        visited.add(num);
    }

return mindiff;

}

console.log(minDiffSet([1, 4, 9, 2, -1, 0]));
console.log(minDiffSet([12, 4, 9, 35, 15, 0]));