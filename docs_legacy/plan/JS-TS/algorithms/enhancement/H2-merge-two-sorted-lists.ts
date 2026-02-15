// H2. Merge two sorted linked lists
// H2. 合并两个有序链表

// Given two sorted linked lists l1 and l2, merge them into a single sorted list
// and return the head of the new list.
// 给定两个升序排列的链表 l1 和 l2，将它们合并为一个新的升序链表并返回新链表的头节点。

interface ListNode {
    val: number;
    next: ListNode | null;
}

// -----------------------------------------------------------------------------
// 1) idea / 思路
// -----------------------------------------------------------------------------

// Goal: merge two ascending lists l1 and l2 into a new ascending list
// 目标：把两个升序链表 l1 、 l2 合并成一个新的升序链表

function mergedTwoSortedLists(l1: ListNode | null, l2: ListNode | null): ListNode | null {
//       1. Create a dummy node (value arbitrary, e.g. 0)
//          - dummy.next will become the head of the merged list
//      1. 创建一个哑节点（值任意，如 0）
//         - dummy.next 以后会成为合并链表的头部

    const dummy: ListNode = {val: 0, next: null};
    let curr = dummy;

//       2. Use three pointers:
//          - p1: traverses l1
//          - p2: traverses l2
//          - curr: tail of the merged list, initially pointing to dummy
//      2. 使用三个指针：
//         - p1：遍历 l1
//         - p2：遍历 l2
//         - curr: 合并链表的尾部，起初指向 dummy

    let p1 = l1;
    let p2 = l2;

//       3. While both p1 and p2 are non-null:
//          - Compare p1.val and p2.val
//          - Attach the smaller node to curr.next
//          - Advance p1 or p2 accordingly
//          - Move curr to the node just attached (the new tail)

//      3. p1 和 p2 都为非空的话：
//         - 比较 p1.val 和 p2.val
//         - 把较小的节点接到 curr.next
//         - 相应前进 p1 或 p2
//         - 把 curr 移到 刚刚接到的 node 上（新的尾部）

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

// 4. After the loop, at most one list has remaining nodes:
//    - Do curr.next = (p1 !== null ? p1 : p2) to append the whole remaining part
// 5. Return dummy.next as the head of the merged list 
//    (skipping the dummy node itself)
// 4. 循环后，最多就一个链表有剩余节点：
//    - 把 curr.next = (p1 !== null ? p1 : p2) 附在整个剩余部分
// 5. 把 dummy.next 返回成合并链表的头部
//    (跳过哑变量剩余节点本身)

    curr.next = p1 !== null ? p1 : p2;
    return dummy.next;
}

// 6. Self-test
// 6. 自测

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

printList(mergedTwoSortedLists(list1, list2)); // 1 -> 2 -> 3 -> 4 -> 4 -> 5 -> 6 -> 7

// -----------------------------------------------------------------------------
// 2) Complexity / 复杂度
// -----------------------------------------------------------------------------

// Time: O(m + n) - each node is visited once
// Space: O(1) - only pointer reassignments, no new nodes except the dummy
// 时间：O(m + n) - 每个节点访问一次
// 空间：O(1) - 只有指针重新赋值，除 dummy 无新节点
