// E1. Majority element (Map / counting)
// E1. 多数元素（Map / 计数）

// Given an integer array nums of length n, you are guaranteed that
// there exists an element that appears strictly more than n / 2 times.
// Find and return the value of that element.

// 给定一个长度为 n 的整数数组 nums，已知其中一定存在一个元素出现次数严格大于 n / 2，
// 请找出并返回这个元素的值。

// 示例：
// 输入：[2,2,1,1,1,2,2] → 输出 2
// Example:
// Input: [2,2,1,1,1,2,2] → Output: 2

// -----------------------------------------------------------------------------
// 1) "One" element that appears strictly more than "n / 2 times".
// -----------------------------------------------------------------------------

function majorityElement_One(nums: number[]): number {
    
    const seen = new Map<number, number>();
    for (const num of nums) {
        
        seen.set(num, (seen.get(num) ?? 0) + 1);

        const half =  Math.floor(nums.length / 2);

        if (seen.get(num)! > half) return num;
    }

    throw new Error('no such a number');

}

console.log(majorityElement_One([2,2,1,1,1,2,2]));
console.log(majorityElement_One([2,2,1,1,1,2,2,3,2,3,2,2]));

// -----------------------------------------------------------------------------
// 2) Boyer-Moore Candidate-voting version / Constraints: > n / 2
// -----------------------------------------------------------------------------

function BoyerMoore(nums: number[]): number{
    
    let candidate = 0;
    let count = 0

    for (const num of nums) {
        
        if (count === 0) {
            candidate = num;
            count++;
        } else {
            if (num === candidate) {
                count++;
            } else {
                count--;
            }
        }
    }

    return candidate;
}

console.log(BoyerMoore([2,2,1,1,1,2,2]));
console.log(BoyerMoore([2,2,1,1,1,2,2,3,2,3,2,2]));


// -----------------------------------------------------------------------------
// 3) "At least one" element that appears strictly more than "n / 3 times".
// -----------------------------------------------------------------------------

function majorityElement_AtLeastOne(nums: number[]): number[] {

    if (nums.length === 0) return [];
    
    const seen = new Map<number, number>();
    const results: number[] = [];

    for (const num of nums) {
        // count the new number from one
        seen.set(num, (seen.get(num) ?? 0 ) +1);

        const third = Math.floor(nums.length / 3);

        if (seen.get(num)! > third) {
            if (!results.includes(num)) {
                results.push(num)
            }
        }
    }
    return results;
}

console.log(majorityElement_AtLeastOne([2,2,1,1,1,2,2]));
console.log(majorityElement_AtLeastOne([2,2,1,1,1,2,2,3,3,3,3,3,2,2,3,3,3,2,2]));


