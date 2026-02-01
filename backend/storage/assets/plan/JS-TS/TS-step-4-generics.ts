// 15. 泛型基础演示 + 练习

// ========== 示例：泛型函数 ==========

function identity<T>(value: T): T {
  return value;
}

const a = identity<string>('hello');
const b = identity(42); // 类型自动推断

console.log('identity:', a, b);

// ========== 示例：泛型接口 ==========

interface Box<T> {
  value: T;
}

const numBox: Box<number> = { value: 100 };
const strBox: Box<string> = { value: 'TS' };

console.log('boxes:', numBox.value, strBox.value);

// ========== 示例：带约束的泛型 ==========

function getLength<T extends { length: number }>(value: T): number {
  return value.length;
}

console.log('len(string):', getLength('abc'));
console.log('len(array):', getLength([1, 2, 3]));


// ===================== 练 习 =====================

// 练习 1：泛型函数 wrapInArray
// 要求：
// 1. 定义一个泛型函数 wrapInArray<T>(value: T): T[]
// 2. 传入 number / string，看返回的数组类型是否正确（VS Code 悬停查看）

function wrapInArray<T>(value: T): T[] {
    return [value];
}

const wa1 = wrapInArray(123);
const wa2 = wrapInArray('hi');
console.log(wa1, wa2);

// TODO: 在这里写你的代码
// function wrapInArray<T>(value: T): T[] { ... }
// const wa1 = wrapInArray(123);
// const wa2 = wrapInArray('hi');
// console.log(wa1, wa2);


// 练习 2：泛型接口 ApiResponse<T>
// 要求：
// 1. 定义 interface ApiResponse<T> { code: number; data: T; message?: string }
// 2. 定义两个变量：
//    - userResp: ApiResponse<{ id: number; name: string }>
//    - countResp: ApiResponse<number>
// 3. 写一个函数 logResponse<T>(resp: ApiResponse<T>): void
//    - 打印 code 和 data

interface ApiResponse<T> {code: number; data: T; message?: string}

const userResp: ApiResponse<{ id: number; name: string} > = {
    code: 200,
    data : { id: 1, name: 'Alice'},
}

const countResp: ApiResponse<number> = {
    code: 200,
    data: 42,
    message: 'The answer',
}

function logResponse<T>(resp: ApiResponse<T>): void {
    console.log('code:', resp.code, 'data:', resp.data, 'message:', resp.message);
}

logResponse(userResp);
logResponse(countResp);


// TODO: 在这里写你的代码
// interface ApiResponse<T> { ... }
// const userResp: ApiResponse<{ id: number; name: string }> = { ... };
// const countResp: ApiResponse<number> = { ... };
// function logResponse<T>(resp: ApiResponse<T>): void { ... }
// logResponse(userResp);
// logResponse(countResp);


// 练习 3：带约束的泛型 getId
// 要求：
// 1. 定义一个类型 HasId：{ id: number | string }
// 2. 定义函数 getId<T extends HasId>(obj: T): number | string
//    - 返回 obj.id
// 3. 试着传入：
//    - { id: 1, name: 'Alice' }（应该 OK）
//    - { name: 'Bob' }（应该编译报错）

type HashId = { id: number | string };

function getId<T extends HashId>(obj: T): number | string {
    return obj.id;
}

console.log(getId({ id: 1, name: 'Alice' }));
console.log(getId({ id: 5, string: 'Bob' })); // 观察编译错误
console.log(getId({ name: 'Bob' })); // 观察编译错误


// TODO: 在这里写你的代码
// type HasId = ...
// function getId<T extends HasId>(obj: T): number | string { ... }
// console.log(getId({ id: 1, name: 'Alice' }));
// console.log(getId({ name: 'Bob' })); // 观察编译错误