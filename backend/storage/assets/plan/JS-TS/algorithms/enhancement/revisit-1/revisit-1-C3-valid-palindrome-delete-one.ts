// C3. Valid palindrome after deleting at most one character (two pointers)
// C3. 最多删除一个字符后是否能成为回文（双指针）

// Given a string s, you may delete at most one character.
// Return true if the remaining string can be a palindrome.
// 给定字符串 s，允许删除最多一个字符。
// 判断删除后能否得到一个回文串，返回 true/false。

// -----------------------------------------------------------------------------
// 1. Two‑pointers + helper / 双指针 + 辅助回文检查
// -----------------------------------------------------------------------------

function validPalindromeDeleteOne(s: string): boolean {
  let left = 0;
  let right = s.length - 1;

  while (left <= right) {
    if (s[left] === s[right]) {
      left++;
      right--;
    } else {
      // 用掉一次删除机会：删左或删右，二选一有一个能回文就行
      return (
        isValidPalindrome1(left + 1, right, s) ||
        isValidPalindrome1(left, right - 1, s)
      );
    }
  }
  // 整个串本来就是回文
  return true;
}

function isValidPalindrome1(left: number, right: number, s: string): boolean {
  while (left <= right) {
    if (s[left] === s[right]) {
      left++;
      right--;
    } else {
      return false;
    }
  }
  return true;
}

console.log(validPalindromeDeleteOne("abca")); // true (remove 'b' or 'c')
console.log(validPalindromeDeleteOne("abc"));  // false
console.log(validPalindromeDeleteOne("aba"));  // true

// -----------------------------------------------------------------------------
// 2. Delete EXACTLY one character to become a palindrome /
//    恰好删除一个字符后能否成为回文
// -----------------------------------------------------------------------------

function validPalindromeDeleteExactlyOne(s: string): boolean {
  const n = s.length;
  // With only one / zero character being deleted once, 
  // it'd either be an empty string, or nothing to be deleted
  if (n <= 1) return false;

  if (isValidPalindrome1(0, n - 1, s)) {
    return true;
  } 
  return validPalindromeDeleteOne(s);
}

console.log('exactly one:', validPalindromeDeleteExactlyOne('abca')); // true
console.log('exactly one:', validPalindromeDeleteExactlyOne('aba'));  // true
console.log('exactly one:', validPalindromeDeleteExactlyOne('abc'));  // false

// -----------------------------------------------------------------------------
// 3. Minimum deletions to make a palindrome /
//    最少删除多少个字符可以变成回文
// -----------------------------------------------------------------------------

// -----------------------------------------------------------------------------
// 1) idea / 思路
// -----------------------------------------------------------------------------

// 1. State
//    Let dp[l][r] be the minimum number of deletions needed to turn
//    the substring s[l...r] into a palindrome.
//    - Indices are inclusive: 0 ≤ l ≤ r < n
//    - Answer: dp[0][n-1]
// 2. Transition
//    Look at two ends s[i] and s[j]
//    2.1 If equal: s[l] === s[r]; both can be kept; no unnecessary deletion
//        - If there're still characters in between (l + 1 <= r -1): >= 3 characters
//          dp[l][r] = dp[l+1][r-1]
//        - If not (0): 1 or 2 characters; means the string itself is a palindrome.
//          dp[l][r] = 0
//    2.2 If unequal: s[i] !== s[r]; want to make a palindrome,
//        make sure to delet an end;
//        - Delete left char s[i]: cost = 1 + dp[l+1][r]
//        - Delete right char s[r]: cost = 1 + dp[l][r-1]
//        Take the smaller: dp[l][r] = 1 + min(dp[l+r][r],dp[l][r-1])
// 3. Order of filling (by increasing length)
//    Since each dp[l][r] depends on much shorter intervals, 
//    - Prioritise intervals with length 1: dp[i][i] = 0 (one char is already a palindrome)
//      and then those with length 2..3 up to n:
//      - loop over all valid l, set r = l + len - 1
//      - apply the formulas above
// 4. Complexity
//    - Number of states: O(n^2) (all combinations of l,r)
//    - Each state: O(1) transition
//      → Time O(n^2), space O(n^2)

// 1. 状态
//    令 dp[l][r] 为把子字符串 s[l...r] 变为回文所需的最小删除数；
//    - 下标含在内：0 ≤ l ≤ r < n
//    - 答案：dp[0][n-1]
// 2. 转移
//    看区间两端字符 s[l] 和 s[r]
//    2.1 如果相等：s[l] === s[r] 这两个可以一起保留，不需要删除：
//        - 中间还有字符的话 (l + 1 <= r - 1): >= 3 个字符:
//          dp[l][r] = dp[l+1][r-1]
//        - 中间没有字符的话 (0): 1 或 2 个字符，这段本身就是回文
//          dp[l][r] = 0
//    2.2 如果不等：s[l] !== s[r 想变成回文，一定要删掉一端的某个字符：
//        - 删左边 s[l]: 代价 = 1 + dp[l+1][r]
//        - 删右边 s[r]: 代价 = 1 + dp[l][r-1]
//        取更少的那个：dp[l][r] = 1 + min(dp[l+1][r], dp[l][r-1])
// 3. 填表顺序 (按区间长度填入)
//    因为每个 dp[l][r] 看“更短的区间”的情况：
//    - 优先处理长度为 1 的区间：dp[i][i] = 0 (一个字符已经是回文)
//    - 然后长度 2,3 ... 直到 n :
//      - 循环多遍所有符合条件的 l，设 r = l + len - 1
//      - 应用上面的公式
// 4. 复杂度
//    - 状态个数：O(n^2) (所有 l,r 组合)
//    - 每个状态：O(1) 次转移
//      → 时间：O(n^2), 空间 O(n^2)

function minDeletionsToPalindrome(s: string): number {
  const n = s.length;
  if (n <= 1) return 0;

  const dp: number[][] = Array.from({ length: n}, () => 
    Array<number>(n).fill(0),);

  for (let len = 2; len <= n; len++) {
    for (let l = 0; l + len - 1 < n; l++) {
      const r = l + len - 1;
      if (s[l] === s[r]) {
        // case I: >= 3 (no deletion); case II: 1 or 2 (0)
        dp[l]![r]! = l + 1 <= r - 1 ? dp[l + 1]![r - 1]! : 0; 
      } else {
        dp[l]![r]! = 1 + Math.min(dp[l]![r - 1]!, dp[l + 1]![r]!);
      }
    }
  }
  return dp[0]![n - 1]!;
}

console.log('min deletions:', minDeletionsToPalindrome('abca'));   // 1
console.log('min deletions:', minDeletionsToPalindrome('abcda'));  // 2
console.log('min deletions:', minDeletionsToPalindrome('racecar'));// 0

// -----------------------------------------------------------------------------
// Debug
// -----------------------------------------------------------------------------

function minDeletionsToPalindromeDebug(s: string): number {
  const n = s.length;
  if (n <= 1) return 0;

  console.log('s =', s, 'length =', n);

  // ① 这一句：const dp: number[][] = Array.from({ length: n }, () => Array<number>(n).fill(0))
  const dp: number[][] = Array.from({ length: n }, (_, rowIndex) => {
    const row = Array<number>(n).fill(0);
    console.log(`init row ${rowIndex}:`, row);
    return row;
  });

  console.log('after init dp =');
  console.table(dp);

  // ② 填表：当 s[l] !== s[r] 时，会执行
  //    dp[l][r] = 1 + Math.min(dp[l + 1][r], dp[l][r - 1]);

// ...existing code...
for (let len = 2; len <= n; len++) {
  console.log('---- len =', len, '----');
  for (let l = 0; l + len - 1 < n; l++) {
    const r = l + len - 1;
    const cl = s[l]!;
    const cr = s[r]!;

    console.log(`processing [l=${l}, r=${r}] => '${cl}' , '${cr}'`);

    if (cl === cr) {
      if (l + 1 <= r - 1) {
        dp[l]![r] = dp[l + 1]![r - 1]!;
        console.log(
          `  equal: dp[${l}][${r}] = dp[${l + 1}][${r - 1}] =`,
          dp[l]![r],
        );
      } else {
        dp[l]![r] = 0;
        console.log(`  equal & short: dp[${l}][${r}] = 0`);
      }
    } else {
      const delLeft = dp[l + 1]![r]!;
      const delRight = dp[l]![r - 1]!;
      dp[l]![r] = 1 + Math.min(delLeft, delRight);

      console.log(
        `  not equal: dp[${l}][${r}] = 1 + min(dp[${l + 1}][${r}] = ${delLeft}, dp[${l}][${r - 1}] = ${delRight}) =>`,
        dp[l]![r],
      );
    }
  }
  console.log('dp table after len =', len);
  console.table(dp);
}

console.log('final dp =');
console.table(dp);
console.log('answer dp[0][n-1] =', dp[0]![n - 1]!);
return dp[0]![n - 1]!;
// ...existing code...
}

// 你可以在终端里运行：
minDeletionsToPalindromeDebug('abca');
minDeletionsToPalindromeDebug('abcda');
