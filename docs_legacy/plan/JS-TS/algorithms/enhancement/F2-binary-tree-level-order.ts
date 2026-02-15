// F2. 二叉树层序遍历（树 + 队列 BFS）
// F2. Binary tree level-order traversal (tree + queue BFS)

// 给定一棵二叉树的根节点 root，按层从上到下，从左到右返回每一层的节点值。
// Given the root of a binary tree, return the node values level by level
// from top to bottom and from left to right.

// - 输入：root = [3,9,20,null,null,15,7]
// - 输出：[[3],[9,20],[15,7]]
// - Input:  root = [3,9,20,null,null,15,7]
// - Output: [[3],[9,20],[15,7]]

// 基础定义 / Basic definition
interface TreeNode {
    val: number;
    left: TreeNode | null;
    right: TreeNode | null;
}

// 1) 经典 BFS 版本 / Classic BFS version
function levelOrder(root: TreeNode | null): number[][] {

    if (root === null) return [];

    const result: number[][] = [];
    const queue: TreeNode[] = [root];

    while (queue.length > 0) {
        const levelSize = queue.length;
        const level: number[] = [];

        for (let i = 0; i < levelSize; i++) {
            const node = queue.shift()!;
            level.push(node.val);

            if (node.left !== null) queue.push(node.left);
            if (node.right !== null) queue.push(node.right);
        }
        result.push(level);
    }

    return result;
}

const tree1: TreeNode = {
    val: 2,
    left: {val: 12, left: null, right: null},
    right: {val: 18, left: null, right: null}
}


console.log(levelOrder(tree1));

// -----------------------------------------------------------------------------
// 1) 核心思路 / Core idea:
// -----------------------------------------------------------------------------

// 一句话：
// 用队列做 BFS ，一层一层遍历二叉树，把每一层的节点值收集进一个数组，
// 再把所有层的数组放进 result

// In one sentence:
// Do BFS with a queue to traverse the binary tree level by level,
// collect values of each level into an array, then push each level-array into result.

// -----------------------------------------------------------------------------
// 2) 详细步骤 / Step-by-step:
// -----------------------------------------------------------------------------

interface TreeNode {
    val: number;
    left: TreeNode | null;
    right: TreeNode | null;
}

function levelOrder2(root: TreeNode | null): number[][] {

// 1. 特殊清空 
// 如果 root === null, 直接返回 []
// 1. Edge Case
// If root === null, return [] immediately

    if (root === null) return [];

// 2. 初始化队列和结果
//    - 建一个空数组 result: number[][] = []
//    - 建一个队列 queue: TreeNode[] = [root]，开头只有根节点
// 2. Initialize queue and result
//    - Create an empty array result: number[][] = []    
//    - Create a queue queue: TreeNode[] = [root], starting with the root node.

    const result: number[][] = [];
    const queue: TreeNode[] = [root];

// 3. 外层循环：按层处理
//    - while (queue.length > 0)：只要队列不空，就还有没处理的节点/层
//    - levelSize = queue.length：当前这一层的节点个数
// 
// 3. Outerloop: process by level
//    - while (queue.length > 0): as long as the queue is not empty, 
//      there are still nodes / levels to process.
//    - levelSize = queue.length: the number of nodes at current level

    while (queue.length > 0) {
        const levelSize = queue.length;
        const level: number[] = [];

// 4. 内层循环：处理当前这一层的所有节点 
//    - 循环 levelSize 次，正好把“这一层”的节点全部拿出来处理
//    - 把其值加入 level；
//    - 如果有左 / 右 子节点，就 push 到队列的尾部，作为“下一层”的节点 
// 4. Inner loop: process all nodes in the current level
//    - Loop levelSize times to take out precisely all nodes at this level to process.
//    - Push its value into level.
//    - If it has left / right children, push them into the queue 
//    - as nodes of the next level.

        for (let i = 0; i < levelSize; i++) {
            const node = queue.shift()!; // pop from the front
            level.push(node.val);        // record its value 

            if (node.left !== null) queue.push(node.left);
            if (node.right !== null) queue.push(node.right);
        }

// 5. 处理完这层后
//    - 一层处理完后，level 里的是当前层的所有节点值，把它 push 到 result：
// 5. After finishing this level
//    - After processing the level, level is containing all node value 
//      at this leve; push it into result.

        result.push(level);
    }

// 6. 所有层之后
//    - 当队列空下来时，所有节点和层级都访问了；result 就是最终答案；
// 6. After all levels
//    - When the queue becoems empty, all nodes and levels were visited.
//      result is the final answer.

    return result;
}

const tree2: TreeNode = {
    val: 2,
    left: {val: 12, left: null, right: null},
    right: {val: 18, left: null, right: null}
}

console.log(levelOrder2(tree2));

// -----------------------------------------------------------------------------
// 2) 复杂度 / Complexity:
// -----------------------------------------------------------------------------

// 1. 时间：O(N)，每个节点进队恰好一次、出队恰好一次
// 2. 空间：O(N)，队列在最宽的一层时，可把这一层的所有节点存下

// 1. Time: O(N), each node is enqueued and dequeued exactly once.
// 2. Space: O(N), the queue may hold up to all nodes in the widest level.


// -----------------------------------------------------------------------------
// 3) 练习 / Practice:
// -----------------------------------------------------------------------------

interface TreeNode {
    val: number;
    left: TreeNode | null;
    right: TreeNode | null;
}

function levelOrder3(root: TreeNode | null): number[][] {
    
    // Edge case return an empty array
    if (root === null) return [];
    
    const queue: TreeNode[] = [root];
    const results: number[][] = [];

    while (queue.length > 0) {
        
        const levelSize = queue.length;
        const level: number[] = [];

        for (let i = 0; i < levelSize; i++) {
            const node = queue.shift()!;
            level.push(node.val);

            if (node.right !== null) queue.push(node.right);
            if (node.left !== null) queue.push(node.left);
        }

        // Note: every loop will generate a new level
        results.push(level);

    }

    return results; 
}

const tree3: TreeNode = {
    val: 2,
    left: {val: 12, left: null, right: null},
    right: {val: 18, left: null, right: null}
}

console.log(levelOrder3(tree3));