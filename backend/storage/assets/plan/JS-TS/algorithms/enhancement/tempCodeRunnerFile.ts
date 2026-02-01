
function countPathsDebug(grid: number[][]): number {
    const rows = grid.length;
    if (!rows) {
        console.log("empty grid → 0");
        return 0;
    }
    const cols = grid[0]!.length;
    const dp = new Array<number>(cols).fill(0);

    console.log("grid:");
    for (const row of grid) console.log(row.join(" "));

    for (let r = 0; r < rows; r++) {
        console.log(`\n=== row ${r} ===`);
        for (let c = 0; c < cols; c++) {
            if (grid[r]![c] === 1) {
                // 障碍，路径数为 0
                dp[c] = 0;
                console.log(`cell (${r},${c}) = 1 (blocked) → dp[${c}] = 0`);
            } else if (r === 0 && c === 0) {
                // 起点
                dp[c] = 1;
                console.log(`cell (${r},${c}) start → dp[0] = 1`);
            } else {
                const fromUp = dp[c]!;               // 上一行同一列
                const fromLeft = c > 0 ? dp[c - 1]! : 0; // 当前行左边
                dp[c] = fromUp + fromLeft;
                console.log(
                    `cell (${r},${c}) = 0, fromUp=${fromUp}, fromLeft=${fromLeft} → dp[${c}] = ${dp[c]}`
                );
            }
        }
        console.log(`row ${r} done, dp = [${dp.join(", ")}]`);
    }

    console.log(`\nresult (paths to bottom-right) = ${dp[cols - 1]}`);
    return dp[cols - 1]!;
}

// 你的示例：
const grid = [
    [0, 0, 0, 0, 1, 0],
    [1, 0, 0, 0, 0, 0],
    [1, 1, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0],
];

countPathsDebug(grid);