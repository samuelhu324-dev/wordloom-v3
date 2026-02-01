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
// 1. tie-break 版 / tie-break version with unique result
// -----------------------------------------------------------------------------

function unsortedTwoSumUnique(nums: number[], target: number): number[] {
    // key: a number, value: target - number;
    const indexMap = new Map<number, number>();

    for (let i = 0; i< nums.length; i++) {
        const x = nums[i]!;    // current value
        const y = target - x;  // value match
        if (indexMap.has(y)) {
            return [i,indexMap.get(y)!];
        }
        indexMap.set(x, i);
    }
    return [];
}

console.log(unsortedTwoSumUnique([2,3,4,3],6));
console.log(unsortedTwoSumUnique([2,3,4,3,4],8));

// -----------------------------------------------------------------------------
// 2. Count 版 / Count version
// -----------------------------------------------------------------------------

function unsortedTwoSumCount(nums: number[], target: number): number {
    let count = 0
    const indexMap = new Map<number, number>();

    for (let i = 0; i < nums.length; i++) {
        const x = nums[i]!;
        const y = target - x;
        if (indexMap.has(y)) { // hit the target
            count++;
        }
        indexMap.set(x, i);
    }
    return count;
}

console.log(unsortedTwoSumCount([2,3,4,3],6));
console.log(unsortedTwoSumCount([2,3,4,3,4],8));

// -----------------------------------------------------------------------------
// 3. All pairs 版 + >= target/ All pairs version + >= target
// -----------------------------------------------------------------------------

// 1. Goal: Given an unsorted array nums, find all index pairs [i,j] such that
//          nums[i] + nums[j] >= target
// 2. Upshot: 
//    - Since we want all pairs, we must enumerate every valid (i,j)
//      not just one pair or a count.
//    - To avoid duplicates and self-pairing: 
//      - We specify only consider j < i :
//        - Outer loop chooses the right index i from 0 to n-1 
//        - Inner loop scans all previous indices j = 0 ... i-1
//    - and this guarantees:
//      - No(i,i): same element will not pair with itself
//      - Each unordered pair appears exactly once (we get (0,1) but never (1,0) again)
//    - Inside the inner loop:
//      - Take x = nums[i]，y = nums[j]
//      - If x + y >= target，push the pair [j,i] (or [i,j], as you prefer) into results.
// 3. Complexity:
//    - Time: outer loop O(n) × inner loop up to O(n) -> O(n^2)
//    - Extra space: O(1) besides the result list
//
// 1. 目标：给定无序数组 nums ，找到所有下标数对 [i,j] ，nums[i] + nums[j] 才 >= target
// 2. 要点：
//    - 因为要所有的数对，所以必须枚举全部符合条件的 (i,j)
//    - 要避免重复 & 自身配对：
//      - 我们具体说明只考虑 j < i:
//        - 外层循环从 0 到 n-1 选择右下标 i：
//        - 内层循环扫描所有之前的下标 j = 0 ... i-1
//      - 这就保证:
//        - 没有 (i,i) : 同一元素不会和自己组成一对
//        - 每个无序数对恰好出现一次 (有 (0,1) 但不会再有 (1,0))
//      - 在内层循环里面：
//        - 取 x = nums[i], y = nums[j]
//        - 若 x + y >= target，就把数对 [j,i] 推入结果（或者 [i,j] 随你）
// 3. 复杂度：
//    - 时间：外层循环 O(n) 乘以内层循环乘到 O(n) -> O(n^2)
//    - 额外空间：除一连串结果之外 O(1)
// 

function unsortedTwoSumGreater(nums: number[], target: number): number[][] {

    const results: Array<[number,number]> = []

    for (let i = 0; i < nums.length; i++) {
        // to make sure no duplicates in the results, we want to:
        for (let j = 0; j < i; j++) {
            const sum = nums[i]! + nums[j]!;
            if (sum >= target) {
                results.push([i,j]);
            }
        }
    }
    return results;
}

console.log(unsortedTwoSumGreater([2,3,4,3],6));
console.log(unsortedTwoSumGreater([2,3,4,3,4],8));

// -----------------------------------------------------------------------------
// 3.1 All pairs 版 + >= target + 更多求和组合
// / All pairs version + >= target + more combinations that we find sum
// -----------------------------------------------------------------------------

// See J1D1
