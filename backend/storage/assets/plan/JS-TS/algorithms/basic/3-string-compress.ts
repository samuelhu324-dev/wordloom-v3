// 题 3：压缩字符串（String）
// 给定一个只包含小写字母的字符串 s，把连续相同字符压缩成“字符 + 次数”。
// 当次数为 1 时，可以省略次数，只保留这个字符本身。

// 输入："aaabbc"
// 输出："a3b2c"
// 输入："abcd"
// 输出："abcd"（因为没有连续重复）
// 输入："aabcccccaaa"
// 输出："a2bc5a3"

function compressString(s: string): string {
    if (s.length === 0) return '';

    const result: string[] = [];
    let i = 0;

    while (i < s.length) {
        const currentChar = s[i];
        let count = 1;
        let j = i + 1;

        while (j < s.length && s[j] === currentChar) {
            count++;
            j++;
        }

        if (count > 1) {
            result.push(currentChar + String(count));
        } else {
            result.push(currentChar!);
        }

        i = j;
            
        }

        return result.join('');

    }
    
// 简单自测
console.log(compressString('aaabbc'));      // a3b2c
console.log(compressString('abcd'));        // abcd
console.log(compressString('aabcccccaaa')); // a2bc5a3
console.log(compressString(''));            // ''
