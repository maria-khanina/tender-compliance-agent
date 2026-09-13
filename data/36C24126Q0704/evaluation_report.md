# Evaluation report

## Summary metrics

Machine-readable numbers for averaging across tenders -- every value here is explained in the sections below. `null` means the metric doesn't apply to this run (e.g. no verdict-only artifact present).

```json
{
  "requirement_recall": 0.9412,
  "requirement_recall_matched": 32,
  "requirement_recall_total": 34,
  "requirement_precision": 0.7273,
  "citation_verified_rate": 1.0,
  "is_mandatory_accuracy": 0.9583,
  "is_mandatory_scored": 24,
  "is_text_verifiable_accuracy": 0.9583,
  "is_text_verifiable_scored": 24,
  "verdict_clean_match_count": 18,
  "verdict_accuracy": 0.7778,
  "false_compliant_rate": 0.0435,
  "false_issue_rate": 0.1739,
  "evidence_citation_verified_rate": 0.9474,
  "evidence_recall": 1.0,
  "verdict_only_accuracy": null,
  "verdict_only_scored": null
}
```

## Requirement recall

For each `true_requirements.json` topic, did the pipeline extract something whose tender.txt citation overlaps the true one? A pure text-offset check, not a judgment of meaning — see coverage flags below for extractions that are technically "found" but sloppy.

**Recall: 94.1% (32/34)**

**Missed** (2) — no overlapping predicted requirement at all. "chunk check" is a mechanical (no-LLM) re-chunking of the source document: whether this topic's matching text ever appeared whole in one chunk handed to the extraction model, or was split across chunks.
- true `price_schedule_completion` — "0001 | | 1.00 | JB | __________________ | __________________ ... 0002 | | 80.00 | HR | __________________ | __________________ ... 0003 | | 1.00 | JB | __________________ | __________________ ... | | | | GRAND TOTAL | __________________"
    - **chunk check:** [1412:1473] whole, in chunk 1 -- the model saw this text intact; [1526:1588] whole, in chunk 1 -- the model saw this text intact; [1755:1816] whole, in chunk 1 -- the model saw this text intact; [2011:2055] whole, in chunk 1 -- the model saw this text intact
- true `submission_deadline` — "RFQ DUE 18 SEP 2026, 3 PM EST."
    - **chunk check:** [14218:14249] whole, in chunk 11 -- the model saw this text intact

**Over-split** (0) — one true topic extracted as several separate predicted requirements:
- none

**Over-merge** (5) — one predicted requirement covering several distinct true topics:
- predicted [8293d996] "Provide evidence of capability and experience in structural water tower inspections, including the identification of structural defects, coating failures, corrosion, erosion, sanitation deficiencies, and contamination routes, supported by sample reports or prior work." — verdict: insufficient_information lumps together 2 true requirements:
  - true `structural_defect_capability_evidence` — "• Provide evidence of capability to identify structural defects, coating failures, corrosion, erosion, sanitation deficiencies, and contamination routes, supported by sample reports or prior work."
  - true `structural_water_tower_inspection_experience` — "Provide evidence of demonstrated experience in structural water tower inspections."
- predicted [66358425] "Provide certifications for Fall Protection, Stairways/Ladders, and Lockout/Tagout, along with equipment-specific Lockout/Tagout procedures, a comprehensive fall protection plan, and evidence of safety controls for tools, ladders, cages, and access systems." — verdict: non_compliant lumps together 4 true requirements:
  - true `fall_protection_plan` — "Provide a comprehensive fall protection plan."
  - true `fall_protection_stairways_ladders_lockout_certifications` — "Provide certifications for Fall Protection, Stairways/Ladders, and Lockout/Tagout."
  - true `lockout_tagout_procedures` — "Provide equipment-specific Lockout/Tagout procedures."
  - true `tool_ladder_access_safety_evidence` — "• Provide evidence of safety controls for tools, ladders, cages, and access systems."
- predicted [9e5958de] "Provide a detailed, technically sound inspection and cleaning methodology, including operational procedures, equipment, and verification steps for reviewer evaluation." — verdict: non_compliant lumps together 2 true requirements:
  - true `inspection_cleaning_methodology` — "Provide a detailed inspection and cleaning methodology, including procedures, equipment, and verification steps."
  - true `work_plans_operational_procedures` — "Provide complete, technically sound work plans and operational procedures for reviewer evaluation."
- predicted [167ab4e9] "Provide evidence of performance in hospital or other high-risk environments, including documentation of Healthcare Environmental Sanitation training and compliance with hospital Infection Control requirements." — verdict: non_compliant lumps together 3 true requirements:
  - true `healthcare_environmental_sanitation_training` — "Provide documentation of Healthcare Environmental Sanitation training."
  - true `hospital_infection_control_compliance_documentation` — "Provide documentation demonstrating compliance with hospital Infection Control requirements."
  - true `past_performance_hospital_high_risk_environment` — "Provide evidence of performance in hospital or other high-risk environments."
- predicted [faea2590] "Provide Confined Space Entry certification for personnel and an OSHA-compliant Confined Space Entry plan." — verdict: non_compliant lumps together 2 true requirements:
  - true `confined_space_entry_certification` — "Provide Confined Space Entry certification."
  - true `confined_space_entry_plan` — "Provide an OSHA-compliant Confined Space Entry plan."

**Tangled** (0) — several true and several predicted requirements all overlapping at once:
- none

## Requirement precision

**Citation-verified rate** (hallucination check): fraction of predicted requirements whose citation was actually located in tender.txt (exactly or via fuzzy match).
- rate: 100.0%
- unverified:
  - none

**Classification precision**: fraction of predicted requirements that matched a true requirement.
- rate: 72.7%
- unexplained (9) — the model recognized these as requirements, but they don't match any true requirement. "closest true topic" is a mechanical (no-LLM) embedding-similarity lookup against every true topic's description; "dedup visibility" checks whether dedup's own cosine pre-filter would have clustered this candidate with whatever predicted requirement DID match that topic -- i.e. whether the dedup LLM call ever had a chance to compare them:
  - predicted [0014b3ec] "Offers received from entities that are not certified SDVOSBs and listed in the SBA certification database at the time of offer shall not be considered."
    - **similarity check:** closest true topic: `sdvosb_setaside_eligibility` (cosine=0.71); vs matched predicted [0dc52f44]: cosine=0.68 (>= dedup threshold 0.6) -> would likely have been clustered together and compared by the dedup LLM call
  - predicted [1c4776d4] "The Offeror agrees to hold the prices in its offer firm for 60 calendar days from the date specified for receipt of offers, unless another time period is specified in an addendum to the solicitation."
    - **similarity check:** closest true topic: `offer_solicitation_number_stated` (cosine=0.67); vs matched predicted [3d04f514]: cosine=0.57 (< dedup threshold 0.6) -> dedup's cosine pre-filter would NOT have clustered these -- the dedup LLM call never saw them side by side
  - predicted [2eaffdda] "Offerors must submit signed and dated offers, including any modifications or revisions, to the designated Government office at or before the exact time specified in the solicitation."
    - **similarity check:** closest true topic: `offer_offeror_contact_info_stated` (cosine=0.70); vs matched predicted [47f8ca48]: cosine=0.66 (>= dedup threshold 0.6) -> would likely have been clustered together and compared by the dedup LLM call
  - predicted [8af7fa24] "All Invoices from the contractor shall be submitted electronically in accordance with VAAR Clause 852.232-72 Electronic Submission of Payment Requests."
    - **similarity check:** closest true topic: `hospital_infection_control_compliance_documentation` (cosine=0.56); vs matched predicted [167ab4e9]: cosine=0.43 (< dedup threshold 0.6) -> dedup's cosine pre-filter would NOT have clustered these -- the dedup LLM call never saw them side by side
  - predicted [ac6cbd5b] "As a minimum, offers shall include— ... (5) Responses to provisions that require Offeror completion of information, representations, and certifications (other than those collected via the System for Award Management (SAM));"
    - **similarity check:** closest true topic: `past_performance_quality_records` (cosine=0.66); vs matched predicted [9622ecc7]: cosine=0.57 (< dedup threshold 0.6) -> dedup's cosine pre-filter would NOT have clustered these -- the dedup LLM call never saw them side by side
  - predicted [b05cbb64] "The Contractor will: ... l approach to performing the full water tower inspection, cleaning, maintenance, and repair services described in the SOW. The"
    - **similarity check:** closest true topic: `structural_water_tower_inspection_experience` (cosine=0.67); vs matched predicted [8293d996]: cosine=0.66 (>= dedup threshold 0.6) -> would likely have been clustered together and compared by the dedup LLM call
  - predicted [bd828a58] "All Labor hours in Section 3.2 must be exclusive of Section 3.1 and bid as a separate line item."
    - **similarity check:** closest true topic: `price_schedule_completion` (cosine=0.65); that true topic has no matched predicted requirement in this run, so there was nothing for dedup to compare it against
  - predicted [cd5c2c30] "As a minimum, offers shall include— ... (4) Information necessary to evaluate the factors contained in the provision at 52.212-2 or as described in the solicitation;"
    - **similarity check:** closest true topic: `offer_solicitation_number_stated` (cosine=0.68); vs matched predicted [3d04f514]: cosine=0.66 (>= dedup threshold 0.6) -> would likely have been clustered together and compared by the dedup LLM call
  - predicted [f7fd27b1] "All Material allowances in Section 3.3 must be exclusive of Section 3.1 and 3.2 and bid as a separate line item."
    - **similarity check:** closest true topic: `price_schedule_completion` (cosine=0.60); that true topic has no matched predicted requirement in this run, so there was nothing for dedup to compare it against

## Coverage flags

Clean 1:1 matches (recall counted them as found) whose citations don't fully overlap in length, split by which side is off. Over-split/over-merge/tangled matches are excluded here -- their predicted fragments are inherently partial by construction, already shown in the recall breakdown above.

**Requirements captured with extra text** (0) — the predicted citation is padded beyond the true one:
- none

**Requirements captured incompletely** (1) — the predicted citation misses part of the true one:
- predicted [0dc52f44] is contained in true `sdvosb_setaside_eligibility` — 53.2%:
    predicted: "To be eligible for an SDVOSB set-aside or sole source contract, the offeror must qualify as a small business concern under the applicable NAICS code size standard and be a certified SDVOSB participant in the SBA certification database, as defined by 13 CFR 121, 125, 128, and VAAR subpart 819.70."
    true: "Pursuant to 38 U.S.C. 8127(e), only certified SDVOSBs listed in the SBA certification database are considered eligible to receive award of a resulting contract. By submitting an offer, the prospective contractor represents that it is an eligible and certified SDVOSB as defined in this clause, 13 CFR 121, 125, and 128, and VAAR subpart 819.70."

## is_mandatory accuracy

For each clean or one-to-many match (tangled groups excluded — there's no single "one" to compare against), does `is_mandatory` agree with the true value? A one-to-many group counts as correct only if every member on the "many" side agrees with the "one".

**Accuracy: 95.8% (24 groups)**

Mismatched:
- true: `amendment_acknowledgment`=False; predicted: `c71c57e5`=True — "ACKNOWLEDGMENT OF AMENDMENTS: The offeror acknowledges receipt of amendments to the Solicitation numbered and dated as follows: AMENDMENT NO | DATE"

## is_text_verifiable accuracy

For each clean or one-to-many match (tangled groups excluded), does `is_text_verifiable` agree with the true value (all-or-nothing on the "many" side, same rule as is_mandatory above)? A wrong `false` here means the pipeline skips verdict generation for a requirement that should get one.

**Accuracy: 95.8% (24 groups)**

Mismatched:
- true: `sdvosb_setaside_eligibility`=False; predicted: `0dc52f44`=True — "Pursuant to 38 U.S.C. 8127(e), only certified SDVOSBs listed in the SBA certification database are considered eligible to receive award of a resulting contract. By submitting an offer, the prospective contractor represents that it is an eligible and certified SDVOSB as defined in this clause, 13 CFR 121, 125, and 128, and VAAR subpart 819.70."

## Verdict accuracy

The confusion matrix covers only clean 1:1 matches — split/merge groups have no single pair to plot, but still count in the two rates below.

Clean matches scored: 18

| true \ pipeline said | `compliant` | `non_compliant` | `contradictory` | `insufficient_information` |
|---|---|---|---|---|
| `compliant` | 5 | 2 | 0 | 1 |
| `non_compliant` | 1 | 2 | 0 | 0 |
| `contradictory` | 0 | 0 | 1 | 0 |
| `insufficient_information` | 0 | 3 | 0 | 3 |

**Mismatched clean matches** — every off-diagonal cell above, in full: the full context retrieved and shown to the model, what it chose to cite from that context, and its reasoning ("model's ..."), next to what `true_verdicts.json` expects ("expected ...").

- `amendment_acknowledgment` — acceptable: ['compliant'], predicted: non_compliant, citation: fuzzy match — worth a second look
  - **requirement:** "The offeror must acknowledge receipt of all amendments to the Solicitation, including their respective numbers and dates."
  - **retrieved context (shown to the model):** "From: proposals@granitestatetankworks.com To: contractingofficer@va.gov Subject: Quote for RFQ 36C24126Q0704 - Water Tower Inspection & Maintenance Solicitation Number: 36C24126Q0704 Granite State Tank Works, LLC 118 Industrial Drive Nashua, NH 03060 (603) 555-0148 Unique Entity [...truncated]"
  - **retrieved context (shown to the model):** "Past Performance: Granite State Tank Works has performed water tower inspection and cleaning contracts for three New Hampshire municipal water districts over the past four years, including one hospital campus water system. Attached are two CPARS entries from the past 3 years. Key [...truncated]"
  - **model's evidence (what it chose to cite):** "Granite State Tank Works, LLC agrees with all terms, conditions, and provisions included in the solicitation."
  - **model's reasoning:** The requirement explicitly mandates that the offeror must acknowledge receipt of all amendments, including their respective numbers and dates. The provided application does not mention any amendments, nor does it list any numbers or dates associated with them. The general statement agreeing to all terms and conditions does not satisfy the specific requirement to acknowledge receipt of amendments.
  - **expected evidence (true_verdicts.json):** none
  - **expected reasoning:** The solicitation's own amendment table is blank (no amendments have been issued), so there is nothing for the offeror to acknowledge; the conditional requirement is not triggered.

- `technical_standards_compliance_documentation` — acceptable: ['non_compliant', 'insufficient_information'], predicted: compliant
  - **requirement:** "Provide documentation demonstrating understanding and application of all relevant AWWA, NHDES, OSHA, and EPA requirements."
  - **retrieved context (shown to the model):** "Past Performance: Granite State Tank Works has performed water tower inspection and cleaning contracts for three New Hampshire municipal water districts over the past four years, including one hospital campus water system. Attached are two CPARS entries from the past 3 years. Key [...truncated]"
  - **retrieved context (shown to the model):** "From: proposals@granitestatetankworks.com To: contractingofficer@va.gov Subject: Quote for RFQ 36C24126Q0704 - Water Tower Inspection & Maintenance Solicitation Number: 36C24126Q0704 Granite State Tank Works, LLC 118 Industrial Drive Nashua, NH 03060 (603) 555-0148 Unique Entity [...truncated]"
  - **model's evidence (what it chose to cite):** "Granite State Tank Works has reviewed the AWWA C652, D101, D102, and M42 standards along with NHDES administrative rules and will perform all work in accordance with these requirements."
  - **model's evidence (what it chose to cite):** "Our lead technician, James Boudreau, holds current OSHA-10 and OSHA-30 certifications... Mr. Boudreau also holds Confined Space Entry certification and has completed Fall Protection and Lockout/Tagout training."
  - **model's evidence (what it chose to cite):** "Granite State Tank Works will submit a site-specific Confined Space Entry plan and Lockout/Tagout procedures prior to mobilization. A fall protection plan is available... Our technicians follow standard SDS management procedures for all chemicals used on VA sites."
  - **model's reasoning:** The bidder explicitly states they have reviewed and will comply with the relevant AWWA standards and NHDES rules. Furthermore, they provide evidence of OSHA-compliant training and safety procedures (Confined Space, Fall Protection, Lockout/Tagout, and SDS management) for their personnel, demonstrating an understanding and application of the required regulatory frameworks.
  - **expected evidence (true_verdicts.json):** "Granite State Tank Works has reviewed the AWWA C652, D101, D102, and M42 standards along with NHDES administrative rules and will perform all work in accordance with these requirements."
  - **expected reasoning:** Application names specific AWWA standards and NHDES rules, but never mentions OSHA or EPA requirements at all -- two of the four named regulatory frameworks are entirely unaddressed.

- `nh_water_operator_license_copy` — acceptable: ['insufficient_information', 'compliant'], predicted: non_compliant
  - **requirement:** "Provide a copy of the NH Water System Operator License for contractor personnel."
  - **retrieved context (shown to the model):** "Past Performance: Granite State Tank Works has performed water tower inspection and cleaning contracts for three New Hampshire municipal water districts over the past four years, including one hospital campus water system. Attached are two CPARS entries from the past 3 years. Key [...truncated]"
  - **retrieved context (shown to the model):** "From: proposals@granitestatetankworks.com To: contractingofficer@va.gov Subject: Quote for RFQ 36C24126Q0704 - Water Tower Inspection & Maintenance Solicitation Number: 36C24126Q0704 Granite State Tank Works, LLC 118 Industrial Drive Nashua, NH 03060 (603) 555-0148 Unique Entity [...truncated]"
  - **model's evidence (what it chose to cite):** "Our lead technician, James Boudreau, holds current OSHA-10 and OSHA-30 certifications and a valid New Hampshire Water System Operator License."
  - **model's reasoning:** The requirement explicitly asks for a copy of the NH Water System Operator License. While the bidder states that their lead technician holds the license, they failed to provide an actual copy of the document as requested in the tender requirements.
  - **expected evidence (true_verdicts.json):** "a valid New Hampshire Water System Operator License"
  - **expected reasoning:** Application states the technician holds a valid NH Water System Operator License, but an email quote cannot confirm whether an actual copy of the license was attached as required.

- `sds_management_procedures` — acceptable: ['compliant'], predicted: non_compliant
  - **requirement:** "Provide procedures for SDS management."
  - **retrieved context (shown to the model):** "Past Performance: Granite State Tank Works has performed water tower inspection and cleaning contracts for three New Hampshire municipal water districts over the past four years, including one hospital campus water system. Attached are two CPARS entries from the past 3 years. Key [...truncated]"
  - **retrieved context (shown to the model):** "From: proposals@granitestatetankworks.com To: contractingofficer@va.gov Subject: Quote for RFQ 36C24126Q0704 - Water Tower Inspection & Maintenance Solicitation Number: 36C24126Q0704 Granite State Tank Works, LLC 118 Industrial Drive Nashua, NH 03060 (603) 555-0148 Unique Entity [...truncated]"
  - **model's evidence (what it chose to cite):** "Our technicians follow standard SDS management procedures for all chemicals used on VA sites."
  - **model's reasoning:** The bidder states that they follow 'standard SDS management procedures' but fails to actually provide or describe what those procedures are. Simply stating that procedures are followed does not satisfy the requirement to provide the procedures themselves.
  - **expected evidence (true_verdicts.json):** "Our technicians follow standard SDS management procedures for all chemicals used on VA sites."
  - **expected reasoning:** Application states technicians follow standard SDS management procedures for all chemicals used on VA sites.

**False-compliant rate** — dangerous direction: the true verdict requires an issue (anything but `compliant`), but every predicted verdict in the group is `compliant`.
- rate: 4.3%

- `technical_standards_compliance_documentation` — acceptable: ['non_compliant', 'insufficient_information'], predicted: compliant
  - **requirement:** "Provide documentation demonstrating understanding and application of all relevant AWWA, NHDES, OSHA, and EPA requirements."
  - **retrieved context (shown to the model):** "Past Performance: Granite State Tank Works has performed water tower inspection and cleaning contracts for three New Hampshire municipal water districts over the past four years, including one hospital campus water system. Attached are two CPARS entries from the past 3 years. Key [...truncated]"
  - **retrieved context (shown to the model):** "From: proposals@granitestatetankworks.com To: contractingofficer@va.gov Subject: Quote for RFQ 36C24126Q0704 - Water Tower Inspection & Maintenance Solicitation Number: 36C24126Q0704 Granite State Tank Works, LLC 118 Industrial Drive Nashua, NH 03060 (603) 555-0148 Unique Entity [...truncated]"
  - **model's evidence (what it chose to cite):** "Granite State Tank Works has reviewed the AWWA C652, D101, D102, and M42 standards along with NHDES administrative rules and will perform all work in accordance with these requirements."
  - **model's evidence (what it chose to cite):** "Our lead technician, James Boudreau, holds current OSHA-10 and OSHA-30 certifications... Mr. Boudreau also holds Confined Space Entry certification and has completed Fall Protection and Lockout/Tagout training."
  - **model's evidence (what it chose to cite):** "Granite State Tank Works will submit a site-specific Confined Space Entry plan and Lockout/Tagout procedures prior to mobilization. A fall protection plan is available... Our technicians follow standard SDS management procedures for all chemicals used on VA sites."
  - **model's reasoning:** The bidder explicitly states they have reviewed and will comply with the relevant AWWA standards and NHDES rules. Furthermore, they provide evidence of OSHA-compliant training and safety procedures (Confined Space, Fall Protection, Lockout/Tagout, and SDS management) for their personnel, demonstrating an understanding and application of the required regulatory frameworks.
  - **expected evidence (true_verdicts.json):** "Granite State Tank Works has reviewed the AWWA C652, D101, D102, and M42 standards along with NHDES administrative rules and will perform all work in accordance with these requirements."
  - **expected reasoning:** Application names specific AWWA standards and NHDES rules, but never mentions OSHA or EPA requirements at all -- two of the four named regulatory frameworks are entirely unaddressed.

**False-issue rate** — mirror direction: the true verdict is `compliant` only, but the pipeline raised an issue anyway.
- rate: 17.4%

- `amendment_acknowledgment` — acceptable: ['compliant'], predicted: non_compliant, citation: fuzzy match — worth a second look
  - **requirement:** "The offeror must acknowledge receipt of all amendments to the Solicitation, including their respective numbers and dates."
  - **retrieved context (shown to the model):** "From: proposals@granitestatetankworks.com To: contractingofficer@va.gov Subject: Quote for RFQ 36C24126Q0704 - Water Tower Inspection & Maintenance Solicitation Number: 36C24126Q0704 Granite State Tank Works, LLC 118 Industrial Drive Nashua, NH 03060 (603) 555-0148 Unique Entity [...truncated]"
  - **retrieved context (shown to the model):** "Past Performance: Granite State Tank Works has performed water tower inspection and cleaning contracts for three New Hampshire municipal water districts over the past four years, including one hospital campus water system. Attached are two CPARS entries from the past 3 years. Key [...truncated]"
  - **model's evidence (what it chose to cite):** "Granite State Tank Works, LLC agrees with all terms, conditions, and provisions included in the solicitation."
  - **model's reasoning:** The requirement explicitly mandates that the offeror must acknowledge receipt of all amendments, including their respective numbers and dates. The provided application does not mention any amendments, nor does it list any numbers or dates associated with them. The general statement agreeing to all terms and conditions does not satisfy the specific requirement to acknowledge receipt of amendments.
  - **expected evidence (true_verdicts.json):** none
  - **expected reasoning:** The solicitation's own amendment table is blank (no amendments have been issued), so there is nothing for the offeror to acknowledge; the conditional requirement is not triggered.

- group of 3 true topic(s) and 1 predicted requirement(s) (not a 1:1 match, so there is no single correct pairing between them):
  - true `healthcare_environmental_sanitation_training` — "Provide documentation of Healthcare Environmental Sanitation training." (acceptable: ['insufficient_information', 'non_compliant'])
      - **expected evidence (true_verdicts.json):** none
      - **expected reasoning:** Application never mentions Healthcare Environmental Sanitation training.
  - true `hospital_infection_control_compliance_documentation` — "Provide documentation demonstrating compliance with hospital Infection Control requirements." (acceptable: ['insufficient_information', 'non_compliant'])
      - **expected evidence (true_verdicts.json):** none
      - **expected reasoning:** Application never addresses hospital Infection Control requirements beyond having performed one hospital-campus contract.
  - true `past_performance_hospital_high_risk_environment` — "Provide evidence of performance in hospital or other high-risk environments." (acceptable: ['compliant'])
      - **expected evidence (true_verdicts.json):** "including one hospital campus water system"
      - **expected reasoning:** Application names one hospital campus water system among its past contracts.
  - **retrieved context (shown to the model):** "Past Performance: Granite State Tank Works has performed water tower inspection and cleaning contracts for three New Hampshire municipal water districts over the past four years, including one hospital campus water system. Attached are two CPARS entries from the past 3 years. Key [...truncated]"
  - **retrieved context (shown to the model):** "From: proposals@granitestatetankworks.com To: contractingofficer@va.gov Subject: Quote for RFQ 36C24126Q0704 - Water Tower Inspection & Maintenance Solicitation Number: 36C24126Q0704 Granite State Tank Works, LLC 118 Industrial Drive Nashua, NH 03060 (603) 555-0148 Unique Entity [...truncated]"
  - predicted verdicts in this group:
    - predicted [167ab4e9] "Provide evidence of performance in hospital or other high-risk environments, including documentation of Healthcare Environmental Sanitation training and compliance with hospital Infection Control requirements." — verdict: non_compliant
      - **model's evidence (what it chose to cite):** "Granite State Tank Works has performed water tower inspection and cleaning contracts for three New Hampshire municipal water districts over the past four years, including one hospital campus water system."
      - **model's evidence (what it chose to cite):** "Our lead technician, James Boudreau, holds current OSHA-10 and OSHA-30 certifications and a valid New Hampshire Water System Operator License. Mr. Boudreau also holds Confined Space Entry certification and has completed Fall Protection and Lockout/Tagout training."
      - **model's reasoning:** While the bidder mentions experience with a hospital campus water system, they failed to provide the required documentation of Healthcare Environmental Sanitation training or evidence of compliance with hospital Infection Control requirements. The provided certifications (OSHA, Water System Operator, Confined Space) do not satisfy the specific requirement for healthcare-specific sanitation and infection control training.

- `sds_management_procedures` — acceptable: ['compliant'], predicted: non_compliant
  - **requirement:** "Provide procedures for SDS management."
  - **retrieved context (shown to the model):** "Past Performance: Granite State Tank Works has performed water tower inspection and cleaning contracts for three New Hampshire municipal water districts over the past four years, including one hospital campus water system. Attached are two CPARS entries from the past 3 years. Key [...truncated]"
  - **retrieved context (shown to the model):** "From: proposals@granitestatetankworks.com To: contractingofficer@va.gov Subject: Quote for RFQ 36C24126Q0704 - Water Tower Inspection & Maintenance Solicitation Number: 36C24126Q0704 Granite State Tank Works, LLC 118 Industrial Drive Nashua, NH 03060 (603) 555-0148 Unique Entity [...truncated]"
  - **model's evidence (what it chose to cite):** "Our technicians follow standard SDS management procedures for all chemicals used on VA sites."
  - **model's reasoning:** The bidder states that they follow 'standard SDS management procedures' but fails to actually provide or describe what those procedures are. Simply stating that procedures are followed does not satisfy the requirement to provide the procedures themselves.
  - **expected evidence (true_verdicts.json):** "Our technicians follow standard SDS management procedures for all chemicals used on VA sites."
  - **expected reasoning:** Application states technicians follow standard SDS management procedures for all chemicals used on VA sites.

- group of 2 true topic(s) and 1 predicted requirement(s) (not a 1:1 match, so there is no single correct pairing between them):
  - true `confined_space_entry_certification` — "Provide Confined Space Entry certification." (acceptable: ['compliant'])
      - **expected evidence (true_verdicts.json):** "Mr. Boudreau also holds Confined Space Entry certification"
      - **expected reasoning:** Application states the lead technician holds Confined Space Entry certification.
  - true `confined_space_entry_plan` — "Provide an OSHA-compliant Confined Space Entry plan." (acceptable: ['insufficient_information', 'non_compliant'])
      - **expected evidence (true_verdicts.json):** "will submit a site-specific Confined Space Entry plan"
      - **expected reasoning:** Application commits to submitting a site-specific Confined Space Entry plan 'prior to mobilization' rather than providing it with the offer as requested.
  - **retrieved context (shown to the model):** "Past Performance: Granite State Tank Works has performed water tower inspection and cleaning contracts for three New Hampshire municipal water districts over the past four years, including one hospital campus water system. Attached are two CPARS entries from the past 3 years. Key [...truncated]"
  - **retrieved context (shown to the model):** "From: proposals@granitestatetankworks.com To: contractingofficer@va.gov Subject: Quote for RFQ 36C24126Q0704 - Water Tower Inspection & Maintenance Solicitation Number: 36C24126Q0704 Granite State Tank Works, LLC 118 Industrial Drive Nashua, NH 03060 (603) 555-0148 Unique Entity [...truncated]"
  - predicted verdicts in this group:
    - predicted [faea2590] "Provide Confined Space Entry certification for personnel and an OSHA-compliant Confined Space Entry plan." — verdict: non_compliant
      - **model's evidence (what it chose to cite):** "Granite State Tank Works will submit a site-specific Confined Space Entry plan and Lockout/Tagout procedures prior to mobilization."
      - **model's reasoning:** The requirement mandates that the bidder provide an OSHA-compliant Confined Space Entry plan as part of the application. The bidder explicitly states that they will submit this plan only 'prior to mobilization,' meaning it is not included in the current tender application.

**Unscored** — split/merge groups excluded from the matrix above (still counted in the two rates above):
- group 1:
  - true `structural_defect_capability_evidence` — "• Provide evidence of capability to identify structural defects, coating failures, corrosion, erosion, sanitation deficiencies, and contamination routes, supported by sample reports or prior work." (acceptable: ['non_compliant'])
  - true `structural_water_tower_inspection_experience` — "Provide evidence of demonstrated experience in structural water tower inspections." (acceptable: ['insufficient_information', 'non_compliant'])
  - predicted [8293d996] "Provide evidence of capability and experience in structural water tower inspections, including the identification of structural defects, coating failures, corrosion, erosion, sanitation deficiencies, and contamination routes, supported by sample reports or prior work." — verdict: insufficient_information
- group 2:
  - true `fall_protection_plan` — "Provide a comprehensive fall protection plan." (acceptable: ['insufficient_information', 'non_compliant'])
  - true `fall_protection_stairways_ladders_lockout_certifications` — "Provide certifications for Fall Protection, Stairways/Ladders, and Lockout/Tagout." (acceptable: ['insufficient_information', 'non_compliant'])
  - true `lockout_tagout_procedures` — "Provide equipment-specific Lockout/Tagout procedures." (acceptable: ['insufficient_information', 'non_compliant'])
  - true `tool_ladder_access_safety_evidence` — "• Provide evidence of safety controls for tools, ladders, cages, and access systems." (acceptable: ['non_compliant'])
  - predicted [66358425] "Provide certifications for Fall Protection, Stairways/Ladders, and Lockout/Tagout, along with equipment-specific Lockout/Tagout procedures, a comprehensive fall protection plan, and evidence of safety controls for tools, ladders, cages, and access systems." — verdict: non_compliant
- group 3:
  - true `inspection_cleaning_methodology` — "Provide a detailed inspection and cleaning methodology, including procedures, equipment, and verification steps." (acceptable: ['insufficient_information', 'non_compliant'])
  - true `work_plans_operational_procedures` — "Provide complete, technically sound work plans and operational procedures for reviewer evaluation." (acceptable: ['insufficient_information', 'non_compliant'])
  - predicted [9e5958de] "Provide a detailed, technically sound inspection and cleaning methodology, including operational procedures, equipment, and verification steps for reviewer evaluation." — verdict: non_compliant
- group 4:
  - true `healthcare_environmental_sanitation_training` — "Provide documentation of Healthcare Environmental Sanitation training." (acceptable: ['insufficient_information', 'non_compliant'])
  - true `hospital_infection_control_compliance_documentation` — "Provide documentation demonstrating compliance with hospital Infection Control requirements." (acceptable: ['insufficient_information', 'non_compliant'])
  - true `past_performance_hospital_high_risk_environment` — "Provide evidence of performance in hospital or other high-risk environments." (acceptable: ['compliant'])
  - predicted [167ab4e9] "Provide evidence of performance in hospital or other high-risk environments, including documentation of Healthcare Environmental Sanitation training and compliance with hospital Infection Control requirements." — verdict: non_compliant
- group 5:
  - true `confined_space_entry_certification` — "Provide Confined Space Entry certification." (acceptable: ['compliant'])
  - true `confined_space_entry_plan` — "Provide an OSHA-compliant Confined Space Entry plan." (acceptable: ['insufficient_information', 'non_compliant'])
  - predicted [faea2590] "Provide Confined Space Entry certification for personnel and an OSHA-compliant Confined Space Entry plan." — verdict: non_compliant

## Evidence

**Citation-verified rate** (evidence-level): fraction of evidence quotes actually located in application.txt.
- rate: 94.7% (2 unverified of 38)

**Evidence recall**: does the expected evidence span (from `true_verdicts.json`) show up somewhere in the requirement's retrieved chunks, before the verdict step chose what to cite? Topics never extracted as a requirement are excluded — that failure is already counted by requirement recall above.
- recall: 100.0% (18/18)
- missed:
  - none
