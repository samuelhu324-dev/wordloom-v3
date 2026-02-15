// E1. 多数元素（Map / 计数）
// E1. Majority element (Map / counting)

// 给定一个长度为 n 的整数数组 nums，已知其中一定存在一个元素出现次数严格大于 n / 2，
// 请找出并返回这个元素的值。

// Given an integer array nums of length n, you are guaranteed that
// there exists an element that appears strictly more than n / 2 times.
// Find and return the value of that element.

// 示例：
// 输入：[2,2,1,1,1,2,2] → 输出 2
// Example:
// Input: [2,2,1,1,1,2,2] → Output: 2


// Appraoch 1: my solution

function majorityElement(nums: number[]): number {

    // key: element - value: count
    const major = new Map<number, number>();
    let count = 1;
    let curr = nums[0]!;

    for (let i = 1; i < nums.length; i++) {

        if (nums[i] === curr) {
        count ++;

        } else {
            // Here supports the count of an array without being sorted
            // that is, it supports segmented count
            const pre =  nums[i - 1]! 
            major.set(pre, (major.get(pre) ?? 0) + count);
            count = 1;
            curr = nums[i]!;
        }
    }
    
    // The loop ends and it lacks the final .set(....). Add it!
    major.set(curr, (major.get(curr) ?? 0) + count);

    for (let j = 0; j < nums.length; j++) {

        const majorlength = major.get(nums[j]!)!;
        const givenlength = nums.length / 2;

        if (majorlength > givenlength) {
            return nums[j]!;
        }
    }

    throw new Error('Invalid Array');
}

console.log(majorityElement([2,2,1,1,1,2,2]));
console.log(majorityElement([2,2,1,1,1,2,2,1,1,1,1,1,1,1,1]));

// Approach 2: classic solution

function majorityElement2(nums: number[]): number {
    const counts = new Map<number, number>();
    const half = Math.floor(nums.length / 2);

    for (const num of nums) {
        const c = (counts.get(num) ?? 0) + 1;
        counts.set(num, c);
        if (c > half) return num;
    }
    
    throw new Error('Invalid Array');
}

console.log(majorityElement2([2,2,1,1,1,2,2]));
console.log(majorityElement2([2,2,1,1,1,2,2,1,1,1,1,1,1,1,1]));

// Approach 3: Boyer–Moore 投票算法，时间 O(n)，空间 O(1)
function majorityElement3(nums: number[]): number {
    let candidate: number | null = null;
    let count = 0;

    for (let i = 0; i < nums.length; i++) {
        const num = nums[i]!;
        if (count === 0) {
            candidate = num;
            count = 1;
        } else if (num === candidate) {
            count++;
        } else {
            count--;
        }
    }

    // 题目保证一定存在多数元素，可以直接返回 candidate!
    return candidate!;
}

console.log(majorityElement3([2,2,1,1,1,2,2]));
console.log(majorityElement3([2,2,1,1,1,2,2,1,1,1,1,1,1,1,1]));
