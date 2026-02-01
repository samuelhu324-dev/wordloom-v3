// F3. 二叉树最大深度（树 + DFS/BFS）
// F3. Maximum depth of a binary tree (tree + DFS/BFS)

// 给定一棵二叉树的根节点 root，返回它的最大深度。
// 最大深度是从根节点到最远叶子节点的节点数量。
// Given the root of a binary tree, return its maximum depth:
// the number of nodes along the longest path from the root to a leaf.

// 示例 / Example:
// Input:  [3,9,20,null,null,15,7]
// Output: 3

export interface TreeNode {
    val: number;
    left: TreeNode | null;
    right: TreeNode | null;
}

// 1) 递归 DFS 版本 / Recursive DFS version
export function maxDepth(root: TreeNode | null): number {
    // TODO: implement recursive DFS
    return 0;
}
