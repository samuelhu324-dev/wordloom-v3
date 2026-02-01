// G1. Valid parentheses (stack)
// G1. 有效括号（栈）

// Given a string s containing only the characters '()[]{}',
// determine if the input string is a valid parentheses sequence.
// A valid sequence means:
// 1) Open brackets are closed by the same type of brackets;
// 2) Open brackets are closed in the correct order.
// 给定一个只包含 '()[]{}' 的字符串 s，判断字符串是否是有效的括号序列。
// 有效括号需满足：
// 1) 左括号必须用相同类型的右括号闭合；
// 2) 左括号必须以正确的顺序闭合。

// -----------------------------------------------------------------------------
// 1) Record version
// -----------------------------------------------------------------------------

function validParentheses_Record(s:string): boolean {
    
    if (s.length === 0) return false;

    const map: Record<string, string> = {
        '[': ']',
        '{': '}',
        '(': ')',
    }

    const stack: string[] = [];

    for (let i = 0; i < s.length; i++) {
        const ch = s[i]!;
        if (ch in map) {
            stack.push(map[ch]!);
        } else {
            const need = stack.pop()!;
            if (need !== ch) return false;
        }
    }
    return stack.length === 0;
}

console.log(validParentheses_Record('([{}])'));
console.log(validParentheses_Record('([{}])([{}])'));
console.log(validParentheses_Record('()[{}]'));
console.log(validParentheses_Record('()[{}'));

// -----------------------------------------------------------------------------
// 2) Map version
// -----------------------------------------------------------------------------

function validParentheses_Map(s:string): boolean {
    if (s.length === 0) return false;

    const map = new Map<string,string>([
        ['(', ')'],
        ['{', '}'],
        ['[', ']'],
    ]);

    const stack: string[] = [];

    for (const ch of s) {
        if (map.has(ch)) {
            stack.push(map.get(ch)!);
        } else {
            const need = stack.pop()!;
            if (need !== ch) return false;
        }
    }
    return stack.length === 0;
}

console.log(validParentheses_Map('([{}])'));
console.log(validParentheses_Map('([{}])([{}])'));
console.log(validParentheses_Map('()[{}]'));
console.log(validParentheses_Map('()[{}'));
