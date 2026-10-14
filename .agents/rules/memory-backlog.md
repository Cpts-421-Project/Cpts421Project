---
trigger: always_on
---

# SYSTEM RULE: CONTINUOUS MEMORY, STATE & STRUCTURE MANAGEMENT

## 1. CORE DIRECTIVE
You operate in a continuous, state-driven environment. Because you lack persistent episodic memory between individual turns, you MUST treat the project's external memory, running backlog, and production structure documentation as your single source of truth. Every execution cycle must strictly adhere to the Read-Execute-Update loop to prevent context loss, architectural drift, and orphaned code.

## 2. PHASE 1: CONTEXT INGESTION (READ)
Before executing any user command, writing code, or making system changes, you must:
* **Load System State:** Read the designated memory file(s) to understand the current architecture, established patterns, and operational logic.
* **Map Production Structure:** Review the active directory layout and structural map. You must know exactly where specific domains, services, and components live before writing a single line of code.
* **Assess the Backlog:** Review the running To-Do/Needs-to-be-Done list to understand immediate priorities, pending blockers, and incomplete multi-step operations.

## 3. PHASE 2: EXECUTION 
Execute the user's request while maintaining high cohesion and low coupling with the existing system state and production structure.
* Respect the existing file hierarchy. Do not create new directories or configuration files outside of the established structural rules.
* If a requested task spans multiple parts or cannot be completed in a single turn, immediately log the remaining steps into the active To-Do list.

## 4. PHASE 3: STATE, STRUCTURE & BACKLOG UPDATE (WRITE)
Upon completing your primary task, you are strictly required to update the project documentation before concluding your turn:
* **Update System Memory:** Document *how* the system works now. If your actions changed workflows, configurations, or operational rules, rewrite the relevant memory sections.
* **Track Production Structure:** If you created, moved, or deleted a file, service, or directory, you MUST update the structural map. Code cannot exist without being mapped.
* **Groom the Backlog:** 
  - Cross off or delete tasks successfully completed during this cycle.
  - Append new requirements, edge cases discovered, or pending refactors to the running To-Do list.
* **No Orphaned State:** Ensure no system changes exist solely in your temporary context window. 

## 5. MEMORY FILE STRUCTURE (EXPECTED FORMAT)
When reading or writing memory, enforce the following structure (this can live in a single `.agent_memory.md` file or split across multi-level READMEs):

* **[SYSTEM STATE]:** High-level architectural rules, active tech stack configurations (e.g., FastAPI, React, Docker), and operational logic.
* **[PRODUCTION STRUCTURE]:** A live, hierarchical map of the codebase. Defines exactly what modules/directories exist, what they are responsible for, and where new files in that domain should be placed.
* **[RECENT CHANGES]:** A brief ledger of what was modified in the last 1-2 execution cycles to maintain immediate temporal context.
* **[ACTIVE BACKLOG]:** The running To-Do list, categorized by `[BLOCKED]`, `[IN PROGRESS]`, and `[PENDING]`.