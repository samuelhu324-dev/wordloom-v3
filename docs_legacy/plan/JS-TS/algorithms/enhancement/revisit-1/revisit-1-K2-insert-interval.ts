// K2. Insert Interval
// K2. 插入区间

// You are given an array of non-overlapping intervals sorted by start time,
// and a new interval. Insert the new interval into the intervals such that
// the result is still non-overlapping and sorted.
// 给定按起点排好序且互不重叠的区间数组和一个新区间，将新区间插入并合并，
// 结果仍然有序且不重叠。

// -----------------------------------------------------------------------------
// 1. Insert one subarray
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
// 2. merge two interval lists
// -----------------------------------------------------------------------------

// -----------------------------------------------------------------------------
// 1) idea / 思路
// -----------------------------------------------------------------------------
// 
// 1. 按起点合并成一条有序链 (不管重不重叠)
//    用两个指针 i,j 扫描 a、b :
//      - 哪一个起点小，就把哪一个 push 到 mergedByStart，对应地移动指针
//      - 剩下没扫完的一条链整体 append 到 mergedByStart 
//      - 这一步就像“归并排序的 merge 步骤”
//    做完之后，mergedByStart 是一条按 start 排序的区间链，但里面可能有重叠
// 2. 把这条有序链的重叠区间合并
//    - 维护当前合并中的区间 [start,end]，初始为 mergedByStart[0]
//    - 依次看后面的每个 [currStart,currEnd]:
//      - 如果 currStart <= end: 说明有重叠
//        更新 end = max(end,currEnd);
//      - 否则：说明不重叠 ->
//        把当前 [start,end] 推进结果数组 res，
//        然后重置 start = currStart, end = currEnd
//    - 循环结束后，再把最后一个 [start,end] 推入 res
// 3. 复杂度
//    - 合并两条有序链：O(m + n)
//    - 扫一遍合并重叠：O(m + n)
//    - 总时间：O(m + n) 
//      空间：O(m + n) (中间的 mergedByStart 和结果)
//
// 1. Merge them into a sorted list by start (whether it is overlapped or not)
//    Use two pointer i,j to scan a,b:
//    - Whichever has a smaller start, push it into the mergedByStart; 
//      we accordingly move pointers
//    - This is just like "merge sort's merge step"
//    After it finishes, mergedByStart is an interval list sorted by start, 
//    however, possibly containing overlaps 
// 2. Merge overlaps in the sorted list 
//    - Maintain current [start,end] being meged, initializing mergedByStart[0]
//    - Look at each possible [currStart,currEnd] in turn
//      - If currStart <= end, that means an overlap
//        Update end = max(end,currEnd)
//      - Otherwise, that means no overlap ->
//        Push the current [start,end] into the array res
//      - And after loop ends, push the last [start,end] into res
// 3. Complexity
//    - Merge two sorted lists: O(m + n)
//    - One scan over merged overlaps: O(m + n)
//    - Total time: O(m + n)
//    - Space: O(m + n) (with mergedByStart in between and result)

function mergedTwoSortedIntervals(a: Array<[number,number]>, 
    b: Array<[number,number]>): Array<[number,number]> {
        const mergedByStart: Array<[number,number]> = [];
        const res: Array<[number,number]> = [];

        let i = 0;
        let j = 0;
        // Push each pair into the res until either is finished
        while (i < a.length && j < b.length) {
            if (a[i]![0]! <= b[j]![0]) {
                mergedByStart.push(a[i++]!);
            } else {
                mergedByStart.push(b[j++]!);
            }
        }

        // for one of remaining lists, push rest of them into an array
        while (i < a.length) mergedByStart.push(a[i++]!);
        while (j < a.length) mergedByStart.push(a[j++]!);

        let [start,end] = mergedByStart[0]!;
        for (let i = 1; i < mergedByStart.length; i++) {
            const [currStart,currEnd] = mergedByStart[i]!;
            if (end >= currStart) { // some overlap
                end = Math.max(currEnd, end);
            } else {  // no overlap
                res.push([start,end]);
                start = currStart;
                end = currEnd;
            }
        }
        res.push([start,end]);
        return res;
    }

console.log(
  mergedTwoSortedIntervals(
    [[1, 2], [3, 4], [5, 6]],
    [[0, 1], [2, 3], [4, 5]]
  )
);

//
// -----------------------------------------------------------------------------
// 2) Practice / 练习
// -----------------------------------------------------------------------------
//
// 1. 从两条链里选下一个区间 next 
//    - 如果 i < a.length && j < b.length:
//      - 哪一个 start 小，就把哪个作为 next 
//    - 如果某一条已经选完，直接从另一条里选
// 2. 只和 res 最后的区间比较，可以把 next 合并进 res
//    设 last = res[res.length - 1]:
//    - 若 res 还空，或 last.end < next.start，则完全不重叠，直接 res.push(next)
//    - 不然就有重叠，则更新 last.end = max(last.end,next.end)
// 3. 到 a、b 穷尽前都继续扫
//    因为任何新区间的 start 都 >= 已在 res 中的所有区间的 start，
//    所以“只和结果末尾比较”就足够判断是否重叠
//
// 1. Pick the next from two lists
//    - If i < a.length && j < b.length:
//      - Whichever has a smaller start, it becomes the next
//    - Pick it from one list, if another has already run out;
// 2. Merge next into res by comparing only with the last interval in res:
//    - If res is empty or last.end < next.start, no evident overlap. 
//      res.push(next) directly.
//    - Else, there would be overlaps, so update last.end = max(last.end,next.end)
//      last.end = max(last.end, next.end)
// 3. Continue until both a and b are exhausted
//    Because any new interval's start >= all intervals' starts already in res
//    it'd be enough for comparison only with the ending result to tell an overlap 
// 

function mergeTwoIntervalListsOnepass(
    a: Array<[number,number]>,
    b: Array<[number,number]>,
): Array<[number,number]> {
    const res: Array<[number,number]> = [];
    let i = 0;
    let j = 0;
    const pickNext = (): [number,number] | undefined => {
        if (i < a.length && j < b.length) {
            if (a[i]![0]! <= b[j]![0]!) return a[i++]!;
            return b[j++];
        }
        if(i < a.length) return a[i++]!;
        if(j < b.length) return b[i++]!;
        return undefined;
    };

    while (true) {
        const next = pickNext();
        if (!next) break;
        const [nextStart, nextEnd] = next;
        // interval's end already in res - next interval's start
        if (!res.length || res[res.length - 1]![1] < nextStart) {
            res.push([nextStart, nextEnd]);
        } else {
            res[res.length - 1]![1] = Math.max(res[res.length - 1]![1], nextEnd); 
        };
    }
    return res;
}

console.log(mergeTwoIntervalListsOnepass(
    [[1,2],[3,4],[5,6]],
    [[2,3],[4,5],[9,10]]
));