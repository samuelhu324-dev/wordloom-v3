// 题 5：第一个不重复的字符（Map）
// Problem 5: First unique character (Map)

// 给定字符串 s，找到第一个在字符串中只出现一次的字符，返回它的下标；如果不存在，返回 -1。
// Given a string s, find the first character that appears only once in the string
// and return its index; if it does not exist, return -1.

// 1. 第一次遍历：统计频次
// 1. First pass: count frequencies

function firstUniqChar(s: string): number {

    const freq = new Map<string, number>();

// Q2 - (freq.get(char) ?? 0) +1  vs freq.get(char) ?? 0 + 1;
// A2 - This is a question of operator's priority:
// + is higher than ??; so freq.get(char) ?? 0 + 1 = freq.get(char) ?? (0 + 1);
// and count will remain 0.

    for (const char of s) {
        freq.set(char, (freq.get(char) ?? 0) + 1);
    };

// Q&A1 - Be careful of the type number of a string.

// 2. 第二次遍历：找第一个频次为 1 的字符;
// 2. Second pass: find the first character whose frequency is 1;

    for (let i = 0; i < s.length; i++) {
        if (freq.get(s[i]!) === 1 ) {
            return i;
        }
    }
    return -1;
}

// self-test
console.log(firstUniqChar('leetcode'));     // 0
console.log(firstUniqChar('loveleetcode')); // 2
console.log(firstUniqChar('aabb'));         // -1