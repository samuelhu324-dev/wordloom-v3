// C2. First unique character in a string (Map)
// C2. 字符串中的第一个不重复字符（Map）

// Given a string s, find the first character that appears exactly once
// and return its index. If no such character exists, return -1.
// 给定字符串 s，找到第一个在字符串中只出现一次的字符，返回它的下标；如果不存在，返回 -1。

// -----------------------------------------------------------------------------
// 1) First Unique Character
// -----------------------------------------------------------------------------

function firstUniqueChar(s: string): number {
    // key: character; value: its frequency
    const indexMap = new Map<string,number>();
    
    for (let i = 0; i < s.length; i++) {
        const ch = s[i]!;
        indexMap.set(ch, (indexMap.get(ch) ?? 0) + 1);
    }

    for (let j = 0; j < s.length; j++) {
        const ch = s[j]!;
        if (indexMap.get(ch) === 1) return j;
    }

    return -1;
}

console.log(firstUniqueChar('string')); // s => 0
console.log(firstUniqueChar('TTwo'));   // w => 2
console.log(firstUniqueChar(''));  // -1 

// -----------------------------------------------------------------------------
// 2) Second Unique Character
// -----------------------------------------------------------------------------

function SecondtUniqueChar(s: string): number {
    // key: character; value: its frequency
    const indexMap = new Map<string,number>();
    let count = 0;
    
    for (let i = 0; i < s.length; i++) {
        const ch = s[i]!;
        indexMap.set(ch, (indexMap.get(ch) ?? 0) + 1);
    }

    for (let j = 0; j < s.length; j++) {
        const ch = s[j]!;
        if (indexMap.get(ch) === 1 && count === 0) {
            count++;
        } else if (indexMap.get(ch) === 1 && count === 1) {
            return j;
        }
    }

    return -1;
}

console.log(SecondtUniqueChar('string')); // t => 1
console.log(SecondtUniqueChar('TTwo'));   // o => 3
console.log(SecondtUniqueChar(''));  // -1 