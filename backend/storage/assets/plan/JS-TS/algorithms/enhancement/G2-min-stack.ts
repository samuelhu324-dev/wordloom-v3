// G2. Min stack (support O(1) getMin)
// G2. 最小栈（支持 O(1) 时间获取最小值）

// Design a stack that supports push, pop, top and getMin in O(1) time.
// 设计一个支持 push、pop、top 和 getMin 的栈。
// getMin 应该在常数时间内返回当前栈中的最小值。

// ----------------------------------------------------------------------------- 
// 1) idea / 思路
// -----------------------------------------------------------------------------
// 
// 1. We want all operations in O(1) time.
//    A single normal stack cannot do getMin() in O(1) because we'd 
//    have to scan all elements.
// 
// 2. So we maintain two stacks:
//    - stack: store all values in normal stack order
//    - minStack: stores the history of minimum values; 
//      its top is always the current minimum
// 
// 3. Operations: 
//    - push(x)
//      - stack.push(x)
//      - and if minStack is empty or x <= currentMin, then x becomes
//        the new (or equal) minimum -> minStack.push(x)
//    - pop()
//      - v = stack.pop()
//      - If v === top(minStack), then we've just removed the current minimum ->
//        also minStack.pop() to roll back to the previous minimum
//     - top()
//       - Return top(stack)
//     - getMin()
//       - Return top(minStack)
//  
//  4. Each operation touches only a constant number of elements 
//     (array tail operations), so:
//     - Time: O(1) per operation
//     - Extra space: O(n) for the additional minStack
//
// 1. 我们想所有运算在 O(1) 时间里算完
//    所以仅仅一个普通的栈无法在 O(1) 做到 getMin()，因为得去扫描所有元素
//
// 2. 我们就维护两个栈：
//    - stack：以普通栈的顺序存所有的值
//    - minStack: 存最小值的状况 / 存最小值的历史
//      栈顶都是当前的最小值
//
// 3. 运算：
//    - push(x)
//      - 先 stack.push(x)
//      - 如果 minStack 为空或者 x <= currentMin，x 再另作或同为最小值 
//        -> minStack.push(x)
//    - pop()
//      - v = stack.pop()
//      - 如果 v === minStack 的栈顶，那么刚移除的是当前最小值 ->
//        也 minStack.pop() (弹出) 回滚到之前的最小值
//    - top()
//      - 返回 top(stack)
//    - getMin()
//      - 返回 top(minStack)
//
// 4. 每个运算仅触及常数多个元素 (数组尾部运算):
//    - 时间：每个运算就 O(1)
//    - 额外空间：再算 minStack就 O(n)

class MinStack {
    private stack: number[] = [];
    private minStack: number[] = [];

    constructor() {}

    push(x: number): void {
        this.stack.push(x);
        if (this.minStack.length === 0 || x <= this.minStack[this.minStack.length - 1]!) {
            this.minStack.push(x);
        }
    };

    pop(): void {
        if (this.stack.length === 0) return;
        const v = this.stack.pop()!;
        if (this.minStack.length && v === this.minStack[this.minStack.length - 1]!) {
            this.minStack.pop();
        }
    };

    top(): number | undefined {
        if (this.stack.length === 0) return undefined;
        return this.stack[this.stack.length - 1];
    };

    getMin(): number | undefined {
        if (this.minStack.length === 0) return undefined;
        return this.minStack[this.minStack.length - 1];
    };
}

function createMinStack() {
    const stack: number[] = [];
    const minStack: number[] = [];

    return {
        // Push onto the stack / 压栈
        push(x: number): void {
            stack.push(x);
            if (minStack.length === 0 || x <= minStack[minStack.length - 1]!) {
                minStack.push(x);
            }
        },

        // pop from the stack / 出栈
        pop(): void {
            if (stack.length === 0) return;
            const v = stack.pop()!;
            if (minStack.length === 0 && v === minStack[minStack.length - 1]!) {
                minStack.pop();
            }
        },

        top(): number | undefined {
            if (stack.length === 0) return undefined;
            return stack[stack.length - 1];
        },

        getMin(): number | undefined {
            if (minStack.length === 0) return undefined;
            return minStack[minStack.length - 1];
        },
    };
}

// 5. Self-test
// 5. 自测

const s1 = createMinStack();
s1.push(5);
s1.push(3);
s1.push(7);
console.log(s1.top());    // stack: [5,3,7] => 7
console.log(s1.getMin()); // minStack: [5,3] => 3
s1.pop();                 // stack: [5,3,7] => [5,3], minStack [5,3] 
console.log(s1.getMin()); // minStack: [5,3] => 3




function mergeTwoIntervalListsOnePass(
  a: Array<[number, number]>,
  b: Array<[number, number]>
): Array<[number, number]> {
  const res: Array<[number, number]> = [];
  let i = 0;
  let j = 0;

  const pickNext = (): [number, number] | undefined => {
    if (i < a.length && j < b.length) {
      if (a[i]![0] <= b[j]![0]) return a[i++]!;
      return b[j++]!;
    }
    if (i < a.length) return a[i++]!;
    if (j < b.length) return b[j++]!;
    return undefined;
  };

  while (true) {
    const next = pickNext();
    if (!next) break;

    const [s, e] = next;
    if (!res.length || res[res.length - 1]![1] < s) {
      // no overlap, start a new interval
      res.push([s, e]);
    } else {
      // overlap, merge with the last interval
      res[res.length - 1]![1] = Math.max(res[res.length - 1]![1], e);
    }
  }
  return res;
}
