// I2. Answer-space Binary Search (integer domain)
// I2. 答案空间二分（在整型区间上二分）
//
// Classic pattern: instead of binary-searching an index in an array,
// you binary-search an integer answer x in [lo, hi]. For each x,
// you call a feasibility function can(x) that tells you whether this x
// is "good enough". The results of can(x) over [lo, hi] must be
// monotone, typically F F F T T T.
//
// 经典套路：不是在数组下标上二分，而是在一个整数区间 [lo, hi]
// 上对“答案”进行二分。对每一个候选答案 x，调用可行性函数 can(x)
// 判断它是否“够好 / 可行”。can(x) 在 [lo, hi] 上必须是单调的，
// 一般形如 F F F T T T。
//
// Example problem (ship packages within D days):
// - Given an array weights and an integer days, choose the minimum ship
//   capacity cap so that we can ship all packages within `days` days
//   if each day we load packages in order until the capacity is full.
//
// 示例题目（D 天内运完包裹的最小载重）：
// - 给定数组 weights 和整数 days，选择一个最小载重 cap，使得在
//   每天按顺序装包裹、当天装满或装不下就开船的规则下，能够在
//   days 天内运完所有包裹。
//
// Template below is generic: plug in a concrete can(x) for your problem.

export function binarySearchAnswerSpace(
  lo: number,
  hi: number,
  can: (x: number) => boolean,
): number {
  // Find the minimum feasible x (first T). If no feasible x exists,
  // the caller can check the returned value separately.
  let ans = hi + 1; // sentinel: "no feasible answer found yet"

  while (lo <= hi) {
    const mid = Math.floor((lo + hi) / 2);
    if (can(mid)) {
      ans = mid;      // mid is feasible → try smaller answers
      hi = mid - 1;
    } else {
      lo = mid + 1;   // mid is not feasible → need larger answers
    }
  }

  return ans;
}

// Example can(x) for the shipping-capacity problem (for future TODO use):
// function canShip(cap: number, weights: number[], days: number): boolean {
//   let neededDays = 1;
//   let load = 0;
//   for (const w of weights) {
//     if (w > cap) return false; // single package exceeds capacity
//     if (load + w > cap) {
//       neededDays++;
//       load = 0;
//     }
//     load += w;
//   }
//   return neededDays <= days;
// }
//
// Usage pattern:
// const ans = binarySearchAnswerSpace(minCap, maxCap, x => canShip(x, weights, days));
//
// TODO: later you can move the concrete problem statement and helper into
// a dedicated function, e.g. `minShipCapacity(weights, days)` that wraps
// this generic template.
