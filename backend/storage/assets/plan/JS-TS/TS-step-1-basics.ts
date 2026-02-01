// TS Step 1: 基本类型 & 简单注解

// 1. 一些最常见的基础类型
const username: string = 'Alice';
const age: number = 20;
const isStudent: boolean = true;

let maybeNumber: number | null = null; // 联合类型提前露个脸

// 2. 给函数参数和返回值写类型
function add(a: number, b: number): number {
  return a + b;
}

function greet(name: string): void {
  console.log('Hello, ' + name);
}

// 3. 对象和数组的简单写法
const user: { name: string; age: number } = {
  name: 'Bob',
  age: 18,
};

const scores: number[] = [90, 85, 100];

console.log(username, age, isStudent, maybeNumber);
console.log('add(1, 2) =', add(1, 2));
greet('TypeScript');
console.log(user, scores);

// === 基本类型示例（第 11 条） ===

// 1. 基础三兄弟
const nickname: string = 'Bob';
const height: number = 1.75;
const active: boolean = false;

// 2. null / undefined 通常配合联合类型
let maybeAge: number | null = null;
maybeAge = 30;

// 3. 数组
const nums: number[] = [1, 2, 3];
const names: Array<string> = ['Alice', 'Bob'];

// 4. 元组：长度和每个位置的类型都固定
const point: [number, number] = [10, 20];

// 5. 对象：用字面量描述形状
const book: { title: string; pages: number } = {
  title: 'TS 入门',
  pages: 200,
};

// 6. 函数类型：参数 + 返回值
function mul(a: number, b: number): number {
  return a * b;
}
const mul2: (a: number, b: number) => number = mul;

// 7. any / unknown（下一个步骤详细说）
let anything: any = 123;
anything = 'abc';

let maybeValue: unknown = 'hello';
// console.log(maybeValue.toUpperCase()); // ❌ 会报错：对象类型为 unknown

// 8. void / never（了解即可）
function logMessage(msg: string): void {
  console.log(msg); // 不关心返回值
}

function fail(msg: string): never {
  throw new Error(msg); // 函数不会“正常返回”
}

console.log(
  nickname,
  height,
  active,
  maybeAge,
  nums,
  names,
  point,
  book,
  mul(2, 3),
  mul2(4, 5),
);

// === 枚举 (enum) & 函数类型 ===

// 1. 枚举：一组可选值的集合
enum Role {
  Admin,          // 0
  User,           // 1
  Guest           // 2
}

enum OrderStatus {
  Pending = 'pending',
  Paid = 'paid',
  Shipped = 'shipped'
}

const r: Role = Role.Admin;
const s: OrderStatus = OrderStatus.Paid;

// 2. 函数类型写法
function sum(a: number, b: number): number {
  return a + b;
}

// 用“函数类型”描述变量
let calc: (x: number, y: number) => number;
calc = sum; // 必须签名兼容

console.log('enum:', r, s);
console.log('calc(1, 2) =', calc(1, 2));

// === any vs unknown ===

let a: any = 123;
a = 'hello';
a.nonExistMethod();          // 编译器不拦你，运行时可能炸

let u: unknown = 'world';
// u.toUpperCase();          // ❌ 编译错误：对象类型为 unknown

// 需要先“缩小类型”
if (typeof u === 'string') {
  console.log(u.toUpperCase()); // 这里被推断成 string，OK
}

// 也可以用类型断言（不如类型缩小安全）
const maybeNum = u as number;   // 强行告诉编译器 “当成 number 吧”

a = 'not a number';

a.nonExistMethod();

   console.log(a.toFixed(2));


