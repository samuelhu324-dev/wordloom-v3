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

// 1) 核心思路 | Core Idea:
// 用递归 (DFS) 算每个当前节点根，可以：
// Using recursion (DFS), for each current node root, do:

interface TreeNode {
    val: number;
    left: TreeNode | null;
    right: TreeNode | null;
}

function sumLeftLeaves(root: TreeNode | null): number {

// 1. 空树：如果 root === null , 子树不存在，所以其分摊的值为 0；
// 1. Empty tree:
// If root === null, the subtree doesn't not exist, so its contribution is 0.

// 2. 检查 root.left 是不是左叶子：
//   2.1 root.left !== null (有一个左子点)
//   2.2 root.left.left === null && root.left.right === null (那个子点一个子点都没有)
//   2.3 如果都成立，我们求出了一个左叶子；把 root.left.val 添加到 sum
// 2. Check whether root.left 是不是左叶子：
//   2.1 root.left! == null (there is a left child)
//   2.2 root.left.left === null && root.left.right === null (that child has no children)
//   2.3 If both hold, we found a left leaf; add root.left.val to sum

    if (root === null) return 0;

    let sum = 0;

    if (root.left !== null && root.left.left === null && root.left.right === null ) {
        sum += root.left.val
    }

// 3. 递归进两树：
//   3.1 左子树里的左叶子和：sumLeftLeaves(root.left)
//   3.2 右子树里的左叶子和：sumLeftLeaves(root.right) 
//   3.3 该节点总的值 = 左叶子可能存在的值 (从尾到头) + 左子树结果 + 右子树结果
// 3. Recurse into both subtrees：
//   3.1 Sum of left leaves in the left subtree: sumLeftLeaves(root.left)
//   3.2 Sum of right leaves in the right subtree: sumRightLeaves(root.right)
//   3.3 Total for this node = possible left-leaf value (from bottom to top) 
//   + left subtree result + right subtree result.

    const sumLeftTree = sumLeftLeaves(root.left);
    const sumRightTree = sumLeftLeaves(root.right);
    return sum + sumLeftTree + sumRightTree;
}

const tree1: TreeNode = {
    val: 1,
    left: {val: 7, left: {val: 3, left: null, right: null},
        right: null},
    right: {val: 2, left: {val: 2, left: null, right: null},
        right: null}
}

const tree2: TreeNode = {
    val: 1,
    left: {val: 7, left: {val: 3, left: {val: 4, left: null, right: null},
     right: null},
        right: null},
    right: null
}

console.log(sumLeftLeaves(tree1));
console.log(sumLeftLeaves(tree2));

// 2) 复杂度 | Complexity:
// 1. 每个节点只被访问一次：
// 2. 每节点作业量为 O(1)；
// 3. 总时间复杂度：O(n), 其中 n 为节点数；
// 4. 额外空间（递归栈）：最坏 O(n)，通常情况下 O(h)，其中 h 为树高
// 1. Each node is visited just once.
// 2. Work per node is O(1)
// 3. The overall time complexity: O(n), where n is the number of nodes
// 4. Extra space (recursion stack): worst O(n), typically O(h), 
// where h is the height of the tree

// 3) 练习 | Practice:

interface TreeNode2 {
    val: number;
    left: TreeNode2 | null;
    right: TreeNode2 | null;
}

function sumLeftLeaves2(root: TreeNode2 | null): number {

    // Note: root has its own type as "TreeNode or null"
    // rather than "number" or "string" or whatever
    if (root === null) return 0;

    let sum = 0;

    // TreeNode cannot work as a built-in type annotation
    // Try to picture a tree according to:
    if (root.left !== null  && 
        root.left.left === null && 
        root.left.right === null) {
        sum += root.left.val;        
    }

    // Bottom-up recursive logic:
    // The recursor will compute the parents' val from their children's
    const sumLeftTree = sumLeftLeaves2(root.left);
    const sumRightTree = sumLeftLeaves2(root.right);
    return sum + sumLeftTree + sumRightTree;
    
}

const tree3: TreeNode2 = {
    val: 1,
    left: {val: 7, left: {val: 3, left: null, right: null},
        right: null},
    right: {val: 2, left: {val: 2, left: null, right: null},
        right: null}
}

const tree4: TreeNode2 = {
    val: 1,
    left: {val: 7, left: {val: 3, left: {val: 4, left: null, right: null},
     right: null},
        right: null},
    right: null
}

console.log(sumLeftLeaves2(tree3));
console.log(sumLeftLeaves2(tree4));