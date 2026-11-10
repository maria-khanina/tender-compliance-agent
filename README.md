# Tender Agent

A pipeline that checks whether a bidder's tender application
satisfies the requirements listed in a tender's requirements
document. Given two plain-text files (requirements, application),
it produces a Markdown compliance report listing, for every
requirement, whether the application is compliant, non-compliant,
lacks sufficient information, or contains contradictory
information, together with the supporting quotes.

## Swappable backends

The language model, vector store, and embedding backend are each
selected by a `*_PROVIDER` setting (`LANGUAGE_MODEL_PROVIDER`,
`VECTOR_STORE_PROVIDER`, `EMBEDDING_PROVIDER`) rather than hardcoded.
Each provider value is dispatched, in its own module under
`backends/` (`llm_client.py`, `vectorstore.py`, `embeddings.py`), to a
concrete implementation behind a stable, backend-agnostic function
signature — the rest of the pipeline never imports a
backend-specific type. Only one implementation exists per axis
today (`openai_compatible`, `qdrant`, `sentence_transformers`), so
switching is still config-only *among implemented options*; adding
a genuinely new backend still means writing one adapter and
registering it, not touching the rest of the codebase.

## Architecture

Before the graph runs, `pipeline.py` parses every input file (one or
more per side, any mix of `.txt`/`.docx`/`.pdf`/`.xlsx`) into plain
text via `steps/ingestion.py`, dispatching by file extension. Each
file keeps its own identity: every citation the pipeline produces
(`TextSpan.document_path`) points back to the specific input file a
quote came from, not to some synthetic merged document. Files are not
concatenated before chunking either — each one is split into chunks
independently (so a numbering scheme detected in the main solicitation
doesn't get misapplied to an attachment's different layout, see
`steps/chunking.py`), and the resulting chunk lists are just appended
together before extraction. An attachment referenced from the main
document (e.g. "see Attachment B for the salient characteristics") is
therefore extracted the same way as the main text: if it states actual
requirements, the model finds them when it reaches that chunk, with no
separate reference-resolution step.

The pipeline itself is a LangGraph state graph, wired up in
`graph.py`; the node logic lives in `steps/`:

1. `split_requirements_node` — splits each requirements document into
   chunks, preferring numbered-clause boundaries over blind
   character splitting when a numbering scheme is detected
   (`steps/chunking.py`).
2. `extract_requirements_node` — runs once per chunk (fanned out via
   LangGraph's `Send` API for parallelism) and asks the language
   model to extract verbatim requirement quotes, then locates each
   quote's exact position in the source text
   (`steps/requirements_extraction.py`, `steps/text_matching.py`).
3. `deduplicate_requirements_node` — clusters near-duplicate
   requirement candidates by embedding similarity, then asks the
   language model to resolve each cluster into non-overlapping
   groups with a canonical text, avoiding both missed duplicates and
   accidental merging of distinct requirements
   (`steps/deduplication.py`).
4. `extract_conditions_node` — reserved for turning a requirement
   into one or more machine-checkable conditions (for example, a
   numeric threshold, or a range expressed as two thresholds
   combined with AND semantics). Disabled by default in this
   version; see `CONDITION_EXTRACTION_ENABLED` below
   (`steps/conditions.py`).
5. `index_application_node` — splits each application document into
   chunks and indexes them into the vector store
   (`steps/chunking.py`, `backends/vectorstore.py`).
6. `generate_verdict_node` — runs once per requirement (also fanned
   out via `Send`): retrieves the most relevant application chunks,
   then either compares an extracted numeric value against the
   requirement's condition deterministically, or falls back to a
   language-model verdict with quoted, role-tagged evidence
   (`steps/evidence_retrieval.py`, `steps/value_extraction.py`,
   `steps/verdicts.py`). If the requirement was marked
   `is_text_verifiable: false` at extraction time (see below), this
   step still retrieves relevant application chunks for the report but
   does not produce a compliant/non-compliant verdict at all.
7. `build_report_node` — renders the final Markdown report
   (`steps/report.py`).

## Report structure

The report splits requirements into a "Mandatory Requirements" section
and a "Preferred (Non-mandatory) Requirements" section
(`Requirement.is_mandatory`, decided by the model at extraction time).
Within each section, verdicts are sorted by severity —
non-compliant, then contradictory, then insufficient-information, then
compliant last — so problems are visible immediately without scrolling
past everything that's fine. Two more sections follow: "Not Verifiable
From Application Text Alone" lists requirements the model judged
impossible to confirm from text alone (for example, whether a
registration is genuinely active, not just claimed) — the application
excerpts retrieved for these are shown for the reader's convenience,
but no automatic verdict is attached, so the pipeline never
manufactures false confidence about a fact it cannot check. "Needs
Manual Review: Unverified Citations" lists every verdict that cited a
quote `steps/text_matching.py` could not locate verbatim in the source
text (`Evidence.citation_verified == False`); those verdicts still
appear in their normal section too, just flagged inline.

Every located citation also records `TextSpan.match_precision`
(`"precise"` for an exact or whitespace-normalized match, `"fuzzy"` for
a rapidfuzz approximate match, `None` if nothing was found) — surfaced
inline in the report and available for anyone inspecting
`predicted_requirements.json`/`predicted_verdicts.json` directly.

The graph is checkpointed to a local SQLite database
(`checkpoints.db`), so a crash mid-run does not require re-running
already-completed stages.

## Known v1 limitations

- Legacy `.doc` (pre-2007 binary Word format) is not supported;
  convert to `.docx` first. `.txt`, `.docx`, `.pdf`, and `.xlsx` are
  all supported (`steps/ingestion.py`).
- Retrieval is per-requirement. If two contradictory statements in
  the application are both far (semantically) from the requirement's
  wording, the contradiction may not be detected.
- `CONDITION_EXTRACTION_ENABLED` is `False` by default, so every
  requirement is judged by the language model rather than
  deterministically, even though the numeric-threshold checker is
  fully implemented. Flip the flag in `config.py` to turn it on.

## Setup

1. Copy the environment template and fill in the values:

   ```
   cp .env.example .env
   ```

2. Start the vector store:

   ```
   docker compose up -d qdrant
   ```

3. Make a language model available. Two provider options (see
   `.env.example` for the exact settings each one needs):

   - `google_genai` — native Gemini via an API key, no local setup.
     This is what the sample case in this repo was actually run and
     validated against (local GPU/WSL2 vLLM setup was never
     completed for this project; see `NOTES.md`).
   - `openai_compatible` — any OpenAI-wire-protocol endpoint at
     `LANGUAGE_MODEL_BASE_URL`, including vLLM:

     ```
     pip install vllm
     vllm serve <model-name> --port 8000
     ```

     Or the bundled vLLM container (Linux/WSL2 with the NVIDIA
     container toolkit):

     ```
     docker compose --profile vllm up -d vllm
     ```

4. Install dependencies:

   ```
   pip install -r requirements.txt -r requirements-dev.txt
   ```

## Running the pipeline

```
python scripts/run_pipeline.py \
    --requirements data/140p6426q0127_piro_handrail/tender.txt \
    --application data/140p6426q0127_piro_handrail/applications/a/application.txt \
    --output data/140p6426q0127_piro_handrail/applications/a/runs/gemini/predicted.md
```

`--requirements` and `--application` each take one or more file paths
(any mix of `.txt`/`.docx`/`.pdf`/`.xlsx`), for tenders that ship as a
main solicitation plus separate attachments:

```
python scripts/run_pipeline.py \
    --requirements data/36C26226Q1384/RFQ.docx \
                   data/36C26226Q1384/AttachmentB.docx \
    --application data/36C26226Q1384/applications/a/application.txt \
    --output data/36C26226Q1384/applications/a/runs/gemini/predicted.md
```

Point `--output` under the application variant's own
`applications/<variant>/runs/<run-label>/` directory (see
`case_layout.py`) — keeps a run's output paired with the fixtures it
should be checked against and separated from any other run-label's
results for the same variant, instead of scattered in the project
root or overwriting a previous run. Besides the Markdown report, this
writes four underlying JSON files next to it, named to mirror the
`true_*.json` fixtures for easy comparison:
`predicted_requirement_drafts.json` (the `RequirementDraft` list
before deduplication), `predicted_requirements.json` (the
deduplicated `Requirement` list), `predicted_verdicts.json` (the
`Verdict` list), and `predicted_retrieved_context.json` (per
requirement, the full set of application chunks
`retrieve_context_chunks` handed to the verdict
step *before* it chose what to cite — the artifact needed to tell
apart "retrieval never surfaced the evidence" from "it saw the
evidence and didn't act on it," see `NOTES.md`). Application chunks
are also inspectable directly in Qdrant's dashboard at
`http://localhost:6333/dashboard`. Raw pre-dedup requirement drafts
and dedup clusters still only exist transiently in the LangGraph
checkpoint (`checkpoints.db`), keyed by a random `thread_id` that
isn't currently surfaced anywhere.

## Sample case

`data/140p6426q0127_piro_handrail/` holds one real tender (a National
Park Service RFQ) paired with a synthetic application engineered to
hit all four verdict labels, plus `true_requirements.json` and
`true_verdicts.json` — hand-authored fixtures (not exact-match
targets) for judging extraction recall/precision and verdict
correctness against a real document. `true_requirements.json` aims to
be exhaustive over the tender's bidder-facing, pre-award requirements
-- both the ones a pipeline can check by reading application.txt
(`is_text_verifiable: true`) and the ones it structurally cannot,
because they describe an action or event rather than application
content (`is_text_verifiable: false`, e.g. the submission channel/
deadline). There is no separate "excluded clauses" list: text that
isn't a bidder requirement at all (government process instructions,
post-award clauses, bare clause titles with no substantive content)
is simply absent from the fixture, and a predicted requirement that
quotes it honestly shows up as "unexplained" in the precision section
rather than being silently excused. Each requirement's `source` is
`{document_path, quote, spans: [{start_char, end_char, used_for_matching}, ...]}`
-- usually one span, but a requirement whose meaning depends on
non-contiguous text (e.g. a shared lead-in clause plus one of several
enumerated items) uses several, with `quote` set to their text joined
by `" ... "`. `used_for_matching` (default `true`) can be set `false`
on a span that is identical across several requirements (like a
shared lead-in): without it, a predicted citation covering just the
lead-in plus one enumerated item would overlap every requirement that
shares that lead-in, not only the one it actually matches. For a case
whose tender comes as several files (a main solicitation plus one or
more attachments), `document_path` in each requirement/evidence
`source` should point at the specific original file the quote was
taken from -- matching what the real pipeline reports -- rather than
inventing one merged `tender.txt` for the whole case. Each future test
case should get its own subdirectory under `data/` with the same two
fixture files, named after the tender's solicitation number.

## Evaluating a run

```
python scripts/evaluate.py --case-dir data/140p6426q0127_piro_handrail
```

`--variant` (default `a`, the case's canonical application) and
`--run-label` (default `gemini`) select which
`applications/<variant>/runs/<run-label>/predicted_*.json` to
evaluate; pass them explicitly to evaluate a `b`/`c` variant or a
differently-labeled run (e.g. an SFT model's own run-label).

Compares a case directory's `predicted_*.json` (from `run_pipeline.py`)
against its `true_*.json` fixtures and prints a Markdown report. The
report opens with a "Summary metrics" section — a fenced JSON block
with every headline number (recall, precision, is_mandatory/
is_text_verifiable accuracy, verdict accuracy, false-compliant/
false-issue rate, evidence recall, and verdict-only accuracy when
that artifact is present) so a separate script can parse it and
average metrics across several tenders without scraping prose;
`null` marks a metric that doesn't apply to this run. Everything
after that is the same numbers explained in detail: requirement
recall (with over-split/over-merge diagnostics from a
bipartite overlap-graph match between true and predicted citation
spans), precision (fraction of predicted requirements matched to a
true one -- the rest are "unexplained" and need manual triage, not
automatically penalized as wrong, since the fixture itself could still
be incomplete), coverage flags for incomplete-capture/over-broad-
citation cases, `is_mandatory`/`is_text_verifiable` accuracy (scored
on clean 1:1 matches and on one-to-many split/merge matches with an
all-or-nothing rule on the "many" side, listing the true and predicted
value for every mismatch; tangled many-to-many matches are excluded,
since there's no single "one" to compare against), a verdict confusion
matrix (rendered as a table over the four verdict labels, with a note
explaining any all-zero row -- usually a true topic that was never
extracted or never got a verdict) plus false-compliant/false-issue
rates (each entry includes the requirement text, cited evidence, and
the model's reasoning), and evidence recall (whether `predicted_retrieved_context.json` actually
contained the evidence `true_verdicts.json` says it should have — the
artifact needed to diagnose retrieval-vs-model failures, see
`NOTES.md`). Pass `--report-output <path>` to write the report to a
file instead of stdout. The matching/metrics logic lives in
`evaluation/matching.py`,
`evaluation/requirement_metrics.py`, `evaluation/verdict_metrics.py`
and `evaluation/evidence_metrics.py`, orchestrated by
`evaluation/orchestrator.py` and rendered by `evaluation/rendering.py`;
`evaluation/__init__.py` re-exports the public surface the CLI imports
from.

`scripts/evaluate.py` measures the whole pipeline end to end, so a
verdict is only scored when extraction+dedup also happened to produce
a cleanly-matched requirement for it. To isolate the verdict-generation
step by itself:

```
python scripts/evaluate_verdicts.py --case-dir data/140p6426q0127_piro_handrail
```

Same `--variant`/`--run-label` arguments as `scripts/evaluate.py`
above. This builds a synthetic `Requirement` directly from each
`true_requirements.json` entry (its own description, citation, and
`is_mandatory`/`is_text_verifiable` flags — no extraction involved),
runs real evidence retrieval and verdict generation against
`application.txt`, and compares the result to `true_verdicts.json`'s
`acceptable_verdicts` by `topic_id`. No match-group logic is involved
at all, so extraction quality can never mask or distort this number.
It also writes `verdict_only_verdicts.json` next to the report; if
that file is present, `scripts/evaluate.py` picks it up automatically
and appends a "Verdict-only evaluation" section to the combined
report, so the two evaluations don't need to be read separately.
Requires a real language-model + vector-store connection, same as
`run_pipeline.py`. Logic lives in `evaluation/verdict_only.py`
(synthetic-requirement building, scoring, rendering — all pure and
tested) plus the impure retrieval/generation loop in the script itself.

To compare metrics across every evaluated case at once:

```
python scripts/aggregate_metrics.py --data-dir data --output data/metrics_summary.md
```

Same `--variant`/`--run-label` arguments (defaults `a`/`gemini`),
applied across every case at once. Scans every subdirectory of
`--data-dir` that has a `true_requirements.json`, re-runs `evaluate()`
(and, where a `verdict_only_verdicts.json` artifact exists under that
variant/run-label, the verdict-only scoring) on each case that has
already been run, and writes one Markdown table — one row per tender
plus a **mean** row averaging each column over the cases where that
metric applies (`n=` shows how many). Cases with no
`predicted_requirements.json` yet for that variant/run-label are
listed as skipped rather than silently dropped. Reuses
`evaluation.build_summary_metrics`, the same function that renders
each case's own "Summary metrics" JSON block, so the two never drift
apart.

## Fine-tuning the verdict model

The verdict step can run on a local Qwen3-4B fine-tuned for this task
instead of a hosted model. The training targets are the gold verdicts of
the cases: verdict, evidence quotes and reasoning written by a stronger
LLM, so supervised fine-tuning distills that model's verdicts into the
small one. The prompts are built with the real retrieval step, so the
model is trained on the same context it sees at inference. Cases are split
into train (431 rows), validation (96) and test (96) by `sft/split.json`.

Training (`sft/`, Hugging Face TRL):

1. **SFT** (`train_verdict_lora.py`): the base model is loaded in 4-bit
   NF4 with double quantization and a LoRA adapter (rank 16) is trained on
   the attention and MLP projections, with bf16 compute, gradient
   checkpointing and 8 gradient accumulation steps; training stops early
   on validation macro F1.
2. **Merge** (`merge_sft_adapter.py`): the adapter is added to the bf16
   base shard by shard and saved as safetensors, which becomes the
   reference model of DPO.
3. **Preference pairs** (`mine_dpo_pairs_local.py`): 8 answers per prompt
   are sampled from the merged model in the same 4-bit quantization that
   DPO trains; each distinct wrong verdict among them becomes a rejected
   answer paired with the gold answer (99 pairs). An earlier run took the samples from an AWQ-quantized model
   served by vLLM; because its quantization differs from the model being
   trained, its pairs did not reflect that model's own mistakes.
4. **DPO** (`train_dpo.py`): a new LoRA adapter on the merged model, beta
   0.1, learning rate 5e-5.
5. **Comparison** (`compare_models.py`) of the base model, SFT and DPO on
   the validation split:

| Metric | Base | SFT | DPO |
|---|---|---|---|
| Verdict accuracy | 0.531 | 0.573 | 0.583 |
| Macro F1 | 0.254 | 0.292 | 0.436 |
| Evidence recall | 0.922 | 0.947 | 0.931 |
| Answers that failed to parse (of 96) | 13 | 3 | 1 |

SFT mostly teaches the answer format (13 unparseable answers down to 3);
DPO raises macro F1, largely through the `contradictory` class (F1 0 to
0.55), which has only 4 validation examples, so that gain is uncertain.
`non_compliant` stays below 0.1 F1 at every stage. Full numbers per class
are in `sft/eval_runs/20260917_123332_qwen3-4b-v1_bnb4bit/`.

## Training pipeline on Slurm

The verdict model is post-trained in five stages, each a separate Slurm
job on a single-node cluster inside WSL2:

| Stage | Module | Resources |
|---|---|---|
| SFT | `sft.train_verdict_lora` | GPU |
| Merge the SFT adapter into bf16 safetensors | `sft.merge_sft_adapter` | CPU only |
| Mine on-policy DPO pairs | `sft.mine_dpo_pairs_local` | GPU |
| DPO | `sft.train_dpo` | GPU |
| Compare base, SFT, and DPO on validation | `sft.compare_models` | GPU |

Each stage starts only after the previous one succeeded
(`--dependency=afterok`), and a failed stage cancels the rest of the
chain. The GPU is a generic resource (`gres/gpu`, mapped to `/dev/dxg`
in WSL2), so only one GPU job runs at a time and the others wait in the
queue instead of running out of GPU memory. Every stage gets the same run
id, which ties its outputs together under `sft/runs/`.

```
sudo bash slurm/setup_wsl.sh
bash slurm/smoke_test.sh
bash slurm/submit_pipeline.sh [run_id]
```

`setup_wsl.sh` installs Slurm and MUNGE and writes `/etc/slurm` from the
templates in `slurm/`; it needs systemd enabled in `/etc/wsl.conf`.
`smoke_test.sh` checks that a job sees the GPU, that a second GPU job
waits for the first, and that a dependent job starts after its parent.
Job resources and the training virtual environment are set in
`slurm/settings.sh`; logs go to `slurm/logs/<stage>-<job id>.log`, and
finished jobs are recorded in `/var/log/slurm/job_completions.log`.

## Training memory and step time

`slurm/submit_memory_experiment.sh` measures the QLoRA SFT setup (4-bit
base, LoRA adapter, bf16 autocast, AdamW) in seven configurations, one
Slurm job each, and `sft.memory_report` writes
`sft/memory_runs/memory_report.md`. Each job trains 2 warm-up and 6
measured optimizer steps on real training text packed to a fixed length.
Measured on an 8 GB laptop GPU under WSL2:

| Setup | Peak allocated | Seconds per step | Tokens per second |
|---|---|---|---|
| Checkpointing on, 1024 tokens | 4.81 GiB | 1.74 | 590 |
| Checkpointing off, 1024 tokens | 11.67 GiB | 19.91 | 51 |
| Checkpointing on, 2048 tokens | 6.73 GiB | 3.84 | 534 |
| Checkpointing off, 2048 tokens | out of memory | | |
| Checkpointing on, 8 × 1024 tokens in one micro-batch | out of memory | | |
| Checkpointing on, 1 × 1024 tokens, 8 accumulation steps | 4.93 GiB | 13.97 | 586 |

What the numbers show:

- The frozen 4-bit base and the adapter take 2.62 GiB; LoRA weights,
  gradients and Adam moments are only 0.49 GiB of it. Everything above that
  is activations, so activation memory decides what fits.
- Gradient checkpointing keeps activations within the GPU. Without it, a
  1024-token step needs 11.7 GiB: the Windows driver silently spills the
  excess into shared system memory instead of failing, and the step becomes
  11 times slower. A peak above the card's 8 GiB in this table means spilled
  memory, not a measurement error.
- Gradient accumulation gives the effective batch of 8 × 1024 tokens with
  the memory of a single micro-batch (4.93 GiB against out of memory) and
  the same throughput, so the real SFT and DPO runs use micro-batch 1 with
  8 accumulation steps.
- Full fine-tuning of the same 4B model with Adam would need about 60 GiB
  before activations (16 bytes per parameter), which is why the model is
  quantized and only a LoRA adapter is trained.

## Tests, style, and types

```
pytest tests/
pycodestyle --max-line-length=88 .
pyright .
```

`pyright .` is the same checker VS Code's Pylance runs in the editor
(`pyrightconfig.json` at the project root is picked up by both), so
issues surfaced here match what's already highlighted live in the
IDE.
