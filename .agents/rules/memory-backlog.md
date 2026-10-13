---
trigger: always_on
---

# SYSTEM RULE: CONTINUOUS MEMORY & STATE MANAGEMENT

## 1. CORE DIRECTIVE
You operate in a continuous, state-driven environment. Because you lack persistent episodic memory between individual turns, you MUST treat the project's external memory and running backlog as your single source of truth. Every execution cycle must strictly adhere to the Read-Execute-Update loop to prevent context loss and architectural drift.

## 2. PHASE 1: CONTEXT INGESTION (READ)
Before executing any user command, writing code, or making system changes, you must:
* **Load System State:** Read the designated memory file(s) to understand the current architecture, established patterns, and recent structural changes.
* **Assess the Backlog:** Review the running To-Do/Needs-to-be-Done list to understand immediate priorities, pending blockers, and incomplete multi-step operations.
* **Acknowledge Context:** Formulate your response or execution plan strictly within the boundaries of the established state. 

## 3. PHASE 2: EXECUTION 
Execute the user's request while maintaining high cohesion and low coupling with the existing system state. 
* Do not introduce new dependencies or architectural shifts without updating the system rules.
* If a requested task spans multiple parts or cannot be completed in a single turn, immediately log the remaining steps into the active To-Do list.

## 4. PHASE 3: STATE & BACKLOG UPDATE (WRITE)
Upon completing your primary task, you are strictly required to update the system state before concluding your turn:
* **Update System Memory:** Document *how* the system works now. If your actions changed workflows, configurations, or operational rules, rewrite the relevant memory sections to reflect the new reality. 
* **Groom the Backlog:** 
  - Cross off or delete tasks that were successfully completed during this cycle.
  - Append new requirements, edge cases discovered, or pending refactors to the running To-Do list.
* **No Orphaned State:** Ensure no system changes exist solely in your temporary context window. If it matters for the next cycle, it must be written to memory.

## 5. MEMORY FILE STRUCTURE (EXPECTED FORMAT)
When reading or writing memory, enforce the following structure:
* **[SYSTEM STATE]:** High-level architectural rules, active tech stack configurations, and operational logic.
* **[RECENT CHANGES]:** A brief ledger of what was modified in the last 1-2 execution cycles.
* **[ACTIVE BACKLOG]:** The running To-Do list, categorized by `[BLOCKED]`, `[IN PROGRESS]`, and `[PENDING]`.