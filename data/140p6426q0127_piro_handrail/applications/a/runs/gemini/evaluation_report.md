# Evaluation report

## Summary metrics

Machine-readable numbers for averaging across tenders -- every value here is explained in the sections below. `null` means the metric doesn't apply to this run (e.g. no verdict-only artifact present).

```json
{
  "requirement_recall": 0.9375,
  "requirement_recall_matched": 15,
  "requirement_recall_total": 16,
  "requirement_precision": 0.5417,
  "citation_verified_rate": 1.0,
  "is_mandatory_accuracy": 0.9,
  "is_mandatory_scored": 10,
  "is_text_verifiable_accuracy": 0.8,
  "is_text_verifiable_scored": 10,
  "verdict_clean_match_count": 6,
  "verdict_accuracy": 1.0,
  "false_compliant_rate": 0.0,
  "false_issue_rate": 0.1111,
  "evidence_citation_verified_rate": 0.9565,
  "evidence_recall": 1.0,
  "verdict_only_accuracy": 0.7857,
  "verdict_only_scored": 14
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
- predicted [0d3ce0da] "Complete the attached price schedule in its entirety, including unit prices and amounts for all line items, ensuring the document is unedited unless an addendum is provided, and include the final offer total as the evaluated price." — verdict: insufficient_information lumps together 3 true requirements:
  - true `final_offer_total_no_alternates` — "NOTE: Alternate quotes/proposals will not be accepted. Provide us with the final offer total, as this will be the evaluated price."
  - true `price_schedule_complete` — "Complete attached Price Schedule and insert total unit price and/or amount, in reference to ALL line items listed."
  - true `price_schedule_must_not_be_edited` — "Must ensure that this document is not edited for any reason (outside of adding units of measure, quantities, etc.) and the unedited Price Schedule is provided with final pricing - if needing to make edits or alter the document, provide an addendum outlining these changes or additional information wanting to make apparent to the evaluators."
- predicted [4d05a7d4] "Provide prior experience references (preferably a minimum of 3) for projects of similar size, scope, and quality completed within the past five years, including brief descriptions and point of contact information." — verdict: non_compliant lumps together 2 true requirements:
  - true `prior_experience_count` — "Offers shall submit the following information in its entirety: ... Three prior experiences of projects in similar size and scope per the "TO SUBMIT AN OFFER" section below within the past five years"
  - true `prior_experience_poc_required` — "NOTE: Contact information SHALL be provided, to include a brief description of the project, as well as point of contact information"

**Tangled** (1) — several true and several predicted requirements all overlapping at once:
- tangle of 2 true and 3 predicted requirements, all overlapping — needs manual untangling:
  - true `contractor_core_data` — "Offers shall submit the following information in its entirety: ... c) Contractor Core Data: Offerors Company Name: Cage Code / Offerors Unique Entity Identifier (UEI): Offerors POC: Offerors POC Email/Phone:"
  - true `uei_required` — "To be considered for award your company must obtain a Unique Entity Identifier (UEI)."
  - predicted [21e353ca] "The company must obtain and provide a Unique Entity Identifier (UEI)." — verdict: compliant
  - predicted [83a49546] "Provide the offeror's point of contact name, email, and phone number." — verdict: compliant
  - predicted [c179e557] "Provide the offeror's company name." — verdict: compliant

## Requirement precision

**Citation-verified rate** (hallucination check): fraction of predicted requirements whose citation was actually located in tender.txt (exactly or via fuzzy match).
- rate: 100.0%
- unverified:
  - none

**Classification precision**: fraction of predicted requirements that matched a true requirement.
- rate: 54.2%
- unexplained (11) — the model recognized these as requirements, but they don't match any true requirement. "closest true topic" is a mechanical (no-LLM) embedding-similarity lookup against every true topic's description; "dedup visibility" checks whether dedup's own cosine pre-filter would have clustered this candidate with whatever predicted requirement DID match that topic -- i.e. whether the dedup LLM call ever had a chance to compare them:
  - predicted [111b9452] "Independently, and not as an agent of the Government, the contractor/vendor shall furnish all labor, materials, equipment, mobilization, and demobilization necessary to fabricate and install a handrail at Pictured Rocks National Lakeshore (PIRO)."
    - **similarity check:** closest true topic: `contractor_core_data` (cosine=0.62); vs matched predicted [c179e557]: cosine=0.55 (< dedup threshold 0.6) -> dedup's cosine pre-filter would NOT have clustered these -- the dedup LLM call never saw them side by side
  - predicted [20b82603] "Offerors are urged and expected to inspect the site and satisfy themselves regarding general and local conditions affecting contract performance."
    - **similarity check:** closest true topic: `or_equal_product_documentation` (cosine=0.60); vs matched predicted [3575ce40]: cosine=0.60 (< dedup threshold 0.6) -> dedup's cosine pre-filter would NOT have clustered these -- the dedup LLM call never saw them side by side
  - predicted [2734d1a7] "The Offeror must represent whether or not it is a corporation that was convicted of a felony criminal violation under a Federal law within the preceding 24 months."
    - **similarity check:** closest true topic: `no_recent_felony_conviction` (cosine=0.74); vs matched predicted [44d4eab3]: cosine=0.78 (>= dedup threshold 0.6) -> would likely have been clustered together and compared by the dedup LLM call
  - predicted [45482ed2] "Attach a copy of the vendor invoice in PDF format to the IPP invoice, showing pricing breakdown, contract number, dates of service, invoice date, and vendor letterhead."
    - **similarity check:** closest true topic: `contractor_core_data` (cosine=0.60); vs matched predicted [c179e557]: cosine=0.55 (< dedup threshold 0.6) -> dedup's cosine pre-filter would NOT have clustered these -- the dedup LLM call never saw them side by side
  - predicted [53dc841e] "Quotes must follow the submission requirements, details, order, and checklist provided in the solicitation sections."
    - **similarity check:** closest true topic: `or_equal_product_documentation` (cosine=0.68); vs matched predicted [3575ce40]: cosine=0.72 (>= dedup threshold 0.6) -> would likely have been clustered together and compared by the dedup LLM call
  - predicted [85a5d7f8] "Provide written confirmation of specialization or documented direct experience in providing all labor, material, tools, supervision, and travel for the service."
    - **similarity check:** closest true topic: `capabilities_statement_required` (cosine=0.70); vs matched predicted [5a3c7965]: cosine=0.64 (>= dedup threshold 0.6) -> would likely have been clustered together and compared by the dedup LLM call
  - predicted [adb13844] "The Offeror must represent whether or not it is a corporation that has any unpaid Federal tax liability that has been assessed, for which all judicial and administrative remedies have been exhausted or have lapsed, and that is not being paid in a timely manner pursuant to an agreement with the authority responsible for collecting the tax liability."
    - **similarity check:** closest true topic: `no_unpaid_federal_tax_liability` (cosine=0.68); vs matched predicted [66934451]: cosine=0.87 (>= dedup threshold 0.6) -> would likely have been clustered together and compared by the dedup LLM call
  - predicted [b80cbcb9] "If unable to use IPP for submitting invoices, submit a written waiver request to the Contracting Officer with the proposal or quotation."
    - **similarity check:** closest true topic: `contractor_core_data` (cosine=0.61); vs matched predicted [c179e557]: cosine=0.51 (< dedup threshold 0.6) -> dedup's cosine pre-filter would NOT have clustered these -- the dedup LLM call never saw them side by side
  - predicted [cf9f1bc1] "Quotes are due by 9 September 2026 at 12 PM ET."
    - **similarity check:** closest true topic: `or_equal_product_documentation` (cosine=0.56); vs matched predicted [3575ce40]: cosine=0.57 (< dedup threshold 0.6) -> dedup's cosine pre-filter would NOT have clustered these -- the dedup LLM call never saw them side by side
  - predicted [e8130a06] "Questions regarding the solicitation will only be accepted until 1 September 2026 at 12 PM ET."
    - **similarity check:** closest true topic: `final_offer_total_no_alternates` (cosine=0.64); vs matched predicted [0d3ce0da]: cosine=0.63 (>= dedup threshold 0.6) -> would likely have been clustered together and compared by the dedup LLM call
  - predicted [f49d216a] "Payment requests must be submitted electronically through the U.S. Department of the Treasury's Invoice Processing Platform (IPP) website."
    - **similarity check:** closest true topic: `contractor_core_data` (cosine=0.66); vs matched predicted [c179e557]: cosine=0.56 (< dedup threshold 0.6) -> dedup's cosine pre-filter would NOT have clustered these -- the dedup LLM call never saw them side by side

## Coverage flags

Clean 1:1 matches (recall counted them as found) whose citations don't fully overlap in length, split by which side is off. Over-split/over-merge/tangled matches are excluded here -- their predicted fragments are inherently partial by construction, already shown in the recall breakdown above.

**Requirements captured with extra text** (0) — the predicted citation is padded beyond the true one:
- none

**Requirements captured incompletely** (0) — the predicted citation misses part of the true one:
- none

## is_mandatory accuracy

For each clean or one-to-many match (tangled groups excluded — there's no single "one" to compare against), does `is_mandatory` agree with the true value? A one-to-many group counts as correct only if every member on the "many" side agrees with the "one".

**Accuracy: 90.0% (10 groups)**

Mismatched:
- true: `amendment_acknowledgment_if_posted`=False; predicted: `d162a6af`=True — "NOTE: Please check SAM.gov regularly in any case an amendment was posted, as this amendment must be reviewed, acknowledged by signing the SF30 and ensuring that it is provided with your final quote/proposal package."

## is_text_verifiable accuracy

For each clean or one-to-many match (tangled groups excluded), does `is_text_verifiable` agree with the true value (all-or-nothing on the "many" side, same rule as is_mandatory above)? A wrong `false` here means the pipeline skips verdict generation for a requirement that should get one.

**Accuracy: 80.0% (10 groups)**

Mismatched:
- true: `sam_registration_active`=False; predicted: `d73e9d83`=True — "This registration must be "active" in SAM. NO EXCEPTIONS."
- true: `submission_deadline_and_channel`=False; predicted: `01e71e4d`=True — "Submit all required documents via email by the date and time listed in this solicitation. Offerors are responsible for submitting quotes/proposals so as to reach the Government office designated in the solicitation by the time specified in the solicitation. Late quotes/proposals will not be accepted."

## Verdict accuracy

The confusion matrix covers only clean 1:1 matches — split/merge groups have no single pair to plot, but still count in the two rates below.

Clean matches scored: 6

| true \ pipeline said | `compliant` | `non_compliant` | `contradictory` | `insufficient_information` |
|---|---|---|---|---|
| `compliant` | 4 | 1 | 0 | 0 |
| `non_compliant` | 0 | 1 | 0 | 0 |
| `contradictory` | 0 | 0 | 0 | 0 |
| `insufficient_information` | 0 | 0 | 0 | 0 |

Why some rows are empty:
- `contradictory` row is empty: true `small_business_size_standard` — never extracted (recall miss)
- `insufficient_information` row is empty: true `price_schedule_must_not_be_edited` — over_merge match — no single pair to plot

**Mismatched clean matches** — every off-diagonal cell above, in full: the full context retrieved and shown to the model, what it chose to cite from that context, and its reasoning ("model's ..."), next to what `true_verdicts.json` expects ("expected ...").

- none

**False-compliant rate** — dangerous direction: the true verdict requires an issue (anything but `compliant`), but every predicted verdict in the group is `compliant`.
- rate: 0.0%

- none

**False-issue rate** — mirror direction: the true verdict is `compliant` only, but the pipeline raised an issue anyway.
- rate: 11.1%

- group of 3 true topic(s) and 1 predicted requirement(s) (not a 1:1 match, so there is no single correct pairing between them):
  - true `final_offer_total_no_alternates` — "NOTE: Alternate quotes/proposals will not be accepted. Provide us with the final offer total, as this will be the evaluated price." (acceptable: ['compliant'])
      - **expected evidence (true_verdicts.json):** "Total: $58,750.00"
      - **expected reasoning:** Application provides exactly one total price for the single line item, with no alternate quotes or competing price options presented.
  - true `price_schedule_complete` — "Complete attached Price Schedule and insert total unit price and/or amount, in reference to ALL line items listed." (acceptable: ['compliant'])
      - **expected evidence (true_verdicts.json):** "Item Number 10: Fabricate/Install Handrail (includes mob/demob, supplies, labor)"
      - **expected evidence (true_verdicts.json):** "Total: $58,750.00"
      - **expected reasoning:** Item 10 price and total are both filled in.
  - true `price_schedule_must_not_be_edited` — "Must ensure that this document is not edited for any reason (outside of adding units of measure, quantities, etc.) and the unedited Price Schedule is provided with final pricing - if needing to make edits or alter the document, provide an addendum outlining these changes or additional information wanting to make apparent to the evaluators." (acceptable: ['insufficient_information'])
      - **expected evidence (true_verdicts.json):** none
      - **expected reasoning:** The application shows a filled-in price schedule (item, price, total) but never represents, one way or the other, whether the underlying template itself was left unedited. Nothing in application.txt lets a text-only check confirm or deny this, so insufficient_information is the only defensible call -- compliant would be false confidence, non_compliant would be an unjustified accusation.
  - **retrieved context (shown to the model):** "QUOTE SUBMISSION In Response to Solicitation 140P6426Q0127 Fabricate and Install Handrail - Pictured Rocks National Lakeshore (PIRO) Submitted to: Colette Riegelmayer, Contract Specialist, National Park Service Submitted by: Superior Rail & Fabrication, LLC CHECKLIST FOR QUOTE SU [...truncated]"
  - **retrieved context (shown to the model):** "2. City of Marquette - Harborfront Park Railing Installation (2022) Fabricated and installed aluminum guardrail and handrail systems along a 210-foot elevated walkway. Contract value: $64,500. Point of Contact: Daniel Ruiz, Public Works Director, City of Marquette, (906) 555-3387 [...truncated]"
  - **retrieved context (shown to the model):** "CAPABILITIES STATEMENT / PROJECT NARRATIVE Superior Rail & Fabrication, LLC has maintained average annual gross revenue of $12.4 million over the past three fiscal years, comfortably within the $19 million small business size standard associated with NAICS code 238990. Our compan [...truncated]"
  - **retrieved context (shown to the model):** "REPRESENTATIONS AND CERTIFICATIONS 52.209-11 Representation Regarding Delinquent Tax Liability or Felony Conviction: (1) Superior Rail & Fabrication, LLC is not a corporation that has any unpaid Federal tax liability that has been assessed, for which all judicial and administrati [...truncated]"
  - predicted verdicts in this group:
    - predicted [0d3ce0da] "Complete the attached price schedule in its entirety, including unit prices and amounts for all line items, ensuring the document is unedited unless an addendum is provided, and include the final offer total as the evaluated price." — verdict: insufficient_information
      - **model's evidence (what it chose to cite):** "We confirm the following documents are included in this quote package: Checklist for Quote Submittal, Price Schedule, Detailed Capabilities Statement / Project Narrative, Prior Experience References, and Contractor Core Data."
      - **model's evidence (what it chose to cite):** "PRICE SCHEDULE Item Number 10: Fabricate/Install Handrail (includes mob/demob, supplies, labor) Price: $58,750.00 Total: $58,750.00"
      - **model's reasoning:** The excerpts mention that a Price Schedule was included and provide a partial line item for Item Number 10 with a total price, but they do not provide the complete price schedule, nor do they show whether the document was unedited in its entirety as required.

**Unscored** — split/merge groups excluded from the matrix above (still counted in the two rates above):
- group 1:
  - true `contractor_core_data` — "Offers shall submit the following information in its entirety: ... c) Contractor Core Data: Offerors Company Name: Cage Code / Offerors Unique Entity Identifier (UEI): Offerors POC: Offerors POC Email/Phone:" (acceptable: ['compliant'])
  - true `uei_required` — "To be considered for award your company must obtain a Unique Entity Identifier (UEI)." (acceptable: ['compliant'])
  - predicted [21e353ca] "The company must obtain and provide a Unique Entity Identifier (UEI)." — verdict: compliant
  - predicted [83a49546] "Provide the offeror's point of contact name, email, and phone number." — verdict: compliant
  - predicted [c179e557] "Provide the offeror's company name." — verdict: compliant
- group 2:
  - true `final_offer_total_no_alternates` — "NOTE: Alternate quotes/proposals will not be accepted. Provide us with the final offer total, as this will be the evaluated price." (acceptable: ['compliant'])
  - true `price_schedule_complete` — "Complete attached Price Schedule and insert total unit price and/or amount, in reference to ALL line items listed." (acceptable: ['compliant'])
  - true `price_schedule_must_not_be_edited` — "Must ensure that this document is not edited for any reason (outside of adding units of measure, quantities, etc.) and the unedited Price Schedule is provided with final pricing - if needing to make edits or alter the document, provide an addendum outlining these changes or additional information wanting to make apparent to the evaluators." (acceptable: ['insufficient_information'])
  - predicted [0d3ce0da] "Complete the attached price schedule in its entirety, including unit prices and amounts for all line items, ensuring the document is unedited unless an addendum is provided, and include the final offer total as the evaluated price." — verdict: insufficient_information
- group 3:
  - true `prior_experience_count` — "Offers shall submit the following information in its entirety: ... Three prior experiences of projects in similar size and scope per the "TO SUBMIT AN OFFER" section below within the past five years" (acceptable: ['compliant', 'insufficient_information'])
  - true `prior_experience_poc_required` — "NOTE: Contact information SHALL be provided, to include a brief description of the project, as well as point of contact information" (acceptable: ['non_compliant', 'insufficient_information'])
  - predicted [4d05a7d4] "Provide prior experience references (preferably a minimum of 3) for projects of similar size, scope, and quality completed within the past five years, including brief descriptions and point of contact information." — verdict: non_compliant

## Evidence

**Citation-verified rate** (evidence-level): fraction of evidence quotes actually located in application.txt.
- rate: 95.7% (1 unverified of 23)

**Evidence recall**: does the expected evidence span (from `true_verdicts.json`) show up somewhere in the requirement's retrieved chunks, before the verdict step chose what to cite? Topics never extracted as a requirement are excluded — that failure is already counted by requirement recall above.
- recall: 100.0% (11/11)
- missed:
  - none

## Verdict-only evaluation

Runs verdict generation directly on true_requirements.json's own text and citations against application.txt, bypassing requirement extraction and match-group sequencing entirely -- isolates whether generate_verdict, given a perfect requirement, makes the right call. Only mismatches are listed below.

**Accuracy: 78.6% (11/14)**

- `price_schedule_complete` — acceptable: ['compliant'], predicted: non_compliant
  - **requirement:** "Offeror must complete the attached Price Schedule in its entirety, unedited except for units/quantities, no alternates."
  - **retrieved context (shown to the model):** "QUOTE SUBMISSION In Response to Solicitation 140P6426Q0127 Fabricate and Install Handrail - Pictured Rocks National Lakeshore (PIRO) Submitted to: Colette Riegelmayer, Contract Specialist, National Park Service Submitted by: Superior Rail & Fabrication, LLC CHECKLIST FOR QUOTE SUBMITTAL We confirm the following documents are included in this quote package: Checklist for Quote Submittal, Price Schedule, Detailed Capabilities Statement / Project Narrative, Prior Experience References, and Contractor Core Data. CONTRACTOR CORE DATA Company Name: Superior Rail & Fabrication, LLC Cage Code: 7RTK9 Unique Entity Identifier (UEI): SRF7X92LM814 Point of Contact: John Castellano, Project Manager POC Email/Phone: j.castellano@superiorrailfab.com / (231) 555-0142 REGISTRATION AND ELIGIBILITY Superior Rail & Fabrication, LLC is a small business under NAICS code 238990. Our company's registration in the System for Award Management (SAM) is active and will remain active through quote submission, award, and the entire period of contract performance. Our Unique Entity Identifier is provided above. REPRESENTATIONS AND CERTIFICATIONS"
  - **retrieved context (shown to the model):** "2. City of Marquette - Harborfront Park Railing Installation (2022) Fabricated and installed aluminum guardrail and handrail systems along a 210-foot elevated walkway. Contract value: $64,500. Point of Contact: Daniel Ruiz, Public Works Director, City of Marquette, (906) 555-3387. 3. We have also completed various municipal handrail and railing projects throughout the Upper Peninsula over the years, consistently meeting client specifications and timelines. PRICE SCHEDULE Item Number 10: Fabricate/Install Handrail (includes mob/demob, supplies, labor) Price: $58,750.00 Total: $58,750.00 FINANCIAL AND BONDING INFORMATION For purposes of confirming our financial capacity, we note that in fiscal year 2024 Superior Rail & Fabrication, LLC's average annual revenue for size-standard purposes was $21.8 million, computed across our fabrication and installation divisions. We look forward to the opportunity to support Pictured Rocks National Lakeshore on this project. Respectfully submitted, John Castellano Project Manager Superior Rail & Fabrication, LLC"
  - **retrieved context (shown to the model):** "CAPABILITIES STATEMENT / PROJECT NARRATIVE Superior Rail & Fabrication, LLC has maintained average annual gross revenue of $12.4 million over the past three fiscal years, comfortably within the $19 million small business size standard associated with NAICS code 238990. Our company specializes in the fabrication and installation of steel, aluminum, and stainless-steel handrail systems for federal, state, and municipal facilities, including compliance with applicable ADA and local building code requirements. Our crews are equipped to perform site measurement, custom fabrication in our own shop, and on-site installation, including all mobilization, demobilization, supplies, and labor described in Item 0010 of the Schedule of Supplies. Shop drawings and product data sheets for the proposed handrail system are included as Attachment A to this quote package. For portions of the handrail hardware, we intend to substitute equivalent stainless-steel fasteners from an alternate manufacturer other than the brand specified in the Statement of Work, in order to avoid current supply delays with the named manufacturer. PRIOR EXPERIENCE REFERENCES 1. Isle Royale National Park - Boardwalk Handrail Replacement (2023) Fabricated and installed 340 linear feet of galvanized steel handrail along the visitor boardwalk. Contract value: $86,000. Point of Contact: Maria Alvarez, Facility Manager, National Park Service, (906) 555-2210."
  - **retrieved context (shown to the model):** "REPRESENTATIONS AND CERTIFICATIONS 52.209-11 Representation Regarding Delinquent Tax Liability or Felony Conviction: (1) Superior Rail & Fabrication, LLC is not a corporation that has any unpaid Federal tax liability that has been assessed, for which all judicial and administrative remedies have been exhausted or have lapsed, and that is not being paid in a timely manner pursuant to an agreement with the authority responsible for collecting the tax liability. (2) Superior Rail & Fabrication, LLC is not a corporation that was convicted of a felony criminal violation under a Federal law within the preceding 24 months. 52.225-20 / 52.225-25 Restricted Business Operations - Certification: Superior Rail & Fabrication, LLC certifies that it does not conduct restricted business operations in Sudan and does not engage in any activities or transactions relating to Iran that would be prohibited under the applicable FAR clauses. 52.222-18 Certification Regarding Knowledge of Child Labor: Superior Rail & Fabrication, LLC certifies that, to the best of its knowledge, none of the end products to be delivered under this contract were produced by forced or indentured child labor. 52.225-2 Buy American Certificate: Superior Rail & Fabrication, LLC certifies that all end products to be delivered under this contract are domestic end products as defined in FAR 52.225-1, Buy American-Supplies. CAPABILITIES STATEMENT / PROJECT NARRATIVE"
  - **model's evidence (what it chose to cite):** "For portions of the handrail hardware, we intend to substitute equivalent stainless-steel fasteners from an alternate manufacturer other than the brand specified in the Statement of Work, in order to avoid current supply delays with the named manufacturer."
  - **model's reasoning:** The requirement states that the Price Schedule must be unedited and that there shall be no alternates. However, the bidder explicitly states in their capabilities statement/project narrative that they intend to substitute equivalent stainless-steel fasteners from an alternate manufacturer, thereby violating the restriction on alternates.
  - **expected evidence (true_verdicts.json):** "Item Number 10: Fabricate/Install Handrail (includes mob/demob, supplies, labor)"
  - **expected evidence (true_verdicts.json):** "Total: $58,750.00"
  - **expected reasoning (true_verdicts.json):** Item 10 price and total are both filled in.

- `prior_experience_count` — acceptable: ['compliant', 'insufficient_information'], predicted: non_compliant
  - **requirement:** "Must provide at least 3 prior experience references for projects similar in size and scope, completed within the past 5 years."
  - **retrieved context (shown to the model):** "REPRESENTATIONS AND CERTIFICATIONS 52.209-11 Representation Regarding Delinquent Tax Liability or Felony Conviction: (1) Superior Rail & Fabrication, LLC is not a corporation that has any unpaid Federal tax liability that has been assessed, for which all judicial and administrative remedies have been exhausted or have lapsed, and that is not being paid in a timely manner pursuant to an agreement with the authority responsible for collecting the tax liability. (2) Superior Rail & Fabrication, LLC is not a corporation that was convicted of a felony criminal violation under a Federal law within the preceding 24 months. 52.225-20 / 52.225-25 Restricted Business Operations - Certification: Superior Rail & Fabrication, LLC certifies that it does not conduct restricted business operations in Sudan and does not engage in any activities or transactions relating to Iran that would be prohibited under the applicable FAR clauses. 52.222-18 Certification Regarding Knowledge of Child Labor: Superior Rail & Fabrication, LLC certifies that, to the best of its knowledge, none of the end products to be delivered under this contract were produced by forced or indentured child labor. 52.225-2 Buy American Certificate: Superior Rail & Fabrication, LLC certifies that all end products to be delivered under this contract are domestic end products as defined in FAR 52.225-1, Buy American-Supplies. CAPABILITIES STATEMENT / PROJECT NARRATIVE"
  - **retrieved context (shown to the model):** "QUOTE SUBMISSION In Response to Solicitation 140P6426Q0127 Fabricate and Install Handrail - Pictured Rocks National Lakeshore (PIRO) Submitted to: Colette Riegelmayer, Contract Specialist, National Park Service Submitted by: Superior Rail & Fabrication, LLC CHECKLIST FOR QUOTE SUBMITTAL We confirm the following documents are included in this quote package: Checklist for Quote Submittal, Price Schedule, Detailed Capabilities Statement / Project Narrative, Prior Experience References, and Contractor Core Data. CONTRACTOR CORE DATA Company Name: Superior Rail & Fabrication, LLC Cage Code: 7RTK9 Unique Entity Identifier (UEI): SRF7X92LM814 Point of Contact: John Castellano, Project Manager POC Email/Phone: j.castellano@superiorrailfab.com / (231) 555-0142 REGISTRATION AND ELIGIBILITY Superior Rail & Fabrication, LLC is a small business under NAICS code 238990. Our company's registration in the System for Award Management (SAM) is active and will remain active through quote submission, award, and the entire period of contract performance. Our Unique Entity Identifier is provided above. REPRESENTATIONS AND CERTIFICATIONS"
  - **retrieved context (shown to the model):** "2. City of Marquette - Harborfront Park Railing Installation (2022) Fabricated and installed aluminum guardrail and handrail systems along a 210-foot elevated walkway. Contract value: $64,500. Point of Contact: Daniel Ruiz, Public Works Director, City of Marquette, (906) 555-3387. 3. We have also completed various municipal handrail and railing projects throughout the Upper Peninsula over the years, consistently meeting client specifications and timelines. PRICE SCHEDULE Item Number 10: Fabricate/Install Handrail (includes mob/demob, supplies, labor) Price: $58,750.00 Total: $58,750.00 FINANCIAL AND BONDING INFORMATION For purposes of confirming our financial capacity, we note that in fiscal year 2024 Superior Rail & Fabrication, LLC's average annual revenue for size-standard purposes was $21.8 million, computed across our fabrication and installation divisions. We look forward to the opportunity to support Pictured Rocks National Lakeshore on this project. Respectfully submitted, John Castellano Project Manager Superior Rail & Fabrication, LLC"
  - **retrieved context (shown to the model):** "CAPABILITIES STATEMENT / PROJECT NARRATIVE Superior Rail & Fabrication, LLC has maintained average annual gross revenue of $12.4 million over the past three fiscal years, comfortably within the $19 million small business size standard associated with NAICS code 238990. Our company specializes in the fabrication and installation of steel, aluminum, and stainless-steel handrail systems for federal, state, and municipal facilities, including compliance with applicable ADA and local building code requirements. Our crews are equipped to perform site measurement, custom fabrication in our own shop, and on-site installation, including all mobilization, demobilization, supplies, and labor described in Item 0010 of the Schedule of Supplies. Shop drawings and product data sheets for the proposed handrail system are included as Attachment A to this quote package. For portions of the handrail hardware, we intend to substitute equivalent stainless-steel fasteners from an alternate manufacturer other than the brand specified in the Statement of Work, in order to avoid current supply delays with the named manufacturer. PRIOR EXPERIENCE REFERENCES 1. Isle Royale National Park - Boardwalk Handrail Replacement (2023) Fabricated and installed 340 linear feet of galvanized steel handrail along the visitor boardwalk. Contract value: $86,000. Point of Contact: Maria Alvarez, Facility Manager, National Park Service, (906) 555-2210."
  - **model's evidence (what it chose to cite):** "2. City of Marquette - Harborfront Park Railing Installation (2022) Fabricated and installed aluminum guardrail and handrail systems along a 210-foot elevated walkway. Contract value: $64,500. Point of Contact: Daniel Ruiz, Public Works Director, City of Marquette, (906) 555-3387. 3. We have also completed various municipal handrail and railing projects throughout the Upper Peninsula over the years, consistently meeting client specifications and timelines."
  - **model's evidence (what it chose to cite):** "PRIOR EXPERIENCE REFERENCES 1. Isle Royale National Park - Boardwalk Handrail Replacement (2023) Fabricated and installed 340 linear feet of galvanized steel handrail along the visitor boardwalk. Contract value: $86,000. Point of Contact: Maria Alvarez, Facility Manager, National Park Service, (906) 555-2210."
  - **model's reasoning:** The requirement states that the bidder must provide at least 3 prior experience references for similar projects completed within the past 5 years. While the bidder provided detailed references for project 1 (Isle Royale National Park, 2023) and project 2 (City of Marquette, 2022), the third mention is a vague statement referring generally to "various municipal handrail and railing projects" without specific details, dates, or contact information. Therefore, only two valid prior experience references are provided, failing to meet the minimum requirement of 3.
  - **expected evidence (true_verdicts.json):** "1. Isle Royale National Park - Boardwalk Handrail Replacement (2023) Fabricated and installed 340 linear feet of galvanized steel handrail along the visitor boardwalk. Contract value: $86,000."
  - **expected evidence (true_verdicts.json):** "2. City of Marquette - Harborfront Park Railing Installation (2022) Fabricated and installed aluminum guardrail and handrail systems along a 210-foot elevated walkway. Contract value: $64,500."
  - **expected evidence (true_verdicts.json):** "3. We have also completed various municipal handrail and railing projects throughout the Upper Peninsula over the years, consistently meeting client specifications and timelines."
  - **expected reasoning (true_verdicts.json):** Three distinct engagements are named, satisfying the count. The third is described only in general terms ('various municipal handrail and railing projects... over the years') without a specific project or contract value, which is a defensible basis for either a clean compliant call or a more cautious insufficient_information call about whether it truly matches the 'similar size and scope' bar -- non_compliant would be wrong, since three references genuinely are present.

- `prior_experience_poc_required` — acceptable: ['non_compliant', 'insufficient_information'], predicted: compliant
  - **requirement:** "Each prior experience reference must include a project description and point-of-contact information."
  - **retrieved context (shown to the model):** "QUOTE SUBMISSION In Response to Solicitation 140P6426Q0127 Fabricate and Install Handrail - Pictured Rocks National Lakeshore (PIRO) Submitted to: Colette Riegelmayer, Contract Specialist, National Park Service Submitted by: Superior Rail & Fabrication, LLC CHECKLIST FOR QUOTE SUBMITTAL We confirm the following documents are included in this quote package: Checklist for Quote Submittal, Price Schedule, Detailed Capabilities Statement / Project Narrative, Prior Experience References, and Contractor Core Data. CONTRACTOR CORE DATA Company Name: Superior Rail & Fabrication, LLC Cage Code: 7RTK9 Unique Entity Identifier (UEI): SRF7X92LM814 Point of Contact: John Castellano, Project Manager POC Email/Phone: j.castellano@superiorrailfab.com / (231) 555-0142 REGISTRATION AND ELIGIBILITY Superior Rail & Fabrication, LLC is a small business under NAICS code 238990. Our company's registration in the System for Award Management (SAM) is active and will remain active through quote submission, award, and the entire period of contract performance. Our Unique Entity Identifier is provided above. REPRESENTATIONS AND CERTIFICATIONS"
  - **retrieved context (shown to the model):** "REPRESENTATIONS AND CERTIFICATIONS 52.209-11 Representation Regarding Delinquent Tax Liability or Felony Conviction: (1) Superior Rail & Fabrication, LLC is not a corporation that has any unpaid Federal tax liability that has been assessed, for which all judicial and administrative remedies have been exhausted or have lapsed, and that is not being paid in a timely manner pursuant to an agreement with the authority responsible for collecting the tax liability. (2) Superior Rail & Fabrication, LLC is not a corporation that was convicted of a felony criminal violation under a Federal law within the preceding 24 months. 52.225-20 / 52.225-25 Restricted Business Operations - Certification: Superior Rail & Fabrication, LLC certifies that it does not conduct restricted business operations in Sudan and does not engage in any activities or transactions relating to Iran that would be prohibited under the applicable FAR clauses. 52.222-18 Certification Regarding Knowledge of Child Labor: Superior Rail & Fabrication, LLC certifies that, to the best of its knowledge, none of the end products to be delivered under this contract were produced by forced or indentured child labor. 52.225-2 Buy American Certificate: Superior Rail & Fabrication, LLC certifies that all end products to be delivered under this contract are domestic end products as defined in FAR 52.225-1, Buy American-Supplies. CAPABILITIES STATEMENT / PROJECT NARRATIVE"
  - **retrieved context (shown to the model):** "2. City of Marquette - Harborfront Park Railing Installation (2022) Fabricated and installed aluminum guardrail and handrail systems along a 210-foot elevated walkway. Contract value: $64,500. Point of Contact: Daniel Ruiz, Public Works Director, City of Marquette, (906) 555-3387. 3. We have also completed various municipal handrail and railing projects throughout the Upper Peninsula over the years, consistently meeting client specifications and timelines. PRICE SCHEDULE Item Number 10: Fabricate/Install Handrail (includes mob/demob, supplies, labor) Price: $58,750.00 Total: $58,750.00 FINANCIAL AND BONDING INFORMATION For purposes of confirming our financial capacity, we note that in fiscal year 2024 Superior Rail & Fabrication, LLC's average annual revenue for size-standard purposes was $21.8 million, computed across our fabrication and installation divisions. We look forward to the opportunity to support Pictured Rocks National Lakeshore on this project. Respectfully submitted, John Castellano Project Manager Superior Rail & Fabrication, LLC"
  - **retrieved context (shown to the model):** "CAPABILITIES STATEMENT / PROJECT NARRATIVE Superior Rail & Fabrication, LLC has maintained average annual gross revenue of $12.4 million over the past three fiscal years, comfortably within the $19 million small business size standard associated with NAICS code 238990. Our company specializes in the fabrication and installation of steel, aluminum, and stainless-steel handrail systems for federal, state, and municipal facilities, including compliance with applicable ADA and local building code requirements. Our crews are equipped to perform site measurement, custom fabrication in our own shop, and on-site installation, including all mobilization, demobilization, supplies, and labor described in Item 0010 of the Schedule of Supplies. Shop drawings and product data sheets for the proposed handrail system are included as Attachment A to this quote package. For portions of the handrail hardware, we intend to substitute equivalent stainless-steel fasteners from an alternate manufacturer other than the brand specified in the Statement of Work, in order to avoid current supply delays with the named manufacturer. PRIOR EXPERIENCE REFERENCES 1. Isle Royale National Park - Boardwalk Handrail Replacement (2023) Fabricated and installed 340 linear feet of galvanized steel handrail along the visitor boardwalk. Contract value: $86,000. Point of Contact: Maria Alvarez, Facility Manager, National Park Service, (906) 555-2210."
  - **model's evidence (what it chose to cite):** "1. Isle Royale National Park - Boardwalk Handrail Replacement (2023) Fabricated and installed 340 linear feet of galvanized steel handrail along the visitor boardwalk. Contract value: $86,000. Point of Contact: Maria Alvarez, Facility Manager, National Park Service, (906) 555-2210."
  - **model's evidence (what it chose to cite):** "2. City of Marquette - Harborfront Park Railing Installation (2022) Fabricated and installed aluminum guardrail and handrail systems along a 210-foot elevated walkway. Contract value: $64,500. Point of Contact: Daniel Ruiz, Public Works Director, City of Marquette, (906) 555-3387."
  - **model's reasoning:** The bidder provided prior experience references that each include both a detailed project description and complete point-of-contact information, thereby fully satisfying the requirement.
  - **expected evidence (true_verdicts.json):** "Point of Contact: Maria Alvarez, Facility Manager, National Park Service, (906) 555-2210."
  - **expected evidence (true_verdicts.json):** "Point of Contact: Daniel Ruiz, Public Works Director, City of Marquette, (906) 555-3387."
  - **expected evidence (true_verdicts.json):** "3. We have also completed various municipal handrail and railing projects throughout the Upper Peninsula over the years, consistently meeting client specifications and timelines."
  - **expected reasoning (true_verdicts.json):** References 1 and 2 both include complete point-of-contact information. Reference 3 gives no point of contact at all, so the requirement's explicit 'contact information SHALL be provided' is unmet for that entry. non_compliant is the more precise call (a clear violation for one of three references); insufficient_information is also acceptable if the pipeline treats partial fulfillment as unable to confirm rather than as a clean fail. compliant is unacceptable -- it would miss a verifiable, unambiguous gap.
