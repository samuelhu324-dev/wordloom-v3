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
