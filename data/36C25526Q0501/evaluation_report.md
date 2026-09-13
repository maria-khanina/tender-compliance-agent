# Evaluation report

## Summary metrics

Machine-readable numbers for averaging across tenders -- every value here is explained in the sections below. `null` means the metric doesn't apply to this run (e.g. no verdict-only artifact present).

```json
{
  "requirement_recall": 0.9375,
  "requirement_recall_matched": 15,
  "requirement_recall_total": 16,
  "requirement_precision": 0.5714,
  "citation_verified_rate": 1.0,
  "is_mandatory_accuracy": 0.9231,
  "is_mandatory_scored": 13,
  "is_text_verifiable_accuracy": 0.8462,
  "is_text_verifiable_scored": 13,
  "verdict_clean_match_count": 5,
  "verdict_accuracy": 0.8,
  "false_compliant_rate": 0.1111,
  "false_issue_rate": 0.1111,
  "evidence_citation_verified_rate": 0.8548,
  "evidence_recall": 1.0,
  "verdict_only_accuracy": null,
  "verdict_only_scored": null
}
```

## Requirement recall

For each `true_requirements.json` topic, did the pipeline extract something whose tender.txt citation overlaps the true one? A pure text-offset check, not a judgment of meaning — see coverage flags below for extractions that are technically "found" but sloppy.

**Recall: 93.8% (15/16)**

**Missed** (1) — no overlapping predicted requirement at all. "chunk check" is a mechanical (no-LLM) re-chunking of the source document: whether this topic's matching text ever appeared whole in one chunk handed to the extraction model, or was split across chunks.
- true `price_schedule_completion` — "0001 | NEW ACQUISITION FOR TRIENNIAL ELECTRICAL TESTING MAINTENANCE, TESTING, INSPECTION, AND/OR CALIBRATION OF THE ELECTRICAL POWER DISTRIBUTION SYSTEM LOCATED AT TRUMAN VA, COLUMBIA, MO ONE-YEAR, STANDALONE CONTRACT | 1.00 | JB | __________________ | __________________ ... GRAND TOTAL __________________"
    - **chunk check:** [1272:1543] whole, in chunk 0 -- the model saw this text intact; [1608:1638] whole, in chunk 0 -- the model saw this text intact

**Over-split** (6) — one true topic extracted as several separate predicted requirements:
- true `offer_content_minimum_elements` — "As a minimum, offers shall include— (1) The solicitation number; (2) The name, address, telephone number of the Offeror; (3) The Offeror’s Unique Entity Identifier (UEI) and, if applicable, Electronic Funds Transfer (EFT) indicator;" split into 3 predicted requirements:
  - predicted [6924090e] "The offer must include the solicitation number." — verdict: compliant
  - predicted [9256eb43] "As a minimum, offers shall include— ... The Offeror’s Unique Entity Identifier (UEI) and, if applicable, Electronic Funds Transfer (EFT) indicator" — verdict: compliant
  - predicted [f96b20ee] "The offer must include the name, address, and telephone number of the Offeror." — verdict: compliant
- true `security_sanctions_representations` — "(d) FASCSA Representation. By submission of this offer, the offeror represents that it has conducted a reasonable inquiry, and that the offeror does not propose to provide or use in response to this solicitation any covered article, or any products or services produced or provided by a source, if the covered article or the source is prohibited by an applicable FASCSA order in effect on the date the solicitation was issued, except as waived by the solicitation, or as disclosed in paragraph (g). ... (e) Sudan certification. By submission of its offer, the offeror certifies, after conducting a reasonable inquiry (that looks at any information in the offeror’s possession but does not need to include an internal or third-party audit), that the offeror does not conduct any restricted business operations in Sudan." split into 2 predicted requirements:
  - predicted [5671eb23] "the offeror represents that it has conducted a reasonable inquiry, and that the offeror does not propose to provide or use in response to this solicitation any covered article, or any products or services produced or provided by a source, if the covered article or the source is prohibited by an applicable FASCSA order in effect on the date the solicitation was issued, except as waived by the solicitation, or as disclosed in paragraph (g)." — not verifiable by text
  - predicted [7f5f200b] "the offeror certifies, after conducting a reasonable inquiry (that looks at any information in the offeror’s possession but does not need to include an internal or third-party audit), that the offeror does not conduct any restricted business operations in Sudan." — not verifiable by text
- true `submission_deadline` — "All questions regarding the solicitation must be submitted via email to James.horne@va.gov no later than 10:00 a.m. central time on 9/15/26. ... Quote Submission: All quotes must be submitted electronically, via email to James.horne@va.gov." split into 2 predicted requirements:
  - predicted [2f788c82] "All questions regarding the solicitation must be submitted via email to James.horne@va.gov no later than 10:00 a.m. central time on 9/15/26." — verdict: insufficient_information
  - predicted [e2a71fa0] "All quotes must be submitted electronically via email to James.horne@va.gov." — verdict: compliant
- true `two_part_proposal_format` — "The proposal shall be prepared in two (2) parts: 1) price response and 2) a non-price response. The pricing response shall consist of the signed Standard Form (SF) 1449 and completion of the price schedule(s). The non-price response shall address the non-price factors." split into 3 predicted requirements:
  - predicted [09e0c8cf] "The proposal shall be prepared in two parts: a price response and a non-price response." — verdict: compliant
  - predicted [1c596384] "The pricing response must include the signed Standard Form (SF) 1449, with blocks 17a, 17b, 30a, 30b, and 30c completed, and the completed price schedule(s). By signing the SF-1449, the Offeror agrees to the contract terms and conditions as written in the RFQ." — verdict: compliant
  - predicted [b2073d5e] "The non-price response shall address the non-price factors." — verdict: compliant
- true `prior_experience_documentation` — "Offeror shall provide at least five (5) years of prior experience as the Prime Contractor Waste Removal Services. ... i. Contract number ii. Estimated annual dollar value of contract iii. Description of services (including location) provided and the offeror’s level of responsibility and authority on the project. iv. Date of contract start and completion. v. Name, title, address, phone number, and email of customer contact." split into 6 predicted requirements:
  - predicted [86d3b008] "For each year of prior experience, provide the contract number." — verdict: non_compliant
  - predicted [bbe347e2] "Offeror shall provide at least five (5) years of prior experience as the Prime Contractor for Waste Removal Services." — verdict: non_compliant
  - predicted [d77f6563] "For each year of prior experience, provide the name, title, address, phone number, and email of the customer contact." — verdict: non_compliant
  - predicted [f6787a8f] "For each year of prior experience, provide a description of services (including location) and the offeror’s level of responsibility and authority on the project." — verdict: non_compliant
  - predicted [f709f267] "For each year of prior experience, provide the estimated annual dollar value of the contract." — verdict: non_compliant
  - predicted [fa826f83] "For each year of prior experience, provide the date of contract start and completion." — verdict: non_compliant
- true `contractor_certification_qualifications` — "A. Contractors shall be currently certified by either the InterNational Electrical Testing Association (NETA) as NETA Certified Technician or the National Institute for Certification in Engineering Technologies (NICET) and completed the Occupational Safety & Health Administration (OSHA) approved 10-hour construction safety training." split into 2 predicted requirements:
  - predicted [13c785ca] "Contractors shall be currently certified by either the InterNational Electrical Testing Association (NETA) as NETA Certified Technician or the National Institute for Certification in Engineering Technologies (NICET)" — not verifiable by text
  - predicted [69501b60] "ologies (NICET) and completed the Occupational Safety & Health Administration (OSHA) approved 10-hour construction safety training. B." — not verifiable by text, citation: fuzzy match — worth a second look

**Over-merge** (0) — one predicted requirement covering several distinct true topics:
- none

**Tangled** (1) — several true and several predicted requirements all overlapping at once:
- tangle of 2 true and 3 predicted requirements, all overlapping — needs manual untangling:
  - true `subcontractor_technical_experience_submission` — "Contractors shall provide evidence of subcontractors’ technical qualifications and experience needed to meet the technical performance requirements of this solicitation, if applicable. Offerors must submit no less than two (2) examples of their technical experience with contracts that involved technical requirements similar to the requirements of this solicitation."
  - true `technical_experience_examples_submission` — "Contractors shall provide evidence they have the technical qualifications and experience needed to meet the technical performance requirements of this solicitation. Offerors must submit no less than two (2) examples of their technical experience with contracts that involved technical requirements similar to the requirements of this solicitation."
  - predicted [10b0c38e] "Offerors must submit no less than two (2) examples of their technical experience with contracts that involved technical requirements similar to the requirements of this solicitation." — verdict: compliant
  - predicted [71010335] "Contractors shall provide evidence of subcontractors’ technical qualifications and experience needed to meet the technical performance requirements of this solicitation, if applicable." — verdict: compliant
  - predicted [a8faf11b] "Contractors shall provide evidence of their technical qualifications and experience required to meet the technical performance requirements of this solicitation." — verdict: compliant

## Requirement precision

**Citation-verified rate** (hallucination check): fraction of predicted requirements whose citation was actually located in tender.txt (exactly or via fuzzy match).
- rate: 100.0%
- unverified:
  - none

**Classification precision**: fraction of predicted requirements that matched a true requirement.
- rate: 57.1%
- unexplained (21) — the model recognized these as requirements, but they don't match any true requirement. "closest true topic" is a mechanical (no-LLM) embedding-similarity lookup against every true topic's description; "dedup visibility" checks whether dedup's own cosine pre-filter would have clustered this candidate with whatever predicted requirement DID match that topic -- i.e. whether the dedup LLM call ever had a chance to compare them:
  - predicted [6673e0a8] "Offerors shall not list any experience for any of their subcontractors it is considering using; only the offeror’s prior experience will be considered."
    - **similarity check:** closest true topic: `subcontractor_technical_experience_submission` (cosine=0.64); vs matched predicted [10b0c38e]: cosine=0.60 (< dedup threshold 0.7) -> dedup's cosine pre-filter would NOT have clustered these -- the dedup LLM call never saw them side by side
  - predicted [6aacb2ef] "For each submitted Technical Experience contract, provide a brief description of the scope of work, explaining how the contract involved work as a prime contractor under the assigned NAICS Code."
    - **similarity check:** closest true topic: `technical_experience_examples_submission` (cosine=0.64); vs matched predicted [a8faf11b]: cosine=0.61 (< dedup threshold 0.7) -> dedup's cosine pre-filter would NOT have clustered these -- the dedup LLM call never saw them side by side
  - predicted [731921c2] "For each submitted past performance contract, provide the name, current mailing address, phone number, and email address of at least one point-of-contact at the awarding organization."
    - **similarity check:** closest true topic: `past_performance_contracts_submission` (cosine=0.71); vs matched predicted [dfe4117b]: cosine=0.63 (< dedup threshold 0.7) -> dedup's cosine pre-filter would NOT have clustered these -- the dedup LLM call never saw them side by side
  - predicted [73f8fdff] "For each submitted Technical Experience contract, provide the name and location of the contract."
    - **similarity check:** closest true topic: `past_performance_contracts_submission` (cosine=0.66); vs matched predicted [dfe4117b]: cosine=0.61 (< dedup threshold 0.7) -> dedup's cosine pre-filter would NOT have clustered these -- the dedup LLM call never saw them side by side
  - predicted [7659eb30] "The offer must include information necessary to evaluate the factors contained in the provision at 52.212-2 or as described in the solicitation."
    - **similarity check:** closest true topic: `offer_content_minimum_elements` (cosine=0.69); vs matched predicted [6924090e]: cosine=0.71 (>= dedup threshold 0.7) -> would likely have been clustered together and compared by the dedup LLM call
  - predicted [803791d6] "Contractors shall have safety trainings – either on-the-job or class-room type – in electrical safety outlined in the OSHA Standard 29 Code of Federal Regulations (CFR) 1910 Subpart S – Electrical, and the NFPA 70E – Standard for Electrical Safety in the Workplace."
    - **similarity check:** closest true topic: `electrical_safety_training_certification_submission` (cosine=0.78); vs matched predicted [72b334ca]: cosine=0.55 (< dedup threshold 0.7) -> dedup's cosine pre-filter would NOT have clustered these -- the dedup LLM call never saw them side by side
  - predicted [88cc1f39] "The Offeror’s Price Quote must include a completed Price Schedule, with the Offeror providing their best pricing for each individual Contract Line Item listed in Section B for all specified pricing periods."
    - **similarity check:** closest true topic: `past_performance_contracts_submission` (cosine=0.60); vs matched predicted [dfe4117b]: cosine=0.54 (< dedup threshold 0.7) -> dedup's cosine pre-filter would NOT have clustered these -- the dedup LLM call never saw them side by side
  - predicted [8909a4d4] "For each submitted past performance contract, provide the date of the contract award and the contract award amount in dollars."
    - **similarity check:** closest true topic: `past_performance_contracts_submission` (cosine=0.63); vs matched predicted [dfe4117b]: cosine=0.56 (< dedup threshold 0.7) -> dedup's cosine pre-filter would NOT have clustered these -- the dedup LLM call never saw them side by side
  - predicted [933a637d] "The subject line of the email shall start with the RFQ reference number 36C25526Q0501."
    - **similarity check:** closest true topic: `submission_deadline` (cosine=0.57); vs matched predicted [2f788c82]: cosine=0.57 (< dedup threshold 0.7) -> dedup's cosine pre-filter would NOT have clustered these -- the dedup LLM call never saw them side by side
  - predicted [a2fa4320] "For each submitted past performance contract, provide a brief description of the contract scope of work."
    - **similarity check:** closest true topic: `past_performance_contracts_submission` (cosine=0.64); vs matched predicted [dfe4117b]: cosine=0.64 (< dedup threshold 0.7) -> dedup's cosine pre-filter would NOT have clustered these -- the dedup LLM call never saw them side by side
  - predicted [b1e17083] "Invoices shall be submitted in arrears: a. Quarterly [] b. Semi-Annually [] c. Other [X] Monthly, in arrears"
    - **similarity check:** closest true topic: `amendment_acknowledgment` (cosine=0.56); vs matched predicted [bd22036a]: cosine=0.61 (< dedup threshold 0.7) -> dedup's cosine pre-filter would NOT have clustered these -- the dedup LLM call never saw them side by side
  - predicted [c2f7556d] "For each submitted Technical Experience contract, provide the performance period, including the starting and completion dates."
    - **similarity check:** closest true topic: `past_performance_contracts_submission` (cosine=0.54); vs matched predicted [dfe4117b]: cosine=0.53 (< dedup threshold 0.7) -> dedup's cosine pre-filter would NOT have clustered these -- the dedup LLM call never saw them side by side
  - predicted [cebfe7e5] "be listed as an SDVOSB participant in the SBA certification database as set forth in 13 CFR"
    - **similarity check:** closest true topic: `sdvosb_setaside_eligibility` (cosine=0.77); vs matched predicted [dec100b3]: cosine=0.68 (< dedup threshold 0.7) -> dedup's cosine pre-filter would NOT have clustered these -- the dedup LLM call never saw them side by side
  - predicted [d249e03c] "As a minimum, offers shall include— ... Responses to provisions that require Offeror completion of information, representations, and certifications (other than those collected via the System for Award Management (SAM))"
    - **similarity check:** closest true topic: `past_performance_contracts_submission` (cosine=0.70); vs matched predicted [dfe4117b]: cosine=0.63 (< dedup threshold 0.7) -> dedup's cosine pre-filter would NOT have clustered these -- the dedup LLM call never saw them side by side
  - predicted [e7939d10] "For each submitted Technical Experience contract, the offeror must provide the percentage of total labor self-performed by the offeror’s employees."
    - **similarity check:** closest true topic: `technical_experience_examples_submission` (cosine=0.52); vs matched predicted [a8faf11b]: cosine=0.54 (< dedup threshold 0.7) -> dedup's cosine pre-filter would NOT have clustered these -- the dedup LLM call never saw them side by side
  - predicted [eb389c31] "For each submitted past performance contract, provide the name of the contracting agency or organization that awarded the contract."
    - **similarity check:** closest true topic: `past_performance_contracts_submission` (cosine=0.69); vs matched predicted [dfe4117b]: cosine=0.69 (< dedup threshold 0.7) -> dedup's cosine pre-filter would NOT have clustered these -- the dedup LLM call never saw them side by side
  - predicted [ecb78e1e] "Offers received from entities that are not certified SDVOSBs and listed in the SBA certification database at the time of offer shall not be considered."
    - **similarity check:** closest true topic: `sdvosb_setaside_eligibility` (cosine=0.71); vs matched predicted [dec100b3]: cosine=0.56 (< dedup threshold 0.7) -> dedup's cosine pre-filter would NOT have clustered these -- the dedup LLM call never saw them side by side
  - predicted [ee676aa0] "For each submitted past performance contract, provide the contract name and contract ID number."
    - **similarity check:** closest true topic: `past_performance_contracts_submission` (cosine=0.66); vs matched predicted [dfe4117b]: cosine=0.61 (< dedup threshold 0.7) -> dedup's cosine pre-filter would NOT have clustered these -- the dedup LLM call never saw them side by side
  - predicted [f1c7d8aa] "The offeror must qualify as a small business concern under the size standard corresponding to the NAICS code assigned to the contract."
    - **similarity check:** closest true topic: `sdvosb_setaside_eligibility` (cosine=0.72); vs matched predicted [dec100b3]: cosine=0.61 (< dedup threshold 0.7) -> dedup's cosine pre-filter would NOT have clustered these -- the dedup LLM call never saw them side by side
  - predicted [f59aa232] "The Offeror’s Price Quote shall contain the following items: ... Completed Acknowledgement of Amendments if issued. Ensure amendments are signed by the same official that has been authorized to sign the SF 1449."
    - **similarity check:** closest true topic: `amendment_acknowledgment` (cosine=0.69); vs matched predicted [bd22036a]: cosine=0.68 (< dedup threshold 0.7) -> dedup's cosine pre-filter would NOT have clustered these -- the dedup LLM call never saw them side by side
  - predicted [f9323528] "All Invoices from the contractor shall be submitted electronically in accordance with VAAR Clause 852.232-72 Electronic Submission of Payment Requests."
    - **similarity check:** closest true topic: `submission_deadline` (cosine=0.58); vs matched predicted [e2a71fa0]: cosine=0.66 (< dedup threshold 0.7) -> dedup's cosine pre-filter would NOT have clustered these -- the dedup LLM call never saw them side by side

## Coverage flags

Clean 1:1 matches (recall counted them as found) whose citations don't fully overlap in length, split by which side is off. Over-split/over-merge/tangled matches are excluded here -- their predicted fragments are inherently partial by construction, already shown in the recall breakdown above.

**Requirements captured with extra text** (0) — the predicted citation is padded beyond the true one:
- none

**Requirements captured incompletely** (2) — the predicted citation misses part of the true one:
- predicted [bd22036a] is contained in true `amendment_acknowledgment` — 78.9%:
    predicted: "The offeror must acknowledge receipt of all solicitation amendments, including the amendment number and date."
    true: "ACKNOWLEDGMENT OF AMENDMENTS: The offeror acknowledges receipt of amendments to the Solicitation numbered and dated as follows: AMENDMENT NO DATE"

- predicted [dec100b3] is contained in true `sdvosb_setaside_eligibility` — 50.4%:
    predicted: "By submitting an offer, the prospective contractor represents that it is an eligible and certified SDVOSB as defined in this clause, 13 CFR 121, 125, and 128, and VAAR subpart 819.70."
    true: "(c) Representation. Pursuant to 38 U.S.C. 8127(e), only certified SDVOSBs listed in the SBA certification database are considered eligible to receive award of a resulting contract. By submitting an offer, the prospective contractor represents that it is an eligible and certified SDVOSB as defined in this clause, 13 CFR 121, 125, and 128, and VAAR subpart 819.70."

## is_mandatory accuracy

For each clean or one-to-many match (tangled groups excluded — there's no single "one" to compare against), does `is_mandatory` agree with the true value? A one-to-many group counts as correct only if every member on the "many" side agrees with the "one".

**Accuracy: 92.3% (13 groups)**

Mismatched:
- true: `amendment_acknowledgment`=False; predicted: `bd22036a`=True — "ACKNOWLEDGMENT OF AMENDMENTS: The offeror acknowledges receipt of amendments to the Solicitation numbered and dated as follows: AMENDMENT NO DATE"

## is_text_verifiable accuracy

For each clean or one-to-many match (tangled groups excluded), does `is_text_verifiable` agree with the true value (all-or-nothing on the "many" side, same rule as is_mandatory above)? A wrong `false` here means the pipeline skips verdict generation for a requirement that should get one.

**Accuracy: 84.6% (13 groups)**

Mismatched:
- true: `submission_deadline`=False; predicted: `2f788c82`=True, `e2a71fa0`=True — "All questions regarding the solicitation must be submitted via email to James.horne@va.gov no later than 10:00 a.m. central time on 9/15/26. ... Quote Submission: All quotes must be submitted electronically, via email to James.horne@va.gov."
- true: `contractor_experience_tenure`=False; predicted: `e7146dfa`=True — "B. Contractors shall have technical training and a history of work experience in maintenance, inspection, and testing of the low and medium voltage Electrical Power Distribution Systems and its components in healthcare, industrial, educational, and commercial facilities for a minimum of five (5) continuous years from the date of this solicitation."

## Verdict accuracy

The confusion matrix covers only clean 1:1 matches — split/merge groups have no single pair to plot, but still count in the two rates below.

Clean matches scored: 5

| true \ pipeline said | `compliant` | `non_compliant` | `contradictory` | `insufficient_information` |
|---|---|---|---|---|
| `compliant` | 2 | 1 | 0 | 0 |
| `non_compliant` | 0 | 1 | 0 | 0 |
| `contradictory` | 0 | 0 | 1 | 0 |
| `insufficient_information` | 0 | 0 | 0 | 0 |

Why some rows are empty:
- `insufficient_information` row is empty: true `prior_experience_documentation` — over_split match — no single pair to plot
- `insufficient_information` row is empty: true `subcontractor_technical_experience_submission` — tangled match — no single pair to plot

**Mismatched clean matches** — every off-diagonal cell above, in full: the full context retrieved and shown to the model, what it chose to cite from that context, and its reasoning ("model's ..."), next to what `true_verdicts.json` expects ("expected ...").

- `technical_capabilities_letter` — acceptable: ['compliant'], predicted: non_compliant
  - **requirement:** "Offer shall provide a letter fully describing their capabilities, not exceeding five pages, that includes a description of their technical approach, methodology, and technique used to carry out the Performance Work Statement."
  - **retrieved context (shown to the model):** "Technical Experience Examples: 1. Sedgwick County Adult Detention Facility, Wichita, KS. Performance period: 01/2021-03/2021. 100% of labor self-performed by Heartland employees. Scope: NETA-standard testing of switchgear, transformers, and circuit breakers as prime contractor un [...truncated]"
  - **retrieved context (shown to the model):** "From: bids@heartlandelectricaltesting.com To: James.horne@va.gov Subject: 36C25526Q0501 - Quote for Electrical Power Distribution Testing Solicitation Number: 36C25526Q0501 Heartland Electrical Testing Services, LLC 4820 Industrial Parkway Kansas City, MO 64120 (816) 555-2290 Uni [...truncated]"
  - **retrieved context (shown to the model):** "Prior Experience: Heartland Electrical Testing Services has performed electrical power distribution testing and maintenance services for healthcare and industrial clients for the past six years. Representative engagements include hospital electrical infrastructure testing contrac [...truncated]"
  - **model's evidence (what it chose to cite):** "Technical Capabilities: Heartland Electrical Testing Services has over a decade of experience performing NETA-standard electrical testing and maintenance for hospital and industrial clients. Our technical approach follows NETA Maintenance Testing Specifications for infrared scanning, breaker trip testing, ground fault protection testing, and transformer oil sampling, using calibrated diagnostic equipment and a documented verification checklist at each stage of the process."
  - **model's reasoning:** The requirement mandates a letter fully describing the bidder's capabilities, including a description of their technical approach, methodology, and technique used to carry out the Performance Work Statement. While the bidder provides a brief paragraph under 'Technical Capabilities', it does not constitute a comprehensive letter describing their capabilities and methodology in the context of the specific Performance Work Statement for this solicitation. The provided text is insufficient to meet the requirement of a full description of the approach and methodology for the specific work requested.
  - **expected evidence (true_verdicts.json):** "Heartland Electrical Testing Services has over a decade of experience performing NETA-standard electrical testing and maintenance for hospital and industrial clients. Our technical approach follows NETA Maintenance Testing Specifications for infrared scanning, breaker trip testing, ground fault protection testing, and transformer oil sampling, using calibrated diagnostic equipment and a documented verification checklist at each stage of the process."
  - **expected reasoning:** Application describes a specific technical approach, methodology, and technique (NETA-standard testing procedures, diagnostic equipment, verification checklist) rather than merely reciting the Performance Work Statement.

**False-compliant rate** — dangerous direction: the true verdict requires an issue (anything but `compliant`), but every predicted verdict in the group is `compliant`.
- rate: 11.1%

- group of 2 true topic(s) and 3 predicted requirement(s) (not a 1:1 match, so there is no single correct pairing between them):
  - true `subcontractor_technical_experience_submission` — "Contractors shall provide evidence of subcontractors’ technical qualifications and experience needed to meet the technical performance requirements of this solicitation, if applicable. Offerors must submit no less than two (2) examples of their technical experience with contracts that involved technical requirements similar to the requirements of this solicitation." (acceptable: ['insufficient_information'])
      - **expected evidence (true_verdicts.json):** "remainder by a licensed subcontractor."
      - **expected reasoning:** Application mentions a subcontractor performed part of the work in one technical experience example, suggesting the conditional requirement may be triggered, but never provides the subcontractor's own technical experience examples in the required format.
  - true `technical_experience_examples_submission` — "Contractors shall provide evidence they have the technical qualifications and experience needed to meet the technical performance requirements of this solicitation. Offerors must submit no less than two (2) examples of their technical experience with contracts that involved technical requirements similar to the requirements of this solicitation." (acceptable: ['compliant'])
      - **expected evidence (true_verdicts.json):** "1. Sedgwick County Adult Detention Facility, Wichita, KS. Performance period: 01/2021-03/2021. 100% of labor self-performed by Heartland employees. Scope: NETA-standard testing of switchgear, transformers, and circuit breakers as prime contractor under NAICS 221122, technically similar to the work under this solicitation. 2. Olathe Medical Center, Olathe, KS. Performance period: 09/2020-11/2020. 90% of labor self-performed by Heartland employees, remainder by a licensed subcontractor. Scope: NETA-standard testing of the emergency power distribution system as prime contractor under NAICS 221122, technically similar to the work under this solicitation."
      - **expected reasoning:** Application provides two technical experience examples as prime contractor under NAICS 221122, each with location, performance period, percentage self-performed, and a scope description technically similar to this solicitation.
  - **retrieved context (shown to the model):** "Technical Experience Examples: 1. Sedgwick County Adult Detention Facility, Wichita, KS. Performance period: 01/2021-03/2021. 100% of labor self-performed by Heartland employees. Scope: NETA-standard testing of switchgear, transformers, and circuit breakers as prime contractor un [...truncated]"
  - **retrieved context (shown to the model):** "From: bids@heartlandelectricaltesting.com To: James.horne@va.gov Subject: 36C25526Q0501 - Quote for Electrical Power Distribution Testing Solicitation Number: 36C25526Q0501 Heartland Electrical Testing Services, LLC 4820 Industrial Parkway Kansas City, MO 64120 (816) 555-2290 Uni [...truncated]"
  - **retrieved context (shown to the model):** "Prior Experience: Heartland Electrical Testing Services has performed electrical power distribution testing and maintenance services for healthcare and industrial clients for the past six years. Representative engagements include hospital electrical infrastructure testing contrac [...truncated]"
  - predicted verdicts in this group:
    - predicted [10b0c38e] "Offerors must submit no less than two (2) examples of their technical experience with contracts that involved technical requirements similar to the requirements of this solicitation." — verdict: compliant
      - **model's evidence (what it chose to cite):** "1. Sedgwick County Adult Detention Facility, Wichita, KS. Performance period: 01/2021-03/2021. 100% of labor self-performed by Heartland employees. Scope: NETA-standard testing of switchgear, transformers, and circuit breakers as prime contractor under NAICS 221122, technically similar to the work under this solicitation."
      - **model's evidence (what it chose to cite):** "2. Olathe Medical Center, Olathe, KS. Performance period: 09/2020-11/2020. 90% of labor self-performed by Heartland employees, remainder by a licensed subcontractor. Scope: NETA-standard testing of the emergency power distribution system as prime contractor under NAICS 221122, technically similar to the work under this solicitation."
      - **model's reasoning:** The requirement asks for no less than two examples of technical experience with contracts involving similar requirements. The bidder provided two specific examples of NETA-standard testing contracts that they explicitly state are technically similar to the solicitation requirements.
    - predicted [71010335] "Contractors shall provide evidence of subcontractors’ technical qualifications and experience needed to meet the technical performance requirements of this solicitation, if applicable." — verdict: compliant
      - **model's evidence (what it chose to cite):** "90% of labor self-performed by Heartland employees, remainder by a licensed subcontractor."
      - **model's reasoning:** The requirement asks for evidence of subcontractors' qualifications 'if applicable'. The bidder's application indicates that they do utilize a subcontractor for a portion of their work (10% in the Olathe Medical Center example). While the bidder mentions the subcontractor is 'licensed', they do not provide specific technical qualifications or experience for that subcontractor. However, since the requirement is conditional ('if applicable') and the bidder self-performs the vast majority of their work (90-100%), the provided information is sufficient to demonstrate their approach to subcontracting, and the lack of detailed subcontractor resumes does not constitute a failure to meet the requirement given the minimal reliance on subcontractors.
    - predicted [a8faf11b] "Contractors shall provide evidence of their technical qualifications and experience required to meet the technical performance requirements of this solicitation." — verdict: compliant
      - **model's evidence (what it chose to cite):** "Technical Experience Examples: 1. Sedgwick County Adult Detention Facility, Wichita, KS... Scope: NETA-standard testing of switchgear, transformers, and circuit breakers... 2. Olathe Medical Center, Olathe, KS... Scope: NETA-standard testing of the emergency power distribution system"
      - **model's evidence (what it chose to cite):** "Past Performance Contracts: 1. Contract: St. Luke's Hospital Electrical System Testing... 2. Contract: Fort Leavenworth Commissary Electrical Testing... Scope: triennial switchgear and transformer testing."
      - **model's reasoning:** The bidder provided multiple specific examples of past contracts and technical experience that demonstrate their capability to perform NETA-standard electrical testing, which aligns with the technical performance requirements of the solicitation.

**False-issue rate** — mirror direction: the true verdict is `compliant` only, but the pipeline raised an issue anyway.
- rate: 11.1%

- `technical_capabilities_letter` — acceptable: ['compliant'], predicted: non_compliant
  - **requirement:** "Offer shall provide a letter fully describing their capabilities, not exceeding five pages, that includes a description of their technical approach, methodology, and technique used to carry out the Performance Work Statement."
  - **retrieved context (shown to the model):** "Technical Experience Examples: 1. Sedgwick County Adult Detention Facility, Wichita, KS. Performance period: 01/2021-03/2021. 100% of labor self-performed by Heartland employees. Scope: NETA-standard testing of switchgear, transformers, and circuit breakers as prime contractor un [...truncated]"
  - **retrieved context (shown to the model):** "From: bids@heartlandelectricaltesting.com To: James.horne@va.gov Subject: 36C25526Q0501 - Quote for Electrical Power Distribution Testing Solicitation Number: 36C25526Q0501 Heartland Electrical Testing Services, LLC 4820 Industrial Parkway Kansas City, MO 64120 (816) 555-2290 Uni [...truncated]"
  - **retrieved context (shown to the model):** "Prior Experience: Heartland Electrical Testing Services has performed electrical power distribution testing and maintenance services for healthcare and industrial clients for the past six years. Representative engagements include hospital electrical infrastructure testing contrac [...truncated]"
  - **model's evidence (what it chose to cite):** "Technical Capabilities: Heartland Electrical Testing Services has over a decade of experience performing NETA-standard electrical testing and maintenance for hospital and industrial clients. Our technical approach follows NETA Maintenance Testing Specifications for infrared scanning, breaker trip testing, ground fault protection testing, and transformer oil sampling, using calibrated diagnostic equipment and a documented verification checklist at each stage of the process."
  - **model's reasoning:** The requirement mandates a letter fully describing the bidder's capabilities, including a description of their technical approach, methodology, and technique used to carry out the Performance Work Statement. While the bidder provides a brief paragraph under 'Technical Capabilities', it does not constitute a comprehensive letter describing their capabilities and methodology in the context of the specific Performance Work Statement for this solicitation. The provided text is insufficient to meet the requirement of a full description of the approach and methodology for the specific work requested.
  - **expected evidence (true_verdicts.json):** "Heartland Electrical Testing Services has over a decade of experience performing NETA-standard electrical testing and maintenance for hospital and industrial clients. Our technical approach follows NETA Maintenance Testing Specifications for infrared scanning, breaker trip testing, ground fault protection testing, and transformer oil sampling, using calibrated diagnostic equipment and a documented verification checklist at each stage of the process."
  - **expected reasoning:** Application describes a specific technical approach, methodology, and technique (NETA-standard testing procedures, diagnostic equipment, verification checklist) rather than merely reciting the Performance Work Statement.

**Unscored** — split/merge groups excluded from the matrix above (still counted in the two rates above):
- group 1:
  - true `offer_content_minimum_elements` — "As a minimum, offers shall include— (1) The solicitation number; (2) The name, address, telephone number of the Offeror; (3) The Offeror’s Unique Entity Identifier (UEI) and, if applicable, Electronic Funds Transfer (EFT) indicator;" (acceptable: ['compliant'])
  - predicted [6924090e] "The offer must include the solicitation number." — verdict: compliant
  - predicted [9256eb43] "As a minimum, offers shall include— ... The Offeror’s Unique Entity Identifier (UEI) and, if applicable, Electronic Funds Transfer (EFT) indicator" — verdict: compliant
  - predicted [f96b20ee] "The offer must include the name, address, and telephone number of the Offeror." — verdict: compliant
- group 2:
  - true `two_part_proposal_format` — "The proposal shall be prepared in two (2) parts: 1) price response and 2) a non-price response. The pricing response shall consist of the signed Standard Form (SF) 1449 and completion of the price schedule(s). The non-price response shall address the non-price factors." (acceptable: ['compliant'])
  - predicted [09e0c8cf] "The proposal shall be prepared in two parts: a price response and a non-price response." — verdict: compliant
  - predicted [1c596384] "The pricing response must include the signed Standard Form (SF) 1449, with blocks 17a, 17b, 30a, 30b, and 30c completed, and the completed price schedule(s). By signing the SF-1449, the Offeror agrees to the contract terms and conditions as written in the RFQ." — verdict: compliant
  - predicted [b2073d5e] "The non-price response shall address the non-price factors." — verdict: compliant
- group 3:
  - true `prior_experience_documentation` — "Offeror shall provide at least five (5) years of prior experience as the Prime Contractor Waste Removal Services. ... i. Contract number ii. Estimated annual dollar value of contract iii. Description of services (including location) provided and the offeror’s level of responsibility and authority on the project. iv. Date of contract start and completion. v. Name, title, address, phone number, and email of customer contact." (acceptable: ['insufficient_information'])
  - predicted [86d3b008] "For each year of prior experience, provide the contract number." — verdict: non_compliant
  - predicted [bbe347e2] "Offeror shall provide at least five (5) years of prior experience as the Prime Contractor for Waste Removal Services." — verdict: non_compliant
  - predicted [d77f6563] "For each year of prior experience, provide the name, title, address, phone number, and email of the customer contact." — verdict: non_compliant
  - predicted [f6787a8f] "For each year of prior experience, provide a description of services (including location) and the offeror’s level of responsibility and authority on the project." — verdict: non_compliant
  - predicted [f709f267] "For each year of prior experience, provide the estimated annual dollar value of the contract." — verdict: non_compliant
  - predicted [fa826f83] "For each year of prior experience, provide the date of contract start and completion." — verdict: non_compliant
- group 4:
  - true `subcontractor_technical_experience_submission` — "Contractors shall provide evidence of subcontractors’ technical qualifications and experience needed to meet the technical performance requirements of this solicitation, if applicable. Offerors must submit no less than two (2) examples of their technical experience with contracts that involved technical requirements similar to the requirements of this solicitation." (acceptable: ['insufficient_information'])
  - true `technical_experience_examples_submission` — "Contractors shall provide evidence they have the technical qualifications and experience needed to meet the technical performance requirements of this solicitation. Offerors must submit no less than two (2) examples of their technical experience with contracts that involved technical requirements similar to the requirements of this solicitation." (acceptable: ['compliant'])
  - predicted [10b0c38e] "Offerors must submit no less than two (2) examples of their technical experience with contracts that involved technical requirements similar to the requirements of this solicitation." — verdict: compliant
  - predicted [71010335] "Contractors shall provide evidence of subcontractors’ technical qualifications and experience needed to meet the technical performance requirements of this solicitation, if applicable." — verdict: compliant
  - predicted [a8faf11b] "Contractors shall provide evidence of their technical qualifications and experience required to meet the technical performance requirements of this solicitation." — verdict: compliant

## Evidence

**Citation-verified rate** (evidence-level): fraction of evidence quotes actually located in application.txt.
- rate: 85.5% (9 unverified of 62)

**Evidence recall**: does the expected evidence span (from `true_verdicts.json`) show up somewhere in the requirement's retrieved chunks, before the verdict step chose what to cite? Topics never extracted as a requirement are excluded — that failure is already counted by requirement recall above.
- recall: 100.0% (10/10)
- missed:
  - none
