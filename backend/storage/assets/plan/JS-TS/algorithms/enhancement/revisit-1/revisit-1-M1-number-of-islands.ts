// M1. Number of Islands
// M1. 岛屿数量

// Given a 2D grid map of '1's (land) and '0's (water),
// count the number of islands. An island is surrounded by water
// and is formed by connecting adjacent lands horizontally or vertically.
// 给定由 '1'（陆地）和 '0'（水）组成的二维网格
// 统计岛屿的数量（上下左右相连视为同一岛屿）。

// -----------------------------------------------------------------------------
// 1) Practice / 练习
// -----------------------------------------------------------------------------

function numIsLands(grid: string[][]): number {
    // indices for outer array
    let rows = grid.length;
    // indices for inner array
    // but if rows === 0, it would be 0; else, grid[0]!.length
    let cols = rows === 0 ? 0 : grid[0]!.length;
    // count of a maximal group of lands
    let count = 0;

    // void means it returns no values
    function dfs(r: number, c: number): void {
        // prevent from crossing the boundary
        if (r < 0 || r >= rows || c < 0 || c >= cols) return;
        // water or already visited lands
        // - the condition below is skipped in the first loop: dfs(r,c)
        //   since grid[r][c] is certainly === '1'
        // - however, it is meaningful when what we gonna turn is not '1'(lands)
        //   the execution would be cancelled here  
        if (grid[r]?.[c] === '0') return;

        // makr the land as visited with '0'
        grid[r]![c] = '0';
        // so does its neighbours and so on... until it reaches water
        dfs(r+1, c); // up
        dfs(r-1, c); // down
        dfs(r, c+1); // left
        dfs(r, c-1); // right
    }
    for (let r = 0; r < rows; r++) {
        for (let c = 0; c < cols; c++) {
            if (grid[r]?.[c] === '1') {
                count++;
                dfs(r,c);
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