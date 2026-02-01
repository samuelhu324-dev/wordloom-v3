// E2：按次数去重
// E2: Deduplicate by frequency 

// -----------------------------------------------------------------------------
// E2-1：只保留出现一次的元素
// E2-1: keep only elements that appear exactly once
// -----------------------------------------------------------------------------

// 给定 nums: number[]，返回一个新数组，
// 只保留在 nums 中出现次数恰好为 1 次的元素，顺序按原数组。
// Given nums: number[], return a new array
// that keeps only the elements whose frequency in nums is exactly 1,
// while preserving the original order.

// 示例：
// → 输入：[2, 3, 2, 2, 1, 3, 4] 
// → 输出：[1, 4]（只有 1 和 4 只出现一次）
// Example:
// → Input:  [2, 3, 2, 2, 1, 3, 4] 
// → Output: [1, 4]  (only 1 and 4 appear exactly once)

// 提示：先用 Map<number, number> 统计频次，再过滤。
// Hint: Count the frequency with Map<number, number> and filter it

// -----------------------------------------------------------------------------
// 1. Standard version 
// -----------------------------------------------------------------------------

function UniqueFrequency(nums: number[]): number[] {
    // key: number ; value: frequency
    const countMap = new Map<number, number>();
    const result: number[] = [];

    // count the frequency with number
    for (const num of nums) {
        countMap.set(num, (countMap.get(num) ?? 0) + 1);

    }

    for (const num of nums) {
        if (countMap.get(num) === 1)
            result.push(num);
    }

    return result;
}

console.log(UniqueFrequency([2, 3, 2, 2, 1]));
console.log(UniqueFrequency([2, 3, 2, 2, 1, 5, 4]));

// -----------------------------------------------------------------------------
// 2. filter version
// -----------------------------------------------------------------------------

function uniqueFrequencyFilter(nums: number[]): number[] {
    
    const frequency = new Map<number, number>();

        for (const num of nums) {
        frequency.set(num, (frequency.get(num) ?? 0) + 1);
    }

    return nums.filter(num => frequency.get(num) === 1);
}

console.log(uniqueFrequencyFilter([2, 3, 2, 2, 1]));
console.log(uniqueFrequencyFilter([2, 3, 2, 2, 1, 5, 4]));

// -----------------------------------------------------------------------------
// E2-2：按次数上限去重（每个元素最多保留 k 次）
// E2-2: 
// -----------------------------------------------------------------------------

// 给定 nums: number[] 和 k: number，返回一个新数组，每个值最多保留 k 次，顺序不变
// 

// → 输入：nums = [1,1,1,2,2,3,3,3], k = 2
// → 输出：[1,1,2,2,3,3]
//
//

// 提示：用 Map<number, number> 记录当前已保留次数，超过 k 就跳过
// Hint: record the count kept with Map<number, number>; skip it for larger k

// -----------------------------------------------------------------------------
// 1. Standard version 
// -----------------------------------------------------------------------------

function uniqueFrequencyLargerK(nums: number[], k: number): number[] {
    // key: number; value: how many times it has been kept
    const countMap = new Map<number, number>();
    const result: number[] = [];

    for (const num of nums) {
        // count of a number
        const count = countMap.get(num) ?? 0;
        
        if (count < k) {
            countMap.set(num, count + 1);
            result.push(num);
        }
    }

    return result;
}

console.log(uniqueFrequencyLargerK([2, 3, 2, 2, 1], 1));
console.log(uniqueFrequencyLargerK([1, 2, 1, 2, 1, 2], 2));

// -----------------------------------------------------------------------------
// 2. filter version 
// -----------------------------------------------------------------------------

function uniqueFrequencyLargerKFilter(nums: number[], k: number): number[] {
    // key: number; value: how many times it has been kept
    const countMap = new Map<number, number>();

    return nums.filter(num =>{
        const count = countMap.get(num) ?? 0;
        if (count < k) {
            countMap.set(num, count + 1);
            return true;
        }
        return false;
    });

}

console.log(uniqueFrequencyLargerKFilter([2, 3, 2, 2, 1], 1));
console.log(uniqueFrequencyLargerKFilter([1, 2, 1, 2, 1, 2], 2));


// -----------------------------------------------------------------------------
// E2-3：只保留第一次出现位置的下标
// E2-3: keep only the first-occurrence indices
// -----------------------------------------------------------------------------

// 给定 nums: number[]，
// 按出现顺序，返回每个不同数组第一次出现的位置组成的数组，
// Given nums: number[], return an array of indices.
// In the order of appearance, include the index of each distinct number's first occurrence.

// → 输入：nums = [4, 2, 4, 3, 2]
// → 输出：[0, 1, 3]（4 首次在 0，2 首次在 1，3 首次在 3）
// 
// 

// 提示：迭代一遍时，用 Set 记录“已经见过的值”，第一次见到时把 index 推入结果；
// Hint: In an iteration over it, record "the value seen" with Set; 
// push the result at first occruence

function uniquePosition(nums: number[]): number[] {

    if (nums.length === 0) return [];
   
    const seen = new Set<number>();
    const result: number[] = [];

    for (let i = 0; i < nums.length; i++) {
        const x = nums[i]!;
        if (!seen.has(x)) {
            seen.add(x);
            result.push(i);
        }
    }
    return result;
}

console.log(uniquePosition([4, 2, 4, 3, 2]));
console.log(uniquePosition([4, 2, 4, 3, 2, 1, 0]));

// -----------------------------------------------------------------------------
// E2-4：去重后保持排序 + 去重前顺序无要求
// E2-4: 
// -----------------------------------------------------------------------------

// 给定 nums: number[]，返回“去重 + 排序（升序）”后的数组。

// → 输入：[3, 1, 2, 3, 2]
// → 输出：[1, 2, 3]
// → 
// → 

// 提示：这里顺序不再是“第一次出现顺序”，可以用 Set 或 Map 收集后转为数组再排序
// 

// -----------------------------------------------------------------------------
// 1. Set version 
// -----------------------------------------------------------------------------


function uniqueSortedArraySet(nums: number[]): number[] {

    if (nums.length === 0) return [];

    const seen = new Set<number>();
    // or just const res = [...new Set(nums)].sort((a, b) => a - b)
    // so the follow-up using raw and [...raw].sort is not needed
    const raw: number[] = [];

    // the "raw material", an unsorted array
    for (const num of nums) {
        if (!seen.has(num)) {
            seen.add(num);
            raw.push(num);
        }
    }

    // the "processed material", a sorted array in ascending order
    const result: number[] = [...raw].sort((a, b) => a - b);

    return result;

}

console.log(uniqueSortedArraySet([3, 1, 2, 3, 2]));
console.log(uniqueSortedArraySet([3, 1, 2, 3, 2, -1, -5]));

// -----------------------------------------------------------------------------
// 2. Set version 
// -----------------------------------------------------------------------------

function uniqueSortedArrayMap(nums: number[]): number[] {

    if (nums.length === 0) return [];

    // key: number; value: its frequency
    const seen = new Map<number, number>();
    const raw: number[] = [];

    for (const num of nums) {
        const first = seen.get(num) ?? 0;
        if (first === 0) {
            seen.set(num, 1);
            raw.push(num);
        }
    }

    const result: number[] = [...raw].sort((a, b) => a - b);
    return result;

}

console.log(uniqueSortedArrayMap([3, 1, 2, 3, 2]));
console.log(uniqueSortedArrayMap([3, 1, 2, 3, 2, -1, -5]));
