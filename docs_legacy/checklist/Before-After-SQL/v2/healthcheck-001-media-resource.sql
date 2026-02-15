-- A) total & soft-delete
select
  count(*) as total,
  count(*) filter (where deleted_at is null) as alive,
  count(*) filter (where deleted_at is not null) as soft_deleted
from media_resources;

-- B) entity distribution
select entity_type, count(*)
from media_resources
group by entity_type
order by count(*) desc;

-- C) duplicated active per (entity, hash)
select workspace_id, entity_type, entity_id, file_hash, count(*) as n
from media_resources
where deleted_at is null
group by workspace_id, entity_type, entity_id, file_hash
having count(*) > 1
order by n desc, entity_type
limit 50;

-- D) active image count per entity (spot outliers)
select entity_type, entity_id, count(*) as active_images
from media_resources
where deleted_at is null
group by entity_type, entity_id
order by active_images desc
limit 50;

-- E) hash -> n, paths, entities (all rows)
select file_hash,
       count(*) as n,
       count(distinct file_path) as paths,
       count(distinct entity_id) as entities
from media_resources
where file_hash is not null
group by file_hash
having count(*) > 1
order by n desc
limit 50;

-- F) DEPUPLICATION BUT NO ADDITION
with ranked as (
  select id, workspace_id, entity_type, entity_id, file_hash, created_at,
         row_number() over (
           partition by workspace_id, entity_type, entity_id, file_hash
           order by created_at desc
         ) as rn
  from media_resources
  where deleted_at is null
)
select *
from ranked
where rn > 1
order by created_at desc
limit 200;

-- G) Q1 hash = Top1?
select
  file_hash,
  count(*) as total,
  count(*) filter (where deleted_at is null) as alive,
  count(distinct workspace_id) as workspaces,
  count(distinct entity_id) as entities,
  count(distinct file_path) as paths
from media_resources
where file_hash = '6f560261de40edf7e508d1ad5a433a3f273bfc9db41b7f8170a99eaf9ff4f091'
group by file_hash;

-- H) Q2 paths = 4?
select
  id, workspace_id, entity_id,
  file_path, file_name,
  created_at, deleted_at
from media_resources
where file_hash = '6f560261de40edf7e508d1ad5a433a3f273bfc9db41b7f8170a99eaf9ff4f091'
order by created_at;

-- I) Q3 file_path duplicates?
select file_path, count(*) as n
from media_resources
group by file_path
having count(*) > 1
order by n desc
limit 50;

-- J) To determine how many alive paths exist 
select file_path, count(*) as n
from media_resources
where deleted_at is null
group by file_path
having count(*) > 1
order by n desc
limit 50;

-- K) Case B
with ranked as (
  select
    id, file_path, created_at, deleted_at,
    row_number() over (
      partition by file_path
      order by created_at desc, id desc
    ) as rn
  from media_resources
  where deleted_at is null
)
select *
from ranked
where rn > 1
order by file_path, created_at desc
limit 200;

-- L) Case B business
begin;

with ranked as (
  select
    id,
    row_number() over (
      partition by file_path
      order by created_at desc, id desc
    ) as rn
  from media_resources
  where deleted_at is null
)
update media_resources
set deleted_at = now()
where id in (select id from ranked where rn > 1);

-- 立刻验证
select file_path, count(*) as n
from media_resources
where deleted_at is null
group by file_path
having count(*) > 1
order by n desc
limit 50;

commit; -- 如果验证为 0
-- rollback; -- 如果还不为 0

-- M) Index Creation
create unique index if not exists uq_media_filepath_alive
on media_resources (file_path)
where deleted_at is null;

-- N) 
create unique index if not exists uq_media_entity_hash_alive
on media_resources (workspace_id, entity_type, entity_id, file_hash)
where deleted_at is null;

-- O) Make sure M and N 
select schemaname, tablename, indexname, indexdef
from pg_indexes
where tablename = 'media_resources'
  and indexname in ('uq_media_filepath_alive', 'uq_media_entity_hash_alive')
order by indexname;
