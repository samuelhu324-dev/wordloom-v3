// 14.1 联合类型：A | B -----------------------------------------

// 字面量联合
type Status = 'success' | 'fail' | 'pending';

function logStatus(s: Status) {
  if (s === 'success') {
    console.log('成功');
  } else if (s === 'fail') {
    console.log('失败');
  } else {
    console.log('等待中');
  }
}

logStatus('success');
// logStatus('SUCCESS'); // ❌ 会编译报错，限制更严格

// 对象联合（可辨识联合：通过 kind / type 等字段区分）
type TextMessage = {
  kind: 'text';
  content: string;
};

type ImageMessage = {
  kind: 'image';
  url: string;
};

type Message = TextMessage | ImageMessage;

function printMessage(msg: Message) {
  if (msg.kind === 'text') {
    // 这里 msg 被缩小成 TextMessage
    console.log('文本：', msg.content);
  } else {
    // 这里 msg 被缩小成 ImageMessage
    console.log('图片：', msg.url);
  }
}

printMessage({ kind: 'text', content: 'Hello' });
printMessage({ kind: 'image', url: 'http://example.com/image.png' });


// 14.2 交叉类型：A & B -----------------------------------------

type WithId = { id: number };
type WithTimestamps = {
  createdAt: Date;
  updatedAt: Date;
};

type Entity = WithId & WithTimestamps;

const post: Entity = {
  id: 1,
  createdAt: new Date('2024-01-01'),
  updatedAt: new Date('2024-02-01')
};

console.log('Entity:', post.id, post.createdAt.toISOString());


// 14.3 小结：什么时候用谁？
// - “要么这样，要么那样” → 联合 A | B
// - “既是 A 又是 B”       → 交叉 A & B


// ===================== 练 习 =====================

// 练习 1：Shape 联合 + 面积函数
// 要求：
// 1. 定义 Circle：{ kind: 'circle'; radius: number }
// 2. 定义 Square：{ kind: 'square'; side: number }
// 3. 定义 Shape = Circle | Square
// 4. 实现 getArea(shape: Shape): number，
//    - circle：π * r * r（用 3.14 即可）
//    - square：side * side
// 5. 分别传入 circle / square 测试

// TODO: 在这里写你的代码
// type Circle = ...
// type Square = ...
// type Shape = ...
// function getArea(shape: Shape): number { ... }
// console.log(getArea(...));

type Circle = {
    kind: 'circle';
    radius: number;
};

type Square = {
    kind: 'square';
    side: number;
}

type Shape = Circle | Square;

function getArea(shape: Shape): number {
    if (shape.kind === 'circle') {
        console.log(getArea({ kind: 'square', side: 4 }));
        console.log('计算圆的面积');
        return 3.14 * shape.radius * shape.radius;
    } else {
        console.log('计算正方形的面积');
        return shape.side * shape.side;
    }
}

console.log(getArea({ kind: 'circle', radius: 5})) ; // 计算圆的面积
console.log(getArea({ kind: 'square', side: 4})); // 计算正方形的面积

// 练习 2：Person & Contact 交叉类型
// 要求：
// 1. 定义 Person：{ name: string; age: number }
// 2. 定义 Contact：{ email: string; phone?: string }
// 3. 定义 PersonWithContact = Person & Contact
// 4. 定义一个变量 personContact: PersonWithContact 并赋值
// 5. 写一个函数 printPerson(p: PersonWithContact)，打印出所有信息

type Person = {
    name: string;
    age: number;
}

type Contact = {
    email: string;
    phone?: string;
}

type PersonWithContact = Person & Contact;

const p: PersonWithContact = {
    name: 'Alice',
    age: 30,
    email: 'xxx@qq.com',
    phone: '123-456-7890'    
}

function printPerson (p: PersonWithContact) : void {
    console.log('Name:', p.name);
    console.log('Age:', p.age);
    console.log('Email:', p.email);
    console.log('Phone:', p.phone);
}

printPerson(p);


// TODO: 在这里写你的代码
// interface Person { ... }
// interface Contact { ... }
// type PersonWithContact = ...
// const personContact: PersonWithContact = { ... };
// function printPerson(p: PersonWithContact) { ... }
// printPerson(personContact);