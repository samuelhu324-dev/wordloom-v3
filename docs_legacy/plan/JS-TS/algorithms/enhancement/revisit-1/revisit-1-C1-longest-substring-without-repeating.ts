// C1. 最长无重复子串长度（字符串 + 滑动窗口 + Set/Map）
// C1. Length of the longest substring without repeating characters (string + sliding window + Set/Map)

// 给定一个字符串 s，请返回其中不包含重复字符的最长子串的长度。
// Given a string s, return the length of the longest substring 
// without repeating characters.

// 示例：
// 输入："abcabcbb" → 输出 3（最长无重复子串是 "abc"）
// 输入："bbbbb"    → 输出 1（最长无重复子串是 "b"）
// Examples:
// Input: "abcabcbb" → Output: 3 (the longest substring is "abc")
// Input: "bbbbb"    → Output: 1 (the longest substring is "b")

// -----------------------------------------------------------------------------
// 1) 核心思路 / Core idea:
// -----------------------------------------------------------------------------
//
// 1. 用两个指针 left 和 right 表示当前窗口 [left, right]，保证窗口内没有重复字符 
// 1. Use two pointers left and right to represent a window [left, right] 
//    and keep it free of duplicate characters
// 2. 用 Set<char> 来记录当前窗口里有哪些字符
// 2. Use a Set<char> to record which characters are currently inside the window
// 3. right 从左到右逐个扫描字符；遇到重复字符时，通过移动 left 缩小窗口，直到重复
//    字符被移出窗口
// 3. right scans the string from left to right one after another. When we meet a
//    duplicate character, we shrink the window via moving left forward
//    until repreated character is removed from the window
// 
// -----------------------------------------------------------------------------
// 2) 详细步骤 / Detailed Steps:
// -----------------------------------------------------------------------------
// 

function longestSubstringUsingSet(s: string): string {
    
// 1. 初始化:
//    - seen = new Set<string>(): 窗口内的字符集合
//    - left = 0: 窗口左边界
//    - bestStart = 0：当前“最长子串”的起点
//    - maxLen = 0：当前“最长子串”的长度
//  1. Initialize：
//    - seen = new Set<string>(): the Set of characters within the window
//    - left = 0: left boundary of the window
//    - bestStart = 0: the current start of "the longest string"
//    - maxLen = 0: the current length of "the longest string"

    const seen = new Set<string>();

    let left = 0;
    let bestStart = 0;
    let maxLen = 0;

    for (let right = 0; right < s.length; right++) {

// 2. 遍历 right 从 0 到 s.length - 1：
//    - 当前字符 ch = s[right]
//    - 如果 ch 已经在 seen 里，就说明 ch 在当前窗口 [left, right - 1] 出现过
//      那么把 left 往前移, 并把 s[left] 从 seen 中删掉，直到窗口中不再包含 ch
//
// 2. Traverse right from 0 to s.length - 1:
//    - Current character ch = s[right]
//    - If seen already contains ch, 
//      that means ch has appeared in the current window [left, right - 1]
//      so move left forward and delete s[left] from seen 
//      until the window no longer contains ch.

        const ch = s[right]!;
        while (seen.has(ch)) {
            seen.delete(s[left]!);
            left++;
        }

// 3. 现在窗口 [left, right - 1] 中已经没有 ch ，可以安全地把 ch 加进窗口：
// 3. Now the window [left, right - 1] doesn't contain ch already, safely adding
//    ch to the window:

        seen.add(ch);

// 4. 窗口长度为 winLen = right - left + 1。如果 winLen > maxLen，更新答案：
// 4. Window length is winLen = right - left + 1. 
//    If winLen > maxLen, update the answer:

        const winLen = right - left + 1;

            if (winLen > maxLen) {
                maxLen = winLen;
                bestStart = left;
            }
    }

    return s.slice(bestStart, bestStart + maxLen);

}

// 5. 自测
// 5. Self-test

console.log(longestSubstringUsingSet('abcabcbb'));
console.log(longestSubstringUsingSet('bbbbb'));

//
// -----------------------------------------------------------------------------
// 3) 正确性直觉 / Intuition for correctness:
// -----------------------------------------------------------------------------
//
// 1. seen 始终对应窗口 [left, right] 内的字符，所以循环不变量是：
//    “窗口中不含重复字符”
// 2. right 每次迭代向右走一步；left 也只向右移动，不会回头
//    → 每个字符至多进窗口一次、出窗口一次 → 整体时间是 O(n)
// 1. seen always reflects the characters inside [left, right], so the loop
//    variant is: "the window contains no duplicates".
// 2. right moves right one step each iteration; 
//    left only moves right as well and will not look back
//    → Each character enters and leaves the window at most once 
//    → overall time is O(n)
//
// -----------------------------------------------------------------------------
// 4) 复杂度 / Complexity:
// -----------------------------------------------------------------------------
// 
// 1. 时间: O(n)，其中 n = s.length
// 2. 空间：O(k)，k 为窗口中不同字符个数，最多 O(字符集大小)
// 1. Time: O(n), where n = s.length
// 2. Space: O(k), where k is the number of distinct chars in the window
//    (at most bounded by the character set)

//
// -----------------------------------------------------------------------------
// 5) Map 版本 / Map versions:
// -----------------------------------------------------------------------------
// 

function longestSubstringUsingMap(s: string): number {

    // the last position where the character has appeared
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

console.log(longestSubstringUsingMap('abcabcbb'));
console.log(longestSubstringUsingMap('bbbbb'));

//
// -----------------------------------------------------------------------------
// 5) 练习 / Practice:
// -----------------------------------------------------------------------------
// 

//
// -----------------------------------------------------------------------------
// 1. Set 版 / Set version
// -----------------------------------------------------------------------------
//

function longestSubstringUsingSet2(s: string): string[] {
    
    // each character seen is stored in a Set
    const seen = new Set<string>;
    const results: string[] = [];
    let left = 0;
    let maxLen = 0;

    for (let right = 0; right < s.length; right++) {

        const ch = s[right]!;

        while (seen.has(ch)) {
            seen.delete(s[left]!);
            left++
        }

        seen.add(ch);

        const winLen = right - left + 1;
        if (winLen > maxLen) {
            maxLen = winLen;
            results.length = 0;
            results.push(s.slice(left, right + 1));
        } else if (winLen === maxLen) {
            results.push(s.slice(left, right + 1));
        }
    }

    return results;
    
}

console.log(longestSubstringUsingSet2('abcabcaw'));
console.log(longestSubstringUsingSet2('abcba'));
console.log(longestSubstringUsingSet2('abbbbb'));


//
// -----------------------------------------------------------------------------
// 2. Map 版 / Map version
// -----------------------------------------------------------------------------
//

function longestSubstringUsingMap2(s: string): string[] {

    // key: character; value: its last index
    const lastIndex = new Map<string, number>();
    const results: string[] = [];
    let left = 0;
    let maxLen = 0;

    for (let right = 0; right < s.length; right++) {

        const ch = s[right]!;

        // only responsible for computation of winLen with left
        if (lastIndex.has(ch)) {
            const prev = lastIndex.get(ch)!
            left = Math.max(left, prev + 1);
        } 

        // if nothing inside the Map, set it
        // if something inside the Map, overwrite it
        lastIndex.set(ch, right);

        const winLen = right - left + 1;

        if (maxLen < winLen) {
            maxLen = winLen;
            results.length = 0;
            results.push(s.slice(left, right + 1));
        } else if (maxLen === winLen) {
            results.push(s.slice(left, right + 1));
        }
    }
    
    return results;

}

console.log(longestSubstringUsingMap2('abcabcaw'));
console.log(longestSubstringUsingMap2('abcba'));
console.log(longestSubstringUsingMap2('abbbbb'));
