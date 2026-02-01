// H2. Merge two sorted linked lists
// H2. 合并两个有序链表

// Given two sorted linked lists l1 and l2, merge them into a single sorted list
// and return the head of the new list.
// 给定两个升序排列的链表 l1 和 l2，将它们合并为一个新的升序链表并返回新链表的头节点。

interface ListNode {
    val: number;
    next: ListNode | null;
}

function twoSortedLists(l1: ListNode | null, l2: ListNode | null): ListNode | null {
    const dummy: ListNode = {val: 0, next: null};
    let curr = dummy;

    let p1 = l1;
    let p2 = l2;

    while (p1 !== null && p2 !== null) {
        if (p1.val <= p2.val) {
            curr.next = p1;
            p1 = p1.next;
        } else {
            curr.next = p2;
            p2 = p2.next;
        }
        curr = curr.next;
    }
    curr.next = p1 !== null ? p1 : p2;
    return dummy.next;
}

const list1: ListNode | null = {
    val: 1,
    next: {val: 2, next: {val: 3, next: {val: 4, next: null}}}
}

const list2: ListNode | null = {
    val: 4,
    next: {val: 5, next: {val: 6, next: {val: 7, next: null}}}
}

function printList(head: ListNode | null): void {
    const vals: number[] = [];
    while (head) {
        vals.push(head.val);
        head = head.next;
    }
    console.log(vals.join(' -> '));
}

printList(twoSortedLists(list1, list2)); // 1 -> 2 -> 3 -> 4 -> 4 -> 5 -> 6 -> 7