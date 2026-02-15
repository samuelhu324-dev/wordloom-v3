1）基础知识怎么补？我先给你一份「JS/TS 基础问答清单」，你之后可以逐条来问。

# A. JavaScript 基础（面试高频，附简短答案）
- [x]  1. var / let / const 区别？
  - var 函数作用域 + 提升 + 可重复声明；
  - let 块级作用域 + 不提升到可用 + 不可重复声明；
  - const 同 let，但绑定的引用不可重新赋值（对象本身可改）。

- [x] 2. == 和 === 区别？
  - == 会做类型转换再比较；
  - === 不做类型转换，类型和值都相等才为真；面试/实战几乎只用 ===。

- [x] 3. 什么是“truthy / falsy”？常见 falsy 有哪些？
  - 在需要布尔值的上下文中，会被当成 true / false 的非布尔值；
  - falsy：false, 0, -0, '', null, undefined, NaN。

- [x] 4. 数组常用方法：map / filter / reduce 分别干什么？
  - map：一一映射，返回新数组；
  - filter：按条件保留元素，返回子数组；
  - reduce：累积计算，返回一个值（或对象/数组）。

- [x] 5. 浅拷贝 vs 深拷贝？常见浅拷贝方式？
  - 浅拷贝：只复制第一层引用，内层对象仍共享；
  - 深拷贝：嵌套对象也新建一份；
  - 常见浅拷贝：{...obj}、Array.from(arr)、arr.slice()、Object.assign({}, obj)。

- [x] 6. 什么是闭包（closure）？有什么用？
  - 函数可以“记住”并访问其词法作用域中的变量，即使函数在定义环境之外执行；
  - 用途：封装私有变量、实现函数工厂、实现 once/debounce 等。

- [x] 7. 箭头函数和普通函数的 this 有什么区别？
  - 普通函数的 this 由调用方式决定；
  - 箭头函数没有自己的 this，会捕获定义时外层的 this；
  - 不能用作构造函数，也没有 arguments。

- [x] 8. 事件循环 / 微任务 / 宏任务 简单说？
  - JS 是单线程，通过事件循环调度任务；
  - 宏任务：setTimeout、DOM 事件、I/O；
  - 微任务：Promise.then、queueMicroxtask；
  - 一轮事件循环：执行当前宏任务 → 执行所有微任务 → 渲染。

- [x] 9. Promise 三个状态？async/await 是什么？
  - 状态：pending / fulfilled / rejected；
  - async 函数总是返回 Promise；
  - await 等待 Promise resolve/reject，相当于把 then 写成同步风格，需要 try/catch 处理异常。

- [x] 10. 原型链简单解释一下？
  - 对象访问属性时，如果自身没有，就从其 [[Prototype]]（__proto__）找；
  - 一直沿着原型链向上，直到 Object.prototype 或 null；
  - 函数的 prototype 属性决定了 new 出来的实例的原型。

# B. TypeScript 基础（前端岗位加分）

- [x] 11. TS常用基本类型有哪些？
  - string, number, boolean, null, undefined, void, any, unknown, never, object 以及数组、元组、枚举、函数类型等。

- [x] 12. any 和 unknown 区别？
  - any：关闭类型检查，什么都可以做；
  - unknown：什么值都能赋给它，但在使用前必须先做类型缩窄；更安全。

- [x] 13. interface 和 type 区别？
  - 都能描述对象形状；interface 支持 extends 和声明合并；
  - type 可以是联合、交叉、条件类型等更复杂别名；
  - 实战中两者混用，但一般：公开结构用 interface，复杂组合用 type。

- [x] 14. 什么是联合类型 / 交叉类型？
  - 联合：A | B，取其一；
  - 交叉：A & B，两个都要（合并属性）。

- [x] 15. 泛型（generics）是做什么的？
  - 给类型加参数，使函数/组件在保持类型安全的同时对多种类型复用；
  - 例如：function identity<T>(value: T): T { return value; }。
