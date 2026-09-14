# Evaluation report

## Summary metrics

Machine-readable numbers for averaging across tenders -- every value here is explained in the sections below. `null` means the metric doesn't apply to this run (e.g. no verdict-only artifact present).

```json
{
  "requirement_recall": 0.9375,
  "requirement_recall_matched": 15,
  "requirement_recall_total": 16,
  "requirement_precision": 0.6087,
  "citation_verified_rate": 1.0,
  "is_mandatory_accuracy": 0.8889,
  "is_mandatory_scored": 9,
  "is_text_verifiable_accuracy": 0.7778,
  "is_text_verifiable_scored": 9,
  "verdict_clean_match_count": 6,
  "verdict_accuracy": 1.0,
  "false_compliant_rate": 0.0,
  "false_issue_rate": 0.3333,
  "evidence_citation_verified_rate": 0.9444,
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

**Over-merge** (1) — one predicted requirement covering several distinct true topics:
- predicted [c42ccbc7] "Provide at least three prior experience references for projects of similar size and scope within the past five years, including brief descriptions and contact information." — verdict: non_compliant lumps together 2 true requirements:
  - true `prior_experience_count` — "Offers shall submit the following information in its entirety: ... Three prior experiences of projects in similar size and scope per the "TO SUBMIT AN OFFER" section below within the past five years"
  - true `prior_experience_poc_required` — "NOTE: Contact information SHALL be provided, to include a brief description of the project, as well as point of contact information"

**Tangled** (2) — several true and several predicted requirements all overlapping at once:
- tangle of 2 true and 3 predicted requirements, all overlapping — needs manual untangling:
  - true `contractor_core_data` — "Offers shall submit the following information in its entirety: ... c) Contractor Core Data: Offerors Company Name: Cage Code / Offerors Unique Entity Identifier (UEI): Offerors POC: Offerors POC Email/Phone:"
  - true `uei_required` — "To be considered for award your company must obtain a Unique Entity Identifier (UEI)."
  - predicted [526001ea] "Provide the offeror's company name." — verdict: compliant
  - predicted [bcd513a4] "The company must obtain and provide a Unique Entity Identifier (UEI)." — verdict: compliant
  - predicted [db017c82] "Provide the offeror's point of contact (POC) name, email, and phone number." — verdict: non_compliant
- tangle of 3 true and 2 predicted requirements, all overlapping — needs manual untangling:
  - true `final_offer_total_no_alternates` — "NOTE: Alternate quotes/proposals will not be accepted. Provide us with the final offer total, as this will be the evaluated price."
  - true `price_schedule_complete` — "Complete attached Price Schedule and insert total unit price and/or amount, in reference to ALL line items listed."
  - true `price_schedule_must_not_be_edited` — "Must ensure that this document is not edited for any reason (outside of adding units of measure, quantities, etc.) and the unedited Price Schedule is provided with final pricing - if needing to make edits or alter the document, provide an addendum outlining these changes or additional information wanting to make apparent to the evaluators."
  - predicted [2cdc4b48] "Complete the attached price schedule in its entirety, including unit prices and total amounts for all line items, without unauthorized edits, and provide the final offer total." — verdict: non_compliant
  - predicted [a647393c] "Alternate quotes or proposals will not be accepted." — verdict: non_compliant

## Requirement precision

**Citation-verified rate** (hallucination check): fraction of predicted requirements whose citation was actually located in tender.txt (exactly or via fuzzy match).
- rate: 100.0%
- unverified:
  - none

**Classification precision**: fraction of predicted requirements that matched a true requirement.
- rate: 60.9%
- unexplained (9) — the model recognized these as requirements, but they don't match any true requirement. "closest true topic" is a mechanical (no-LLM) embedding-similarity lookup against every true topic's description; "dedup visibility" checks whether dedup's own cosine pre-filter would have clustered this candidate with whatever predicted requirement DID match that topic -- i.e. whether the dedup LLM call ever had a chance to compare them:
  - predicted [41946648] "Provide written confirmation of sufficient documented direct experience in providing all labor, material, tools, supervision, and travel for the SOW."
    - **similarity check:** closest true topic: `capabilities_statement_required` (cosine=0.70); vs matched predicted [f6d5d4f1]: cosine=0.64 (>= dedup threshold 0.6) -> would likely have been clustered together and compared by the dedup LLM call
  - predicted [7b6b3f00] "Quotes must be structured in accordance with and in the order detailed in the solicitation, utilizing the checklist to ensure all required documents are submitted."
    - **similarity check:** closest true topic: `or_equal_product_documentation` (cosine=0.70); vs matched predicted [e0e693f1]: cosine=0.69 (>= dedup threshold 0.6) -> would likely have been clustered together and compared by the dedup LLM call
  - predicted [c269bd2a] "The contractor must submit payment requests electronically through the Invoice Processing Platform (IPP) system."
    - **similarity check:** closest true topic: `contractor_core_data` (cosine=0.66); vs matched predicted [526001ea]: cosine=0.56 (< dedup threshold 0.6) -> dedup's cosine pre-filter would NOT have clustered these -- the dedup LLM call never saw them side by side
  - predicted [ce8becf4] "Item Number 10: Fabricate/Install Handrail (includes mob/demob, supplies, labor) - Price Total - Price"
    - **similarity check:** closest true topic: `contractor_core_data` (cosine=0.55); vs matched predicted [526001ea]: cosine=0.52 (< dedup threshold 0.6) -> dedup's cosine pre-filter would NOT have clustered these -- the dedup LLM call never saw them side by side
  - predicted [cee41754] "Quotes are due by 9 September 2026 at 12 PM ET."
    - **similarity check:** closest true topic: `or_equal_product_documentation` (cosine=0.56); vs matched predicted [e0e693f1]: cosine=0.52 (< dedup threshold 0.6) -> dedup's cosine pre-filter would NOT have clustered these -- the dedup LLM call never saw them side by side
  - predicted [d4eec50a] "Questions regarding the solicitation will only be accepted until 1 September 2026 at 12 PM ET."
    - **similarity check:** closest true topic: `final_offer_total_no_alternates` (cosine=0.64); vs matched predicted [2cdc4b48]: cosine=0.63 (>= dedup threshold 0.6) -> would likely have been clustered together and compared by the dedup LLM call
  - predicted [d6d6d8df] "If unable to use IPP for invoices, submit a written waiver request to the Contracting Officer with the proposal."
    - **similarity check:** closest true topic: `contractor_core_data` (cosine=0.61); vs matched predicted [526001ea]: cosine=0.51 (< dedup threshold 0.6) -> dedup's cosine pre-filter would NOT have clustered these -- the dedup LLM call never saw them side by side
  - predicted [dfe1c013] "Provide a vendor invoice document in PDF format showing pricing breakdown, contract number, dates of service, invoice date, and vendor letterhead."
    - **similarity check:** closest true topic: `contractor_core_data` (cosine=0.60); vs matched predicted [526001ea]: cosine=0.55 (< dedup threshold 0.6) -> dedup's cosine pre-filter would NOT have clustered these -- the dedup LLM call never saw them side by side
  - predicted [f34982a4] "Offerors are urged and expected to inspect the site to satisfy themselves regarding local conditions affecting contract performance."
    - **similarity check:** closest true topic: `or_equal_product_documentation` (cosine=0.60); vs matched predicted [e0e693f1]: cosine=0.57 (< dedup threshold 0.6) -> dedup's cosine pre-filter would NOT have clustered these -- the dedup LLM call never saw them side by side

## Coverage flags

Clean 1:1 matches (recall counted them as found) whose citations don't fully overlap in length, split by which side is off. Over-split/over-merge/tangled matches are excluded here -- their predicted fragments are inherently partial by construction, already shown in the recall breakdown above.

**Requirements captured with extra text** (0) — the predicted citation is padded beyond the true one:
- none

**Requirements captured incompletely** (1) — the predicted citation misses part of the true one:
- predicted [10492f08] is contained in true `sam_registration_active` — 73.7%:
    predicted: "The company must be registered in the System for Award Management (SAM) with an active status, qualify as a small business for the specified NAICS code at the time of quote submission, at award, and throughout contract performance."
    true: "This registration must be "active" in SAM. NO EXCEPTIONS."

## is_mandatory accuracy

For each clean or one-to-many match (tangled groups excluded — there's no single "one" to compare against), does `is_mandatory` agree with the true value? A one-to-many group counts as correct only if every member on the "many" side agrees with the "one".

**Accuracy: 88.9% (9 groups)**

Mismatched:
- true: `amendment_acknowledgment_if_posted`=False; predicted: `19270fca`=True — "NOTE: Please check SAM.gov regularly in any case an amendment was posted, as this amendment must be reviewed, acknowledged by signing the SF30 and ensuring that it is provided with your final quote/proposal package."

## is_text_verifiable accuracy

For each clean or one-to-many match (tangled groups excluded), does `is_text_verifiable` agree with the true value (all-or-nothing on the "many" side, same rule as is_mandatory above)? A wrong `false` here means the pipeline skips verdict generation for a requirement that should get one.

**Accuracy: 77.8% (9 groups)**

Mismatched:
- true: `sam_registration_active`=False; predicted: `10492f08`=True — "This registration must be "active" in SAM. NO EXCEPTIONS."
- true: `submission_deadline_and_channel`=False; predicted: `7f62e524`=True — "Submit all required documents via email by the date and time listed in this solicitation. Offerors are responsible for submitting quotes/proposals so as to reach the Government office designated in the solicitation by the time specified in the solicitation. Late quotes/proposals will not be accepted."

## Verdict accuracy

The confusion matrix covers only clean 1:1 matches — split/merge groups have no single pair to plot, but still count in the two rates below.

Clean matches scored: 6

| true \ pipeline said | `compliant` | `non_compliant` | `contradictory` | `insufficient_information` |
|---|---|---|---|---|
| `compliant` | 2 | 0 | 0 | 0 |
| `non_compliant` | 0 | 0 | 0 | 1 |
| `contradictory` | 0 | 1 | 0 | 0 |
| `insufficient_information` | 0 | 1 | 0 | 1 |

**Mismatched clean matches** — every off-diagonal cell above, in full: the full context retrieved and shown to the model, what it chose to cite from that context, and its reasoning ("model's ..."), next to what `true_verdicts.json` expects ("expected ...").

- none

**False-compliant rate** — dangerous direction: the true verdict requires an issue (anything but `compliant`), but every predicted verdict in the group is `compliant`.
- rate: 0.0%

- none

**False-issue rate** — mirror direction: the true verdict is `compliant` only, but the pipeline raised an issue anyway.
- rate: 33.3%

- group of 2 true topic(s) and 3 predicted requirement(s) (not a 1:1 match, so there is no single correct pairing between them):
  - true `contractor_core_data` — "Offers shall submit the following information in its entirety: ... c) Contractor Core Data: Offerors Company Name: Cage Code / Offerors Unique Entity Identifier (UEI): Offerors POC: Offerors POC Email/Phone:" (acceptable: ['insufficient_information'])
      - **expected evidence (true_verdicts.json):** "NORTHWOODS FABRICATION & ERECTORS, INC."
      - **expected evidence (true_verdicts.json):** "Cage Code / Unique Entity Identifier (UEI): HRN4K7Q2XM56"
      - **expected evidence (true_verdicts.json):** "Teresa Blackwood Estimator"
      - **expected reasoning:** Application gives company name and Cage Code/UEI, but never states a point-of-contact name or a POC email/phone under the Contractor Core Data checklist -- the closing signature gives a name and title but not in that capacity, and no phone or email accompanies it. Two of the four required elements are missing.
  - true `uei_required` — "To be considered for award your company must obtain a Unique Entity Identifier (UEI)." (acceptable: ['compliant'])
      - **expected evidence (true_verdicts.json):** "Cage Code / Unique Entity Identifier (UEI): HRN4K7Q2XM56"
      - **expected reasoning:** UEI is explicitly stated (combined with Cage Code on one line).
  - **retrieved context (shown to the model):** "Amendment: We acknowledge that Amendment 0001 to this solicitation exists and confirm that this quote reflects the solicitation as amended. We appreciate your consideration of this quote. Sincerely, Teresa Blackwood Estimator Northwoods Fabrication & Erectors, Inc."
  - **retrieved context (shown to the model):** "We will supply the exact handrail hardware and fasteners specified by brand name in the Statement of Work, with no substitutions. Price Schedule: We have revised the item description on the enclosed Price Schedule to specify "Type 316 stainless fasteners" in place of the generic [...truncated]"
  - **retrieved context (shown to the model):** "NORTHWOODS FABRICATION & ERECTORS, INC. 1487 County Road 550, Marquette, MI 49855 Quote submitted for RFQ 140P6426Q0127 - Fabricate and Install Handrail, Pictured Rocks National Lakeshore Attn: Colette Riegelmayer, Contract Specialist, National Park Service Dear Ms. Riegelmayer, [...truncated]"
  - predicted verdicts in this group:
    - predicted [526001ea] "Provide the offeror's company name." — verdict: compliant
      - **model's evidence (what it chose to cite):** "NORTHWOODS FABRICATION & ERECTORS, INC."
      - **model's evidence (what it chose to cite):** "Northwoods Fabrication & Erectors, Inc."
      - **model's reasoning:** The application explicitly provides the offeror's company name, Northwoods Fabrication & Erectors, Inc., in both the header and the signature block.
    - predicted [bcd513a4] "The company must obtain and provide a Unique Entity Identifier (UEI)." — verdict: compliant
      - **model's evidence (what it chose to cite):** "Cage Code / Unique Entity Identifier (UEI): HRN4K7Q2XM56"
      - **model's reasoning:** The requirement states that the company must obtain and provide a Unique Entity Identifier (UEI). The bidder provides their UEI (HRN4K7Q2XM56) directly in their application under the company overview section, thereby fully satisfying the requirement.
    - predicted [db017c82] "Provide the offeror's point of contact (POC) name, email, and phone number." — verdict: non_compliant
      - **model's evidence (what it chose to cite):** "Sincerely, Teresa Blackwood Estimator Northwoods Fabrication & Erectors, Inc."
      - **model's reasoning:** The requirement asks for the offeror's point of contact name, email, and phone number. While the bidder provides a name (Teresa Blackwood), neither her email address nor her phone number is provided anywhere in the application text.

- group of 3 true topic(s) and 2 predicted requirement(s) (not a 1:1 match, so there is no single correct pairing between them):
  - true `final_offer_total_no_alternates` — "NOTE: Alternate quotes/proposals will not be accepted. Provide us with the final offer total, as this will be the evaluated price." (acceptable: ['non_compliant'])
      - **expected evidence (true_verdicts.json):** "Alternate Item 10A - Fabricate/Install Handrail, Value-Engineered Mounting Bracket: $47,900.00"
      - **expected evidence (true_verdicts.json):** "We are prepared to perform under either configuration at the Government's discretion."
      - **expected reasoning:** Application provides two priced configurations (Item 10 and Alternate Item 10A) rather than a single final offer total, and explicitly states it is prepared to perform under either -- exactly the alternate-quote situation the requirement prohibits.
  - true `price_schedule_complete` — "Complete attached Price Schedule and insert total unit price and/or amount, in reference to ALL line items listed." (acceptable: ['compliant'])
      - **expected evidence (true_verdicts.json):** "Item 10 - Fabricate/Install Handrail: $52,300.00"
      - **expected reasoning:** Item 10 price and total are filled in ($52,300.00).
  - true `price_schedule_must_not_be_edited` — "Must ensure that this document is not edited for any reason (outside of adding units of measure, quantities, etc.) and the unedited Price Schedule is provided with final pricing - if needing to make edits or alter the document, provide an addendum outlining these changes or additional information wanting to make apparent to the evaluators." (acceptable: ['non_compliant'])
      - **expected evidence (true_verdicts.json):** "We have revised the item description on the enclosed Price Schedule to specify "Type 316 stainless fasteners" in place of the generic wording, to ensure our fabrication shop orders the correct hardware grade; all unit and quantity fields remain as issued."
      - **expected reasoning:** Application explicitly admits editing the Price Schedule item description beyond units/quantities (changing the wording to specify a fastener grade), and provides no addendum explaining the change alongside an unedited copy as the requirement demands.
  - **retrieved context (shown to the model):** "Amendment: We acknowledge that Amendment 0001 to this solicitation exists and confirm that this quote reflects the solicitation as amended. We appreciate your consideration of this quote. Sincerely, Teresa Blackwood Estimator Northwoods Fabrication & Erectors, Inc."
  - **retrieved context (shown to the model):** "We will supply the exact handrail hardware and fasteners specified by brand name in the Statement of Work, with no substitutions. Price Schedule: We have revised the item description on the enclosed Price Schedule to specify "Type 316 stainless fasteners" in place of the generic [...truncated]"
  - **retrieved context (shown to the model):** "NORTHWOODS FABRICATION & ERECTORS, INC. 1487 County Road 550, Marquette, MI 49855 Quote submitted for RFQ 140P6426Q0127 - Fabricate and Install Handrail, Pictured Rocks National Lakeshore Attn: Colette Riegelmayer, Contract Specialist, National Park Service Dear Ms. Riegelmayer, [...truncated]"
  - predicted verdicts in this group:
    - predicted [2cdc4b48] "Complete the attached price schedule in its entirety, including unit prices and total amounts for all line items, without unauthorized edits, and provide the final offer total." — verdict: non_compliant
      - **model's evidence (what it chose to cite):** "We have revised the item description on the enclosed Price Schedule to specify "Type 316 stainless fasteners" in place of the generic wording, to ensure our fabrication shop orders the correct hardware grade; all unit and quantity fields remain as issued."
      - **model's evidence (what it chose to cite):** "Note: the alternate bracket configuration in Item 10A above uses a bracket manufactured by TrailGuard Systems rather than the brand specified in the Statement of Work."
      - **model's reasoning:** The requirement mandates completing the price schedule in its entirety without unauthorized edits. The bidder admits to revising the item description on the Price Schedule, constituting an unauthorized edit, and also proposes a substitution using a different brand for the bracket.
    - predicted [a647393c] "Alternate quotes or proposals will not be accepted." — verdict: non_compliant
      - **model's evidence (what it chose to cite):** "Alternate Item 10A - Fabricate/Install Handrail, Value-Engineered Mounting Bracket: $47,900.00 We are prepared to perform under either configuration at the Government's discretion."
      - **model's reasoning:** The requirement states that alternate quotes or proposals will not be accepted. The bidder explicitly submitted an alternate quote for 'Alternate Item 10A' using a different bracket and stated they are prepared to perform under either configuration, which violates the requirement.

- group of 2 true topic(s) and 1 predicted requirement(s) (not a 1:1 match, so there is no single correct pairing between them):
  - true `prior_experience_count` — "Offers shall submit the following information in its entirety: ... Three prior experiences of projects in similar size and scope per the "TO SUBMIT AN OFFER" section below within the past five years" (acceptable: ['non_compliant'])
      - **expected evidence (true_verdicts.json):** "1. Hiawatha National Forest - Trailhead Guardrail Installation (2022)."
      - **expected evidence (true_verdicts.json):** "2. Marquette County Road Commission - Overlook Handrail Replacement (2021)."
      - **expected reasoning:** Application lists only 2 prior experience references, short of the 3 required.
  - true `prior_experience_poc_required` — "NOTE: Contact information SHALL be provided, to include a brief description of the project, as well as point of contact information" (acceptable: ['compliant'])
      - **expected evidence (true_verdicts.json):** "Point of Contact: Rebecca Sorenson, Facilities Coordinator, USDA Forest Service, (906) 555-4471."
      - **expected evidence (true_verdicts.json):** "Point of Contact: Gary Thibodeau, Project Engineer, Marquette County Road Commission, (906) 555-6023."
      - **expected reasoning:** Both references given include a project description and complete point-of-contact information (name, title, organization, phone).
  - **retrieved context (shown to the model):** "Amendment: We acknowledge that Amendment 0001 to this solicitation exists and confirm that this quote reflects the solicitation as amended. We appreciate your consideration of this quote. Sincerely, Teresa Blackwood Estimator Northwoods Fabrication & Erectors, Inc."
  - **retrieved context (shown to the model):** "NORTHWOODS FABRICATION & ERECTORS, INC. 1487 County Road 550, Marquette, MI 49855 Quote submitted for RFQ 140P6426Q0127 - Fabricate and Install Handrail, Pictured Rocks National Lakeshore Attn: Colette Riegelmayer, Contract Specialist, National Park Service Dear Ms. Riegelmayer, [...truncated]"
  - **retrieved context (shown to the model):** "We will supply the exact handrail hardware and fasteners specified by brand name in the Statement of Work, with no substitutions. Price Schedule: We have revised the item description on the enclosed Price Schedule to specify "Type 316 stainless fasteners" in place of the generic [...truncated]"
  - predicted verdicts in this group:
    - predicted [c42ccbc7] "Provide at least three prior experience references for projects of similar size and scope within the past five years, including brief descriptions and contact information." — verdict: non_compliant
      - **model's evidence (what it chose to cite):** "Prior Experience: 1. Hiawatha National Forest - Trailhead Guardrail Installation (2022). Fabricated and installed 180 linear feet of galvanized guardrail. Contract value: $41,200. Point of Contact: Rebecca Sorenson, Facilities Coordinator, USDA Forest Service, (906) 555-4471. 2. Marquette County Road Commission - Overlook Handrail Replacement (2021). Fabricated and installed 95 linear feet of aluminum handrail at a scenic overlook. Contract value: $22,800. Point of Contact: Gary Thibodeau, Project Engineer, Marquette County Road Commission, (906) 555-6023."
      - **model's reasoning:** The requirement specifies providing at least three prior experience references for projects of similar size and scope within the past five years, including brief descriptions and contact information. The bidder's application only provides two references under the prior experience section, thus failing to meet the minimum quantity of three references.

**Unscored** — split/merge groups excluded from the matrix above (still counted in the two rates above):
- group 1:
  - true `contractor_core_data` — "Offers shall submit the following information in its entirety: ... c) Contractor Core Data: Offerors Company Name: Cage Code / Offerors Unique Entity Identifier (UEI): Offerors POC: Offerors POC Email/Phone:" (acceptable: ['insufficient_information'])
  - true `uei_required` — "To be considered for award your company must obtain a Unique Entity Identifier (UEI)." (acceptable: ['compliant'])
  - predicted [526001ea] "Provide the offeror's company name." — verdict: compliant
  - predicted [bcd513a4] "The company must obtain and provide a Unique Entity Identifier (UEI)." — verdict: compliant
  - predicted [db017c82] "Provide the offeror's point of contact (POC) name, email, and phone number." — verdict: non_compliant
- group 2:
  - true `final_offer_total_no_alternates` — "NOTE: Alternate quotes/proposals will not be accepted. Provide us with the final offer total, as this will be the evaluated price." (acceptable: ['non_compliant'])
  - true `price_schedule_complete` — "Complete attached Price Schedule and insert total unit price and/or amount, in reference to ALL line items listed." (acceptable: ['compliant'])
  - true `price_schedule_must_not_be_edited` — "Must ensure that this document is not edited for any reason (outside of adding units of measure, quantities, etc.) and the unedited Price Schedule is provided with final pricing - if needing to make edits or alter the document, provide an addendum outlining these changes or additional information wanting to make apparent to the evaluators." (acceptable: ['non_compliant'])
  - predicted [2cdc4b48] "Complete the attached price schedule in its entirety, including unit prices and total amounts for all line items, without unauthorized edits, and provide the final offer total." — verdict: non_compliant
  - predicted [a647393c] "Alternate quotes or proposals will not be accepted." — verdict: non_compliant
- group 3:
  - true `prior_experience_count` — "Offers shall submit the following information in its entirety: ... Three prior experiences of projects in similar size and scope per the "TO SUBMIT AN OFFER" section below within the past five years" (acceptable: ['non_compliant'])
  - true `prior_experience_poc_required` — "NOTE: Contact information SHALL be provided, to include a brief description of the project, as well as point of contact information" (acceptable: ['compliant'])
  - predicted [c42ccbc7] "Provide at least three prior experience references for projects of similar size and scope within the past five years, including brief descriptions and contact information." — verdict: non_compliant

## Evidence

**Citation-verified rate** (evidence-level): fraction of evidence quotes actually located in application.txt.
- rate: 94.4% (1 unverified of 18)

**Evidence recall**: does the expected evidence span (from `true_verdicts.json`) show up somewhere in the requirement's retrieved chunks, before the verdict step chose what to cite? Topics never extracted as a requirement are excluded — that failure is already counted by requirement recall above.
- recall: 100.0% (11/11)
- missed:
  - none
