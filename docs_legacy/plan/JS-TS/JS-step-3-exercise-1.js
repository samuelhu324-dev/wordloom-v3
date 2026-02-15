// JS Step 3 Practice: Promise & async/await
// 题 1：判断输出顺序（回调版）
// 新建一个文件，比如：JS-step-3-exercise-1.js，写入下面代码，然后在脑子里先想一想打印顺序：

const fs = require('fs');

console.log('A');

fs.readFile('a.txt', 'utf-8', (err, contentA) => {
  if (err) {
    console.error('read a error');
    return;
  }
  console.log('B');
});

console.log('C');


const fs = require('fs');


// 问题：
// 1. 控制台实际的输出顺序是：A / B / C 还是 A / C / B？为什么？
// 2. 用你的话解释一下：这里“谁”是异步的，“谁”只是被延迟执行的普通代码？

//

// 题 2：把 fs.readFile 封装成 Promise
// 在同一个文件里，补全下面函数，让它返回一个 Promise：
// 然后写一段测试代码，要求：



function readFilePromise(path, encoding) {
  // TODO：在这里返回一个 Promise，
  // 内部用 fs.readFile 去读文件，
  // 读成功时 resolve(content)，读失败时 reject(err)
}


const fs = require('fs');

function readFilePromise(path, encoding) {
  return new Promise((resolve, reject) => {
    fs.readFile(path, encoding, (err, content) => {
      if (err) reject(err);      // 读失败 → Promise 失败
      else resolve(content);     // 读成功 → Promise 成功
    });
  });
}

readFilePromise('a.txt', 'utf-8')
    .then(a => {
        console.log('A length:', a.length);
    })
    .catch(err => {
        console.log('read error:', err);
    });

// 1. 读 a.txt，成功后打印：A length: <长度>；
// 2. 出错时打印：read error: <错误信息>。
// **限制：**测试代码只能用 .then(...).catch(...)，不能用 async/await。

// 题 3：把 Promise 链改写成 async/await
// 假设你已经有了上一题的 readFilePromise，下面是 Promise 链的写法：

readFilePromise('a.txt', 'utf-8')
  .then(a => {
    console.log('A length:', a.length);
    return readFilePromise('b.txt', 'utf-8');
  })
  .then(b => {
    console.log('B length:', b.length);
  })
  .catch(err => {
    console.error('read error:', err);
  });

 //

async function main() {
    try {
        const a = await readFilePromise('a.txt', 'utf-8');
        console.log('A length:', a.length);
        const b = await readFilePromise('b.txt', 'utf-8');
        console.log('B length:', b.length);
    } catch (err) {
        console.error('read error:', err);
    }
}

main();

// 要求：

// 1. 写一个 async function main()，用 await 实现同样的逻辑和错误处理；
// 2. 只能用一个 try/catch，在 catch 里统一打印错误；
// 3. 在文件末尾调用 main()。