# Findings from the first real end-to-end run

Case: `data/140p6426q0127_piro_handrail/`, model: Gemini
(`google_genai` provider), 38 requirements after dedup, 38 verdicts.
Outputs: `actual_report.md`, `actual_requirements.json`,
`actual_verdicts.json` in that same case folder. Run against Gemini
rather than local vLLM because the local GPU's driver setup /
WSL2 was never completed for this project -- `google_genai` was
validated as a working alternative provider instead (see "Swappable
backends" in `README.md`); the `openai_compatible`/vLLM path remains
implemented but not yet exercised end-to-end.

## Open, unresolved

1. **The planted revenue contradiction ($12.4M vs $21.8M) was not
   caught — 0/38 verdicts came back `contradictory`.** Cause is
   NOT confirmed yet, but is now answerable: `graph.py`'s
   `generate_verdict_node` now also emits a `RetrievedEvidenceRecord`
   (`requirement_id` + the full pre-selection `evidence_chunks` list)
   into a new `retrieved_evidence` state key, returned from
   `run_pipeline` as `PipelineResult.retrieved_evidence` and written
   by `scripts/run_pipeline.py` as `actual_retrieved_evidence.json`.
   Once the pipeline is re-run, checking whether both revenue chunks
   appear in `small_business_size_standard`'s retrieved set will
   finally distinguish "retrieval never surfaced both together" from
   "it saw both and didn't notice" — not done yet, needs a fresh run.
7. **`actual_requirements.json`/`actual_verdicts.json` from the first
   run no longer validate against the current schema.** Confirmed by
   trying to run `scripts/evaluate.py` against them after adding
   `RequirementDraft.is_text_verifiable` (required, no default —
   deliberately not backfilled with a guessed value): pydantic raises
   a missing-field error. Expected and correct, not a bug — it's
   direct proof a fresh pipeline run is now required before
   `scripts/evaluate.py` can produce anything meaningful again.
8. **`is_text_verifiable` accuracy has no evaluation metric yet.**
   `expected_requirements.json` doesn't carry a ground-truth value for
   it either. Same gap `is_mandatory` had before its accuracy metric
   was added to `evaluation/metrics.py` — worth adding once there's a
   fresh run to check it against.

## Confirmed, needs fixing

2. **`is_mandatory` misclassified on real text.** The site-visit
   clause ("In no event shall failure to inspect... constitute
   grounds for a claim") is unambiguously non-mandatory per our own
   prompt wording, but extraction returned `is_mandatory: true` for
   it. Worked correctly on a 3-line synthetic smoke test earlier, not
   on this longer real clause. **Sidestepped, not fixed as a general
   capability**: this specific clause doesn't impose any obligation on
   the application's content at all (the site visit happens before/
   outside the application), so it was moved out of
   `expected_requirements.json` into `excluded_clauses` entirely (see
   below) — a correct extraction should now drop it via the new
   applicant-facing filter in the prompt, never reaching the
   `is_mandatory` decision for it. Whether extraction still
   mis-judges `is_mandatory` on *other* genuinely-mandatory-adjacent
   real clauses is unverified until the next real run.
3. **`is_mandatory` has zero downstream effect even when correct.**
   Fixed: `steps/report.py` now splits the report into "Mandatory
   Requirements" and "Preferred (Non-mandatory) Requirements"
   sections.
4. **`citation_verified: false` is invisible in `report.md`.** Fixed:
   unverified evidence quotes are now marked inline
   ("*(quote not located verbatim in source text)*") and collected
   into a "Needs Manual Review: Unverified Citations" section at the
   end of the report.
5. **Extraction over-captures non-bidder-facing text.** Several
   extracted "requirements" are instructions to the government
   evaluator (e.g. "Quotations shall be evaluated in an impartial
   manner...") or post-award clauses (IPP invoicing, COR/CO
   authority) — not things a bidder's quote could ever satisfy or
   fail. **Addressed, not yet validated**: `REQUIREMENT_EXTRACTION_PROMPT`
   now explicitly instructs the model to extract only requirements
   addressed to the bidder and to ignore text addressed to the
   government/contracting officer or post-award-only obligations,
   zero-shot (no worked examples, to avoid overfitting the prompt to
   this one tender). Needs a fresh run to confirm it actually works.
6. **`report.md` section order is non-deterministic.** Fixed: within
   each mandatory/non-mandatory section, verdicts are now sorted by
   severity (`non_compliant` → `contradictory` →
   `insufficient_information` → `compliant`), which is both more
   useful (problems surface first) and fully deterministic.

## Implemented this round (beyond the numbered findings)

- **Citation match precision.** `TextSpan.match_precision` (new field:
  `"precise"` for exact/whitespace-normalized matches, `"fuzzy"` for
  the rapidfuzz tier, `None` when nothing was found) — the three-tier
  cascade in `steps/text_matching.py` itself is unchanged (kept for
  speed and determinism: exact substring search is far cheaper than
  fuzzy alignment, and fuzzy alignment doesn't guarantee picking the
  same span a human would when several similar substrings exist), but
  which tier matched is no longer thrown away.
- **`is_text_verifiable` flag.** New field on `RequirementDraft`/
  `Requirement`, decided by the model in the same extraction call as
  `is_mandatory` (and merged across duplicates the same way, except
  the safe direction is inverted: false wins if any candidate in a
  dedup cluster says not verifiable). For `is_text_verifiable=False`
  requirements, `generate_verdict_node` still retrieves relevant
  application chunks but skips producing a `compliant`/`non_compliant`
  verdict entirely — they land in a new "Not Verifiable From
  Application Text Alone" report section instead, to stop the
  pipeline from manufacturing false confidence on facts like SAM
  registration status or an attachment's genuine existence that no
  text-only tool can confirm.
- **`site_visit_expectation` reclassified.** Re-read the actual clause
  text (FAR 52.237-1): it bars the *contractor*, after contract award,
  from claiming compensation/schedule relief for not having inspected
  the site — it is not a rule about bid-evaluation eligibility, and
  not about the government's obligation to grant site access (part
  (b) of the same clause schedules an organized visit). Since it
  imposes no obligation on the application's content at all, it no
  longer belongs in `expected_requirements.json`; moved to
  `excluded_clauses` instead, where its role as a "text that sounds
  like a bidder obligation but isn't one" trap is actually correct.
- Added `tests/test_report.py` (4 tests: mandatory/preferred split,
  severity ordering, not-verifiable section, unverified-citation
  flagging) and a fuzzy-match test in `tests/test_text_matching.py`.
  `pyright .`, `pycodestyle --max-line-length=88 .`, `pytest tests/`
  all clean (39 tests total).

## Housekeeping done

- Moved run outputs out of the project root into the case's own
  `data/` folder, renamed to `actual_*` to pair with `expected_*`.
- Grouped root-level modules into packages once the file count grew
  too large to scan at a glance: `backends/` (`llm_client.py`,
  `vectorstore.py`, `embeddings.py` — the three swappable-provider
  adapters, plus a shared `retry.py` added later), `steps/`
  (`chunking.py`, `text_matching.py`, `requirements_extraction.py`,
  `deduplication.py`, `conditions.py`, `evidence_retrieval.py`,
  `value_extraction.py`, `verdicts.py`, `report.py` — the LangGraph
  node logic), `evaluation/` (`matching.py`, `metrics.py`,
  `orchestrator.py`, `rendering.py`, with `__init__.py` re-exporting
  the public surface). `graph.py`, `pipeline.py`, `schemas.py`,
  `config.py`, `logging_config.py`, `prompts.py` stayed at root as
  cross-cutting/orchestration code. All cross-file imports updated to
  qualified paths (e.g. `from steps.chunking import ...`); `pyright .`,
  `pycodestyle`, and `pytest tests/` all clean afterward.
- Renamed `steps/dedup.py` -> `deduplication.py`,
  `steps/extraction.py` -> `requirements_extraction.py`,
  `steps/retrieval.py` -> `evidence_retrieval.py` (and matching test
  file) for clearer, less abbreviated module names.
- Full pass for code-style compliance (function length, comprehension
  length, scattered constants) across every module (~20 files):
  every function that exceeded 10 statements was decomposed into
  smaller named helpers (worst offenders: `evaluation/orchestrator.py`
  `evaluate()` at 21 statements, `evaluation/metrics.py`
  `compute_verdict_accuracy()` at 20, `steps/text_matching.py`
  `locate_quote_in_chunk()` at 22); every list/dict/set comprehension
  spanning 3+ lines was rewritten as an explicit loop. Along the way,
  consolidated several duplicated patterns into shared helpers: a
  `_safe_ratio()` division-with-zero-guard used ~9 times in
  `evaluation/metrics.py`, a `_span_from_source()`/`_prefix_ids()`
  pair in `evaluation/orchestrator.py`/`matching.py`, a
  `_span_from_local_offsets()` helper collapsing three near-identical
  blocks in `steps/text_matching.py`'s citation cascade, a
  `COMPARISON_FUNCTIONS` lookup table replacing an if/elif chain in
  `steps/conditions.py::apply_operator`, and a shared
  `backends/retry.py::build_retry_decorator()` replacing duplicated
  `tenacity.retry(...)` construction in `llm_client.py` and
  `vectorstore.py`. Moved four hand-tuned evaluation thresholds
  (`REQUIREMENT_MATCH_MINIMUM_OVERLAP_RATIO` and siblings) out of
  `evaluation/orchestrator.py` into `config.py` as
  `EVALUATION_*` constants, alongside the main pipeline's tuning
  constants. Verified behavior-preserving throughout: after every
  file, re-ran `pyright .` / `pycodestyle` / `pytest tests/` (all
  clean, 34 tests) and re-ran `scripts/evaluate.py` against the real
  case data to confirm byte-identical output to before the refactor.
  A small `ast`-based audit script (statement-per-function counter +
  multiline-comprehension detector) was used to find every violation
  objectively rather than by manual scanning; it isn't part of the
  repo, just a one-off tool for this pass.
- Fixed two stale-documentation gaps found while re-checking
  `README.md` against the current code: the Setup section only
  described the vLLM/`openai_compatible` path and never mentioned
  `google_genai`, even though that's the provider actually used for
  the real run; and `.env.example`'s sample Gemini model name
  (`gemini-2.0-flash`) was the same one that returned 404 during the
  real run (see below) and had to be updated to
  `gemini-3.5-flash-lite`.

## In progress

- Designing an evaluation script (`scripts/evaluate.py`, not yet
  written) comparing `actual_*.json` against `expected_*.json`.
  Design agreed:
  - Matching is a bipartite overlap graph over `(document_path,
    start_char, end_char)` between expected and actual requirements,
    built with a sweep-line interval-intersection (sort both lists by
    `start_char`, two-pointer scan) rather than a full O(N·M) matrix —
    connected components classify each match as clean 1:1,
    over-split (1 expected : N actual), or over-merge (N expected : 1
    actual), reported as separate diagnostic counts, not folded into
    recall.
  - Recall counts an expected topic as found if it has ≥1 connected
    actual, regardless of split/merge. Two coverage-ratio flags
    (`expected_covered`, `actual_explained`) catch incomplete capture
    and over-broad citation respectively.
  - `expected_requirements.json` was revised from 13 "representative"
    topics to an exhaustive 15-topic list over tender.txt's
    bidder-facing, pre-award, text-verifiable content, plus a new
    `excluded_clauses` list (7 entries) of concrete spans a bad
    extraction could mistake for a requirement (government-facing
    evaluation instructions, post-award clauses). An actual
    requirement matching neither list is a genuine fixture gap for
    manual triage, not an automatic precision penalty.
    `excluded_clauses` must only ever be populated by reading
    tender.txt directly — never auto-populated from a run's unmatched
    output, or the precision metric becomes tautological.
  - Precision/hallucination is now two separate numbers: citation
    hallucination (`citation_verified` rate, already free) and
    classification precision (unmatched actual, split by whether it
    overlaps `excluded_clauses`).
  - `prior_experience_minimum_3_with_poc` was split into
    `prior_experience_count` and `prior_experience_poc_required` —
    concrete example of a composite requirement where offset-only
    matching can't see a downstream defect (case where extraction
    citation covers the full composite sentence but only some
    sub-conditions get checked). Preferred fix for this class of bug
    is decomposing fixtures into atomic sub-topics, not an LLM-judge.
  - `expected_verdict` (single string) replaced with
    `acceptable_verdicts` (list) in `expected_verdicts.json`. Verdict
    confusion matrix computed only on clean 1:1 matches;
    false-compliant-rate / false-issue-rate computed over all matched
    groups including split/merge (a group counts as false-compliant
    if any expected verdict in it is non-compliant/insufficient/
    contradictory but every actual verdict in it is compliant, and
    mirrored for false-issue) — merges/splits don't excuse a missed
    real problem.
  - Evidence recall: `expected_verdicts.json`'s existing per-topic
    `evidence` field already **is** the expected-requirement →
    expected-evidence mapping; no new fixture needed. Requires a new
    artifact (not yet built): the full pre-selection retrieved-chunk
    set per requirement, persisted from the graph. Compute forward-
    only recall (expected evidence found in retrieved set) — this is
    the one thing that can finally answer the still-open contradiction
    question above.
  - LLM-judge is optional and scoped to flagged ambiguous cases only
    (high-overlap-but-different-topic, incomplete-capture flags) —
    not run as part of the default metric computation.
  - Both revised fixtures validated: all `source`/`evidence` offsets
    round-trip exactly against `tender.txt`/`application.txt`, and the
    15 `topic_id`s match 1:1 between `expected_requirements.json` and
    `expected_verdicts.json`.
  - Pre-selection retrieval artifact implemented (see finding 1
    above): `RetrievedEvidenceRecord` in `schemas.py`, wired through
    `graph.py`/`pipeline.py`/`scripts/run_pipeline.py`. `pyright .`
    and `pytest tests/` both clean after the change.
  - `scripts/evaluate.py` implemented, split into an `evaluation/`
    package: `matching.py` (bisect-based sweep + union-find connected
    components, 34 test cases combined across all three new modules),
    `metrics.py` (recall, precision, coverage flags, `is_mandatory`
    accuracy, verdict confusion matrix + false-compliant/false-issue
    rates, evidence citation-verified rate, evidence recall),
    `orchestrator.py` (fixture loading + orchestration),
    `rendering.py` (Markdown rendering); `__init__.py` re-exports the
    public surface. `pyright .`, `pycodestyle`, and `pytest tests/`
    all clean. Later reorganized further (see housekeeping below) —
    `llm_client.py`/`vectorstore.py`/`embeddings.py` moved into
    `backends/`, and `chunking.py`/`text_matching.py`/`extraction.py`/
    `dedup.py`/`conditions.py`/`retrieval.py`/`value_extraction.py`/
    `verdicts.py`/`report.py` moved into `steps/`, to cut root-level
    clutter (root .py file count 22 -> 6).
  - Smoke-tested `scripts/evaluate.py` against the existing (stale,
    pre-fix) `actual_requirements.json`/`actual_verdicts.json` from
    the first real run, with an empty stand-in for
    `actual_retrieved_evidence.json` (that run predates the artifact,
    so evidence recall reports 0% — expected, not a bug). Two numbers
    independently reproduced already-known findings exactly: evidence
    citation-verified rate came back 94.4% = 34/36, matching NOTES.md
    finding 4's "2 of 36 unverified" precisely; `is_mandatory`
    accuracy flagged `site_visit_expectation` as mismatched, matching
    finding 2. New signal from the same smoke test, not yet
    investigated: classification precision came back only 34.2%, with
    25 of the old run's 38 actual requirements unexplained by either
    `expected_requirements.json` or `excluded_clauses`. Cause not
    confirmed — could be genuine extraction over-capture (finding 5,
    not fixed in that old run) or the revised "exhaustive" fixture
    still missing legitimate topics; needs a fresh run plus manual
    triage of the unexplained set before drawing conclusions.
  - Not yet done: fixing findings 2-6 above, re-running the pipeline
    to get a fresh, fully current `actual_*` set (including
    `actual_retrieved_evidence.json`), and running `scripts/evaluate.py`
    against it for a real (non-smoke-test) evaluation.

## Quote-echo bug fix, fixture corrections, terminology rename

Found via manual line-by-line audit of a real run's
`actual_requirements.json`/`actual_verdicts.json` against `tender.txt`,
plus a follow-up audit specifically of the fixture's `source.quote`
values against the surrounding tender text.

1. **Citation echo bug, two layers (fixed).** Verified citations were
   displaying the model's own (possibly-corrupted) text instead of the
   text actually matched in the source, for both fuzzy-matched
   requirement citations (`steps/text_matching.py`) and requirement
   draft text (`steps/requirements_extraction.py`). Caught a real
   Gemini hallucination this way: a Bengali-script fragment
   ("ভাবের") inserted into an otherwise-verbatim quote, which the
   fuzzy matcher had incorrectly marked `citation_verified: true`.
   Fixed by always slicing the displayed text from `chunk.text`, never
   echoing the model's own string, whenever a citation is verified at
   any tier; the model's raw text is shown only when nothing was
   found, with a bracketed note. Confirmed fixed against a fresh run.
2. **`small_business_size_standard` audited, not re-anchored.** The
   pipeline consistently extracts "Your company must also be
   registered... and be considered a small business for the size
   standard associated with the NAICS code found in block 10..." (a
   compound SAM+small-business restatement, occurring 3 times in
   `tender.txt`) but never the fixture's anchor sentence ("This
   requirement is a 100% total small business set-aside... NAICS code
   is 238990... size standard is $19 M") — confirmed by running
   `split_requirements_document` directly: the anchor sentence sits in
   the same whole chunk as the requirements the model did extract, so
   this is not a chunking artifact. Initially mis-characterized as "a
   different anchor of an equivalent statement" — corrected on review:
   the restatements the model does extract never state the actual
   NAICS code or dollar figure, only "the size standard found in block
   10", so they do NOT carry the concrete, checkable criterion this
   topic is about. The fixture's anchor was deliberately left
   unchanged rather than re-pointed at what the model typically
   extracts, since doing so would hide a genuine extraction gap
   (the model never captures the actual $19M/NAICS-238990 figures
   anywhere) instead of measuring it.
3. **`tax_liability_representation` / `felony_conviction_representation`
   re-anchored (fixed).** Fixture `source.quote` previously pointed at
   the "(b) The Offeror represents... It is [ ] is not [ ]..." checkbox
   lines; re-anchored to the substantive "(a) ... Has any unpaid
   Federal tax liability..." / "... Was convicted of a felony..."
   clause text just above, since that is what actually defines the
   eligibility condition (the checkbox is only the attestation
   mechanism). Separately confirmed this is a genuine, real extraction
   miss and not a fixture-anchor artifact: both the (a) and (b) spans
   sit inside single, whole chunks, and no actual requirement from a
   real run overlaps either span. Root cause of the miss itself is
   NOT confirmed (no per-chunk raw model output is logged) — a
   plausible but unverified guess is that the extraction prompt's
   applicant-facing filter over-triggers on the clause's leading
   "the Government will not enter into a contract with any
   corporation that--" framing.
4. **`sudan_iran_restricted_business_representation`,
   `buy_american_certificate`, `child_labor_certification` moved to
   `excluded_clauses` (fixed).** All three only ever appeared in
   `tender.txt` as a bare clause title inside the "VI. LIST OF
   PROVISIONS (BY REFERENCE)" table of contents, with zero substantive
   text (unlike tax/felony above) describing what each certification
   actually commits the bidder to — nothing text-verifiable to extract.
   `sudan_iran_restricted_business_representation` additionally
   conflated two legally and physically separate clauses (52.225-20
   Sudan, 52.225-25 Iran, ~100 characters apart but about different
   countries) under one topic/anchor; split into two separate
   `excluded_clauses` entries.
5. **Evidence recall counted genuinely-missed requirements as evidence
   misses too (fixed).** `compute_evidence_recall`'s denominator
   previously included every topic with expected evidence in
   `expected_verdicts.json`, even ones the pipeline never extracted as
   a requirement at all — for those, there is no retrieval to check,
   so counting them here double-penalized the same failure already
   reflected in requirement recall. Added
   `topics_with_matched_requirement` in `evaluation/span_adapters.py`
   to filter to topics with at least one matched actual requirement
   before computing recall; regression test in
   `tests/test_span_adapters.py`. Measured effect on one real run:
   evidence recall went from 53.8% (7/13) to 100% (9/9) once the 6
   never-extracted topics were correctly excluded rather than counted
   as misses.
6. **Evaluation-report rendering showed fixture descriptions, not real
   quotes (fixed).** `_expected_line` (now `_true_line`) previously
   showed only the fixture's free-text `description`, not any text
   actually present in `tender.txt` — a reader had no way to see the
   real source line without opening the fixture file directly. Added
   `true_quotes_by_topic` to `EvaluationReport` and changed the line
   format to `true `{topic_id}` — "{quote}"`, dropping the description
   entirely per explicit request (topic_id + real quote is enough).
7. **Terminology rename across the whole `evaluation/` package, its
   tests, `scripts/evaluate.py`, and `README.md`.** "actual" (implying
   "correct") renamed to "predicted"; "expected" renamed to "true".
   Covers fixture types (`ExpectedRequirement` -> `TrueRequirement`,
   etc.), fixture files (`expected_requirements.json` ->
   `true_requirements.json`, `expected_verdicts.json` ->
   `true_verdicts.json`), pipeline-output files
   (`actual_requirements.json` -> `predicted_requirements.json`, same
   for `_verdicts`/`_retrieved_evidence`, and the report itself
   `actual_report.md`/`actual.md` -> `predicted.md`), `MatchGroup`
   fields (`expected_topic_ids` -> `true_topic_ids`,
   `actual_node_ids` -> `predicted_node_ids`), match shapes
   (`unmatched_expected` -> `unmatched_true`, `unmatched_actual` ->
   `unmatched_predicted`), `scripts/evaluate.py --output-prefix`
   default (`actual` -> `predicted`). Deliberately did NOT touch
   `evaluation/matching.py`'s generic bipartite-overlap helper
   (`find_overlapping_pairs`, `_overlap_ratio`) — it is reused for
   `excluded_clauses` overlap checks where "true topic" framing does
   not apply, so its internal params were renamed to neutral
   `reference_spans`/`other_spans` instead. Also deliberately did NOT
   touch `steps/conditions.py`'s `actual_value` (numeric
   condition-checking, unrelated concept) or ordinary `expected`/
   `actual` variable names in unrelated test assertions elsewhere in
   the repo.
  - After all of the above, re-ran the full pipeline for real
    (Gemini, `gemini-3.5-flash-lite`) against
    `data/140p6426q0127_piro_handrail/` and `scripts/evaluate.py`
    against the fresh output: 13/13 `true_requirements.json` topics
    now have matching `true_verdicts.json` entries; requirement recall
    76.9% (10/13, the 3 misses being exactly the confirmed-genuine
    tax/felony/small-business gaps above); is_mandatory accuracy
    100% (8 clean pairs); evidence recall 100% (9/9, no longer
    counting never-extracted topics). Classification precision (50%,
    14 unexplained) and evidence citation-verified rate (65.5%) are
    this run's own new numbers (Gemini output varies run to run) and
    have not yet been triaged.
  - Not yet done: pending from the still-open design discussion —
    loosening `REQUIREMENT_DEDUPLICATION_SIMILARITY_THRESHOLD` from a
    hard precision gate to a coarse pre-filter (hypothesized root
    cause of "found the right idea in a different place" cases, e.g.
    `contractor_core_data`'s over-split into 4 pieces).

## Report rendering cleanup, is_text_verifiable metric, isolated verdict evaluation

1. **Coverage flags rendering, verdict-group duplication, wording
   (fixed).** Renamed the "Coverage flags" section into two named
   subsections, `Requirements captured with extra text` (flagged by
   `predicted_explained_ratio`) and `Requirements captured
   incompletely` (flagged by `true_covered_ratio`), each a single
   terse line per case instead of a repeated two-paragraph
   explanation. `_render_verdict_group_list` now collapses a clean 1:1
   true/predicted pair into one combined line instead of listing the
   same underlying item twice (once as "true", once as "predicted") —
   only genuinely multi-node split/merge groups still render as a
   list. Removed "the fixture says" personification wording throughout
   `evaluation/rendering.py` in favor of direct language ("the true
   verdict requires..."); shortened most section explanations. Dropped
   the "Not verifiable" subsection from the verdict-accuracy section
   entirely per explicit request (the same information is already
   visible inline via each predicted line's "not verifiable by text"
   suffix).
2. **`is_text_verifiable` added to `TrueRequirement` + accuracy metric
   (implemented).** All 13 `true_requirements.json` topics are
   `is_text_verifiable: true` by construction — this list is defined
   (see its own top-level notes) as exhaustive over TEXT-VERIFIABLE
   bidder-facing requirements, so there was never a real candidate for
   `false` among them; the metric still has value because it catches a
   predicted `false` on a topic that should get a real verdict (which
   would silently skip verdict generation via
   `graph.py`'s `generate_verdict_node`). `compute_is_text_verifiable_accuracy`
   in `evaluation/requirement_metrics.py` mirrors
   `compute_is_mandatory_accuracy`'s clean-1:1-only scoring, sharing a
   new `_mismatched_boolean_flag_topics` helper. Real-run result:
   100% (8/8 clean pairs) — no mismatches yet observed.
3. **Isolated verdict-only evaluation (implemented).** New
   `evaluation/verdict_only.py` (pure, tested:
   `build_synthetic_requirements`, `score_verdicts`,
   `render_verdict_only_report`) plus `scripts/evaluate_verdicts.py`
   (the impure retrieval/generation loop, mirroring
   `graph.py`'s `generate_verdict_node` but run directly against
   synthetic `Requirement` objects built straight from
   `true_requirements.json` -- text = the fixture's own `description`,
   citation = its own `source`, `is_mandatory`/`is_text_verifiable`
   copied as-is). This completely bypasses `evaluation/matching.py`'s
   match-group machinery: every topic is scored, not just the ones a
   real extraction happened to cleanly match. Real-run result: **76.9%
   (10/13)**, with 3 confirmed verdict-generation-level mismatches
   (not extraction artifacts, since the input citation here is
   guaranteed correct): `price_schedule_complete` (predicted
   `contradictory`, should be `compliant`), `prior_experience_count`
   (predicted `non_compliant`, acceptable are
   `compliant`/`insufficient_information`), and
   `prior_experience_poc_required` (predicted `compliant` -- the
   dangerous false-compliant direction -- acceptable are
   `non_compliant`/`insufficient_information`). The third one matches
   the false-compliant case already flagged by the full-pipeline
   `evaluation_report.md` on the same run, confirming it is a genuine
   verdict-model weakness on this case, not something extraction could
   have masked or caused.
  - Not yet done: loosening
    `REQUIREMENT_DEDUPLICATION_SIMILARITY_THRESHOLD` (still the
    leading hypothesis for "found the right idea in a different
    place" cases, e.g. `contractor_core_data`'s over-split).

## Fixture redesign: is_text_verifiable rescoped, multi-span sources, excluded_clauses removed, coverage-flag bug fixed

Prompted by the user pushing back on a wrong framing: `true_requirements.json`
had been scoped to TEXT-VERIFIABLE requirements only, but the report shown
to a real bidder needs to tell them about every requirement, verifiable
from application text or not -- so the ground truth must cover all of
them, with `is_text_verifiable` as a descriptive flag, not a scope filter.

1. **Coverage-flag denominator bug (found and fixed).** A real report
   showed `uei_required`'s predicted and true text as visually identical
   yet only "50.0% of the predicted citation is true content." Root
   cause, confirmed against `predicted_requirements.json`: the matched
   predicted `Requirement` had **two** citations from dedup (one at the
   true anchor, one an unrelated restatement ~13,000 characters away),
   and the old `predicted_explained_ratio` denominator summed the
   length of *all* of a node's citations regardless of which one
   actually overlapped the true topic -- so an unrelated restatement
   elsewhere silently counted as "padding" on a perfectly clean match.
   Fixed by reworking `compute_coverage_flags` (`evaluation/
   requirement_metrics.py`) to operate on raw `SpanRef` lists rather
   than pre-aggregated per-node lengths, filtering to only the specific
   citation spans that overlap the group's true span(s)
   (`_relevant_length`). Regression test:
   `test_coverage_flags_ignore_unrelated_citations_of_the_same_node`.
   `evaluation/matching.py`'s `_overlap_length` was made public
   (`overlap_length`) to support this from `requirement_metrics.py`.
2. **Multi-span `TrueSource` (implemented, fixture-only for now).**
   `TrueSource.source` changed from a single `{start_char, end_char}`
   to `{spans: [{start_char, end_char}, ...]}`, with `quote` set to the
   spans' text joined by `" ... "` when there's more than one. Used to
   fix `tax_liability_representation`/`felony_conviction_representation`
   (renamed `no_unpaid_federal_tax_liability`/
   `no_recent_felony_conviction`): both used to anchor to the isolated
   "(b) The Offeror represents..." checkbox line, which reads as
   meaningless out of context; re-anchored to two spans each -- the
   shared "(a) ... the Government will not enter into a contract with
   any corporation that--" lead-in, plus the specific enumerated
   condition -- since the lead-in is shared by both conditions in one
   sentence and can't be included contiguously with only one of them.
   Considered but deliberately did NOT extend this to the live
   pipeline's `TextSpan`/extraction prompt this round: it would need
   per-fragment verification (three-tier match, worst-precision-wins
   aggregation) in `steps/text_matching.py`, a prompt change, and
   updates everywhere `citation.quote` is read as one string -- a real
   behavior change to the live pipeline, not just the fixture, worth
   doing only if this shared-lead-in pattern recurs across more real
   tenders. Confirmed (again) this is a genuine extraction miss, not a
   chunking artifact: both spans sit inside one whole chunk under
   `split_requirements_document`.
3. **`excluded_clauses` removed entirely.** Classification precision is
   now simply matched-predicted / total-predicted -- no carve-out.
   `ExcludedClause`, `excluded_clause_spans`,
   `excluded_overlap_requirement_ids` all deleted. Text that isn't a
   bidder requirement at all (government process instructions,
   post-award clauses, bare clause titles with no substantive content,
   e.g. the Sudan/Iran/Buy-American/child-labor clause titles) is
   simply absent from the fixture now; a predicted requirement quoting
   it honestly shows up as "unexplained" instead of being silently
   excused. Precision-section wording also fixed: dropped the
   incorrect "(recall, above)" parenthetical, dropped the personifying
   "the fixture says" phrasing throughout `evaluation/rendering.py` in
   favor of direct language ("the true verdict requires..."), and the
   unexplained list now shows bare requirement text (no verdict/
   citation-status suffix, which was irrelevant noise for a precision
   audit).
4. **`is_text_verifiable` re-audited per topic against the corrected
   definition.** `submission_deadline_and_channel` changed from `true`
   to `false`: it is about the process of submission (channel/timing),
   which application.txt has no natural way to represent one way or
   the other -- unlike the SAM/tax/felony self-representations, there
   is no sentence a bidder would even attempt to write attesting to
   this. Its `true_verdicts.json` entry's `acceptable_verdicts` changed
   from `["insufficient_information"]` to `null` (no longer scored for
   verdict accuracy -- the interesting failure mode, a pipeline
   wrongly guessing a verdict from silence, is now caught by the
   `is_text_verifiable` accuracy metric instead, which is more precise
   than a verdict-guessing test). All other topics confirmed `true`.
5. **`is_mandatory`/`is_text_verifiable` accuracy extended to one-to-many
   matches (implemented).** Previously scored clean 1:1 matches only.
   Now also scores `over_split`/`over_merge` groups with an all-or-
   nothing rule on the "many" side (`_group_flag_matches` in
   `evaluation/requirement_metrics.py`); `tangled` groups remain
   excluded (no single "one" to compare against). This immediately
   surfaced two real, previously-invisible findings on a real run: the
   model marked one of `contractor_core_data`'s four split-out fields
   ("Cage Code / ... UEI:") `is_text_verifiable: false` while marking
   the other three `true` -- an internal inconsistency the old
   clean-only scoring silently excluded; and it marked the amendment-
   acknowledgment sentence `is_mandatory: true` and
   `is_text_verifiable: false`, both arguably wrong in ways directly
   explained by its citation missing the "in any case an amendment was
   posted" lead-in (confirmed via the same coverage-flag section that
   flagged this citation as only 64.2% complete).
6. **Two real fixture gaps found via a full manual audit of every
   "unexplained" predicted requirement against tender.txt (added).**
   `capabilities_statement_required` (new topic, split out of what was
   miscategorized as `capabilities_statement_with_shop_drawings`,
   renamed `shop_drawings_and_product_data_required`): the old topic's
   `source` only covered the shop-drawings half of a two-sentence
   checklist bullet even though its description claimed both halves;
   the broader "provide a capabilities statement" sentence was a real,
   separate, previously-uncovered topic. `price_schedule_must_not_be_edited`
   (new topic): a real, distinct, previously-missed requirement ("must
   ensure this document is not edited... provide an addendum if
   changes are needed") sitting right next to `price_schedule_complete`
   in tender.txt. `amendment_acknowledgment_if_posted` (new topic,
   `is_mandatory: false` since conditional on an amendment existing):
   also found this way. 16 topics total now (was 13), all offsets
   round-trip verified programmatically, `true_requirements.json` and
   `true_verdicts.json` topic_ids match 1:1.
7. **Verdict-accuracy group listings reordered and enriched.** The
   false-compliant/false-issue/unscored line format changed from
   `topic (acceptable) — predicted [id] "text" — verdict: X` to
   `topic — acceptable: [...], predicted: X — "text"` per explicit
   request (topic key, acceptable verdicts, predicted verdict,
   requirement text, in that order).
8. **`scripts/evaluate_verdicts.py`'s output merged into the main
   report.** It now also writes `verdict_only_verdicts.json` (raw
   `Verdict` list) next to its own report; `scripts/evaluate.py` picks
   this up automatically if present and appends a rendered
   "Verdict-only evaluation" section to the combined report via
   `evaluation/verdict_only.score_verdicts`/`render_verdict_only_report`,
   so the two evaluations don't need to be read as separate files.
   `VerdictOnlyOutcome` enriched with `requirement_text`,
   `evidence_quotes`, and `reasoning` (previously topic_id/verdict
   only) so every outcome -- not just mismatches -- is fully
   auditable without cross-referencing other files.
  - Real-run results after all of the above: requirement recall 81.2%
    (13/16); classification precision 60.7% (11 unexplained, all
    manually triaged -- either genuine restatement-elsewhere cases
    already known, or genuinely out-of-scope post-award/government
    content, none revealing a further fixture gap this pass);
    `is_mandatory` accuracy 92.3% (13 groups, 1 mismatch); `is_text_verifiable`
    accuracy 84.6% (13 groups, 2 mismatches, both explained above);
    verdict confusion matrix now has 6 distinct cells (up from 5,
    including a first-ever `true insufficient_information -> predicted
    insufficient_information` cell) simply because more topics reached
    "clean" match status this run -- confirming the earlier
    explanation that a sparse confusion matrix reflects small-sample
    clean-match coverage, not a rendering bug. Isolated verdict-only
    accuracy: 80.0% (12/15 text-verifiable topics), with the same 3
    mismatches as before plus full requirement/evidence/reasoning
    detail now visible directly in `evaluation_report.md`.
  - Not yet done: loosening
    `REQUIREMENT_DEDUPLICATION_SIMILARITY_THRESHOLD` (unchanged from
    before -- still the leading hypothesis for "found the right idea
    in a different place" cases).

## Matching robustness, report formatting, and a confirmed dedup gap

1. **Multi-span sources could cross-match.** Two true topics sharing
   the exact same lead-in span (like `no_unpaid_federal_tax_liability`
   and `no_recent_felony_conviction`) would both satisfy the overlap
   threshold against a predicted citation covering only the lead-in
   plus one of the two enumerated conditions, since matching worked
   per-span. Added `SourceSpan.used_for_matching` (default `true`);
   the shared lead-in span in both topics is now `false`, so only the
   distinctive per-topic span is used for overlap matching (the lead-in
   still displays in `quote`). Regression tests in
   `tests/test_span_adapters.py` reproduce the cross-match with the
   flag off and confirm it disappears with the flag on.
2. **Confirmed the 11 unexplained predicted items by reading
   tender.txt directly around each citation's exact offsets.** 2 are
   genuinely out of scope (a bare "use the checklist" pointer, a
   post-award IPP-invoicing clause). The other 9 are restatements of
   topics already covered elsewhere in `true_requirements.json` (SAM
   registration, price schedule, prior experience, capabilities
   statement, amendment acknowledgment, submission channel) -- the
   tender repeats the same checklist items in at least three places
   (a "CHECKLIST FOR QUOTE SUBMITTAL" list, a numbered "TO SUBMIT AN
   OFFER" list, and an "EVALUATION CRITERIA" section), and dedup only
   merges some of the cross-location restatements into the requirement
   matching each topic's anchor. No fixture change from this audit;
   the dedup gap is a real pipeline weakness worth revisiting.
   **Root cause confirmed, not guessed**: reloaded the actual
   `requirement_drafts` (pre-dedup) from `checkpoints.db` for the run
   that produced the current `predicted_requirements.json`
   (thread `9b1db709-...`, verified by comparing its final
   `requirements` texts against the saved JSON) and re-ran
   `steps.deduplication._cluster_by_similarity` on the real embeddings
   -- reproduced the exact same clusters as the actual run bit-for-bit,
   confirming the method. None of the 9 unmerged restatements share a
   connected component with the draft matching their topic's anchor;
   cosine similarity between each pair is 0.57-0.73, well under the
   0.85 threshold (`c6b312ea`/anchor 0.665, `d86dc0b0`/anchor 0.687,
   `be31df78`/anchor 0.671, `da5d42ec`/anchor 0.720, `2c76a141`/anchor
   0.693, `b74216ba`/anchor 0.729, `5ff87e30`/anchor 0.620). So this is
   an embedding/threshold gap, not an LLM grouping-resolution mistake
   -- the clustering step never even presents these pairs to the LLM
   for a merge decision. Notably `be31df78` and its own neighboring
   sentence `c23f401f` (same paragraph, and `c23f401f` DID cluster
   successfully with the true anchor's group) score only 0.57 against
   each other -- similarity here doesn't reliably track "same
   paragraph" either, so a purely embedding-distance fix would need a
   real threshold change, not just better chunk locality.
4. **Threshold lowered to 0.6, then 0.7 -- confirmed a structural**
   **limit, not just a tuning problem.** At 0.6: 28 requirements
   collapsed to 15, with real over-merges (`price_schedule_complete` +
   `price_schedule_must_not_be_edited` + `final_offer_total_no_alternates`
   all lumped into one) and a confirmed bug (see below). At 0.7: 20
   requirements, the price-schedule 3-way merge is fixed, but
   `prior_experience_count`/`prior_experience_poc_required` are still
   merged, and a new tangle appeared between `contractor_core_data`
   and `uei_required` (its "Cage Code / ... UEI" line merged with the
   plain UEI requirement) that did not exist at 0.85. Measured why
   directly: cosine similarity between `contractor_core_data`'s UEI
   line and `uei_required` is 0.748 -- HIGHER than the similarity
   between `prior_experience_count` and the restatement we want merged
   (`c6b312ea`, 0.673). No single global threshold can merge the
   second pair without also merging the first, since the "wrong" merge
   is textually closer than the "right" one. This is a hard limit of a
   single global cosine cutoff over generic sentence embeddings for
   this task, not something further threshold tuning can resolve.
5. **Bug found and fixed**: at the larger cluster sizes 0.6 produced,
   `_resolve_group` (`steps/deduplication.py`) derived a resolved
   group's `requirement_id` from `drafts[group_draft_indices[0]]` --
   when the LLM's grouping response had two groups whose
   `member_indices` both started at the same cluster position, both
   groups got the exact same `requirement_id` despite covering
   different content (confirmed: `847cc30b` appeared twice, once for
   a shop-drawings requirement and once for a capabilities-statement
   requirement). Fixed by generating a fresh `uuid.uuid4()` for every
   resolved group instead of reusing an input draft's id. Regression
   test in `tests/test_deduplication.py` reproduces the exact
   overlapping-`member_indices` scenario.
6. **Recommendation**: revert
   `REQUIREMENT_DEDUPLICATION_SIMILARITY_THRESHOLD` to 0.85. A missed
   merge is visible and honest (shows up as "unexplained" in precision,
   or as a separate clean match) and never hides a real requirement's
   own pass/fail outcome; a wrong merge silently lumps two independently
   checkable requirements' verdicts into one, which is worse for a
   compliance report. Left at 0.7 pending the user's decision.
3. **Report formatting overhaul**, all in `evaluation/rendering.py`
   and `evaluation/verdict_only.py`: every quoted text/reasoning
   snippet now has internal whitespace collapsed to single spaces
   before being embedded in a bullet (source text and model reasoning
   both contain literal newlines, which broke Markdown bullet
   indentation); the `is_mandatory`/`is_text_verifiable` mismatch list
   now prints the true and predicted value for every topic/requirement
   in the group instead of just the topic id; the verdict confusion
   matrix renders as a table over the four verdict labels with a note
   explaining any all-zero row; false-compliant/false-issue entries
   now include the requirement text, cited evidence, and the model's
   reasoning (bold field labels), matching the verdict-only section's
   level of detail.

## Second case (36C24126Q0731): fixture audit, LOS split, model-vs-expected in reports

1. **Audited all 20 unexplained predicted requirements against tender.txt.**
   2 are genuine gaps, now added: `eft_indicator_if_applicable` (EFT
   suffix, conditional) and `quote_signed_and_dated` ("(b) Submission
   of Quotes. Submit signed and dated quotes..."). The rest are either
   SD/VOSB/LOS clause-definition or evaluation-factor boilerplate
   (correctly out of scope), restatements of an existing topic anchored
   elsewhere (cosine similarity to the matched anchor measured directly:
   0.59-0.84, same below-threshold pattern as the first case), or one
   FAR clause explicitly marked "N/A (Not Applicable)" for this
   solicitation right in the tender text (`(c) Period for acceptance
   of Quotes`) -- confirmed by reading past the model's own citation
   boundary, not assumed.
2. **`los_compliance_assertion` split into two topics.** The original
   bundled a substantive fact application text can't verify ("Offeror
   must meet LOS requirements", now `los_requirements_met`,
   is_text_verifiable: false) with a checkable procedural instruction
   ("Compliance... must be asserted... in the email", kept as
   `los_compliance_assertion`, is_text_verifiable: true). The bundled
   topic's `acceptable_verdicts: ["insufficient_information"]` was
   itself wrong for the same reason: the application is a complete
   email that never mentions LOS at all, so the required assertion is
   verifiably absent -- a clear non_compliant, consistent with every
   other "must include X in your quote" topic in this fixture (e.g.
   `far_52_212_3_reps_and_certs`), not insufficient_information.
   Confirmed with a fresh real run: the model gets the corrected,
   narrower `los_compliance_assertion` right (non_compliant).
3. **Verdict-accuracy sections in both `evaluation_report.md` and the
   verdict-only report now show both sides for every wrong verdict**:
   the model's own evidence/reasoning (bold `model's ...` labels) next
   to what `true_verdicts.json` expected (`expected ...` labels) --
   previously only the model's side was shown, which made it look like
   the fixture's expectation was unstated. Added a new "Mismatched
   clean matches" list right under the confusion matrix (previously
   the matrix had zero detail for its own off-diagonal cells) via
   `VerdictAccuracyResult.mismatched_clean_groups`. Verdict-only report
   no longer lists `[OK]` outcomes (mismatches only) and adds
   `true_rationale` per outcome.
4. **`evaluation/verdict_only.py` had the same bug as the main report
   pre-fix**: `_render_outcome` showed the model's own evidence and
   the true rationale, but never the true/expected evidence quotes.
   Added `VerdictOnlyOutcome.true_evidence_quotes` and rendered them.
   Regenerated both `evaluation_report.md` and `verdict_only_report.md`
   for both cases from the already-saved `verdict_only_verdicts.json`
   (no new LLM calls needed).
5. **`product_chart_full_pricing` false-compliant case confirmed as a
   model reasoning miss, not a retrieval miss.** Checked
   `predicted_retrieved_evidence.json` directly: one retrieved chunk
   (application.txt 2187-3446) contains both "Total quoted price for
   this solicitation: $21,540.00." and, four lines later, "Grand total
   of the line items above: $22,940.00." -- the model had the whole
   contradiction in front of it in one chunk, cited only the second
   number in its own evidence, and never noticed the mismatch.

## Multi-file input parsing (`steps/ingestion.py`)

Five real tenders were checked for suitability as future test cases
this round; none arrived as a single `.txt` file (docx, docx+pdf,
docx+docx+xlsx). Added a real ingestion step instead of the one-off
scratch scripts used to convert each of them by hand so far:

1. **New `steps/ingestion.py`**: `load_document_texts(paths)` dispatches
   per file extension (`.txt`/`.docx`/`.pdf`/`.xlsx`; legacy `.doc`
   raises a clear "convert to .docx" error rather than attempting a
   fragile antiword/LibreOffice integration). `.docx` extraction walks
   `document.element.body` in document order (paragraphs and tables
   interleaved, matching how the file actually reads) rather than
   `document.paragraphs`, which silently drops tables. Non-breaking
   spaces (U+00A0) are normalized to regular spaces for every format --
   a real bug hit by hand on the first docx conversion (case
   `36C24126Q0731`), where citation offsets didn't line up until this
   was done.
2. **Files are chunked independently, then the chunk lists are just
   appended -- no raw-text concatenation with delimiters, no offset
   manifest.** Confirmed by reading `backends/vectorstore.py` and
   `steps/evidence_retrieval.py` that this needs zero other code
   changes: `_compute_point_id` only needs `chunk_index` unique
   *within* a `document_path`, and neighbor-chunk expansion is already
   scoped by `document_path`. This also means each file's own clause-
   numbering style is detected independently instead of guessing one
   pattern across a mix of styles, and `TextSpan.document_path` (via
   `steps/text_matching.py` copying `chunk.document_path`) now points
   at the real source file a citation came from, instead of always
   echoing whatever single path was passed on the CLI.
3. **Deliberately not solved**: resolving "see Attachment X" cross-
   references (via reference detection + semantic retrieval into the
   attachment, or inlining short attachments as shared context for
   every chunk). Discussed and dropped in favor of just chunking
   attachments the same as the main text -- if an attachment states
   actual requirements, extraction finds them there directly, no
   special-casing needed. Revisit only if a real case shows this
   missing something (e.g. an attachment too large to reliably self-
   describe in isolation, unlike the short, self-labeled "SALIENT
   CHARACTERISTICS" attachment in `36C26226Q1384` that motivated this
   whole discussion).
4. `run_pipeline(requirements_paths: list[str], application_paths:
   list[str])` and the CLI's `--requirements`/`--application` both take
   one or more paths now (`nargs="+"`), symmetric on both sides even
   though only the requirements side has hit a real multi-file case so
   far.

## Vector store collection isolation bug (found and fixed)

Found while running two `scripts/evaluate_verdicts.py` invocations for
different cases in the background at the same time (to extend the new
retrieved-context rendering to the verdict-only report). Confirmed, not
guessed: `backends/vectorstore.py`'s `index_chunks` always called
`reset_collection` (delete + recreate) against one fixed collection
name (`settings.vector_store_collection_name`, no per-case scoping),
so the later-starting process's reset wiped out the earlier process's
freshly-indexed chunks mid-run. Direct inspection of
`data/36C24126Q0731/verdict_only_retrieved_evidence.json` after the
concurrent run showed 8 of 12 requirements retrieved evidence chunks
whose `document_path` was `140p6426q0127_piro_handrail`'s
`application.txt`, not its own -- i.e. real verdicts were generated
against another tender's application text.

**Fixed**: `collection_name` is now a required, explicit parameter on
every function in `backends/vectorstore.py`
(`reset_collection`/`index_chunks`/`search_similar_chunks`/
`get_neighbor_chunks`, plus a new `delete_collection`) -- no more
implicit global collection name inside these functions. A new
`case_collection_name(identifier)` helper builds
`f"{base_name}__{identifier}"`. `pipeline.run_pipeline` derives its
collection name from the same per-run `thread_id` it already generates
for the checkpointer, and deletes that collection in a `finally` block
after the graph finishes (real pipeline runs never need the collection
to survive past the run, since the full result already comes back
in-memory). `scripts/evaluate_verdicts.py` derives its collection name
from `case_dir.name` instead (deterministic, so re-running the same
case is still idempotent, and it's helpful for the collection to
persist across runs of the same case for debugging). `graph.py`'s
`PipelineState`/`RequirementVerdictInput` both carry `collection_name`
through explicitly, including through the `Send`-based fan-out to
`generate_verdict_node` (which does not otherwise see full graph
state).

Verified the fix under the exact failure scenario: re-ran both cases'
`evaluate_verdicts.py` concurrently again, and confirmed both
`verdict_only_retrieved_evidence.json` files now contain only their own
case's `document_path`. Also deleted the one stale pre-fix shared
collection left over in Qdrant. `pytest tests/` (64 passed), `pyright .`
(0 errors), `pycodestyle --max-line-length=88 .` all clean after the
change. No dedicated unit tests existed for `backends/vectorstore.py`
or `steps/evidence_retrieval.py` before this (integration-only, real
Qdrant); none added here either since the fix is a straightforward
required-parameter threading change with no new branching logic to
cover, and the real concurrent re-run is the actual regression check.
