// M1. Number of Islands
// M1. 岛屿数量

// Given a 2D grid map of '1's (land) and '0's (water),
// count the number of islands. An island is surrounded by water
// and is formed by connecting adjacent lands horizontally or vertically.
// 给定由 '1'（陆地）和 '0'（水）组成的二维网格
// 统计岛屿的数量（上下左右相连视为同一岛屿）。

// -----------------------------------------------------------------------------
// 1) Idea / 思路
// -----------------------------------------------------------------------------

// 
// 1. We are given a 2D grid of '1' (land) and '0' (water) 
// 2. An island is a maximal group of '1' cells connected 
//    by up / down / left / right
// 3. Goal: count how many such connected groups exist.
//
// Key idea:
//   - Use double fors to scan over the whole grid.
//   - Whenever seeing a '1' that has not been visited, we:
//     - Count a new island.
//     - Run DFS from this cell to "flood" the entire island, turning all
//       connected '1' cells into '0' so they won't be counted again.
// 
// So each island is discovered exactly once and then erased.
//
// 1. 我们给定一个 2D 网格的 '1'（陆地） 和 '0'（水）
// 2. 岛屿是最大的一组 1 '格'，由 上/下/左/右 连接起来
// 3. 目标：数有多少个这样连接的组存在
// 
// 核心思路：
//   - 使用双重 for 循环把整个网格都扫一遍
//   - 每当遇到一个还没访问过的 '1'：
//     - 新数一个岛
//     - 从该格运行DFS，"倒给"整个岛屿，把所有连接的 '1' 格转成 '0'
//       所以再次数数不进去
//

// -----------------------------------------------------------------------------
// 2) Algorithm / 算法
// -----------------------------------------------------------------------------

// 1. Let rows = grid.length, cols = row === 0 ? 0 : grid[0]!.length, count = 0
// 2. Define dfs(r,c): 
//    - If (r,c) is out of bounds, return directly.
//    - If grid[r][c] !== '1', return (water or already visited).
//    - Otherwise:
//      - Set grid[r][c] = '0' to mark this land as visited.
//      - Recurse its 4 neighbours: (r+1, c), (r-1, c), (r, c+1), (r, c-1)
// 3. Double fors:
//    - For each r in [0, rows] and c in [0, cols]:
//      If grid[r][c] === '1':
//      - count++ (found a new island).
//      - Call dfs(r,c) to erase this whole island.
// 4. Return count 
// 
// 1. 设 rows = grid.length, cols = row 
// 2. 定义 dfs(r,c) 函数：
//    - 若 (r,c) 越界，直接返回；
//    - 若 grid[r][c] !== '1' (是水或已经访问过) 直接返回；
//    - 否则：
//      - 把 grid[r][c] 设为 '0' , 把“这块陆地"标记为"已经访问过”
//      - 对其四周递归：(r+1, c)、(r-1, c)、(r, c+1)、(r, c-1)
// 3. 双重 for 循环：
//    - 每个 [0, rows] 里的 r 和 每个 [0, cols] 里的 c
//      若 grid[r][c] === '1':
//      - count++ (求出了一个新的岛屿)
//      - 调用 dfs(r,c) 抹除这整个岛屿
// 4. 返回计数
// 

function numIsLands(grid: string[][]): number {
  // rows: the outer array's indices
  // cols: the inner array's indices
  // If rows === 0, then cols = 0; else: the grid[0]!.length (any number is okay here)
  let rows = grid.length;
  let cols = rows === 0 ? 0 : grid[0]!.length;
  let count = 0;

  function DFS(r: number, c: number): void {
    // in case for boundary-cross
    if (r < 0 || r >= rows || c < 0 || c >= cols) return;
    // water or already visted land
    if (grid[r]?.[c] !== '1') return;

    grid[r][c] = '0';
    
    DFS(r+1, c); // ↓
    DFS(r-1, c); // ↑
    DFS(r, c+1); // →
    DFS(r, c-1); // ←
  }

  for (let r = 0; r < rows; r++) {
    for (let c = 0; c < cols; c++) {
      if (grid[r]![c] === '1') {
        count++;
        DFS(r, c);
      }
    }
  }
  return count;
}

// 1) 空网格
console.log(numIsLands([])); // 0

// 2) 全是水
console.log(
  numIsLands([
    ["0", "0"],
    ["0", "0"],
  ]),
); // 0

// 3) 只有一块连续陆地
console.log(
  numIsLands([
    ["1", "1", "1"],
    ["1", "1", "1"],
  ]),
); // 1

// 4) 多个岛屿（题解里那种）
console.log(
  numIsLands([
    ["1", "1", "0", "0", "0"],
    ["1", "1", "0", "0", "1"],
    ["0", "0", "1", "0", "1"],
    ["0", "0", "0", "0", "1"],
  ]),
); // 3

// 5) 只在对角线相连（不算一块岛）
console.log(
  numIsLands([
    ["1", "0", "1"],
    ["0", "1", "0"],
    ["1", "0", "1"],
  ]),
); // 5


// -----------------------------------------------------------------------------
// 3) Complexity / 复杂度
// -----------------------------------------------------------------------------
// 
// Each cell is visited at most once (when DFS turns '1' into '0').
// 1. Time: O(rows * cols).
// 2. Space: 
//    - O(rows * cols) in worst case for recursion stack (a big single island)
//    - Extra memory is only the recursion stack; we mark in-place

// 每个格子最多访问一次（从'1'变成'0'时）
// 1. 时间：O(rows * cols)
// 2. 空间：
//    - O(rows * cols) 递归栈在最坏情况下（一块大岛）
//    - 额外内存只有递归栈；原地标记


// -----------------------------------------------------------------------------
// 4) Practice / 练习
// -----------------------------------------------------------------------------
// 