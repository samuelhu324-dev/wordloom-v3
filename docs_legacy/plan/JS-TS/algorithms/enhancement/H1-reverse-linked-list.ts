// H1. Reverse singly linked list (iterative)
// H1. 反转单链表（迭代）

// Given the head of a singly linked list, reverse the list and return the new head.
// 给定单链表的头节点 head，反转链表并返回新的头节点。

// Example:
// - Input: head = 1 -> 2 -> 3 -> 4 -> 5 -> null
// - Output：5 -> 4 -> 3 -> 2 -> 1 -> null

// - Input: head = 7 -> null
// - Output: 7 -> null

// -----------------------------------------------------------------------------
// 1) Core idea / 核心想法:
// -----------------------------------------------------------------------------

// Iterate with two pointers and keep "head-inserting" nodes into a new list
// 用两个指针迭代，再把 nodes “从前往后插”到一个新链表中


interface ListNode {
    val: number;
    next: ListNode | null;
}

function ReverseListNode(head: ListNode | null): ListNode | null {

// 1. prev: head of the already reveresed part (starts as null)
// 2. curr: current node being processed (starts from head and moves forward)
// 1. prev: 已经反转的那段链表的头部（先是 null）
// 2. curr: 正在处理的当前节点（头部开始再往后走）

    let prev: ListNode | null = null;
    let curr: ListNode | null = head;

// 3. Each loop does three things: 
//   - const next = curr.next
//     Save the original next node to next 
//     in case that changing pointers will lose the rest of the list
//   - curr.next = prev
//     Point curr.next to prev that already reverses the head of the list
//     Equivalent to "inserting curr to the front of the reversed list" 
//   - prev = curr; curr = next;
//     - Moves prev forward one step: now new head is curr
//     - Moves curr forward one step: continue to process the remaining of the original list
// 3. 每步循环做三件事：const next = curr.next
//   - const next = curr.next
//     先把“原来的下一个节点”保存到 next ，放止等会改指针之后找不到后面的 
//   - curr.next = prev
//     把当前节点 curr 的 next 指针，指向“已反转链表的头 prev”
//     等价于“把 curr 插到新链表的最前面”
//   - prev = curr; curr = next;
//     - prev 前进一步：现在新头部变成当前节点
//     - curr 前进一步：继续处理原链表中剩下的部分

    while (curr !== null) {

        // Ready-to-process Zone
        const next: ListNode | null = curr.next;
        curr.next = prev;

        // Processed Zone
        prev = curr;
        curr = next;
    }

    return prev;
}

// 4. 自测
// 4. Self-test

const List1: ListNode = {
    val: 5,
    next: { val: 10, next: { val: 15, next: null } },
};

console.log(ReverseListNode(List1));

// -----------------------------------------------------------------------------
// 2) Complexity / 复杂度:
// -----------------------------------------------------------------------------
// 1. Time: each node is visited once
// 2. Space: only constant extra pointers are used.
// 1. 时间：O(n)，每个节点只访问一次
// 2. 空间：O(1)，只额外用到常数个指针变量

