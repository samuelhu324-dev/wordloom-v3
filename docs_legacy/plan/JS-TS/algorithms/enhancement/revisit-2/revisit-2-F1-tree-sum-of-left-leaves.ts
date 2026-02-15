// F1. Sum of all left leaves in a binary tree (tree)
// F1. 二叉树所有左叶子之和（树）

// Given the root of a binary tree root,
// compute and return the sum of all left leaf nodes in the tree.
// A left leaf is a node that is the left child of its parent and has no children itself.
// 给定一棵二叉树的根节点 root，
// 请计算并返回这棵树中所有“左叶子节点”的节点值之和。
// 左叶子：是某个节点的 left 子节点，且该子节点没有任何子节点。

// Example (description):
// If a tree has left leaves with values 2 and 4, the function should return 6.
// 示例（描述）：
// 若一棵树的左叶子节点值分别为 2 和 4，则返回 6。

// -----------------------------------------------------------------------------
// 1) DFS with recurrsion
// -----------------------------------------------------------------------------

interface TreeNode {
    val: number;
    left: TreeNode | null;
    right: TreeNode | null;
}

function sumLeftLeaves_DFS(root: TreeNode | null): number {

    if (root === null) return 0;

    const sumLeftTree = sumLeftLeaves_DFS(root.left)!;
    const sumRightTree = sumLeftLeaves_DFS(root.right)!;

    if (root.left !== null &&
        root.left.left === null &&
        root.left.right === null
    ) {
        const sum = root.left.val;
        return sum + sumLeftTree + sumRightTree;
    }
    
    return sumLeftTree + sumRightTree;
}

const tree1: TreeNode | null = {
    val: 5,
    left: {val: 3, left: {val: 4, left: null, right: null} ,right: null},
    right: {val: 3, left: {val: 4, left: null, right: null} ,right: null},
}

console.log(sumLeftLeaves_DFS(tree1));

// -----------------------------------------------------------------------------
// 2) BFS with queue (or DFS with stack)
// -----------------------------------------------------------------------------

interface TreeNode {
    val: number;
    left: TreeNode | null;
    right: TreeNode | null;
}

function sumLeftLeaves_BFS(root: TreeNode | null): number {
    
    if (root === null) return 0;
    
    // const stack: TreeNode[] = [root];
    const queue: TreeNode[] = [root];
    let sum = 0;

    // while (stack.length > 0)
    while (queue.length > 0) {
        // const node = stack.pop()!;
        const node = queue.shift()!;

        if (node.left) {
            if (node.left.left === null && node.left.right === null) {
                sum += node.left.val;
            }
            // stack.push(node.left)
            queue.push(node.left);
        }

        if (node.right) {
            // stack.push(node.right)
            queue.push(node.right);
        }

    }

    return sum;
}

const tree2: TreeNode | null = {
    val: 5,
    left: {val: 3, left: {val: 4, left: null, right: null} ,right: null},
    right: {val: 3, left: {val: 4, left: null, right: null} ,right: null},
}

console.log(sumLeftLeaves_BFS(tree2));




