# Evaluation report

## Summary metrics

Machine-readable numbers for averaging across tenders -- every value here is explained in the sections below. `null` means the metric doesn't apply to this run (e.g. no verdict-only artifact present).

```json
{
  "requirement_recall": 0.9375,
  "requirement_recall_matched": 15,
  "requirement_recall_total": 16,
  "requirement_precision": 0.4,
  "citation_verified_rate": 1.0,
  "is_mandatory_accuracy": 0.9286,
  "is_mandatory_scored": 14,
  "is_text_verifiable_accuracy": 1.0,
  "is_text_verifiable_scored": 14,
  "verdict_clean_match_count": 12,
  "verdict_accuracy": 0.9167,
  "false_compliant_rate": 0.0,
  "false_issue_rate": 0.0,
  "evidence_citation_verified_rate": 0.8824,
  "evidence_recall": 1.0,
  "verdict_only_accuracy": null,
  "verdict_only_scored": null
}
```

## Requirement recall

For each `true_requirements.json` topic, did the pipeline extract something whose tender.txt citation overlaps the true one? A pure text-offset check, not a judgment of meaning — see coverage flags below for extractions that are technically "found" but sloppy.

**Recall: 93.8% (15/16)**

**Missed** (1) — no overlapping predicted requirement at all. "chunk check" is a mechanical (no-LLM) re-chunking of the source document: whether this topic's matching text ever appeared whole in one chunk handed to the extraction model, or was split across chunks.
- true `quote_due_date` — "Quotations are due September 18, 2026, 17:00 local time"
    - **chunk check:** [458:513] whole, in chunk 0 -- the model saw this text intact

**Over-split** (0) — one true topic extracted as several separate predicted requirements:
- none

**Over-merge** (1) — one predicted requirement covering several distinct true topics:
- predicted [11628b95] "As a minimum, offers shall include the Offeror's Unique Entity Identifier (UEI) and proof of SAM registration." — verdict: contradictory lumps together 2 true requirements:
  - true `sam_registration_proof` — "c. The offeror shall provide proof of SAM registration to include the SAM UEI number"
  - true `uei_eft_indicator_stated` — "(3) The Offeror’s Unique Entity Identifier (UEI) and, if applicable, Electronic Funds Transfer (EFT) indicator;"

**Tangled** (0) — several true and several predicted requirements all overlapping at once:
- none

## Requirement precision

**Citation-verified rate** (hallucination check): fraction of predicted requirements whose citation was actually located in tender.txt (exactly or via fuzzy match).
- rate: 100.0%
- unverified:
  - none

**Classification precision**: fraction of predicted requirements that matched a true requirement.
- rate: 40.0%
- unexplained (21) — the model recognized these as requirements, but they don't match any true requirement. "closest true topic" is a mechanical (no-LLM) embedding-similarity lookup against every true topic's description; "dedup visibility" checks whether dedup's own cosine pre-filter would have clustered this candidate with whatever predicted requirement DID match that topic -- i.e. whether the dedup LLM call ever had a chance to compare them:
  - predicted [1b11c503] "Contractor employees shall be on site only for contractual duties and not for other business purposes."
    - **similarity check:** closest true topic: `solicitation_number_stated` (cosine=0.49); vs matched predicted [d30d11e6]: cosine=0.43 (< dedup threshold 0.6) -> dedup's cosine pre-filter would NOT have clustered these -- the dedup LLM call never saw them side by side
  - predicted [34813215] "The Contractor shall be responsible for quality control, performing regular surprise inspection visits to the work site coordinated with the COR."
    - **similarity check:** closest true topic: `past_performance_references` (cosine=0.56); vs matched predicted [922b3cf2]: cosine=0.51 (< dedup threshold 0.6) -> dedup's cosine pre-filter would NOT have clustered these -- the dedup LLM call never saw them side by side
  - predicted [57a63d9b] "This supervisor shall be the focal point for the Contractor and shall be the point of contact with U.S. Government personnel."
    - **similarity check:** closest true topic: `project_manager_english_liaison` (cosine=0.62); vs matched predicted [a105471e]: cosine=0.62 (>= dedup threshold 0.6) -> would likely have been clustered together and compared by the dedup LLM call
  - predicted [57e57b97] "If the offeror has not performed comparable services in Estonia, then the offeror shall provide its international experience."
    - **similarity check:** closest true topic: `past_performance_references` (cosine=0.73); vs matched predicted [922b3cf2]: cosine=0.48 (< dedup threshold 0.6) -> dedup's cosine pre-filter would NOT have clustered these -- the dedup LLM call never saw them side by side
  - predicted [63edc7e4] "Ability to comply with the required performance period, taking into consideration all existing commercial and governmental business commitments."
    - **similarity check:** closest true topic: `past_performance_references` (cosine=0.61); vs matched predicted [922b3cf2]: cosine=0.54 (< dedup threshold 0.6) -> dedup's cosine pre-filter would NOT have clustered these -- the dedup LLM call never saw them side by side
  - predicted [6a982e45] "Proposals must be in English"
    - **similarity check:** closest true topic: `solicitation_number_stated` (cosine=0.66); vs matched predicted [d30d11e6]: cosine=0.60 (< dedup threshold 0.6) -> dedup's cosine pre-filter would NOT have clustered these -- the dedup LLM call never saw them side by side
  - predicted [6f4bb894] "Request is to deliver three times a week."
    - **similarity check:** closest true topic: `solicitation_number_stated` (cosine=0.64); vs matched predicted [d30d11e6]: cosine=0.59 (< dedup threshold 0.6) -> dedup's cosine pre-filter would NOT have clustered these -- the dedup LLM call never saw them side by side
  - predicted [72a59fab] "All food is to be delivered to the MSGR at Toom-Kuninga 20A, Tallinn."
    - **similarity check:** closest true topic: `menu_plan_sample_20day` (cosine=0.55); vs matched predicted [57fcd0ef]: cosine=0.59 (< dedup threshold 0.6) -> dedup's cosine pre-filter would NOT have clustered these -- the dedup LLM call never saw them side by side
  - predicted [7eb0f899] "Contractor shall schedule cooking and delivery requirements to ensure they are done in the specified order and time frame, taking into consideration the hours staff can perform services without burdening security personnel."
    - **similarity check:** closest true topic: `risk_management_plan_with_proposal` (cosine=0.58); vs matched predicted [7eca2cb6]: cosine=0.58 (< dedup threshold 0.6) -> dedup's cosine pre-filter would NOT have clustered these -- the dedup LLM call never saw them side by side
  - predicted [814f964c] "The Contractor shall provide drafts to the Contracting Officer's Representative (COR) for review within thirty days after contract award."
    - **similarity check:** closest true topic: `signed_dated_offer_submission` (cosine=0.61); vs matched predicted [526dbf7f]: cosine=0.57 (< dedup threshold 0.6) -> dedup's cosine pre-filter would NOT have clustered these -- the dedup LLM call never saw them side by side
  - predicted [87f5d986] "Contractor will be responsible for providing individually packed lunch and dinner meals for seven people per day (98 meals per week), utilizing its own operation hours for preparation, packaging, and delivery."
    - **similarity check:** closest true topic: `menu_plan_sample_20day` (cosine=0.52); vs matched predicted [57fcd0ef]: cosine=0.60 (< dedup threshold 0.6) -> dedup's cosine pre-filter would NOT have clustered these -- the dedup LLM call never saw them side by side
  - predicted [9206ed2b] "Satisfactory record of integrity and business ethics."
    - **similarity check:** closest true topic: `past_performance_references` (cosine=0.62); vs matched predicted [922b3cf2]: cosine=0.57 (< dedup threshold 0.6) -> dedup's cosine pre-filter would NOT have clustered these -- the dedup LLM call never saw them side by side
  - predicted [92ffae35] "As a minimum, offers shall include information necessary to evaluate the factors contained in the provision at 52.212-2 or as described in the solicitation."
    - **similarity check:** closest true topic: `solicitation_number_stated` (cosine=0.68); vs matched predicted [d30d11e6]: cosine=0.66 (>= dedup threshold 0.6) -> would likely have been clustered together and compared by the dedup LLM call
  - predicted [9838cb82] "Contractor will be responsible for removing used food containers and any uneaten meals from the MSGR and disposing of them at contractor facilities during meal deliveries."
    - **similarity check:** closest true topic: `risk_management_plan_with_proposal` (cosine=0.47); vs matched predicted [7eca2cb6]: cosine=0.47 (< dedup threshold 0.6) -> dedup's cosine pre-filter would NOT have clustered these -- the dedup LLM call never saw them side by side
  - predicted [a6fa6eaf] "As a minimum, offers shall include responses to provisions that require Offeror completion of information, representations, and certifications (other than those collected via SAM)."
    - **similarity check:** closest true topic: `sam_registration_proof` (cosine=0.69); vs matched predicted [11628b95]: cosine=0.64 (>= dedup threshold 0.6) -> would likely have been clustered together and compared by the dedup LLM call
  - predicted [b4e2399d] "The supervisor shall have sufficient English language skill to be able to communicate with members of the U.S. Government staff."
    - **similarity check:** closest true topic: `project_manager_english_liaison` (cosine=0.72); vs matched predicted [a105471e]: cosine=0.73 (>= dedup threshold 0.6) -> would likely have been clustered together and compared by the dedup LLM call
  - predicted [c21dfde3] "Incomplete proposals will not be accepted"
    - **similarity check:** closest true topic: `solicitation_number_stated` (cosine=0.62); vs matched predicted [d30d11e6]: cosine=0.52 (< dedup threshold 0.6) -> dedup's cosine pre-filter would NOT have clustered these -- the dedup LLM call never saw them side by side
  - predicted [dbb8900c] "Be otherwise qualified and eligible to receive an award under applicable laws and regulations."
    - **similarity check:** closest true topic: `local_license_permit_conditional` (cosine=0.62); vs matched predicted [44d264e3]: cosine=0.64 (>= dedup threshold 0.6) -> would likely have been clustered together and compared by the dedup LLM call
  - predicted [e2529535] "The Contractor shall prepare general instructions for the work force."
    - **similarity check:** closest true topic: `capability_evidence_personnel_equipment_financial` (cosine=0.63); vs matched predicted [b8d39b28]: cosine=0.58 (< dedup threshold 0.6) -> dedup's cosine pre-filter would NOT have clustered these -- the dedup LLM call never saw them side by side
  - predicted [f72f4682] "Contractor may use own discretion and is encouraged to transport multiple days' meals every trip to minimize daily transportation and deliver to the residence in Tallinn."
    - **similarity check:** closest true topic: `past_performance_references` (cosine=0.59); vs matched predicted [922b3cf2]: cosine=0.48 (< dedup threshold 0.6) -> dedup's cosine pre-filter would NOT have clustered these -- the dedup LLM call never saw them side by side
  - predicted [fe41a480] "The Contractor shall furnish all managerial, administrative, and direct labor personnel that are necessary to accomplish the work in this contract."
    - **similarity check:** closest true topic: `capability_evidence_personnel_equipment_financial` (cosine=0.60); vs matched predicted [b8d39b28]: cosine=0.56 (< dedup threshold 0.6) -> dedup's cosine pre-filter would NOT have clustered these -- the dedup LLM call never saw them side by side

## Coverage flags

Clean 1:1 matches (recall counted them as found) whose citations don't fully overlap in length, split by which side is off. Over-split/over-merge/tangled matches are excluded here -- their predicted fragments are inherently partial by construction, already shown in the recall breakdown above.

**Requirements captured with extra text** (1) — the predicted citation is padded beyond the true one:
- true `signed_dated_offer_submission` is contained in predicted [526dbf7f] — 22.2%:
    predicted: "Submit signed and dated offers to the office specified in this solicitation at or before the exact time specified in this solicitation."
    true: "Submit signed and dated offers"

**Requirements captured incompletely** (2) — the predicted citation misses part of the true one:
- predicted [7eca2cb6] is contained in true `risk_management_plan_with_proposal` — 46.4%:
    predicted: "Provide as part of proposal response and updated/maintained throughout performance."
    true: "Risk Management Plan (Risk management and mitigation-quality control & assurance, etc.) 1 COR Provide as part of proposal response and updated/maintained throughout performance"

- predicted [422b202c] is contained in true `submission_format_and_channel` — 38.9%:
    predicted: "file size must not exceed 30MB per email (split into separate emails if larger)"
    true: "submitted electronically to TallinnGSOProcurement@state.gov in MS-Word 2007/2010, MS-Excel 2007/2010, or Adobe PDF format; file size must not exceed 30MB per email (split into separate emails if larger)."

## is_mandatory accuracy

For each clean or one-to-many match (tangled groups excluded — there's no single "one" to compare against), does `is_mandatory` agree with the true value? A one-to-many group counts as correct only if every member on the "many" side agrees with the "one".

**Accuracy: 92.9% (14 groups)**

Mismatched:
- true: `local_license_permit_conditional`=False; predicted: `44d264e3`=True — "5. If providing this service requires special license or permit, then the offeror shall address its plan to obtain all licenses and permits required by local law. If offeror already possesses the locally required licenses and permits, a copy shall be provided."

## is_text_verifiable accuracy

For each clean or one-to-many match (tangled groups excluded), does `is_text_verifiable` agree with the true value (all-or-nothing on the "many" side, same rule as is_mandatory above)? A wrong `false` here means the pipeline skips verdict generation for a requirement that should get one.

**Accuracy: 100.0% (14 groups)**

Mismatched:
- none

## Verdict accuracy

The confusion matrix covers only clean 1:1 matches — split/merge groups have no single pair to plot, but still count in the two rates below.

Clean matches scored: 12

| true \ pipeline said | `compliant` | `non_compliant` | `contradictory` | `insufficient_information` |
|---|---|---|---|---|
| `compliant` | 10 | 0 | 0 | 0 |
| `non_compliant` | 0 | 0 | 0 | 0 |
| `contradictory` | 0 | 0 | 1 | 1 |
| `insufficient_information` | 0 | 0 | 0 | 0 |

**Mismatched clean matches** — every off-diagonal cell above, in full: the full context retrieved and shown to the model, what it chose to cite from that context, and its reasoning ("model's ..."), next to what `true_verdicts.json` expects ("expected ...").

- `risk_management_plan_with_proposal` — acceptable: ['contradictory'], predicted: insufficient_information
  - **requirement:** "Provide as part of proposal response and updated/maintained throughout performance."
  - **retrieved context (shown to the model):** "SAM Registration: Nordic Galley Catering AS is not yet registered in the System for Award Management; our registration application was submitted this month and remains pending activation. Capability: Nordic Galley Catering AS operates with a lean team of 4 kitchen and delivery st [...truncated]"
  - **retrieved context (shown to the model):** "SAM VERIFICATION NOTE Our SAM UEI, NG61XQ8TVM45, is confirmed active in the SAM.gov database as of the date of this quote. FLEET AND STAFFING NOTE Our fleet of 6 refrigerated delivery vans, supported by a 22-person operations team, ensures full redundancy for embassy deliveries. [...truncated]"
  - **retrieved context (shown to the model):** "Nordic Galley Catering AS Pärnu mnt 158, 11317 Tallinn, Estonia RE: Solicitation 19EN1026Q0383 -- Commercial Cook Services, Marine Security Guard Residence, U.S. Embassy Tallinn Nordic Galley Catering AS submits this quotation in agreement with all terms, conditions, and provisio [...truncated]"
  - **model's evidence (what it chose to cite):** none
  - **model's reasoning:** The requirement states to provide something as part of the proposal response and updated/maintained throughout performance, but the text does not specify what item, plan, or document is actually being referred to. Therefore, there is insufficient information to determine if the bidder has satisfied this requirement.
  - **expected evidence (true_verdicts.json):** "Our Risk Management Plan, covering risk identification, mitigation, and quality assurance procedures, is enclosed as Appendix C with this proposal."
  - **expected evidence (true_verdicts.json):** "We will finalize and submit our Risk Management Plan to the COR during the first month of performance, once site-specific risks have been assessed on the ground."
  - **expected reasoning:** Application states the Risk Management Plan 'is enclosed as Appendix C with this proposal,' but later separately states it 'will finalize and submit' the Risk Management Plan 'during the first month of performance' -- the two statements conflict on whether the plan was actually provided with the proposal.

**False-compliant rate** — dangerous direction: the true verdict requires an issue (anything but `compliant`), but every predicted verdict in the group is `compliant`.
- rate: 0.0%

- none

**False-issue rate** — mirror direction: the true verdict is `compliant` only, but the pipeline raised an issue anyway.
- rate: 0.0%

- none

**Unscored** — split/merge groups excluded from the matrix above (still counted in the two rates above):
- group 1:
  - true `sam_registration_proof` — "c. The offeror shall provide proof of SAM registration to include the SAM UEI number" (acceptable: ['contradictory'])
  - true `uei_eft_indicator_stated` — "(3) The Offeror’s Unique Entity Identifier (UEI) and, if applicable, Electronic Funds Transfer (EFT) indicator;" (acceptable: ['compliant', 'insufficient_information'])
  - predicted [11628b95] "As a minimum, offers shall include the Offeror's Unique Entity Identifier (UEI) and proof of SAM registration." — verdict: contradictory

## Evidence

**Citation-verified rate** (evidence-level): fraction of evidence quotes actually located in application.txt.
- rate: 88.2% (4 unverified of 34)

**Evidence recall**: does the expected evidence span (from `true_verdicts.json`) show up somewhere in the requirement's retrieved chunks, before the verdict step chose what to cite? Topics never extracted as a requirement are excluded — that failure is already counted by requirement recall above.
- recall: 100.0% (14/14)
- missed:
  - none
