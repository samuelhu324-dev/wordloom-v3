// K1. Merge Intervals
// K1. 合并区间

// Given an array of intervals where intervals[i] = [start_i, end_i],
// merge all overlapping intervals, and return an array of the non-overlapping intervals.
// 输入若干闭区间 [start_i, end_i]，合并所有有重叠的区间，返回不相交的区间列表。

function mergeIntervals(intervals: Array<[number,number]>): Array<[number,number]> {

    const sort = [...intervals].sort((a,b) => (a[0] - b[0]));
    const results: Array<[number,number]> = [];
    let [start,end] = sort[0]!;

    for (let i = 1; i < sort.length; i++) {
        let [currStart,currEnd] = sort[i]!;
        if (end >= currStart) {
            end = Math.max(currEnd, end);
        } else {
            // push the previous run's [start,end] when end < currStart
            results.push([start,end]);
            // reset it as a new one
            start = currStart;
            end = currEnd;
        }
    }
    results.push([start, end]);
    return results;
}

console.log(mergeIntervals([[1, 9], [2, 4], [3, 7], [8, 15]]));
console.log(mergeIntervals([[1, 2], [2, 4], [3, 7], [8, 15]]));
