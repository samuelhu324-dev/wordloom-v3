// 题 1：最小差值对

// 方法一：排序 + 遍历相邻元素
// 描述：给定一个包含 n 个整数的数组，找出其中差值最小的一对数，返回它们的差值。
// 例如，输入数组 [3, 8, 2]，差值最小的一对数是 (2, 3)，它们的差值为 1。

function minDiffPair(nums: number[]): number {
  // 少于 2 个数没法组成一对
  if (nums.length < 2) {
    throw new Error('need at least 2 numbers');
  }

  // 浅拷贝一份并按从小到大排序（不改原数组）
  const sorted = [...nums].sort((a, b) => a - b);
  
  // 初始化答案为一个很大的数
  let ans = Infinity;

  // 遍历排序后的数组，计算相邻元素的差值
  for (let i = 1; i < sorted.length; i++) {
    const curr = sorted[i]!;     // 加上 !，告诉 TS 一定不是 undefined
    const prev = sorted[i - 1]!; // 同上
    const diff = curr - prev;
    if (diff < ans) {
      ans = diff;
    }
  }
  
  return ans;
}

// 简单自测
console.log(minDiffPair([3, 8, 2]));             // 1
console.log(minDiffPair([1, 5, 3, 19, 18, 25])); // 1
console.log(minDiffPair([-1, -5, 10, 12]));      // 4

// 方法二：使用 Set 存储已访问元素 / 双重for循环
// 描述：通过一个 Set 来存储已经访问过的元素，遍历数组时计算当前元素与 Set 中每个元素的差值，更新最小差值。

function minDiffPairSet(nums: number[]): number {
  if (nums.length < 2) {
  // 少于 2 个数没法组成一对
    throw new Error('need at least 2 numbers');
  }

  // 使用 Set 存储已访问的元素 / 双重for循环
  // <number>：TS泛型；指定 Set 中存储的元素类型为数字
  const seen = new Set<number>();

  // 初始化答案为一个很大的数
  let ans = Infinity;

  // 遍历数组
  for (const num of nums) {
    for (const s of seen) {
      const diff = Math.abs(num - s); 
      if (diff < ans) {
        ans = diff;
      }
    }
    seen.add(num);
  } 
  return ans;
}

// 自测
console.log(minDiffPairSet([3, 8, 2])); // 1
console.log(minDiffPairSet([1, 5, 3, 19, 18, 25])); // 1
console.log(minDiffPairSet([-1, -5, 10, 12])); // 4
