// 题 8：二叉树的最大深度
// 定义二叉树节点：x
// 实现函数 maxDepth(root: TreeNode | null): number，返回树的最大深度（根节点深度为 1）。
// - 示例：只有一个根节点 → 返回 1
// - 示例：根 → 左 → 左，共三层 → 返回 3。

interface TreeNode {
  val: number;
  left: TreeNode | null;
  right: TreeNode | null;
}

/**
 * 返回二叉树的最大深度（根节点深度为 1）
 */

function maxDepth(root: TreeNode | null): number {
    if (root === null) {
        return 0;
    } else {
    const leftDepth = maxDepth(root.left);
    const rightDepth = maxDepth(root.right);
    
// Q&A1 - Be careful of + 1； without it, it cannot form an iterator;
    return Math.max(leftDepth, rightDepth) + 1;
}

}

// self-test
const tree1: TreeNode = {
    val: 1,
    left: {val: 1, left: null, right: null},
    right: null,
};

console.log(maxDepth(tree1));

const tree2: TreeNode = {
    val: 5,
    left: {val: 3, left: {val: 2, left: null, right: null}, right: null},
    right: {val: 3, left: {val: 2, left: null, right: null}, right: null},
}

console.log(maxDepth(tree2));
