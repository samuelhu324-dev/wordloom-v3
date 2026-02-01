// J1. Subsets (backtracking)
// J1. 子集（回溯）

// Given an integer array nums with distinct elements, 
// return all possible subsets (the power set).
// 给定一个整数数组 nums（元素互不相同），返回所有可能的子集（幂集）。

// -----------------------------------------------------------------------------
// 1) Core idea / 核心想法：
// -----------------------------------------------------------------------------

// Thinking of buiding subset as walking a decision tree
// For each position i, we can choose whether to include nums[i] or skip it  
// 把构建子集的过程看成走一颗决策树：
// 每个位置 i ，可以选择要 nums[i] 或不要 nums[i] 

function subsetsBackstring(nums: number[]): number[][] {
// 1. We use DFS + backtracking to go through all choesn paths 
//    - path: the current subset we are building
//    - start: the first index we are allowed to pick nex
//             so we never go backwards or repeat 
// 1. 我们用 DFS + 回溯，把所有选择路径都走一遍:
//    - path: 我们在构建的当前子集
//    - start: 可以由我们接下来去取的第一个下标（所以我们绝不走回头路或重复）

    const result: number[][] = [];
    const path: number[] = [];

    function backtrack(start: number) {

// 2. For each call backstring(start):
//    - The current path is already one valid subset, so record it:
//      result.push([...path]);
// 
// 2. 任意一次调用 backstring(start):
//    - 当前的 path 就是一个符合条件的子集，记录一下：
//    - result.push([...path]);

        result.push([...path]);

// 3. Then enumerate the possible elements from i = start:
//     The pattern  push → recursion → pop is to "make a choice" 
//     → dive into this branch → back to current node → try next choice
//
// 3. 然后从 i = start 枚举后面的元素：
//   push → 递归 → pop 这套，就是“做选择” → 深入这一分支 
//   → 回到当前节点 → 尝试下一种选择  

        for (let i = start; i < nums.length; i++) {
            path.push(nums[i]!);
            backtrack(i + 1);
            path.pop();
        }
    }

    backtrack(0);
    return result;
}

// 4. Self-test
// 4. 自测
console.log(subsetsBackstring([1, 2, 3]));
console.log(subsetsBackstring([3, 2]));

// -----------------------------------------------------------------------------
// 2) Complexity / 复杂度
// -----------------------------------------------------------------------------

// Time: - visit two states of each element (choose or not); 2^n subsets in total
//         with each subset copied once. 
//       - Overall: O(n * 2^n) 
// Space: recursive stack and path with depth of n at most: O(n) (excluding output)
// 时间:  - 访问每个元素两种状态（选/不选） 一共 2^n 个子集，每个子集复制一次 
//          整体 O(n * 2^n) 
// 空间：递归栈和 path 最多深度 n ，O(n) (不计输出)

// -----------------------------------------------------------------------------
// 3) Practice / 练习
// -----------------------------------------------------------------------------

function subsetsBackstring2(nums: number[]): number[][] {
    const result: number[][] = [];
    const path: number[] = [];
    backstring(0);
    return result;

    function backstring(start: number) {
        result.push([...path]);

        for (let i = start; i < nums.length; i++) {
            path.push(nums[i]!);
            backstring(i + 1);
            path.pop();
        }
    }
}

console.log(subsetsBackstring2([1, 2, 3]));
console.log(subsetsBackstring2([3, 2]));