// JS Step 3 Practice: Promise & async/await
// 结构：
// - 辅助函数 mockRequest：模拟网络请求（随机成功/失败）
// - 练习 1：Promise 基本用法（then / catch）
// - 练习 2：Promise 链式调用
// - 练习 3：async/await + try/catch


// ========== 辅助函数：模拟异步请求 ==========
// delayMs: 延迟毫秒数
// shouldFail: 是否模拟失败
function mockRequest(name, delayMs, shouldFail = false) {
  return new Promise((resolve, reject) => {
    setTimeout(() => {
      if (shouldFail) {
        reject(new Error(`Request ${name} failed`));
      } else {
        resolve(`Response from ${name}`);
      }
    }, delayMs);
  });
}


// ========== 练习 1：Promise 基本用法 ==========
// 题目：读代码，理解 then / catch 的执行顺序。

console.log('--- Exercise 1: basic Promise ---');

mockRequest('A', 500, false)
  .then((value) => {
    console.log('Exercise1 success:', value);
  })
  .catch((err) => {
    console.log('Exercise1 error:', err.message);
  });

// 正确结果：
// 大约 500ms 后，打印：
// Exercise1 success: Response from A



// ========== 练习 2：Promise 链式调用 ==========
// 题目：依次发起两个请求：先 A，再 B，A 成功后才发 B。

console.log('--- Exercise 2: promise chain ---');

mockRequest('A', 300, false)
  .then((valueA) => {
    console.log('A done:', valueA);
    // 返回一个新的 Promise，链条会等待它完成
    return mockRequest('B', 300, false);
  })
  .then((valueB) => {
    console.log('B done:', valueB);
  })
  .catch((err) => {
    console.log('Exercise2 error:', err.message);
  });

// 预期输出顺序：
// A done: Response from A
// B done: Response from B



// ========== 练习 3：async/await + 错误处理 ==========
// 题目：用 async/await 写出和练习 2 一样的逻辑，包含错误处理。

console.log('--- Exercise 3: async/await ---');

async function runAsyncFlow() {
  try {
    const valueA = await mockRequest('A', 200, false);
    console.log('Async A done:', valueA);

    const valueB = await mockRequest('B', 200, true); // 这里我们故意让 B 失败
    console.log('Async B done:', valueB); // 不会执行到这里
  } catch (err) {
    console.log('Async flow error:', err.message);
  } finally {
    console.log('Async flow finished (finally)');
  }
}

runAsyncFlow();

// 预期：
// Async A done: Response from A
// Async flow error: Request B failed
// Async flow finished (finally)
