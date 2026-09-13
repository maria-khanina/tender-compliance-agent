# Evaluation report

## Summary metrics

Machine-readable numbers for averaging across tenders -- every value here is explained in the sections below. `null` means the metric doesn't apply to this run (e.g. no verdict-only artifact present).

```json
{
  "requirement_recall": 0.9118,
  "requirement_recall_matched": 31,
  "requirement_recall_total": 34,
  "requirement_precision": 0.8378,
  "citation_verified_rate": 1.0,
  "is_mandatory_accuracy": 1.0,
  "is_mandatory_scored": 31,
  "is_text_verifiable_accuracy": 0.9677,
  "is_text_verifiable_scored": 31,
  "verdict_clean_match_count": 30,
  "verdict_accuracy": 0.8,
  "false_compliant_rate": 0.1667,
  "false_issue_rate": 0.0,
  "evidence_citation_verified_rate": 1.0,
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

**Over-merge** (0) — one predicted requirement covering several distinct true topics:
- none

**Tangled** (0) — several true and several predicted requirements all overlapping at once:
- none

## Requirement precision

**Citation-verified rate** (hallucination check): fraction of predicted requirements whose citation was actually located in tender.txt (exactly or via fuzzy match).
- rate: 100.0%
- unverified:
  - none

**Classification precision**: fraction of predicted requirements that matched a true requirement.
- rate: 83.8%
- unexplained (6) — the model recognized these as requirements, but they don't match any true requirement. "closest true topic" is a mechanical (no-LLM) embedding-similarity lookup against every true topic's description; "dedup visibility" checks whether dedup's own cosine pre-filter would have clustered this candidate with whatever predicted requirement DID match that topic -- i.e. whether the dedup LLM call ever had a chance to compare them:
  - predicted [333ce859] "The Offeror agrees to hold the prices in its offer firm for 60 calendar days from the date specified for receipt of offers, unless another time period is specified in an addendum to the solicitation."
    - **similarity check:** closest true topic: `offer_solicitation_number_stated` (cosine=0.67); vs matched predicted [fccabca2]: cosine=0.57 (< dedup threshold 0.6) -> dedup's cosine pre-filter would NOT have clustered these -- the dedup LLM call never saw them side by side
  - predicted [4972e12c] "All Labor hours in Section 3.2 is exclusive of section 3.1 and shall be bid as a separate line item."
    - **similarity check:** closest true topic: `price_schedule_completion` (cosine=0.65); that true topic has no matched predicted requirement in this run, so there was nothing for dedup to compare it against
  - predicted [5176715a] "All Material allowances in Section 3.3 are exclusive of section 3.1 and 3.2 and shall be bid as a separate line item."
    - **similarity check:** closest true topic: `price_schedule_completion` (cosine=0.60); that true topic has no matched predicted requirement in this run, so there was nothing for dedup to compare it against
  - predicted [63322b1f] "As a minimum, offers shall include responses to provisions that require Offeror completion of information, representations, and certifications (other than those collected via the System for Award Management (SAM))."
    - **similarity check:** closest true topic: `past_performance_quality_records` (cosine=0.66); vs matched predicted [fd2f3822]: cosine=0.57 (< dedup threshold 0.6) -> dedup's cosine pre-filter would NOT have clustered these -- the dedup LLM call never saw them side by side
  - predicted [a1d44066] "Offerors may withdraw their offers by written notice to the Government received at any time before award."
    - **similarity check:** closest true topic: `offer_offeror_contact_info_stated` (cosine=0.60); vs matched predicted [6a8fa94c]: cosine=0.57 (< dedup threshold 0.6) -> dedup's cosine pre-filter would NOT have clustered these -- the dedup LLM call never saw them side by side
  - predicted [dcdc1834] "As a minimum, offers shall include information necessary to evaluate the factors contained in the provision at 52.212-2 or as described in the solicitation."
    - **similarity check:** closest true topic: `offer_solicitation_number_stated` (cosine=0.68); vs matched predicted [fccabca2]: cosine=0.66 (>= dedup threshold 0.6) -> would likely have been clustered together and compared by the dedup LLM call

## Coverage flags

Clean 1:1 matches (recall counted them as found) whose citations don't fully overlap in length, split by which side is off. Over-split/over-merge/tangled matches are excluded here -- their predicted fragments are inherently partial by construction, already shown in the recall breakdown above.

**Requirements captured with extra text** (0) — the predicted citation is padded beyond the true one:
- none

**Requirements captured incompletely** (1) — the predicted citation misses part of the true one:
- predicted [2ba9c5b3] is contained in true `sdvosb_setaside_eligibility` — 53.2%:
    predicted: "The offeror must qualify as a small business concern under the corresponding NAICS code size standard and be a certified SDVOSB listed in the SBA certification database at the time of offer submission and at the time of award, and represent this eligibility upon submission."
    true: "Pursuant to 38 U.S.C. 8127(e), only certified SDVOSBs listed in the SBA certification database are considered eligible to receive award of a resulting contract. By submitting an offer, the prospective contractor represents that it is an eligible and certified SDVOSB as defined in this clause, 13 CFR 121, 125, and 128, and VAAR subpart 819.70."

## is_mandatory accuracy

For each clean or one-to-many match (tangled groups excluded — there's no single "one" to compare against), does `is_mandatory` agree with the true value? A one-to-many group counts as correct only if every member on the "many" side agrees with the "one".

**Accuracy: 100.0% (31 groups)**

Mismatched:
- none

## is_text_verifiable accuracy

For each clean or one-to-many match (tangled groups excluded), does `is_text_verifiable` agree with the true value (all-or-nothing on the "many" side, same rule as is_mandatory above)? A wrong `false` here means the pipeline skips verdict generation for a requirement that should get one.

**Accuracy: 96.8% (31 groups)**

Mismatched:
- true: `sdvosb_setaside_eligibility`=False; predicted: `2ba9c5b3`=True — "Pursuant to 38 U.S.C. 8127(e), only certified SDVOSBs listed in the SBA certification database are considered eligible to receive award of a resulting contract. By submitting an offer, the prospective contractor represents that it is an eligible and certified SDVOSB as defined in this clause, 13 CFR 121, 125, and 128, and VAAR subpart 819.70."

## Verdict accuracy

The confusion matrix covers only clean 1:1 matches — split/merge groups have no single pair to plot, but still count in the two rates below.

Clean matches scored: 30

| true \ pipeline said | `compliant` | `non_compliant` | `contradictory` | `insufficient_information` |
|---|---|---|---|---|
| `compliant` | 7 | 0 | 0 | 2 |
| `non_compliant` | 1 | 4 | 0 | 0 |
| `contradictory` | 0 | 0 | 1 | 0 |
| `insufficient_information` | 4 | 10 | 0 | 1 |

**Mismatched clean matches** — every off-diagonal cell above, in full: the full context retrieved and shown to the model, what it chose to cite from that context, and its reasoning ("model's ..."), next to what `true_verdicts.json` expects ("expected ...").

- `technical_standards_compliance_documentation` — acceptable: ['non_compliant', 'insufficient_information'], predicted: compliant
  - **requirement:** "Provide documentation demonstrating understanding and application of all relevant AWWA, NHDES, OSHA, and EPA requirements."
  - **retrieved context (shown to the model):** "Past Performance: Granite State Tank Works has performed water tower inspection and cleaning contracts for three New Hampshire municipal water districts over the past four years, including one hospital campus water system. Attached are two CPARS entries from the past 3 years. Key [...truncated]"
  - **retrieved context (shown to the model):** "From: proposals@granitestatetankworks.com To: contractingofficer@va.gov Subject: Quote for RFQ 36C24126Q0704 - Water Tower Inspection & Maintenance Solicitation Number: 36C24126Q0704 Granite State Tank Works, LLC 118 Industrial Drive Nashua, NH 03060 (603) 555-0148 Unique Entity [...truncated]"
  - **model's evidence (what it chose to cite):** "Our lead technician, James Boudreau, holds current OSHA-10 and OSHA-30 certifications and a valid New Hampshire Water System Operator License."
  - **model's evidence (what it chose to cite):** "Granite State Tank Works has reviewed the AWWA C652, D101, D102, and M42 standards along with NHDES administrative rules and will perform all work in accordance with these requirements."
  - **model's reasoning:** The bidder provides documentation demonstrating understanding and application of AWWA, NHDES, OSHA, and EPA requirements by specifically citing relevant AWWA standards, NHDES administrative rules, OSHA certifications, and SDS management procedures for chemicals.
  - **expected evidence (true_verdicts.json):** "Granite State Tank Works has reviewed the AWWA C652, D101, D102, and M42 standards along with NHDES administrative rules and will perform all work in accordance with these requirements."
  - **expected reasoning:** Application names specific AWWA standards and NHDES rules, but never mentions OSHA or EPA requirements at all -- two of the four named regulatory frameworks are entirely unaddressed.

- `inspection_cleaning_methodology` — acceptable: ['insufficient_information', 'non_compliant'], predicted: compliant
  - **requirement:** "Provide a detailed inspection and cleaning methodology, including procedures, equipment, and verification steps."
  - **retrieved context (shown to the model):** "Past Performance: Granite State Tank Works has performed water tower inspection and cleaning contracts for three New Hampshire municipal water districts over the past four years, including one hospital campus water system. Attached are two CPARS entries from the past 3 years. Key [...truncated]"
  - **retrieved context (shown to the model):** "From: proposals@granitestatetankworks.com To: contractingofficer@va.gov Subject: Quote for RFQ 36C24126Q0704 - Water Tower Inspection & Maintenance Solicitation Number: 36C24126Q0704 Granite State Tank Works, LLC 118 Industrial Drive Nashua, NH 03060 (603) 555-0148 Unique Entity [...truncated]"
  - **model's evidence (what it chose to cite):** "Our inspection and cleaning methodology includes tank draining coordination with Facility Services, interior/exterior visual inspection, sediment removal, and a written verification checklist at each stage."
  - **model's reasoning:** The bidder provides an overview of their inspection and cleaning methodology, detailing the specific procedures (tank draining coordination, interior/exterior visual inspection, sediment removal) and verification steps (written verification checklist at each stage), thereby satisfying the requirement.
  - **expected evidence (true_verdicts.json):** "Our inspection and cleaning methodology includes tank draining coordination with Facility Services, interior/exterior visual inspection, sediment removal, and a written verification checklist at each stage."
  - **expected reasoning:** Application describes procedures (draining coordination, visual inspection, sediment removal) and a verification checklist, but never mentions equipment.

- `work_plans_operational_procedures` — acceptable: ['insufficient_information', 'non_compliant'], predicted: compliant
  - **requirement:** "Provide complete, technically sound work plans and operational procedures for reviewer evaluation."
  - **retrieved context (shown to the model):** "Past Performance: Granite State Tank Works has performed water tower inspection and cleaning contracts for three New Hampshire municipal water districts over the past four years, including one hospital campus water system. Attached are two CPARS entries from the past 3 years. Key [...truncated]"
  - **retrieved context (shown to the model):** "From: proposals@granitestatetankworks.com To: contractingofficer@va.gov Subject: Quote for RFQ 36C24126Q0704 - Water Tower Inspection & Maintenance Solicitation Number: 36C24126Q0704 Granite State Tank Works, LLC 118 Industrial Drive Nashua, NH 03060 (603) 555-0148 Unique Entity [...truncated]"
  - **model's evidence (what it chose to cite):** "Our inspection and cleaning methodology includes tank draining coordination with Facility Services, interior/exterior visual inspection, sediment removal, and a written verification checklist at each stage."
  - **model's evidence (what it chose to cite):** "Granite State Tank Works will submit a site-specific Confined Space Entry plan and Lockout/Tagout procedures prior to mobilization. A fall protection plan is available and will be finalized in coordination with the COR once the work schedule is confirmed."
  - **model's reasoning:** The bidder provides a clear overview of their technical approach and methodology for the inspection and cleaning process, along with plans for submitting site-specific operational procedures such as confined space entry plans and lockout/tagout procedures prior to mobilization. This satisfies the requirement to provide work plans and operational procedures for evaluation.
  - **expected evidence (true_verdicts.json):** none
  - **expected reasoning:** Application never provides a distinct work plan or operational procedures document beyond the general technical-approach narrative.

- `nh_water_operator_license_copy` — acceptable: ['insufficient_information', 'compliant'], predicted: non_compliant
  - **requirement:** "Provide a copy of the NH Water System Operator License (certified Water Works Operator)."
  - **retrieved context (shown to the model):** "Past Performance: Granite State Tank Works has performed water tower inspection and cleaning contracts for three New Hampshire municipal water districts over the past four years, including one hospital campus water system. Attached are two CPARS entries from the past 3 years. Key [...truncated]"
  - **retrieved context (shown to the model):** "From: proposals@granitestatetankworks.com To: contractingofficer@va.gov Subject: Quote for RFQ 36C24126Q0704 - Water Tower Inspection & Maintenance Solicitation Number: 36C24126Q0704 Granite State Tank Works, LLC 118 Industrial Drive Nashua, NH 03060 (603) 555-0148 Unique Entity [...truncated]"
  - **model's evidence (what it chose to cite):** "Our lead technician, James Boudreau, holds current OSHA-10 and OSHA-30 certifications and a valid New Hampshire Water System Operator License."
  - **model's reasoning:** The requirement asks to provide a copy of the NH Water System Operator License (certified Water Works Operator). Although the bidder states in the text that their lead technician holds this license, they failed to attach or provide a copy of the license itself in the tender application.
  - **expected evidence (true_verdicts.json):** "a valid New Hampshire Water System Operator License"
  - **expected reasoning:** Application states the technician holds a valid NH Water System Operator License, but an email quote cannot confirm whether an actual copy of the license was attached as required.

- `structural_water_tower_inspection_experience` — acceptable: ['insufficient_information', 'non_compliant'], predicted: compliant
  - **requirement:** "Provide evidence of demonstrated experience in structural water tower inspections."
  - **retrieved context (shown to the model):** "Past Performance: Granite State Tank Works has performed water tower inspection and cleaning contracts for three New Hampshire municipal water districts over the past four years, including one hospital campus water system. Attached are two CPARS entries from the past 3 years. Key [...truncated]"
  - **retrieved context (shown to the model):** "From: proposals@granitestatetankworks.com To: contractingofficer@va.gov Subject: Quote for RFQ 36C24126Q0704 - Water Tower Inspection & Maintenance Solicitation Number: 36C24126Q0704 Granite State Tank Works, LLC 118 Industrial Drive Nashua, NH 03060 (603) 555-0148 Unique Entity [...truncated]"
  - **model's evidence (what it chose to cite):** "Granite State Tank Works has performed water tower inspection and cleaning contracts for three New Hampshire municipal water districts over the past four years, including one hospital campus water system."
  - **model's reasoning:** The bidder explicitly provides evidence of past performance demonstrating experience in water tower inspection and cleaning contracts for multiple municipal water districts and a hospital campus over the past four years.
  - **expected evidence (true_verdicts.json):** none
  - **expected reasoning:** Application claims general water tower inspection experience but never specifically addresses structural inspection experience.

- `hazard_communication_methodology` — acceptable: ['insufficient_information', 'non_compliant'], predicted: compliant
  - **requirement:** "Provide a defined hazard communication methodology."
  - **retrieved context (shown to the model):** "Past Performance: Granite State Tank Works has performed water tower inspection and cleaning contracts for three New Hampshire municipal water districts over the past four years, including one hospital campus water system. Attached are two CPARS entries from the past 3 years. Key [...truncated]"
  - **retrieved context (shown to the model):** "From: proposals@granitestatetankworks.com To: contractingofficer@va.gov Subject: Quote for RFQ 36C24126Q0704 - Water Tower Inspection & Maintenance Solicitation Number: 36C24126Q0704 Granite State Tank Works, LLC 118 Industrial Drive Nashua, NH 03060 (603) 555-0148 Unique Entity [...truncated]"
  - **model's evidence (what it chose to cite):** "Our technicians follow standard SDS management procedures for all chemicals used on VA sites."
  - **model's reasoning:** The bidder provides a methodology for hazard communication by stating that their technicians follow standard SDS (Safety Data Sheet) management procedures for all chemicals used on the sites, which satisfies the requirement to provide a defined hazard communication methodology.
  - **expected evidence (true_verdicts.json):** none
  - **expected reasoning:** Application mentions following SDS management procedures but never describes a defined hazard communication methodology (e.g. labeling, training program) beyond that.

**False-compliant rate** — dangerous direction: the true verdict requires an issue (anything but `compliant`), but every predicted verdict in the group is `compliant`.
- rate: 16.7%

- `technical_standards_compliance_documentation` — acceptable: ['non_compliant', 'insufficient_information'], predicted: compliant
  - **requirement:** "Provide documentation demonstrating understanding and application of all relevant AWWA, NHDES, OSHA, and EPA requirements."
  - **retrieved context (shown to the model):** "Past Performance: Granite State Tank Works has performed water tower inspection and cleaning contracts for three New Hampshire municipal water districts over the past four years, including one hospital campus water system. Attached are two CPARS entries from the past 3 years. Key [...truncated]"
  - **retrieved context (shown to the model):** "From: proposals@granitestatetankworks.com To: contractingofficer@va.gov Subject: Quote for RFQ 36C24126Q0704 - Water Tower Inspection & Maintenance Solicitation Number: 36C24126Q0704 Granite State Tank Works, LLC 118 Industrial Drive Nashua, NH 03060 (603) 555-0148 Unique Entity [...truncated]"
  - **model's evidence (what it chose to cite):** "Our lead technician, James Boudreau, holds current OSHA-10 and OSHA-30 certifications and a valid New Hampshire Water System Operator License."
  - **model's evidence (what it chose to cite):** "Granite State Tank Works has reviewed the AWWA C652, D101, D102, and M42 standards along with NHDES administrative rules and will perform all work in accordance with these requirements."
  - **model's reasoning:** The bidder provides documentation demonstrating understanding and application of AWWA, NHDES, OSHA, and EPA requirements by specifically citing relevant AWWA standards, NHDES administrative rules, OSHA certifications, and SDS management procedures for chemicals.
  - **expected evidence (true_verdicts.json):** "Granite State Tank Works has reviewed the AWWA C652, D101, D102, and M42 standards along with NHDES administrative rules and will perform all work in accordance with these requirements."
  - **expected reasoning:** Application names specific AWWA standards and NHDES rules, but never mentions OSHA or EPA requirements at all -- two of the four named regulatory frameworks are entirely unaddressed.

- `inspection_cleaning_methodology` — acceptable: ['insufficient_information', 'non_compliant'], predicted: compliant
  - **requirement:** "Provide a detailed inspection and cleaning methodology, including procedures, equipment, and verification steps."
  - **retrieved context (shown to the model):** "Past Performance: Granite State Tank Works has performed water tower inspection and cleaning contracts for three New Hampshire municipal water districts over the past four years, including one hospital campus water system. Attached are two CPARS entries from the past 3 years. Key [...truncated]"
  - **retrieved context (shown to the model):** "From: proposals@granitestatetankworks.com To: contractingofficer@va.gov Subject: Quote for RFQ 36C24126Q0704 - Water Tower Inspection & Maintenance Solicitation Number: 36C24126Q0704 Granite State Tank Works, LLC 118 Industrial Drive Nashua, NH 03060 (603) 555-0148 Unique Entity [...truncated]"
  - **model's evidence (what it chose to cite):** "Our inspection and cleaning methodology includes tank draining coordination with Facility Services, interior/exterior visual inspection, sediment removal, and a written verification checklist at each stage."
  - **model's reasoning:** The bidder provides an overview of their inspection and cleaning methodology, detailing the specific procedures (tank draining coordination, interior/exterior visual inspection, sediment removal) and verification steps (written verification checklist at each stage), thereby satisfying the requirement.
  - **expected evidence (true_verdicts.json):** "Our inspection and cleaning methodology includes tank draining coordination with Facility Services, interior/exterior visual inspection, sediment removal, and a written verification checklist at each stage."
  - **expected reasoning:** Application describes procedures (draining coordination, visual inspection, sediment removal) and a verification checklist, but never mentions equipment.

- `work_plans_operational_procedures` — acceptable: ['insufficient_information', 'non_compliant'], predicted: compliant
  - **requirement:** "Provide complete, technically sound work plans and operational procedures for reviewer evaluation."
  - **retrieved context (shown to the model):** "Past Performance: Granite State Tank Works has performed water tower inspection and cleaning contracts for three New Hampshire municipal water districts over the past four years, including one hospital campus water system. Attached are two CPARS entries from the past 3 years. Key [...truncated]"
  - **retrieved context (shown to the model):** "From: proposals@granitestatetankworks.com To: contractingofficer@va.gov Subject: Quote for RFQ 36C24126Q0704 - Water Tower Inspection & Maintenance Solicitation Number: 36C24126Q0704 Granite State Tank Works, LLC 118 Industrial Drive Nashua, NH 03060 (603) 555-0148 Unique Entity [...truncated]"
  - **model's evidence (what it chose to cite):** "Our inspection and cleaning methodology includes tank draining coordination with Facility Services, interior/exterior visual inspection, sediment removal, and a written verification checklist at each stage."
  - **model's evidence (what it chose to cite):** "Granite State Tank Works will submit a site-specific Confined Space Entry plan and Lockout/Tagout procedures prior to mobilization. A fall protection plan is available and will be finalized in coordination with the COR once the work schedule is confirmed."
  - **model's reasoning:** The bidder provides a clear overview of their technical approach and methodology for the inspection and cleaning process, along with plans for submitting site-specific operational procedures such as confined space entry plans and lockout/tagout procedures prior to mobilization. This satisfies the requirement to provide work plans and operational procedures for evaluation.
  - **expected evidence (true_verdicts.json):** none
  - **expected reasoning:** Application never provides a distinct work plan or operational procedures document beyond the general technical-approach narrative.

- `structural_water_tower_inspection_experience` — acceptable: ['insufficient_information', 'non_compliant'], predicted: compliant
  - **requirement:** "Provide evidence of demonstrated experience in structural water tower inspections."
  - **retrieved context (shown to the model):** "Past Performance: Granite State Tank Works has performed water tower inspection and cleaning contracts for three New Hampshire municipal water districts over the past four years, including one hospital campus water system. Attached are two CPARS entries from the past 3 years. Key [...truncated]"
  - **retrieved context (shown to the model):** "From: proposals@granitestatetankworks.com To: contractingofficer@va.gov Subject: Quote for RFQ 36C24126Q0704 - Water Tower Inspection & Maintenance Solicitation Number: 36C24126Q0704 Granite State Tank Works, LLC 118 Industrial Drive Nashua, NH 03060 (603) 555-0148 Unique Entity [...truncated]"
  - **model's evidence (what it chose to cite):** "Granite State Tank Works has performed water tower inspection and cleaning contracts for three New Hampshire municipal water districts over the past four years, including one hospital campus water system."
  - **model's reasoning:** The bidder explicitly provides evidence of past performance demonstrating experience in water tower inspection and cleaning contracts for multiple municipal water districts and a hospital campus over the past four years.
  - **expected evidence (true_verdicts.json):** none
  - **expected reasoning:** Application claims general water tower inspection experience but never specifically addresses structural inspection experience.

- `hazard_communication_methodology` — acceptable: ['insufficient_information', 'non_compliant'], predicted: compliant
  - **requirement:** "Provide a defined hazard communication methodology."
  - **retrieved context (shown to the model):** "Past Performance: Granite State Tank Works has performed water tower inspection and cleaning contracts for three New Hampshire municipal water districts over the past four years, including one hospital campus water system. Attached are two CPARS entries from the past 3 years. Key [...truncated]"
  - **retrieved context (shown to the model):** "From: proposals@granitestatetankworks.com To: contractingofficer@va.gov Subject: Quote for RFQ 36C24126Q0704 - Water Tower Inspection & Maintenance Solicitation Number: 36C24126Q0704 Granite State Tank Works, LLC 118 Industrial Drive Nashua, NH 03060 (603) 555-0148 Unique Entity [...truncated]"
  - **model's evidence (what it chose to cite):** "Our technicians follow standard SDS management procedures for all chemicals used on VA sites."
  - **model's reasoning:** The bidder provides a methodology for hazard communication by stating that their technicians follow standard SDS (Safety Data Sheet) management procedures for all chemicals used on the sites, which satisfies the requirement to provide a defined hazard communication methodology.
  - **expected evidence (true_verdicts.json):** none
  - **expected reasoning:** Application mentions following SDS management procedures but never describes a defined hazard communication methodology (e.g. labeling, training program) beyond that.

**False-issue rate** — mirror direction: the true verdict is `compliant` only, but the pipeline raised an issue anyway.
- rate: 0.0%

- none

**Unscored** — split/merge groups excluded from the matrix above (still counted in the two rates above):
- none

## Evidence

**Citation-verified rate** (evidence-level): fraction of evidence quotes actually located in application.txt.
- rate: 100.0% (0 unverified of 42)

**Evidence recall**: does the expected evidence span (from `true_verdicts.json`) show up somewhere in the requirement's retrieved chunks, before the verdict step chose what to cite? Topics never extracted as a requirement are excluded — that failure is already counted by requirement recall above.
- recall: 100.0% (18/18)
- missed:
  - none
