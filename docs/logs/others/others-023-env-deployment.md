你踩到的是工程世界最常见的地雷阵：“本地要开一堆东西 + 环境混淆 + 测试把开发库炸了”。解决它的套路很成熟：把“启动、依赖、配置、数据”都收进一个可复制的环境盒子里，然后给数据库加“防呆保险丝”。

下面我给你一套在你这种 API + worker + Elasticsearch +（可能还有 DB/Redis/Kafka） 场景里，最省命、最不容易混淆的做法。

1) 本地多服务怎么管：Docker Compose + Profiles（最常用、最稳）

核心思想：

所有依赖（ES/DB/Redis…）都用 compose 起

你的 api/worker 可以选择：也容器化（更一致），或本机跑（更快迭代）

用 profiles 分组：dev、test、infra-only、full

典型组合：

compose up infra：只起 ES/DB/Redis

compose up full：起 ES/DB/Redis + api + worker

compose up test：起一套“测试专用”的依赖（不同端口/不同卷/不同索引前缀）

你会立刻得到：

一条命令开全套

每个人环境一致

不再“我机器上没复现”

2) 环境混淆怎么根治：把“环境标识”做成一等公民

你现在的混淆风险主要来自三类：

A) 配置文件混用（.env / settings）

做法：

明确三套：.env.dev、.env.test、.env.prod

启动命令显式指定：ENV=dev / ENV=test

禁止默认连接任何共享/真实资源（默认只连 dev）

B) 资源命名冲突（DB、ES index、队列 topic）

做法：

统一加前缀：wordloom_dev_*、wordloom_test_*

ES 索引最关键：比如 wl_dev_media_v1 vs wl_test_media_v1

队列同理：wl.dev.events / wl.test.events

C) 数据持久化卷混用（docker volume）

做法：

dev/test 用不同 volume 名称：wl_dev_pgdata、wl_test_pgdata

或者 test 直接用临时卷（跑完就删），减少污染

3) 防止“测试库误写开发库”：上保险丝（强烈建议必须做）

这部分是救命的。你要让系统在“连错库”时直接拒绝启动。

保险丝 1：启动时做“环境哨兵检查”

在 DB 里放一个表或一条 metadata：

environment = dev/test/prod

project = wordloom

created_at

应用启动时检查：

ENV=test 就必须连到 environment=test 的库

不匹配就 panic 退出，并打印“你连错库了”

这招几乎可以把“误连库”概率打到接近 0。

保险丝 2：测试环境强制 “DROP/CREATE only allowed in test”

如果你有迁移/清库脚本：

只有当 ENV=test 且库内 sentinel=TEST 才允许 destructive 操作

否则拒绝执行

保险丝 3：端口/host 刻意不同

很土但有效：

dev DB：5432

test DB：55432

你一眼就能看出来 config 有没有错

4) 开发/测试工作流建议：两条路选一条（别混着来）
路线 A：本地 dev + 容器 infra（最舒服）

compose 起 ES/DB/Redis

你本机跑 API/worker（热重载快，debug 好用）

.env.dev 指向 localhost:xxxxx

适合你现在这种“开发频繁改代码”的阶段。

路线 B：全容器化（最一致）

compose 起所有东西：api/worker 也在容器里

一键全套，CI/CD 也容易复用

缺点：调试和热重载要多配置一点

适合团队协作/后期稳定阶段。

5) 你这种 “worker + ES + API” 的测试分层（避免每次都开全家桶）

你不需要所有测试都依赖 ES/worker。

建议分三层：

Unit tests（纯内存/纯 fake）

不起 DB、不起 ES

快，跑得勤

Integration tests（容器依赖）

起 DB + ES

测 repository / adapter / bulk writer

用 test profile，资源全部隔离

E2E tests（全链路）

起 API + worker + ES + DB

跑关键路径几条就行（别多，贵）

这样你日常 80% 的改动只跑 unit，只有改到 ES bulk 或 outbox 才跑 integration/e2e。

6) 你可以立刻做的“最小落地清单”（不用大改架构）

增加 .env.dev / .env.test，把 ES index 前缀区分开

给 DB 增加 env_sentinel（一张表或一行 metadata）

应用启动加检查：ENV 必须匹配 sentinel

docker compose 把 ES/DB 起起来，并给 dev/test 各自 volume + 端口

写两个命令：

make dev-up（起 infra）

make test-up（起 test infra）

make test（跑测试，并确保只连 test）

这五步做完，你的“开一堆服务”和“库混淆”会立刻下降一个数量级。

行，PG 已经确定了；至于 worker 和 api 是否同一个 repo——别让这个“不确定”卡住你。工程上更稳的办法是：**不管是同 repo 还是多 repo，都用同一套“本地环境控制平面”**来管依赖、配置、端口、数据隔离。你把它当成“本地小型平台”，api/worker 只是它上面的两个进程而已。
下面给你一套立刻能落地的方案：目录怎么摆、compose 怎么写、dev/test/prod 怎么隔离、以及如何防止“连错库”。

1) 统一入口：在项目根目录放一个“环境控制平面”
无论你是 monorepo（api+worker 同 repo）还是 polyrepo（分开），你都可以做一个目录：
/deploy
  docker-compose.yml
  docker-compose.test.yml   (可选)
  env/
    dev.env
    test.env
  scripts/
    dev-up.sh
    dev-down.sh
    test-up.sh
    test-reset.sh
    test-down.sh
Makefile

你之后的体验应该是：


make dev-up：起 PG + ES（+可选 Prometheus/Grafana）


make dev-api：本机跑 API


make dev-worker：本机跑 worker


make test-up：起一套测试专用 PG + ES


make test：跑测试（强制指向 test 环境）


这一步做完，“开一堆服务”就不再靠记忆力。

2) 关键点：dev/test 必须“物理隔离”，不是“心理隔离”
PG 隔离（强烈推荐做“库名 + 用户 + 端口”三重隔离）


dev：


DB：wordloom_dev


User：wordloom_dev


Port：5432




test：


DB：wordloom_test


User：wordloom_test


Port：55432（故意不一样，防手滑）




ES 也一样：


dev：9200


test：59200
并且索引名前缀强制区分：wl_dev_* vs wl_test_*



你以后看到配置里写着 55432 / 59200，就知道“这是测试的，别碰生产脑子”。


3) 防止“连错库”的保险丝：DB Sentinel（必须上）
这是最救命的一招：应用启动时先验证自己连的是不是正确环境，不对就直接退出。
Sentinel 的做法（概念）
在每个数据库里存一条元信息，比如：


env = dev 或 env = test


project = wordloom


应用（API/worker）启动时：


ENV=test 但库里 sentinel 是 dev → panic 退出


同理，任何 destructive 操作（清库、drop、reset）必须要求：


ENV=test 且 sentinel=TEST 才允许




这会把“测试误写开发库”的概率打到接近 0。

4) Docker Compose：只容器化依赖（你代码先别急着塞进容器）
你现在处在开发期，最舒服的组合通常是：


PG + ES：docker compose 起


API + worker：本机跑（debug/热重载最爽）


一个最小化 compose（你可以直接抄骨架）：
# deploy/docker-compose.yml
services:
  pg_dev:
    image: postgres:16
    environment:
      POSTGRES_DB: wordloom_dev
      POSTGRES_USER: wordloom_dev
      POSTGRES_PASSWORD: wordloom_dev_pw
    ports:
      - "5432:5432"
    volumes:
      - wl_pg_dev:/var/lib/postgresql/data

  es_dev:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.15.0
    environment:
      discovery.type: single-node
      xpack.security.enabled: "false"
      ES_JAVA_OPTS: "-Xms1g -Xmx1g"
    ports:
      - "9200:9200"
    volumes:
      - wl_es_dev:/usr/share/elasticsearch/data

volumes:
  wl_pg_dev:
  wl_es_dev:

再来一份 test（端口/卷/库名全部不同）：
# deploy/docker-compose.test.yml
services:
  pg_test:
    image: postgres:16
    environment:
      POSTGRES_DB: wordloom_test
      POSTGRES_USER: wordloom_test
      POSTGRES_PASSWORD: wordloom_test_pw
    ports:
      - "55432:5432"
    volumes:
      - wl_pg_test:/var/lib/postgresql/data

  es_test:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.15.0
    environment:
      discovery.type: single-node
      xpack.security.enabled: "false"
      ES_JAVA_OPTS: "-Xms1g -Xmx1g"
    ports:
      - "59200:9200"
    volumes:
      - wl_es_test:/usr/share/elasticsearch/data

volumes:
  wl_pg_test:
  wl_es_test:


5) Makefile：把“启动/停止/重置”变成肌肉记忆
dev-up:
	docker compose -f deploy/docker-compose.yml up -d

dev-down:
	docker compose -f deploy/docker-compose.yml down

test-up:
	docker compose -f deploy/docker-compose.test.yml up -d

test-down:
	docker compose -f deploy/docker-compose.test.yml down

test-reset:
	docker compose -f deploy/docker-compose.test.yml down -v
	docker compose -f deploy/docker-compose.test.yml up -d

你会发现：这东西一旦有了，你每天省下来的时间是按“小时”算的。

6) “部署问题”先用同一思路：环境=配置+依赖+数据隔离
你现在先别纠结 Kubernetes。最少阻力的部署路径一般是：


staging / demo：直接用 compose（跟本地几乎一致）


prod：后面再决定是 compose on VM 还是 k8s（看你规模/团队）


核心不变：


prod 的 .env.prod 永远单独存放（不要和 dev/test 混）


prod 的 DB/ES 名称和端口也应当在命名上“明显不同”


prod 也要 sentinel（只是 sentinel=prod）



7) 关于“worker 和 api 是否同 repo”：别纠结，按两种情况都能跑


同 repo（monorepo）：你在同一个根目录做 deploy/ 最顺


不同 repo（polyrepo）：你做一个独立的 wordloom-ops（或 infra）仓库放 deploy/，两个 repo 都只依赖它提供的 dev/test 环境端点


你现在可以先按“同 repo”的方式做起来；就算以后拆 repo，这套 deploy 目录也能原封不动搬走。

你下一步可以直接照做的“最小闭环”（1 次提交搞定）


加 deploy/docker-compose.yml + deploy/docker-compose.test.yml


Makefile 加 dev-up/dev-down/test-up/test-reset


.env.dev .env.test（强制写不同端口、不同 DB 名、不同 ES 前缀）


DB 增 sentinel + 应用启动校验（API/worker 都要校验）


做完这四步，你的“开一堆服务 + 混库”问题会立刻降级成“可控的小麻烦”，不再是每天掉血的深渊。
如果你愿意，我可以直接按你项目习惯（比如 Python/FastAPI + 自研 worker？还是 Celery？）把 ENV 配置结构（settings.py / pydantic settings / dotenv 读取优先级）也一起整理成一套“不会串”的模板，并把 sentinel 校验写成你架构里最合适的位置（例如 app startup hook / worker bootstrap）。