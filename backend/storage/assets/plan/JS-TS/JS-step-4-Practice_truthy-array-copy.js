// JS Step 4 Practice: truthy/falsy、数组方法、浅/深拷贝
// 结构：
// - 练习 1：truthy / falsy 判断
// - 练习 2：map / filter / reduce
// - 练习 3：浅拷贝 vs 深拷贝


// ========== 练习 1：truthy / falsy ==========
// 题目：先自己在心里判断每个值在 if 里会不会执行，然后再运行看结果。

console.log('--- Exercise 1: truthy / falsy ---');

function testIf(value, label) {
  if (value) {
    console.log(label, '=> if 条件为 true');
  } else {
    console.log(label, '=> if 条件为 false');
  }
}

testIf(false, 'false');
testIf(0, '0');
testIf(-0, '-0');
testIf('', "'' (空字符串)");
testIf('0', "'0' (字符串)");
testIf('false', "'false' (字符串)");
testIf(null, 'null');
testIf(undefined, 'undefined');
testIf(NaN, 'NaN');
testIf([], '[] (空数组)');
testIf({}, '{} (空对象)');

// 思考：哪些是你预期之外的？特别注意：[] 和 {} 是 truthy。

// 额外：|| 和 ?? 的差异
console.log('\n--- Exercise 1 extra: || vs ?? ---');

const n = 0;
const a = n || 10; // 0 是 falsy，|| 会用右边 10
const b = n ?? 10; // 0 不是 null / undefined，?? 保留左边 0

console.log('a (0 || 10) =', a); // 10
console.log('b (0 ?? 10) =', b); // 0


// ========== 练习 2：map / filter / reduce ==========
// 题目：先读注释，自己在脑中写出结果，再运行看输出。

console.log('\n--- Exercise 2: map / filter / reduce ---');

const numbers = [1, 2, 3, 4, 5];

// 2.1 map：每个元素 +1
const plusOne = numbers.map((n) => n + 1);
console.log('plusOne:', plusOne); // 预期：[2, 3, 4, 5, 6]

// 2.2 filter：保留偶数
const evens = numbers.filter((n) => n % 2 === 0);
console.log('evens:', evens); // 预期：[2, 4]

// 2.3 reduce：求和
const sum = numbers.reduce((acc, cur) => acc + cur, 0);
console.log('sum:', sum); // 预期：15

// 2.4 reduce：把数组转成“值 => 出现次数”的对象
const nums2 = [1, 2, 2, 3, 3, 3];

const countMap = nums2.reduce((acc, cur) => {
  acc[cur] = (acc[cur] || 0) + 1;
  return acc;
}, {});

console.log('countMap:', countMap); // 预期：{ '1': 1, '2': 2, '3': 3 }

// ---- 小练习（可以自己在下面写代码尝试）：
// 1）给定字符串数组 ['alice', 'bob', 'carol']，用 map 转成大写。
// 2）给定对象数组 [{active: true}, {active:false}, ...]，用 filter 只保留 active 为 true 的。
// 3）给定数字数组，用 reduce 求最大值。



// ========== 练习 3：浅拷贝 vs 深拷贝 ==========
// 题目：观察修改 nested 对象后，原对象是否被影响。

console.log('\n--- Exercise 3: shallow copy vs deep copy ---');

// 3.1 浅拷贝演示
const original = {
  name: 'Alice',
  nested: {
    score: 100,
  },
};

const shallow1 = { ...original };               // 对象展开
const shallow2 = Object.assign({}, original);   // Object.assign

console.log('before change:');
console.log('original.nested.score =', original.nested.score);
console.log('shallow1.nested.score =', shallow1.nested.score);
console.log('shallow2.nested.score =', shallow2.nested.score);

// 修改浅拷贝里的嵌套对象
shallow1.nested.score = 60;

console.log('\nafter change shallow1.nested.score = 60:');
console.log('original.nested.score =', original.nested.score); // 看看是多少？
console.log('shallow1.nested.score =', shallow1.nested.score);
console.log('shallow2.nested.score =', shallow2.nested.score);

// 思考：为什么改 shallow1，会影响 original 和 shallow2？


// 3.2 深拷贝演示（使用 JSON 序列化）
// 注意：真实项目里可以用 lodash.cloneDeep 等库，这里只做概念演示。

const original2 = {
  name: 'Bob',
  nested: {
    score: 100,
  },
};

const deep = JSON.parse(JSON.stringify(original2));

console.log('\n--- deep copy ---');
console.log('before change:');
console.log('original2.nested.score =', original2.nested.score);
console.log('deep.nested.score =', deep.nested.score);

deep.nested.score = 0;

console.log('\nafter change deep.nested.score = 0:');
console.log('original2.nested.score =', original2.nested.score); // 看看是否被影响？
console.log('deep.nested.score =', deep.nested.score);

// 小练习：
// 1）自己再定义一个对象，里面多嵌套一层，比如 { a: { b: { c: 1 } } }，用浅拷贝和深拷贝分别试一试。
// 2）思考：为什么浅拷贝对“第一层”属性是独立的，但对更深层不是？