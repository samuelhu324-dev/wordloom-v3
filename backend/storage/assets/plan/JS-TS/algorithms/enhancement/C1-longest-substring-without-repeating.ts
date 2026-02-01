// C1. 最长无重复子串长度（字符串 + 滑动窗口 + Set/Map）
// C1. Length of the longest substring without repeating characters (string + sliding window + Set/Map)

// 给定一个字符串 s，请返回其中不包含重复字符的最长子串的长度。

// Given a string s, return the length of the longest substring without repeating characters.

// 示例：
// 输入："abcabcbb" → 输出 3（最长无重复子串是 "abc"）
// 输入："bbbbb"    → 输出 1（最长无重复子串是 "b"）
// Examples:
// Input: "abcabcbb" → Output: 3 (the longest substring is "abc")
// Input: "bbbbb"    → Output: 1 (the longest substring is "b")

// -----------------------------------------------------------------------------
// 1) classic version: tie‑break by earliest start using Set
// -----------------------------------------------------------------------------

function longestSubstringWithoutRepeating(s: string): string {

    const seen = new Set<string>();

    let left = 0;
    let bestStart = 0;
    let maxLen = 0;

    for (let right = 0; right < s.length; right++) {
        const ch = s[right]!;

        while (seen.has(ch)) {
            seen.delete(s[left]!);
            left++;
        }

        seen.add(ch);

        const winLen = right - left + 1;
        if (winLen > maxLen) {
            maxLen = winLen;
            bestStart = left;
        }
    }

return s.slice(bestStart, bestStart + maxLen);

}

console.log(longestSubstringWithoutRepeating("abcabcbb")); // "abc"
console.log(longestSubstringWithoutRepeating("bbbbb"));    // "b"

// -----------------------------------------------------------------------------
// 2) classic version: tie‑break by earliest start using Map
// -----------------------------------------------------------------------------

function longestSubstringUsingMap(s: string): number {
    const lastIndex = new Map<string, number>();
    let left = 0;
    let maxLen = 0;

    for (let right = 0; right < s.length; right++) {
        const ch = s[right]!;

        if (lastIndex.has(ch)) {
            const prev = lastIndex.get(ch)!;
            left = Math.max(left, prev + 1);
        }

        lastIndex.set(ch, right);

        const winLen = right - left + 1;
        if (winLen > maxLen) {
            maxLen = winLen;
        }
    }

    return maxLen;
}

console.log(longestSubstringUsingMap("abcabcbb")); // "abc"
console.log(longestSubstringUsingMap("bbbbb"));    // "b"

// -----------------------------------------------------------------------------
// 3) no tie-break: return all longest Substrings (or its counts) if necessary
// -----------------------------------------------------------------------------

// string version:

function allLongestSubstringsWithoutRepeating(s: string): string[] {

    const seen = new Set<string>();
    let left = 0;
    
    let maxLen = 0;
    const results: string[] = [];

    for (let right = 0; right < s.length; right++) {
        
        const ch = s[right]!;
        while (seen.has(ch)) {
            left++;
            seen.delete(ch);
        }

        seen.add(ch);

        const winLen = right - left + 1;
        if (winLen > maxLen) {
            maxLen = winLen;
            // empty the results for new element(s)
            results.length = 0;
            results.push(s.slice(left, right + 1));
        } else if (winLen === maxLen) {
            results.push(s.slice(left, right + 1));
        }
    }
     return results;
}

console.log(allLongestSubstringsWithoutRepeating("abcabcbb")); // ["abc", "bca", "cab"]
console.log(allLongestSubstringsWithoutRepeating("bbbbb"));    // "b"
console.log(allLongestSubstringsWithoutRepeating("abcdefg"));    // "b"

// count version:

function allLongestSubstringsWithoutRepeating2(s: string): number {

    const seen = new Set<string>();
    let left = 0;
    
    let maxLen = 0;
    let counts = 0;

    for (let right = 0; right < s.length; right++) {
        
        const ch = s[right]!;
        while (seen.has(ch)) {
            left++;
            seen.delete(ch);
        }

        seen.add(ch);

        const winLen = right - left + 1;
        if (winLen > maxLen) {
            maxLen = winLen;
            // empty the results for new element(s)
            counts = 0;
            counts++;
        } else if (winLen === maxLen) {
            counts++;
        }
    }
     return counts;
}

console.log(allLongestSubstringsWithoutRepeating2("abcabcbb")); // ["abc", "bca", "cab"]
console.log(allLongestSubstringsWithoutRepeating2("bbbbb"));    // "b"
console.log(allLongestSubstringsWithoutRepeating2("abcdefg"));    // "b"