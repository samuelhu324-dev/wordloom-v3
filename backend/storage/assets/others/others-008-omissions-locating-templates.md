每次排查只做三件事（可写成 Checklist）：

客户端证据：DevTools Network
这次 /file 请求的 status、TTFB、size、是否 cached
服务端证据：同 correlation_id 的后端轨迹（上面 jq）
依赖证据：看 db_duration_ms / storage_duration_ms / file_size_bytes
db 大：查库慢
storage 大：磁盘/对象存储慢
file_size 巨大：图过大/未压缩/传输慢（体感慢通常在这里）
建议你把这个模板写进 others-007-omissions-locating.md，每次照抄执行，减少“靠感觉”。


