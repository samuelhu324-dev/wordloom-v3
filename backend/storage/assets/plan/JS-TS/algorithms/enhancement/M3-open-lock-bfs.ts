// M3. Open the Lock (BFS on state space)
// M3. 打开转盘锁（状态图 BFS）

// You have a lock represented by a 4-digit string, from "0000" to "9999".
// Some combinations are deadends. Given a target, find the minimum number of moves
// to open the lock, or -1 if impossible.
// 四位数密码锁，从 "0000" 开始，每次转动一位 +1/-1，有若干死锁状态，给定目标字符串，求最少旋转步数，不可达则返回 -1。

export function openLock(deadends: string[], target: string): number {
  // TODO: implement (BFS over string states)
  return -1;
}
