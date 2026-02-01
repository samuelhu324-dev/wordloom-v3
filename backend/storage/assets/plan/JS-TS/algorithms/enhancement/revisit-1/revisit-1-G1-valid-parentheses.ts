// G1. 有效括号（栈）
// G1. Valid parentheses (stack)

// 给定一个只包含 '()[]{}' 的字符串 s，判断字符串是否是有效的括号序列。
// 有效括号需满足：
// 1) 左括号必须用相同类型的右括号闭合；
// 2) 左括号必须以正确的顺序闭合。
// Given a string s containing only the characters '()[]{}',
// determine if the input string is a valid parentheses sequence.
// A valid sequence means:
// 1) Open brackets are closed by the same type of brackets;
// 2) Open brackets are closed in the correct order.

// -----------------------------------------------------------------------------
// 1) 核心思路 / Core Idea
// -----------------------------------------------------------------------------

// 用栈（stack）存“当前还没被匹配的括号”。
// Use a stack to hold brackets that are not matched yet.

// 1. 从左到右扫描字符串
// 2. 遇到 左括号：把“期待的右括号”压栈
// 3. 遇到 右括号：从栈顶弹出期望值，比对是否相同
// 4. 所有字符处理完后：如果从未比对失败且栈刚好为空，返回 true

// 1. Scan the string from left to right
// 2. When seeing an opening bracket, 
//    push the expected closing bracket onto the stack
// 3. When seeing a closing bracket, pop the expected value 
//    from the top of the stack and compare
// 4. After all characters are finished treating, 
//    If match(es) never failed and stack is empty, return true

// -----------------------------------------------------------------------------
// 2) 实现 / Implementation
// -----------------------------------------------------------------------------

function isValidParentheses(s: string): boolean {

// 1. 奇数长度直接不可能合法
// 1. Old length can't be valid

    if (s.length % 2 === 1) return false;
    const stack: string[] = [];

// 2. 用 map 记录 “左” 到 “右” 的映射
//    - Key 是左括号，value 是对应的右括号
// 2. Use a map to record "opening" to "closing".
//    - Keys are opening brackets, values are corresponding closing brackets

    const map: Record<string, string> = {
        '(': ')',
        '[': ']',
        '{': '}',
    };

// 3. 每个字符循环一遍
//    - 这样可以自然处理嵌套，比如 ([{}])
//    - 栈中顺序就是： ) - ] - } 依次被 } - ] - ) 匹配
// 3. Loop over each char
//    - This naturally handles nesting (([{}]))
//    - The order in the stack is: ) - ] - } are matched respectively by } - ] - )

    for (const ch of s) {
        if (ch in map) {
            stack.push(map[ch]!);
        } else {
            const expected = stack.pop();
            if (expected !== ch) return false;
        }
    }

// 4. 最后栈检查
//    - 如果还有未匹配的“期待右括号”残留在栈中，可能左括号多了
// 4. Final stack check
//    - If there are still expected closings in the stack
//      possibly there were too many openings.

    return stack.length === 0;

}

// 5. 自测
// 5. Self-test

console.log(isValidParentheses('()[]{}'));   // true
console.log(isValidParentheses('()[]}'));    // false
console.log(isValidParentheses('(([]{}'));   // false
console.log(isValidParentheses(''));         // true（按常规定义）
console.log(isValidParentheses('()[]()'));   // true
console.log(isValidParentheses('([{}])'));   // true
console.log(isValidParentheses('(]'));       // false

// -----------------------------------------------------------------------------
// 3) 复杂度 / Complexity
// -----------------------------------------------------------------------------

// 1. 时间：O(n)，每个字符最多入栈一次、出栈一次
// 2. 空间：O(n)，最坏情况，全是左括号时栈大小为 n 
// 1. Time: O(n), Each character is pushed and popped at most once
// 2. Space: O(n), In the worst case (all openings), the stack size is n

// -----------------------------------------------------------------------------
// 4) 练习 / Practice
// -----------------------------------------------------------------------------

function isValidParentheses_Practice(s: string): boolean {

    const stack: string[] = [];
    const map: Record<string, string> = {
        '(': ')',
        '[': ']',
        '{': '}',
    }

    for (const ch of s) {
        if (ch in map) {
            stack.push(map[ch]!);
        } else {
            const exp = stack.pop();
            if (exp !== ch) return false;
        }
    }
    return stack.length === 0;
    
}

console.log(isValidParentheses_Practice('((()))'));
console.log(isValidParentheses_Practice('()[]'));
console.log(isValidParentheses_Practice('()['));
console.log(isValidParentheses_Practice(''));

