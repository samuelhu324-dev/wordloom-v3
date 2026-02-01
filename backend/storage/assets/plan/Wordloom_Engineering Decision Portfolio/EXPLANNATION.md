## EXPLANATION

- [ ] <Q1> Conversation Starter

<!----------------------------------------------------------------------------------------
 ... in consideration of the complexity of "text editor" and "too many granular details":
     1) Skip "v2", "v1" and any other version-based topics
        at interviews and just extract their motivations towards "v3"
     2) "Earlier versions exposed limitations in data structure and evolution …" 
  ---------------------------------------------------------------------------------------->

- [ ] <Q1-1> Why did you build Wordloom?

- It started as a very lightweight internal tool to manage vocabulary and notes 
  for my own use.
- As it grew, I realised the real challenge wasn’t features, but how data and structure
  evolved over time.
- That led me to redesign it around clearer domain boundaries and long-term system
  ownership, which is what the current version focuses on.

---

<!----------------------------------------------------------------------------------------
 ... to avoid UI mending and chores in a too wide range, focus on:
     1) Delete vs Recycle (data security)
     2) Aggregation Boundary (DDD-breakdown / coupling control)
     3) Safe Rollback - Architecture Migration v2 -> v3
     4) Schema evolution
     5) Admin / internal route Separation (boundary of roles)

... important signals:
     1) data integrity
     2) system evolution
     3) ownership
     4) risk management
     5) trade-offs
  ---------------------------------------------------------------------------------------->

- [ ] <Q2> "What are you capable of?"

<!----------------------------------------------------------------------------------------
 ... 1) About Storage/Sepration/traceability:
        - Git: code with rollback, not data 
        - DB: data recovery relies on migration, backup and delete strategies
        - Docker/WSL/Cloud: more about runtime system separation
     2) so when being asked:
  ---------------------------------------------------------------------------------------->

- [ ] <Q2-1> ... "Delete & Recyle"?

- "Docker + Postgres for dev; Alembic for migrations; most of data recovery is based on logical recycle"

<!----------------------------------------------------------------------------------------
 ... 2) Data Domains & Division of Roles:
        - Domain data: "Library / Book / Bookshelf /Block" 
        - Engineering Decisions: "ADRs" (which often go into different paths than DB)
        - Operational metadata: version No., state, mark of soft-deletion, auditing fields⭐
        - User data: privilege, tenant sepration, auditing compliance⭐
 ... most importantly, define the Domain data on "deletion", rather than engineering files like ADRs 
  ---------------------------------------------------------------------------------------->

- "I kept deletion semantics scoped to domain entities, and treated engineering decisions like ADRs separately."

<!----------------------------------------------------------------------------------------
 ... 
        A. Semantics 
           - Soft-delete: invisible from users' eyes but marked as deleted_at or status = archived
             in DB.✅
           - Hard-delete: when it is allowed to trigger? Triggering conditions?⚠️
             e.g. DB row deleted - often possible after purge, admin-only delete, retention policy
           - TTL (Time To Live): how long data can be kept in the recycle area at most 
             once this time is exceeded, it can be safely cleaned up.⚠️

  ---------------------------------------------------------------------------------------->

- [ ] <Q2-1-A-0> ... "Semantics"?

- Deletion semantics were defined at the domain level first

- [ ] <Q2-1-A-1> ... "Haven't made hard-delete"?

- I deliberately avoided hard deletes in the workflow, 
  because irreversible operations are risky without strong guarantees.

- [ ] <Q2-1-A-2> ... "No TTL"?

- I used manual purge instead of automatic TTL-based cleanup 
  to keep deletion behaviour explicit and observable.

<!----------------------------------------------------------------------------------------
 ... 
        B. Reversibility
           1) Accidental deletions can be rolled back (Wordloom has its own recycle bin) 
              even though only book-level deletion was designed 
              and whether they can be restored untouched (without critical loss)
              - e.g. ID, order, references and versions (and they may involve "Elastic", 
                     which provides a history of rollbacks.⚠️
            2) What Wordloom contains is last-known-good state restoration.✅ 

  ---------------------------------------------------------------------------------------->

- [ ] <Q2-1-B> ... "Support historical playbacks"?

- I only support restoring to the last consistent state, not full historical replay. 
  Full versioned recovery would require an event-based or search-index-backed approach, 
  which I intentionally avoided to control complexity."

- Those were consciously scoped out to control complexity.

<!----------------------------------------------------------------------------------------
 ... 
        C. Read-path consistency 
           - No matter which "read path" you use (API, search, list pages, reports, etc.),
             the same rules must be applied, such as filtering out deleted / expired / 
             unauthorised data, so that results stay consistent.✅
             -> A common bug is: the main API already filtered deleted, but search, analytics,
                or some list didn't. Users then still see "ghost data" in some views.
                That means read-path consistency is broken.

  ---------------------------------------------------------------------------------------->

  - [ ] <Q2-1-C> ... "Consistent read-path"?

  - "In Wordloom, The read-path consistency rule rougly ensures that whenever you read from
     a soft-deleted table (e.g. with is_deleted / deleted_at), every query path adds the same filters,
     so no deleted rows "leak" into any read view."


<!----------------------------------------------------------------------------------------
 ... 
        D. Isolation
           - Was recycle mechanism designed as cross-cutting to avoid global fixes
             if any modification happens.
           - Have you turned it into a clear policy/service without invading all modules ⚠️

  ---------------------------------------------------------------------------------------->

- [ ] <Q2-1-D> ... "About your policy/service"?

- "Deletion rules are centralised as policy-like definitions rather than scattered checks, 
    which makes the behaviour easier to reason about and change."

<!----------------------------------------------------------------------------------------
 ... 
        E. Authorization & Audit
           1) Who's able to delete it? And who can restore it?
              Is it required for audit records? (who, when, what was deleted, and why?)
            - Admin perspective.✅
            - No full compliance-grade auditing (who/ why / tenant).⚠️

  ---------------------------------------------------------------------------------------->

- [ ] <Q2-1-E> ... "Is there any compliance system in your program"?

- "I scoped audit concerns to admin-level visibility and basic timelines, 
   rather than full compliance-grade auditing, given the single-user/internal context."

<!----------------------------------------------------------------------------------------
 ... 
        F. Idempotency 
           - For the same delete request, even if its executed multiple times, 
             the final result mus be the same: the data is deleted only  once, 
             no extra deletions and no inconsistent satate.⚠️
             -> No double-click delete from user side: On the frontend, disable the
                "Delete" button (or show a loading state) right after the first click,
                so even if the user clicks multiple times, only one delete request is sent.
             -> The frontend prevents multiple clicks, and the backend ensures idempotency
                so that even if duplicate requests occur, the system still behaves correctly

  ---------------------------------------------------------------------------------------->

- [ ] <Q2-1-F> ... "Simplified idempotency"?

- "I enforced effective idempotency at the interaction level by immediately updating state, 
   reducing the need for defensive retries in the backend."


<!----------------------------------------------------------------------------------------
 ... 
        G. Scope (trigged by a deletion)
           - A deletion of any Library may cause widespread data loss 
             as it dominates the file-layered system.✅
           - But if you delete a book, their blocks still remain intact since referential features
             like "wordloom-based inner link" hasn't been developed.⚠️

  ---------------------------------------------------------------------------------------->

- [ ] <Q2-1-G> ... "Have you made any guard/restraints for referential intergrity"?

- "I designed the recycle layer to avoid dangling references at the domain level. 
   While I didn’t implement full referential enforcement for every edge case, 
   the system prevents restoring objects into an inconsistent state."

---

- [ ] <Q3-1> ... "Aggregation Boundary / Coupling Control"?

- Early on, changes propagated too widely.
- I separated domain / application / infra to contain change
- Boundary rules were institutionalised, not memorised.

<!----------------------------------------------------------------------------------------
 ... 
        A. Module boundaries:
           - split modules by domain

  ---------------------------------------------------------------------------------------->

  - [ ] <Q3-1-A> In a sentence:

    - I split the system into independent modules by domain, instead of organising it by technical layers or pages
  
  - [ ] <Q3-1-A> Expanded (30-60s)

    - In the early days, for speed, features were stacked horizontally, so changing one thing affected many places.
    - As the relationships between Library / Bookshelf / Book / Block grew more complex,
      I split them into separate domain modules. Each module is reponsible only for its own concepts,
      avoiding arbitrary cross-module references.

<!----------------------------------------------------------------------------------------
 ... 
        B. Layered reponsibilities: 
           - domain / application / routers / schemas

  ---------------------------------------------------------------------------------------->

  - [ ] <Q3-1-B> In a sentence:

   - I deliberately separate business rules, use-case flows, interface layer, and data shapes
     to avoid mixing responsibilities.
 
  - [ ] <Q3-1-B> Expanded (30-60s):
   
   - `domain` only goes into invariants and rules;
   - `application` is reponsible for orchestrating use cases;
   - `routers` only handle accepting incoming requests;
   - `schemas` define the external contracts and validation.
   - This way, changing interfaces, flows, or rules won't drag each other down.

<!----------------------------------------------------------------------------------------
 ... 
        C. Dependency directions:
           - repo impl & DB models live in infra

  ---------------------------------------------------------------------------------------->

  - [ ] <Q3-1-C> In a sentence:

   - For core logic, no dependence on data base or any framework; infra is just implementation details.
 
  - [ ] <Q3-1-C> Expanded (30-60s):
   
   - `repository` interfaces live in the application layer, while their specific implementations
      and ORM / DB models all live in infra.
   - For `domain` and `application`, no import of FastAPI / SQLAlchemy, so that when the architecture
     evolves, it won't be locked in by technical details.

<!----------------------------------------------------------------------------------------
 ... 
        D. Contract isolation:
           - schemas / DTO ≠ domain entity

  ---------------------------------------------------------------------------------------->

  - [ ] <Q3-1-D> In a sentence:

   - The API's data shape is not the same as the internal state of domain objects.
 
  - [ ] <Q3-1-D> Expanded (30-60s)
   
   - `schemas` handle the external contract and validation; domain entities only care about business meaning.
   - A change of frontend fields or refactoring of API won't pollute domain model directly.

<!----------------------------------------------------------------------------------------
 ... 
        E. Events decoupling:
           - handlers deal with side effects
           - This is a technique to stop the system from turning into an accidental
             giant ball of mud.

  ---------------------------------------------------------------------------------------->

  - [ ] <Q3-1-E> In a sentence:

   - I process side effects with `handlers` to avoid the fact that core flow depend
     on other modules directly.
 
  - [ ] <Q3-1-E> Expanded (30-60s):
   
   - For example, any change of a `Book` won't call `search / chronicle / media` directly,
     but trigger updates for an event or handlers to reduce tight coupling.
   
<!----------------------------------------------------------------------------------------
 ... 
        F. Institutionalisation: 
           - DDD_RULES / HEXAGONAL_RULES
           - which leaves guardrails for the future.

  ---------------------------------------------------------------------------------------->

  - [ ] <Q3-1-F> In a sentence:

   - I turn boundary constraints into explicit rules, instead of relying on memory or verbal agreements.
 
  - [ ] <Q3-1-F> Expanded (30-60s):
   
   - For example, the `domain` layer must not depend on the UI; `schemas` must not contain business logic;
     only use cases may cross modules.
   - The rule files work as prevention of boundaries from quietly rotting as features grow.

<!----------------------------------------------------------------------------------------
 ... 
        G. Stop doing text editor: 
           - with knowledge about when to stop
           - no further elaboration.

  ---------------------------------------------------------------------------------------->

  - [ ] <Q3-1-F> In a sentence:

   - When I spot edirtor-side complexity will backlash into core domain, 
     I choose to stop at the boundary instead of forcing it further.

---

- [ ] <Q4-1> ... "Schemea evolution / migration safety"?

  - The goal wasn’t zero risk, but reversible risk.

  - When moving from v2 to v3, I deliberately avoided a big-bang rewrite.
    v2 continued to record real data for reference, while v3 was developed as a clean greenfield.

  - I isolated the data layer completely, reshaping and migrating data into a new Postgres schema rather than sharing a database.
    Schema changes were versioned using Alembic, which made evolution explicit and repeatable.

  - This approach reduced cross-version coupling and gave me a clear rollback and comparison path during development.

<!----------------------------------------------------------------------------------------
 ... 
        A. v2 -> v3: parallel development, not a big-bang rewrite (blue-gree mindset)
           - v2 continues to handle recording real data and performance observation
           - v3 is a redesigned greenfield greenfield project.
           - Both coexist at the same time and do not contaminate each other.
           - After v3 becomes stable, v2 naturally degrades into a legacy system.

  ---------------------------------------------------------------------------------------->

  - [ ] <Q4-1-A> 15-20 seconds:

   - I avoided a big-bang rewrite. v2 continued to record real data for reference and performance observation, 
     while v3 was developed as a clean greenfield. Once v3 stabilised, v2 naturally became legacy, 
     which avoided cross-contamination during development.

<!----------------------------------------------------------------------------------------
 ... 
        B. Data-layer isolation + WSL2 + new Postgres: avoiding schema pollution
          What is actually done:
           - v3 uses an independent database environment
           - From the old SQL data, you:
             - clean it,
             - transform the schema,
             - and them import it into the new Postgres
           - Avoided v2/v3 sharing one DB and dragging each other down at the schema level
           - Rebuilt the environment with WSL2 to bypass all the messy local-machine setup
             (no need to go into detail here)

  ---------------------------------------------------------------------------------------->

  - [ ] <Q4-1-B> 15-20 seconds:

   - I isolated the data layer between v2 and v3.
   - Instead of sharing a database, I migrated and reshaped the data into a new Postgres
     schema for v3.
   - This kept schema changes explicit and avoided accidental coupling between old and
     new versions.

<!----------------------------------------------------------------------------------------
 ... 
        C. Schema migration + Alembic: turning "schema changes" into an engineering asset
           - Didn't change tables in place.
           - Instead, you:
             - designed a new schema
             - mapped and transformed old data into the new structure.
             - used Alembic to manage versioned migrations.
           - New DB = new schema = a new evolution track.

  ---------------------------------------------------------------------------------------->

  - [ ] <Q4-1-C> 15-20 seconds:

   - Schema changes were versioned using Alembic, so structure changes were repeatable and explicit.
   - Instead of manual edits, migrations became part of the system's evolution history.

