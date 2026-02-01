// F2. 二叉树层序遍历（树 + 队列 BFS）
// F2. Binary tree level-order traversal (tree + queue BFS)

// 给定一棵二叉树的根节点 root，按层从上到下，从左到右返回每一层的节点值。
// Given the root of a binary tree, return the node values level by level
// from top to bottom and from left to right.

// - 输入：root = [3,9,20,null,null,15,7]
// - 输出：[[3],[9,20],[15,7]]
// - Input:  root = [3,9,20,null,null,15,7]
// - Output: [[3],[9,20],[15,7]]

interface TreeNode {
    val: number;
    left: TreeNode | null;
    right: TreeNode | null; 
}

function levelOrder(root: TreeNode | null): number[][] {

    if (root === null) return [];
    
    const results: number[][] = [];
    const queue: TreeNode[]  = [root];

    while (queue.length > 0) {
        const levelSize = queue.length;
        const level: number[] = [];

        for (let i = 0; i < levelSize; i++) {
            const node = queue.shift()!;
            level.push(node.val);

            if (node.left !== null) queue.push(node.left);
            if (node.right !== null) queue.push(node.right);
        }
        results.push(level);
    }
    return results;
}

const tree1: TreeNode = {
    val: 4,
    left: {val: 6, left: null, right: {val: 7, left: null, right: null}},
    right: {val: 9, left: null, right: null},
}

console.log(levelOrder(tree1));

// 
// -----------------------------------------------------------------------------
// 0) Recursive DFS
// -----------------------------------------------------------------------------
// 

function levelOrderDFS(root: TreeNode | null): number[][] {

// 1. result: number[][] = []
//    - result[0] goes for level 0 (root)
//    - result[1], level 1
//    - result[2], level 2 ...
// 1. result: number[][] = []
//    - result[0] 放第 0 层（根）
//    - result[1] 放第 1 层
//    - result[2] 放第 2 层 ...
    const result: number[][] = [];

// 2. Recursive function
//    - node:  current node
//    - level: depth of this node
// 2. 递归函数
//    - 节点：当前节点
//    - 层级：该节点的深度

    function dfs(node: TreeNode | null, level: number) {

// 3. 在 dfs 里做三件事：
//    - 若 node === null，直接返回（叶子下面的空指针）
//    - 若这是第一次到达这一层 (result[level] 还是 undefined) 先建一个空数组：
//      result[level] = []
//    - 把当前节点的值推进去：result[level].push(node.val)
//    - 递归到左右子树，level +1：
//      - dfs(node.left, level + 1)
//      - dfs(node.right, level + 1)
// 3. Inside dfs:
//    - If node === null, return it directly.
//    - If this is the first time we reach this level (result[level] is undefined),
//      initialize it: result[level] = []
//    - Push the current value: result[level].push(node.val)
//    - Recurse to children with level + 1:
//      - dfs(node.left, level + 1)
//      - dfs(node.right, level + 1)

    if (node === null) return;

    if (result[level] === undefined) {
        result[level] = [];
    }
    result[level].push(node.val);

    dfs(node.left, level + 1);
    dfs(node.right, level + 1);
}
    dfs(root, 0);

// 4. Call from dfs(root, 0) because the root is at level 0
// 4. 从根开始调用，因为根在第 0 层


    return result;
}

// 5. Self-test
// 5. 自测

const Tree1: TreeNode = {
    val: 4,
    left: {val: 6, left: null, right: {val: 7, left: null, right: null}},
    right: {val: 9, left: null, right: null},
}

console.log(levelOrder(Tree1));

// 6. Complexity
//    - Time: O(n) (each node is visited once)
//    - Space: O(h) recursive queue with height of h (O(n) at worst)
// 6. 复杂度
//    - 时间：O(n)（每个节点访问一次）
//    - 空间：O(h) 递归栈，h 为树高 (最坏 O(n))

// 
// -----------------------------------------------------------------------------
// 1) Practice / 练习 - Recursive DFS
// -----------------------------------------------------------------------------
// 

interface TreeNode {
    val: number;
    left: TreeNode | null;
    right: TreeNode | null; 
}

function levelOrderDFS2(root: TreeNode | null): number[][] {
    
    const results: number[][] = [];
    DFS(root, 0);
    return results;

    function DFS(node: TreeNode | null, level: number) {

        if (node === null) return []
        // create an empty array (marked as level, e.g.，0)
        if (results[level] === undefined) results[level] = [];

        results[level].push(node.val);

        if (node.left !== null) DFS(node.left, level + 1);
        if (node.right !== null) DFS(node.right, level + 1);
    }
}

const TREE1: TreeNode = {
    val: 10,
    left: {val: 15, left: null, right: null},
    right: {val: 30, left:{val: 45, left: null, right: null}, right: null}
}

console.log(levelOrderDFS2(TREE1));

// 
// -----------------------------------------------------------------------------
// 2) Practice / 练习 - BFS with stack
// -----------------------------------------------------------------------------
// 

interface TreeNode {
    val: number;
    left: TreeNode | null;
    right: TreeNode | null; 
}

function levelOrderStack(root: TreeNode | null): number[][] {

    if (root === null) return [];

    const queue: TreeNode[] = [root];
    const results: number[][] = [];

    while (queue.length > 0) {
        // decides how many times the loop will happen
        const levelSize = queue.length;
        // gives a container for the number(s) in a level
        const level: number[] = [];

        for (let i = 0; i < levelSize; i++) {
            const node = queue.shift()!;
            level.push(node.val);

            if (node.left !== null) queue.push(node.left);
            if (node.right !==null) queue.push(node.right);
        }
        results.push(level);
    }
    return results;
}

const TREE2: TreeNode = {
    val: 10,
    left: {val: 15, left: null, right: null},
    right: {val: 30, left:{val: 45, left: null, right: null}, right: null}
}
const TREE3: TreeNode = {
  val: 1,
  left: {
    val: 2,
    left: { val: 4, left: null, right: null },
    right:{ val: 5, left: null, right: null }
  },
  right:{
    val: 3,
    left: { val: 6, left: null, right: null },
    right:{ val: 7, left: null, right: null }
  }
};

console.log(levelOrderStack(TREE2));
console.log(levelOrderStack(TREE3));
// 
// -----------------------------------------------------------------------------
// 3) Practice / 练习 - DFS with stack
// -----------------------------------------------------------------------------
// 

function levelOrderWithStack(root: TreeNode | null): number[][] {
    if (root === null) return [];

    const results: number[][] = [];
    const stack: {node: TreeNode; level: number}[] = [
        {node: root, level: 0},
    ];

    while (stack.length > 0) {
        const { node, level } = stack.pop()!;

        if (!results[level]) results[level] = [];
        results[level].push(node.val);

        if (node.right) stack.push({node: node.right, level: level + 1})
        if (node.left) stack.push({node: node.left, level: level + 1})
    }

    return results;
}

const TREE4: TreeNode = {
  val: 1,
  left: {
    val: 2,
    left: { val: 4, left: null, right: null },
    right:{ val: 5, left: null, right: null }
  },
  right:{
    val: 3,
    left: { val: 6, left: null, right: null },
    right:{ val: 7, left: null, right: null }
  }
};

console.log(levelOrderWithStack(TREE4));