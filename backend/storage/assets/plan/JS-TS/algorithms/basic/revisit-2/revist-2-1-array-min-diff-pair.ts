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

// 1) 思路 | Idea：

// 1. 核心：如果把数组从小到大排好序，那么差值最小的一对数一定在某一对相邻元素之间
// 不可能隔得很远
// 1. Core: If making the array sorted in ascending order, 
// then the pair with minimum difference must be among some contiguous elements,
// not probably being far apart.

// 2) 步骤 | Steps:

function mindiffpair(nums: number[]): number {

// 1. 先判断数组长度，小于2直接抛错，因为没法组成一对数
// 1. Tell the length of the arrary first; throw an error if less than 2,
// since you cannot form a pair.

    if (nums.length < 2) {
        throw new Error('No pair can be formed.')
    }

// 2. 浅拷贝一份数组并从小到大排序，避免修改原数组
// 2. Make a shallow copy of the array and sort it in ascending order
// to avoid modifying the original array.
// array-modified version: const arr = nums.sort((a, b) => a - b);

    const arr = [...nums].sort((a, b) => a - b);

// 3. 用一个变量ans存当前发现的最小值，初始设为Infinity.
// 3. Store the min-diff found currently using a variable ans, 
// setting the inital to Infinity.

    let ans = Infinity;

// 4. 从左到右遍历排序后的数组；每个下标i（1开头）
// 只计算它和前一个元素i-1的差值 sorted[i] - sorted[i - 1]。
// 4. Traverse the sorted array from left to right. For each index i (starting from 1),
// only compute the difference between between sorted[i] 
// and its previous element sorted[i -1]

    for (let i = 1; i < arr.length; i++) {
     const cur = arr[i];
     const pre = arr[i -1];
     const mindiff = cur! - pre!;

// 5. 如果这个差值比当前ans更小，就更新ans。
// 5. If this diffrence is smalle than the current ans, update ans.

     if (mindiff < ans) {
        ans = mindiff;
     }

    }

// 6. 遍历后，ans就是所有数对中最小的差值，返回ans。
// 6. After the traversal, ans would be the min difference among all pairs; 
// return ans.

return ans;

}

// 7. 自测
// 7. self-test

console.log(mindiffpair([2, 7, 9, -1, 3]));
console.log(mindiffpair([-1, 0, 1, 2]));
console.log(mindiffpair([-1, -3, 5, 3, 2]));

// 3) 练习 | Practice:

function mindiffpair2(nums: number[]): number {
    if (nums.length < 2) {
        throw new Error('Not a pair');
    }

    let ans = Infinity;

    const sort = [...nums].sort((a, b) => a - b);

    for (let i = 1; i < sort.length; i++) {
        const cur = sort[i]!;
        const pre = sort[i - 1]!;
        const mindiff = cur - pre;

        if (mindiff < ans) {
            ans = mindiff;
        }
    }
return ans;

}

console.log(mindiffpair2([2, 7, 9, -1, 3]));
console.log(mindiffpair2([-1, 0, 1, 2]));
console.log(mindiffpair2([-1, -3, 5, 3, 2]));

// 方法二：使用 Set 存储已访问元素 / 双重for循环
// Approach 2： Store elements visited using Set / Double-for-loops

// 1) 思路 | Idea：
// 1. 核心：依次遍历数组，维护一个“已经遇到的元素集合 (Set) ”; 当前元素，和之前遇到的
// 每一个元素求绝对值，持续更新最小差值。
// 1. Core: Traverse the array in turn and maintain a set of elements seen before.
// For each current element, find the absolute difference with every previously
// seen element and  update minimum difference continuously.

// 2）步骤 | Steps:

function mindiffpairset(nums: number[]): number {

// 1. 先判断数组长度，小于2直接抛错；
// 1. Check the array length first; throw an error directly if it's less than 2;

    if (nums.length < 2) {
        throw new Error('No pair found.')
    }

// 2. 创建一个空的 Set<number> 储存已经遍历过的元素
// 2. Create an empty Set<number> to store the elements 
// that have already been traversed.

    const seen = new Set<number>();

// 3. 定义变量 ans = Infinity,记录当前最小差值
// 3. Define a variable ans = Infinity to keep track of current minimum difference.

    let ans = Infinity;

// 4. 使用 for ... of 遍历数组 nums 中的每个元素 num :
// 4. Traverse each element num in the array nums using for ... of

    for (const num of nums) {

// 4.1 seen 集合中的每个元素s，计算绝对差值 Math.abs(num - s)
// 4.1 For each element in the seen set, 
// compute the absolute difference Math.abs(num - s)

        for (const s of seen) {
            
            const mindiff =  Math.abs(num - s);

// 4.2 如果这个差值比当前ans更小，就更新ans
// 4.2 If this difference is smaller than the current ans, update ans.

            if (mindiff < ans) {
                ans = mindiff;
            }

        }

// 4.3 当前元素和之前所有元素比较结束后，把当前元素 num 加入 seen，
// 表示之后遇到的新元素也要和它比较，并且第一轮 seen 集合没有元素时就跳过内嵌的循环
// 直接add一个新num到seen中；
// 4.3 Add the current element num into seen after finishing comparisons between
// num and all previously elements seen before, and when there's no element 
// in the seen set at first round, skip the nested loop, add a new num into seen directly.

        seen.add(num);

    }

// 5. 遍历结束后，返回 ans 返成所有数对的最小差值
// 5. Return the ans as the minimum difference of all pairs after traversal ends.

return ans;

}

// 6. 自测
// 6. Self-test

console.log(mindiffpairset([2, 5, 8, 10, 11, 0]));
console.log(mindiffpairset([1, -5, -20, -23]));
console.log(mindiffpairset([0]));

// 7. 练习
// 7. Practice

function mindiffpairset2(nums: number[]): number {
    if (nums.length < 2) {
        throw new Error('No pair given');
    }

    let ans = Infinity;
    const seen = new Set<number>();

    for (const num of nums) {
        
        for (const s of seen) {
            const mindiff = Math.abs(s - num);
            if (mindiff < ans) {
                ans = mindiff;
            }
        }

        seen.add(num);
    }

return ans;

}

console.log(mindiffpairset2([2, 5, 9, 10]));
console.log(mindiffpairset2([10, -100, -400, 200]));
console.log(mindiffpairset2([1]));

