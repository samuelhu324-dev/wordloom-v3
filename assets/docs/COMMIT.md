feat: Wordloom v3 milestone — backend, editor and admin workspace

Summary
-------

This commit checkpoints several weeks of offline development and brings Wordloom
from "router wiring" to a working v3 vertical slice:

- Backend: all 7 core modules (Tag, Media, Bookshelf, Book, Block, Library, Search)
  are implemented on top of FastAPI with a layered structure (API / Service / Repository),
  using PostgreSQL + psycopg + Alembic migrations.
- Testing: P0–P2 testing framework is wired up, basic happy-path tests are added
  for the main endpoints.
- Frontend: Next.js admin workspace is in place, including Library / Bookshelf /
  Book pages and a first version of the block-based text editor shell.
- UI: introduced design tokens for spacing and typography, plus an admin shell
  layout that future public views can reuse.
- Architecture & docs: ADRs and RULES files are updated to reflect the v3
  domain model and deletion strategy (Basement / Trash).

Background
----------

Due to unstable network access over the past weeks, most of the work was done
locally and only pushed once a stable connection was available. As a result,
this commit is larger than usual and covers multiple iterations of work.

From now on I will go back to smaller, incremental commits again.