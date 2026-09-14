# Evaluation report

## Summary metrics

Machine-readable numbers for averaging across tenders -- every value here is explained in the sections below. `null` means the metric doesn't apply to this run (e.g. no verdict-only artifact present).

```json
{
  "requirement_recall": 0.9118,
  "requirement_recall_matched": 31,
  "requirement_recall_total": 34,
  "requirement_precision": 0.6957,
  "citation_verified_rate": 1.0,
  "is_mandatory_accuracy": 1.0,
  "is_mandatory_scored": 16,
  "is_text_verifiable_accuracy": 0.9375,
  "is_text_verifiable_scored": 16,
  "verdict_clean_match_count": 11,
  "verdict_accuracy": 1.0,
  "false_compliant_rate": 0.1333,
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

**Over-merge** (4) — one predicted requirement covering several distinct true topics:
- predicted [404a1444] "Provide complete, technically sound work plans and operational procedures including detailed inspection and cleaning methodology, equipment, verification steps, and technical specifications for ROV use in submerged surface inspections." — verdict: compliant lumps together 3 true requirements:
  - true `inspection_cleaning_methodology` — "Provide a detailed inspection and cleaning methodology, including procedures, equipment, and verification steps."
  - true `rov_technical_specifications` — "• Provide technical specifications and procedures for ROV use in submerged surface inspections."
  - true `work_plans_operational_procedures` — "Provide complete, technically sound work plans and operational procedures for reviewer evaluation."
- predicted [4fe5498a] "Provide evidence of demonstrated experience in structural water tower inspections, including capability to identify structural defects, coating failures, corrosion, erosion, sanitation deficiencies, and contamination routes, supported by sample reports or prior work." — verdict: compliant lumps together 2 true requirements:
  - true `structural_defect_capability_evidence` — "• Provide evidence of capability to identify structural defects, coating failures, corrosion, erosion, sanitation deficiencies, and contamination routes, supported by sample reports or prior work."
  - true `structural_water_tower_inspection_experience` — "Provide evidence of demonstrated experience in structural water tower inspections."
- predicted [38065faf] "Provide comprehensive safety plans and procedures, including an OSHA-compliant Confined Space Entry plan, equipment-specific Lockout/Tagout procedures, a comprehensive fall protection plan, SDS management procedures, hospital Infection Control compliance documentation, a defined hazard communication methodology, and evidence of safety controls for tools, ladders, cages, and access systems." — verdict: compliant lumps together 7 true requirements:
  - true `confined_space_entry_plan` — "Provide an OSHA-compliant Confined Space Entry plan."
  - true `fall_protection_plan` — "Provide a comprehensive fall protection plan."
  - true `hazard_communication_methodology` — "Provide a defined hazard communication methodology."
  - true `hospital_infection_control_compliance_documentation` — "Provide documentation demonstrating compliance with hospital Infection Control requirements."
  - true `lockout_tagout_procedures` — "Provide equipment-specific Lockout/Tagout procedures."
  - true `sds_management_procedures` — "Provide procedures for SDS management."
  - true `tool_ladder_access_safety_evidence` — "• Provide evidence of safety controls for tools, ladders, cages, and access systems."
- predicted [6fd0b452] "Provide required personnel certifications and documentation, including proof of OSHA 10 and OSHA 30, NH Water System Operator License, NHDES current standing confirmation, Confined Space Entry, Fall Protection, Stairways/Ladders, Lockout/Tagout, coating integrity assessment training, and Healthcare Environmental Sanitation training." — verdict: compliant lumps together 7 true requirements:
  - true `coating_integrity_training_evidence` — "Provide evidence of coating integrity assessment training."
  - true `confined_space_entry_certification` — "Provide Confined Space Entry certification."
  - true `fall_protection_stairways_ladders_lockout_certifications` — "Provide certifications for Fall Protection, Stairways/Ladders, and Lockout/Tagout."
  - true `healthcare_environmental_sanitation_training` — "Provide documentation of Healthcare Environmental Sanitation training."
  - true `nh_water_operator_license_copy` — "Provide a copy of the NH Water System Operator License (certified Water Works Operator)."
  - true `nhdes_standing_documentation` — "Provide documentation confirming current standing with NHDES."
  - true `osha_10_30_certifications` — "Provide proof of OSHA 10 and OSHA 30 certifications."

**Tangled** (0) — several true and several predicted requirements all overlapping at once:
- none

## Requirement precision

**Citation-verified rate** (hallucination check): fraction of predicted requirements whose citation was actually located in tender.txt (exactly or via fuzzy match).
- rate: 100.0%
- unverified:
  - none

**Classification precision**: fraction of predicted requirements that matched a true requirement.
- rate: 69.6%
- unexplained (7) — the model recognized these as requirements, but they don't match any true requirement. "closest true topic" is a mechanical (no-LLM) embedding-similarity lookup against every true topic's description; "dedup visibility" checks whether dedup's own cosine pre-filter would have clustered this candidate with whatever predicted requirement DID match that topic -- i.e. whether the dedup LLM call ever had a chance to compare them:
  - predicted [10a0cd3e] "The Offeror agrees to hold the prices in its offer firm for 60 calendar days from the date specified for receipt of offers, unless another time period is specified in an addendum to the solicitation."
    - **similarity check:** closest true topic: `offer_solicitation_number_stated` (cosine=0.67); vs matched predicted [459c3100]: cosine=0.57 (< dedup threshold 0.6) -> dedup's cosine pre-filter would NOT have clustered these -- the dedup LLM call never saw them side by side
  - predicted [16251f07] "All Labor hours in Section 3.2 is exclusive of section 3.1 and shall be bid as a separate line item."
    - **similarity check:** closest true topic: `price_schedule_completion` (cosine=0.65); that true topic has no matched predicted requirement in this run, so there was nothing for dedup to compare it against
  - predicted [79159e06] "As a minimum, offers shall include information necessary to evaluate the factors contained in the provision at 52.212-2 or as described in the solicitation."
    - **similarity check:** closest true topic: `offer_solicitation_number_stated` (cosine=0.68); vs matched predicted [459c3100]: cosine=0.66 (>= dedup threshold 0.6) -> would likely have been clustered together and compared by the dedup LLM call
  - predicted [98acc3b3] "Offerors may withdraw their offers by written notice to the Government received at any time before award."
    - **similarity check:** closest true topic: `offer_offeror_contact_info_stated` (cosine=0.60); vs matched predicted [d6896d92]: cosine=0.57 (< dedup threshold 0.6) -> dedup's cosine pre-filter would NOT have clustered these -- the dedup LLM call never saw them side by side
  - predicted [9eb195a8] "As a minimum, offers shall include responses to provisions that require Offeror completion of information, representations, and certifications (other than those collected via the System for Award Management (SAM))."
    - **similarity check:** closest true topic: `past_performance_quality_records` (cosine=0.66); vs matched predicted [a66995c1]: cosine=0.57 (< dedup threshold 0.6) -> dedup's cosine pre-filter would NOT have clustered these -- the dedup LLM call never saw them side by side
  - predicted [cf4f247b] "All Material allowances in Section 3.3 are exclusive of section 3.1 and 3.2 and shall be bid as a separate line item."
    - **similarity check:** closest true topic: `price_schedule_completion` (cosine=0.60); that true topic has no matched predicted requirement in this run, so there was nothing for dedup to compare it against
  - predicted [f961b60f] "Offerors are responsible for submitting offers and any modifications or revisions to the Government office designated in the solicitation by the time specified in the solicitation."
    - **similarity check:** closest true topic: `amendment_acknowledgment` (cosine=0.70); that true topic has no matched predicted requirement in this run, so there was nothing for dedup to compare it against

## Coverage flags

Clean 1:1 matches (recall counted them as found) whose citations don't fully overlap in length, split by which side is off. Over-split/over-merge/tangled matches are excluded here -- their predicted fragments are inherently partial by construction, already shown in the recall breakdown above.

**Requirements captured with extra text** (0) — the predicted citation is padded beyond the true one:
- none

**Requirements captured incompletely** (1) — the predicted citation misses part of the true one:
- predicted [685b9947] is contained in true `sdvosb_setaside_eligibility` — 53.2%:
    predicted: "The concern must qualify as a small business concern and be a certified SDVOSB listed in the SBA certification database at the time of submission of offer(s) and at the time of award, and the prospective contractor must represent this eligibility upon submission."
    true: "Pursuant to 38 U.S.C. 8127(e), only certified SDVOSBs listed in the SBA certification database are considered eligible to receive award of a resulting contract. By submitting an offer, the prospective contractor represents that it is an eligible and certified SDVOSB as defined in this clause, 13 CFR 121, 125, and 128, and VAAR subpart 819.70."

## is_mandatory accuracy

For each clean or one-to-many match (tangled groups excluded — there's no single "one" to compare against), does `is_mandatory` agree with the true value? A one-to-many group counts as correct only if every member on the "many" side agrees with the "one".

**Accuracy: 100.0% (16 groups)**

Mismatched:
- none

## is_text_verifiable accuracy

For each clean or one-to-many match (tangled groups excluded), does `is_text_verifiable` agree with the true value (all-or-nothing on the "many" side, same rule as is_mandatory above)? A wrong `false` here means the pipeline skips verdict generation for a requirement that should get one.

**Accuracy: 93.8% (16 groups)**

Mismatched:
- true: `sdvosb_setaside_eligibility`=False; predicted: `685b9947`=True — "Pursuant to 38 U.S.C. 8127(e), only certified SDVOSBs listed in the SBA certification database are considered eligible to receive award of a resulting contract. By submitting an offer, the prospective contractor represents that it is an eligible and certified SDVOSB as defined in this clause, 13 CFR 121, 125, and 128, and VAAR subpart 819.70."

## Verdict accuracy

The confusion matrix covers only clean 1:1 matches — split/merge groups have no single pair to plot, but still count in the two rates below.

Clean matches scored: 11

| true \ pipeline said | `compliant` | `non_compliant` | `contradictory` | `insufficient_information` |
|---|---|---|---|---|
| `compliant` | 10 | 0 | 0 | 0 |
| `non_compliant` | 0 | 0 | 0 | 0 |
| `contradictory` | 0 | 0 | 0 | 0 |
| `insufficient_information` | 1 | 0 | 0 | 0 |

Why some rows are empty:
- `contradictory` row is empty: true `nhdes_standing_documentation` — over_merge match — no single pair to plot

**Mismatched clean matches** — every off-diagonal cell above, in full: the full context retrieved and shown to the model, what it chose to cite from that context, and its reasoning ("model's ..."), next to what `true_verdicts.json` expects ("expected ...").

- none

**False-compliant rate** — dangerous direction: the true verdict requires an issue (anything but `compliant`), but every predicted verdict in the group is `compliant`.
- rate: 13.3%

- group of 3 true topic(s) and 1 predicted requirement(s) (not a 1:1 match, so there is no single correct pairing between them):
  - true `inspection_cleaning_methodology` — "Provide a detailed inspection and cleaning methodology, including procedures, equipment, and verification steps." (acceptable: ['compliant'])
      - **expected evidence (true_verdicts.json):** "Our inspection approach uses a remotely operated vehicle (ROV) for submerged surface inspection, followed by interior drain-down and manual verification of the tank floor, walls, and roof structure, documented with photographs at each station and a written verification checklist."
      - **expected reasoning:** Application describes a detailed, sequenced inspection and cleaning methodology with documentation and verification steps.
  - true `rov_technical_specifications` — "• Provide technical specifications and procedures for ROV use in submerged surface inspections." (acceptable: ['insufficient_information', 'non_compliant'])
      - **expected evidence (true_verdicts.json):** "Our inspection approach uses a remotely operated vehicle (ROV) for submerged surface inspection"
      - **expected reasoning:** Application only asserts that a remotely operated vehicle (ROV) is used for submerged surface inspection, without providing any of the required technical specifications (e.g. ROV model, depth capability, camera resolution) or procedures for its use -- the bare usage claim does not satisfy the requirement's specific ask for specifications and procedures.
  - true `work_plans_operational_procedures` — "Provide complete, technically sound work plans and operational procedures for reviewer evaluation." (acceptable: ['compliant'])
      - **expected evidence (true_verdicts.json):** "Detailed work plans and operational procedures for this project are included as Attachment B to this quote."
      - **expected reasoning:** Application states detailed work plans and operational procedures are included as an attachment.
  - **retrieved context (shown to the model):** "Standards Compliance: Our work will be performed in accordance with AWWA C652, AWWA D101/M42, applicable NHDES administrative rules, OSHA 1910.146, and EPA guidance on potable water system disinfection byproducts. Inspection Methodology: Our inspection approach uses a remotely op [...truncated]"
  - **retrieved context (shown to the model):** "Our hazard communication methodology follows a written HazCom program with SDS binders maintained on every service vehicle; SDS management procedures are documented in the same binder system. All field technicians hold current Confined Space Entry certification and current Lockou [...truncated]"
  - **retrieved context (shown to the model):** "Past Performance: 1. City of Concord Water Works - Elevated Tank Inspection & Recoating (2023). Contract value: $98,000. CPARS rating: Very Good. Point of Contact: Sandra Hollis, Water Utility Director, (603) 555-4471. 2. Town of Bow Public Works - Standpipe Cleaning & Inspection [...truncated]"
  - **retrieved context (shown to the model):** "From: proposals@bedrocktankmaintenance.com To: contractingofficer@va.gov Subject: Quote for RFQ 36C24126Q0704 - Water Tower Inspection & Maintenance Solicitation Number: 36C24126Q0704 Bedrock Tank Maintenance, LLC 1180 Quarry Road Concord, NH 03301 (603) 555-0294 Unique Entity Id [...truncated]"
  - predicted verdicts in this group:
    - predicted [404a1444] "Provide complete, technically sound work plans and operational procedures including detailed inspection and cleaning methodology, equipment, verification steps, and technical specifications for ROV use in submerged surface inspections." — verdict: compliant
      - **model's evidence (what it chose to cite):** "Inspection Methodology: Our inspection approach uses a remotely operated vehicle (ROV) for submerged surface inspection, followed by interior drain-down and manual verification of the tank floor, walls, and roof structure, documented with photographs at each station and a written verification checklist. Detailed work plans and operational procedures for this project are included as Attachment B to this quote."
      - **model's reasoning:** The bidder provides an inspection methodology utilizing an ROV for submerged surface inspections, incorporates verification steps and photographic documentation, and explicitly states that detailed work plans and operational procedures are included as Attachment B, thereby satisfying the requirement.

- group of 7 true topic(s) and 1 predicted requirement(s) (not a 1:1 match, so there is no single correct pairing between them):
  - true `coating_integrity_training_evidence` — "Provide evidence of coating integrity assessment training." (acceptable: ['compliant'])
      - **expected evidence (true_verdicts.json):** "Our lead inspector holds NACE Level 2 Coating Inspector certification."
      - **expected reasoning:** Application cites the lead inspector's NACE Level 2 Coating Inspector certification.
  - true `confined_space_entry_certification` — "Provide Confined Space Entry certification." (acceptable: ['compliant'])
      - **expected evidence (true_verdicts.json):** "All field technicians hold current Confined Space Entry certification and current Lockout/Tagout certification."
      - **expected reasoning:** Application states all field technicians hold current Confined Space Entry certification.
  - true `fall_protection_stairways_ladders_lockout_certifications` — "Provide certifications for Fall Protection, Stairways/Ladders, and Lockout/Tagout." (acceptable: ['insufficient_information'])
      - **expected evidence (true_verdicts.json):** "current Lockout/Tagout certification."
      - **expected evidence (true_verdicts.json):** "Tool, ladder, and access safety controls include daily pre-use inspection of harnesses and lanyards, caged ladder access with fall-arrest anchor points, and a two-person rule for all confined-space entries."
      - **expected reasoning:** Application confirms Lockout/Tagout certification and describes fall-protection equipment use, but never confirms a Stairways/Ladders certification specifically, so one of the three combined certifications is unaddressed.
  - true `healthcare_environmental_sanitation_training` — "Provide documentation of Healthcare Environmental Sanitation training." (acceptable: ['compliant'])
      - **expected evidence (true_verdicts.json):** "Our field personnel have completed Healthcare Environmental Sanitation training"
      - **expected reasoning:** Application states field personnel have completed Healthcare Environmental Sanitation training.
  - true `nh_water_operator_license_copy` — "Provide a copy of the NH Water System Operator License (certified Water Works Operator)." (acceptable: ['compliant'])
      - **expected evidence (true_verdicts.json):** "Our lead technician, Daniel Whitcomb, holds a valid New Hampshire Water System Operator License; a copy is enclosed with this quote."
      - **expected reasoning:** Application states a copy of the NH Water System Operator License is enclosed.
  - true `nhdes_standing_documentation` — "Provide documentation confirming current standing with NHDES." (acceptable: ['contradictory'])
      - **expected evidence (true_verdicts.json):** "We maintain current standing with NHDES, confirmed by a standing letter dated March 2026 on file with our safety office."
      - **expected evidence (true_verdicts.json):** "our NHDES public water system registration is currently under renewal review following a routine compliance audit initiated earlier this year; we expect the review to conclude before the anticipated award date."
      - **expected reasoning:** Application states it maintains current standing with NHDES confirmed by a dated standing letter, but later states its NHDES registration is currently under renewal review following a compliance audit -- the two statements about current NHDES standing conflict.
  - true `osha_10_30_certifications` — "Provide proof of OSHA 10 and OSHA 30 certifications." (acceptable: ['compliant'])
      - **expected evidence (true_verdicts.json):** "Our field technicians hold current OSHA 10 and OSHA 30 certifications."
      - **expected reasoning:** Application states field technicians hold current OSHA 10 and OSHA 30 certifications.
  - **retrieved context (shown to the model):** "Our hazard communication methodology follows a written HazCom program with SDS binders maintained on every service vehicle; SDS management procedures are documented in the same binder system. All field technicians hold current Confined Space Entry certification and current Lockou [...truncated]"
  - **retrieved context (shown to the model):** "Past Performance: 1. City of Concord Water Works - Elevated Tank Inspection & Recoating (2023). Contract value: $98,000. CPARS rating: Very Good. Point of Contact: Sandra Hollis, Water Utility Director, (603) 555-4471. 2. Town of Bow Public Works - Standpipe Cleaning & Inspection [...truncated]"
  - **retrieved context (shown to the model):** "Standards Compliance: Our work will be performed in accordance with AWWA C652, AWWA D101/M42, applicable NHDES administrative rules, OSHA 1910.146, and EPA guidance on potable water system disinfection byproducts. Inspection Methodology: Our inspection approach uses a remotely op [...truncated]"
  - **retrieved context (shown to the model):** "From: proposals@bedrocktankmaintenance.com To: contractingofficer@va.gov Subject: Quote for RFQ 36C24126Q0704 - Water Tower Inspection & Maintenance Solicitation Number: 36C24126Q0704 Bedrock Tank Maintenance, LLC 1180 Quarry Road Concord, NH 03301 (603) 555-0294 Unique Entity Id [...truncated]"
  - predicted verdicts in this group:
    - predicted [6fd0b452] "Provide required personnel certifications and documentation, including proof of OSHA 10 and OSHA 30, NH Water System Operator License, NHDES current standing confirmation, Confined Space Entry, Fall Protection, Stairways/Ladders, Lockout/Tagout, coating integrity assessment training, and Healthcare Environmental Sanitation training." — verdict: compliant
      - **model's evidence (what it chose to cite):** "Our field technicians hold current OSHA 10 and OSHA 30 certifications. Our lead technician, Daniel Whitcomb, holds a valid New Hampshire Water System Operator License; a copy is enclosed with this quote. We maintain current standing with NHDES, confirmed by a standing letter dated March 2026 on file with our safety office. Our field personnel have completed Healthcare Environmental Sanitation training and hold current Hospital Infection Control compliance documentation."
      - **model's evidence (what it chose to cite):** "All field technicians hold current Confined Space Entry certification and current Lockout/Tagout certification. A written, OSHA-compliant Confined Space Entry plan and equipment-specific Lockout/Tagout procedures are included as Attachment D. A comprehensive fall protection plan covering ladder climbs, roof-hatch access, and harness anchor points is included as Attachment E."
      - **model's evidence (what it chose to cite):** "Coating Integrity Training: Our lead inspector holds NACE Level 2 Coating Inspector certification."
      - **model's reasoning:** The bidder's application explicitly addresses and provides evidence of meeting all the requested personnel certifications and documentation requirements, including OSHA 10 and OSHA 30, NH Water System Operator License, NHDES current standing confirmation, Confined Space Entry, Fall Protection, Stairways/Ladders, Lockout/Tagout, coating integrity assessment training, and Healthcare Environmental Sanitation training.

**False-issue rate** — mirror direction: the true verdict is `compliant` only, but the pipeline raised an issue anyway.
- rate: 0.0%

- none

**Unscored** — split/merge groups excluded from the matrix above (still counted in the two rates above):
- group 1:
  - true `inspection_cleaning_methodology` — "Provide a detailed inspection and cleaning methodology, including procedures, equipment, and verification steps." (acceptable: ['compliant'])
  - true `rov_technical_specifications` — "• Provide technical specifications and procedures for ROV use in submerged surface inspections." (acceptable: ['insufficient_information', 'non_compliant'])
  - true `work_plans_operational_procedures` — "Provide complete, technically sound work plans and operational procedures for reviewer evaluation." (acceptable: ['compliant'])
  - predicted [404a1444] "Provide complete, technically sound work plans and operational procedures including detailed inspection and cleaning methodology, equipment, verification steps, and technical specifications for ROV use in submerged surface inspections." — verdict: compliant
- group 2:
  - true `structural_defect_capability_evidence` — "• Provide evidence of capability to identify structural defects, coating failures, corrosion, erosion, sanitation deficiencies, and contamination routes, supported by sample reports or prior work." (acceptable: ['compliant'])
  - true `structural_water_tower_inspection_experience` — "Provide evidence of demonstrated experience in structural water tower inspections." (acceptable: ['compliant'])
  - predicted [4fe5498a] "Provide evidence of demonstrated experience in structural water tower inspections, including capability to identify structural defects, coating failures, corrosion, erosion, sanitation deficiencies, and contamination routes, supported by sample reports or prior work." — verdict: compliant
- group 3:
  - true `confined_space_entry_plan` — "Provide an OSHA-compliant Confined Space Entry plan." (acceptable: ['compliant'])
  - true `fall_protection_plan` — "Provide a comprehensive fall protection plan." (acceptable: ['compliant'])
  - true `hazard_communication_methodology` — "Provide a defined hazard communication methodology." (acceptable: ['compliant'])
  - true `hospital_infection_control_compliance_documentation` — "Provide documentation demonstrating compliance with hospital Infection Control requirements." (acceptable: ['compliant'])
  - true `lockout_tagout_procedures` — "Provide equipment-specific Lockout/Tagout procedures." (acceptable: ['compliant'])
  - true `sds_management_procedures` — "Provide procedures for SDS management." (acceptable: ['compliant'])
  - true `tool_ladder_access_safety_evidence` — "• Provide evidence of safety controls for tools, ladders, cages, and access systems." (acceptable: ['compliant'])
  - predicted [38065faf] "Provide comprehensive safety plans and procedures, including an OSHA-compliant Confined Space Entry plan, equipment-specific Lockout/Tagout procedures, a comprehensive fall protection plan, SDS management procedures, hospital Infection Control compliance documentation, a defined hazard communication methodology, and evidence of safety controls for tools, ladders, cages, and access systems." — verdict: compliant
- group 4:
  - true `coating_integrity_training_evidence` — "Provide evidence of coating integrity assessment training." (acceptable: ['compliant'])
  - true `confined_space_entry_certification` — "Provide Confined Space Entry certification." (acceptable: ['compliant'])
  - true `fall_protection_stairways_ladders_lockout_certifications` — "Provide certifications for Fall Protection, Stairways/Ladders, and Lockout/Tagout." (acceptable: ['insufficient_information'])
  - true `healthcare_environmental_sanitation_training` — "Provide documentation of Healthcare Environmental Sanitation training." (acceptable: ['compliant'])
  - true `nh_water_operator_license_copy` — "Provide a copy of the NH Water System Operator License (certified Water Works Operator)." (acceptable: ['compliant'])
  - true `nhdes_standing_documentation` — "Provide documentation confirming current standing with NHDES." (acceptable: ['contradictory'])
  - true `osha_10_30_certifications` — "Provide proof of OSHA 10 and OSHA 30 certifications." (acceptable: ['compliant'])
  - predicted [6fd0b452] "Provide required personnel certifications and documentation, including proof of OSHA 10 and OSHA 30, NH Water System Operator License, NHDES current standing confirmation, Confined Space Entry, Fall Protection, Stairways/Ladders, Lockout/Tagout, coating integrity assessment training, and Healthcare Environmental Sanitation training." — verdict: compliant

## Evidence

**Citation-verified rate** (evidence-level): fraction of evidence quotes actually located in application.txt.
- rate: 100.0% (0 unverified of 28)

**Evidence recall**: does the expected evidence span (from `true_verdicts.json`) show up somewhere in the requirement's retrieved chunks, before the verdict step chose what to cite? Topics never extracted as a requirement are excluded — that failure is already counted by requirement recall above.
- recall: 100.0% (30/30)
- missed:
  - none
