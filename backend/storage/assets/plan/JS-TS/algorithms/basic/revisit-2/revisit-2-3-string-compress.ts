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
// and try to finish in a single pass if possible.

// 方法一：双指针压缩
// Approach 1: two-pointers compression

// 1) 思路 | Idea: 
// 用两个下标 i 、 j ，可以表示一段相同字符的起点和终点 [i, j]
// 数出长度，然后把这一段压缩成 字符 + 次数 ，写入结果数组
// Use two indices i and j to represent the start and end 
// of a run of identical characters [i, j].
// Count its length, then compress this as "char + count" to the result array


// 2) 步骤 | Steps:

// 1. 创建空数组 res 保存压缩后的个端字符串片段；
// 1. Create an empty array res to store compressed string snippets.

function CompressString(s: string): string {

    const res: string[] = [];

// 2. 令 i = 0 ，表示当前这一段的起始位置; i < s.length 时循环：
// 2. Set i = 0, which represents where the current run starts. While i < s.length,
// it gives a loop:

    let i = 0;

    while (i < s.length) {

// 2.1 取当前字符: curr = s[i]
// 2.1 Take current character: curr = s[i]

        let curr = s[i]!;

// 2.2 令 j = i + 1，count = 1 ，向右移动 j (想一想字符串) 
// ；只要 s[j] === curr, 就 count++, j++
// 2.2 Set j = i + 1, count 1, move j right (imagine the string);
// as s[j] === curr, count++, j++

        let j = i + 1;
        let count = 1;

// 2.3 一旦遇到不同字符或到达末尾，说明 [i, j] 是一整段相同字符：
// 2.3 Once a different char or end is reached, 
// it suggests that [i, j] is one full run of chars.
// 2.3.1 若 count > 1，向 res 推入 curr + String(count); 否则只推入 curr 本身。
// 2.3.1 Push curr + String(count) into res if count > 1; else, push just curr itself.
        
        while (j < s.length && s[j] === curr) {
            count ++;
            j ++;
        }

        count > 1 ? res.push(curr + String(count)) : res. push(curr);

// 2.3.2 把 i 更新为 j，开始处理下一段
// 2.3.2 Update i = j and start process the next run.

        i = j;

    }

// 3. 循环后，将 res 里所有片段拼接成字符串返回
// 3. After the loop, join all snippets inside res into a string.

return res.join('');

}

// 4. 自测
// 4. Self-test

console.log(CompressString('aaaavsswwwqqqa'));
console.log(CompressString('sssswsssss'));

// 3) 复杂度 | Complexity:
// Only one pass over the string: 时间 O(n)，得结果的额外空间 O(n)。
// 只过一遍字符串：extra space O(n) for the result.

// 4) 练习 | Practice:

function CompressString2(s: string): string {
    
    // This will give the result as a string array.
    const res: string[] = [];
    
    let i = 0;

    // Here's a loop to determine where the first char is
    // e.g., aaa bbb ccc (first a, b and c)
    while (i < s.length) {
        
        // We need the first char to assist the second loop: s[i] is the same char.
        let first = s[i]!;
        // j must be iterable numerically at each run
        let j = i + 1;
        // the first one has already got one count, so:
        let count = 1;

        while(j < s.length && first === s[j]) {
            // Double incrementations signal the same char added
            count++
            j++
        }

        // It will give a combination of "char + number", 
        // as a string array
        count > 1 ? res.push(first + String(count)) : res.push(first)

        // Set i as current j to rerun the loop until i < s.length
        i = j;
    }

return res.join('');

}

console.log(CompressString2('TTTTHHHHHIIIISSSASTRING'));
console.log(CompressString2('HereIsAString'));

// 方法二：for + 单指针 压缩
// Approach 2: for + single-pointer compression

// 1) 思路 | Idea: 
// 单个指针(下标)从左到右遍历；用变量 curr 记录“当前一段的字符”，count 记录出现次数，
// 遇到不同字符，把前一段压缩写入结果字符串
// Traverse from left to right with a single pointer (index)；keep track of 
// "the current run of snippet" using curr
// Reaching a different char, the previous run should be filled into the result string.

// 2) 步骤 | Steps:

function CompressStringSingle(s: string): string {

// 1. 特判：如果字符串长度为1，可以按需返回（当前代码返回空串）；
// 1. Edge case: return is available as needed, if the string has a length of 1
// (return an empty string for the current code);

    if (s.length === 1) return '';

// 2. 初始化：
// res = '' 可以储存最终结果；
// curr = s[0], count = 1，表示当前的那一段字符及其次数
// 2. Initialize: 
// res = '' to store the final result.
// curr = s[0], count = 1, which represents the run of a string and its count(s)

    let res: string = '';
    let curr = s[0]!;
    let count = 1;

// 3. 以 for (i = 1; i < s.length; i++) 从第二个字符开始遍历：
// 3. Start traversing from the second char with for (i = 1; i < s.length; i++):

    for (let i = 1; i < s.length; i++) {

// 3.1 若 s[i] === curr，说明仍在同一段内，count++
// 3.1 It suggests that still in the same run and count ++, if s[i] === curr

        if (s[i] === curr) {
            count++;

// 3.2 不然就是当前段结束：
// 3.2.1 把这段追加进  res: count > 1 ? curr + String(count) : curr
// 3.2.2 更新 curr = s[i] 并 重设 count = 1

// 3.2 Otherwise it is that the current run ends:
// 3.2.1 Append this to res: count > 1 ? curr + String(count) : curr
// 3.2.2 Update curr = s[i] and reset count = 1

        } else {
            res += count > 1 ? curr + String(count) : curr;
            curr = s[i]!; 
            count = 1;
        } 

    }

// 4. 循环后，最后一段还没写入，需要再把 curr 和 count 按同样规则追加进 res，再返回
// 4. After the loop, the last run hasn't been written in; 
// append it to res the same way as what we did, then return it.

res += count > 1? curr + String(count) : curr;

return res;

}

// 5. 自测:
// 5. Self-test:

console.log(CompressStringSingle('Thisisanotherstring'));
console.log(CompressStringSingle('Stttring'));

// 3) 练习 | Practice:

function CompressStringSingle2(s: string): string {

    if (s.length === 0) {
        return '';
    }

    // The result for final string.
    let res: string = '';
    // The first char of the string s.
    let first = s[0]!;
    // Since the loop gonna start from index 1, then
    let count = 1;

    for (let i = 1; i < s.length; i++) {
        if (first === s[i]) {
            count++;
        } else {
            // joins the first char with String(count) if count > 1, 
            // then reset the count to 1, and first to s[i] and go ahead to next run
            res += count > 1 ? first + String(count) : first;
            count = 1;
            first = s[i]!;
        }
    }

// The last loop skips the else, so we got to attach "res+ =...." at the end 
// before returning the res
res += count > 1 ? first + String(count) : first;

return res;

}

console.log(CompressStringSingle2('Thisisanotherstring'));
console.log(CompressStringSingle2('Stttring'));
