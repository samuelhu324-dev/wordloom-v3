// J1. Subsets (backtracking)
// J1. 子集（回溯）

// Given an integer array nums with distinct elements, 
// return all possible subsets (the power set).
// 给定一个整数数组 nums（元素互不相同），返回所有可能的子集（幂集）。

function subsets(nums: number[]): number[][] {
    const result: number[][] = [];
    const path: number[] = [];

    function backtrack(start: number) {
        result.push([...path]);

        for (let i = start; i < nums.length; i++) {
            path.push(nums[i]!);
            backtrack(i + 1);
            path.pop();
        }
    }

    backtrack(0);
    return result;
}

console.log(subsets([1,2,3]));
