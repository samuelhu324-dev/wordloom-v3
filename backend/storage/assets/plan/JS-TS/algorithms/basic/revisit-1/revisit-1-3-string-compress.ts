// 题 3：压缩字符串
// Problem 3: String Compression

// Approach 1: two-pointers

// 给定一个只包含小写字母的字符串 s，把连续相同字符压缩成“字符 + 次数”。
// 当次数为 1 时，可以省略次数，只保留这个字符本身。
// Given a string s that contains only lowercase letters, compress consecutive
// identical characters into "character + count".
// When the count is 1, you can omit the count and keep only the character itself.

function compressString(s: string): string[] {

// Q1 - const result = [] vs (with a type annotation) const result: string[] = [];
// A1 - TS will treat it as any[] in the former case, Later, since you only push strings into it, 
// TS will infer that result is actually a string[];

    const res: string[] = [];
    let i = 0;

    while (i < s.length) {

// Q2 - let curr = s[i]; vs const curr = s[i]; what's the difference?
// A2 - Nothing different here.

        const curr = s[i];

// Q3 - let j = i + 1; vs let j = 1;
// A3 - the latter will cause dead loop, 
// since it won't move on to a different character (let's say: from aaa to b... )

        let j = i + 1;
        let count = 1;

        while (j < s.length && s[j] === curr) {
            count ++;
            j ++;
        }

        if (count > 1) {
            res.push(curr + String(count));
        } else {
            res.push(curr!);
        }
    i = j;

    } 
    return res
}
    
// Input:  "aaabbc"
// Output: "a3b2c"
// Input:  "abcd"
// Output: "abcd" (because there are no consecutive repeats)
// Input:  "aabcccccaaa"
// Output: "a2bc5a3"

console.log(compressString("aaabbc"));
console.log(compressString("abcd"));
console.log(compressString("aabcccccaaa"));

// Approach 2: for + single pointer

function compressString2(s: string): string {
    if (s.length === 1) return "";
    
    let res = '';
    let i = 0
    let curr = s[0];
    let count = 1;

    for (i = 1; i < s.length; i++) {
        if (curr === s[i]) {
            count++
        } else {
            res += count > 1 ? curr + String(count) : curr;
            curr = s[i];
            count = 1;
        }
    }
    res += count > 1 ? curr + String(count) : curr;
    return res;
    
}

// self-test:

console.log(compressString2("aaabbc"));
console.log(compressString2("abcd"));
console.log(compressString2("aabcccccaaa"));