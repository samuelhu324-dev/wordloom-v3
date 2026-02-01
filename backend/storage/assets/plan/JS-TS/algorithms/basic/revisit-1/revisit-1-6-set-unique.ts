// 题 6：数组去重并保持原顺序
// Problem 6: Remove duplicates from an array while preserving the original order


// 输入：[2, 3, 2, 2, 1] → 输出：[2, 3, 1]
// Input: [2, 3, 2, 2, 1] → Output: [2, 3, 1]

// 方法一：for + Set
// Method 1: for loop + Set

function SetUnique1(nums: number []): number[] {
    const seen = new Set<number>();
    const result: number [] = [];

    for (const num of nums) {
        if (!seen.has(num)) {
            seen.add(num);
            result.push(num);
        }
    }

return result;

}

// self-test

console.log(SetUnique1([2, 3, 1, 3, 4, 5, 5]));
console.log(SetUnique1([2, 5, 6, 6]));


// 方法二：filter + Set
// Method 2: filter + Set

function SetUnique2(nums: number[]): number[] {
    
    const seen = new Set<number>();

    return nums.filter(num => {
        if (seen.has(num)) {
            return false;
        } else {
            seen.add(num);
            return true;
        }
    }
    )
}

// self-test

console.log(SetUnique2([2, 3, 1, 3, 4, 5, 5]));
console.log(SetUnique2([2, 5, 6, 6]));
