// K2. Insert Interval
// K2. 插入区间

// You are given an array of non-overlapping intervals sorted by start time,
// and a new interval. Insert the new interval into the intervals such that
// the result is still non-overlapping and sorted.
// 给定按起点排好序且互不重叠的区间数组和一个新区间，将新区间插入并合并，
// 结果仍然有序且不重叠。

// -----------------------------------------------------------------------------
// 1) Insert one subarray
// -----------------------------------------------------------------------------

function insertInterval(intervals: Array<[number, number]>, newInterval: [number, number]): Array<[number, number]> {
  const inter = [...intervals];
  inter.push(newInterval);
  inter.sort((a,b) => (a[0] - b[0]));

  let [start,end] = inter[0]!;
  const results: Array<[number,number]> = [];

  for (let i = 1; i < inter.length; i++) {

    const [currStart, currEnd] = inter[i]!;
    if (end >= currStart) {
      // remain the initial start and bigger end 
      // e.g. [1,9] [1,2] ->
      // end<9> > currStart<1> && end<9> > currEnd<2> -> [1,9]
      end = Math.max(currEnd,end);
    } else {
      results.push([start, end]);
      start = currStart;
      end = currEnd;
    }
  }
  results.push([start,end]);
  return results;
}

console.log(insertInterval([[1,2],[3,4],[5,6]],[1,4]));

// -----------------------------------------------------------------------------
// 2) merge two interval lists
// -----------------------------------------------------------------------------

function mergeTwoIntervalLists(
  a: Array<[number,number]>,
  b: Array<[number,number]>
): Array<[number,number]> {
  const mergedByStart: Array<[number,number]> = [];
  let i = 0, j = 0;

  while (i < a.length && j < b.length) {
    if (a[i]![0] <= b[j]![0]) {
      mergedByStart.push(a[i++]!);
    } else {
      mergedByStart.push(b[j++]!);
    }
  }
  while (i < a.length) mergedByStart.push(a[i++]!);
  while (j < b.length) mergedByStart.push(b[j++]!);

  if (mergedByStart.length === 0) return [];

  const res: Array<[number,number]> = [];
  let [start,end] = mergedByStart[0]!;

  for (let k = 1; k < mergedByStart.length; k++) {
    const [currStart,currEnd] = mergedByStart[k]!;
    if (end >= currStart) {
      end = Math.max(end, currEnd);
    } else {
      res.push([start,end]);
      start = currStart;
      end = currEnd;
    }
  }
  res.push([start,end]);
  return res;
}

console.log(
  mergeTwoIntervalLists(
    [[1, 2], [3, 4], [5, 6]],
    [[0, 1], [2, 3], [4, 5]]
  )
);


//
const res: Array<[number, number]> = [];
for (const [s, e] of mergedByStart) {
  if (!res.length || res[res.length - 1][1] < s) {
    res.push([s, e]);                          // 不重叠，新开一段
  } else {
    res[res.length - 1][1] = Math.max(         // 重叠，更新末尾区间的 end
      res[res.length - 1][1],
      e
    );
  }
}
//