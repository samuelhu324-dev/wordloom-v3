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