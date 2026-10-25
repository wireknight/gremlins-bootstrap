# PROTOCOL.md — how a seed card runs

The later stages have local step contracts, handoffs, recovery, a router and deterministic gates. The
bootstrap scripts and runtime target **pi** (`pi` + `pi-subagents`) with `gh`. Stage 0 has none of that
machinery yet, and its cards build it. Until then, the discipline is carried by this protocol and three
substitutes:

- **Independence by session.** Design, implementation and verification run in SEPARATE local agent
  sessions (or separate contexts with no shared transcript). A session that wrote the fix cannot verify
  it, whatever its report says.
- **Receipts as work evidence.** Every phase maintains a rolling report, commits evidence under
  `.cards/evidence/<card>/`, and writes its completion sentinel last. Receipts prove commands, bytes,
  outputs and completion. They do not claim to prove that a model read or understood a source; there is
  no READ-receipt stage.
- **The operator is the initial router and gate.** The operator or coordinating agent launches each
  phase's named local role. Before the runtime lands, integration is an operator merge or the scoped
  NORMAL-card `merge_card.py` decision below. After it lands, a mechanical integration desk may perform
  named chores through the unbypassed local gate, never a hand-written edit.

Every AI step stays on this host. Once B4.1/B5.1 land, GitHub Actions may run model-free builds and long
test lanes. `remote:start` and cloud-step claim/start/check/park/resume/release are retired refusals, not
alternative flows.

## The normal order

Phases D, C, T, R, F, V, B, M apply to every NORMAL implementation card. A phase that cannot meet its
standard answers STOP and touches nothing. TEST-ONLY STRENGTHENING and small-fix are defined later and
are the only exceptions.

## Phase D — design (words only)

- Pickup: `designer`.
- Reads the request, relevant why-layer articles and the base tree. Produces the full card: routing,
  exact failing test and base failure, mutants (exact edit + killing test + expected failure), scope,
  checks and stop conditions. Writes no code, patch or test and runs no build while designing.
- Answers all six **DESIGN SELF-CHECK** items in the card:
  1. **Claims and pins:** every claim has a named test/check and is no broader than its pins.
  2. **Constants:** no test re-types a production constant; import it or read the fixture.
  3. **Shared state and test order:** shared state and required order are explicit; no leftovers.
  4. **Inherited environment:** every subprocess boundary is checked; writing git commands remove
     `GIT_DIR`, `GIT_INDEX_FILE`, `GIT_WORK_TREE`, `GIT_COMMON_DIR` and `GIT_PREFIX`.
  5. **Mutant kills:** each mutant is traced through the actual assertion that must fail.
  6. **Composition:** in-flight cards on the same paths are named with order, split or merge point;
     `n/a — <why>` is an answer.
- Creates mutants and never runs one. An operator-only decision is NEEDS-DECISION with options and a
  recommendation.
- Receipt: the card file committed alone plus `design.md` under `.cards/evidence/<card>/`, listing
  decisions and rejected alternatives.

## Phase C — card check (before anything is built)

- Pickup: `verifier`, a different family than `designer`.
- Reads the card against the named base: quoted names exist exactly once or are declared new at exact
  paths; the failing test and base failure are exact; every mutant is complete; scope is a whitelist.
- Refuses a missing or unanswered DESIGN SELF-CHECK item, naming the first gap. The checker fixes nothing.
- A defect returns the card to D with a written amendment; it is never repaired in C.
- Receipt: PASS or FAIL with itemized checks under `.cards/evidence/<card>/card-check.md`.

## Phase T — TDD, the red (test alone)

- Pickup: `implementer`.
- Writes ONLY the card's failing test and fixtures, runs its command, and records the exact base failure.
  A different failure is STOP back to D, never an adjustment of test or expected message to fit.
- Commits test and fixtures alone by explicit pathspec on `card/<N>`; nothing else rides. The fix and all
  later receipts use the same branch.
- Receipt: red commit sha, command and verbatim output under `.cards/evidence/<card>/red.txt`.

## Phase R — red confirmed (different family, committed bytes)

- Pickup: `verifier`, a different family than `implementer`, in a session that saw none of T.
- Checks out the red commit and runs the card's command on committed bytes, comparing with the card,
  never with the implementer's narration.
- Answers RED-CONFIRMED-N on exact match or RED-NOT-CONFIRMED-N with the observed difference. These are
  bootstrap issue-ledger audit tokens, not a remote step protocol.
- Receipt: command and output under `.cards/evidence/<card>/red-confirm.txt`.

## Phase F — fix and mutants

- Pickup: `implementer` (T's session may continue).
- Writes the specified fix, runs the failing test and green set, and commits by explicit pathspec.
- Applies each mutant ONE AT A TIME. First write `IF CUT WHILE APPLIED:` to `agent-if-cut` in the
  worktree's OWN git directory and save originals in `agent-if-cut.d/`. Apply the exact edit, run the
  named test, observe the stated red, restore, and prove original hashes. Clear the note only after the
  hash-proven restore. A surviving mutant is reported, never hidden or weakened away.
- Receipt: fix sha, green results and a mutant table (edit, test, expected/observed, restore hashes)
  under `.cards/evidence/<card>/fix.md`.

## Phase V — verification (committed bytes, mutants from words)

- Pickup: `verifier`, again independent of implementation.
- Checks out the fix commit, proves the red commit is its ancestor, re-runs checks and the now-green
  failing test. Re-applies each mutant FROM THE CARD'S WORDS, writes its own patch, records patch sha256
  and tree ids before/after in a temporary index (`git read-tree`, `git apply --cached`,
  `git write-tree`), observes the named red, and restores hash-proven with IF-CUT state throughout.
- Produces fresh reports from which a tool derives, for every changed production function, its covering
  tests and whether each RAN or was SKIPPED. This is evidence for M, not a license for V to skip a test.
- Answers VERIFIED-N or NOT-VERIFIED-N with evidence. Receipt: `verify.md` and `provenance.json` under
  `.cards/evidence/<card>/`.

## Phase B — bug scan

- Pickup: `verifier` during Act I. After B3.1 lands, `/qa` and bug scans use the `qa` role at max by its
  explicit ref, never generic issue routing and never the acceptance verdict.
- Hunts what tests do not cover: stated bug classes, scope boundaries, error paths and quiet failure
  modes named by the mutants. Findings are reported, never fixed in this phase. Each invalidating finding
  returns to D; a real out-of-scope finding becomes a follow-up card.
- Found-nothing is recorded. Every skipped surface and reason is recorded; an unreported skip is a
  COVERAGE_GAP, not a clean scan. Pure-documentation cards may skip with the reason recorded.
- Receipt: `.cards/evidence/<card>/bugscan.md` with scope, reading and findings.

## Phase M — final review and landing

- Pickup: `designer`, independent of implementation. `advisor` may give a second opinion but has no
  verdict authority. `judge` is read-only and enters only when investigation returns INDETERMINATE or
  ESCALATED, or a contradiction or high-stakes partial verdict remains; disagreement alone is not the
  trigger.
- Reads the change, card with every comment and all receipts. Does not re-run except when evidence looks
  wrong or incomplete, and says why. Never runs a mutant.
- Reviews the machine-generated changed-function RAN/SKIPPED map. A function whose covering tests all
  skipped, or which has none, HOLDS the card unless the card states why no executed test can exist and
  names the lane that will run it. Rename/move-only functions are reported, not held.
- Always checks the merge onto integration with `git merge-tree --write-tree`, which needs no build.
  If the tip moved, `implementer` forward-merges integration into the card branch with an ordinary merge
  commit and V re-runs on the merged tree. No rebase or forced merge. A semantic conflict returns to D.
- Answers ACCEPTED-N or SENT-BACK-N with the required change in words. The reviewer never lands the work.

Landing then follows exactly one path:

1. **Operator merge (default without opt-in):** the operator merges, fast-forward when possible, and pushes.
2. **Bootstrap automerge (NORMAL implementation cards only):** with `.cards/AUTOMERGE` on integration,
   the coordinator runs `python3 merge_card.py --repo <owner>/<repo> --card <N>`. The script refuses
   unless the card branch is a clean fast-forward, red-first receipts exist under `.cards/evidence/<N>/`
   (`red.txt`, `red-confirm.txt`, `fix.md`, `verify.md`, or `vr/` and `vf/`), and issue verdicts end
   `RED-CONFIRMED`, `VERIFIED`, `ACCEPTED` in that order. It then performs a non-forced ref update and
   posts `MERGED-N`. TEST-ONLY and small-fix lack these receipts and cannot use this gate.
3. **Mechanical integration after the runtime lands:** outside the bootstrap opt-in, and for lanes the
   red-first script cannot accept, the coordinator dispatches one named chore to `mechanical`: clean
   merge, generated-file commit, landing battery, reconciliation, or push through the unbypassed local
   pre-push gate. While bootstrap automerge is enabled it remains the ONLY landing path for a NORMAL
   card. Conflict or judgment STOPs; coordinator diagnoses and routes, never resolves inline. After
   B5.1, `push-ready.py` must also print READY before every collection push.

**Sunset:** when the ladder lands, run `merge_card.py --disable-automerge`. A bootstrap re-run never
re-enables it; only explicit `--automerge` does. The operator holds the push again.

## Declared exception 1 — TEST-ONLY STRENGTHENING

Use only when adding assertions over behavior that already holds, so the base is green by design.

- The card's Failing test section reads `none — TEST-ONLY STRENGTHENING`. There is no T red commit, no R
  re-run of the original card's red, and no production fix.
- The diff touches only test files (the project's configured `test_globs`, or the test paths the card
  names). Every NEW assertion gets one production mutant that removes what it pins; that assertion must
  turn red. Each mutant is restored hash-proven.
- `designer` still creates mutants and never runs them. `implementer` and `verifier` run them as in F/V.
  Verification proves the class green at the follow-up commit and that every new assertion bites.
- Final review and independent roles remain. Bootstrap red-first automerge is unavailable; landing is
  operator or mechanical through the applicable local gate.

## Declared exception 2 — small-fix

Use only for a reviewed batch of cosmetic findings: typos, wording, broken links and anchors, stale
numbers, comments, formatting, and unused code proven unreferenced.

Never include behavior changes, test assertions, installers, git hooks, prompts or other instructions
agents follow, security, or concurrency. An item that turns out bigger leaves the lane and becomes a
NORMAL card.

Flow: coordinator batches findings by area into one branch and dispatches ONE `implementer` handoff with
`Work class: small-fix`. Linters for touched files pass. ONE quick independent check from a different
family confirms, per item, that each edit matches its finding and changes nothing else. The batch record
maps finding id → edit → linter. The coordinator (`designer`) reads the batch diff; the `advisor`
pre-push scan and local pre-push hook still run. The red-test/mutant/separate-full-battery cycle is not
required. The batch merges through the collection, not through red-first bootstrap automerge.

## Cross-cutting rules

1. **Expected reds are results.** T's failing test and F/V's mutants are supposed to be red. Report them;
   do not troubleshoot the fact that they failed as promised.
2. **No one-run path for NORMAL cards.** A session offering to design, test, fix and verify in one go is a
   protocol violation. The two exceptions narrow eligibility and change proof shape, not independence.
3. **STOP touches nothing.** If a standard cannot be met, leave the tree as found and escalate.
4. **Everything lands on the issue.** Amendments, work receipts, verdicts and skips are issue comments;
   the tracker is the ledger from card one.
5. **Receipts are durable.** Stage 0 creates `.cards/evidence/<card>/` by hand. B0.2/B0.3 automate rolling
   reports, completion and recovery. A missing receipt is missing evidence, not a green.
6. **Forward-merge, never rewrite.** Commit by explicit pathspec, never `git add .`, and never amend,
   rebase a pushed branch, or force-push. A moved integration tip is forward-merged and re-verified.
7. **Steering-grade errors and clean hooks (HR-24).** Every LLM-facing CLI/gate says what was measured,
   where/rule failed, and how to fix it. Scrub inherited git environment variables and add no new Python
   or shell lint warnings.

## What changes when the machinery lands

D/C gain local card contracts and the six-item self-check gate. T/R/F/V gain local handoffs, rolling
reports, durable run recovery and IF-CUT tooling. B gains the separate max-pinned QA role. M gains
changed-function coverage evidence and bounded mechanical integration. Builds gain local admission and a
host-wide lock, plus model-free GitHub evidence with same-SHA reconciliation and cost records. Collection
pushes gain model-free readiness. The protocol never becomes obsolete: it remains the specification the
machinery is audited against.
