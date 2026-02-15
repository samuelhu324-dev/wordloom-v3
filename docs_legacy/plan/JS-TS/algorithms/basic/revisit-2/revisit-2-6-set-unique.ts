// 题 6：数组去重并保持原顺序
// Problem 6: Remove duplicates from an array while preserving the original order

// 实现函数 unique(nums: number[]): number[]，返回一个新数组
// 去掉重复元素，保留第一次出现的顺序。
// Implement a function unique(nums: number[]): number[] that returns a new array
// with duplicates removed, keeping the order of their first occurrence.

// - 输入：[2, 3, 2, 2, 1] → 输出 [2, 3, 1].
// - Input:  [2, 3, 2, 2, 1] → Output: [2, 3, 1]

// 方法一：for + Set
// Approach 1: for loop + Set

// 1) 思路 | Idea:
// 1. 用一个 Set 记录“已经见过的元素”；
// 1. Remember all seen numbers using a Set

// 2. 从左到右扫描数组，遇到一个新数字就：
//   2.1 加入 Set 并推入结果数组；
// 2. Scan the array from left to right; Seeing a new number:
//   2.1 Add it to the Set and push it into the result array

// 3. 这样既能去重，又能保持第一次出现时的顺序
// 3. It can both dedupe it and keep the order of first occurrence

// 2) 步骤 | Steps:

function unique(nums: number[]): number[] {

// 1. 创建空的 Set<number> 变量 seen ，存已经出现过的数字
// 1. Create an empty Set<number>, variable seen, to store numbers that have appeared.

    const seen = new Set<number>();

// 2. 创建空数组 result 存最终的去重结果
// 2. Create an empty array result to store the final deduped result.

    const result: number[] = [];

// 3. 使用 (const num of nums) 就可迭代
//  3.1 如果 seen 里还没有 num:
//  调用 seen.add(num) 标记为seen，
//  然后 result.push(num) 追加到结果中
//  3.2 如果已经在 seen 里，什么也不做（跳过重复元素）

// 3. using (const num of nums) iterate:
//   3.1 if seen hasn't contain num:
//   Call seen.add(num) to mark it as seen,
//   then result.push(num) to append it to the result.
//   3.2 If it's already in seen, do nothing (skip the duplicate).

    for (const num of nums) {
        if (!seen.has(num)) {
            seen.add(num);
            result.push(num)
        }

    }

// 4. 循环后返回 result
// 4. Return result after the loop

return result;

}

// 5. 自测
// 5. Self-test

console.log(unique([2, 4, 5, 5, 7, 9]));
console.log(unique([4, 3, 4, 3]));

// 3) 练习 | Practice:

function unique2(nums: number[]): number[] {

    // filter is used to remove the duplicates
    // and apend the new one into the result / Set by pushing/adding it.
    const result: number[] = [];
    const filter = new Set<number>();

    for (const num of nums) {
        if (!filter.has(num)) {
            result.push(num);
            filter.add(num);
        }
    }
return result;
}

console.log(unique2([2, 4, 5, 5, 7, 9]));
console.log(unique2([4, 3, 4, 3]));

// 方法二：filter + Set
// Approach 2: filter + Set

// 1) 思路 | Idea:
// 1. 同样使用 Set 设遇到的元素，一边遍历，一边决定“这个元素要不要保留”：
// 1. Use a Set of seen numbers as well. Traversing it while deciding 
// whether "this element should be kept" or not:

//   1.1 On the first occurrence of a number: add it to seen, return true to keep it. 
//   1.2 On later occurrence: seen already has it, return false to discard it. 
//   1.1 第一次出现的时候：添加到 seen 中，返回 true 保留
//   1.2 之后出现的时候：seen 已经有了，返回 false 丢弃

// 2) 步骤 | Steps:

function uniquefilter(nums: number[]): number[] {

// 1. 创建空的 Set<number> 叫 seen
// 1. Create an empty Set<number> called seen.

    const seen = new Set<number>();

// 2. 调用 nums.filter(num => {...}):
//   2.1 如果 seen.has(num) 为真，这是一个重复的元素 → 返回false，过掉
//   2.2 否则是第一次出现：
//   调用 seen.add(num) 记录
//   然后返回 真 ，filter 才保留该元素
// 2. Call nums.filter(num => {...}):
//   2.1 If seen.has(num) is true, this is a duplicate → return false, filter it
//   2.2 Otherwise this is its first occurrence:
//   Call seen.add(num) to record it, 
//   then return true so that filter keeps this element.
// 3. filter 的返回值就是去重后的新数组
// The value filter returns is the new array being deduped.

    return nums.filter(num => {
        if (seen.has(num)) {
            return false;
        } else {
            // so Set and its method .add(..) here are dedicated to
            // providing a judgement of whether each element is a duplicate?
            seen.add(num); 
            return true;
        }
    })
}

// 4. 自测：
// 4. Self-test:

console.log(uniquefilter([2, 4, 5, 5, 7, 9]));
console.log(uniquefilter([4, 3, 4, 3]));

// 3) 复杂度 | Complexity: 
// 时间：filter 也是对数组线性地操作一遍，整体O(n)
// 空间：也需要 Set 存不同元素，以及返回的新数组 O(k)，k ≤ n
// Time: filter performs one linear pass over the array → O(n) time
// Space: also needs Set for seen plus the result array: O(k)，k ≤ n

// 4) 练习 | Practice:

function uniquefilter2(nums: number[]): number[] {

    // Same as Approach 1, but the seen here is required to filter the duplicates
    const seen = new Set<number>();

        return nums.filter(num => {
            if (seen.has(num)) {
                // duplicate scaned, discard it
                return false;
            } else {
                // new element identified, keep it
                // But be careful of the order, if "return true;" is already executed
                // nothing happens within the loop that filter built;
                seen.add(num);
                return true;
            }
        })
    }

console.log(uniquefilter2([2, 4, 5, 5, 7, 9]));
console.log(uniquefilter2([4, 3, 4, 3]));
