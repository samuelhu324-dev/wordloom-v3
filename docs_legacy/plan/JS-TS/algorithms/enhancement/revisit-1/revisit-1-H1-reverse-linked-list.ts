// H1. Reverse singly linked list (iterative)
// H1. 反转单链表（迭代）

// Given the head of a singly linked list, reverse the list and return the new head.
// 给定单链表的头节点 head，反转链表并返回新的头节点。

// Example:
// - Input: head = 1 -> 2 -> 3 -> 4 -> 5 -> null
// - Output：5 -> 4 -> 3 -> 2 -> 1 -> null

// - Input: head = 7 -> null
// - Output: 7 -> null

interface ListNode {
    val: number;
    next: ListNode | null;
}

function reverseList(head: ListNode | null): ListNode | null {
    
    if (head === null) return null;

    let prev: ListNode | null = null;
    let curr: ListNode | null = head;

    while (curr !== null) {
        const next: ListNode | null = curr.next;  // then 10 -> 15 -> null will be preserved
        curr.next = prev;        // curr.next = null; thus, curr = 5 -> null
        prev = curr;             // prev = 5 -> null;
        curr = next;             // curr = 10 -> 15 -> null；
    }

    return prev;
}

const list1: ListNode = {
    val: 5,
    next: {val: 10, next: 
        {val: 15, next: null}},
}

console.log(reverseList(list1));

