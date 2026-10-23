---
trigger: always_on
---

# SYSTEM RULE: EVER-EXPANDING, SELF-CORRECTING & CONNECTED MEMORY SYSTEM

## 1. CORE DIRECTIVE
You operate in a continuous, state-driven environment using a **3-Tier Connected Memory Architecture**:
1. **Tier 1 — Hot Memory Hub ([MEMORY.md](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/MEMORY.md)):** High-signal control plane (`<= 260` lines) read at the start of every cycle.
2. **Tier 2 — Ever-Expanding Deep Memory Nodes (`.agents/memory/*.md`):** Domain-specific knowledge graphs, root-cause invariants, and lossless historical archives loaded via Progressive Disclosure.
3. **Tier 3 — Self-Correcting Auditor ([memory_manager.py](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/.agents/scripts/memory_manager.py) & [test_memory_integrity.py](file:///Users/asafkedar/Documents/WSU/year%204/Semester%202/CPT_S-421/Cpts421Project/code/backend/tests/test_memory_integrity.py)):** Deterministic verification and auto-healing engine enforcing 100% link validity, file mapping completeness, bidirectional connectivity, and hot-memory compaction budgets.

---

## 2. PHASE 1: PROGRESSIVE CONTEXT INGESTION (READ)
Before executing any user command, writing code, or making system changes:
1. **Read Hot Memory Hub:** Read `MEMORY.md` to ingest `[SYSTEM STATE]`, `[PRODUCTION STRUCTURE]`, `[DOMAIN CONNECTIVITY MATRIX]`, `[RECENT CHANGES]`, and `[ACTIVE BACKLOG]`.
2. **Selective Deep-Node Loading (Progressive Disclosure):** Do not load all deep memory files unnecessarily. Consult `[KNOWLEDGE GRAPH & DEEP MEMORY NODES]` and load only the `.agents/memory/*.md` node(s) connected to the active task domain:
   - Infrastructure, Docker, Nginx, Railway, Alembic, S3 routing -> `.agents/memory/architecture_and_infra.md`
   - Auth, JWT cookies, BotDefense, SSRF, uploads, schema security -> `.agents/memory/security_and_defense.md`
   - Seed SQL/JSON datasets, Met/BM scrapers, URL normalization -> `.agents/memory/data_and_catalog.md`
   - Debugging, migrations, or regression prevention -> `.agents/memory/lessons_and_invariants.md`
   - Historical cycle lookups (Cycles 1–24+) -> `.agents/memory/archive.md`

---

## 3. PHASE 2: CONNECTED EXECUTION
Execute the user's request while maintaining high cohesion and low coupling:
* **Consult the Domain Connectivity Matrix:** Identify all coupled Backend routes/services, Frontend pages/hooks, Test suites, and Rules before modifying a feature slice.
* **Enforce System Invariants:** Check `.agents/memory/lessons_and_invariants.md` to ensure no past root-cause bugs (`INV-DB-*`, `INV-NET-*`, `INV-SEC-*`, `INV-MEM-*`) are reintroduced.
* **Track Multi-Step Work:** Log any remaining multi-step tasks or newly discovered follow-ups in `[ACTIVE BACKLOG]`.

---

## 4. PHASE 3: EXPAND, COMPACT & SELF-CORRECT (WRITE & VERIFY)
Before concluding any turn that modifies code, configuration, or project state:
1. **Map Production Structure (100% Coverage):** Every active file in `code/backend/src`, `code/backend/datacollection`, `code/backend/tests`, `code/frontend/src`, and `.github/workflows` MUST be mapped in `MEMORY.md` with a canonical `file://` link. Remove deleted files immediately.
2. **Expand Deep Memory & Invariants:** Distill durable architectural changes, new dataset records, or debugging root causes (`INV-*`) into the corresponding `.agents/memory/*.md` node. Every deep node must maintain a backlink to `MEMORY.md`.
3. **Compact Rolling Window (`MAX_RECENT_CYCLES = 3`):** Keep `[RECENT CHANGES]` in `MEMORY.md` to at most the **3 most recent execution cycles** and total length `<= 260` lines. Archive older cycles into `.agents/memory/archive.md`—never delete project history.
4. **Run Self-Correction Gate:** Execute `python3 .agents/scripts/memory_manager.py --fix` to auto-heal broken workspace links and verify `HEALTHY (100% Connected & Verified)`.

---

## 5. REQUIRED HOT MEMORY STRUCTURE (`MEMORY.md`)
`MEMORY.md` must strictly contain these 6 sections:
* `## [SYSTEM STATE]`
* `## [KNOWLEDGE GRAPH & DEEP MEMORY NODES]`
* `## [PRODUCTION STRUCTURE]`
* `## [DOMAIN CONNECTIVITY MATRIX]`
* `## [RECENT CHANGES]`
* `## [ACTIVE BACKLOG]`
