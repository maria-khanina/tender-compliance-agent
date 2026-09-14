# Evaluation report

## Summary metrics

Machine-readable numbers for averaging across tenders -- every value here is explained in the sections below. `null` means the metric doesn't apply to this run (e.g. no verdict-only artifact present).

```json
{
  "requirement_recall": 0.9091,
  "requirement_recall_matched": 10,
  "requirement_recall_total": 11,
  "requirement_precision": 0.75,
  "citation_verified_rate": 1.0,
  "is_mandatory_accuracy": 0.875,
  "is_mandatory_scored": 8,
  "is_text_verifiable_accuracy": 0.75,
  "is_text_verifiable_scored": 8,
  "verdict_clean_match_count": 5,
  "verdict_accuracy": 0.8,
  "false_compliant_rate": 0.0,
  "false_issue_rate": 0.1429,
  "evidence_citation_verified_rate": 1.0,
  "evidence_recall": 1.0,
  "verdict_only_accuracy": null,
  "verdict_only_scored": null
}
```

## Requirement recall

For each `true_requirements.json` topic, did the pipeline extract something whose tender.txt citation overlaps the true one? A pure text-offset check, not a judgment of meaning — see coverage flags below for extractions that are technically "found" but sloppy.

**Recall: 90.9% (10/11)**

**Missed** (1) — no overlapping predicted requirement at all. "chunk check" is a mechanical (no-LLM) re-chunking of the source document: whether this topic's matching text ever appeared whole in one chunk handed to the extraction model, or was split across chunks.
- true `quote_due_date` — "Per Amendment 0001, the hour and date for receipt of offers is EXTENDED to 08-14-2026, 1:00 PM CDT."
    - **chunk check:** [416:515] whole, in chunk 0 -- the model saw this text intact

**Over-split** (1) — one true topic extracted as several separate predicted requirements:
- true `technical_capability_narrative` — "Factor 2 – Technical Capability: The Offeror shall describe its technical approach to performing the required grease trap cleaning services. The quotation shall identify the work to be performed by the prime contractor and any proposed subcontractors, including their respective roles and responsibilities. The Offeror shall demonstrate that its proposed approach is consistent with the applicable limitations on subcontracting requirements for this SDVOSB set-aside." split into 2 predicted requirements:
  - predicted [27aa883d] "The quotation shall identify the work to be performed by the prime contractor and any proposed subcontractors, including their roles, responsibilities, and a demonstration of consistency with applicable limitations on subcontracting." — verdict: contradictory
  - predicted [faaec92e] "The Offeror shall describe its technical approach to performing the required grease trap cleaning services." — verdict: compliant

**Over-merge** (0) — one predicted requirement covering several distinct true topics:
- none

**Tangled** (1) — several true and several predicted requirements all overlapping at once:
- tangle of 2 true and 3 predicted requirements, all overlapping — needs manual untangling:
  - true `sf1449_administrative_info_completion` — "A. Administrative Information: The Contractor shall provide the following information in its quote: 1. SF 1449 (first page) with completed blocks 17a, 30a, 30b, and 30c. 2. Acknowledgement of Amendments (if any) on page 2. 3. Contractor information on page 2."
  - true `subcontracting_certificate_completion` — "4. Complete certification for Clause 852.219-75 VA Notice of Limitations on Subcontracting— Certificate of Compliance for Services and Construction (for SDVOSB/VOSB set-asides or when using SDVOSB and VOSB small business evaluation factors under clause 852-215-70), if included in Section C. ... (d) Offeror completed certification/fill-in required. The formal certification must be completed, signed and returned with the offeror’s bid, quotation, or proposal. The Government will not consider offers for award from offerors that do not provide the certification, and all such responses will be deemed ineligible for evaluation and award."
  - predicted [b25b0aa2] "The offeror must complete, sign, and return the formal certification regarding jurisdiction, compliance with Title 18 U.S.C. Section 1001, and authorization, including providing the name, title, signature, date, and company information." — verdict: non_compliant
  - predicted [d8b7a9ec] "Quotes must be complete, self-sufficient, respond directly to the solicitation, and include required information such as acknowledgement of amendments, contractor information, and the completed certification for Clause 852.219-75." — verdict: contradictory, citation: fuzzy match — worth a second look
  - predicted [fef8c977] "SF 1449 (first page) with completed blocks 17a, 30a, 30b, and 30c." — verdict: compliant

## Requirement precision

**Citation-verified rate** (hallucination check): fraction of predicted requirements whose citation was actually located in tender.txt (exactly or via fuzzy match).
- rate: 100.0%
- unverified:
  - none

**Classification precision**: fraction of predicted requirements that matched a true requirement.
- rate: 75.0%
- unexplained (4) — the model recognized these as requirements, but they don't match any true requirement. "closest true topic" is a mechanical (no-LLM) embedding-similarity lookup against every true topic's description; "dedup visibility" checks whether dedup's own cosine pre-filter would have clustered this candidate with whatever predicted requirement DID match that topic -- i.e. whether the dedup LLM call ever had a chance to compare them:
  - predicted [695a4313] "Provide six (6) service inspections per contract year, to occur in the months of December, February, April, June, August, and October."
    - **similarity check:** closest true topic: `quote_due_date` (cosine=0.52); that true topic has no matched predicted requirement in this run, so there was nothing for dedup to compare it against
  - predicted [821e108a] "Provide up to three (3) service calls per contract year to pump the lift station located in Building 410."
    - **similarity check:** closest true topic: `relevant_experience_submission` (cosine=0.50); vs matched predicted [8ddce7ec]: cosine=0.56 (< dedup threshold 0.6) -> dedup's cosine pre-filter would NOT have clustered these -- the dedup LLM call never saw them side by side
  - predicted [86c8a7a1] "The offeror must specify required service documentation, including disposal manifests, volume tickets, photographs, and inspection reports."
    - **similarity check:** closest true topic: `relevant_experience_submission` (cosine=0.64); vs matched predicted [8ddce7ec]: cosine=0.61 (>= dedup threshold 0.6) -> would likely have been clustered together and compared by the dedup LLM call
  - predicted [b435f6ed] "The offeror must provide the number, location, type, rated capacity, approximate current contents, and required cleaning frequency of each grease trap or interceptor."
    - **similarity check:** closest true topic: `technical_capability_narrative` (cosine=0.62); vs matched predicted [faaec92e]: cosine=0.69 (>= dedup threshold 0.6) -> would likely have been clustered together and compared by the dedup LLM call

## Coverage flags

Clean 1:1 matches (recall counted them as found) whose citations don't fully overlap in length, split by which side is off. Over-split/over-merge/tangled matches are excluded here -- their predicted fragments are inherently partial by construction, already shown in the recall breakdown above.

**Requirements captured with extra text** (0) — the predicted citation is padded beyond the true one:
- none

**Requirements captured incompletely** (5) — the predicted citation misses part of the true one:
- predicted [1ec324a3] is contained in true `amendment_acknowledgment` — 76.0%:
    predicted: "The offeror must acknowledge receipt of all amendments to the solicitation."
    true: "ACKNOWLEDGMENT OF AMENDMENTS: The offeror acknowledges receipt of amendments to the Solicitation numbered and dated as follows:"

- predicted [0f8c28ac] is contained in true `price_schedule_completion_all_periods` — 39.8%:
    predicted: "The Contractor must provide firm-fixed pricing for all line items listed in the Price Schedule for the Base Period and all four (4) Option Periods."
    true: "Factor 1 – Price: The Contractor must provide firm-fixed pricing for all line items listed in the Price Schedule for the Base Period and all four (4) Option Periods. If the Price Schedule is not completed entirely, or the offeror indicates additional/variable pricing fees, the entire quote may be considered unacceptable, and the offeror could be ineligible for award."

- predicted [fd2669ee] is contained in true `offsite_disposal_cost_inclusion` — 30.2%:
    predicted: "The contractor shall provide all labor, materials, equipment, and tools necessary to clean grease traps, remove and dispose of grease in accordance with all Federal, State, and Local regulations, and include all transportation and offsite disposal costs in the price."
    true: "The Tomah VA does not provide an approved onsite disposal or receiving facility for grease-trap waste. The contractor is responsible for transporting the waste to an offsite location. Please refer to the Performance Work Statement (Section B.3) in the solicitation."

- predicted [1a3fe8fb] is contained in true `subcontracting_cap_representation` — 48.1%:
    predicted: "The contractor must comply with the limitations on subcontracting as set forth in VAAR 852.219-73, 852.219-74, and 852.219-75, including specific percentage caps for services and construction, and ensure that work by similarly situated subcontractors counts toward these limits."
    true: "(i) [X] Services. In the case of a contract for services (except construction), the contractor will not pay more than 50% of the amount paid by the government to it to firms that are not certified SDVOSBs listed in the SBA certification database as set forth in 852.219–73 or certified VOSBs listed in the SBA certification database as set forth in 852.219–74. Any work that a similarly situated certified SDVOSB/VOSB subcontractor further subcontracts will count towards the 50% subcontract amount that cannot be exceeded. Other direct costs may be excluded to the extent they are not the principal purpose of the acquisition and small business concerns do not provide the service as set forth in 13 CFR 125.6."

- predicted [e905f884] is contained in true `sdvosb_certification_status` — 67.4%:
    predicted: "All SDVOSBs submitting quotes must be listed as certified by the Small Business Administration on its Small Business Search website in accordance with VAAR 819.7003."
    true: "SDVOSB Set-aside: This procurement is 100% set aside for Service-Disabled Veteran-Owned Small Businesses (SDVOSBs). All SDVOSBs submitting quotes must be listed as certified by the Small Business Administration on its Small Business Search website, available at SBA: Small Business Search, to have their quotes considered, in accordance with VAAR 819.7003."

## is_mandatory accuracy

For each clean or one-to-many match (tangled groups excluded — there's no single "one" to compare against), does `is_mandatory` agree with the true value? A one-to-many group counts as correct only if every member on the "many" side agrees with the "one".

**Accuracy: 87.5% (8 groups)**

Mismatched:
- true: `relevant_experience_submission`=False; predicted: `8ddce7ec`=True — "Factor 3 – Relevant Experience: Submit information, if any, of contracts providing services similar to the requirements of this Contract, particularly if that experience is at a VA facility. Information shall include the contract number, size/scope of each contract, the total number of years of experience providing such services, and when those services were provided."

## is_text_verifiable accuracy

For each clean or one-to-many match (tangled groups excluded), does `is_text_verifiable` agree with the true value (all-or-nothing on the "many" side, same rule as is_mandatory above)? A wrong `false` here means the pipeline skips verdict generation for a requirement that should get one.

**Accuracy: 75.0% (8 groups)**

Mismatched:
- true: `subcontracting_cap_representation`=False; predicted: `1a3fe8fb`=True — "(i) [X] Services. In the case of a contract for services (except construction), the contractor will not pay more than 50% of the amount paid by the government to it to firms that are not certified SDVOSBs listed in the SBA certification database as set forth in 852.219–73 or certified VOSBs listed in the SBA certification database as set forth in 852.219–74. Any work that a similarly situated certified SDVOSB/VOSB subcontractor further subcontracts will count towards the 50% subcontract amount that cannot be exceeded. Other direct costs may be excluded to the extent they are not the principal purpose of the acquisition and small business concerns do not provide the service as set forth in 13 CFR 125.6."
- true: `sdvosb_certification_status`=False; predicted: `e905f884`=True — "SDVOSB Set-aside: This procurement is 100% set aside for Service-Disabled Veteran-Owned Small Businesses (SDVOSBs). All SDVOSBs submitting quotes must be listed as certified by the Small Business Administration on its Small Business Search website, available at SBA: Small Business Search, to have their quotes considered, in accordance with VAAR 819.7003."

## Verdict accuracy

The confusion matrix covers only clean 1:1 matches — split/merge groups have no single pair to plot, but still count in the two rates below.

Clean matches scored: 5

| true \ pipeline said | `compliant` | `non_compliant` | `contradictory` | `insufficient_information` |
|---|---|---|---|---|
| `compliant` | 0 | 1 | 0 | 1 |
| `non_compliant` | 0 | 1 | 0 | 1 |
| `contradictory` | 0 | 0 | 0 | 0 |
| `insufficient_information` | 0 | 1 | 0 | 0 |

Why some rows are empty:
- `contradictory` row is empty: true `technical_capability_narrative` — over_split match — no single pair to plot

**Mismatched clean matches** — every off-diagonal cell above, in full: the full context retrieved and shown to the model, what it chose to cite from that context, and its reasoning ("model's ..."), next to what `true_verdicts.json` expects ("expected ...").

- `offsite_disposal_cost_inclusion` — acceptable: ['insufficient_information'], predicted: non_compliant
  - **requirement:** "The contractor shall provide all labor, materials, equipment, and tools necessary to clean grease traps, remove and dispose of grease in accordance with all Federal, State, and Local regulations, and include all transportation and offsite disposal costs in the price."
  - **retrieved context (shown to the model):** "Option Periods 1-4: Pricing for the option periods will be provided upon request following any notice of intent to award, once current fuel and disposal-market rates are confirmed. TECHNICAL CAPABILITY Northwoods Septic & Grease Solutions, LLC will perform all six annual service [...truncated]"
  - **retrieved context (shown to the model):** "Northwoods Septic & Grease Solutions, LLC 2280 Highway 12, La Crosse, WI 54601 RE: Solicitation 36C25226Q0525 -- Grease Trap Cleaning Service, Tomah VA Medical Center Northwoods Septic & Grease Solutions, LLC submits the following quote in response to the above-referenced solicit [...truncated]"
  - **retrieved context (shown to the model):** "VAAR 852.219-75 CERTIFICATE OF COMPLIANCE Northwoods Septic & Grease Solutions, LLC certifies that if awarded the contract, it will comply with the limitations on subcontracting specified in this clause and in the resultant contract. Northwoods Septic & Grease Solutions, LLC is a [...truncated]"
  - **model's evidence (what it chose to cite):** "Option Periods 1-4: Pricing for the option periods will be provided upon request following any notice of intent to award, once current fuel and disposal-market rates are confirmed."
  - **model's reasoning:** The requirement explicitly states that the contractor must include all transportation and offsite disposal costs in the price. The bidder's application fails to provide pricing for the option periods, stating it will be provided upon request after the notice of intent to award. This violates the requirement to include these costs in the bid price.
  - **expected evidence (true_verdicts.json):** "All grease removed during service will be transported by our own tanker trucks to Coulee Region Renewable Energy, a licensed grease-disposal facility in Onalaska, WI, for proper disposal in accordance with all applicable federal, state, and local regulations."
  - **expected reasoning:** Application confirms grease will be transported offsite to a named licensed disposal facility, but never states that the transportation and disposal costs are included in the quoted price rather than billed separately, so compliance with the cost-inclusion requirement cannot be confirmed.

**False-compliant rate** — dangerous direction: the true verdict requires an issue (anything but `compliant`), but every predicted verdict in the group is `compliant`.
- rate: 0.0%

- none

**False-issue rate** — mirror direction: the true verdict is `compliant` only, but the pipeline raised an issue anyway.
- rate: 14.3%

- group of 2 true topic(s) and 3 predicted requirement(s) (not a 1:1 match, so there is no single correct pairing between them):
  - true `sf1449_administrative_info_completion` — "A. Administrative Information: The Contractor shall provide the following information in its quote: 1. SF 1449 (first page) with completed blocks 17a, 30a, 30b, and 30c. 2. Acknowledgement of Amendments (if any) on page 2. 3. Contractor information on page 2." (acceptable: ['compliant'])
      - **expected evidence (true_verdicts.json):** "SF 1449, page 1: Blocks 17a, 30a, 30b, and 30c have been completed as required and are included with this submission."
      - **expected evidence (true_verdicts.json):** "Contractor Information: Northwoods Septic & Grease Solutions, LLC, UEI ND8K5MPQJ217, 2280 Highway 12, La Crosse, WI 54601. Point of Contact: Karen Holt, (608) 555-0142, karen.holt@northwoodsseptic.com."
      - **expected reasoning:** Application states that SF 1449 blocks 17a/30a/30b/30c are completed and provides the required contractor information.
  - true `subcontracting_certificate_completion` — "4. Complete certification for Clause 852.219-75 VA Notice of Limitations on Subcontracting— Certificate of Compliance for Services and Construction (for SDVOSB/VOSB set-asides or when using SDVOSB and VOSB small business evaluation factors under clause 852-215-70), if included in Section C. ... (d) Offeror completed certification/fill-in required. The formal certification must be completed, signed and returned with the offeror’s bid, quotation, or proposal. The Government will not consider offers for award from offerors that do not provide the certification, and all such responses will be deemed ineligible for evaluation and award." (acceptable: ['compliant'])
      - **expected evidence (true_verdicts.json):** "Northwoods Septic & Grease Solutions, LLC certifies that if awarded the contract, it will comply with the limitations on subcontracting specified in this clause and in the resultant contract. Northwoods Septic & Grease Solutions, LLC is authorized to execute this certification on its own behalf."
      - **expected reasoning:** Application includes the VAAR 852.219-75 certification language, signed and dated by an authorized representative.
  - **retrieved context (shown to the model):** "VAAR 852.219-75 CERTIFICATE OF COMPLIANCE Northwoods Septic & Grease Solutions, LLC certifies that if awarded the contract, it will comply with the limitations on subcontracting specified in this clause and in the resultant contract. Northwoods Septic & Grease Solutions, LLC is a [...truncated]"
  - **retrieved context (shown to the model):** "Option Periods 1-4: Pricing for the option periods will be provided upon request following any notice of intent to award, once current fuel and disposal-market rates are confirmed. TECHNICAL CAPABILITY Northwoods Septic & Grease Solutions, LLC will perform all six annual service [...truncated]"
  - **retrieved context (shown to the model):** "Northwoods Septic & Grease Solutions, LLC 2280 Highway 12, La Crosse, WI 54601 RE: Solicitation 36C25226Q0525 -- Grease Trap Cleaning Service, Tomah VA Medical Center Northwoods Septic & Grease Solutions, LLC submits the following quote in response to the above-referenced solicit [...truncated]"
  - predicted verdicts in this group:
    - predicted [b25b0aa2] "The offeror must complete, sign, and return the formal certification regarding jurisdiction, compliance with Title 18 U.S.C. Section 1001, and authorization, including providing the name, title, signature, date, and company information." — verdict: non_compliant
      - **model's evidence (what it chose to cite):** "VAAR 852.219-75 CERTIFICATE OF COMPLIANCE"
      - **model's reasoning:** The requirement mandates a formal certification regarding jurisdiction, compliance with Title 18 U.S.C. Section 1001, and authorization. While the bidder provided a 'VAAR 852.219-75 Certificate of Compliance' regarding subcontracting limitations, they failed to provide the specific certification required by the tender regarding jurisdiction and Title 18 U.S.C. Section 1001.
    - predicted [d8b7a9ec] "Quotes must be complete, self-sufficient, respond directly to the solicitation, and include required information such as acknowledgement of amendments, contractor information, and the completed certification for Clause 852.219-75." — verdict: contradictory, citation: fuzzy match — worth a second look
      - **model's evidence (what it chose to cite):** "All work under this contract will be performed exclusively by Northwoods Septic & Grease Solutions, LLC's own certified technicians; no subcontractors will be used at any point in the performance of this contract."
      - **model's evidence (what it chose to cite):** "Our subcontractor, Coulee Region Grease Traps Inc., performed grease trap cleaning and lift station pumping services for three years (2022-2025) under a similar contract"
      - **model's reasoning:** The bidder's application contains contradictory information regarding their performance model. In the 'Technical Capability' section, the bidder explicitly states that no subcontractors will be used, while in the 'Relevant Experience' section, they refer to 'Our subcontractor, Coulee Region Grease Traps Inc.' This inconsistency makes the application contradictory and fails the requirement for a complete and self-sufficient response.
    - predicted [fef8c977] "SF 1449 (first page) with completed blocks 17a, 30a, 30b, and 30c." — verdict: compliant
      - **model's evidence (what it chose to cite):** "SF 1449, page 1: Blocks 17a, 30a, 30b, and 30c have been completed as required and are included with this submission."
      - **model's reasoning:** The bidder explicitly states in their administrative information that they have completed the required blocks (17a, 30a, 30b, and 30c) on the SF 1449 form and included it with their submission.

**Unscored** — split/merge groups excluded from the matrix above (still counted in the two rates above):
- group 1:
  - true `technical_capability_narrative` — "Factor 2 – Technical Capability: The Offeror shall describe its technical approach to performing the required grease trap cleaning services. The quotation shall identify the work to be performed by the prime contractor and any proposed subcontractors, including their respective roles and responsibilities. The Offeror shall demonstrate that its proposed approach is consistent with the applicable limitations on subcontracting requirements for this SDVOSB set-aside." (acceptable: ['contradictory'])
  - predicted [27aa883d] "The quotation shall identify the work to be performed by the prime contractor and any proposed subcontractors, including their roles, responsibilities, and a demonstration of consistency with applicable limitations on subcontracting." — verdict: contradictory
  - predicted [faaec92e] "The Offeror shall describe its technical approach to performing the required grease trap cleaning services." — verdict: compliant
- group 2:
  - true `sf1449_administrative_info_completion` — "A. Administrative Information: The Contractor shall provide the following information in its quote: 1. SF 1449 (first page) with completed blocks 17a, 30a, 30b, and 30c. 2. Acknowledgement of Amendments (if any) on page 2. 3. Contractor information on page 2." (acceptable: ['compliant'])
  - true `subcontracting_certificate_completion` — "4. Complete certification for Clause 852.219-75 VA Notice of Limitations on Subcontracting— Certificate of Compliance for Services and Construction (for SDVOSB/VOSB set-asides or when using SDVOSB and VOSB small business evaluation factors under clause 852-215-70), if included in Section C. ... (d) Offeror completed certification/fill-in required. The formal certification must be completed, signed and returned with the offeror’s bid, quotation, or proposal. The Government will not consider offers for award from offerors that do not provide the certification, and all such responses will be deemed ineligible for evaluation and award." (acceptable: ['compliant'])
  - predicted [b25b0aa2] "The offeror must complete, sign, and return the formal certification regarding jurisdiction, compliance with Title 18 U.S.C. Section 1001, and authorization, including providing the name, title, signature, date, and company information." — verdict: non_compliant
  - predicted [d8b7a9ec] "Quotes must be complete, self-sufficient, respond directly to the solicitation, and include required information such as acknowledgement of amendments, contractor information, and the completed certification for Clause 852.219-75." — verdict: contradictory, citation: fuzzy match — worth a second look
  - predicted [fef8c977] "SF 1449 (first page) with completed blocks 17a, 30a, 30b, and 30c." — verdict: compliant

## Evidence

**Citation-verified rate** (evidence-level): fraction of evidence quotes actually located in application.txt.
- rate: 100.0% (0 unverified of 21)

**Evidence recall**: does the expected evidence span (from `true_verdicts.json`) show up somewhere in the requirement's retrieved chunks, before the verdict step chose what to cite? Topics never extracted as a requirement are excluded — that failure is already counted by requirement recall above.
- recall: 100.0% (7/7)
- missed:
  - none
