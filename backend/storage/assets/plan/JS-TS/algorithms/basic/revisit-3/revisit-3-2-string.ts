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

function validPalindrome(s: string): boolean {
    
    let left = 0;
    let right = s.length - 1;

    while (left < right) {
        if (s[left] === s[right]) {
            left++;
            right--
        } else {
            return isPalindromeInRange(left+1, right, s)
            || isPalindromeInRange(left, right-1, s);
        }
    }

    return true;
}

function isPalindromeInRange(left: number, right: number, s: string): boolean {
    while (left < right) {
        if (s[left] === s[right]) {
            left++
            right--
        } else {
            return false;
        }
    };

    return true;

}

console.log(validPalindrome('ThisIsAString'));
console.log(validPalindrome('abba'));
console.log(validPalindrome('acbba'));
console.log(validPalindrome('abbca'));

// 题 3：压缩字符串
// Problem 3: String Compression

// 给定一个只包含小写字母的字符串 s，把每一轮的连续相同字符压缩成
// “字符 + 次数”，次数为 1 时可以省略。
// Given a string s that contains only lowercase letters,
// compress every run of consecutive identical characters into
// "character + count"; it can be omitted, when the count is 1.

// - "aaabbc" → "a3b2c"
// - "abcd" → "abcd"。

//  - 要求：返回新字符串，不原地修改；尽量就一次遍历完成。
//  - Requirement: return a new string (do not modify in place),
//    and try to finish in a single pass if possible.

//
// -----------------------------------------------------------------------------
// 1) 双指针压缩
// 1) two-pointers compression
// -----------------------------------------------------------------------------
//

function stringCompress(s: string): string{

    if (s.length === 0) return '';

    const res: string[] = [];
    const n  = s.length;
    let i = 0;

    while (i < n) {
        const curr = s[i]!;
        let j = i + 1;

        while (j < n && s[j] === curr) {
            j++
        }

        const count = j - i;
        if (count > 1) {
            res.push(curr + String(count));
        } else {
            res.push(curr);
        }

        i = j;
    }

    return res.join('');
}

console.log(stringCompress("aabbccaad"));

// -----------------------------------------------------------------------------
// 1. 练习 / Practice: 
// -----------------------------------------------------------------------------

function stringCompressTwoPointers(s: string): string {

    let i = 0;
    const res: string[] = [];

    while (i < s.length) {

        let curr = s[i]!;
        let j = i + 1;

        while (curr === s[j]! && j < s.length) {
            j++;
        }

        const count = j - i;

        if (count > 1) {
            res.push(curr + String(count));
        } else {
            res.push(curr);
        }

        i = j;
    }
    return res.join('');
}

console.log(stringCompressTwoPointers('aaaabbbccca'));

//
// -----------------------------------------------------------------------------
// 2) 单指针压缩
// 2) single-pointer compression
// -----------------------------------------------------------------------------
//

function stringCompressPointer(s: string): string {

    if (s.length === 0) return '';

    let count = 1;
    let curr = s[0]!;
    let res: string = ''

    for (let i = 1; i < s.length; i++) {

        const x = s[i]!;
        if (curr === x) {
            count ++;
        } else {
            res += count > 1 ? curr + String(count) : curr;
            count = 1;
            curr = x; 
        }
    }

     res += count > 1 ? curr + String(count) : curr;
     return res; 

}

console.log(stringCompressPointer('Stttring'));
console.log(stringCompressPointer('aaaabbbccca'));
