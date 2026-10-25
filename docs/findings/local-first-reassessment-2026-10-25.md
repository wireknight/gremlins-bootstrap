# Bootstrap local-first reassessment — 2026-10-25

## Bottom line

The October 21 card set has been re-derived for the current architecture: **every AI step runs locally;
GitHub Actions is model-free build/test compute**. The ladder remains at 19 cards. Pointer, READ-receipt,
and remote-cloud cards were replaced by local handoff, recovery, and local-compute cards. This was a
specification and validation pass; no bootstrap replay has run yet.

## Inputs and scope

| Item | Value |
|---|---|
| Prior bootstrap tip | `8513efb` (2026-10-21) |
| Current architecture reference | Toolkit `eab9b5d` (2026-10-25) |
| Files changed | 19 cards, 4 operator documents, `file_cards.py`, `merge_card.py` |
| Files added | Three replacement cards plus this findings document |
| Out of scope | Executing the ladder, publishing the repository, rebuilding article PDFs |

Canonical reference surfaces read during the pass were the current workflow, issue-card template, and the
operator rulings for cloud-AI retirement, role split, design self-check, test-only strengthening, small-fix,
run evidence, provider recovery, host shapes, local admission/build lock, and push readiness.

## Architecture mapping

| Superseded October 21 shape | Current shape |
|---|---|
| `B0.2-pointer.md` | `B0.2-handoff.md`: explicit local role/model, rolling report, HANDOFF anatomy, size watch |
| `B0.3-receipt.md` | `B0.3-recovery.md`: durable run state, sentinel completion, resume/relaunch, IF-CUT restore |
| Six roles, QA on verifier | Seven roles with a separate max-pinned QA role |
| Advisor involved in adjudication | Advisor gives second opinions only; judge enters on evidence triggers |
| `local:start` versus `remote:start` | Local-only AI; remote start and cloud members refuse before effects |
| `B4.2-remote-env.md` | `B4.2-local-compute.md`: admission, build lock, local manifests, host shapes |
| Local mode refused GitHub builds | Local mode may dispatch model-free Actions builds and long lanes |
| Final review without coverage map | Changed-function RAN/SKIPPED evidence with an uncovered/all-skipped HOLD |
| One order presented as absolute | Normal order plus exactly TEST-ONLY STRENGTHENING and small-fix |
| Rebase after a moved tip | Ordinary forward-merge into the card branch, then fresh verification |
| Automerge by receipts alone | Automerge additionally requires a NORMAL implementation issue |
| Unreadable docs could vanish | Unreadable in-scope docs are INCOMPLETE, never clean |

## File map

- `cards/B0.1-steps.md`: seven local contracts, semantic outcomes, evidence and exceptions.
- `cards/B0.2-handoff.md`: local brief, rolling report, completion sentinel, size watch.
- `cards/B0.3-recovery.md`: run-state recovery and IF-CUT restoration.
- `cards/B0.4-profiles.md`: seven thin role profiles and permission boundaries.
- `cards/B2.1-roles.md`, `B2.2-kickoff.md`, `B2.3-router.md`: one role registry, local-only start, routing.
- `cards/B3.1-qa.md`, `B3.2-investigate.md`: QA split and evidence-triggered judge.
- `cards/B4.1-build.md`, `B4.2-local-compute.md`: model-free Actions and admitted local compute.
- `cards/B5.1-battery.md`: same-SHA reconciliation, recorded reds, model-free push readiness.
- `file_cards.py`: renamed order, mandatory six-item self-check validation, lint hygiene.
- `merge_card.py`: NORMAL-only lane guard and forward-merge remedies.
- `README.md`, `BOOTSTRAP.md`, `LEDGER.md`, `PROTOCOL.md`: operator contract synchronized to the cards.

## Validation ledger

| Check | Result |
|---|---|
| `python3 file_cards.py --dry-run` | PASS: 19 unique cards in the renamed order |
| Card sections and self-check census | PASS: every required section once; all six answers in all 19 cards |
| Negative self-check fixture | PASS: missing item 2 refused with the item named |
| Architecture matrix | PASS: 36/36 current-shape obligations |
| Ledger/filer identity | PASS: the same 19 stage entries and filer entries |
| Local Markdown links | PASS: README, BOOTSTRAP, LEDGER, PROTOCOL |
| `ruff check file_cards.py merge_card.py` | PASS after fixing five pre-existing findings |
| `python3 -m py_compile file_cards.py merge_card.py` | PASS |
| `git diff --check` | PASS |
| Control-character scan | PASS: no control characters in source/docs |

### Automerge behavior

- RED first: `require_normal_card` did not exist, so the lane-guard test failed with `AttributeError`.
- GREEN: all 19 filed card bodies pass as NORMAL implementation cards.
- NORMAL variants pass, including `Work class: implementation — description` and Markdown headings.
- TEST-ONLY declarations with both em-dash and hyphen forms refuse `not-normal-card`.
- `Work class: small-fix`, missing work class, and missing Failing test section refuse with steering messages.
- Valid verdict and recovery sequences pass, including a later successful verification after an earlier
  failed verification.
- Unresolved SENT-BACK, NOT-VERIFIED after the last VERIFIED, trailing SENT-BACK, and missing red evidence
  all refuse.

### Text and dependency review

- No old filenames (`B0.2-pointer`, `B0.3-receipt`, `B4.2-remote-env`) remain.
- No `robot` role remains.
- READ-receipt and `remote:start` strings remain only where forbidden, retired, or explicitly historical.
- `rebase` remains only in prohibitions; every remedy is forward-merge plus fresh verification.
- Bootstrap automerge is the only NORMAL-card landing path while enabled. Mechanical integration applies
  outside that opt-in and to lanes the red-first script cannot accept.
- Small-fix routes only to the default Sonnet implementer, never the optional second implementer.

## Remaining work

1. Execute the 19-card replay in a fresh target repository; specification validation is not a replay.
2. Record any divergence between the cards and the implementation they produce, then amend by card.
3. Publish or link the card-set repository only after the operator chooses its public name and venue.
4. Rebuild the companion article's PDF editions after the `fig11` asset path is restored; they remain stale.
