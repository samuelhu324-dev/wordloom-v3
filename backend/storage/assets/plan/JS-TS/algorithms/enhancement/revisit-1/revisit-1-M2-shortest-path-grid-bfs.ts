// M2. Shortest Path in Grid (BFS)
// M2. 网格中的最短路径（BFS）
//
// Given a grid with 0 as empty cell and 1 as obstacle, find the shortest path
// from the top-left to the bottom-right cell, moving in 4 directions. 
// If not reachable, return -1.
// 给定只包含 0（可走）和 1（障碍）的网格，从左上角走到右下角
// 只能上下左右移动，返回最短路径长度，不可达则返回 -1。
//
// -----------------------------------------------------------------------------
// 1) BFS (layer by layer)
// -----------------------------------------------------------------------------
//
// 1. State
//    Each state is a cell (r,c) plus its dist (how many steps we took from start)
// 2. Start from (0,0)
//    If top-left (0,0) or bottom-right (row - 1, cols -1) is an obstacle,
//    return -1 directly. Otherwise push (0,0,0) into queue and mark it visited
// 3. Directions
//    We can move in only 4 directions: up, down, left, right.
//    Represent them as (dr,dc) pairs
// 4. BFS expansion
//    While the queue is not empty, pop the front (r,c,dist)
//    - If (r,c) is the bottom-right cell, return dist 
//     (this is the shortest path length).
//    - Otherwise, for each direction, compute neighbour (nr,nc) and check:
//      1. nr,nc is part of the grid
//      2. grid[nr][nc] === 0 (not an obstacle)
//      3. !visited[nr][nc], which hasn't been visited before
//         While all pass, mark visited[nr][nc] = true, and push (nr,nc,dist + 1)
//         into the queue.
// 5. No path
//    If the queue becomes empty and we never reached the bottom-right, 
//    return -1 (target not reachable)
// 6. Why it must be shortest?
//    BFS explores cells in increasing dist order (layer by layer). The first time
//    we reach the target, we must have used the fewest steps.
// 
// 1. 状态
//    每个状态是一格 (r,c) 加上其 dist (到起点走了多少步)
// 2. 从 (0,0) 开始
//    如果左上 (0,0) 或者 右下 (row - 1, cols - 1) 是障碍 (值为 1 )
//    直接返回 -1 ; 否则把 (0,0,0) 推入队列并标为已访问
// 3. 方向
//    只能走四个方向：上、下、左、右，表示为 (dr,dc) 数对
// 4. BFS 扩散
//    队列没有空的话，弹出队头 (r,c,dist)
//    - 如果 (r,c) 是右下格，返回 dist (这是最短路径)
//    - 否则，每个方向，计算相邻格 (nr,nc) 再看：
//      1. nr,nc 在网格内部
//      2. grid[nr][nc] === 0 (not an obstacle)
//      3. !visited[nr][nc]，之前没访问过
//         一切顺利的话，标记 visited[nr][nc] = true 并把 (nr,nc,dist + 1) 推入队列
// 5. 无路可走
//    如果队列为空，永远走不到右下角，返回 -1 (目标不可达) 
// 6. 为什么一定是最短？
//    BFS以递增顺序探索格子（一层一层）。第一次到目标时，我们一定使用了最少的步数

function shortestPathDP(grid: number[][]): number {
    const rows = grid.length;
    // rows have nothing
    if (!rows) return -1;
    const cols = grid[0]!.length;
    // both top-right and bottom-left cell are blocks
    if (grid[0]![0] === 1 || grid[rows - 1]![cols - 1] === 1) return -1;

    const dirs: [number,number][] = [
        [-1, 0], // Up
        [1, 0],  // Down
        [0, -1], // Left 
        [0, 1]   // Right
    ];

    const visited: boolean[][] = Array.from({ length: rows }, () => 
        Array(cols).fill(false)
    );

    const queue: [number, number, number][] = [];
    // initialize the queue from grid[0][0]
    queue.push([0, 0, 0]);
    visited[0]![0] = true;

    while (queue.length) {
        const [r, c, dist] = queue.shift()!;
        // return the final answer
        if (r === rows - 1 && c === cols - 1) {
            return dist;
        }

        for (const [dr, dc] of dirs) {
            const nr = r + dr;
            const nc = c + dc;

            if (nr >= 0 && nr < rows && // 1. crossing the boundary of rows
                nc >= 0 && nc < cols && // 2. crossing the boundary of cols
                grid[nr]![nc] !== 1 &&  // 3. the cell is not a block
                !visited[nr]![nc]       // 4. it hasn't visited yet
            ) {
                visited[nr]![nc] = true;
                queue.push([nr, nc, dist + 1]);
            }
        }
    }
    return -1;
}

console.log(shortestPathDP([
    [0,0,0,1,0,0,0],
    [0,1,0,0,0,0,0],
    [0,0,0,0,0,0,0]]))

// dist:
// 0:     0 1 2 X 6 7 8
// 1:     1 X 3 4 5 6 7
// 2:     2 3 4 5 6 7 8   ← 终点 (2,6) 距离 8

// -----------------------------------------------------------------------------
// 2. DP -> find the number of all paths
// -----------------------------------------------------------------------------
//
// -----------------------------------------------------------------------------
// 1) What does dp[c] mean? / dp[c] 的含义
// -----------------------------------------------------------------------------
//
// dp[c] = number of paths to cell (r,c) on the current row
//
// We can scan the grid row by row, left to right. For each row r, dp[c] stores the 
// the number of different paths from (0,0) to (r,c).
// 
// dp[c] = 当前行上到第 (r,c) 格的路径数
// 
// 我们可以一排排扫描网格，从左到右扫。每一排 r ，
// dp[c] 存第 (0,0) 到 第 (r,c) 条不同路径数
// 
// -----------------------------------------------------------------------------
// 2) Transition / 状态转移
// -----------------------------------------------------------------------------
// 
// 1. If grid[r][c] === 1 => this cell is blocked => no path ends here => dp[c] = 0
// 2. Else if (r,c) is the start (0,0) => exactly one path (do nothing) => dp[c] = 1
// 3. Otherwise the cell is free:
//    - fromUp = dp[c] is the number of paths coming from the cell above (r-1,c)
//      (stored in the old value of dp[c]) 
//    - fromLeft = dp[c-1] is the number of paths from the left neighbour (r,c-1)
//      (already updated to the curent row's value)
//    - One step down would reach (r,c) for each path to (r-1,c)
//      So does one step right, for each path to (r,c-1), giving a unique path to (r,c)
//      without duplicate(s) 
//      thus: dp[c] = fromUp + fromLeft
//
// 1. 如果 grid[r][c] === 1 => 这格是障碍 => 路不到这 => dp[c] = 0
// 2. 不然如果 (r,c) 为 起点 (0,0) => 恰好一条路 (哪都不走) => dp[c] = 1
// 3. 否则这一格能走：
//    - fromUp = dp[c] 是 (r-1,c) 上面的格子的路径数 (存到 dp[c] 之前的值中)
//    - fromLeft = dp[c-1] 是左邻格 (r,c-1) 的路径数（已经更新为当前行的值）
//    - 到 (r-1,c) 的每条路径，下移一步就到 (r,c)
//      到 (r,c-1) 的每条路径，右移一步也到 (r,c)，说明到 (r,c) 路径唯一，不重复 
//      因而：dp[c] = fromUp + fromLeft
//
// -----------------------------------------------------------------------------
// 3) Why 1D array would work / 1D 数组怎么就能用？
// -----------------------------------------------------------------------------
//  
// 1. It has 2D formula ways[r][c] = ways[r-1][c] + ways[r][c-1], for each row r，
//    processing current row r, we only need:
//    - the previous row's value at column c -> old dp[c]
//    - the current row's left neighbour at column c-1 -> new dp[c-1]
//      So a single row dp[] is enough
// 
// 1. 二维公式是 ways[r][c] = ways[r-1][c] + ways[r][c-1], 处理当前行 r ，只需要：
//    - 第 c 排，前一排的值 -> 之前的 dp[c]
//    - 第 c-1 排，当前排的左格 -> 现在的 dp[c-1]
//      所以就一排 dp[] 足够了

function findAllpathsBFS(grid: number[][]): number {
    
}
