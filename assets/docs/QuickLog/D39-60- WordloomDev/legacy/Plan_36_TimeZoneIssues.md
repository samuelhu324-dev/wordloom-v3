长期（尤其是你以后要做跨时区展示 / 前端根据用户时区格式化）：

建议抽一个 time_provider.utc_now() 返回 datetime.now(timezone.utc)；

在 repository 里决定是否 .replace(tzinfo=None)；

慢慢把散落的 utcnow() 改成调用 time_provider。

一句压缩版总结

从“工程健康度”和 Python 官方推荐来看，datetime.now(timezone.utc) 是正确默认；utcnow() 只是为了兼容某些老的、要求 naive 的存储/库，在边界做一次转换就好。

你可以把规则写进 DDD/Hexagonal 的 RULES：
领域内一律使用 aware UTC 时间；存 DB / 出 DB 时由 Adapter 统一处理 naive / aware 的转换。