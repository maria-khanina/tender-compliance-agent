# Evaluation report

## Summary metrics

Machine-readable numbers for averaging across tenders -- every value here is explained in the sections below. `null` means the metric doesn't apply to this run (e.g. no verdict-only artifact present).

```json
{
  "requirement_recall": 1.0,
  "requirement_recall_matched": 24,
  "requirement_recall_total": 24,
  "requirement_precision": 0.75,
  "citation_verified_rate": 1.0,
  "is_mandatory_accuracy": 0.8333,
  "is_mandatory_scored": 24,
  "is_text_verifiable_accuracy": 0.875,
  "is_text_verifiable_scored": 24,
  "verdict_clean_match_count": 19,
  "verdict_accuracy": 0.7895,
  "false_compliant_rate": 0.1905,
  "false_issue_rate": 0.0,
  "evidence_citation_verified_rate": 0.8718,
  "evidence_recall": 1.0,
  "verdict_only_accuracy": null,
  "verdict_only_scored": null
}
```

## Requirement recall

For each `true_requirements.json` topic, did the pipeline extract something whose tender.txt citation overlaps the true one? A pure text-offset check, not a judgment of meaning — see coverage flags below for extractions that are technically "found" but sloppy.

**Recall: 100.0% (24/24)**

**Missed** (0) — no overlapping predicted requirement at all. "chunk check" is a mechanical (no-LLM) re-chunking of the source document: whether this topic's matching text ever appeared whole in one chunk handed to the extraction model, or was split across chunks.
- none

**Over-split** (2) — one true topic extracted as several separate predicted requirements:
- true `cylinder_tracking_plan_delivery` — "5.2. The contractor shall submit an innovative plan with their proposal for tracking medical gas cylinders being delivered to and from the ordering activity. ... 5.2.1. The cylinder tracking plan shall include, but is not limited to: a) Method used for data entry and extraction (i.e. web-based portal, Microsoft Excel spreadsheet, SharePoint, email, etc.); b) Mechanism for data entry (i.e. barcode scanning, handwriting serial numbers, photos, etc.); c) How and when Government will be able to extract data; d) What type of data will be entered and stored; e) Limits on access to Government employees, if applicable; f) Any technology, equipment, software, etc. that requires connection to the Government network, if applicable; and g) Any other pertinent information related to the cylinder tracking plan ... 5.2.2. If the contractor has an impending tracking system or one that is not yet fully operational but would like to submit as part of their proposal, the contractor shall include a timeline for implementation which must coincide with the phase-in timeline as described in paragraph 4.1." split into 3 predicted requirements:
  - predicted [17b50972] "The cylinder tracking plan shall include, but is not limited to, data entry and extraction methods, data mechanisms, data extraction timing, types of data stored, access limits, network connection technology, and all other items listed under paragraph 5.2.1." — verdict: non_compliant
  - predicted [52463513] "The contractor shall submit an innovative plan with their proposal for tracking medical gas cylinders being delivered to and from the ordering activity at no additional cost to the Government." — verdict: compliant
  - predicted [aba86746] "If the contractor proposes an impending or not yet fully operational tracking system, they must include an implementation timeline coinciding with the phase-in timeline, and such systems not operational by contract transition conclusion shall not be submitted." — verdict: compliant
- true `past_performance_reference_provided` — "ii. Past Performance: In response to this factor, offerors shall provide past performance references for work performed within the past three (3) years that is directly relevant to the complexity, size, and scope of this requirement. Offerors, at minimum, shall list: • Contract or project number and title • Period of performance • Dollar Value • Brief description / Scope • Name of Agency / Facility • Point of Contact: Include name, title, phone number, and e- mail address" split into 2 predicted requirements:
  - predicted [22b18b3e] "Brief description / Scope" — verdict: compliant
  - predicted [833793de] "Offerors shall provide past performance references for work performed within the past three years relevant in complexity, size, and scope, including project number/title, period of performance, dollar value, agency/facility name, and point of contact details." — verdict: compliant, citation: fuzzy match — worth a second look

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
- rate: 75.0%
- unexplained (9) — the model recognized these as requirements, but they don't match any true requirement. "closest true topic" is a mechanical (no-LLM) embedding-similarity lookup against every true topic's description; "dedup visibility" checks whether dedup's own cosine pre-filter would have clustered this candidate with whatever predicted requirement DID match that topic -- i.e. whether the dedup LLM call ever had a chance to compare them:
  - predicted [09e9b8f5] "Cylinder tracking reports shall include perpetual delivery, pick-up, and location data per cylinder, and any other helpful cylinder tracking reports."
    - **similarity check:** closest true topic: `cylinder_tracking_plan_delivery` (cosine=0.72); vs matched predicted [17b50972]: cosine=0.70 (>= dedup threshold 0.6) -> would likely have been clustered together and compared by the dedup LLM call
  - predicted [24794e46] "It is requested to separate documents as described in the solicitation instructions."
    - **similarity check:** closest true topic: `technical_continuity_of_operations` (cosine=0.59); vs matched predicted [f9c6f029]: cosine=0.57 (< dedup threshold 0.6) -> dedup's cosine pre-filter would NOT have clustered these -- the dedup LLM call never saw them side by side
  - predicted [441ebae7] "The quote shall contain the vendor’s best terms from a price standpoint."
    - **similarity check:** closest true topic: `quote_identification_and_solicitation_number` (cosine=0.68); vs matched predicted [142c5932]: cosine=0.68 (>= dedup threshold 0.6) -> would likely have been clustered together and compared by the dedup LLM call
  - predicted [4b48953b] "Offeror shall use Attachment B as the basis for their total bid price."
    - **similarity check:** closest true topic: `quote_identification_and_solicitation_number` (cosine=0.64); vs matched predicted [142c5932]: cosine=0.60 (>= dedup threshold 0.6) -> would likely have been clustered together and compared by the dedup LLM call
  - predicted [72a1fa52] "Files must be readable using Microsoft Office 2007 or later, specifically Word (Doc or Docx) and Excel."
    - **similarity check:** closest true topic: `cylinder_tracking_plan_delivery` (cosine=0.55); vs matched predicted [17b50972]: cosine=0.60 (< dedup threshold 0.6) -> dedup's cosine pre-filter would NOT have clustered these -- the dedup LLM call never saw them side by side
  - predicted [84d9ed07] "Files in Adobe PDF Files – when scanning documents, scanner resolution should be set at least 200 dots per inch (dpi)."
    - **similarity check:** closest true topic: `cylinder_tracking_plan_delivery` (cosine=0.48); vs matched predicted [17b50972]: cosine=0.49 (< dedup threshold 0.6) -> dedup's cosine pre-filter would NOT have clustered these -- the dedup LLM call never saw them side by side
  - predicted [906aa4be] "Quoters shall email their quotes electronically to emanuel.nevarez@va.gov with the solicitation number in the subject line."
    - **similarity check:** closest true topic: `quote_identification_and_solicitation_number` (cosine=0.69); vs matched predicted [142c5932]: cosine=0.66 (>= dedup threshold 0.6) -> would likely have been clustered together and compared by the dedup LLM call
  - predicted [93b4a8ec] "Cost reports shall include actual billing data, average cost per delivery, average cost per week/month/year per medical gas, and other cost-related reports."
    - **similarity check:** closest true topic: `cylinder_tracking_plan_delivery` (cosine=0.63); vs matched predicted [52463513]: cosine=0.66 (>= dedup threshold 0.6) -> would likely have been clustered together and compared by the dedup LLM call
  - predicted [c8e9dd19] "Usage reports shall include actual deliveries for any set of dates, average deliveries per week/month/year, average deliveries per week/month/year per gas type, and other usage-related reports."
    - **similarity check:** closest true topic: `cylinder_tracking_plan_delivery` (cosine=0.63); vs matched predicted [52463513]: cosine=0.63 (>= dedup threshold 0.6) -> would likely have been clustered together and compared by the dedup LLM call

## Coverage flags

Clean 1:1 matches (recall counted them as found) whose citations don't fully overlap in length, split by which side is off. Over-split/over-merge/tangled matches are excluded here -- their predicted fragments are inherently partial by construction, already shown in the recall breakdown above.

**Requirements captured with extra text** (0) — the predicted citation is padded beyond the true one:
- none

**Requirements captured incompletely** (2) — the predicted citation misses part of the true one:
- predicted [844810f8] is contained in true `technical_cylinder_management_innovation` — 75.8%:
    predicted: "Offerors shall demonstrate the innovative use of a cylinder tracking and management system."
    true: "c. Cylinder Management: Demonstrate the innovative use of cylinder tracking and management system."

- predicted [8d199097] is contained in true `sdvosb_vosb_certification_status_at_submission` — 44.9%:
    predicted: "Service-Disabled Veteran-Owned and Veteran-Owned Small Businesses must be registered and certified with the SBA upon submission and listed in the SBA certification database at the time of offer and award."
    true: "Veterans Involvement : Eligible and certified service-disabled Veteran- owned small businesses offerors will receive full credit, and offerors qualifying as Veteran-owned small businesses will receive partial credit for the certified Service-Disabled Veteran-Owned and Veteran-Owned Small Business Status evaluation factor. To receive credit, an offeror must be listed at the time of submission of offers and at time of award, as a certified SDVOSB/VOSB in the SBA certification database on the SBA Veteran Small Business Certification Program portal at https://veterans.certify.sba.gov/"

## is_mandatory accuracy

For each clean or one-to-many match (tangled groups excluded — there's no single "one" to compare against), does `is_mandatory` agree with the true value? A one-to-many group counts as correct only if every member on the "many" side agrees with the "one".

**Accuracy: 83.3% (24 groups)**

Mismatched:
- true: `amendment_acknowledgment`=False; predicted: `f0ca21bb`=True — "b. The contractor shall acknowledge all amendments to the solicitation that may be issued."
- true: `sdvosb_vosb_certification_status_at_submission`=False; predicted: `8d199097`=True — "Veterans Involvement : Eligible and certified service-disabled Veteran- owned small businesses offerors will receive full credit, and offerors qualifying as Veteran-owned small businesses will receive partial credit for the certified Service-Disabled Veteran-Owned and Veteran-Owned Small Business Status evaluation factor. To receive credit, an offeror must be listed at the time of submission of offers and at time of award, as a certified SDVOSB/VOSB in the SBA certification database on the SBA Veteran Small Business Certification Program portal at https://veterans.certify.sba.gov/"
- true: `sdvosb_subcontractor_disclosure_if_electing_credit`=False; predicted: `3e3754b8`=True — "If an Offeror is a large business and proposes to use certified SDVOSBs or VOSBs as subcontractors and elects to receive evaluation consideration under this factor, they must indicate their intention along with stating in their proposal the names of the certified SDVOSB and VOSB with whom they intend to subcontract, the description of SDVOSB/VOSB services/supplies, and approximate dollar values of proposed subcontractors."
- true: `subcontracting_limitations_breakdown`=False; predicted: `63fcedf7`=True — "Limitations on Subcontracting: In response to this factor (when applicable) Offerors shall submit a breakdown of the work identified in the Statement of Work and tasks associated with Contract Administration. The offer shall identify which work will be performed by the prime contractor, any similarly situated entity, and any other subcontractors."

## is_text_verifiable accuracy

For each clean or one-to-many match (tangled groups excluded), does `is_text_verifiable` agree with the true value (all-or-nothing on the "many" side, same rule as is_mandatory above)? A wrong `false` here means the pipeline skips verdict generation for a requirement that should get one.

**Accuracy: 87.5% (24 groups)**

Mismatched:
- true: `sam_registration_active_at_offer`=False; predicted: `19de3dba`=True — "Offerors shall be registered and active at System for Award Management (SAM) at time of offer."
- true: `technical_medical_gas_regulatory_proof`=False; predicted: `453cb8b2`=True — "d. Provide proof that all medical gases conform to the most recent specifications prescribed in the United States Pharmacopoeia (USP) and National Formulary, the contractor, medical gas manufacturers and fillers of medical gases utilized in conjunction with this contract are registered with the U.S. Food and Drug Administration (FDA), and all medical gases shall be manufactured, processed, packaged, transported, and stored to the FDA’s CGMP regulations and Title 21, of the Code of Federal Regulations for labeling."
- true: `sdvosb_vosb_certification_status_at_submission`=False; predicted: `8d199097`=True — "Veterans Involvement : Eligible and certified service-disabled Veteran- owned small businesses offerors will receive full credit, and offerors qualifying as Veteran-owned small businesses will receive partial credit for the certified Service-Disabled Veteran-Owned and Veteran-Owned Small Business Status evaluation factor. To receive credit, an offeror must be listed at the time of submission of offers and at time of award, as a certified SDVOSB/VOSB in the SBA certification database on the SBA Veteran Small Business Certification Program portal at https://veterans.certify.sba.gov/"

## Verdict accuracy

The confusion matrix covers only clean 1:1 matches — split/merge groups have no single pair to plot, but still count in the two rates below.

Clean matches scored: 19

| true \ pipeline said | `compliant` | `non_compliant` | `contradictory` | `insufficient_information` |
|---|---|---|---|---|
| `compliant` | 10 | 1 | 0 | 0 |
| `non_compliant` | 0 | 2 | 1 | 0 |
| `contradictory` | 1 | 1 | 0 | 0 |
| `insufficient_information` | 2 | 0 | 0 | 1 |

**Mismatched clean matches** — every off-diagonal cell above, in full: the full context retrieved and shown to the model, what it chose to cite from that context, and its reasoning ("model's ..."), next to what `true_verdicts.json` expects ("expected ...").

- `project_management_plan_submitted` — acceptable: ['insufficient_information'], predicted: compliant
  - **requirement:** "The contractor shall submit a Project Management Plan (PMP) demonstrating scope, schedule, and service level understanding, including communications/task matrix, deliverable responsibilities, schedules, task estimates, progress tracking, and problem-resolution approaches."
  - **retrieved context (shown to the model):** "Cylinder Management: As described above under Cylinder Tracking, our barcode-based tracking system represents an innovative use of cylinder tracking and management technology across the ordering activity network. Regulatory Compliance: All medical gases supplied under this contra [...truncated]"
  - **retrieved context (shown to the model):** "Price Schedule: Attached is our fully priced Schedule of Items (Attachment C), covering all 1,331 line items across all five ordering periods. Northern Plains Medical Gases agrees to hold the prices in this offer firm for 90 calendar days from the date specified for receipt of of [...truncated]"
  - **retrieved context (shown to the model):** "We do not currently operate a system for tracking medical gas cylinders within an ordering activity's facility after delivery, and are therefore not submitting a facility-side tracking plan with this proposal. Reporting Capabilities: Northern Plains Medical Gases will provide on- [...truncated]"
  - **retrieved context (shown to the model):** "Veterans Involvement / Limitations on Subcontracting: Northern Plains Medical Gases will perform 100% of the work identified in the Statement of Work and Contract Administration with its own personnel and equipment; no subcontractors, similarly situated entities, or other perform [...truncated]"
  - **retrieved context (shown to the model):** "From: contracts@northernplainsgases.com To: emanuel.nevarez@va.gov Subject: Quote for Solicitation 36C26326Q0197 - Medical Cylinder Gases IDIQ Solicitation Number: 36C26326Q0197 Northern Plains Medical Gases, LLC 2200 19th Ave N Fargo, ND 58102 (701) 555-0184 Unique Entity Identi [...truncated]"
  - **model's evidence (what it chose to cite):** "Project Management Plan: Our Project Management Plan assigns a single point of contact, Dana Whitfield, who will coordinate onboarding, task order communications, and identify and delineate the roles and responsibilities of our dispatch and billing staff. Dana Whitfield is also responsible for ensuring contract deliverables are provided on time. A preliminary delivery, install, and user acceptance schedule is included as Appendix 1, showing task dependencies and an estimate of how much time each critical task is expected to take through the first 60 days of performance."
  - **model's reasoning:** The bidder submits a Project Management Plan that addresses the scope, schedule, and service level understanding. It includes a communications and task matrix (assigning a single point of contact for onboarding and communications, and delineating dispatch and billing staff roles), deliverable responsibilities (ensuring deliverables on time), schedules (delivery, install, and user acceptance schedule), and task estimates (showing time expected for critical tasks through the first 60 days).
  - **expected evidence (true_verdicts.json):** "Our Project Management Plan assigns a single point of contact, Dana Whitfield, who will coordinate onboarding, task order communications, and identify and delineate the roles and responsibilities of our dispatch and billing staff. Dana Whitfield is also responsible for ensuring contract deliverables are provided on time. A preliminary delivery, install, and user acceptance schedule is included as Appendix 1, showing task dependencies and an estimate of how much time each critical task is expected to take through the first 60 days of performance."
  - **expected reasoning:** Application's Project Management Plan section addresses the communications/task matrix, the responsible individual, and a preliminary schedule with time estimates, but never describes an approach to identifying warning signs of potential project problems and their resolution process, so the PMP as described is missing one required element.

- `quote_identification_and_solicitation_number` — acceptable: ['compliant', 'insufficient_information'], predicted: non_compliant, citation: fuzzy match — worth a second look
  - **requirement:** "The quote must identify the offeror, include the solicitation number, and be complete, self-sufficient, and respond directly to requirements."
  - **retrieved context (shown to the model):** "From: contracts@northernplainsgases.com To: emanuel.nevarez@va.gov Subject: Quote for Solicitation 36C26326Q0197 - Medical Cylinder Gases IDIQ Solicitation Number: 36C26326Q0197 Northern Plains Medical Gases, LLC 2200 19th Ave N Fargo, ND 58102 (701) 555-0184 Unique Entity Identi [...truncated]"
  - **retrieved context (shown to the model):** "Veterans Involvement / Limitations on Subcontracting: Northern Plains Medical Gases will perform 100% of the work identified in the Statement of Work and Contract Administration with its own personnel and equipment; no subcontractors, similarly situated entities, or other perform [...truncated]"
  - **retrieved context (shown to the model):** "Price Schedule: Attached is our fully priced Schedule of Items (Attachment C), covering all 1,331 line items across all five ordering periods. Northern Plains Medical Gases agrees to hold the prices in this offer firm for 90 calendar days from the date specified for receipt of of [...truncated]"
  - **retrieved context (shown to the model):** "Cylinder Management: As described above under Cylinder Tracking, our barcode-based tracking system represents an innovative use of cylinder tracking and management technology across the ordering activity network. Regulatory Compliance: All medical gases supplied under this contra [...truncated]"
  - **retrieved context (shown to the model):** "We do not currently operate a system for tracking medical gas cylinders within an ordering activity's facility after delivery, and are therefore not submitting a facility-side tracking plan with this proposal. Reporting Capabilities: Northern Plains Medical Gases will provide on- [...truncated]"
  - **model's evidence (what it chose to cite):** "Note: Item pricing for four specialty gas mixture line items in the Schedule of Items remains pending confirmation from our upstream supplier and will be provided by change order shortly after award."
  - **model's reasoning:** The requirement states that the quote must be complete, self-sufficient, and respond directly to requirements. However, the quote states that pricing for four specialty gas mixture line items remains pending confirmation and will be provided after award, making the quote incomplete and not self-sufficient.
  - **expected evidence (true_verdicts.json):** "Subject: Quote for Solicitation 36C26326Q0197 - Medical Cylinder Gases IDIQ"
  - **expected reasoning:** The quote header identifies the offeror (Northern Plains Medical Gases, LLC, with address and UEI) and states the solicitation number.

- `technical_continuity_of_operations` — acceptable: ['contradictory'], predicted: compliant
  - **requirement:** "Offeror shall provide procedures or documentation demonstrating the ability to navigate emergency situations, shortages, and supply chain interruptions."
  - **retrieved context (shown to the model):** "We do not currently operate a system for tracking medical gas cylinders within an ordering activity's facility after delivery, and are therefore not submitting a facility-side tracking plan with this proposal. Reporting Capabilities: Northern Plains Medical Gases will provide on- [...truncated]"
  - **retrieved context (shown to the model):** "Cylinder Management: As described above under Cylinder Tracking, our barcode-based tracking system represents an innovative use of cylinder tracking and management technology across the ordering activity network. Regulatory Compliance: All medical gases supplied under this contra [...truncated]"
  - **retrieved context (shown to the model):** "Price Schedule: Attached is our fully priced Schedule of Items (Attachment C), covering all 1,331 line items across all five ordering periods. Northern Plains Medical Gases agrees to hold the prices in this offer firm for 90 calendar days from the date specified for receipt of of [...truncated]"
  - **retrieved context (shown to the model):** "From: contracts@northernplainsgases.com To: emanuel.nevarez@va.gov Subject: Quote for Solicitation 36C26326Q0197 - Medical Cylinder Gases IDIQ Solicitation Number: 36C26326Q0197 Northern Plains Medical Gases, LLC 2200 19th Ave N Fargo, ND 58102 (701) 555-0184 Unique Entity Identi [...truncated]"
  - **retrieved context (shown to the model):** "Veterans Involvement / Limitations on Subcontracting: Northern Plains Medical Gases will perform 100% of the work identified in the Statement of Work and Contract Administration with its own personnel and equipment; no subcontractors, similarly situated entities, or other perform [...truncated]"
  - **model's evidence (what it chose to cite):** "Continuity of Operations: In the event of a supply-chain interruption, we maintain backup supply agreements with two independent industrial gas fillers and can reroute deliveries from our Sioux Falls depot within 24 hours of a disruption at any other location."
  - **model's reasoning:** The bidder explicitly provides procedures and documentation regarding their ability to handle supply chain interruptions and shortages, detailing backup supply agreements and rerouting capabilities from their Sioux Falls depot within 24 hours.
  - **expected evidence (true_verdicts.json):** "All specialty and bulk medical gases offered under this contract are sourced through an exclusive regional supply agreement with a single filler, Prairie Industrial Gas Co., which ensures consistent quality control across all deliveries."
  - **expected evidence (true_verdicts.json):** "Continuity of Operations: In the event of a supply-chain interruption, we maintain backup supply agreements with two independent industrial gas fillers and can reroute deliveries from our Sioux Falls depot within 24 hours of a disruption at any other location."
  - **expected reasoning:** The Depots and Delivery section states that all specialty and bulk gases are sourced through an exclusive agreement with a single filler, while the Continuity of Operations section states the opposite -- that backup supply agreements exist with two independent fillers. An exclusive single-supplier arrangement and a two-supplier backup arrangement cannot both be true.

- `phase_in_strategy_submitted` — acceptable: ['insufficient_information'], predicted: compliant
  - **requirement:** "Offerors shall provide a phase-in strategy including a Project Communications Plan with staff roles and contact info, an Implementation Plan, and a Delivery Plan with milestones meeting the contract effective date or 60-day requirement."
  - **retrieved context (shown to the model):** "Price Schedule: Attached is our fully priced Schedule of Items (Attachment C), covering all 1,331 line items across all five ordering periods. Northern Plains Medical Gases agrees to hold the prices in this offer firm for 90 calendar days from the date specified for receipt of of [...truncated]"
  - **retrieved context (shown to the model):** "Cylinder Management: As described above under Cylinder Tracking, our barcode-based tracking system represents an innovative use of cylinder tracking and management technology across the ordering activity network. Regulatory Compliance: All medical gases supplied under this contra [...truncated]"
  - **retrieved context (shown to the model):** "We do not currently operate a system for tracking medical gas cylinders within an ordering activity's facility after delivery, and are therefore not submitting a facility-side tracking plan with this proposal. Reporting Capabilities: Northern Plains Medical Gases will provide on- [...truncated]"
  - **retrieved context (shown to the model):** "Veterans Involvement / Limitations on Subcontracting: Northern Plains Medical Gases will perform 100% of the work identified in the Statement of Work and Contract Administration with its own personnel and equipment; no subcontractors, similarly situated entities, or other perform [...truncated]"
  - **retrieved context (shown to the model):** "From: contracts@northernplainsgases.com To: emanuel.nevarez@va.gov Subject: Quote for Solicitation 36C26326Q0197 - Medical Cylinder Gases IDIQ Solicitation Number: 36C26326Q0197 Northern Plains Medical Gases, LLC 2200 19th Ave N Fargo, ND 58102 (701) 555-0184 Unique Entity Identi [...truncated]"
  - **model's evidence (what it chose to cite):** "Our Project Management Plan assigns a single point of contact, Dana Whitfield, who will coordinate onboarding, task order communications, and identify and delineate the roles and responsibilities of our dispatch and billing staff. Dana Whitfield is also responsible for ensuring contract deliverables are provided on time. A preliminary delivery, install, and user acceptance schedule is included as Appendix 1, showing task dependencies and an estimate of how much time each critical task is expected to take through the first 60 days of performance."
  - **model's evidence (what it chose to cite):** "Our phase-in strategy includes a Project Communications Plan identifying Dana Whitfield as the point of contact for all phase-in and ongoing contract communications, along with the roles of our dispatch and billing staff who will support this contract through the period of performance. We will also submit an Implementation Plan describing depot staffing and cylinder-inventory buildup during the phase-in period."
  - **model's reasoning:** The bidder provides a phase-in strategy that encompasses a Project Communications Plan detailing staff roles (dispatch and billing) and contact information (Dana Whitfield), an Implementation Plan describing depot staffing and inventory buildup, and a Delivery Plan with milestones spanning the first 60 days of performance, thus fully satisfying the requirement.
  - **expected evidence (true_verdicts.json):** "Our phase-in strategy includes a Project Communications Plan identifying Dana Whitfield as the point of contact for all phase-in and ongoing contract communications, along with the roles of our dispatch and billing staff who will support this contract through the period of performance. We will also submit an Implementation Plan describing depot staffing and cylinder-inventory buildup during the phase-in period."
  - **expected reasoning:** Application's phase-in strategy addresses a Project Communications Plan and an Implementation Plan, but never mentions a Delivery Plan or any milestone dates/timelines demonstrating the ability to meet the effective date or the 60-calendar-day requirement, so one of the three required components is missing.

**False-compliant rate** — dangerous direction: the true verdict requires an issue (anything but `compliant`), but every predicted verdict in the group is `compliant`.
- rate: 19.0%

- `project_management_plan_submitted` — acceptable: ['insufficient_information'], predicted: compliant
  - **requirement:** "The contractor shall submit a Project Management Plan (PMP) demonstrating scope, schedule, and service level understanding, including communications/task matrix, deliverable responsibilities, schedules, task estimates, progress tracking, and problem-resolution approaches."
  - **retrieved context (shown to the model):** "Cylinder Management: As described above under Cylinder Tracking, our barcode-based tracking system represents an innovative use of cylinder tracking and management technology across the ordering activity network. Regulatory Compliance: All medical gases supplied under this contra [...truncated]"
  - **retrieved context (shown to the model):** "Price Schedule: Attached is our fully priced Schedule of Items (Attachment C), covering all 1,331 line items across all five ordering periods. Northern Plains Medical Gases agrees to hold the prices in this offer firm for 90 calendar days from the date specified for receipt of of [...truncated]"
  - **retrieved context (shown to the model):** "We do not currently operate a system for tracking medical gas cylinders within an ordering activity's facility after delivery, and are therefore not submitting a facility-side tracking plan with this proposal. Reporting Capabilities: Northern Plains Medical Gases will provide on- [...truncated]"
  - **retrieved context (shown to the model):** "Veterans Involvement / Limitations on Subcontracting: Northern Plains Medical Gases will perform 100% of the work identified in the Statement of Work and Contract Administration with its own personnel and equipment; no subcontractors, similarly situated entities, or other perform [...truncated]"
  - **retrieved context (shown to the model):** "From: contracts@northernplainsgases.com To: emanuel.nevarez@va.gov Subject: Quote for Solicitation 36C26326Q0197 - Medical Cylinder Gases IDIQ Solicitation Number: 36C26326Q0197 Northern Plains Medical Gases, LLC 2200 19th Ave N Fargo, ND 58102 (701) 555-0184 Unique Entity Identi [...truncated]"
  - **model's evidence (what it chose to cite):** "Project Management Plan: Our Project Management Plan assigns a single point of contact, Dana Whitfield, who will coordinate onboarding, task order communications, and identify and delineate the roles and responsibilities of our dispatch and billing staff. Dana Whitfield is also responsible for ensuring contract deliverables are provided on time. A preliminary delivery, install, and user acceptance schedule is included as Appendix 1, showing task dependencies and an estimate of how much time each critical task is expected to take through the first 60 days of performance."
  - **model's reasoning:** The bidder submits a Project Management Plan that addresses the scope, schedule, and service level understanding. It includes a communications and task matrix (assigning a single point of contact for onboarding and communications, and delineating dispatch and billing staff roles), deliverable responsibilities (ensuring deliverables on time), schedules (delivery, install, and user acceptance schedule), and task estimates (showing time expected for critical tasks through the first 60 days).
  - **expected evidence (true_verdicts.json):** "Our Project Management Plan assigns a single point of contact, Dana Whitfield, who will coordinate onboarding, task order communications, and identify and delineate the roles and responsibilities of our dispatch and billing staff. Dana Whitfield is also responsible for ensuring contract deliverables are provided on time. A preliminary delivery, install, and user acceptance schedule is included as Appendix 1, showing task dependencies and an estimate of how much time each critical task is expected to take through the first 60 days of performance."
  - **expected reasoning:** Application's Project Management Plan section addresses the communications/task matrix, the responsible individual, and a preliminary schedule with time estimates, but never describes an approach to identifying warning signs of potential project problems and their resolution process, so the PMP as described is missing one required element.

- `technical_continuity_of_operations` — acceptable: ['contradictory'], predicted: compliant
  - **requirement:** "Offeror shall provide procedures or documentation demonstrating the ability to navigate emergency situations, shortages, and supply chain interruptions."
  - **retrieved context (shown to the model):** "We do not currently operate a system for tracking medical gas cylinders within an ordering activity's facility after delivery, and are therefore not submitting a facility-side tracking plan with this proposal. Reporting Capabilities: Northern Plains Medical Gases will provide on- [...truncated]"
  - **retrieved context (shown to the model):** "Cylinder Management: As described above under Cylinder Tracking, our barcode-based tracking system represents an innovative use of cylinder tracking and management technology across the ordering activity network. Regulatory Compliance: All medical gases supplied under this contra [...truncated]"
  - **retrieved context (shown to the model):** "Price Schedule: Attached is our fully priced Schedule of Items (Attachment C), covering all 1,331 line items across all five ordering periods. Northern Plains Medical Gases agrees to hold the prices in this offer firm for 90 calendar days from the date specified for receipt of of [...truncated]"
  - **retrieved context (shown to the model):** "From: contracts@northernplainsgases.com To: emanuel.nevarez@va.gov Subject: Quote for Solicitation 36C26326Q0197 - Medical Cylinder Gases IDIQ Solicitation Number: 36C26326Q0197 Northern Plains Medical Gases, LLC 2200 19th Ave N Fargo, ND 58102 (701) 555-0184 Unique Entity Identi [...truncated]"
  - **retrieved context (shown to the model):** "Veterans Involvement / Limitations on Subcontracting: Northern Plains Medical Gases will perform 100% of the work identified in the Statement of Work and Contract Administration with its own personnel and equipment; no subcontractors, similarly situated entities, or other perform [...truncated]"
  - **model's evidence (what it chose to cite):** "Continuity of Operations: In the event of a supply-chain interruption, we maintain backup supply agreements with two independent industrial gas fillers and can reroute deliveries from our Sioux Falls depot within 24 hours of a disruption at any other location."
  - **model's reasoning:** The bidder explicitly provides procedures and documentation regarding their ability to handle supply chain interruptions and shortages, detailing backup supply agreements and rerouting capabilities from their Sioux Falls depot within 24 hours.
  - **expected evidence (true_verdicts.json):** "All specialty and bulk medical gases offered under this contract are sourced through an exclusive regional supply agreement with a single filler, Prairie Industrial Gas Co., which ensures consistent quality control across all deliveries."
  - **expected evidence (true_verdicts.json):** "Continuity of Operations: In the event of a supply-chain interruption, we maintain backup supply agreements with two independent industrial gas fillers and can reroute deliveries from our Sioux Falls depot within 24 hours of a disruption at any other location."
  - **expected reasoning:** The Depots and Delivery section states that all specialty and bulk gases are sourced through an exclusive agreement with a single filler, while the Continuity of Operations section states the opposite -- that backup supply agreements exist with two independent fillers. An exclusive single-supplier arrangement and a two-supplier backup arrangement cannot both be true.

- group of 1 true topic(s) and 2 predicted requirement(s) (not a 1:1 match, so there is no single correct pairing between them):
  - true `past_performance_reference_provided` — "ii. Past Performance: In response to this factor, offerors shall provide past performance references for work performed within the past three (3) years that is directly relevant to the complexity, size, and scope of this requirement. Offerors, at minimum, shall list: • Contract or project number and title • Period of performance • Dollar Value • Brief description / Scope • Name of Agency / Facility • Point of Contact: Include name, title, phone number, and e- mail address" (acceptable: ['insufficient_information'])
      - **expected evidence (true_verdicts.json):** "Contract/Project: VISN 23 Medical Gas Supply IDIQ, Fargo VA Medical Center. Period of Performance: 2021-2024. Description: cylinder gas delivery and rental services for a multi-building VA medical campus. Agency/Facility: Department of Veterans Affairs, Fargo VA Medical Center. Point of Contact: Marcus Ellingson, Contracting Officer Representative, (701) 555-0122, marcus.ellingson@va.gov."
      - **expected reasoning:** Application provides one past performance reference with contract identification, period of performance, description, agency, and point of contact, but never states a dollar value for the contract, so the reference is missing one of the required elements.
  - **retrieved context (shown to the model):** "Price Schedule: Attached is our fully priced Schedule of Items (Attachment C), covering all 1,331 line items across all five ordering periods. Northern Plains Medical Gases agrees to hold the prices in this offer firm for 90 calendar days from the date specified for receipt of of [...truncated]"
  - **retrieved context (shown to the model):** "We do not currently operate a system for tracking medical gas cylinders within an ordering activity's facility after delivery, and are therefore not submitting a facility-side tracking plan with this proposal. Reporting Capabilities: Northern Plains Medical Gases will provide on- [...truncated]"
  - **retrieved context (shown to the model):** "Cylinder Management: As described above under Cylinder Tracking, our barcode-based tracking system represents an innovative use of cylinder tracking and management technology across the ordering activity network. Regulatory Compliance: All medical gases supplied under this contra [...truncated]"
  - **retrieved context (shown to the model):** "Veterans Involvement / Limitations on Subcontracting: Northern Plains Medical Gases will perform 100% of the work identified in the Statement of Work and Contract Administration with its own personnel and equipment; no subcontractors, similarly situated entities, or other perform [...truncated]"
  - **retrieved context (shown to the model):** "From: contracts@northernplainsgases.com To: emanuel.nevarez@va.gov Subject: Quote for Solicitation 36C26326Q0197 - Medical Cylinder Gases IDIQ Solicitation Number: 36C26326Q0197 Northern Plains Medical Gases, LLC 2200 19th Ave N Fargo, ND 58102 (701) 555-0184 Unique Entity Identi [...truncated]"
  - predicted verdicts in this group:
    - predicted [22b18b3e] "Brief description / Scope" — verdict: compliant
      - **model's evidence (what it chose to cite):** "Attached is our fully priced Schedule of Items (Attachment C), covering all 1,331 line items across all five ordering periods."
      - **model's reasoning:** The requirement asks for a brief description and scope. The bidder's application clearly provides a price schedule and scope details covering all line items and ordering periods, satisfying the general scope requirement.
    - predicted [833793de] "Offerors shall provide past performance references for work performed within the past three years relevant in complexity, size, and scope, including project number/title, period of performance, dollar value, agency/facility name, and point of contact details." — verdict: compliant, citation: fuzzy match — worth a second look
      - **model's evidence (what it chose to cite):** "Past Performance: Contract/Project: VISN 23 Medical Gas Supply IDIQ, Fargo VA Medical Center. Period of Performance: 2021-2024. Description: cylinder gas delivery and rental services for a multi-building VA medical campus. Agency/Facility: Department of Veterans Affairs, Fargo VA Medical Center. Point of Contact: Marcus Ellingson, Contracting Officer Representative, (701) 555-0122, marcus.ellingson@va.gov."
      - **model's reasoning:** The bidder provided past performance references under the "Past Performance" section in excerpt [3], which includes the project number/title (VISN 23 Medical Gas Supply IDIQ, Fargo VA Medical Center), period of performance (2021-2024), dollar value/complexity and scope description (cylinder gas delivery and rental services for a multi-building VA medical campus), agency/facility name (Department of Veterans Affairs, Fargo VA Medical Center), and point of contact details (Marcus Ellingson, Contracting Officer Representative, (701) 555-0122, marcus.ellingson@va.gov). This satisfies all criteria for the past performance requirement.

- `phase_in_strategy_submitted` — acceptable: ['insufficient_information'], predicted: compliant
  - **requirement:** "Offerors shall provide a phase-in strategy including a Project Communications Plan with staff roles and contact info, an Implementation Plan, and a Delivery Plan with milestones meeting the contract effective date or 60-day requirement."
  - **retrieved context (shown to the model):** "Price Schedule: Attached is our fully priced Schedule of Items (Attachment C), covering all 1,331 line items across all five ordering periods. Northern Plains Medical Gases agrees to hold the prices in this offer firm for 90 calendar days from the date specified for receipt of of [...truncated]"
  - **retrieved context (shown to the model):** "Cylinder Management: As described above under Cylinder Tracking, our barcode-based tracking system represents an innovative use of cylinder tracking and management technology across the ordering activity network. Regulatory Compliance: All medical gases supplied under this contra [...truncated]"
  - **retrieved context (shown to the model):** "We do not currently operate a system for tracking medical gas cylinders within an ordering activity's facility after delivery, and are therefore not submitting a facility-side tracking plan with this proposal. Reporting Capabilities: Northern Plains Medical Gases will provide on- [...truncated]"
  - **retrieved context (shown to the model):** "Veterans Involvement / Limitations on Subcontracting: Northern Plains Medical Gases will perform 100% of the work identified in the Statement of Work and Contract Administration with its own personnel and equipment; no subcontractors, similarly situated entities, or other perform [...truncated]"
  - **retrieved context (shown to the model):** "From: contracts@northernplainsgases.com To: emanuel.nevarez@va.gov Subject: Quote for Solicitation 36C26326Q0197 - Medical Cylinder Gases IDIQ Solicitation Number: 36C26326Q0197 Northern Plains Medical Gases, LLC 2200 19th Ave N Fargo, ND 58102 (701) 555-0184 Unique Entity Identi [...truncated]"
  - **model's evidence (what it chose to cite):** "Our Project Management Plan assigns a single point of contact, Dana Whitfield, who will coordinate onboarding, task order communications, and identify and delineate the roles and responsibilities of our dispatch and billing staff. Dana Whitfield is also responsible for ensuring contract deliverables are provided on time. A preliminary delivery, install, and user acceptance schedule is included as Appendix 1, showing task dependencies and an estimate of how much time each critical task is expected to take through the first 60 days of performance."
  - **model's evidence (what it chose to cite):** "Our phase-in strategy includes a Project Communications Plan identifying Dana Whitfield as the point of contact for all phase-in and ongoing contract communications, along with the roles of our dispatch and billing staff who will support this contract through the period of performance. We will also submit an Implementation Plan describing depot staffing and cylinder-inventory buildup during the phase-in period."
  - **model's reasoning:** The bidder provides a phase-in strategy that encompasses a Project Communications Plan detailing staff roles (dispatch and billing) and contact information (Dana Whitfield), an Implementation Plan describing depot staffing and inventory buildup, and a Delivery Plan with milestones spanning the first 60 days of performance, thus fully satisfying the requirement.
  - **expected evidence (true_verdicts.json):** "Our phase-in strategy includes a Project Communications Plan identifying Dana Whitfield as the point of contact for all phase-in and ongoing contract communications, along with the roles of our dispatch and billing staff who will support this contract through the period of performance. We will also submit an Implementation Plan describing depot staffing and cylinder-inventory buildup during the phase-in period."
  - **expected reasoning:** Application's phase-in strategy addresses a Project Communications Plan and an Implementation Plan, but never mentions a Delivery Plan or any milestone dates/timelines demonstrating the ability to meet the effective date or the 60-calendar-day requirement, so one of the three required components is missing.

**False-issue rate** — mirror direction: the true verdict is `compliant` only, but the pipeline raised an issue anyway.
- rate: 0.0%

- none

**Unscored** — split/merge groups excluded from the matrix above (still counted in the two rates above):
- group 1:
  - true `cylinder_tracking_plan_delivery` — "5.2. The contractor shall submit an innovative plan with their proposal for tracking medical gas cylinders being delivered to and from the ordering activity. ... 5.2.1. The cylinder tracking plan shall include, but is not limited to: a) Method used for data entry and extraction (i.e. web-based portal, Microsoft Excel spreadsheet, SharePoint, email, etc.); b) Mechanism for data entry (i.e. barcode scanning, handwriting serial numbers, photos, etc.); c) How and when Government will be able to extract data; d) What type of data will be entered and stored; e) Limits on access to Government employees, if applicable; f) Any technology, equipment, software, etc. that requires connection to the Government network, if applicable; and g) Any other pertinent information related to the cylinder tracking plan ... 5.2.2. If the contractor has an impending tracking system or one that is not yet fully operational but would like to submit as part of their proposal, the contractor shall include a timeline for implementation which must coincide with the phase-in timeline as described in paragraph 4.1." (acceptable: ['insufficient_information'])
  - predicted [17b50972] "The cylinder tracking plan shall include, but is not limited to, data entry and extraction methods, data mechanisms, data extraction timing, types of data stored, access limits, network connection technology, and all other items listed under paragraph 5.2.1." — verdict: non_compliant
  - predicted [52463513] "The contractor shall submit an innovative plan with their proposal for tracking medical gas cylinders being delivered to and from the ordering activity at no additional cost to the Government." — verdict: compliant
  - predicted [aba86746] "If the contractor proposes an impending or not yet fully operational tracking system, they must include an implementation timeline coinciding with the phase-in timeline, and such systems not operational by contract transition conclusion shall not be submitted." — verdict: compliant
- group 2:
  - true `past_performance_reference_provided` — "ii. Past Performance: In response to this factor, offerors shall provide past performance references for work performed within the past three (3) years that is directly relevant to the complexity, size, and scope of this requirement. Offerors, at minimum, shall list: • Contract or project number and title • Period of performance • Dollar Value • Brief description / Scope • Name of Agency / Facility • Point of Contact: Include name, title, phone number, and e- mail address" (acceptable: ['insufficient_information'])
  - predicted [22b18b3e] "Brief description / Scope" — verdict: compliant
  - predicted [833793de] "Offerors shall provide past performance references for work performed within the past three years relevant in complexity, size, and scope, including project number/title, period of performance, dollar value, agency/facility name, and point of contact details." — verdict: compliant, citation: fuzzy match — worth a second look

## Evidence

**Citation-verified rate** (evidence-level): fraction of evidence quotes actually located in application.txt.
- rate: 87.2% (5 unverified of 39)

**Evidence recall**: does the expected evidence span (from `true_verdicts.json`) show up somewhere in the requirement's retrieved chunks, before the verdict step chose what to cite? Topics never extracted as a requirement are excluded — that failure is already counted by requirement recall above.
- recall: 100.0% (18/18)
- missed:
  - none
