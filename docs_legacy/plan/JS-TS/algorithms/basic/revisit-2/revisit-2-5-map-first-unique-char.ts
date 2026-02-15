// 题 5：第一个不重复的字符（Map）
// Problem 5: First unique character (Map)

// 给定字符串 s，找到第一个在字符串中只出现一次的字符，返回它的下标；如果不存在，返回 -1。
// Given a string s, find the first character that appears only once in the string
// and return its index; if it does not exist, return -1.

// 1) 思路 | Idea:
// 目标：求字符串中恰好出现一次的字符的下标；没有就返回 - 1；
// Goal: Find the index of first char that appears exactly once in the string;
// if none, return -1.

// 2) 方法 | Approach:
// 1. 过两遍字符串：
// Use two passes over the string:

//   1.1 第一遍：统计每个字符出现次数 
//   1.2 第二遍：按原顺序找出第一个频次为1的字符；
//   1.1 First pass: tally how many times each character appears
//   1.2 Second pass: find out the first character with freqency of 1 in original order

// 2. 使用 Map<string, number> 可以存频次：
// 2. Use a Map<string, number> to store frequencies:

//   2.1 键：字符
//   2.2 值：该字符出现次数
//   2.1 key: character - char
//   2.2 value: how many times this char appears

// 3) 步骤 | Steps:

function FirstUniChar(s: string): number {
    
// 1. 创建Map：空 Map 装 char → count
// 1. Create the Map: an empty map to hol char → count

    const freq = new Map<string, number>();

// 2. 第一遍：数出频次 
// 2. First pass: count frequencies

//   2.1 每个字符 char：取出当前次数：freq.get(char)?? 0 (没出现默认0次)
//   2.2 然后 + 1 累计：(freq.get(char) ?? 0) + 1
//   2.1 For each character char: freq.get(char)?? 0 (default to 0 if not present)
//   2.2 Then + 1 to rack up: (freq.get(char) ?? 0) + 1

    for (const char of s) {

        // Q&A1 ** const curr = freq.set(char, (freq.get(char) ?? 0) + 1); **
        // which assigns the value to a new constant curr, but we don't want to use it.
        freq.set(char, (freq.get(char) ?? 0) + 1);

    }

// 3. 第二遍：求第一个只出现一次的字符
// 3. Second pass: find the first char that appears just once:

//   3.1 从左到右用下标 i 扫描字符串 s  
//   3.2 当前字符 s[i]: 如果 freq.get(s[i]) === 1 ，该字符就唯一 → 立即返回 i；
//   3.1 Scan string s from left to right with index i
//   3.2 For current character s[i]:
//   If freq.get(s[i]) === 1, this character is unique → return i immediately.

    for (let i = 0; i < s.length; i++) {

        if (freq.get(s[i]!) === 1) return i;
    }

// 4. 如果扫完求不出：说明没有任何字符只出现一次，并返回 -1
// 4. If finished without finding one: 
// which suggests no char appears just once, and return -1.

return -1;

}

// 5. 自测：
// 5. Self-test:

console.log(FirstUniChar('loveproblem'));
console.log(FirstUniChar('pppproblem'));

// 3) 练习 | Practice:

function FirstUniChar2(s: string): number {

    // shows the frequency with a specific character as a key (string)
    // and a specific count as a value (number) 
    let freq = new Map<string, number>();

    for (const char of s) {

        // Sets a pair of value and key in order to give a second pass 
        // for the first char that appears once in the string.

        // Q&A2 *** freq = freq.set(char, (freq.get(char) ?? 0) + 1 ); ***
        // which refers to the same Map
        freq.set(char, (freq.get(char) ?? 0) + 1 );
    }

    for (let i = 0; i < s.length; i++) {

        // to ensure which char that has just one count for the first time.
        if (freq.get(s[i]!) === 1) return i;
    }

return -1;

}

console.log(FirstUniChar2('loveproblem'));
console.log(FirstUniChar2('pppproblem'));
