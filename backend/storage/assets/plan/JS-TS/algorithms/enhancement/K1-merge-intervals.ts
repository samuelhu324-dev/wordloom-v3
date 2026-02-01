// K1. Merge Intervals
// K1. 合并区间

// Given an array of intervals where intervals[i] = [start_i, end_i],
// merge all overlapping intervals, and return an array of the non-overlapping intervals.
// 输入若干闭区间 [start_i, end_i]，合并所有有重叠的区间，返回不相交的区间列表。

// -----------------------------------------------------------------------------
// 1) Steps / 步骤
// -----------------------------------------------------------------------------

function mergeIntervals(intervals: Array<[number,number]>): Array<[number,number]> {

// 1. Sort by start
//    - Sort all intervals by start ascending:
//      This only requires a linear scan through it. As long as each new interval
//      is compared with the "current merged interval" once, we can decide overlap
// 2. Initialize current interval
//    - Take the first interval [s,e] as the current merged interval:
//      currStart = s, currEnd = e
//    - We will try to extend this interval as much as possible.
//
// 1. 按起点排序
//    - 把所有区间按 start 从小到大排：
//      这样只需要线性往后扫，每个新区间只要跟“当前维护的区间”比较一次
//      就能判断是否重叠
// 2. 初始化当前区间
//    - 取第一个区间 [s,e] 取作当前合并区间：
//      currStart = s, currEnd = e
//    - 之后我们把这个区间尽可能扩大一下

  if (intervals.length === 0) return [];

  intervals.sort((a,b) => (a[0] - b[0]));

  const merged: Array<[number,number]> = [];

  let [currStart,currEnd] = intervals[0]!;
  
// 3. Scan the rest linearly
//    - For each follow-up [start,end]:
//      If start <= currEnd: overlap (or end-to-end)
//      [start,end] intersects/connects [currStart,currEnd]
//      so merge by extending the end: currEnd = max(currEnd,end)
//      (with start as invariant, always currStart)
//    - Else (start > currEnd): no overlap
//      The current interval [currStart,currEnd] was already sealed up
//      with all possible intervals on the right:
//      1. Push [currStart,currEnd] into merged;
//      2. Start a new current interval with [start,end]: currStart = start, currEnd = end
// 3. 线性扫描其余区间
//    - 每个后续区间 [start,end]：
//      若 start <= currEnd：就有重叠 / 首尾相接，
//      说明 [start,end] 和当前 [currStart,currEnd] 相交或接上，
//      所以扩大端点就可以合并：currEnd = max(currEnd,end)
//      (起点不用变，永远是 currStart)
//    - 否则（start > currEnd）：没有重叠
//      当前区间 [currStart,currEnd] 已经封口了，后面的都在右边
//      1. 把 [currStart,currEnd] 推入 merged;
//      2. 另起一个新的当前区间 [start, end]：currStart = start, currEnd = end

  for (let i = 1; i < intervals.length; i++) {
    const [start,end] = intervals[i]!;
    if (currEnd >= start ) {
      currEnd = Math.max(currEnd, end);
    } else {
      merged.push([currStart, currEnd]);
      currStart = start;
      currEnd = end;
    }
  }

// 4. Add up the last one: 
//    - After the scan, the last maintained [currStart,currEnd] has not been pushed yet
//    - Just push it once more
// 4. 补上最后一个区间:
//    - 扫描后最后维护的那个 [currStart,currEnd] 还没被push进去
//    - 再 push 一次就好

  merged.push([currStart,currEnd]);

  return merged;
   
}

// 5. Self-test
// 5. 自测

console.log(mergeIntervals([[1,2],[2,3],[3,4],[7,8]]));

// -----------------------------------------------------------------------------
// 2) Complexity / 复杂度
// -----------------------------------------------------------------------------

// 1. 时间：排序 O(n log n)，一趟扫描 O(n) , 总体 O(n log n)；
// 2. 空间：只用常数额外空间（结果数组不算）O(1) 额外空间
// 1. Time: Sorting O(n log n). One pass: O(n). Overall: O(n long n)
// 2. Space: only with extra constant space (excluding the output list) Extra space: O(1) 
