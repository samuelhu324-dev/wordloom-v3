## FAQ

1️⃣ 开场寒暄	3–5 min	放松、建立“正常人”信号
2️⃣ 自我介绍	3–4 min	不要爆内容
3️⃣ 项目深挖（核心）	20–30 min	三条 deep dive 主战场
4️⃣ 技术补充 / 即兴问答	10–15 min	判断力 > 细节
5️⃣ 反问	5–8 min	你筛选他们
6️⃣ 收尾	2–3 min	留下“可合作”印象

- [ ] <Conservation-1>

- Thanks for having me. Looking forward to the conversation
- Hope your day’s going well so far.

- Yeah, it’s been good. Happy to get started whenever you are.

<!---------------------------------------------------------------------------------------------------
  ---------------------------------------------------------------------------------------------------
  -------------------------------------------------------------------------------------------------->

- [ ] <Introduction-2> Can you briefly introduce yourself?

    <!--------------------------------------------------------------------------------------------------- 
     ... 1) internal: 
            - for internal use /team-facing (not shipping new external features)
         2) data-heavy:
            - a data centric system with complex relationships (which mainly come from how data is related,
              evolves, and is referenced)
         3) long-running:
            - long-lived / continuously evolving over years.
         4) system ownership:
            - end-to-end ownership (accountable for outcomes and consequences)
         5) data modeling: 
            - defining the meaning of data, its relationships, and its lifecycle
         6) controlling complexity:
            - preventing change from spreading; keeping boundaries clear
       
      --------------------------------------------------------------------------------------------------> 

  - I'm a software engineer with a strong focus on **internal**, **data-heavy** systems. 
    Recently I've been working on a **long-running** project. Now I'm caring about 
    maintainability and safe evolution. 
  - I'd be interested in **system ownership**, **data modelling**, and **controlling complexity** 
    as systems grow. 



  - [ ] <Introduction-2-1> why a **data-heavy** system you are willing to maintain / develop?

    <!--------------------------------------------------------------------------------------------------- 
     ... 1) What is a "data-heavy system"?  
            - data heavy doesn't equal data volume
            - data-heavy equals the system's complexity mainly comes from "how data is stored, evolves,
              and gets referenced."
         2) Put differently, the hard part is not:
            - algorithms
            - ops / infrastructure
            - QPS
         3) Instead, it's about:
            - relationships between data
            - lifecycle (creation -> change -> deletion / archival)
            - whether the system is still understandable and maintainable after schema/data evolution
         4) Using Wordloom as an example (you'll get it immediately)
            - It's:
              - Library / Bookshelf / Book / Block
              - deletions affecting search, analytics, and references
              - version changes affecting historical data
      ... These "dependencies between data" are the real source of complexity
      -------------------------------------------------------------------------------------------------->  

    - By data-heavy, I mean systems where complexity mainly comes from 
      how data is structured, related, and evolves over time, not just from algorithms or traffic.

--------------------------------------------------------------------------------------------------------

  - [ ] <Introduction-2-2> How were you **data-modeling** it during your development?

    <!--------------------------------------------------------------------------------------------------- 
     ... 1) So what is a "data-modeling"?  
            - What is the data?
            - How is it related to other data?
            - What changes will it undergo over its lifecycle?
         2) In your project, you've already done things like:
            - splitting "text" into Blocks
            - splitting "collection relationships" into Library / Bookshelf
            - deciding what is domain data and what is metadata
              - can it be reconstructed from other data? -> if yes, it's more likely metadata
              - will chaning it alter the business meaning or its rules -> it's more likely domain data
              - is its primary purpose performance / query acceleration, indexing, or auditing?
                -> if yes, it's more likely metadata. 
         3) It's not just drawing an ER diagram - it's modeling the meaning of the data
      -------------------------------------------------------------------------------------------------->

    - **Data modeling** for me is about defining what data represents in the system,
      in how entities relate, and how those relationships survive changes over time.

--------------------------------------------------------------------------------------------------------

  - [ ] <Introduction-2-3> Why you just described it as **complex**?

    <!--------------------------------------------------------------------------------------------------- 
     ... 1) Wrong expressions:  
            - Because the architecture is complex...
            - Because it uses DDD...
            - Because there are many modules...
      -------------------------------------------------------------------------------------------------->

    - The complexity isn’t in features, but in keeping data and behavior consistent as the system evolves.

--------------------------------------------------------------------------------------------------------

  - [ ] <Introduction-2-4> How do you usually maintain it as a **long-term system** / 
                           How do you **own** that system?

    <!--------------------------------------------------------------------------------------------------- 
     ... 1) Some negative examples:  
            - I refactor regularly...
            - I follow best practice...
            - I write clean code...
      -------------------------------------------------------------------------------------------------->
    
    - I focus on preventing uncontrolled change.
    - That means keeping reponsibilities clear, evolving schemas carefully. and making sure destructive
      actions are reversible.
    - Bascially, most of the work is deciding what not to change.
    
--------------------------------------------------------------------------------------------------------

- [ ] <Introduction-3> Why did you build a system like that? (or what kind of system you are maintaining)

  - It started as a very lightweight **internal** tool to manage volcabulary and notes just for my own use.
    and as it grew, I'd realise that the real challenge wasn't features, but how data and strcture
    evolved over time.
  - I redesigned it so that responsibilities were explicit, and changes had a `clear` place to go.



  - [ ] <Introduction-3-1> How did you make them **clear**?

    <!--------------------------------------------------------------------------------------------------- 
     ... 1) You should prove that "I know what will happen once boundaries get mixed"
            Doesn't mention DDD
            Doesn't mention tools
            Goes striaght to responsibility + constraints.
      -------------------------------------------------------------------------------------------------->
    
    - I made `domain` boundaries clear by deciding what each part of the system is responsible for,
      and what it's not allowed to do.
    
    - (20-30s):
      I clarified domain boundaries by separating `core domain concepts` from `orchestration` and `infrastructure` concerns.
      Each `domain` focuses on its own rules and state, and `cross-domain` interactions are handled explicitly rather than implicitly.

        - [ ] <Introduction-3-1-1> Can you give me an example?
          
          - For example, content structure, lifecycle tracking, and deletion semantics live in separate domains.
          - A domain never directly manipulates another domain's data; it exposes intent, and 
            the application layer coordinates the interaction.
          - That helped prevent changes in one area from cascading across the system.  

<!---------------------------------------------------------------------------------------------------
  ---------------------------------------------------------------------------------------------------
  -------------------------------------------------------------------------------------------------->

- [ ] <Deep-Dive-3>

- Tell us more about that project.
- What kind of challenges did you face?
- What were the main challenges?
- What trade-offs did you make?

   - I worked on an internal, data-heavy system where safety and maintainability mattered.
     I treated deletion as a semantic decision, prioritising reversibility and read-path consistency.

     As the system grew, I redesigned clear domain boundaries to contain coupling and 
     prevent changes from propagating unpredictably.

     Finally, I avoided a big-bang rewrite by evolving the system in parallel, 
     isolating schemas and keeping changes reversible.

- [ ] <Deep-Dive-3-1> Delete & Recycle? (Data safety / Semantics)

- (within 15s)
  - I treated deletion as a semantic decision, not a technical one.
    I prioritised reversibility and read-path consistency, so deletes were scoped, recoverable,
    and didn't silently break queries or statistics

- (within 30s)
   - Deletion wasn’t just removing rows.
     I defined deletion semantics at the domain level first, prioritising reversibility and consistency.
     Most deletes were soft and recoverable, and I centralised read-path filtering 
     so deleted data wouldn’t accidentally leak into search, stats, or reads.

- (expanded)
    - I separated domain data, operational metadata, and decision files, and designed deletion around reversibility.
    - I avoided irreversible deletes unless there was a strong reason.
      Full audit trails and TTL-based purging were consciously scoped out to control complexity.

  <!----------------------------------------------------------------------------------------------
    ----------------------------------------------------------------------------------------------
  - `Router`:
    The router only handles how requests enter the system — HTTP methods, paths, and status codes.
    It doesn’t contain business logic.
  
  - `Schema`:
    Schemas define the external contract.
    They validate input shape and constraints, and protect the internal system from malformed requests.
  
  - `Domain`:
    The domain layer contains business rules and invariants —
    what actions mean and what is allowed in the system.

  - `Application`:
    The application layer orchestrates use cases.
    It coordinates domain logic and repositories, but doesn’t know storage details.

  - `Repository`:
    Repositories abstract persistence.
    The application asks for data in business terms, without knowing how it's stored.

  - `Models`:
    Database models live in the infrastructure layer and represent storage structure, not business concepts.
    ----------------------------------------------------------------------------------------------
    ---------------------------------------------------------------------------------------------->

- [ ] <Deep-Dive-3-2> Aggregation Boundary / Coupling Control? (Data safety / Semantics)

- (within 15s)
   - As the system grew, changes started propagating too widely, 
     so I redesigned clear domain boundaries and separated responsibilities to contain coupling.

- (within 30s)
   - Early iterations favoured speed, but changes began to ripple across modules.
     I reorganised the backend into domain-based modules with clear layering, so changes stayed local instead of spreading through the system
  
- (expanded)
   - Each module had its own routers, schemas, application logic, and domain rules, while persistence lived in infra.
     Cross-module side effects were handled via handlers, not direct calls.
     Boundary rules were written down explicitly to prevent gradual erosion over time

- Can you walk me through your backend flow / architecture?
- How do requests move through your system?

  - I designed the backend as a layered flow so that each layer isolates a different kind of change 
    — transport, validation, business rules, and persistence.

  - Requests enter through routers, which only handle transport concerns.
    Schemas define the external contract and validate input.
    Domain logic captures business rules and semantics.
    The application layer orchestrates use cases across domains and repositories.
    Repositories abstract persistence, while database models remain an infrastructure detail.

- [ ] <Deep-Dive-3-3> Schema Evolution / Migration Safety

- (within 15s)
   - I avoided a big-bang rewrite by evolving the system in parallel, keeping changes reversible and data isolated.

- (within 30s)
   - Instead of rewriting in place, I ran v2 and v3 in parallel. v2 continued recording real data, while v3 was developed as a clean greenfield.
     Data and schemas were isolated to avoid cross-version contamination.

- (expanded)
   - Schema changes were versioned using Alembic, and data was reshaped into a new Postgres schema rather than reused directly.
     The goal wasn’t zero risk, but reversible risk during evolution.

<!-------------------------------------------------------------------------------------------
  -------------------------------------------------------------------------------------------
  ------------------------------------------------------------------------------------------->

- [ ] <Scope-control-4> For all:

  - Those were consciously scoped out to control complexity.

  - That was a deliberate trade-off.
    Given the system’s stage, I optimised for X and explicitly didn’t pursue Y.
  
  - When asked broad design questions, I usually anchor the answer to one concrete concern, 
    like safety or change isolation, rather than passing over all aspects.
  
  - From a change-isolation perspective …

  - The main concern here was safety rather than features …

- [ ] <Scope-control-4-1> How did you design API? 

  - (...about whehter your API, changes .. are stable and you took version / contract into account)
  - I focused on keeping the API as a stable contract. 
    The main concern wasn’t endpoint shape, but preventing internal changes from leaking outward

  - If you mean API design from a safety and evolution perspective…
  - From a change-isolation perspective, the API was intentionally thin…
  - “There are many aspects of API design, but the most important one in this system was…”

- [ ] <Scope-control-4-2> Why did you structure it this way? 
  
  - Because uncontrolled change was the biggest risk as the system grew

- [ ] <Scope-control-4-3> How did you handle validation / errors?
  
  - (...no more details about HTTP code and Pydantic details)
  - Validation errors were stopped at the boundary, so invalid requests never reached domain logic.

- [ ] <Scope-control-4-4> How complex was the data model?

  - (...don't describe schemas structure)
  - The complexity wasn’t in the number of tables, but in controlling how changes propagated.


<!-------------------------------------------------------------------------------------------
  -------------------------------------------------------------------------------------------
  -------------------------------------------------------------------------------------------> 

- [ ] <follow-up-5-1> ...about system itself

- What kind of system challenges is the team dealing with right now?

  - ... That makes sense — is that complexity more around data, or around coordinating changes?
  - ... Is most of the complexity coming from data, scale, or just feature velocity?

--------------------------------------------------------------------------------------------------------

- [ ] <follow-up-5-2> ...about boundary & ownership

- How do you usually define ownership for systems or components in the team?
- What does ownership look like for someone in this role after six months?

  - When something breaks in production, how do you usually handle it?

--------------------------------------------------------------------------------------------------------

- [ ] <Follow-up-5-3> ...about decisions

- When core parts of the system need to change, how are those decisions usually made?


<!-------------------------------------------------------------------------------------------
  -------------------------------------------------------------------------------------------
  ------------------------------------------------------------------------------------------->

- [ ] <Wrap-up-6-1> 

- No, I think we’ve covered the important parts. I really appreciate the discussion.

- I’m particularly interested in roles where I can take ownership of a system 
  and help it evolve safely over time. Thanks again for the discussion.

<!-------------------------------------------------------------------------------------------
  -------------------------------------------------------------------------------------------
  ------------------------------------------------------------------------------------------->

- [ ] <Hiring-7-1> ..about contract

- 



