// D1. 无序数组的两数之和（数组 + Map）
// D1. Two-sum in an unsorted array (array + Map)
//
// 给定一个无序整数数组 nums 和一个目标值 target，
// 请返回和为 target 的两个不同元素的下标，顺序任意；
// 如果不存在这样的两个数，返回空数组 []。
//
// Given an unsorted integer array nums and an integer target,
// return the indices of two distinct elements whose sum is target (in any order).
// If no such pair exists, return an empty array [].
//
// 示例：
// 输入：nums = [3,2,4], target = 6
// 输出：[1,2]（因为 nums[1] + nums[2] = 2 + 4 = 6）
// Example:
// Input: nums = [3,2,4], target = 6
// Output: [1,2] (since nums[1] + nums[2] = 2 + 4 = 6)
//
// -----------------------------------------------------------------------------
// 1) 暴力思路（对比用） / Brute force (for comparison)
// -----------------------------------------------------------------------------
//
// 枚举所有 (i, j) , 0 <= i < j < n ，检查 nums[i] + nums[j] 是否等于 target
// 时间复杂度 O(n^2) ，当 n 较大时会超时
// Enumerate all pairs (i, j) (0 <= i < j < n) 
// and check whether nums[i] + nums[j] equals target
// Time complexity - O(n^2) - it will time out for larger n
//
// -----------------------------------------------------------------------------
// 2) 高效思路：数组 + Map / Efficient idea: array + Map
// -----------------------------------------------------------------------------
// 
// 我们在元素 x = nums[i] 的位置时，只需要知道之前有没有元素 y = target - x
// 这就是“从值查下标”的问题，用 Map 做哈希表即可
//
// When at element x = nums[i], we only need to know whether 
// there was a previous element y = target - x
// This is "value to index" lookup. Just make hash table with a Map.
//
// -----------------------------------------------------------------------------
// 3) 步骤 / Steps:
// -----------------------------------------------------------------------------

function unsortedSumSubarray(nums: number[], target: number): number[] {

// 1. 创建一个 Map<number, number>，记为 indexMap ，含义是：
//    - key = 某个数值，value = 该数值出现的下标
// 1. Create a Map<number, number> as indexMap, which means:
//    - key = some value, value = an index of its occurrence

    const indexMap = new Map<number, number>();

// 2. 从左到右迭代一遍数组下标 i = 0...n-1
//    - 当前数 x = nums[i]，需要的搭档是 y = target - x
//    - 检查 y 是否在 indexMap 里
//    - 如果有，说明存在某个下标 j（保存在 indexMap.get(y) 中）
//      满足 nums[j] + nums[i] === target，直接返回 [i, j]
//    - 如果没有，把当前值记进去：indexMap.set(x, i)，继续迭代
// 2. Iterate indices over the array from left to right i = 0...n-1
//    - For current number x = nums[i], the partner is y = target - x 
//    - Check whether y is already in indexMap
//    - If yes, that means some index j can be found and stored in indexMap.get(y)
//      for nums[j] + nums[i] === target; return [i ,j] directly.
//    - If not, write current value down: indexMap.set(x, i) and continue

    for (let i = 0; i < nums.length; i++) {
        const x = nums[i]!;
        const y = target - x;

        if (indexMap.has(y)) return [i, indexMap.get(y)!];

        indexMap.set(x, i);
    }

// 3. 如果循环完找不到数对，就返回 []
// If the loop finishes without finding a pair, return []

    return [];

}

// 4. 自测
// 4. Self-test

console.log(unsortedSumSubarray([1, 2, 3], 5));
console.log(unsortedSumSubarray([1, -1, 1, 0], 0));

//
// -----------------------------------------------------------------------------
// 4) 正确的理由 / Why this is correct:
// -----------------------------------------------------------------------------
// 
// 1. 我们始终只把“遇到的元素”放进 indexMap，因此下标都不等
// 2. 一旦在 indexMap 里找到 y ，就说明存在早于 i 的下标 j
//    使得 nums[j] + nums[i] === target，题目只要“任意一对”，
//    所以第一对发现时就可以返回
// 1. We only ever store "elements seen" into indexMap, 
//    thus both indices are distinct.
// 2. Once we find y in indexMap, that means it has an index j prior to i
//    making nums[j] + nums[i] === target; the problem needs only "any pair"
//    so when the first pair is found, we can return it.
//
// -----------------------------------------------------------------------------
// 5) 复杂度 / Complexity:
// -----------------------------------------------------------------------------
// 
// 1. 每个元素大多数时候只被 插入（Set）/ 查询（get）一次，
//    Map 的预期时间平均都是 O(1)
// 2. 总时间复杂度：O(n)；空间复杂度：O(n)；
// 1. Each element is inserted (Set) / looked up at most once; 
//    each operation is O(1) on average
// 2. Total time complexity: O(n); space complexity: O(n);
// 
// -----------------------------------------------------------------------------
// 6) 练习 / Practice:
// -----------------------------------------------------------------------------
// 
// 1. tie-break: 返回任意数对 / return any pair
 
function unsortedAnySum(nums: number[], target: number): number[] {
    const indexMap = new Map<number, number>();

    for (let i = 0; i < nums.length; i++) {
        // Create x, y as key (number) in indexMap
        const x = nums[i]!;
        const y = target - x;
        // return a pair of indices
        if (indexMap.has(y)) return [i, indexMap.get(y)!];
        
        indexMap.set(x, i);
            
    }
    return [];
}

console.log(unsortedAnySum([1, 2, 3], 5));
console.log(unsortedAnySum([1, -1, 1, 0], 0));

//
// 2. count 版 / count version
// 

function unsortedSumCount(nums: number[], target: number): number {
     
    if (nums.length === 0) return 0;

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

console.log(unsortedSumCount([1, 2, 3], 5));
console.log(unsortedSumCount([1, -1, 1, 0], 0));

// 
// 3. All-pairs versions / 所有对 版 
// 

function unsortedSumAllPairs(nums: number[], target: number): number[][] {
    
    const indexMap = new Map<number, number>();
    // This is a tuple [number, number] defined by the generic
    // but contained in an array
    const result = new Array<[number, number]>();

    for (let i = 0; i < nums.length; i++) {

        if (nums.length === 0) return [];

        const x = nums[i]!;
        const y = target - x;
        
        if (indexMap.has(y)) {
            result.push([x, i])
        };
        
        indexMap.set(x, i);
    }

    return result;
}

console.log(unsortedSumAllPairs([1, 2, 3], 5));
console.log(unsortedSumAllPairs([1, -1, 1, 0], 0));
