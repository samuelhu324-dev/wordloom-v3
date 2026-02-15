// 题 6：数组去重并保持原顺序
// 输入：[2, 3, 2, 2, 1] → 输出：[2, 3, 1]
// 方法一：for + Set

function unique(nums: number[]): number[] {
    const seen = new Set<number>();
    const result: number[] = [];

    for (const num of nums) {
        if (!seen.has(num)) {
            seen.add(num);
            result.push(num);
        }
    }
    return result;
}

// 方法二：filter + Set

function unique(nums: number[]): number[] {
    const seen = new Set<number>();
    return nums.filter(num => {
        if (seen.has(num)) {
            return false;
        } else {
            seen.add(num);
            return true;
        }
    });
}


// 简单自测
console.log(unique([2, 3, 2, 2, 1]));   // [2, 3, 1]
console.log(unique([1, 1, 1]));         // [1]
console.log(unique([1, 2, 3]));         // [1, 2, 3]