# BOOTSTRAP.md — instructions for the pi agent

You are the **coordinator** for rebuilding a self-verifying agent workflow runtime from this card set.
The user gave you a target repository (`<owner>/<repo>`). Everything below is for you to run; the user
does at most two things (see "What only the human does").

This repository contains no runtime source code: only `LEDGER.md`, `README.md`, `BOOTSTRAP.md`,
`PROTOCOL.md`, `LICENSE`, `file_cards.py`, `merge_card.py`, the 19 cards in `cards/`, and the
findings documents under `docs/findings/`. Read `README.md` for the contract and `PROTOCOL.md` before
dispatching anything. **Precedence: the card outranks everything while in flight; this repository's docs
outrank the articles; the articles supply the why.**

Runtime: **pi** (`pi` + `pi-subagents`) with `gh`. Dispatch phases as separate local `subagent` runs,
each with an explicit role and resolved `model:effort`; never inherit your own model.

## Step 1 — bootstrap the target repository (one command)

Ask for `<owner>/<repo>` only if the user did not give it. Then run:

```bash
python3 file_cards.py --bootstrap --repo <owner>/<repo>
```

It is idempotent: it checks `gh` authentication, creates the private repository if absent, seeds
`LEDGER.md`, `PROTOCOL.md` and `LICENSE`, and files all 19 cards, skipping titles that already exist.
Every `gh` call is time-boxed (`CARDS_GH_TIMEOUT`, default 60 s, writes 3x); a timeout is re-checked by
re-listing issues, so it cannot create duplicates.

Read the **last stdout line** and exit code:

| Result | Meaning | What you do |
|---|---|---|
| exit 0, `BOOTSTRAP OK repo=... filed=N skipped=M cards=19` | done | go to Step 2 |
| exit 2, `AUTH-ERROR not-logged-in ...` | `gh` is not logged in | stop and ask the human; re-run after |
| exit 2, `AUTH-ERROR gh-missing ...` | `gh` is not installed | tell the user to install it; re-run after |
| exit 2, `REPO-ERROR ...` / `SEED-ERROR ...` / `FILE-ERROR ...` | the line names the fix | apply it; re-run |
| exit 1, `CARD-ERROR ...` | a card or one of its six self-check answers is malformed | report verbatim; do not edit cards to hide it |

Never work around an error by hand-editing issues or files: re-run the command. It is the only writer.

### Where the work happens

This card-set clone holds only scripts and cards. Build the runtime in a **separate clone of the target
repository**, next to this one:

```bash
gh repo clone <owner>/<repo> ../<repo>
```

Work in that clone's main tree (no isolated worktrees for code-producing phases). Each card works on
`card/<N>` (`<N>` = issue number), created from the integration branch and **pushed to origin** with
`git push -u origin card/<N>`, because `merge_card.py` reads the branch, evidence and issue from GitHub.
Commit by explicit pathspec, never `git add .`, and never amend, rebase a pushed branch, or force-push.

## Step 2 — verify

```bash
gh issue list -R <owner>/<repo> --state all --limit 50 --json number,title
```

There must be exactly 19 issues, one per card title in `LEDGER.md`. More than 19 means duplicates: stop
and report; do not delete anything.

## Step 3 — start LOCAL, the only execution mode

Every card and every AI step runs on this host. Do not ask whether to run remote: `remote:start` and all
cloud-step claim/start/check/park/resume/release members are retired and must refuse before effects.
Once the relevant cards land, local mode MAY dispatch model-free builds and long test lanes to GitHub
Actions (`gh-build.py`, `gh-full-lanes.py`, `gh-snapshot.py`, `gh-wait.py`). GitHub is compute, not an
agent host.

## Step 4 — run Act I (stages 0 to 2) under PROTOCOL.md

Work through `LEDGER.md` in ladder order: B0.1 to B0.4, B1.0 to B1.4, B2.1 to B2.3. For each NORMAL
card, run phases D, C, T, R, F, V, B, M from `PROTOCOL.md`, **each as a separate local subagent run in
its own context**:

- `designer` writes or amends words only and answers all six DESIGN SELF-CHECK items; `verifier` (a
  different family than `implementer`) runs card-check, red confirmation and verification; `implementer`
  writes the red test alone, then the fix and mutants; final review is `designer`.
- During Act I, the verifier may run the seed bug scan. After B3.1 lands, `/qa` and bug scans use the QA
  role at max by explicit ref, never generic issue routing. QA never accepts.
- `advisor` is optional and never gives a verdict. `judge` is read-only and enters only when an
  investigation returns INDETERMINATE or ESCALATED, or a contradiction or high-stakes partial verdict
  remains. Coordinator/advisor disagreement alone is not the trigger.
- Every phase maintains B0.2's rolling report and commits its evidence under `.cards/evidence/<card>/`.
  Completion means the final sentinel and required evidence, not a claim that a model read something.
- A phase that cannot meet its standard answers STOP and touches nothing. A red that differs from the
  card returns to design for a written amendment. Expected reds are results, not trouble.
- Never run a normal card in one context. Never let implementer verify or verifier implement. Apply
  TEST-ONLY STRENGTHENING and small-fix only under their exact PROTOCOL.md eligibility and proof rules;
  there is no third exception.
- Resolve roles through the user's bindings. Implementer and verifier must be different families. If
  fewer than two families are available, stop and ask.

Ask only blocking questions, batched. State non-blocking assumptions and continue.

## Landing a NORMAL card: bootstrap automerge

A repository created by `file_cards.py --bootstrap` has opted in (`.cards/AUTOMERGE`). When a NORMAL
implementation card reaches `ACCEPTED`, land it with the script, never by your own judgment:

```bash
python3 merge_card.py --repo <owner>/<repo> --card <N> --dry-run   # checks only
python3 merge_card.py --repo <owner>/<repo> --card <N>             # fast-forward
```

The script refuses unless `card/<N>` is a clean fast-forward, red-first receipts are committed under
`.cards/evidence/<N>/`, and the issue's verdict lines end `RED-CONFIRMED`, `VERIFIED`, `ACCEPTED` in
that order. TEST-ONLY and small-fix lanes do not have those receipts and cannot use this gate.

On a refusal, do what the line says. If the integration tip moved, forward-merge that tip into the card
branch with an ordinary merge commit and re-run phase V on the merged tree. Never rebase, force a merge,
push integration yourself, or bypass the script.

With `--no-automerge`, or after sunset, `merge_card.py` answers `MERGE-REFUSED automerge-off`: prepare
the exact fast-forward commands in an issue comment and tell the user; the push is theirs.

**Sunset:** when the ladder is done, run
`python3 merge_card.py --repo <owner>/<repo> --disable-automerge` and tell the user the push is theirs.

## The two things you never do

1. **Never move integration except through `merge_card.py`**, and never at all once automerge is off.
2. **Never edit a card to make a phase pass.** An amendment is written in words by `designer` on the
   issue and the card is checked again.

## What only the human does

1. **Log in to GitHub once**: `python3 file_cards.py --login` (or `gh auth login --scopes repo,workflow`,
   or export `GH_TOKEN` with those scopes). Browser/device approval is not an agent task.
2. **Nothing during the run** with bootstrap automerge enabled. With `--no-automerge`, merge and push
   when the agent reports a NORMAL card `ACCEPTED`. Either way, the push is yours after sunset.

## Done when

Stage 2 lands the seven-role registry, local-only kickoff and router. From then on, hand the coordinator
role to the runtime and let it dispatch stages 3 to 5 from `LEDGER.md`:

```text
local:start ledger LEDGER.md :: Run the bootstrap ladder. Ask only blocking questions.
```

Every AI step stays local; stages 4 and 5 add model-free GitHub builds, local admission/build locks,
same-SHA reconciliation and push-readiness checks. Before a collection push after B5.1, `push-ready.py`
must print READY; non-READY means no push, and the independent pre-push gate still runs.

When B5.2 has landed and the full battery is green twice from clean checkouts (a cache is not a rerun),
end the sunset with `merge_card.py --disable-automerge`. The final findings document records cards opened
and closed, commits, mutants killed, send-backs and amendments, wall time, and **what the articles got
wrong**.
