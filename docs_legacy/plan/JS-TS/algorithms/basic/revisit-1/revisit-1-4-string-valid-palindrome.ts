// 题 4：判断能否通过删除一个字符变成回文（String + 双指针）
// Problem 4: Determine whether a string can become a palindrome by deleting at most one character (String + two pointers)

// 给定一个字符串 s，你可以最多删除一个字符。
// 判断剩下的字符串能否是回文（true / false）。
// Given a string s, you may delete at most one character.
// Determine whether the remaining string can be a palindrome (true / false).

// 示例：
//   输入："abca"  → 可以删掉 'b' 或 'c'，变成 "aca" 或 "aba"，返回 true
//   输入："abc"   → 无论删谁都不是回文，返回 false
// Examples:
//   Input: "abca"  → you can delete 'b' or 'c' to get "aca" or "aba", return true
//   Input: "abc"   → no matter which character you delete, it can’t form a palindrome, return false

// 要求：
//   1. 实现函数 validPalindrome(s: string): boolean
//   2. 尽量使用双指针（left / right），时间复杂度 O(n)
//   3. 只需要考虑普通字符串，大小写敏感与否你可以自行约定（先简单按“完全相等”处理）
// Requirements:
//   1. Implement the function validPalindrome(s: string): boolean
//   2. Try to use the two-pointer technique (left / right), with time complexity O(n)
//   3. Only consider normal strings; whether it is case-sensitive is up to you
//      (for now, just treat characters as “exactly equal”)

// 题 4：判断能否通过删除一个字符变成回文
// Problem 4: Determine whether a string can become a palindrome 
// by deleting one character

// 方法一：String + 双指针
// Approach 1: String + two pointers

function validPalindrome(s: string): boolean {
    let left = 0;
    let right = s.length - 1;

// 1. 全程匹配，直接是回文
// 1. If all characters match throughout, it is a palindrome directly 

    while (left < right) {
        if (s[left] === s[right]) {
            left ++;
            right --;
        } else {
            return isPalidromeInRange(left+1, right, s) 
            || isPalidromeInRange(left, right-1, s);
        }
    }
    return true;
}

// 2. 出现不匹配时，尝试跳过左指针或右指针
// 2. When a mismatch occurs, try skipping either the left pointer or the right pointer

function isPalidromeInRange(l: number, r: number, str: string): boolean {
    while (l < r) {
    if (str[l] === str[r]) {
        l ++;
        r --;
    } else {
        return false;
    }
  } 
return true;
}

// 3. 自测
// 3. self-test

console.log(validPalindrome('abca')); // true
console.log(validPalindrome('abc'));  // false
console.log(validPalindrome('abba')); // true
console.log(validPalindrome('a'));    // true
console.log(validPalindrome(''));     // 这里我们约定空串也算回文，所以 true

