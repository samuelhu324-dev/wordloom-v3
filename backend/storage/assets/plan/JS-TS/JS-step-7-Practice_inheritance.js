// JS Step 7 Practice: 继承链 Person -> Student -> ExchangeStudent


console.log('=== Part 1: 使用 class ===');

class Person {
  constructor(name) {
    this.name = name;
  }
  sayHi() {
    console.log('[Person.sayHi] Hi, I am ' + this.name);
  }
}

class Student extends Person {
  constructor(name, school) {
    super(name);
    this.school = school;
  }
  study() {
    console.log('[Student.study] ' + this.name + ' studies at ' + this.school);
  }
}

class ExchangeStudent extends Student {
  constructor(name, school, country) {
    super(name, school);
    this.country = country;
  }
  travel() {
    console.log('[ExchangeStudent.travel] ' + this.name + ' is in ' + this.country);
  }
}

const e1 = new ExchangeStudent('Alice', 'MIT', 'USA');

// 先预测下面三行分别会打印什么，再运行：
e1.sayHi();    // ?
e1.study();    // ?
e1.travel();   // ?

// 预测原型关系真假：
console.log('\n[Part1 原型链检查]');
console.log('Object.getPrototypeOf(e1) === ExchangeStudent.prototype ?',
  Object.getPrototypeOf(e1) === ExchangeStudent.prototype); // ?
console.log('Object.getPrototypeOf(ExchangeStudent.prototype) === Student.prototype ?',
  Object.getPrototypeOf(ExchangeStudent.prototype) === Student.prototype); // ?
console.log('Object.getPrototypeOf(Student.prototype) === Person.prototype ?',
  Object.getPrototypeOf(Student.prototype) === Person.prototype); // ?



console.log('\n=== Part 2: 手动构造同样的继承链（不写 class） ===');

function Person2(name) {
  this.name = name;
}
Person2.prototype.sayHi = function () {
  console.log('[Person2.sayHi] Hi, I am ' + this.name);
};

function Student2(name, school) {
  Person2.call(this, name); // 相当于 super(name)
  this.school = school;
}
// 关键：Student2 原型 继承 Person2 原型
Student2.prototype = Object.create(Person2.prototype);
Student2.prototype.constructor = Student2;
Student2.prototype.study = function () {
  console.log('[Student2.study] ' + this.name + ' studies at ' + this.school);
};

function ExchangeStudent2(name, school, country) {
  Student2.call(this, name, school);
  this.country = country;
}
// 关键：ExchangeStudent2 原型 继承 Student2 原型
ExchangeStudent2.prototype = Object.create(Student2.prototype);
ExchangeStudent2.prototype.constructor = ExchangeStudent2;
ExchangeStudent2.prototype.travel = function () {
  console.log('[ExchangeStudent2.travel] ' + this.name + ' is in ' + this.country);
};

const e2 = new ExchangeStudent2('Bob', 'Harvard', 'UK');

// 同样先预测输出：
e2.sayHi();   // ?
e2.study();   // ?
e2.travel();  // ?

console.log('\n[Part2 原型链检查]');
console.log('Object.getPrototypeOf(e2) === ExchangeStudent2.prototype ?',
  Object.getPrototypeOf(e2) === ExchangeStudent2.prototype); // ?
console.log('Object.getPrototypeOf(ExchangeStudent2.prototype) === Student2.prototype ?',
  Object.getPrototypeOf(ExchangeStudent2.prototype) === Student2.prototype); // ?
console.log('Object.getPrototypeOf(Student2.prototype) === Person2.prototype ?',
  Object.getPrototypeOf(Student2.prototype) === Person2.prototype); // ?


// Extra：比较两条链的“形状”是否一致
console.log('\n=== Extra: 形状对比 ===');
console.log('class 写法链顶：',
  Object.getPrototypeOf(Person.prototype) === Object.prototype);
console.log('手动写法链顶：',
  Object.getPrototypeOf(Person2.prototype) === Object.prototype);