// JS Step 6 Practice: 原型 & 原型链

console.log('--- Exercise 1: 基本原型关系 ---');

const obj = {};
const arr = [];
function fn() {}

console.log('1-obj proto === Object.prototype ?',
  Object.getPrototypeOf(obj) === Object.prototype);

console.log('1-arr proto === Array.prototype ?',
  Object.getPrototypeOf(arr) === Array.prototype);

console.log('1-fn proto === Function.prototype ?',
  Object.getPrototypeOf(fn) === Function.prototype);

console.log('1-Array.prototype proto === Object.prototype ?',
  Object.getPrototypeOf(Array.prototype) === Object.prototype);


// ========== Exercise 2: 属性查找顺序 ==========
// 先在脑中写出每一行的输出，再运行验证。

console.log('\n--- Exercise 2: 原型链上的属性查找 ---');

const parent = { a: 1 };
const child = { b: 2 };

child.__proto__ = parent; // 只用来理解原型

console.log('2-child.a = ?', child.a); // ?
console.log('2-child.b = ?', child.b); // ?
console.log('2-child.c = ?', child.c); // ?


// ========== Exercise 3: 构造函数 & prototype ==========

console.log('\n--- Exercise 3: 构造函数 prototype ---');

function Person(name) {
  this.name = name;
}

Person.prototype.sayHi = function () {
  console.log('Hi, I am ' + this.name);
};

const p1 = new Person('Alice');
const p2 = new Person('Bob');

console.log('3-p1.__proto__ === Person.prototype ?',
  Object.getPrototypeOf(p1) === Person.prototype);

p1.sayHi(); // 预测输出
p2.sayHi(); // 预测输出


// ========== Exercise 4: 覆盖同名属性 ==========
// 问：下面每一行输出什么？为什么？

console.log('\n--- Exercise 4: 实例属性覆盖原型属性 ---');

function Animal() {}
Animal.prototype.legCount = 4;

const cat = new Animal();
console.log('4-cat.legCount (before) =', cat.legCount);

cat.legCount = 3;
console.log('4-cat.legCount (after)  =', cat.legCount);
console.log('4-Animal.prototype.legCount =', Animal.prototype.legCount);


// ========== Exercise 5: Object.create ==========
// Object.create(proto) 直接以某个对象作为原型创建新对象。

console.log('\n--- Exercise 5: Object.create ---');

const base = { kind: 'base' };
const obj2 = Object.create(base); // obj2 的原型就是 base

obj2.name = 'child';

console.log('5-obj2.name =', obj2.name);   // 自己的属性
console.log('5-obj2.kind =', obj2.kind);   // 从原型来的
console.log('5-base.kind =', base.kind);   // 原型上的值

// 思考：如果现在写 base.kind = 'changed'; 再打印 obj2.kind，会变成什么？自己试试。

// JS Step 6 Extra: 手动复制方法 vs 使用 prototype / class

console.log('=== Part 1: 手动把方法塞进每个对象（没有 prototype） ===');

// 一个“说话”函数：
function sayHiImpl() {
  console.log('Hi, I am ' + this.name);
}

// 创建 3 个用户：每次都要手动把 sayHi 塞进去
const user1 = { name: 'Alice', sayHi: sayHiImpl };
const user2 = { name: 'Bob',   sayHi: sayHiImpl };
const user3 = { name: 'Carol', sayHi: sayHiImpl };

// 试着调用：
user1.sayHi();
user2.sayHi();
user3.sayHi();

// 思考：如果有 1000 个用户，就要写 1000 次 sayHi: sayHiImpl。
// 如果改打印逻辑，要确保所有地方都同步更新，不然就会漏改。


console.log('\n=== Part 2: 使用构造函数 + prototype 共享方法 ===');

function Person(name) {
  this.name = name;          // 每个实例自己的“数据”
}

// 所有 Person 实例共享这一份 sayHi 函数：
Person.prototype.sayHi = function () {
  console.log('Hi, I am ' + this.name);
};

const p1 = new Person('Alice');
const p2 = new Person('Bob');
const p3 = new Person('Carol');

p1.sayHi();
p2.sayHi();
p3.sayHi();

// 验证：三个实例的 sayHi 都指向同一个函数
console.log('\n共享方法验证:');
console.log('p1.sayHi === p2.sayHi ?', p1.sayHi === p2.sayHi);
console.log('p2.sayHi === p3.sayHi ?', p2.sayHi === p3.sayHi);


// === Part 3: 用 class 写法（语法糖，本质同 Part 2） ===

console.log('\n=== Part 3: 使用 class 语法糖 ===');

class Student {
  constructor(name) {
    this.name = name;
  }

  sayHi() {                           // 实例方法：自动挂到 Student.prototype 上
    console.log('Hi, I am ' + this.name);
  }
}

const s1 = new Student('Dave');
const s2 = new Student('Emma');

s1.sayHi();
s2.sayHi();

console.log('\nclass 写法下的原型验证:');
console.log(
  'Object.getPrototypeOf(s1) === Student.prototype ?',
  Object.getPrototypeOf(s1) === Student.prototype
);
console.log('s1.sayHi === s2.sayHi ?', s1.sayHi === s2.sayHi);

// 练习：
// 1）在 Part 1 里再多加几个 userX，体会一下“手动塞方法”的麻烦。
// 2）在 Part 2 / Part 3 里，给 Person / Student 再添加一个方法，比如 greet(otherName)，只改 prototype / class 一处，看所有实例是否都获得了这个新方法。
// 3）用 Object.getPrototypeOf(...) 查看 user1 / p1 / s1 的原型分别是谁。

console.log('\n=== 直观对比：方法共享 vs 不共享 ===');

// 手动塞方法（不共享）
function sayHiImpl() {
  console.log('Hi, I am ' + this.name);
}

const u1 = { name: 'Alice', sayHi: sayHiImpl };
const u2 = { name: 'Bob',   sayHi: sayHiImpl };

console.log('u1.sayHi === u2.sayHi ?', u1.sayHi === u2.sayHi); // 这里你自己看输出


// 构造函数 + prototype（共享）
function Person2(name) {
  this.name = name;
}
Person2.prototype.sayHi = function () {
  console.log('Hi, I am ' + this.name);
};

const pA = new Person2('Carol');
const pB = new Person2('Dave');

console.log('pA.sayHi === pB.sayHi ?', pA.sayHi === pB.sayHi); // 再看这一行输出