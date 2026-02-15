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

// 方法：String + 双指针
// Approach: String + two pointers

// 1) 思路 | Idea:

// 1. 使用左右双指针从两端向中间比较字符：
// left 0 开头，right s.length - 1 开头
// 1 Compare chars using right-and-left pointers from both ends to the middle:
// left starts at 0, right starts at s.length - 1.

// 2. 如果过程中所有字符都两两相等，那本身就是回文，直接返回true；
// 2. If all chars match pairwise along the way, so it is panlidrome itself; 
// return true directly.

// 3. 关键是第一次不相等的时候的办法：
// s[left] !== s[right]的时候，你有一次删除机会，可以：
//   3.1 删掉左边这个字符：也就是跳过left，检查 [left + 1, right] 是否为回文；
//   3.2 或者删掉右边这个字符，跳过right，检查 [left, right - 1] 是否为回文；
// 3. The catch is what to do at the first mismatch:
// You have a chance to delete when s[left] !== s[right], to:
//   3.1 delete that string on the left: i.e., skip left 
//   and check whether [left + 1, right] is a palindrome
//   3.2 or delete that string on the right: skip right
//   and check whether [left + 1, right] is a palindrome

// 4. 只要两个选项有一个得到回文，就返回 true ；两个都不行，就返回 false
// 4. As long as either of the two options yields a palindrome,
// return true; if both fail, return false.

// 2) Helper | 辅助函数
// 1. isPalindromeInRange 是一个标准回文检查器：给定字符串 str 和 左右边界 [l, r]
// 判断这段子串
// 1. isPalindfomeInRange is a standard palindrome checker:
// given a string str left-right boundaries [l, r], 
// a determinator of whether this substring is a palindrome.

// 2. 内部同样使用双指针，从 l he r 向中间收缩
// 2. It also shows the use of two pointers
// shrinking from l and r toward the center
//   2.1 一直都匹配 (str[1] === str[2]) 最终返回 true
//   2.1 All pair always match (str[1] === str[2]); return true eventually
//   2.2 一有不等，就立即返回 false
//   2.2 On the first mismatch, return false immediately.

// 3. 只负责纯回文判断，不再删除字符
// 删掉字符的逻辑由外层 validPalindrome 决定传入哪一段
// 3. responsible only for the judgement of a pure palindrome and no longer delete a char
// for any logical deletion, the outer validPalindrome decide which run to pass in

// 2) 步骤 | Steps:

function validPalindrome(s: string): boolean {

// 1. 初始化 left = 0, right = s.length - 1
// 1. Initialize left = 0, right = s.length -1

    let left = 0;
    let right = s.length - 1;

    while (left < right) {

// 2. left < right 时:
// 2.1 若 s[left] === s[right]：说明当前两端匹配，向内移：
// 2.1 While left < right, which suggests the ends match, move inward: 

        if (s[left] === s[right]) {
            left++; 
            right--;

// 2.2 否则（首次不匹配）：
// 调用 isPalindromeInRange 函数，先算参数 (s, left + 1, right) 去掉左边
// 如果 false 再算参数 (s, left, right -1) 去掉右边
// 如果二者有一个返回 true，整体返回 true，否则返回 false。
// 2.2 Other (first mismatch):
// Call isPalindromeInRange function first with arguements (s, left + 1, right) to remove left
// If false, it goes with (s, left, right -1) to remove right
// If either returns true, return true entirely; else return false.

        } else {
            return isPalindromeInRange(s, left + 1, right)
            || isPalindromeInRange(s, left, right -1);
        }
    }

// 3. 如果循环顺利结束没不匹配出现，说明原串是回文，直接返回 true 
// 3. If the loop finishes successfully without mismatch
// , which suggests it's a palindrome; return true directly.

return true;

}

function isPalindromeInRange(str: string, l: number, r: number) {
    while (l < r) {
        if (str[l] === str[r]) {
            l++;
            r--;
        } else {
            return false;
        }
        
    }
    return true;
}

// 4. 自测：
// 4. Self-test:

console.log(validPalindrome('acbba'));
console.log(validPalindrome('abc'));
console.log(validPalindrome('abba'));

// 3) 复杂度 | Complexity:
// 双指针只扫一遍字符串，辅助函数在最坏情况下页只扫剩下的部分，总时间复杂度 O(n)
// 仅使用常数级额外变量，空间复杂度 O(1)
// Two pointers sweep through the string once; 
// the helper at worst only scans the remaining part
// Only constant extra variables are used, with space complexity of O(1)

// 4) 练习 | Practice:

function validPalindrome2(s: string): boolean {
    
    // Set outermost left-and-right length
    let left = 0;
    let right = s.length -1;

    // no matter ValindPalindrome or isPalindromeInRange
    // they share the same logic on iteration of 
    // left ++ and right --, while s[left] === s[right]
    // The extra layer is the deletion logic (skip left => skip right) 
    // You'll see it soon below:
    while (left < right) {
        if (s[left] === s[right]) {
            left ++;
            right --;

        } else {
            return isPalindromeInRange2(s, left + 1, right) 
            || isPalindromeInRange2(s, left, right - 1);
        }
    }
return true;
}

function isPalindromeInRange2(s: string, left: number, right: number): boolean {
    while (left < right) {
        if (s[left] === s[right]) {
            left ++;
            right --;
        } else {
            return false;
        }
        
    }
    return true;
}

console.log(validPalindrome2('acbba'));
console.log(validPalindrome2('abc'));
console.log(validPalindrome2('abba'));