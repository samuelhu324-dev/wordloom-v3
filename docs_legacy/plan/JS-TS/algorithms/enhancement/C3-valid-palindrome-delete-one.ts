// C3. Valid palindrome after deleting at most one character (two pointers)
// C3. 最多删除一个字符后是否能成为回文（双指针）

// Given a string s, you may delete at most one character.
// Return true if the remaining string can be a palindrome.
// 给定字符串 s，允许删除最多一个字符。
// 判断删除后能否得到一个回文串，返回 true/false。

// -----------------------------------------------------------------------------
// 1) Two‑pointers + helper / 双指针 + 辅助回文检查
// -----------------------------------------------------------------------------

function validPalindromeDeleteOne(s: string): boolean {
  let left = 0;
  let right = s.length - 1;

  while (left < right) {
    if (s[left] === s[right]) {
      left++;
      right--;
    } else {
      // 尝试跳过左边或右边任意一个字符
      return (
        isPalindromeRange(s, left + 1, right) ||
        isPalindromeRange(s, left, right - 1)
      );
    }
  }

  // 如果一路都没冲突，本身就是回文
  return true;
}

function isPalindromeRange(str: string, l: number, r: number): boolean {
  while (l < r) {
    if (str[l] !== str[r]) return false;
    l++;
    r--;
  }
  return true;
}

// 2) Self‑test / 自测

console.log(validPalindromeDeleteOne("abca")); // true (remove 'b' or 'c')
console.log(validPalindromeDeleteOne("abc"));  // false
console.log(validPalindromeDeleteOne("aba"));  // true

// -----------------------------------------------------------------------------
// 3) Complexity / 复杂度
// -----------------------------------------------------------------------------
// Time 时间：O(n)  主循环 + 至多一次子区间回文检查
// Space 空间：O(1)  仅常数级指针变量
