// JS Step 5 Practice: 事件循环 / 宏任务 / 微任务
// 建议：每一小题先在脑子里写出“日志输出顺序”，再运行 node 看结果。

console.log('--- Exercise 1: setTimeout vs Promise ---');

console.log('1-start');

setTimeout(() => {
  console.log('1-timeout');
}, 0);

Promise.resolve().then(() => {
  console.log('1-promise-then');
});

console.log('1-end');


// ========== Exercise 2 ==========
// 问：下面这段输出顺序是什么？先自己写在注释里，再运行验证。

console.log('\n--- Exercise 2: 多个微任务 ---');

console.log('2-start');

Promise.resolve().then(() => {
  console.log('2-then-1');
});

Promise.resolve().then(() => {
  console.log('2-then-2');
});

console.log('2-end');


// ========== Exercise 3 ==========
// 问：输出顺序？注意：then 里面又写了 setTimeout。

console.log('\n--- Exercise 3: 微任务里再注册宏任务 ---');

console.log('3-start');

setTimeout(() => {
  console.log('3-timeout-1');
}, 0);

Promise.resolve().then(() => {
  console.log('3-then');

  setTimeout(() => {
    console.log('3-timeout-2');
  }, 0);
});

console.log('3-end');


// ========== Exercise 4 ==========
// 问：输出顺序？特别注意：then 链的执行时机。

console.log('\n--- Exercise 4: then 链 ---');

console.log('4-start');

Promise.resolve()
  .then(() => {
    console.log('4-then-1');
  })
  .then(() => {
    console.log('4-then-2');
  });

setTimeout(() => {
  console.log('4-timeout');
}, 0);

console.log('4-end');


// ========== Extra：自己加题 ==========
// 1）试着加上 queueMicrotask(() => console.log('micro'))，观察它和 Promise.then 的顺序。
// 2）自己设计一段：混合多个 setTimeout、Promise.then，预测日志顺序，再运行验证。