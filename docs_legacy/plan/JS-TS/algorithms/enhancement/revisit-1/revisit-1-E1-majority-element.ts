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

// 方法 2：Map 计数
// Approach 2: Counting with Map

// 1) 思路 | Idea: 

// 1. 数组中一定存在一个元素，出现次数严格大于 n / 2
// 2. 直接用 Map<number, number> 统计每个元素出现的次数：
//   2.1 key = 元素值
//   2.2 value = 出现次数
// 3. 一边统计就一边在跑的时候检查：
//   3.1 如果当前元素的次数 > n / 2 ，立刻返回它；
//   3.2 由于题目保证一定存在多数元素，所以一定能跑一次的过程中就提早返回

// 1. In an array, sure that there exists an element whose frequency is strictly
// greater than n / 2.
// 2. Count the occurrence of each element with a Map<number, number> directly:
//  2.1 key = element value
//  2.2 value = count
// 3. While counting, checking on the fly:
//  3.1 If current occurence > n / 2, return it immedately;
//  3.2 Sure that for the problem a majority element exists, so sure that within one pass 
//  it can be returned earlier.

// 2) 步骤 / Steps:

function majorElementMapCounting(nums: number[]): number {

// 1. 计算阈值：half = Math.floor(nums.length / 2) 并 创建 Map Counts
// 1. Compute a threshold: half = Math.floor(nums.length / 2) and create the Map Counts
    const counts = new Map<number, number>();
    const half = Math.floor(nums.length / 2);

// 2. 迭代遍 nums：
// 更新当前元素的次数: const c = (counts.get(num) ?? 0) + 1; count.set(num, c);
//   2.1 如果 c > half ，就立即返回 num
// 2. Iterate over nums: 
// Update its count: const c = (count.get(num) ?? 0) + 1; count.set(num, c);
//  2.1 If c > half, return num immediately

    for (const num of nums) {
        const c = (counts.get(num) ?? 0) + 1;
        counts.set(num, c);
        if (c > half) return num;
    }

// 3. 理论上，我们永远走不到最后这，我们到了的话，就抛错。
// 3. In theory we never reach the end; if we do, throw an error.

    throw new Error('Invalid Array');
}

// 4. 自测
// 4. Self-test

console.log(majorElementMapCounting([2,2,1,1,1,2,2]));
console.log(majorElementMapCounting([2,2,1,1,1,2,2,3,3,3,3,3,1,1,1,1,1,1,1]));

// 3) 复杂度 | Compelxity:
// 1. 时间：O(n)，只需过一次；
// 2. 空间：O(k)，k 为不同元素个数，要在 Map 中存每种元素的计数
// 1. Time: Just One pass needed
// 2. Space: k is the number of different elements. 
// Need a map entry for each distinct value.

// 4) 练习 | Practice:

function majorElementMapCounting2(nums: number[]): number {

    const major = new Map<number, number>();
    
    for (const num of nums) {

        // while counting check on the fly.
        const count = (major.get(num) ?? 0) + 1;
        // Store the num and c(count) pair
        major.set(num, count);
        if (count > nums.length / 2) return num;
    }

    throw new Error('Invalid Array.')
}

console.log(majorElementMapCounting2([2,2,2,2,2,1,1,1]));
console.log(majorElementMapCounting2([2,2,2,2,2,1,1,1,3,3,3,2,2,2,2,2,2,2]));

// 方法 3：Boyer–Moore 投票算法
// Approach 3:  Boyer–Moore Voting Algorithm

// 1) 思路 | Idea:
// 1. 设真正的多数元素为 x，出现超过 n /2 次
// 2. 想成投票和抵消过程：
//   2.1 每出现一次 x 的时候，给 x +1
//   2.2 每个 非x 元素抵掉 x 的一票；
// 3. 因为 x 的票比其他算上的所有元素多，不可能被完全抵消干净
// 所以整轮抵消结束后，剩下的候选人一定是 x；

// 1. Let the real majority element be x, appearing more than n / 2 times
// 2. Think of it as a voting and cancellation process:
//  2.1 Every occrrence of x gives + 1 to x;
//  2.2 Every non-x element cancels out one vote from x.
// 3. Since x has more votes than all others combined,
// impossible to be fully cancelled out.
// After one full pass of cancellation, the remaining candidate must be x.

// 2. 步骤 | Steps:

function majorElementCancel(nums: number[]): number {

// 1. 维护两个变量
//   1.1 candidate: 当前的候选多数票
//   1.2 count: 当前候选元素的“净票数”
// 1. Maintain two variables
//   1.1 candidate: current majority candidate
//   1.2 count: current net vote of the candidate

    let candidate = Infinity;
    let count = 0;

// 2. 每个 nums 中的元素 num：
//   2.1 If count === 0，说明之前的候选票与反对票抵消完了：
//   设 candidate = num，count = 1
//   2.2 Else if，如果 num === candidate，就 count++（同个元素，支持票）
//   2.3 Else，就 count--（不同元素，取消一票）
// 2. For each element num in nums:
//   2.1 If count === candidate, which suggests candidate and opposing votes are cancelled out
//   Set candidate = num and count = 1
//   2.2 Else if num === candidate: Do count++ (same element, supporting vote).
//   2.3 Else, count-- (different element, cancels one vote).

    for (const num of nums) {

        if (count === 0) {
            candidate = num;
            count = 1;
        } else if (num === candidate) {
            count++;
        } else {
            count--;
        }
    }

// 3. 循环后，candidate 就是多数元素（本题保证一定存在）
// 3. After the loop, candidate is the majority element (guaranteed by the problem).

return candidate;

}

// 4. 自测：
// 4. Self-test:

console.log(majorElementCancel([2,2,2,2,2,1,1,1]));
console.log(majorElementCancel([2,2,2,2,2,1,1,1,3,3,3,2,2,2,2,2,2,2]));

// 5) 为什么不等值可以用？| Why it works with many distinct values
// 1. 算法没有假设，只有两个不等值。
// 2. 只要某个值出现超过 n / 2 次：
//  2.1 我们可以按照“candidate vs 别的票”来思考
//  2.2 候选值和非候选值一定抵消得掉
//  2.3 真实的多数票比总共其他所有的票都多，所以无法完全抵消 

// 1. The algorithm does not assume there are only two distinct values.
// 2. As long as some value apepars more than n /2 times:
//  2.1 We can think in terms of "candidate vs. everyone else".
//  2.2 Cancellation always happens between the candidate and non-candidate values.
//  2.3 The true majority has more votes than all others together, 
//  so it cannot be fully cancelled.

// 6) 复杂度 | Complexity:
// 时间：O(n) - 过一次
// 空间：O(1) - 只用两个标准变量：candidate 和 count
// Time: O(n) - One pass.
// Space: O(1) - only two standard variables are used: candidate and count

function majorElementCancel2(nums: number[]): number {

    let count = 0;
    let candidate = Infinity;

    for (const num of nums) {

        // 1. first run: choose a num as a candidate
        // 2. subsequent run(s): if the candidate chosen was offset; choose a new one in place
        if (count === 0) {
            candidate = num;
        } else if (candidate === num) {
            count++;
        } else {
            count--;
        }
    }
    // given that some element is guaranteed to appear more than n /2 strictly,
    // for majority element, full cancellations won't happen.
    return candidate;
}

console.log(majorElementCancel2([1,1,1,1,1,1,2,2,2,2,3,1,1]));
console.log(majorElementCancel2([0,1,2,3,1,2,3,2,2,2,3,2,2,2,2]));
