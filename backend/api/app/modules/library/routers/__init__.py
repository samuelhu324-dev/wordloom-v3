"""
Library Routers - HTTP 适配器

FastAPI routers 将 Use Case 暴露为 REST 端点。

结构:
  routers/
  └── library_router.py

职责:
  1. 解析 HTTP 请求 → 转换为输入端口 DTO
  2. 从 DI 容器调用 Use Case
  3. 转换输出端口 DTO → HTTP 响应
  4. 处理异常 → HTTP 错误响应
  5. 日志和可观测性

Router 没有业务逻辑，只做 HTTP 翻译。
"""
