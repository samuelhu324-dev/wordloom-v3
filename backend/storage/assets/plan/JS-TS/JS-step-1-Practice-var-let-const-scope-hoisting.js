// JS Step 1 Practice: var / let / const, scope and hoisting.
// 单行注释用 // 开头
/* 多行注释可以用  斜杠+星号  包裹
   这里写的内容都不会被当成代码执行
*/

// ========== 练习 1：作用域判断 ==========
// 题目：预测每一行 console.log 的结果（或报什么错），然后运行验证。

function test() {
  if (true) {
    var x = 1;
    let y = 2;
    const z = 3;
  }

  // 这里是正确答案：
  // x 在函数作用域内可见（var），所以输出 1
  console.log('x:', x); // x: 1

  // y / z 是块级作用域（let / const），出了 if 的 {} 就不可见
  // 访问时会抛 ReferenceError: y is not defined
  // 这行一报错，后面的语句就不会执行
  console.log('y:', y); // ReferenceError
  console.log('z:', z); // 不会执行
}

 test(); 


// ========== 练习 2：提升 & 暂时性死区（TDZ） ==========
// 题目：预测每一行 console.log 的结果（或错误类型）。

// 正确答案：
// a 使用 var 声明，会被“提升”，在这里已经存在但值是 undefined
console.log('a before declaration:', a); // undefined

// b 使用 let 声明，同样被提升，但处于 TDZ，访问会抛 ReferenceError
console.log('b before declaration:', b); // ReferenceError: Cannot access 'b' before initialization

var a = 10;
let b = 20;


// ========== 练习 3：选择合适的声明方式 ==========
// 原始代码：
// var count = 0;
// var MAX = 10;
// for (var i = 0; i < MAX; i++) {
//   count += i;
// }
// var result = { total: count };

// 改写后的更合理写法：
// 解释：
// - count 会在循环中被多次重新赋值，所以用 let；
// - MAX 是一个不会改变的常量，用 const；
// - i 只在 for 的块级作用域里使用，用 let；
// - result 这个引用创建后不会被重新赋值，用 const。

let count = 0;
const MAX = 10;

for (let i = 0; i < MAX; i++) {
  count += i;
}

const result = { total: count };
console.log('result:', result); // { total: 45 } （0+1+...+9）