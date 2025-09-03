# ================================
# Ryan-Style 3-Step Vibe Coding Prompt (Universal)
# ================================
# Editor: Cursor / Claude Code / Windsurf (any)
# Files (if available): @create-prd.md, @generate-tasks.md, @process-task-list.md
# Principle: One small step at a time → Review → Approve → Next
# ================================

[Step 1/3] Create PRD (제품 요구서; PRD)
System/DevTool:
- If the file @create-prd.md is present, strictly follow it.
- Otherwise, follow the rubric below to produce a PRD.
User:
- Feature name: <짧은 제목>
- Context files to reference: <@file1 @file2 ...>

Assistant (Do):
1) Write PRD as markdown: PRD-<slug>.md
2) Include sections:
   - Problem & Users(문제/사용자/가치)
   - Goals & Non-goals(목표/비목표)
   - Scope & UX flows(범위/주요 흐름)
   - Constraints(제약: API/Rate-limit/Security/Perf)
   - Dependencies(의존성)
   - Acceptance Criteria(수용기준: 테스트 가능 문장)
   - Observability(로그/메트릭/리커버리)
   - Risks & Rollback(위험/롤백)
3) Ask 3–5 clarification questions if the PRD has gaps.
Stop after producing the PRD. Wait for approval.

----------------------------------------------------

[Step 2/3] Generate Tasks from PRD (태스크 분해)
System/DevTool:
- If @generate-tasks.md exists, use it.
- Else, use the rubric below.
User:
- Input PRD: @PRD-<slug>.md

Assistant (Do):
1) Create a hierarchical task list markdown: tasks-<slug>.md
2) Numbering: 1, 1.1, 1.2, 2, 2.1 ...
3) For each task include:
   - Description(무엇을/왜)
   - Acceptance Criteria(검증 기준)
   - Test Plan(테스트 단계/샘플)
   - Risk & Rollback(위험/되돌리기)
   - Effort(대략 난이도/예상시간)
   - Touch Points(수정 파일/모듈 예상)
4) Add “Persistent Notes” section to track: touched files, unexpected findings, useful links.
Stop after producing tasks-<slug>.md. Wait for approval.

----------------------------------------------------

[Step 3/3] Process Task List (한 번에 하나, 실행/검증 루프)
System/DevTool:
- If @process-task-list.md exists, use it.
- Else, follow the loop below.
User:
- Start with task: <e.g., 1.1>

Assistant (Loop for each single task):
1) Plan: Summarize the exact changes and impact scope (no unrelated refactors).
2) Implement: Propose patch/diff or code blocks; list created/modified files.
3) Self-test: Run or describe tests; show results/logs (or dry-run reasoning).
4) Verify: Map results to Acceptance Criteria; note residual risks.
5) Ask: “Approve, Revise, or Stop?” and wait.
   - If “Revise”: apply only requested changes; show new diff/results.
   - If “Approve”: mark the task done in tasks-<slug>.md and propose next task id.
   - If blocked/missing info: ask precise questions (max 3).
Guardrails:
- Never process multiple tasks at once.
- Never introduce secrets; request env/keys via placeholders.
- Respect constraints (rate-limit, security, perf).
Stop after each task and wait for approval.

# (Optional) Editor Shortcuts
# Cursor: “Use @create-prd.md” → “Take @PRD-<slug>.md and use @generate-tasks.md” → “Use @process-task-list.md; start task 1.1”
# Claude Code: Use plan-mode; mount the three rule files; then run Step 1 → 2 → 3.

# End of Prompt
