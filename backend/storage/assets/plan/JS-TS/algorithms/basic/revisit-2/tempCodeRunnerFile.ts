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