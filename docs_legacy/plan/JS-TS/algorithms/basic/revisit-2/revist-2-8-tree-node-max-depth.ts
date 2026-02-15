// 题 8：二叉树的最大深度
// Problem 8: Maximum depth of a binary tree

// 定义二叉树节点：x
// Define the binary tree node: x

// 实现函数 maxDepth(root: TreeNode | null): number，返回树的最大深度（根节点深度为 1）。
// Implement a function maxDepth(root: TreeNode | null): number that returns

// - 示例：只有一个根节点 → 返回 1
// - 示例：根 → 左 → 左，共三层 → 返回 3。、
// - Example: only a root node → return 1
// - Example: root → left → left (three levels) → return 3.

// 1) 思路 | Idea:
// 1. 一句话：一棵树的最大深度 = 1 + max (左子树最大深度，右子树最大深度)
// 1. In one sentence: the max dpeth of a tree 
// = 1 + max (max depth of left subtree, max depth of right subtree)

interface TreeNode {
  val: number;
  left: TreeNode | null;
  right: TreeNode | null;
}

// 2) 递归情况 | Recursive case
// 1. 当前根节点 root :
//   1.1 递归求左子树的最大深度：leftDepth = maxDepth(root.left)；
//   1.2 递归求右子树的最大深度：rightDepth = maxDepth(root.right)；
// 2. 当前这棵树（以 root 为根）的最大深度就是：
//   2.1 1 + Math.max(leftDepth, rightDepth)：
//   2.2 外面 + 1 算再加上当前这一层（根节点）的深度；
// 1. For the current root:
//   1.1 Find left subtree depth recursively: leftDepth = maxDepth(root.left);
//   1.2 Find right subtree depth recursively: rightDepth = maxDepth(root.right);
// 2. The max depth of this tree currently is:
//   2.1 1 + Math.max(leftDepth, rightDepth):
//   2.2 The outer + 1 accounts for the current root level on top.

function MaxDepth(root: TreeNode | null): number {

    if (root === null) {
        return 0;
    }

    const leftDepth = MaxDepth(root.left);
    const rightDepth = MaxDepth(root.right);

// 3) 必须有 + 1 的原因 | Why + 1 is Necessary
// leftDepth / rightDepth 只是子树的深度
// 但我们要的是整棵树（包含当前根）的深度，所以还要算上当前的层
// 以及：没有 + 1 无法形成 null 为 0 和 有值为 + 1 的迭代
// leftDepth / rightDepth is just the depth of subtrees
// but what we need is the depth of the whole tree including the current root
// so it also got to account for the current level
// Still: iterations canot be formed without + 1: null for 0 and any value for + 1 

return Math.max(leftDepth, rightDepth) + 1;

}

// 4) 自测：
// 4) Self-test:

const tree1: TreeNode | null = {
    val: 5,
    left: {val: 2, left: null, right: null},
    right: {val: 4, left: null, right:{val: 3, left: null, right: null}}
}

const tree2: TreeNode | null = {
    val: 3,
    left: null,
    right: {val: 3, left: null, right: {val: 1, left: null, right: null}}
}

console.log(MaxDepth(tree1));
console.log(MaxDepth(tree2));

// 5) 练习 | Practice:

interface TreeNode1 {
  val: number;
  left: TreeNode1 | null;
  right: TreeNode1 | null;
}

function MaxDepth2(root: TreeNode1 | null) {
    
    // part of the fundamental iteration: if null, we've got 0
    if (root === null) {
        return 0;
    }

    // another part of the iteration, which consists of the iterator
    // by referencing left and right property in TreeNode.
    const leftDepth: number = MaxDepth2(root.left);
    const rightDepth: number = MaxDepth2(root.right);

// leftDepth / rightDepth must have its own type annotation as number
// rather than Treenode (which cannot be returned, dead loop.)
// + 1 means "make iterator really useful", 
// where you'll see the change of result for the root number
return Math.max(leftDepth, rightDepth) + 1;

}

// Note: comma(s) would be needed to separate const's elements

const tree3: TreeNode1 = {
    val: 4,
    left: {val: 1, left: {val: 2, left: null, right: null}, right: null},
    right: null
}

const tree4: TreeNode1 = {
    val: 6,
    left: {val: 1, left: null, right: null },
    right: {val: 2, left: {val: 3, left: null, right: null}, right: null}
}

// test

console.log(MaxDepth2(tree3));
console.log(MaxDepth2(tree4));