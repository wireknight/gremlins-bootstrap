# LEDGER.md — the current-shape bootstrap ladder

Coordination state for rebuilding the runtime from cards in an empty tree under the card discipline. The
bootstrap scripts and runtime target **pi** (`pi` + `pi-subagents`) and `gh`. All 19 cards are drafted in
full form under `cards/`, each with its six-answer DESIGN SELF-CHECK, and routed through one seven-role
registry (`designer`, `implementer`, `verifier`, `qa`, `advisor`, `judge`, `mechanical`) rather than
hardcoded model names. Amendments and follow-ups are written by `designer` in words only.

## The honesty clause

This repository ships no runtime source code: only this ledger, README, `PROTOCOL.md`, `BOOTSTRAP.md`,
the 19 cards, `file_cards.py`, `merge_card.py`, an Apache-2.0 `LICENSE`, and the findings documents
under `docs/findings/`. Stage 0 builds execution
machinery itself; until then, cards execute under `PROTOCOL.md` in role-separated local sessions. The
contract, not the tooling, is the discipline. The original toolkit these cards restate is private and is
not disclosed here; the cards carry design decisions as falsifiable tests.

The current boundary is **every AI step local, GitHub Actions for model-free builds and long test lanes**.
The October 21 pointer, READ-receipt and remote-cloud design is superseded. `remote:start` and cloud-step
claim/start/check/park/resume/release are retained only as refusals with retirement wording.

## Stage gates

A stage is done when every NORMAL card in it has landed (exact red confirmed by a different family,
mutants killed twice, final review read, receipts under `.cards/evidence/<card>/`), the battery is green
on the integration tip, any required collection push reads READY after B5.1 lands, and the stage close-out
is written to `docs/findings/`. The next stage's cards may not branch before.

TEST-ONLY STRENGTHENING and small-fix are runtime exceptions with their own proof shapes in PROTOCOL.md,
not permission to skip a NORMAL ladder card's red-first evidence. Bootstrap automerge accepts NORMAL
implementation cards only.

## Guidance and its precedence

Every card cites its guidance: **the card outranks everything while in flight; the repo's own docs outrank
the articles; the articles supply the why.** A divergence goes to the measure desk before amendment.

| Stage | Article (the why-layer) |
|---|---|
| 0 | The Card Is the Contract (local steps; handoffs and recovery; no one-run path; two exceptions) |
| 1 | The Enforcement Pipeline (hook ladder); Dura Lex, Sed Lex (inject + enforce; fail loud) |
| 2 | The Card Is the Contract (seven roles; local-only AI plus model-free compute; verifier and QA at max); Never Ask a Model If It's Right (independence by assignment) |
| 3 | A Million Tests Is Still a Survey (failing-first; survey honesty); The Anti-Rot Machine (the sweep); Never Ask a Model If It's Right (evidence-triggered doubt ladder) |
| 4 | The Card Is the Contract (model-free Actions; local admission/build lock; host shapes; real mutants; cost guard) |
| 5 | A Million Tests Is Still a Survey (battery honesty); The Card Is the Contract (recorded reds; push readiness); The Anti-Rot Machine (generated views; anchors; doctor) |

## The two acts

**Act I builds the card machinery itself** (stages 0-2: local steps, handoffs, recovery, enforcement and
router). It runs under [PROTOCOL.md](PROTOCOL.md), with the operator or coordinating agent dispatching
phases. Integration moves by operator merge or, for NORMAL cards in bootstrap mode, model-free
`merge_card.py`.

**Act II uses that machinery to build everything else** (stages 3-5: specialists, model-free and local
compute, battery and docs gates). From stage 3 on, the runtime dispatches cards from this ledger. The
protocol remains the audit specification.

The boundary is stage 2's exit gate. The runtime dispatching itself is the moment the builder becomes the
built.

## Local-only execution, model-free GitHub compute

Once B2.2 lands, `local:start` is the only admitted start. It records `Execution: local` and accepts a
goal, any readable ledger, or both. Every AI desk runs locally with B0.2 handoffs and B0.3 recovery.
`status` reads state without dispatching.

Local mode may call `gh-build.py run`, `gh-full-lanes.py run`, `gh-snapshot.py publish` and `gh-wait.py`
for model-free work under their caps and spending guard. No tool can start a cloud AI task. `remote:start`
and the six retired cloud members refuse before configuration reads, GitHub calls or state changes.
`WORKFLOW_MODE=remote` is never a current choice; legacy remote state is labelled RETIRED.

## Stage 0 — local execution machinery (Act I)

Every card here first runs under [PROTOCOL.md](PROTOCOL.md), because the machinery does not exist yet.

- **B0.1 steps** (D-C-T-R-F-V-B-M): seven local markdown step files (design,
  card-check, `s1`, `vr`, `s2`, `vf`, final), semantic outcomes, role/`may_add` bindings, normal order
  plus exactly two exceptions, `vr`/`vf` provenance, final changed-function RAN/SKIPPED evidence, and no
  live READ-receipt or cloud-task contract.
- **B0.2 handoff** (D-C-T-R-F-V-B-M): the local desk brief
  with explicit role and `model:effort`, rolling DRAFT report, HANDOFF done/next/restore anatomy,
  close-only completion sentinel, and OK/WATCH/HANDOFF/UNKNOWN size watch. No proof-of-reading claim.
- **B0.3 recovery** (D-C-T-R-F-V-B-M): durable run root, per-child status and sentinel completion,
  session-wide TODO without second writers, bounded same-child resume for retryable cuts, fresh relaunch
  for request-size/stopped runs, journaled `reuseFrom`, and IF-CUT originals restored hash-proven before
  any resume/relaunch.
- **B0.4 profiles** (D-C-T-R-F-V-B-M): seven thin profiles (`designer`,
  `implementer`, `verifier`, `qa`, `advisor`, `judge`, `mechanical`) binding the local step, rolling
  report, STOP and each role's permission boundary.

## Stage 1 — enforcement cores (Act I)

- **B1.0 anchors**: `@Anchor(file=..., anchor=..., quote=...)` and `HR-N`, quote-verified by one
  `lint-anchors.py`, including staged `--index`; the fixer never invents a missing target.
- **B1.1 digest**: generated union digest, smallness by reference, loud per-layer budgets, conflicts
  flagged rather than merged, no silent truncation.
- **B1.2 inject**: session-start numbering slice and compaction re-arm, fail loud; project doctrine
  resolves from SESSION cwd, not a child desk's cwd.
- **B1.3 write-gate**: pending-overlay doctrine lint, advisory by default, blocking under strict switch,
  three-part refusal and audited override.
- **B1.4 hooks**: deterministic pre-commit and pre-push, env-scrubbed, linked-worktree guarded, honest
  skips, owned watchdog cleanup; local pre-push remains unbypassed even when mechanical integration calls it.

## Stage 2 — the router (Act I; the runtime starts dispatching itself)

- **B2.1 roles**: one seven-role registry, optional second implementer by explicit ref, verifier and QA at
  max, advisor without verdict authority, judge only on evidence triggers, bounded mechanical writes,
  fresh different-family provider recovery by complexity with evidence provenance.
- **B2.2 kickoff**: ledger-generic `local:start`, model-free GitHub compute admitted, cloud AI and
  `remote:start` refused before effects, read-only status with legacy remote marked RETIRED.
- **B2.3 router**: per-line field capture, missing/empty/contradictory fields refused, work-class/executor
  collisions named with the fix, sticky routes, QA by explicit ref, judge/advisor explicit only, and the
  bounded small-fix lane.

## Stage 3 — specialists (Act II)

- **B3.1 qa**: a separate max-pinned QA role for quality passes and bug scans, stable finding records,
  found-nothing and COVERAGE_GAP reported, tree unchanged, never acceptance; cheap first-pass review stays
  on verifier.
- **B3.2 investigate**: concrete propositions, counterexample-carrying REFUTED, and read-only judge with
  `UPHOLD` / `REOPEN` / `EXPAND_SCOPE` / `NEEDS_HUMAN`, invoked only on INDETERMINATE, ESCALATED,
  contradiction or high-stakes partial. Advisor disagreement alone is not the trigger.
- **B3.3 synchronize**: two-direction consistency sweep, dangling edges and stale multiplicities,
  generated-view completeness, stable findings ids, no auto-repair.

## Stage 4 — model-free and local compute (Act II)

- **B4.1 build**: local-mode model-free Actions builds of exact bytes, env-only inputs, conclude before
  upload, six outcome classes, exactly one local rerun for designated failures, real-mutant pre-dispatch
  checks, run/disk/rate caps and per-session cost ledger with optional spending guard. No cloud AI writes.
- **B4.2 local-compute**: host/provider admission with durable HELD queue, host-wide build lock with
  admission-cited DONE evidence, conservative liveness and owned cleanup, nine-key local-lane manifests,
  and real-or-simulated host-shape coverage. This replaces the retired remote environment/controller.

## Stage 5 — battery and docs gates (Act II)

- **B5.1 battery**: per-suite caps and honest skips, complete shards, same-SHA reconciliation, cleared
  remote reds recorded against investigation cards, no second rerun, and `push-ready.py` reading one
  manifest with tracked named rules; non-READY means no push while independent pre-push still runs.
- **B5.2 docs-gates**: one anchor linter and one consistency sweep invoked by entry point, generated views
  and template render-check, doctor's hook classifications and linked-worktree guard, battery
  registration, and unreadable in-scope docs reported INCOMPLETE rather than clean.

## Standing desks

- **Card-writing [`designer`, words only]**: writes later cards and all six self-check answers; creates
  mutants; never runs one.
- **Measure [`mechanical` or `verifier`]**: any "card says X, code says Y" divergence becomes a measurement
  card before amendment. Mechanical desks never resolve it with a hand-written edit.
- **Integration [`mechanical`]**: after the machinery lands, performs named clean merges, generated-file
  commits, local batteries, reconciliations and pushes through the unbypassed local gate. A conflict or
  judgment STOPs; coordinator diagnoses and routes, never resolves inline. While bootstrap automerge is
  enabled, however, it remains the ONLY landing path for a NORMAL card; mechanical integration applies
  outside that opt-in and to lanes the red-first script cannot accept.

## Done when

1. Every NORMAL card has receipts and a close-out on its issue; exceptions carry their own declared proof.
2. The full battery is green on the integration tip from clean checkouts, twice (a cache is not a rerun).
3. After B5.1, every collection push has a model-free READY result and the independent pre-push gate runs.
4. Bootstrap automerge is sunset with `merge_card.py --disable-automerge`; the operator holds the push again.
5. The final findings doc records cards opened and closed, commits, mutants killed, send-backs and
   amendments, wall time, and what the articles got wrong. That list feeds later installments.
