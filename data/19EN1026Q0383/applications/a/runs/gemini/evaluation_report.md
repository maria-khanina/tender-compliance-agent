# Evaluation report

## Summary metrics

Machine-readable numbers for averaging across tenders -- every value here is explained in the sections below. `null` means the metric doesn't apply to this run (e.g. no verdict-only artifact present).

```json
{
  "requirement_recall": 0.9375,
  "requirement_recall_matched": 15,
  "requirement_recall_total": 16,
  "requirement_precision": 0.3548,
  "citation_verified_rate": 1.0,
  "is_mandatory_accuracy": 0.9091,
  "is_mandatory_scored": 11,
  "is_text_verifiable_accuracy": 1.0,
  "is_text_verifiable_scored": 11,
  "verdict_clean_match_count": 9,
  "verdict_accuracy": 0.7778,
  "false_compliant_rate": 0.1,
  "false_issue_rate": 0.0,
  "evidence_citation_verified_rate": 1.0,
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
- predicted [5d267269] "As a minimum, offers shall include the solicitation number, offeror contact details, UEI, evaluation information, completed representations/certifications, agreement statement, and completed SF-1449 cover page and Section 1." — verdict: compliant lumps together 5 true requirements:
  - true `offeror_contact_info_stated` — "(2) The name, address, telephone number of the Offeror;"
  - true `sf1449_section1_completion` — "1. A completed solicitation, in which the SF-1449 cover page (blocks 12, 17, 19-24, and 30 as appropriate), and Section 1 has been filled out."
  - true `solicitation_number_stated` — "(1) The solicitation number;"
  - true `statement_of_agreement_with_terms` — "(6) A statement specifying the extent of agreement with all terms, conditions, and provisions included in the solicitation and any solicitation amendments."
  - true `uei_eft_indicator_stated` — "(3) The Offeror’s Unique Entity Identifier (UEI) and, if applicable, Electronic Funds Transfer (EFT) indicator;"

**Tangled** (0) — several true and several predicted requirements all overlapping at once:
- none

## Requirement precision

**Citation-verified rate** (hallucination check): fraction of predicted requirements whose citation was actually located in tender.txt (exactly or via fuzzy match).
- rate: 100.0%
- unverified:
  - none

**Classification precision**: fraction of predicted requirements that matched a true requirement.
- rate: 35.5%
- unexplained (20) — the model recognized these as requirements, but they don't match any true requirement. "closest true topic" is a mechanical (no-LLM) embedding-similarity lookup against every true topic's description; "dedup visibility" checks whether dedup's own cosine pre-filter would have clustered this candidate with whatever predicted requirement DID match that topic -- i.e. whether the dedup LLM call ever had a chance to compare them:
  - predicted [09085a8b] "Contractor employees shall be on site only for contractual duties and not for other business purposes."
    - **similarity check:** closest true topic: `solicitation_number_stated` (cosine=0.49); vs matched predicted [5d267269]: cosine=0.40 (< dedup threshold 0.6) -> dedup's cosine pre-filter would NOT have clustered these -- the dedup LLM call never saw them side by side
  - predicted [146cd98a] "Incomplete proposals will not be accepted."
    - **similarity check:** closest true topic: `solicitation_number_stated` (cosine=0.62); vs matched predicted [5d267269]: cosine=0.58 (< dedup threshold 0.6) -> dedup's cosine pre-filter would NOT have clustered these -- the dedup LLM call never saw them side by side
  - predicted [1bdca98a] "Contractor shall schedule cooking and delivery requirements to ensure that these are done in the order and time frame specified, taking into consideration staff hours and security personnel."
    - **similarity check:** closest true topic: `signed_dated_offer_submission` (cosine=0.61); vs matched predicted [f732039f]: cosine=0.54 (< dedup threshold 0.6) -> dedup's cosine pre-filter would NOT have clustered these -- the dedup LLM call never saw them side by side
  - predicted [2271ec16] "Proposals must be in English"
    - **similarity check:** closest true topic: `solicitation_number_stated` (cosine=0.66); vs matched predicted [5d267269]: cosine=0.58 (< dedup threshold 0.6) -> dedup's cosine pre-filter would NOT have clustered these -- the dedup LLM call never saw them side by side
  - predicted [2680130f] "Contractor will utilize its own facilities for the preparation, provide individually packed meals of food and deliver them to the residence."
    - **similarity check:** closest true topic: `capability_evidence_personnel_equipment_financial` (cosine=0.55); vs matched predicted [4021f4f7]: cosine=0.51 (< dedup threshold 0.6) -> dedup's cosine pre-filter would NOT have clustered these -- the dedup LLM call never saw them side by side
  - predicted [317cdec4] "The Contractor shall perform surprise inspection visits to the work site on a regular basis and coordinate these visits with the COR."
    - **similarity check:** closest true topic: `capability_evidence_personnel_equipment_financial` (cosine=0.57); vs matched predicted [4021f4f7]: cosine=0.55 (< dedup threshold 0.6) -> dedup's cosine pre-filter would NOT have clustered these -- the dedup LLM call never saw them side by side
  - predicted [39061e79] "Be otherwise qualified and eligible to receive an award under applicable laws and regulations."
    - **similarity check:** closest true topic: `local_license_permit_conditional` (cosine=0.62); vs matched predicted [9f24c602]: cosine=0.64 (>= dedup threshold 0.6) -> would likely have been clustered together and compared by the dedup LLM call
  - predicted [391c1df6] "The Contractor shall be responsible for quality control."
    - **similarity check:** closest true topic: `capability_evidence_personnel_equipment_financial` (cosine=0.60); vs matched predicted [4021f4f7]: cosine=0.58 (< dedup threshold 0.6) -> dedup's cosine pre-filter would NOT have clustered these -- the dedup LLM call never saw them side by side
  - predicted [5032c98b] "The Contractor shall furnish all managerial, administrative, and direct labor personnel that are necessary to accomplish the work in this contract."
    - **similarity check:** closest true topic: `capability_evidence_personnel_equipment_financial` (cosine=0.60); vs matched predicted [4021f4f7]: cosine=0.57 (< dedup threshold 0.6) -> dedup's cosine pre-filter would NOT have clustered these -- the dedup LLM call never saw them side by side
  - predicted [52e640d6] "Ability to comply with the required performance period, taking into consideration existing business commitments."
    - **similarity check:** closest true topic: `past_performance_references` (cosine=0.61); vs matched predicted [2da1c6ac]: cosine=0.54 (< dedup threshold 0.6) -> dedup's cosine pre-filter would NOT have clustered these -- the dedup LLM call never saw them side by side
  - predicted [55431190] "The Contractor shall provide a supervisor who understands written and spoken English to act as the focal point and point of contact with U.S. Government personnel."
    - **similarity check:** closest true topic: `project_manager_english_liaison` (cosine=0.69); vs matched predicted [a3c32a93]: cosine=0.71 (>= dedup threshold 0.6) -> would likely have been clustered together and compared by the dedup LLM call
  - predicted [55619b15] "Necessary organization, experience, and skills or the ability to obtain them."
    - **similarity check:** closest true topic: `capability_evidence_personnel_equipment_financial` (cosine=0.63); vs matched predicted [4021f4f7]: cosine=0.67 (>= dedup threshold 0.6) -> would likely have been clustered together and compared by the dedup LLM call
  - predicted [66a8fcc2] "The schedules shall take into consideration the hours that the staff can effectively perform their services without placing a burden on the security personnel of the Post."
    - **similarity check:** closest true topic: `capability_evidence_personnel_equipment_financial` (cosine=0.44); vs matched predicted [4021f4f7]: cosine=0.42 (< dedup threshold 0.6) -> dedup's cosine pre-filter would NOT have clustered these -- the dedup LLM call never saw them side by side
  - predicted [9472f3e9] "Contractor will be responsible for providing individually packed lunch and dinner meals daily for seven people (98 meals per week)."
    - **similarity check:** closest true topic: `menu_plan_sample_20day` (cosine=0.52); vs matched predicted [11dcd5b3]: cosine=0.60 (< dedup threshold 0.6) -> dedup's cosine pre-filter would NOT have clustered these -- the dedup LLM call never saw them side by side
  - predicted [cafd1ce8] "Contractor will be responsible for removing used food containers and any uneaten meals from the residence/MSGR and disposing of them at contractor facilities during meal deliveries."
    - **similarity check:** closest true topic: `risk_management_plan_with_proposal` (cosine=0.50); vs matched predicted [b40344d2]: cosine=0.54 (< dedup threshold 0.6) -> dedup's cosine pre-filter would NOT have clustered these -- the dedup LLM call never saw them side by side
  - predicted [d04dd84f] "Satisfactory record of integrity and business ethics."
    - **similarity check:** closest true topic: `past_performance_references` (cosine=0.62); vs matched predicted [2da1c6ac]: cosine=0.57 (< dedup threshold 0.6) -> dedup's cosine pre-filter would NOT have clustered these -- the dedup LLM call never saw them side by side
  - predicted [d0680587] "The Contractor shall prepare general instructions for the work force and provide drafts to the COR for review within thirty days after contract award."
    - **similarity check:** closest true topic: `signed_dated_offer_submission` (cosine=0.64); vs matched predicted [f732039f]: cosine=0.60 (>= dedup threshold 0.6) -> would likely have been clustered together and compared by the dedup LLM call
  - predicted [d7ac0328] "If the offeror has not performed comparable services in Estonia, then the offeror shall provide its international experience."
    - **similarity check:** closest true topic: `past_performance_references` (cosine=0.73); vs matched predicted [2da1c6ac]: cosine=0.48 (< dedup threshold 0.6) -> dedup's cosine pre-filter would NOT have clustered these -- the dedup LLM call never saw them side by side
  - predicted [dcbc7b98] "Contractor may use its own discretion on when to transport meals (with delivery three times a week and encouragement to transport multiple days' meals per trip) to ensure daily availability."
    - **similarity check:** closest true topic: `past_performance_references` (cosine=0.59); vs matched predicted [2da1c6ac]: cosine=0.48 (< dedup threshold 0.6) -> dedup's cosine pre-filter would NOT have clustered these -- the dedup LLM call never saw them side by side
  - predicted [f35f4c7f] "All food is to be delivered to the MSGR at Toom-Kuninga 20A, Tallinn."
    - **similarity check:** closest true topic: `menu_plan_sample_20day` (cosine=0.55); vs matched predicted [11dcd5b3]: cosine=0.59 (< dedup threshold 0.6) -> dedup's cosine pre-filter would NOT have clustered these -- the dedup LLM call never saw them side by side

## Coverage flags

Clean 1:1 matches (recall counted them as found) whose citations don't fully overlap in length, split by which side is off. Over-split/over-merge/tangled matches are excluded here -- their predicted fragments are inherently partial by construction, already shown in the recall breakdown above.

**Requirements captured with extra text** (1) — the predicted citation is padded beyond the true one:
- true `signed_dated_offer_submission` is contained in predicted [f732039f] — 22.2%:
    predicted: "Submit signed and dated offers to the office specified in this solicitation at or before the exact time specified."
    true: "Submit signed and dated offers"

**Requirements captured incompletely** (2) — the predicted citation misses part of the true one:
- predicted [b40344d2] is contained in true `risk_management_plan_with_proposal` — 46.4%:
    predicted: "Provide items as part of proposal response and updated/maintained throughout performance."
    true: "Risk Management Plan (Risk management and mitigation-quality control & assurance, etc.) 1 COR Provide as part of proposal response and updated/maintained throughout performance"

- predicted [96505bb4] is contained in true `submission_format_and_channel` — 38.9%:
    predicted: "file size must not exceed 30MB per email (split into separate emails if larger)"
    true: "submitted electronically to TallinnGSOProcurement@state.gov in MS-Word 2007/2010, MS-Excel 2007/2010, or Adobe PDF format; file size must not exceed 30MB per email (split into separate emails if larger)."

## is_mandatory accuracy

For each clean or one-to-many match (tangled groups excluded — there's no single "one" to compare against), does `is_mandatory` agree with the true value? A one-to-many group counts as correct only if every member on the "many" side agrees with the "one".

**Accuracy: 90.9% (11 groups)**

Mismatched:
- true: `local_license_permit_conditional`=False; predicted: `9f24c602`=True — "5. If providing this service requires special license or permit, then the offeror shall address its plan to obtain all licenses and permits required by local law. If offeror already possesses the locally required licenses and permits, a copy shall be provided."

## is_text_verifiable accuracy

For each clean or one-to-many match (tangled groups excluded), does `is_text_verifiable` agree with the true value (all-or-nothing on the "many" side, same rule as is_mandatory above)? A wrong `false` here means the pipeline skips verdict generation for a requirement that should get one.

**Accuracy: 100.0% (11 groups)**

Mismatched:
- none

## Verdict accuracy

The confusion matrix covers only clean 1:1 matches — split/merge groups have no single pair to plot, but still count in the two rates below.

Clean matches scored: 9

| true \ pipeline said | `compliant` | `non_compliant` | `contradictory` | `insufficient_information` |
|---|---|---|---|---|
| `compliant` | 4 | 0 | 0 | 0 |
| `non_compliant` | 1 | 1 | 0 | 1 |
| `contradictory` | 1 | 0 | 0 | 0 |
| `insufficient_information` | 0 | 1 | 0 | 0 |

**Mismatched clean matches** — every off-diagonal cell above, in full: the full context retrieved and shown to the model, what it chose to cite from that context, and its reasoning ("model's ..."), next to what `true_verdicts.json` expects ("expected ...").

- `local_license_permit_conditional` — acceptable: ['contradictory'], predicted: compliant
  - **requirement:** "The offeror shall address its plan to obtain all licenses and permits required by local law, or provide a copy if already possessed."
  - **retrieved context (shown to the model):** "Capability: Baltic Table Catering OÜ has 14 full-time kitchen and delivery staff, two delivery vehicles, and audited annual financial statements. A link to our most recent annual report is provided: https://balticatering.ee/reports/2025-annual-report.pdf Licenses and Permits: Bal [...truncated]"
  - **retrieved context (shown to the model):** "Baltic Table Catering OÜ Sepapaja 6, 15551 Tallinn, Estonia RE: Solicitation 19EN1026Q0383 -- Commercial Cook Services, Marine Security Guard Residence, U.S. Embassy Tallinn Baltic Table Catering OÜ hereby submits the following quotation in response to Solicitation 19EN1026Q0383, [...truncated]"
  - **model's evidence (what it chose to cite):** "Licenses and Permits: Baltic Table Catering OÜ already holds all locally required food handling and health inspection permits for its kitchen facility; a copy of our current Health Board (Terviseamet) permit is enclosed with this quotation."
  - **model's reasoning:** The requirement states that the offeror shall address its plan to obtain all licenses and permits required by local law, or provide a copy if already possessed. The bidder explicitly states that it already holds all locally required permits and has enclosed a copy of its current Health Board permit, thus satisfying the requirement.
  - **expected evidence (true_verdicts.json):** "Licenses and Permits: Baltic Table Catering OÜ already holds all locally required food handling and health inspection permits for its kitchen facility; a copy of our current Health Board (Terviseamet) permit is enclosed with this quotation."
  - **expected evidence (true_verdicts.json):** "Our current Health Board permit covers general food handling; we have separately submitted an application for the specific health inspection permit required for embassy-adjacent delivery routes, which is still pending review as of this quotation."
  - **expected reasoning:** Application first states it already holds all locally required food handling and health inspection permits with a copy enclosed, but later admits a specific required health inspection permit is still pending review -- the two statements directly conflict on whether the required permits are actually in hand.

- `risk_management_plan_with_proposal` — acceptable: ['non_compliant'], predicted: insufficient_information
  - **requirement:** "Provide items as part of proposal response and updated/maintained throughout performance."
  - **retrieved context (shown to the model):** "Capability: Baltic Table Catering OÜ has 14 full-time kitchen and delivery staff, two delivery vehicles, and audited annual financial statements. A link to our most recent annual report is provided: https://balticatering.ee/reports/2025-annual-report.pdf Licenses and Permits: Bal [...truncated]"
  - **retrieved context (shown to the model):** "Baltic Table Catering OÜ Sepapaja 6, 15551 Tallinn, Estonia RE: Solicitation 19EN1026Q0383 -- Commercial Cook Services, Marine Security Guard Residence, U.S. Embassy Tallinn Baltic Table Catering OÜ hereby submits the following quotation in response to Solicitation 19EN1026Q0383, [...truncated]"
  - **model's evidence (what it chose to cite):** none
  - **model's reasoning:** The excerpts describe the bidder's capabilities, licenses, past performance, risk management, and administrative information, but they do not mention whether the bidder has provided the specific items as part of the proposal response or how those items will be updated and maintained throughout performance as required by the solicitation.
  - **expected evidence (true_verdicts.json):** "A detailed Risk Management Plan covering risk identification, mitigation strategies, and our quality control and assurance procedures will be finalized and provided to the COR shortly after contract award, once the transition schedule is confirmed."
  - **expected reasoning:** Application explicitly defers the Risk Management Plan to shortly after contract award, rather than providing it as part of the proposal response as required.

**False-compliant rate** — dangerous direction: the true verdict requires an issue (anything but `compliant`), but every predicted verdict in the group is `compliant`.
- rate: 10.0%

- `local_license_permit_conditional` — acceptable: ['contradictory'], predicted: compliant
  - **requirement:** "The offeror shall address its plan to obtain all licenses and permits required by local law, or provide a copy if already possessed."
  - **retrieved context (shown to the model):** "Capability: Baltic Table Catering OÜ has 14 full-time kitchen and delivery staff, two delivery vehicles, and audited annual financial statements. A link to our most recent annual report is provided: https://balticatering.ee/reports/2025-annual-report.pdf Licenses and Permits: Bal [...truncated]"
  - **retrieved context (shown to the model):** "Baltic Table Catering OÜ Sepapaja 6, 15551 Tallinn, Estonia RE: Solicitation 19EN1026Q0383 -- Commercial Cook Services, Marine Security Guard Residence, U.S. Embassy Tallinn Baltic Table Catering OÜ hereby submits the following quotation in response to Solicitation 19EN1026Q0383, [...truncated]"
  - **model's evidence (what it chose to cite):** "Licenses and Permits: Baltic Table Catering OÜ already holds all locally required food handling and health inspection permits for its kitchen facility; a copy of our current Health Board (Terviseamet) permit is enclosed with this quotation."
  - **model's reasoning:** The requirement states that the offeror shall address its plan to obtain all licenses and permits required by local law, or provide a copy if already possessed. The bidder explicitly states that it already holds all locally required permits and has enclosed a copy of its current Health Board permit, thus satisfying the requirement.
  - **expected evidence (true_verdicts.json):** "Licenses and Permits: Baltic Table Catering OÜ already holds all locally required food handling and health inspection permits for its kitchen facility; a copy of our current Health Board (Terviseamet) permit is enclosed with this quotation."
  - **expected evidence (true_verdicts.json):** "Our current Health Board permit covers general food handling; we have separately submitted an application for the specific health inspection permit required for embassy-adjacent delivery routes, which is still pending review as of this quotation."
  - **expected reasoning:** Application first states it already holds all locally required food handling and health inspection permits with a copy enclosed, but later admits a specific required health inspection permit is still pending review -- the two statements directly conflict on whether the required permits are actually in hand.

**False-issue rate** — mirror direction: the true verdict is `compliant` only, but the pipeline raised an issue anyway.
- rate: 0.0%

- none

**Unscored** — split/merge groups excluded from the matrix above (still counted in the two rates above):
- group 1:
  - true `offeror_contact_info_stated` — "(2) The name, address, telephone number of the Offeror;" (acceptable: ['compliant'])
  - true `sf1449_section1_completion` — "1. A completed solicitation, in which the SF-1449 cover page (blocks 12, 17, 19-24, and 30 as appropriate), and Section 1 has been filled out." (acceptable: ['compliant'])
  - true `solicitation_number_stated` — "(1) The solicitation number;" (acceptable: ['compliant'])
  - true `statement_of_agreement_with_terms` — "(6) A statement specifying the extent of agreement with all terms, conditions, and provisions included in the solicitation and any solicitation amendments." (acceptable: ['compliant'])
  - true `uei_eft_indicator_stated` — "(3) The Offeror’s Unique Entity Identifier (UEI) and, if applicable, Electronic Funds Transfer (EFT) indicator;" (acceptable: ['compliant', 'insufficient_information'])
  - predicted [5d267269] "As a minimum, offers shall include the solicitation number, offeror contact details, UEI, evaluation information, completed representations/certifications, agreement statement, and completed SF-1449 cover page and Section 1." — verdict: compliant

## Evidence

**Citation-verified rate** (evidence-level): fraction of evidence quotes actually located in application.txt.
- rate: 100.0% (0 unverified of 28)

**Evidence recall**: does the expected evidence span (from `true_verdicts.json`) show up somewhere in the requirement's retrieved chunks, before the verdict step chose what to cite? Topics never extracted as a requirement are excluded — that failure is already counted by requirement recall above.
- recall: 100.0% (12/12)
- missed:
  - none
