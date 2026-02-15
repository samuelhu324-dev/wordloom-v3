-- 1) 回放单个 request_id 的事件序列
select
  created_at,
  event_type,
  decision,
  result,
  error_code
from public.media_write_events
where request_id = '5eb05f8c-e039-4b5e-a1b5-xxxxxxxxxxxx'::uuid
order by created_at asc;

-- 2) 最近 10 分钟：每个 request 的最终错误（按最新时间排序）
select
  request_id,
  max(created_at) as last_at,
  max(error_code) filter (where event_type='WRITE_RESULT') as final_error
from public.media_write_events
where created_at > now() - interval '10 minutes'
group by request_id
order by last_at desc;

-- 2.1) 
select
  request_id,
  min(created_at) as start_at,
  max(created_at) as end_at,
  count(*) as events,
  max(result) filter (where event_type = 'WRITE_RESULT') as final_result
from public.media_write_events
group by request_id
order by start_at desc
limit 20;

-- 3) 过去 1 天：失败/有错误码的事件
select *
from public.media_write_events
where created_at > now() - interval '1 day'
  and (result = 'FAILED' or error_code is not null)
order by created_at desc;

-- 4) 过去 10 分钟：事件不完整的 request（缺 decision 或缺 result）
with per_request as (
  select
    request_id,
    bool_or(event_type='WRITE_DECISION') as has_decision,
    bool_or(event_type='WRITE_RESULT')   as has_result,
    max(created_at) as last_at
  from public.media_write_events
  where created_at > now() - interval '10 minutes'
  group by request_id
)
select *
from per_request
where not (has_decision and has_result)
order by last_at desc;

-- 5) 
select
  created_at,
  event_type,
  request_id,
  workspace_id, entity_type, entity_id, role, position, blob_hash,
  decision, result, error_code,
  payload
from public.media_write_events
where request_id = '<REQ_ID>'::uuid
order by created_at asc;

