// 题 4：判断能否通过删除一个字符变成回文（String + 双指针）
//
// 给定一个字符串 s，你可以最多删除一个字符。
// 判断剩下的字符串能否是回文（true / false）。
//
// 示例：
//   输入："abca"  → 可以删掉 'b' 或 'c'，变成 "aca" 或 "aba"，返回 true
//   输入："abc"   → 无论删谁都不是回文，返回 false
//
// 要求：
//   1. 实现函数 validPalindrome(s: string): boolean
//   2. 尽量使用双指针（left / right），时间复杂度 O(n)
//   3. 只需要考虑普通字符串，大小写敏感与否你可以自行约定（先简单按“完全相等”处理）


// 题 4：判断能否通过删除一个字符变成回文（String + 双指针）

function validPalindrome(s: string): boolean {
  let left = 0;
  let right = s.length - 1;

    while (left < right) {
      if (s[left] === s[right]) {
        left++;
        right--;
      } else {

        // 出现不匹配时，尝试跳过左指针或右指针
        return isPalindromeInRange(s, left +1 , right) ||
                isPalindromeInRange(s, left, right -1);
      }
    } 
    return true; // 全程匹配，直接是回文
  }

function isPalindromeInRange(s: string, left: number, right: number): boolean {
  while (left < right) {
    if (s[left] !== s[right]) {
      return false;
    }
    left++;
    right--;
  }
  return true;
}

console.log('result =', validPalindrome('abca')); // 先只看这个用例


// 简单自测
console.log(validPalindrome('abca')); // true
console.log(validPalindrome('abc'));  // false
console.log(validPalindrome('abba')); // true
console.log(validPalindrome('a'));    // true
console.log(validPalindrome(''));     // 这里我们约定空串也算回文，所以 true

