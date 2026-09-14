# Evaluation report

## Summary metrics

Machine-readable numbers for averaging across tenders -- every value here is explained in the sections below. `null` means the metric doesn't apply to this run (e.g. no verdict-only artifact present).

```json
{
  "requirement_recall": 0.9118,
  "requirement_recall_matched": 31,
  "requirement_recall_total": 34,
  "requirement_precision": 0.8333,
  "citation_verified_rate": 1.0,
  "is_mandatory_accuracy": 1.0,
  "is_mandatory_scored": 30,
  "is_text_verifiable_accuracy": 0.9667,
  "is_text_verifiable_scored": 30,
  "verdict_clean_match_count": 28,
  "verdict_accuracy": 1.0,
  "false_compliant_rate": 0.0,
  "false_issue_rate": 0.0,
  "evidence_citation_verified_rate": 0.9524,
  "evidence_recall": 1.0,
  "verdict_only_accuracy": null,
  "verdict_only_scored": null
}
```

## Requirement recall

For each `true_requirements.json` topic, did the pipeline extract something whose tender.txt citation overlaps the true one? A pure text-offset check, not a judgment of meaning — see coverage flags below for extractions that are technically "found" but sloppy.

**Recall: 91.2% (31/34)**

**Missed** (3) — no overlapping predicted requirement at all. "chunk check" is a mechanical (no-LLM) re-chunking of the source document: whether this topic's matching text ever appeared whole in one chunk handed to the extraction model, or was split across chunks.
- true `amendment_acknowledgment` — "ACKNOWLEDGMENT OF AMENDMENTS: The offeror acknowledges receipt of amendments to the Solicitation numbered and dated as follows: AMENDMENT NO | DATE"
    - **chunk check:** [1122:1270] SPLIT across chunks [0, 1] -- the model may never have seen this requirement's full text in one call
- true `price_schedule_completion` — "0001 | | 1.00 | JB | __________________ | __________________ ... 0002 | | 80.00 | HR | __________________ | __________________ ... 0003 | | 1.00 | JB | __________________ | __________________ ... | | | | GRAND TOTAL | __________________"
    - **chunk check:** [1412:1473] whole, in chunk 1 -- the model saw this text intact; [1526:1588] whole, in chunk 1 -- the model saw this text intact; [1755:1816] whole, in chunk 1 -- the model saw this text intact; [2011:2055] whole, in chunk 1 -- the model saw this text intact
- true `submission_deadline` — "RFQ DUE 18 SEP 2026, 3 PM EST."
    - **chunk check:** [14218:14249] whole, in chunk 11 -- the model saw this text intact

**Over-split** (0) — one true topic extracted as several separate predicted requirements:
- none

**Over-merge** (1) — one predicted requirement covering several distinct true topics:
- predicted [f7b23cb8] "Provide documentation of previous performance and demonstrated experience on potable water tower inspection, cleaning, or repair contracts." — verdict: compliant lumps together 2 true requirements:
  - true `past_performance_water_tower_contracts` — "Provide documentation of previous performance on potable water tower inspection, cleaning, or repair contracts."
  - true `structural_water_tower_inspection_experience` — "Provide evidence of demonstrated experience in structural water tower inspections."

**Tangled** (0) — several true and several predicted requirements all overlapping at once:
- none

## Requirement precision

**Citation-verified rate** (hallucination check): fraction of predicted requirements whose citation was actually located in tender.txt (exactly or via fuzzy match).
- rate: 100.0%
- unverified:
  - none

**Classification precision**: fraction of predicted requirements that matched a true requirement.
- rate: 83.3%
- unexplained (6) — the model recognized these as requirements, but they don't match any true requirement. "closest true topic" is a mechanical (no-LLM) embedding-similarity lookup against every true topic's description; "dedup visibility" checks whether dedup's own cosine pre-filter would have clustered this candidate with whatever predicted requirement DID match that topic -- i.e. whether the dedup LLM call ever had a chance to compare them:
  - predicted [51b72b22] "Offerors may withdraw their offers by written notice to the Government received at any time before award."
    - **similarity check:** closest true topic: `offer_offeror_contact_info_stated` (cosine=0.60); vs matched predicted [4fd41bb3]: cosine=0.58 (< dedup threshold 0.6) -> dedup's cosine pre-filter would NOT have clustered these -- the dedup LLM call never saw them side by side
  - predicted [8895a236] "All Labor hours in Section 3.2 is exclusive of section 3.1 and shall be bid as a separate line item."
    - **similarity check:** closest true topic: `price_schedule_completion` (cosine=0.65); that true topic has no matched predicted requirement in this run, so there was nothing for dedup to compare it against
  - predicted [ab5e9935] "The offer shall include responses to provisions that require Offeror completion of information, representations, and certifications (other than those collected via SAM)."
    - **similarity check:** closest true topic: `sds_management_procedures` (cosine=0.68); vs matched predicted [c2f2557f]: cosine=0.54 (< dedup threshold 0.6) -> dedup's cosine pre-filter would NOT have clustered these -- the dedup LLM call never saw them side by side
  - predicted [c9b80c5b] "The offer shall include information necessary to evaluate the factors contained in the provision at 52.212-2 or as described in the solicitation."
    - **similarity check:** closest true topic: `offer_solicitation_number_stated` (cosine=0.70); vs matched predicted [98628627]: cosine=0.69 (>= dedup threshold 0.6) -> would likely have been clustered together and compared by the dedup LLM call
  - predicted [dbfe9e14] "All Material allowances in Section 3.3 are exclusive of section 3.1 and 3.2 and shall be bid as a separate line item."
    - **similarity check:** closest true topic: `price_schedule_completion` (cosine=0.60); that true topic has no matched predicted requirement in this run, so there was nothing for dedup to compare it against
  - predicted [fcad9d28] "The Offeror agrees to hold the prices in its offer firm for 60 calendar days from the date specified for receipt of offers, unless another time period is specified in an addendum to the solicitation."
    - **similarity check:** closest true topic: `offer_solicitation_number_stated` (cosine=0.67); vs matched predicted [98628627]: cosine=0.56 (< dedup threshold 0.6) -> dedup's cosine pre-filter would NOT have clustered these -- the dedup LLM call never saw them side by side

## Coverage flags

Clean 1:1 matches (recall counted them as found) whose citations don't fully overlap in length, split by which side is off. Over-split/over-merge/tangled matches are excluded here -- their predicted fragments are inherently partial by construction, already shown in the recall breakdown above.

**Requirements captured with extra text** (0) — the predicted citation is padded beyond the true one:
- none

**Requirements captured incompletely** (1) — the predicted citation misses part of the true one:
- predicted [244e2384] is contained in true `sdvosb_setaside_eligibility` — 53.2%:
    predicted: "The offeror must qualify as a small business under the assigned NAICS code and be a certified SDVOSB listed in the SBA certification database at the time of offer submission and award."
    true: "Pursuant to 38 U.S.C. 8127(e), only certified SDVOSBs listed in the SBA certification database are considered eligible to receive award of a resulting contract. By submitting an offer, the prospective contractor represents that it is an eligible and certified SDVOSB as defined in this clause, 13 CFR 121, 125, and 128, and VAAR subpart 819.70."

## is_mandatory accuracy

For each clean or one-to-many match (tangled groups excluded — there's no single "one" to compare against), does `is_mandatory` agree with the true value? A one-to-many group counts as correct only if every member on the "many" side agrees with the "one".

**Accuracy: 100.0% (30 groups)**

Mismatched:
- none

## is_text_verifiable accuracy

For each clean or one-to-many match (tangled groups excluded), does `is_text_verifiable` agree with the true value (all-or-nothing on the "many" side, same rule as is_mandatory above)? A wrong `false` here means the pipeline skips verdict generation for a requirement that should get one.

**Accuracy: 96.7% (30 groups)**

Mismatched:
- true: `sdvosb_setaside_eligibility`=False; predicted: `244e2384`=True — "Pursuant to 38 U.S.C. 8127(e), only certified SDVOSBs listed in the SBA certification database are considered eligible to receive award of a resulting contract. By submitting an offer, the prospective contractor represents that it is an eligible and certified SDVOSB as defined in this clause, 13 CFR 121, 125, and 128, and VAAR subpart 819.70."

## Verdict accuracy

The confusion matrix covers only clean 1:1 matches — split/merge groups have no single pair to plot, but still count in the two rates below.

Clean matches scored: 28

| true \ pipeline said | `compliant` | `non_compliant` | `contradictory` | `insufficient_information` |
|---|---|---|---|---|
| `compliant` | 18 | 0 | 0 | 0 |
| `non_compliant` | 0 | 4 | 0 | 0 |
| `contradictory` | 0 | 2 | 0 | 0 |
| `insufficient_information` | 1 | 3 | 0 | 0 |

**Mismatched clean matches** — every off-diagonal cell above, in full: the full context retrieved and shown to the model, what it chose to cite from that context, and its reasoning ("model's ..."), next to what `true_verdicts.json` expects ("expected ...").

- none

**False-compliant rate** — dangerous direction: the true verdict requires an issue (anything but `compliant`), but every predicted verdict in the group is `compliant`.
- rate: 0.0%

- none

**False-issue rate** — mirror direction: the true verdict is `compliant` only, but the pipeline raised an issue anyway.
- rate: 0.0%

- none

**Unscored** — split/merge groups excluded from the matrix above (still counted in the two rates above):
- group 1:
  - true `past_performance_water_tower_contracts` — "Provide documentation of previous performance on potable water tower inspection, cleaning, or repair contracts." (acceptable: ['compliant'])
  - true `structural_water_tower_inspection_experience` — "Provide evidence of demonstrated experience in structural water tower inspections." (acceptable: ['compliant'])
  - predicted [f7b23cb8] "Provide documentation of previous performance and demonstrated experience on potable water tower inspection, cleaning, or repair contracts." — verdict: compliant

## Evidence

**Citation-verified rate** (evidence-level): fraction of evidence quotes actually located in application.txt.
- rate: 95.2% (2 unverified of 42)

**Evidence recall**: does the expected evidence span (from `true_verdicts.json`) show up somewhere in the requirement's retrieved chunks, before the verdict step chose what to cite? Topics never extracted as a requirement are excluded — that failure is already counted by requirement recall above.
- recall: 100.0% (29/29)
- missed:
  - none
