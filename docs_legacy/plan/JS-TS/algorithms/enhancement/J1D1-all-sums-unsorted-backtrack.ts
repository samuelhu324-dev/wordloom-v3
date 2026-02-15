// J1D1. All index combinations with sum >= target (unsorted array + backtracking)
// J1D1. 无序数组中，所有满足和 >= target 的下标组合（回溯）
//
// -----------------------------------------------------------------------------
// 题目说明 / Problem statement
// -----------------------------------------------------------------------------
// 给定一个无序整数数组 nums 和一个目标值 target，
// 请找出所有满足「其对应元素之和 >= target」的下标组合。
// 这里的“下标组合”指：从数组中选出若干个不同的下标 i1, i2, ..., ik（k ≥ 2），
// 只要 nums[i1] + nums[i2] + ... + nums[ik] >= target，就把 [i1, i2, ..., ik] 视为一个合法解。
//
// 要求：
//   1. 每个下标在同一个组合中最多出现一次（不能重复使用同一元素）。
//   2. 组合内部的下标顺序可以不固定，但为了避免重复，通常约定按升序输出
//      （例如 [0,1,2] 和 [2,1,0] 认为是同一个组合，只保留其中一种形式）。
//   3. 返回值是由所有合法下标数组组成的列表，列表中各个组合的顺序可以任意。
//   4. 如果不存在任何这样的下标组合，返回空数组 []。
//
// Given an unsorted integer array nums and an integer target,
// find all index combinations whose corresponding elements sum to at least target.
// An "index combination" means choosing distinct indices i1, i2, ..., ik (k ≥ 2)
// such that nums[i1] + nums[i2] + ... + nums[ik] >= target.
// Each valid combination [i1, i2, ..., ik] should be returned once.
//
// Requirements:
//   1. Each index can be used at most once in a single combination.
//   2. The order of indices inside a combination does not matter;
//      to avoid duplicates we normally output them in ascending order
//      (e.g. [0,1,2] and [2,1,0] are considered the same; keep only one).
//   3. The function returns a list of all such index-arrays; the outer list order is arbitrary.
//   4. If no such combination exists, return an empty array [].
//
// 示例 / Example
// nums = [2, 3, 4, 4], target = 5
// 一些合法的下标组合（按升序写出一种形式即可，例如）：
//   [0,1]  -> nums[0] + nums[1] = 2 + 3 = 5
//   [0,2]  -> 2 + 4 = 6
//   [1,2]  -> 3 + 4 = 7
//   [0,1,2] -> 2 + 3 + 4 = 9
//   [0,3], [1,3], [2,3], [0,1,3], [0,2,3], [1,2,3], [0,1,2,3], ...
// 函数应返回包含所有这类下标数组的列表（顺序任意）。
// -----------------------------------------------------------------------------

function allSumsUnsortedBacktracking(nums: number[], target: number): number[][] {
  
  return [];
}

// -----------------------------------------------------------------------------
// 1) 思路 / Idea:
// -----------------------------------------------------------------------------

// 1. Find out all subsets of indices such that
//    nums[i1] + nums[i2] + ... num[ik] >= target
// 2. Order inside a combination doesn't matter, so we mandate:
//    Always choose indices in increasing order (0 -> 1 -> 2 -> ...)
//    This way [0,1,2] is generated only once , never as [2,1,0]  
// 3. Core technique: backtracking (DFS over subsets)
// 4. Maintain:
//    - path: number[] - current chosen indices
//    - sum: number - current sum of nums[path[*]]
//    - start: number - next index we are allowed to choose from
// 5. Recursive function: backtrack(start, sum):
//    5.1 Loop i from start to nums.length - 1:
//        - Choose index i: path.push(i), newSum = sum + nums[i]
//        - If newSum >= target, make a copy of path and into results.
//        - Recurse: backtrack(i + 1, newSum)
//          (only pick indices after i, so each index used <= 1 time, no permutations)
//        - Backtrack: path.pop() to undo the choice and try the next i.
// 6. Start with backtrack(0,0)
//
// 1. 找出所有下标子集，nums[i1] + nums[i2] + ... num[ik] 才 >= target
// 2. 组合里面的顺序无所谓，我们强制：
//    下标始终顺序递增选 (0 -> 1 -> 2 -> ...)
//    这样 [0,1,2] 生成仅一次，永远不会有 [2,10]
// 3. 核心技术：回溯 (DFS 整个子集)
// 4. 维护：
//    - path: number[] - 当前选中的下标
//    - sum: number - nums[path[*]] 当前的和
//    - start: number - 可以让我们从中选择的下一个下标
// 5. 递归函数：backtrack(start, sum):
//    5.1 从 start 到 nums.length - 1 循环
//        - 选择下标：path.push(i)，newSum = sum + nums[i]
//        - 若 newSum >= target ，把当前 path 拷贝一份进 results
//        - 递归：backtrack(i + 1, newSum)
//          (只能挑 i 后的下标，所以每个下标使用小于 1 次，不做排列组合)
//        - 回溯：path.pop()，撤销这次选择，试下个 i 
// 6. 用 backtrack(0,0) 来扫：

function allSumunsortedbacktracking(nums: number[], target: number): number[][] {
  const results: number[][] = [];
  const path: number[] = [];

  function backtrack(start: number, sum: number) {
    
    for (let i = start; i < nums.length; i++) {
      path.push(i);
      const newSum = sum + nums[i]!;

      if (newSum >= target) {
        results.push([...path]);
      }

      backtrack(i + 1, newSum);
      path.pop();
    }
  }
  backtrack(0,0);
  return results;
}

// 7. 自测
// 7. Self-test

console.log(allSumunsortedbacktracking([2,3,4,4], 5));

// -----------------------------------------------------------------------------
// 2) Properties / 属性
// -----------------------------------------------------------------------------

// 1. Covered all subsets: every index is either chosen or skipped 
//    as we walk from left to right
// 2. No duplicates: indices are always added in ascending order
// 3. Supported "compound combinations": a path will be recorded once >= target,
//    but recursion continue to expand to the right, thus leading to
//    longer combinations (e.g. [0,1] to [0,1,2] etc.)

// 1. 考虑了所有子集：每个下标我们从左到右跑的时候，要么选中要么跳过
// 2. 没有重复内容：下标始终以升序添加
// 3. 支持了“复数组合”：一条路径一旦满足 >= target 会被记录，但递归继续向右扩展
//    从而得到更长的组合（例如 [0,1] 扩到 [0,1,2] 等）

// -----------------------------------------------------------------------------
// 3) Practice / 练习
// -----------------------------------------------------------------------------

