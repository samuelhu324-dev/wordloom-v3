// C1. Length of the longest substring without repeating characters 
// (string + sliding window + Set/Map)
// C1. 最长无重复子串长度（字符串 + 滑动窗口 + Set/Map）

// Given a string s, return the length of the longest substring 
// without repeating characters.
// 给定一个字符串 s，请返回其中不包含重复字符的最长子串的长度。

// Examples:
// Input: "abcabcbb" → Output: 3 (the longest substring is "abc")
// Input: "bbbbb"    → Output: 1 (the longest substring is "b")
// 示例：
// 输入："abcabcbb" → 输出 3（最长无重复子串是 "abc"）
// 输入："bbbbb"    → 输出 1（最长无重复子串是 "b"）

// -----------------------------------------------------------------------------
// 1) classic version: tie‑break by earliest start using Set (string)
// -----------------------------------------------------------------------------

function longestSubstringWithoutRepeating(s: string): string {
    
    if (s.length === 0) return '';
    const seen = new Set<string>();

    let left = 0;
    let maxLen = 0;
    let maxStart = 0;

    for (let right = 0; right < s.length; right++) {
        
        const ch = s[right]!;

        while (seen.has(ch)) {
            seen.delete(s[left]!);
            left++;
        }

        seen.add(ch);

        const currLen = right - left + 1;
        if (currLen > maxLen) {
            maxLen = currLen;
            maxStart = left;
        }
    }

    return s.slice(maxStart, maxStart + maxLen);
}

console.log(longestSubstringWithoutRepeating("abcabcbb")); // "abc"
console.log(longestSubstringWithoutRepeating("bbbbb"));    // "b"

// -----------------------------------------------------------------------------
// 2) classic version: tie‑break by earliest start using Map (length)
// -----------------------------------------------------------------------------

function longestSubstringUsingMap(s: string): number {
    
    if (s.length === 0) return 0;
    
    const lastIndex = new Map<string,number>();
    
    let left = 0;
    let maxLen = 0;

    for (let right = 0; right < s.length; right++) {

        const ch = s[right]!;

        if (lastIndex.has(ch)) {
            const prev = lastIndex.get(ch)!;
            // 1. for current subarray without duplicate at least with left as its start
            // 2. prev + 1 guarantees that new subarray moves forward + 1
            left = Math.max(left, prev + 1);
        }

        lastIndex.set(ch, right);

        const currLen = right - left + 1;
        if (currLen > maxLen) {
            maxLen = currLen;
        }
    }
    return maxLen;

}

console.log(longestSubstringUsingMap("abcabcbb")); // "abc" 3
console.log(longestSubstringUsingMap("bbbbb"));    // "b" 1

// -----------------------------------------------------------------------------
// 3) no tie-break: return all longest Substrings (or its counts) if necessary
// -----------------------------------------------------------------------------

// string[] version:

function allLongestSubstringsWithoutRepeating(s: string): string[] {

    if (s.length === 0) return [];
    const seen = new Set<string>();
    const results: string[] = [];

    let left = 0;
    let maxLen = 0;

    for (let right = 0; right < s.length; right++) {
        const ch = s[right]!;

        while (seen.has(ch)) {
            seen.delete(s[left]!);
            left++;
        }

        seen.add(ch);

        const currLen = right - left + 1;
        if (currLen > maxLen) {
            maxLen = currLen;
            // empty the results with same length
            results.length = 0;
            results.push(s.slice(left, right + 1));
        } else if (currLen === maxLen) { // results with same length
            results.push(s.slice(left, right + 1));
        }
    }
    return results;

}

console.log(allLongestSubstringsWithoutRepeating("abcabcbb")); // 
console.log(allLongestSubstringsWithoutRepeating("bbbbb"));    // 
console.log(allLongestSubstringsWithoutRepeating("abcdefg"));    // "

// count version:

function allLongestSubstringsCount(s: string): number {
    
    if (s.length === 0) return 0;

    const lastIndex = new Map<string,number>();
    
    let left = 0;
    let maxLen = 0;
    let count = 0;

    for (let right = 0; right < s.length; right++) {
        
        const ch = s[right]!;

        // use the old window's position to tell
        // if there are any dupliates if new character is added into the subarray
        // if yes, shrink the left:  
        if (lastIndex.has(ch)) {
            const prev = lastIndex.get(ch)!;
            left = Math.max(left, prev + 1);
        }

        lastIndex.set(ch, right);

        const currLen = right - left + 1;
        if (currLen > maxLen) {
            maxLen = currLen;
            // just one case
            count = 0;
            count++;
        } else if (currLen === maxLen) { // multi-cases
            count++;
        }
    }
    return count;
}

console.log(allLongestSubstringsCount("abcabcbb")); //
console.log(allLongestSubstringsCount("bbbbb"));    // 
console.log(allLongestSubstringsCount("abcdefg"));    // 