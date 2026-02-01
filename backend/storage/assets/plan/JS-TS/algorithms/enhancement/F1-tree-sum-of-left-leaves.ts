// F1. 二叉树所有左叶子之和（树）
// F1. Sum of all left leaves in a binary tree (tree)

// 给定一棵二叉树的根节点 root，
// 请计算并返回这棵树中所有“左叶子节点”的节点值之和。
// 左叶子：是某个节点的 left 子节点，且该子节点没有任何子节点。

// Given the root of a binary tree root,
// compute and return the sum of all left leaf nodes in the tree.
// A left leaf is a node that is the left child of its parent and has no children itself.

// 示例（描述）：
// 若一棵树的左叶子节点值分别为 2 和 4，则返回 6。
// Example (description):
// If a tree has left leaves with values 2 and 4, the function should return 6.

interface TreeNode {
    val: number;
    left: TreeNode | null;
    right: TreeNode | null;
}

function sumLeftLeaf(root: TreeNode | null): number {

    // if the tree has no leaves at all, return 0
    if (root === null) return 0;

     let sum = 0;

    // Here's the definition of left leaf (try to sketch it):
    if (root.left !== null && 
        root.left.left === null &&
        root.left.right === null
    ) {
        
        sum +=  root.left.val
    }

    // Iterator"s": both left and right nodes may share a left leave!
    const leftSum = sumLeftLeaf(root.left);
    const rightSum = sumLeftLeaf(root.right);

return leftSum + rightSum + sum;

}

const tree1 = {
    val: 1,
    left: {val: 2, left: null, right: null},
    right: null
}

const tree2 = {
    val: 3,
    left: {val: 4, left: null, 
        right: {val: 5, left: null, right: 
            {val: 3, left: {val: 3, left: null, right: null}, right: null}}},
    right: null
}

console.log(sumLeftLeaf(tree1));
console.log(sumLeftLeaf(tree2));
