-- healthcheck-004-observe-media-write.sql
-- 目标：把 media_write_events 当作“黑匣子面板”，批量观测最近请求、失败、以及按 blob_hash / slot 回放故事

-- 4.1 最近 20 个 request：事件序列 + 最终结果 + 耗时
-- 日常“看系统是不是健康”的总面板（最近 20 次写入，每次发生了哪些事件、耗时、最终结果）。
select
  request_id,
  min(created_at) as t0,
  max(created_at) as t1,
  (max(created_at) - min(created_at)) as duration,
  array_agg(event_type order by created_at) as events,
  max(decision) filter (where event_type='WRITE_DECISION') as decision,
  max(result)   filter (where event_type='WRITE_RESULT')   as final_result,
  max(error_code) filter (where event_type='WRITE_RESULT') as final_error
from public.media_write_events
group by request_id
order by t1 desc
limit 20;

-- 4.2 最近失败的请求：定位 error_code / payload
-- 把失败请求捞出来，直接看 error_code 与 payload（最省时间）。
select *
from public.media_write_events
where event_type='WRITE_RESULT'
  and result='FAILED'
order by created_at desc
limit 50;

-- 4.3 某个 blob_hash 的所有写入轨迹（追“这张图经历了什么”）
-- 把 <BLOB_HASH> 替换成真实 hash
-- 按 blob_hash 回放“这张图”走过哪些写入（非常适合查重复上传、幂等、替换）。
select
  created_at, event_type, request_id,
  workspace_id, entity_type, entity_id, role, position,
  decision, result, error_code,
  payload
from public.media_write_events
where blob_hash = '<BLOB_HASH>'
order by created_at desc
limit 200;

-- 4.4 某个 slot 的所有写入轨迹（追“这个位置被写了几次/怎么变的”）
-- 把 <> 替换成真实值
-- 按 slot 回放“这个位置”发生过什么（非常适合查 slot 唯一、replace 行为）。
select
  created_at, event_type, request_id,
  workspace_id, entity_type, entity_id, role, position,
  decision, result, error_code,
  payload
from public.media_write_events
where workspace_id = '<WORKSPACE_UUID>'::uuid
  and entity_type  = '<ENTITY_TYPE>'::public.mediaentitytype
  and entity_id    = '<ENTITY_UUID>'::uuid
  and role         = '<ROLE>'
  and position     = <POSITION>
order by created_at desc
limit 200;

-- 4.5 找“事件不完整”的 request（只有 request 没有 result / 或缺 decision）
-- 专门用来抓“链路断了”或“同 request_id 多次决策/多次结果”。
with per_request as (
  select
    request_id,
    bool_or(event_type='WRITE_REQUEST')  as has_request,
    bool_or(event_type='WRITE_DECISION') as has_decision,
    bool_or(event_type='WRITE_RESULT')   as has_result,
    max(created_at) as last_at
  from public.media_write_events
  where created_at > now() - interval '30 minutes'
  group by request_id
)
select *
from per_request
where not (has_request and has_decision and has_result)
order by last_at desc;

-- 4.6 同一个 request_id 是否出现了多次 decision / result（用于排查重复调用/重试复用）
-- 专门用来抓“链路断了”或“同 request_id 多次决策/多次结果”。
select
  request_id,
  count(*) filter (where event_type='WRITE_DECISION') as decision_rows,
  count(*) filter (where event_type='WRITE_RESULT')   as result_rows,
  max(created_at) as last_at
from public.media_write_events
where created_at > now() - interval '30 minutes'
group by request_id
having count(*) filter (where event_type='WRITE_DECISION') > 1
    or count(*) filter (where event_type='WRITE_RESULT') > 1
order by last_at desc;

-- WRITE_DB 缺关键字段（B方案）
select *
from public.media_write_events
where event_type = 'WRITE_DB'
  and (
    payload is null
    or not (payload ? 'action')
    or not (payload ? 'target_table')
    or not (payload ? 'blob_hash')
    or not (payload ? 'slot')
  )
order by created_at desc
limit 100;

-- backfill
update public.media_write_events
set payload = jsonb_build_object(
  'action', 'INSERT',
  'target_table', 'public.media_resources',
  'blob_hash', blob_hash,
  'slot', jsonb_build_object(
    'workspace_id', workspace_id::text,
    'entity_type', entity_type::text,
    'entity_id', entity_id::text,
    'role', role,
    'position', position
  )
)
where id = '44b457ca-4225-4c9f-9d39-93f75142a545'::uuid;

--validate
alter table public.media_write_events
validate constraint ck_mwe_write_db_payload_schema_v1;