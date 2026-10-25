# Synchronize report — gremlins-bootstrap

DRAFT status: 22/22 contract-complete outputs; aggregation complete

- Mode: `autofix`
- Severity floor: `info`
- Baseline: `acf4038` (tracked tree clean before specialist edits)
- Repository: `/Users/angel/Desktop/gremlins-bootstrap`
- Aggregation source: only `.synchronize/wave1/` outputs written by this run

## Executive summary

- **43/49 catalogue tokens** were exercised through 20 specialist batches, plus the anchor-alignment
  overlay and the orchestrator-side `skill-agent-drift` check. Six build-specific tokens were not
  dispatched because their input shapes are absent.
- **55 tests pass**, Ruff and `py_compile` pass, `file_cards.py --dry-run` validates all 19 cards, the
  mechanical completeness runner reports **zero category gaps**, anchor lint is aligned, and
  `git diff --check` passes.
- Autofix modified **8 unique files**. Every modification has an owning phase output and a declared
  touch matrix. No `ROLLBACK_REQUEST` was emitted and no build regression was detected.
- The completed formal phase is **NOT_APPLICABLE**, not a proof or a green verification claim. Several
  other phases are also honestly NOT_APPLICABLE because their input shapes do not exist.
- Report-only findings remain visible below; a green test suite does not erase them.
- Two reports omitted the required literal `touched_files` field. The orchestrator normalized
  `touched_files: []` from their explicit zero-edit records without changing any verdict or dispatching
  another phase.

## Execution and recovery record

1. Offline workflow validation succeeded, and the detached probe returned `PROBE_OK`.
2. The initial async workflow used Copilot-backed virtual bindings. Twenty children failed before doing
   phase work because those bindings had no credentials. The formal child completed independently as
   NOT_APPLICABLE. No source file was touched by the failed children.
3. The failed dispatch was preserved at `.synchronize/dispatch-copilot-failed.js`. Only those 20
   unsuccessful phases were redispatched, as fresh runs with direct Z.AI models. The recovery probe also
   returned `PROBE_OK`; all 20 completed. The completed formal phase was not duplicated.
4. The orchestrator-side `skill-agent-drift` check found no local skills directory and was recorded as
   NOT_APPLICABLE rather than PASS or ERROR.
5. Structural output validation found two missing `touched_files` fields. A structural retry was queued
   but host admission held new launches because swap exceeded the operator's 6000 MB ceiling. No launch
   or inline phase analysis occurred. The orchestrator then normalized the two fields from the specialists'
   explicit zero-edit records, preserving every verdict; no further dispatch was required.

## Phase outcomes

| Batch | Covered tokens | Verdict and specialist-reported outcome |
|---|---|---|
| `docs-validator` | phantom-symbols, citations, markdown-links, image-references, spec-references, deleted-symbols, directory-diagrams, shell-paths, aspirational-markers, outdated-markers, implicit-date-markers, doc-structure, toc, doc-hygiene, docs-quality, docs | **FAIL, report-only**: 7 implicit-date warnings in historical Provenance lines; 23 missing-TOC infos; 1 missing docs README outside the matrix. Reference and structure detectors otherwise clean. No fixes. |
| `module-validator` | stale, module-readmes | **NOT_APPLICABLE**: no supported module shape or registry. No edits. Structural retry pending for missing `touched_files`. |
| `meta-validator` | self, agent-quality | **NOT_APPLICABLE**: no self-host or adopter meta surfaces. One report-only mode-detection warning. No edits. |
| `count-claims` | count-claims | **PASS**: all manifest-position counts match. Two info census omissions resolved by the canonical-counts sibling and independently verified; this phase claims no edits. |
| `canonical-counts` | canonical-counts | **PASS**: 2 info census omissions fixed in `BOOTSTRAP.md` and `LEDGER.md`; all other counts verified. |
| `claudemd-alignment` | claudemd-alignment | **NOT_APPLICABLE**: no `CLAUDE.md` or Claude-facing references. No edits. |
| `ci` | ci | **NOT_APPLICABLE for CI config / PASS for doc claims**: no CI system, but CI mentions in docs/scripts are conditional and consistent. Structural retry pending for missing `touched_files`. |
| `docker` | docker | **NOT_APPLICABLE**: no Dockerfiles, compose files, Testcontainers, or image claims. No edits. |
| `code-quality` | metrics, perf, conventions | **PASS**: 1 report-only warning (no convention sources), 2 informational items (one narrow exception pass and uncalibrated thresholds). No mechanical fix eligible. |
| `dry` | dry | **SUCCESS**: `AUTOMERGE_PATH` single-sourced. Two other duplication candidates deferred below threshold. |
| `simplify` | simplify | **PASS**: 5 behavior-preserving simplifications across both scripts; 2 behavior-changing candidates left report-only. |
| `docs-code-alignment` | docs-benchmark, feature-claims, code-examples, code-blocks | **PASS**: examples measured with zero findings; features/compile/benchmarks NOT_APPLICABLE. No edits. |
| `assessment` | assessment | **SUCCESS**: 20 current/historical claims measured with no stale values. Three informational observations; no edits. |
| `tests` | tests | **PASS**: 31 focused regression tests created, all passing. Three report-only observations; production probe had zero net diff. |
| `dead-code` | dead-code | **SUCCESS**: 37/37 symbols and both entry files alive. No edits. |
| `benchmark` | benchmark | **NOT_APPLICABLE**: no benchmark corpus, JMH assets, result JSON, or perf tooling. No edits. |
| `test-docs` | test-docs | **FAIL with open report-only work**: 13 contract tests added, suite 44 passing. Five fixes completed, one partial, and five judgment-required network/stateful cases remain open. |
| `test-completeness` | test-completeness | **PASS after BF-1 fix**: six semantic category gaps closed and a real non-object-comment crash fixed red→green. Suite 55 passing; completeness runner reports zero gaps. Two judgment-required findings remain. |
| `docs-gen` | docs-gen | **PASS**: one info discoverability gap fixed by linking the reassessment findings from README. |
| `formal` | formal | **NOT_APPLICABLE**: no formal target, spec directory, backend wiring, or TLA files. No verdict or edits. |
| `skill-agent-drift` | skill-agent-drift | **NOT_APPLICABLE**: no local skills directory; deterministic script result recorded without calling it a clean zero check. |
| `anchor-alignment` | always-on overlay | **PASS (CLEAN)**: check/fix/normalize all green with zero rewrites and zero citations in effective scope. |

## Autofix modifications

| Owning phase | Files modified | Result |
|---|---|---|
| `canonical-counts` | `BOOTSTRAP.md`, `LEDGER.md` | Completed repository-content enumerations with README, BOOTSTRAP, merge_card, and findings docs. |
| `dry` | `merge_card.py` | Imported `AUTOMERGE_PATH` from `file_cards.py` instead of redefining it. |
| `simplify` | `file_cards.py`, `merge_card.py` | Added `is_not_found` and `paginate_items`, used them at both call sites, simplified `last`, replaced redundant `state == "absent"`, and converted one concatenation to an f-string. |
| `docs-gen` | `README.md` | Added a resolving link to the local-first reassessment record. |
| `tests` | `tests/conftest.py`, `tests/test_file_cards.py`, `tests/test_merge_card.py` | Created offline fake-gh infrastructure and 31 regression tests. |
| `test-docs` | `tests/test_file_cards.py`, `tests/test_merge_card.py` | Added 13 tests for documented branches, exits, timeout, and recovery contracts. |
| `test-completeness` | `tests/conftest.py`, `tests/test_file_cards.py`, `tests/test_merge_card.py`, `merge_card.py` | Added 11 tests for all five TDD categories and guarded non-object comments in `verdict_events`. |

Unique union: `BOOTSTRAP.md`, `LEDGER.md`, `README.md`, `file_cards.py`, `merge_card.py`,
`tests/conftest.py`, `tests/test_file_cards.py`, `tests/test_merge_card.py`.

## Report-only findings and deferred decisions

### Documentation and metadata

- **7 implicit-date warnings** in card Provenance lines are historical revision records. Marker-mode
  autofix does not support implicit-date edits, so no history was rewritten.
- **23 missing-TOC infos** remain. Adding Contents sections to GitHub-issue card contracts is an
  authorial decision, not a permitted mechanical fix.
- **Missing docs README** remains report-only: the matrix allows `docs/findings/**` but not
  `docs/README.md`. The docs-generator did not exceed that boundary.
- **Mode-detection warning** from `meta-validator`: no self-host or adopter signatures exist. The phase
  remains NOT_APPLICABLE unless the operator supplies an override or confirms permanent N/A.
- **Convention-source warning** from `code-quality`: no `CLAUDE.md`, project configuration,
  Ruff config, or project metric thresholds exist. Creating configuration is outside scope and judgment-required.
- **Uncalibrated metrics context** remains unmeasured rather than being misreported as a pass or defect.
- **Inventory-claims context**: references to `scripts/*.py`, `tests/*`, and other target-runtime
  artifacts are work-order specifications, not broken references in this repository. No edits were made.

### Implementation and behavior

- `dry` F-2: the two-use pagination template was initially deferred; `simplify` later extracted it with
  equivalence tests. `dry` F-3 remains deferred because the refusal text differs.
- `simplify` F-6: `api()` still uses a 60-second default rather than propagating `CARDS_GH_TIMEOUT`.
  Changing that default is behavior-affecting and judgment-required.
- `simplify` F-7: the near-duplicate gh-missing refusal has different steering text; no consolidation.
- `assessment` I-1: the external toolkit hash cannot be verified from this repository; the historical
  finding was left unchanged. I-3: README's summary prose is not a manifest enumeration and was not
  mechanically expanded.
- `tests` TQ-3: verdict recognition remains the documented bare-line form; markdown list verdicts are
  not counted. Widening it is a behavior decision. TQ-4: `ACCEPTED == len(events) - 1` is redundant
  defense-in-depth, not a defect, and was left unchanged.
- `test-completeness` JR-1: malformed or empty JSON is handled inconsistently across readers. Deciding
  the correct refusal contract is judgment-required because silently treating it as empty could cause
  duplicate issue creation.

### Remaining test/network coverage

- `test-docs` TD-3: `merge()`'s automerge-off, fast-forward, and evidence-missing paths need a
  stateful multi-response fake and remain open (one CRITICAL-class coverage item).
- TD-7: `seed_file` created/updated/unchanged write behavior needs a stateful fake.
- TD-8: create-timeout re-list recovery needs a stateful fake.
- TD-9: the full-run machine-readable terminal line needs network orchestration coverage.
- TD-10: `CARDS_GH_TIMEOUT` environment override needs safe reload testing.
- `test-completeness` JR-2: login, repo creation, seed writes, list/create failures, actual DELETE,
  merge happy path, and remaining refusals remain judgment-required coverage, not claims of completion.

## Validation record

| Gate | Result |
|---|---|
| `python3 -m pytest tests/ -q` | **55 passed** |
| `ruff check file_cards.py merge_card.py tests/` | **All checks passed** |
| `python3 -m py_compile file_cards.py merge_card.py tests/*.py` | **PASS** |
| `python3 file_cards.py --dry-run` | **19 cards validated** |
| `qa-test-completeness-check.py --scripts-dir . --tests-dir tests --scripts file_cards.py,merge_card.py` | **0 category gaps; all 5 categories covered** |
| `lint-anchors.py --check --dir docs` | **Aligned; no misalignment** |
| `git diff --check` | **PASS** |
| Structural output check | **22/22 contract-complete** |

Sensitivity and red→green evidence:

- The test-quality specialist's initial list-marker verdict pin failed against the real regex and was
  corrected to the documented bare-line contract.
- The test-docs sensitivity mutation to `is_not_found` went red, was reverted byte-identically, and the
  suite returned to green.
- BF-1, non-object comments crashing `verdict_events`, first failed with `AttributeError` at
  `merge_card.py:73`; after the `isinstance(comment, dict)` guard, all 55 tests pass.
- Simplification's behavior-equivalence checks cover empty and varied event sequences, paginated shapes,
  title filtering, and exact refusal text.

## Out-of-scope and concurrency record

- `.claude/cache/deletion-ledger.json` appeared during reference analysis outside every touch matrix.
  It was quarantined at `.synchronize/cache-artifacts/deletion-ledger.json` and recorded in
  `.synchronize/rollback-log.jsonl` as `OUT_OF_SCOPE_EDIT`. No evidence was deleted and `.gitignore` was
  not edited.
- Sibling edits are preserved and attributed to their owning phases. Count-claims explicitly does not
  claim the canonical-counts fixes. DRY does not claim the simplifications. Test phases do not claim
  production refactors. The modification union above is de-duplicated.
- No `ROLLBACK_REQUEST` was emitted. The out-of-scope cache was the only required orchestrator action.

## Explicitly skipped or NOT_APPLICABLE surfaces

- Build-specific tokens not dispatched: `pre`, `gradle`, `alignment`, `javadoc`, `code-javadoc`,
  `docs-javadoc`. Their build inputs are absent (no Gradle or Java/Kotlin project shape).
- Formal verification: no specs or backend target.
- Module registry, Docker, Claude alignment, CI configuration, benchmarks, and local skill-agent drift:
  all probed and reported NOT_APPLICABLE rather than counted as green zero-check passes.
- `spec-references`: no `specs/` directory; reported SKIPPED, not zero.
- Gradle/`--no-daemon`: not applicable because this is a Python repository.

## Close-out

- Structural output validation is complete at 22/22. Commit the autofix changes and this report separately
  with explicit pathspecs. The queued structural probe was never launched and no retry remains necessary.
