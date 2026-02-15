// JS Step 2 Practice: function, closure, this, arrow function.

/*
  本文件结构：
  - 练习 1：闭包基础（计数器）
  - 练习 2：闭包 + 参数（makeAdder）
  - 练习 3：this & 普通函数 vs 箭头函数
  每个练习都有“题目说明 + 正确答案注释”，你可以先读题目，再看答案。
*/


// ========== 练习 1：闭包基础：计数器 ==========
// 题目：实现一个 makeCounter 函数，每次调用返回的函数时，内部计数 +1。

function makeCounter() {
  // TODO: 在这里声明一个内部计数变量，并返回一个函数
  let count = 0;

  return function () {
    count += 1;
    console.log('current count:', count);
    return count;
  };
}


// 正确答案示例：
// const counterA = makeCounter();
// counterA(); // 1
// counterA(); // 2
// counterA(); // 3
// const counterB = makeCounter();
// counterB(); // 1  （与 A 独立）


// 为了方便你直接看到效果，这里实际调用一遍：
console.log('--- Exercise 1: counter ---');
const counterA = makeCounter();
counterA(); // 1
counterA(); // 2
counterA(); // 3


// ========== 练习 2：闭包 + 参数：makeAdder ==========
// 题目：实现 makeAdder(base)，返回一个函数，该函数接收一个数 n，返回 base + n。

function makeAdder(base) {
  return function (n) {
    return base + n;
  };
}


// 正确答案示例：
console.log('--- Exercise 2: makeAdder ---');
const add5 = makeAdder(5);
const add10 = makeAdder(10);

console.log(add5(2));  // 7
console.log(add5(10)); // 15
console.log(add10(3)); // 13


// ========== 练习 3：this & 普通函数 vs 箭头函数 ==========
// 题目：读代码，思考每一行 console.log 打印什么，然后运行验证。

console.log('--- Exercise 3: this ---');

const obj = {
  name: 'Wordloom',
  normalFn: function () {
    console.log('normalFn this.name =', this.name);
  },
  arrowFn: () => {
    console.log('arrowFn this.name =', this.name);
  },
};


obj.normalFn(); // normalFn this.name = 'Wordloom'
// 解释：作为 obj 的方法被调用，this === obj

obj.arrowFn();  // arrowFn this.name = ??? 这里通常是 undefined
// 解释：arrowFn 的 this 不指向 obj，而是定义时外层作用域的 this
// 在 Node.js 顶层运行时，外层 this 通常是一个空对象 {}，没有 name 属性 → 打印 undefined



// ========== 练习 3 延伸：this 丢失的问题 ==========
// 题目：下面这段代码中，调用 standaloneNormal() 和 standaloneArrow() 会打印什么？为什么？

const obj2 = {
  name: 'Library',
  normalFn() {
    console.log('obj2.normalFn this.name =', this.name);
  },
  arrowFn: () => {
    console.log('obj2.arrowFn this.name =', this.name);
  },
};

const standaloneNormal = obj2.normalFn;
const standaloneArrow = obj2.arrowFn;

console.log('--- Exercise 3 extra: this lost ---');
obj2.normalFn();       // this === obj2 → 打印 'Library'
standaloneNormal();    // this 不再是 obj2 → 在严格模式下是 undefined → 打印 undefined

obj2.arrowFn();        // 和前面一样，this 是外层 → 通常 undefined
standaloneArrow();     // this 仍是外层 → 仍然是 undefined

// 小结：
// - 普通函数方法如果“拆出来单独调用”，this 就丢了（不再指向原来的对象）。
// - 箭头函数的 this 与定义时的外层绑定在一起，无论怎么调用都一样。