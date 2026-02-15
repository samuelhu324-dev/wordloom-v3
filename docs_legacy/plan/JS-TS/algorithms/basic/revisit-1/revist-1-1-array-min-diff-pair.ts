// 题 1：最小差值对

// 方法一：排序 + 遍历相邻元素
// Approach 1: Sort + scan adjacent elements

// 描述：给定一个包含 n 个整数的数组，找出其中差值最小的一对数，返回它们的差值。
// Description: Given an array of n integers, find the pair of numbers 
// with the smallest difference and return that difference.

// 例如，输入数组 [3, 8, 2]，差值最小的一对数是 (2, 3)，它们的差值为 1。
// For example, for the input array [3, 8, 2], the pair with the smallest difference is (2, 3),
// and their difference is 1.

  function MinDiff(nums: number[]): number {

// 1. 少于 2 个数没法组成一对
// 1. With fewer than 2 numbers, a pair cannot be formed.

    if (nums.length < 2) {
        throw new Error('no less than two numbers')
    }
  
// 2. 浅拷贝一份并从小到大排序（不改原数组） 
// 2. Make a shallow copy of the array and sort it in ascending order 
// (without modifying the original array).

// Q1 - What'll happen without shallow-copying it.
// A1 - Other orders related to nums will be affected.
// say - const arr = nums.sort((a, b) => a - b); 
    
    const arr = [...nums].sort((a, b) => a - b); 

// Q2 - Why (a, b)?
// A2 - (a, b) => a - b is a ComapreFunction:
// function compare(a: number, b: number) {
// return a - b;
// }
// 返回 < 0：a 在前
// // If the return value is < 0: a comes before b.
// 返回 > 0：b 在前
// > 0: b comes before a.\
// 返回 0：位置不变
// 0: no changes of where they are.

// 3. 初始化答案为一个很大的数
// 3. Initialize the answer as a very large number.

    let ans = Infinity; // 4. const vs. let

// 4. 遍历排序后的数组，计算相邻元素的差值
// 4. Traverse the sorted array and compute the difference 
// between each pair of adjacent elements.

        for (let i = 1; i < arr.length ; i++) {   

// Q3 - for of ... vs for?
// A3 - 1. traditional for:  compare the current with the previous by getting index(i)
//    - 2. for ... of: get value directly but no maintenance of indices

            const cur = arr[i];
            const pre = arr[i-1];
            const diff = cur! - pre!;
            if (diff < ans) {
                ans = diff;  

// Q&A4 - It is a fixed value if using const before 
            }
        
        }
   return ans;  

// Q&A5 - Be careful of where return is located!
  }


// 5. self-test:

console.log(MinDiff([2, 4, 5, 6]));
console.log(MinDiff([2, 5, 7]));
