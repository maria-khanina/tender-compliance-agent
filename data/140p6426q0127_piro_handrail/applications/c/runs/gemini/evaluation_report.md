# Evaluation report

## Summary metrics

Machine-readable numbers for averaging across tenders -- every value here is explained in the sections below. `null` means the metric doesn't apply to this run (e.g. no verdict-only artifact present).

```json
{
  "requirement_recall": 0.9375,
  "requirement_recall_matched": 15,
  "requirement_recall_total": 16,
  "requirement_precision": 0.7059,
  "citation_verified_rate": 1.0,
  "is_mandatory_accuracy": 0.9,
  "is_mandatory_scored": 10,
  "is_text_verifiable_accuracy": 0.8,
  "is_text_verifiable_scored": 10,
  "verdict_clean_match_count": 6,
  "verdict_accuracy": 0.8333,
  "false_compliant_rate": 0.1111,
  "false_issue_rate": 0.0,
  "evidence_citation_verified_rate": 0.8947,
  "evidence_recall": 1.0,
  "verdict_only_accuracy": null,
  "verdict_only_scored": null
}
```

## Requirement recall

For each `true_requirements.json` topic, did the pipeline extract something whose tender.txt citation overlaps the true one? A pure text-offset check, not a judgment of meaning — see coverage flags below for extractions that are technically "found" but sloppy.

**Recall: 93.8% (15/16)**

**Missed** (1) — no overlapping predicted requirement at all. "chunk check" is a mechanical (no-LLM) re-chunking of the source document: whether this topic's matching text ever appeared whole in one chunk handed to the extraction model, or was split across chunks.
- true `small_business_size_standard` — "This requirement is a 100% total small business set-aside. The associated NAICS code is 238990. The small business size standard is $19 M."
    - **chunk check:** [810:948] whole, in chunk 0 -- the model saw this text intact

**Over-split** (0) — one true topic extracted as several separate predicted requirements:
- none

**Over-merge** (2) — one predicted requirement covering several distinct true topics:
- predicted [9412aa95] "Complete the attached price schedule in its entirety, including unit prices and total amounts for all line items without unauthorized edits, and provide the final offer total as the evaluated price." — verdict: compliant lumps together 3 true requirements:
  - true `final_offer_total_no_alternates` — "NOTE: Alternate quotes/proposals will not be accepted. Provide us with the final offer total, as this will be the evaluated price."
  - true `price_schedule_complete` — "Complete attached Price Schedule and insert total unit price and/or amount, in reference to ALL line items listed."
  - true `price_schedule_must_not_be_edited` — "Must ensure that this document is not edited for any reason (outside of adding units of measure, quantities, etc.) and the unedited Price Schedule is provided with final pricing - if needing to make edits or alter the document, provide an addendum outlining these changes or additional information wanting to make apparent to the evaluators."
- predicted [cba387ba] "Provide references and examples (preferably a minimum of 3) of prior projects of similar size and scope completed within the past five years, including brief project descriptions and point of contact information." — verdict: compliant lumps together 2 true requirements:
  - true `prior_experience_count` — "Offers shall submit the following information in its entirety: ... Three prior experiences of projects in similar size and scope per the "TO SUBMIT AN OFFER" section below within the past five years"
  - true `prior_experience_poc_required` — "NOTE: Contact information SHALL be provided, to include a brief description of the project, as well as point of contact information"

**Tangled** (1) — several true and several predicted requirements all overlapping at once:
- tangle of 2 true and 2 predicted requirements, all overlapping — needs manual untangling:
  - true `contractor_core_data` — "Offers shall submit the following information in its entirety: ... c) Contractor Core Data: Offerors Company Name: Cage Code / Offerors Unique Entity Identifier (UEI): Offerors POC: Offerors POC Email/Phone:"
  - true `uei_required` — "To be considered for award your company must obtain a Unique Entity Identifier (UEI)."
  - predicted [5343f4e1] "Provide company name, point of contact (POC), and POC email and phone number." — verdict: compliant
  - predicted [98c5b2c9] "The company must obtain and provide a Unique Entity Identifier (UEI) / Cage Code to be considered for award." — verdict: compliant

## Requirement precision

**Citation-verified rate** (hallucination check): fraction of predicted requirements whose citation was actually located in tender.txt (exactly or via fuzzy match).
- rate: 100.0%
- unverified:
  - none

**Classification precision**: fraction of predicted requirements that matched a true requirement.
- rate: 70.6%
- unexplained (5) — the model recognized these as requirements, but they don't match any true requirement. "closest true topic" is a mechanical (no-LLM) embedding-similarity lookup against every true topic's description; "dedup visibility" checks whether dedup's own cosine pre-filter would have clustered this candidate with whatever predicted requirement DID match that topic -- i.e. whether the dedup LLM call ever had a chance to compare them:
  - predicted [60faa893] "Quotes are due by the specified date and time."
    - **similarity check:** closest true topic: `final_offer_total_no_alternates` (cosine=0.59); vs matched predicted [9412aa95]: cosine=0.57 (< dedup threshold 0.6) -> dedup's cosine pre-filter would NOT have clustered these -- the dedup LLM call never saw them side by side
  - predicted [79645554] "The contractor must use the IPP website to submit invoices for payment, or submit a written waiver request to the Contracting Officer if unable to comply."
    - **similarity check:** closest true topic: `contractor_core_data` (cosine=0.63); vs matched predicted [98c5b2c9]: cosine=0.56 (< dedup threshold 0.6) -> dedup's cosine pre-filter would NOT have clustered these -- the dedup LLM call never saw them side by side
  - predicted [8d76a27b] "Quotes must follow the order and instructions detailed in the solicitation and use the provided checklist."
    - **similarity check:** closest true topic: `or_equal_product_documentation` (cosine=0.70); vs matched predicted [6f621da5]: cosine=0.73 (>= dedup threshold 0.6) -> would likely have been clustered together and compared by the dedup LLM call
  - predicted [91029718] "Offerors are urged and expected to inspect the site to satisfy themselves regarding general and local conditions affecting contract performance."
    - **similarity check:** closest true topic: `or_equal_product_documentation` (cosine=0.60); vs matched predicted [6f621da5]: cosine=0.60 (< dedup threshold 0.6) -> dedup's cosine pre-filter would NOT have clustered these -- the dedup LLM call never saw them side by side
  - predicted [fda987f9] "Provide written confirmation that the company specializes in or has sufficient documented direct experience to provide all labor, material, tools, supervision, and travel for the SOW."
    - **similarity check:** closest true topic: `capabilities_statement_required` (cosine=0.70); vs matched predicted [5071ba74]: cosine=0.64 (>= dedup threshold 0.6) -> would likely have been clustered together and compared by the dedup LLM call

## Coverage flags

Clean 1:1 matches (recall counted them as found) whose citations don't fully overlap in length, split by which side is off. Over-split/over-merge/tangled matches are excluded here -- their predicted fragments are inherently partial by construction, already shown in the recall breakdown above.

**Requirements captured with extra text** (0) — the predicted citation is padded beyond the true one:
- none

**Requirements captured incompletely** (1) — the predicted citation misses part of the true one:
- predicted [33dc85b7] is contained in true `amendment_acknowledgment_if_posted` — 64.2%:
    predicted: "Signed amendments, including SF30, must be reviewed and submitted with the final quote if applicable."
    true: "NOTE: Please check SAM.gov regularly in any case an amendment was posted, as this amendment must be reviewed, acknowledged by signing the SF30 and ensuring that it is provided with your final quote/proposal package."

## is_mandatory accuracy

For each clean or one-to-many match (tangled groups excluded — there's no single "one" to compare against), does `is_mandatory` agree with the true value? A one-to-many group counts as correct only if every member on the "many" side agrees with the "one".

**Accuracy: 90.0% (10 groups)**

Mismatched:
- true: `amendment_acknowledgment_if_posted`=False; predicted: `33dc85b7`=True — "NOTE: Please check SAM.gov regularly in any case an amendment was posted, as this amendment must be reviewed, acknowledged by signing the SF30 and ensuring that it is provided with your final quote/proposal package."

## is_text_verifiable accuracy

For each clean or one-to-many match (tangled groups excluded), does `is_text_verifiable` agree with the true value (all-or-nothing on the "many" side, same rule as is_mandatory above)? A wrong `false` here means the pipeline skips verdict generation for a requirement that should get one.

**Accuracy: 80.0% (10 groups)**

Mismatched:
- true: `sam_registration_active`=False; predicted: `f487145e`=True — "This registration must be "active" in SAM. NO EXCEPTIONS."
- true: `submission_deadline_and_channel`=False; predicted: `ccb13e23`=True — "Submit all required documents via email by the date and time listed in this solicitation. Offerors are responsible for submitting quotes/proposals so as to reach the Government office designated in the solicitation by the time specified in the solicitation. Late quotes/proposals will not be accepted."

## Verdict accuracy

The confusion matrix covers only clean 1:1 matches — split/merge groups have no single pair to plot, but still count in the two rates below.

Clean matches scored: 6

| true \ pipeline said | `compliant` | `non_compliant` | `contradictory` | `insufficient_information` |
|---|---|---|---|---|
| `compliant` | 5 | 0 | 0 | 0 |
| `non_compliant` | 0 | 0 | 0 | 0 |
| `contradictory` | 1 | 0 | 0 | 0 |
| `insufficient_information` | 0 | 0 | 0 | 0 |

**Mismatched clean matches** — every off-diagonal cell above, in full: the full context retrieved and shown to the model, what it chose to cite from that context, and its reasoning ("model's ..."), next to what `true_verdicts.json` expects ("expected ...").

- `capabilities_statement_required` — acceptable: ['contradictory'], predicted: compliant
  - **requirement:** "Provide a detailed capabilities statement, technical questionnaire, or project narrative demonstrating knowledge of and experience in the required products and services."
  - **retrieved context (shown to the model):** "Amendment: We acknowledge receipt of Amendment 0001 to this solicitation, dated 08-05-2026. The signed SF30 acknowledging this amendment is enclosed and provided with this final quote package. Financial Note: Please note that our current fabrication shop backlog means work on any [...truncated]"
  - **retrieved context (shown to the model):** "We will supply the exact handrail hardware and fasteners specified by brand name in the Statement of Work; this is not an "or equal" submission. Shop drawings and product data for the proposed handrail system are included as Attachment A to this quote package. Price Schedule: The [...truncated]"
  - **retrieved context (shown to the model):** "COPPER STATE HANDRAIL CO. 2814 Forge Street, Escanaba, MI 49829 Quote submitted for RFQ 140P6426Q0127 - Fabricate and Install Handrail, Pictured Rocks National Lakeshore Attn: Colette Riegelmayer, Contract Specialist, National Park Service Dear Ms. Riegelmayer, Copper State Handr [...truncated]"
  - **model's evidence (what it chose to cite):** "Capabilities Statement / Project Narrative: Copper State Handrail Co. specializes in steel and aluminum handrail fabrication for federal and municipal facilities. Our crew can mobilize and begin fabrication within 10 business days of award, completing installation well within any reasonable schedule the Government requires."
  - **model's evidence (what it chose to cite):** "Prior Experience References: 1. Munising Falls Interpretive Center - Boardwalk Handrail (2023). Fabricated and installed 210 linear feet of galvanized steel handrail... 2. City of Escanaba - Ludington Park Overlook Railing (2022). Fabricated and installed 130 linear feet of aluminum guardrail... 3. Delta County Road Commission - Bridge Approach Handrail (2021). Fabricated and installed 95 linear feet of galvanized handrail..."
  - **model's reasoning:** The bidder provides a dedicated capabilities statement and project narrative detailing their specialization in steel and aluminum handrail fabrication, alongside prior experience references demonstrating knowledge and experience in the required products and services.
  - **expected evidence (true_verdicts.json):** "Our crew can mobilize and begin fabrication within 10 business days of award, completing installation well within any reasonable schedule the Government requires."
  - **expected evidence (true_verdicts.json):** "our current fabrication shop backlog means work on any newly awarded contract, including this one, cannot begin until at least 45 days after award, consistent with our present production schedule."
  - **expected reasoning:** The Capabilities Statement claims the crew can mobilize and begin fabrication within 10 business days of award, but a later Financial Note states the current shop backlog means work cannot begin until at least 45 days after award -- the two stated start timelines for the same contract conflict.

**False-compliant rate** — dangerous direction: the true verdict requires an issue (anything but `compliant`), but every predicted verdict in the group is `compliant`.
- rate: 11.1%

- `capabilities_statement_required` — acceptable: ['contradictory'], predicted: compliant
  - **requirement:** "Provide a detailed capabilities statement, technical questionnaire, or project narrative demonstrating knowledge of and experience in the required products and services."
  - **retrieved context (shown to the model):** "Amendment: We acknowledge receipt of Amendment 0001 to this solicitation, dated 08-05-2026. The signed SF30 acknowledging this amendment is enclosed and provided with this final quote package. Financial Note: Please note that our current fabrication shop backlog means work on any [...truncated]"
  - **retrieved context (shown to the model):** "We will supply the exact handrail hardware and fasteners specified by brand name in the Statement of Work; this is not an "or equal" submission. Shop drawings and product data for the proposed handrail system are included as Attachment A to this quote package. Price Schedule: The [...truncated]"
  - **retrieved context (shown to the model):** "COPPER STATE HANDRAIL CO. 2814 Forge Street, Escanaba, MI 49829 Quote submitted for RFQ 140P6426Q0127 - Fabricate and Install Handrail, Pictured Rocks National Lakeshore Attn: Colette Riegelmayer, Contract Specialist, National Park Service Dear Ms. Riegelmayer, Copper State Handr [...truncated]"
  - **model's evidence (what it chose to cite):** "Capabilities Statement / Project Narrative: Copper State Handrail Co. specializes in steel and aluminum handrail fabrication for federal and municipal facilities. Our crew can mobilize and begin fabrication within 10 business days of award, completing installation well within any reasonable schedule the Government requires."
  - **model's evidence (what it chose to cite):** "Prior Experience References: 1. Munising Falls Interpretive Center - Boardwalk Handrail (2023). Fabricated and installed 210 linear feet of galvanized steel handrail... 2. City of Escanaba - Ludington Park Overlook Railing (2022). Fabricated and installed 130 linear feet of aluminum guardrail... 3. Delta County Road Commission - Bridge Approach Handrail (2021). Fabricated and installed 95 linear feet of galvanized handrail..."
  - **model's reasoning:** The bidder provides a dedicated capabilities statement and project narrative detailing their specialization in steel and aluminum handrail fabrication, alongside prior experience references demonstrating knowledge and experience in the required products and services.
  - **expected evidence (true_verdicts.json):** "Our crew can mobilize and begin fabrication within 10 business days of award, completing installation well within any reasonable schedule the Government requires."
  - **expected evidence (true_verdicts.json):** "our current fabrication shop backlog means work on any newly awarded contract, including this one, cannot begin until at least 45 days after award, consistent with our present production schedule."
  - **expected reasoning:** The Capabilities Statement claims the crew can mobilize and begin fabrication within 10 business days of award, but a later Financial Note states the current shop backlog means work cannot begin until at least 45 days after award -- the two stated start timelines for the same contract conflict.

**False-issue rate** — mirror direction: the true verdict is `compliant` only, but the pipeline raised an issue anyway.
- rate: 0.0%

- none

**Unscored** — split/merge groups excluded from the matrix above (still counted in the two rates above):
- group 1:
  - true `contractor_core_data` — "Offers shall submit the following information in its entirety: ... c) Contractor Core Data: Offerors Company Name: Cage Code / Offerors Unique Entity Identifier (UEI): Offerors POC: Offerors POC Email/Phone:" (acceptable: ['compliant'])
  - true `uei_required` — "To be considered for award your company must obtain a Unique Entity Identifier (UEI)." (acceptable: ['compliant'])
  - predicted [5343f4e1] "Provide company name, point of contact (POC), and POC email and phone number." — verdict: compliant
  - predicted [98c5b2c9] "The company must obtain and provide a Unique Entity Identifier (UEI) / Cage Code to be considered for award." — verdict: compliant
- group 2:
  - true `final_offer_total_no_alternates` — "NOTE: Alternate quotes/proposals will not be accepted. Provide us with the final offer total, as this will be the evaluated price." (acceptable: ['compliant'])
  - true `price_schedule_complete` — "Complete attached Price Schedule and insert total unit price and/or amount, in reference to ALL line items listed." (acceptable: ['compliant'])
  - true `price_schedule_must_not_be_edited` — "Must ensure that this document is not edited for any reason (outside of adding units of measure, quantities, etc.) and the unedited Price Schedule is provided with final pricing - if needing to make edits or alter the document, provide an addendum outlining these changes or additional information wanting to make apparent to the evaluators." (acceptable: ['compliant'])
  - predicted [9412aa95] "Complete the attached price schedule in its entirety, including unit prices and total amounts for all line items without unauthorized edits, and provide the final offer total as the evaluated price." — verdict: compliant
- group 3:
  - true `prior_experience_count` — "Offers shall submit the following information in its entirety: ... Three prior experiences of projects in similar size and scope per the "TO SUBMIT AN OFFER" section below within the past five years" (acceptable: ['compliant'])
  - true `prior_experience_poc_required` — "NOTE: Contact information SHALL be provided, to include a brief description of the project, as well as point of contact information" (acceptable: ['compliant'])
  - predicted [cba387ba] "Provide references and examples (preferably a minimum of 3) of prior projects of similar size and scope completed within the past five years, including brief project descriptions and point of contact information." — verdict: compliant

## Evidence

**Citation-verified rate** (evidence-level): fraction of evidence quotes actually located in application.txt.
- rate: 89.5% (2 unverified of 19)

**Evidence recall**: does the expected evidence span (from `true_verdicts.json`) show up somewhere in the requirement's retrieved chunks, before the verdict step chose what to cite? Topics never extracted as a requirement are excluded — that failure is already counted by requirement recall above.
- recall: 100.0% (13/13)
- missed:
  - none
