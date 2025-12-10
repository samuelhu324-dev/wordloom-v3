/**
 * 快速测试脚本 - 验证 markdownToNoteContent 是否正常工作
 *
 * 在浏览器控制台中运行此脚本来测试
 */

// 复制 markdownToNoteContent 和相关函数到这里进行测试

const testCases = [
  {
    name: "简单段落",
    input: "这是第一段\n这是第二段",
    expected: 2
  },
  {
    name: "标题",
    input: "# 标题1\n## 标题2",
    expected: 2
  },
  {
    name: "混合内容",
    input: "# 标题\n这是内容\n> 引用",
    expected: 3
  },
  {
    name: "空内容",
    input: "",
    expected: 0
  },
  {
    name: "只有空行",
    input: "\n\n\n",
    expected: 0
  }
];

// 在浏览器中粘贴这个并运行看结果
console.log("markdownToNoteContent 测试套件");
testCases.forEach(test => {
  console.log(`测试: ${test.name}`);
  console.log(`输入: "${test.input}"`);
  console.log(`期望块数: ${test.expected}`);
  // 实际测试需要从 blocks.ts 导入 markdownToNoteContent
});
