# The card set

This repository contains **no runtime source code**. It contains work orders: a ledger and 19 cards
(GitHub issues, filed from `cards/`) that rebuild a self-verifying agent workflow runtime from an empty
tree. The current target shape is **local AI desks with model-free GitHub compute**. There is no live
cloud-agent mode and no READ-receipt stage.

The bootstrap scripts and the runtime they rebuild are designed for the **pi** coding-agent harness
(`@earendil-works/pi-coding-agent` with `pi-subagents`: session-start and tool-call extensions, role
virtual models, async subagent runs and resumable workflow drivers) paired with the GitHub CLI (`gh`).

The original toolkit the cards were derived from is private and stays private. The cards are words, the
words are the spec, and whatever your agents build from them is yours. Nothing here discloses that
toolkit's code, files, or history, only its design decisions, each stated as a falsifiable test.

## The normal card contract

A normal implementation card is a GitHub issue with routing fields (`Pickup`, `Work class`,
`Execution tier`, `Verifier`), a failing test with the exact failure it must show at the base, mutants
(an exact edit, the test that must turn red, the expected failure), a scope, STOP conditions, and a
six-answer **DESIGN SELF-CHECK**: claims and pins, constants, shared state and test order, inherited
environment, mutant kills, and composition with other in-flight cards.

The normal order has no one-run path:

1. the implementer commits the failing test alone and stops;
2. a verifier from a **different model family** confirms the exact failure on committed bytes;
3. the implementer writes the fix and runs the mutants, one at a time, with an IF-CUT note first and
   hash-proven restores;
4. the verifier re-runs everything on committed bytes, re-applying mutants from the card's words;
5. QA may scan and report, never accept;
6. the designer's final review **reads** the evidence, including changed-function RAN/SKIPPED coverage,
   and accepts or sends the card back in words. The advisor may advise; the judge hears only contested
   evidence on the defined escalation triggers.

Two exceptions are explicit, never improvised:

- **TEST-ONLY STRENGTHENING** starts from green, has no red commit or fix, touches test files only, and
  proves that each new assertion bites through its own mutant. The verifier never re-runs the original
  card's red.
- **Small-fix** batches only the allowed cosmetic classes. Linters, one quick independent check per item,
  the coordinator's batch-diff review and the pre-push gate replace the red/mutant/full-battery cycle.
  Behavior, test assertions, installers, hooks, agent instructions, security and concurrency are forbidden;
  anything bigger becomes a normal card.

Nobody in those lanes grades its own homework. The issue tracker is the ledger; normal-card receipts live
under `.cards/evidence/<card>/`.

## How to run it

**The fast path: let your pi agent do it.** You do two things; the agent does the rest.

1. Install **pi** (`pi` + `pi-subagents`) and the GitHub CLI (`gh`), and log in to GitHub once:
   `python3 file_cards.py --login` (or `gh auth login --scopes repo,workflow`, or export `GH_TOKEN` with
   those scopes). This needs a browser or device approval, so an agent cannot do it for you.
2. Open a pi session in a clone of this repository and give it one prompt:

   > Read BOOTSTRAP.md and bootstrap into `<owner>/<repo>`.

   The agent runs `python3 file_cards.py --bootstrap --repo <owner>/<repo>`, creating the private
   repository if needed, seeding `LEDGER.md`, `PROTOCOL.md` and `LICENSE`, and filing all 19 cards.
   Re-running is safe. It then coordinates Act I under [PROTOCOL.md](PROTOCOL.md) in local mode.

**Bootstrap automerge, normal cards only.** In a repository the bootstrap creates, accepted normal cards
can land without you: `merge_card.py` fast-forwards the integration branch only when red-first receipts
are committed and the issue's verdict lines end `RED-CONFIRMED`, `VERIFIED`, `ACCEPTED` in order. The
script refuses anything else. TEST-ONLY and small-fix lanes do not have those red-first receipts and
cannot use this gate. Automerge is recorded in `.cards/AUTOMERGE` and ended with
`merge_card.py --disable-automerge`, after which the push is yours again. Pass `--no-automerge` to merge
every card yourself.

**The manual path** (what the agent does):

1. `python3 file_cards.py --check-auth` verifies `gh` and login (read-only).
2. `python3 file_cards.py --bootstrap --repo <owner>/<repo>` creates, seeds and files. `--dry-run`
   validates every card, including all six self-check answers, with no network.
3. Run Act I (stages 0–2) under [PROTOCOL.md](PROTOCOL.md), each phase in its own role-separated local
   **pi** session. Stage 0 builds local step contracts, handoffs and recovery; stage 1 builds enforcement;
   stage 2 builds the seven-role registry, local-only kickoff and router.
4. Start Act II with:

   ```text
   local:start ledger LEDGER.md :: Run the bootstrap ladder. Ask only blocking questions.
   ```

   Every AI step remains local. Once stages 4–5 land their tools, `gh-build.py`, `gh-full-lanes.py`,
   `gh-snapshot.py` and `gh-wait.py` may use GitHub Actions for model-free builds and long test lanes.
   `remote:start` and cloud-step claim/start/check/park/resume/release refuse with the retirement wording.
5. Route through one seven-role registry: `designer`, `implementer`, `verifier`, `qa`, `advisor`, `judge`,
   `mechanical`. Model bindings are configuration. The designer/coordinator reasons and reviews;
   implementer and verifier are different families; verifier and QA are pinned to max; QA uses its own
   explicit ref; advisor gives second opinions but no verdict; judge enters only on INDETERMINATE,
   ESCALATED, contradiction, or high-stakes-partial triggers; mechanical chores never include a
   hand-written edit. A second implementer may be selected explicitly by ref.

Before the machinery lands, every card runs under the seed protocol: design, card check, TDD, red
confirmed, fix and mutants, verification, bug scan, final review and merge. Independence is enforced by
session separation and evidence by committed receipts. After stage 2, the runtime dispatches Act II from
the ledger. The protocol remains the audit specification.

## The why-layer

The cards cite the article series that argues each mechanism (rationale, constraints, failure modes,
prices). Canonical on Substack, mirrors elsewhere:

1. The Trusted Golden Cage
2. The Enforcement Pipeline
3. Shadow Types
4. A Million Tests Is Still a Survey
5. Dura Lex, Sed Lex
6. The Anti-Rot Machine
7. Untrusted Labor in a Trusted Envelope
8. Never Ask a Model If It's Right
9. The Card Is the Contract (this repository's companion piece)

Precedence: **the card outranks everything while in flight; the repo's own docs outrank the articles;
the articles supply the why.**

## Status

The full current-shape ladder is drafted: 19 cards in `cards/`, from local execution machinery through
docs gates and doctor. The October 21 pointer, READ-receipt and remote-cloud cards are superseded by
local handoff, recovery and local-compute cards. The supersession is recorded in the
[2026-10-25 local-first reassessment](docs/findings/local-first-reassessment-2026-10-25.md).
What remains is execution, not specification: create or
choose a repository, file the cards, and run the ladder until the machinery starts dispatching itself.
The close-out records become this repository's history.

## License

The card texts in this repository are Apache-2.0. The code your agents write from them belongs to whoever
writes it.
