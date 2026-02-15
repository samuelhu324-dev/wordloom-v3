// M4. Graph BFS Template
// M4. 图的 BFS 模板

// Adjacency list representation: graph[node] = array of neighbors
// 邻接表表示的无向 / 有向图：graph[node] = 邻居列表

export function bfsGraph(start: number, graph: number[][]): number[] {
  // Return the order of nodes visited by BFS from start.
  // 返回从 start 出发 BFS 访问的节点顺序。

  const visited = new Set<number>();
  const order: number[] = [];
  const queue: number[] = [];

  queue.push(start);
  visited.add(start);

  while (queue.length > 0) {
    const node = queue.shift()!;
    order.push(node);

    for (const nei of graph[node] ?? []) {
      if (!visited.has(nei)) {
        visited.add(nei);
        queue.push(nei);
      }
    }
  }

  return order;
}
