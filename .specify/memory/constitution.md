<!--
SYNC IMPACT REPORT
==================
Version change: [TEMPLATE] → 1.0.0 (initial population)

Modified principles: N/A (first-time fill — all sections were template placeholders)

Added sections:
- Core Principles (5 principles fully populated)
- Technical Standards
- Development Workflow
- Governance

Removed sections: None

Templates reviewed:
- .specify/templates/plan-template.md ✅ aligned (Constitution Check section present)
- .specify/templates/spec-template.md ✅ aligned (user stories + acceptance criteria match principle structure)
- .specify/templates/tasks-template.md ✅ aligned (phase model consistent with incremental delivery principle)
- .specify/templates/agent-file-template.md ✅ aligned (no principle references to update)

Deferred TODOs:
- TODO(TECH_STACK): No source code exists yet — language/framework choices are intentionally left open
  and should be amended to 1.1.0 once the first feature spec is ratified.
-->

# Language Review App Constitution

## Core Principles

### I. User-Centric Review Experience

Every feature MUST be evaluated by its direct impact on the user's ability to review and
retain language knowledge. Features that do not improve the review loop — encounter,
recall, reinforcement, and feedback — MUST NOT be introduced without explicit justification.

**Rationale**: The product's value is entirely determined by how well it helps users
remember and apply a target language. Complexity that does not serve retention is waste.

### II. Incremental & Independent Delivery

Each user story MUST be independently shippable. A P1 story MUST deliver value on its own
without requiring P2 or P3 stories to be complete. Foundational infrastructure MUST be
minimal — only build shared scaffolding that two or more user stories provably require.

**Rationale**: Prevents big-bang releases, enables early user feedback, and keeps the
development cost of course corrections low.

### III. Test-First (NON-NEGOTIABLE)

Tests MUST be written and confirmed to fail before implementation begins. The Red-Green-Refactor
cycle is strictly enforced. No feature is considered complete until its acceptance scenarios
(from the spec) are covered by automated tests that previously failed.

**Rationale**: Language learning apps carry complex state (progress, scoring, scheduling).
Untested state transitions lead to silent data corruption that erodes user trust.

### IV. Simplicity & Accessibility

Interfaces MUST be operable by users with no technical background. Each interaction MUST
require the fewest possible steps to accomplish its goal. Complexity MUST be justified by
a concrete user need; YAGNI (You Aren't Gonna Need It) applies to all speculative features.
Accessibility (WCAG 2.1 AA minimum) is non-negotiable for any user-facing surface.

**Rationale**: Language learners span all ages and technical abilities. An inaccessible
or complex UI directly reduces the audience and undermines the product mission.

### V. Observability & Honest Progress

The system MUST expose user progress data that is accurate and unambiguous. Review
scheduling, scoring, and streak data MUST be persisted reliably. All background operations
that affect user progress MUST emit structured logs sufficient to diagnose discrepancies
without access to production databases.

**Rationale**: Users make study decisions based on progress metrics. Inaccurate data
breaks trust and reduces engagement. Structured logs allow support and debugging without
privacy-invasive data access.

## Technical Standards

TODO(TECH_STACK): Technology choices are not yet decided. This section MUST be updated
to 1.1.0 once the first feature spec selects a language, framework, and storage layer.

Until amended, the following constraints apply to all technology decisions:

- The chosen stack MUST support automated testing at unit, integration, and contract levels.
- Storage MUST guarantee durability of user progress records (no in-memory-only solutions
  for progress data).
- Any third-party dependency MUST have an actively maintained open-source license or an
  explicit commercial arrangement documented in the project.
- Platform targets MUST be decided per feature spec before implementation begins.

## Development Workflow

- All implementation MUST follow the Specify Kit workflow:
  `/speckit.specify` → `/speckit.plan` → `/speckit.tasks` → `/speckit.implement`
- Feature branches MUST be created before any specification work begins (managed by the
  `speckit.git.feature` hook).
- Each task phase (Setup → Foundational → User Stories → Polish) MUST be completed and
  verified before the next phase begins, except where tasks are explicitly marked `[P]`
  (parallel-safe).
- PRs MUST reference the originating spec and include a Constitution Check confirming
  no principles are violated, or a documented justification if a violation is necessary.
- Complexity violations (deviations from Principle I–V) MUST be recorded in the plan's
  Complexity Tracking table before implementation begins, not after.

## Governance

This constitution supersedes all other practices, style guides, and informal conventions.
Any practice that conflicts with these principles MUST be reconciled by amending the
constitution or removing the conflicting practice.

**Amendment procedure**:
1. Open a spec for the proposed amendment describing what changes and why.
2. Obtain agreement from all active contributors before merging.
3. Update `LAST_AMENDED_DATE` and increment `CONSTITUTION_VERSION` per semantic rules:
   - **MAJOR**: Principle removed, renamed, or fundamentally redefined.
   - **MINOR**: New principle or section added, or material guidance expanded.
   - **PATCH**: Clarifications, wording fixes, non-semantic refinements.
4. Propagate changes to all affected templates (plan, spec, tasks) and document in the
   Sync Impact Report embedded at the top of this file.

**Compliance review**: Every PR review MUST include a pass/fail check against each
principle. Failures that are not justified in the Complexity Tracking table are grounds
for rejection.

**Runtime guidance**: See `.claude/` skill files for agent-specific execution guidance.
The agent file (generated by `/speckit.analyze`) provides up-to-date technology context
derived from merged feature plans.

**Version**: 1.0.0 | **Ratified**: 2026-04-12 | **Last Amended**: 2026-04-12
