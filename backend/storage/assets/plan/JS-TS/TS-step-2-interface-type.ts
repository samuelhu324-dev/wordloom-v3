// 练习 1：interface 继承

interface Animal {
  name: string;
}

// 定义一个 Dog 接口，继承 Animal，多一个字段 bark(): void
interface Dog extends Animal {
  bark(): void;
}

// 然后写一个 const dog: Dog = { ... }，在控制台里调用 dog.bark()
const dog: Dog = {
  name: '旺财',
  bark() {
    console.log(this.name + ': 汪汪！');
  }
};

dog.bark();

// --------------------------------------------------------
// 练习 2：type 联合 + 交叉

// 定义 type Success = { type: 'success'; data: string }
type Success = {
  type: 'success';
  data: string;
};

// 定义 type Fail = { type: 'fail'; error: string }
type Fail = {
  type: 'fail';
  error: string;
};

// 定义 type Result = Success | Fail
type Result = Success | Fail;

// 再写一个函数 printResult(r: Result)，根据 r.type 打印不同信息
function printResult(r: Result): void {
  if (r.type === 'success') {
    console.log('成功：', r.data);
  } else {
    console.log('失败：', r.error);
  }
}

// 简单跑几下看看效果
const r1: Result = { type: 'success', data: '保存完成' };
const r2: Result = { type: 'fail', error: '网络错误' };

printResult(r1);
printResult(r2);