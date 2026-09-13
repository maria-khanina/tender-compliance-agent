# Evaluation report

## Summary metrics

Machine-readable numbers for averaging across tenders -- every value here is explained in the sections below. `null` means the metric doesn't apply to this run (e.g. no verdict-only artifact present).

```json
{
  "requirement_recall": 0.875,
  "requirement_recall_matched": 14,
  "requirement_recall_total": 16,
  "requirement_precision": 0.4231,
  "citation_verified_rate": 0.9038,
  "is_mandatory_accuracy": 1.0,
  "is_mandatory_scored": 12,
  "is_text_verifiable_accuracy": 0.5833,
  "is_text_verifiable_scored": 12,
  "verdict_clean_match_count": 4,
  "verdict_accuracy": 0.75,
  "false_compliant_rate": 0.125,
  "false_issue_rate": 0.125,
  "evidence_citation_verified_rate": 0.8846,
  "evidence_recall": 1.0,
  "verdict_only_accuracy": null,
  "verdict_only_scored": null
}
```

## Requirement recall

For each `true_requirements.json` topic, did the pipeline extract something whose tender.txt citation overlaps the true one? A pure text-offset check, not a judgment of meaning — see coverage flags below for extractions that are technically "found" but sloppy.

**Recall: 87.5% (14/16)**

**Missed** (2) — no overlapping predicted requirement at all. "chunk check" is a mechanical (no-LLM) re-chunking of the source document: whether this topic's matching text ever appeared whole in one chunk handed to the extraction model, or was split across chunks.
- true `amendment_acknowledgment` — "ACKNOWLEDGMENT OF AMENDMENTS: The offeror acknowledges receipt of amendments to the Solicitation numbered and dated as follows: AMENDMENT NO DATE"
    - **chunk check:** [995:1142] whole, in chunk 0 -- the model saw this text intact
- true `price_schedule_completion` — "0001 | NEW ACQUISITION FOR TRIENNIAL ELECTRICAL TESTING MAINTENANCE, TESTING, INSPECTION, AND/OR CALIBRATION OF THE ELECTRICAL POWER DISTRIBUTION SYSTEM LOCATED AT TRUMAN VA, COLUMBIA, MO ONE-YEAR, STANDALONE CONTRACT | 1.00 | JB | __________________ | __________________ ... GRAND TOTAL __________________"
    - **chunk check:** [1272:1543] whole, in chunk 0 -- the model saw this text intact; [1608:1638] whole, in chunk 0 -- the model saw this text intact

**Over-split** (5) — one true topic extracted as several separate predicted requirements:
- true `offer_content_minimum_elements` — "As a minimum, offers shall include— (1) The solicitation number; (2) The name, address, telephone number of the Offeror; (3) The Offeror’s Unique Entity Identifier (UEI) and, if applicable, Electronic Funds Transfer (EFT) indicator;" split into 3 predicted requirements:
  - predicted [21db188f] "Offers shall include the solicitation number." — verdict: compliant
  - predicted [7d97d851] "Offers shall include the offeror's Unique Entity Identifier (UEI) and EFT indicator if applicable." — verdict: compliant
  - predicted [9467cb78] "Offers shall include the name, address, and telephone number of the offeror." — verdict: compliant
- true `security_sanctions_representations` — "(d) FASCSA Representation. By submission of this offer, the offeror represents that it has conducted a reasonable inquiry, and that the offeror does not propose to provide or use in response to this solicitation any covered article, or any products or services produced or provided by a source, if the covered article or the source is prohibited by an applicable FASCSA order in effect on the date the solicitation was issued, except as waived by the solicitation, or as disclosed in paragraph (g). ... (e) Sudan certification. By submission of its offer, the offeror certifies, after conducting a reasonable inquiry (that looks at any information in the offeror’s possession but does not need to include an internal or third-party audit), that the offeror does not conduct any restricted business operations in Sudan." split into 2 predicted requirements:
  - predicted [577463b9] "Offeror represents that it has conducted a reasonable inquiry and does not propose to provide prohibited covered articles or sources per FASCSA orders." — verdict: insufficient_information
  - predicted [fc93c98a] "Offeror certifies that it does not conduct any restricted business operations in Sudan." — verdict: insufficient_information
- true `submission_deadline` — "All questions regarding the solicitation must be submitted via email to James.horne@va.gov no later than 10:00 a.m. central time on 9/15/26. ... Quote Submission: All quotes must be submitted electronically, via email to James.horne@va.gov." split into 2 predicted requirements:
  - predicted [0a7a8ec5] "All quotes must be submitted electronically via email to the designated address." — verdict: compliant
  - predicted [62d52ab9] "All questions regarding the solicitation must be submitted via email by the specified deadline." — verdict: insufficient_information
- true `two_part_proposal_format` — "The proposal shall be prepared in two (2) parts: 1) price response and 2) a non-price response. The pricing response shall consist of the signed Standard Form (SF) 1449 and completion of the price schedule(s). The non-price response shall address the non-price factors." split into 3 predicted requirements:
  - predicted [51a7a942] "The proposal shall be prepared in two parts: price response and non-price response." — verdict: compliant
  - predicted [5ddad1d9] "The non-price response shall address the non-price factors." — verdict: compliant
  - predicted [96f123ea] "The pricing response shall consist of the signed Standard Form 1449 and completion of the price schedule." — verdict: compliant
- true `electrical_safety_training_certification_submission` — "Training certifications shall be submitted to the VA Contracting Officer with the proposal for this solicitation. If no training certifications are available, the contractor’s employer shall certify that he/she has met this requirement in writing and submit it to the VA Contracting Officer with the proposal for this solicitation." split into 2 predicted requirements:
  - predicted [827a40fd] "If no training certifications are available, the contractor's employer shall certify in writing that the requirement has been met and submit it with the proposal." — verdict: contradictory
  - predicted [a88a6ec2] "Training certifications shall be submitted to the VA Contracting Officer with the proposal." — verdict: contradictory

**Over-merge** (0) — one predicted requirement covering several distinct true topics:
- none

**Tangled** (1) — several true and several predicted requirements all overlapping at once:
- tangle of 2 true and 3 predicted requirements, all overlapping — needs manual untangling:
  - true `subcontractor_technical_experience_submission` — "Contractors shall provide evidence of subcontractors’ technical qualifications and experience needed to meet the technical performance requirements of this solicitation, if applicable. Offerors must submit no less than two (2) examples of their technical experience with contracts that involved technical requirements similar to the requirements of this solicitation."
  - true `technical_experience_examples_submission` — "Contractors shall provide evidence they have the technical qualifications and experience needed to meet the technical performance requirements of this solicitation. Offerors must submit no less than two (2) examples of their technical experience with contracts that involved technical requirements similar to the requirements of this solicitation."
  - predicted [6c880dce] "Contractors shall provide evidence they have the technical qualifications and experience needed to meet the technical performance requirements." — verdict: compliant
  - predicted [db32b26f] "Contractors shall provide evidence of subcontractors' technical qualifications and experience if applicable." — verdict: compliant
  - predicted [e0b4adcc] "Offerors must submit no less than two examples of their technical experience with contracts involving similar technical requirements." — verdict: compliant

## Requirement precision

**Citation-verified rate** (hallucination check): fraction of predicted requirements whose citation was actually located in tender.txt (exactly or via fuzzy match).
- rate: 90.4%
- unverified:
  - predicted [851ad3d3] "To demonstrate prior experience, submit a description of services provided including location and offeror's level of responsibility and authority." — verdict: compliant, citation: UNVERIFIED — not located in tender.txt
  - predicted [8856d758] "Provide a brief description of the scope of work explaining how the contract involved work as a prime contractor under the specified NAICS code." — verdict: compliant, citation: UNVERIFIED — not located in tender.txt
  - predicted [e9fddfa1] "To demonstrate prior experience, submit the name, title, address, phone number, and email of the customer contact." — verdict: compliant, citation: UNVERIFIED — not located in tender.txt
  - predicted [eaa61eac] "Provide the percentage of total labor self-performed by the offeror's employees for each submitted technical experience contract." — verdict: non_compliant, citation: UNVERIFIED — not located in tender.txt
  - predicted [edc75454] "Provide the performance period, including starting and completion dates, for each submitted technical experience contract." — verdict: compliant, citation: UNVERIFIED — not located in tender.txt

**Classification precision**: fraction of predicted requirements that matched a true requirement.
- rate: 42.3%
- unexplained (30) — the model recognized these as requirements, but they don't match any true requirement. "closest true topic" is a mechanical (no-LLM) embedding-similarity lookup against every true topic's description; "dedup visibility" checks whether dedup's own cosine pre-filter would have clustered this candidate with whatever predicted requirement DID match that topic -- i.e. whether the dedup LLM call ever had a chance to compare them:
  - predicted [12a7e245] "Provide completed acknowledgement of amendments if issued."
    - **similarity check:** closest true topic: `amendment_acknowledgment` (cosine=0.77); that true topic has no matched predicted requirement in this run, so there was nothing for dedup to compare it against
  - predicted [19dabbaa] "Submit signed and dated offers to the specified office at or before the exact time specified."
    - **similarity check:** closest true topic: `amendment_acknowledgment` (cosine=0.64); that true topic has no matched predicted requirement in this run, so there was nothing for dedup to compare it against
  - predicted [1b9d9ae0] "Provide the name of the contract and contract ID number."
    - **similarity check:** closest true topic: `past_performance_contracts_submission` (cosine=0.66); vs matched predicted [f3d1aa39]: cosine=0.61 (>= dedup threshold 0.6) -> would likely have been clustered together and compared by the dedup LLM call
  - predicted [1c0f8a74] "Provide identification of at least one point-of-contact at the organization that awarded the contract, including name, mailing address, phone number, and email address."
    - **similarity check:** closest true topic: `past_performance_contracts_submission` (cosine=0.71); vs matched predicted [f3d1aa39]: cosine=0.63 (>= dedup threshold 0.6) -> would likely have been clustered together and compared by the dedup LLM call
  - predicted [25d8e03b] "Be listed as an SDVOSB participant in the SBA certification database."
    - **similarity check:** closest true topic: `sdvosb_setaside_eligibility` (cosine=0.77); vs matched predicted [052be2c9]: cosine=0.68 (>= dedup threshold 0.6) -> would likely have been clustered together and compared by the dedup LLM call
  - predicted [2e757dee] "Offers received from entities not certified as SDVOSBs and listed in the SBA database at the time of offer shall not be considered."
    - **similarity check:** closest true topic: `sdvosb_setaside_eligibility` (cosine=0.71); vs matched predicted [052be2c9]: cosine=0.56 (< dedup threshold 0.6) -> dedup's cosine pre-filter would NOT have clustered these -- the dedup LLM call never saw them side by side
  - predicted [376fc247] "The concern must qualify as a small business under the size standard corresponding to the assigned NAICS code."
    - **similarity check:** closest true topic: `sdvosb_setaside_eligibility` (cosine=0.72); vs matched predicted [052be2c9]: cosine=0.61 (>= dedup threshold 0.6) -> would likely have been clustered together and compared by the dedup LLM call
  - predicted [4341ac83] "Offers shall include information necessary to evaluate the factors contained in the solicitation provisions."
    - **similarity check:** closest true topic: `offer_content_minimum_elements` (cosine=0.66); vs matched predicted [21db188f]: cosine=0.69 (>= dedup threshold 0.6) -> would likely have been clustered together and compared by the dedup LLM call
  - predicted [45568428] "Ensure amendments are signed by the official authorized to sign the SF 1449."
    - **similarity check:** closest true topic: `amendment_acknowledgment` (cosine=0.63); that true topic has no matched predicted requirement in this run, so there was nothing for dedup to compare it against
  - predicted [5016d9c5] "Offerors shall not list subcontractor experience; only the offeror's prior experience will be considered."
    - **similarity check:** closest true topic: `subcontractor_technical_experience_submission` (cosine=0.64); vs matched predicted [e0b4adcc]: cosine=0.60 (< dedup threshold 0.6) -> dedup's cosine pre-filter would NOT have clustered these -- the dedup LLM call never saw them side by side
  - predicted [53cacccd] "The offeror shall price each line item within the pricing periods."
    - **similarity check:** closest true topic: `statement_of_agreement_with_terms` (cosine=0.68); vs matched predicted [af210e26]: cosine=0.63 (>= dedup threshold 0.6) -> would likely have been clustered together and compared by the dedup LLM call
  - predicted [5ddb35cd] "Provide the name of the contracting agency or organization that awarded the contract."
    - **similarity check:** closest true topic: `past_performance_contracts_submission` (cosine=0.69); vs matched predicted [f3d1aa39]: cosine=0.69 (>= dedup threshold 0.6) -> would likely have been clustered together and compared by the dedup LLM call
  - predicted [84635e91] "Provide a signed SF-1449 indicating agreement with contract terms and conditions."
    - **similarity check:** closest true topic: `two_part_proposal_format` (cosine=0.65); vs matched predicted [96f123ea]: cosine=0.72 (>= dedup threshold 0.6) -> would likely have been clustered together and compared by the dedup LLM call
  - predicted [851ad3d3] "To demonstrate prior experience, submit a description of services provided including location and offeror's level of responsibility and authority."
    - **similarity check:** closest true topic: `prior_experience_documentation` (cosine=0.79); vs matched predicted [1a0e0f93]: cosine=0.68 (>= dedup threshold 0.6) -> would likely have been clustered together and compared by the dedup LLM call
  - predicted [8856d758] "Provide a brief description of the scope of work explaining how the contract involved work as a prime contractor under the specified NAICS code."
    - **similarity check:** closest true topic: `technical_experience_examples_submission` (cosine=0.70); vs matched predicted [6c880dce]: cosine=0.67 (>= dedup threshold 0.6) -> would likely have been clustered together and compared by the dedup LLM call
  - predicted [8e7977d6] "Offerors must follow the instructions contained in the solicitation."
    - **similarity check:** closest true topic: `statement_of_agreement_with_terms` (cosine=0.70); vs matched predicted [af210e26]: cosine=0.62 (>= dedup threshold 0.6) -> would likely have been clustered together and compared by the dedup LLM call
  - predicted [915ea31a] "Offerors are required to meet all solicitation requirements, including terms and conditions, representations, certifications, and technical requirements."
    - **similarity check:** closest true topic: `statement_of_agreement_with_terms` (cosine=0.75); vs matched predicted [af210e26]: cosine=0.69 (>= dedup threshold 0.6) -> would likely have been clustered together and compared by the dedup LLM call
  - predicted [94124548] "The offeror is responsible for ensuring the proposal is received by the contract specialist on or before the deadline."
    - **similarity check:** closest true topic: `prior_experience_documentation` (cosine=0.63); vs matched predicted [1a0e0f93]: cosine=0.62 (>= dedup threshold 0.6) -> would likely have been clustered together and compared by the dedup LLM call
  - predicted [b13cc0a0] "Provide the name and location of each submitted technical experience contract."
    - **similarity check:** closest true topic: `past_performance_contracts_submission` (cosine=0.66); vs matched predicted [f3d1aa39]: cosine=0.58 (< dedup threshold 0.6) -> dedup's cosine pre-filter would NOT have clustered these -- the dedup LLM call never saw them side by side
  - predicted [b21f9b51] "Offers shall include responses to provisions requiring offeror completion of information, representations, and certifications."
    - **similarity check:** closest true topic: `past_performance_contracts_submission` (cosine=0.67); vs matched predicted [f3d1aa39]: cosine=0.60 (>= dedup threshold 0.6) -> would likely have been clustered together and compared by the dedup LLM call
  - predicted [b906df1a] "Provide the date of the contract award and the contract award amount in dollars."
    - **similarity check:** closest true topic: `past_performance_contracts_submission` (cosine=0.63); vs matched predicted [f3d1aa39]: cosine=0.56 (< dedup threshold 0.6) -> dedup's cosine pre-filter would NOT have clustered these -- the dedup LLM call never saw them side by side
  - predicted [c626d568] "The Offeror's Price Quote shall contain the required pricing items."
    - **similarity check:** closest true topic: `statement_of_agreement_with_terms` (cosine=0.76); vs matched predicted [af210e26]: cosine=0.70 (>= dedup threshold 0.6) -> would likely have been clustered together and compared by the dedup LLM call
  - predicted [d582c960] "Provide a brief description of the contract scope of work."
    - **similarity check:** closest true topic: `past_performance_contracts_submission` (cosine=0.65); vs matched predicted [f3d1aa39]: cosine=0.63 (>= dedup threshold 0.6) -> would likely have been clustered together and compared by the dedup LLM call
  - predicted [dcddc888] "Offerors shall provide their best pricing for the Contract Line Items listed in the Cost/Price Schedule."
    - **similarity check:** closest true topic: `statement_of_agreement_with_terms` (cosine=0.64); vs matched predicted [af210e26]: cosine=0.61 (>= dedup threshold 0.6) -> would likely have been clustered together and compared by the dedup LLM call
  - predicted [e9fddfa1] "To demonstrate prior experience, submit the name, title, address, phone number, and email of the customer contact."
    - **similarity check:** closest true topic: `prior_experience_documentation` (cosine=0.77); vs matched predicted [1a0e0f93]: cosine=0.63 (>= dedup threshold 0.6) -> would likely have been clustered together and compared by the dedup LLM call
  - predicted [eaa61eac] "Provide the percentage of total labor self-performed by the offeror's employees for each submitted technical experience contract."
    - **similarity check:** closest true topic: `technical_experience_examples_submission` (cosine=0.61); vs matched predicted [6c880dce]: cosine=0.65 (>= dedup threshold 0.6) -> would likely have been clustered together and compared by the dedup LLM call
  - predicted [edc75454] "Provide the performance period, including starting and completion dates, for each submitted technical experience contract."
    - **similarity check:** closest true topic: `past_performance_contracts_submission` (cosine=0.62); vs matched predicted [f3d1aa39]: cosine=0.56 (< dedup threshold 0.6) -> dedup's cosine pre-filter would NOT have clustered these -- the dedup LLM call never saw them side by side
  - predicted [f3eee506] "To demonstrate prior experience, submit a detailed description for each year including the contract number and estimated annual dollar value."
    - **similarity check:** closest true topic: `prior_experience_documentation` (cosine=0.75); vs matched predicted [1a0e0f93]: cosine=0.62 (>= dedup threshold 0.6) -> would likely have been clustered together and compared by the dedup LLM call
  - predicted [f51972d0] "The subject line of the email shall start with the specified RFQ reference number."
    - **similarity check:** closest true topic: `submission_deadline` (cosine=0.57); vs matched predicted [62d52ab9]: cosine=0.57 (< dedup threshold 0.6) -> dedup's cosine pre-filter would NOT have clustered these -- the dedup LLM call never saw them side by side
  - predicted [fd904b5c] "Contractors shall have safety training in electrical safety outlined in OSHA Standard 29 CFR 1910 Subpart S and NFPA 70E."
    - **similarity check:** closest true topic: `electrical_safety_training_certification_submission` (cosine=0.78); vs matched predicted [827a40fd]: cosine=0.54 (< dedup threshold 0.6) -> dedup's cosine pre-filter would NOT have clustered these -- the dedup LLM call never saw them side by side

## Coverage flags

Clean 1:1 matches (recall counted them as found) whose citations don't fully overlap in length, split by which side is off. Over-split/over-merge/tangled matches are excluded here -- their predicted fragments are inherently partial by construction, already shown in the recall breakdown above.

**Requirements captured with extra text** (0) — the predicted citation is padded beyond the true one:
- none

**Requirements captured incompletely** (2) — the predicted citation misses part of the true one:
- predicted [052be2c9] is contained in true `sdvosb_setaside_eligibility` — 50.4%:
    predicted: "By submitting an offer, the contractor represents that it is an eligible and certified SDVOSB."
    true: "(c) Representation. Pursuant to 38 U.S.C. 8127(e), only certified SDVOSBs listed in the SBA certification database are considered eligible to receive award of a resulting contract. By submitting an offer, the prospective contractor represents that it is an eligible and certified SDVOSB as defined in this clause, 13 CFR 121, 125, and 128, and VAAR subpart 819.70."

- predicted [1a0e0f93] is contained in true `prior_experience_documentation` — 26.9%:
    predicted: "Offeror shall provide at least five years of prior experience as a prime contractor in waste removal services."
    true: "Offeror shall provide at least five (5) years of prior experience as the Prime Contractor Waste Removal Services. ... i. Contract number ii. Estimated annual dollar value of contract iii. Description of services (including location) provided and the offeror’s level of responsibility and authority on the project. iv. Date of contract start and completion. v. Name, title, address, phone number, and email of customer contact."

## is_mandatory accuracy

For each clean or one-to-many match (tangled groups excluded — there's no single "one" to compare against), does `is_mandatory` agree with the true value? A one-to-many group counts as correct only if every member on the "many" side agrees with the "one".

**Accuracy: 100.0% (12 groups)**

Mismatched:
- none

## is_text_verifiable accuracy

For each clean or one-to-many match (tangled groups excluded), does `is_text_verifiable` agree with the true value (all-or-nothing on the "many" side, same rule as is_mandatory above)? A wrong `false` here means the pipeline skips verdict generation for a requirement that should get one.

**Accuracy: 58.3% (12 groups)**

Mismatched:
- true: `sdvosb_setaside_eligibility`=False; predicted: `052be2c9`=True — "(c) Representation. Pursuant to 38 U.S.C. 8127(e), only certified SDVOSBs listed in the SBA certification database are considered eligible to receive award of a resulting contract. By submitting an offer, the prospective contractor represents that it is an eligible and certified SDVOSB as defined in this clause, 13 CFR 121, 125, and 128, and VAAR subpart 819.70."
- true: `security_sanctions_representations`=False; predicted: `577463b9`=True, `fc93c98a`=True — "(d) FASCSA Representation. By submission of this offer, the offeror represents that it has conducted a reasonable inquiry, and that the offeror does not propose to provide or use in response to this solicitation any covered article, or any products or services produced or provided by a source, if the covered article or the source is prohibited by an applicable FASCSA order in effect on the date the solicitation was issued, except as waived by the solicitation, or as disclosed in paragraph (g). ... (e) Sudan certification. By submission of its offer, the offeror certifies, after conducting a reasonable inquiry (that looks at any information in the offeror’s possession but does not need to include an internal or third-party audit), that the offeror does not conduct any restricted business operations in Sudan."
- true: `submission_deadline`=False; predicted: `0a7a8ec5`=True, `62d52ab9`=True — "All questions regarding the solicitation must be submitted via email to James.horne@va.gov no later than 10:00 a.m. central time on 9/15/26. ... Quote Submission: All quotes must be submitted electronically, via email to James.horne@va.gov."
- true: `contractor_certification_qualifications`=False; predicted: `d4e855fe`=True — "A. Contractors shall be currently certified by either the InterNational Electrical Testing Association (NETA) as NETA Certified Technician or the National Institute for Certification in Engineering Technologies (NICET) and completed the Occupational Safety & Health Administration (OSHA) approved 10-hour construction safety training."
- true: `contractor_experience_tenure`=False; predicted: `2b89b913`=True — "B. Contractors shall have technical training and a history of work experience in maintenance, inspection, and testing of the low and medium voltage Electrical Power Distribution Systems and its components in healthcare, industrial, educational, and commercial facilities for a minimum of five (5) continuous years from the date of this solicitation."

## Verdict accuracy

The confusion matrix covers only clean 1:1 matches — split/merge groups have no single pair to plot, but still count in the two rates below.

Clean matches scored: 4

| true \ pipeline said | `compliant` | `non_compliant` | `contradictory` | `insufficient_information` |
|---|---|---|---|---|
| `compliant` | 1 | 1 | 0 | 0 |
| `non_compliant` | 0 | 1 | 0 | 0 |
| `contradictory` | 0 | 0 | 0 | 0 |
| `insufficient_information` | 0 | 1 | 0 | 0 |

Why some rows are empty:
- `contradictory` row is empty: true `electrical_safety_training_certification_submission` — over_split match — no single pair to plot

**Mismatched clean matches** — every off-diagonal cell above, in full: the full context retrieved and shown to the model, what it chose to cite from that context, and its reasoning ("model's ..."), next to what `true_verdicts.json` expects ("expected ...").

- `technical_capabilities_letter` — acceptable: ['compliant'], predicted: non_compliant
  - **requirement:** "Offerors shall provide a capabilities letter not exceeding five pages describing their technical approach, methodology, and technique."
  - **retrieved context (shown to the model):** "From: bids@heartlandelectricaltesting.com To: James.horne@va.gov Subject: 36C25526Q0501 - Quote for Electrical Power Distribution Testing Solicitation Number: 36C25526Q0501 Heartland Electrical Testing Services, LLC 4820 Industrial Parkway Kansas City, MO 64120 (816) 555-2290 Uni [...truncated]"
  - **retrieved context (shown to the model):** "Technical Experience Examples: 1. Sedgwick County Adult Detention Facility, Wichita, KS. Performance period: 01/2021-03/2021. 100% of labor self-performed by Heartland employees. Scope: NETA-standard testing of switchgear, transformers, and circuit breakers as prime contractor un [...truncated]"
  - **retrieved context (shown to the model):** "Prior Experience: Heartland Electrical Testing Services has performed electrical power distribution testing and maintenance services for healthcare and industrial clients for the past six years. Representative engagements include hospital electrical infrastructure testing contrac [...truncated]"
  - **model's evidence (what it chose to cite):** "Offerors shall provide a capabilities letter not exceeding five pages describing their technical approach, methodology, and technique."
  - **model's reasoning:** The requirement explicitly states that offerors shall provide a capabilities letter not exceeding five pages describing their technical approach, methodology, and technique. Although the bidder includes a short section titled 'Technical Capabilities' within their email body, they failed to provide a formal separate capabilities letter as required by the solicitation.
  - **expected evidence (true_verdicts.json):** "Heartland Electrical Testing Services has over a decade of experience performing NETA-standard electrical testing and maintenance for hospital and industrial clients. Our technical approach follows NETA Maintenance Testing Specifications for infrared scanning, breaker trip testing, ground fault protection testing, and transformer oil sampling, using calibrated diagnostic equipment and a documented verification checklist at each stage of the process."
  - **expected reasoning:** Application describes a specific technical approach, methodology, and technique (NETA-standard testing procedures, diagnostic equipment, verification checklist) rather than merely reciting the Performance Work Statement.

**False-compliant rate** — dangerous direction: the true verdict requires an issue (anything but `compliant`), but every predicted verdict in the group is `compliant`.
- rate: 12.5%

- group of 2 true topic(s) and 3 predicted requirement(s) (not a 1:1 match, so there is no single correct pairing between them):
  - true `subcontractor_technical_experience_submission` — "Contractors shall provide evidence of subcontractors’ technical qualifications and experience needed to meet the technical performance requirements of this solicitation, if applicable. Offerors must submit no less than two (2) examples of their technical experience with contracts that involved technical requirements similar to the requirements of this solicitation." (acceptable: ['insufficient_information'])
      - **expected evidence (true_verdicts.json):** "remainder by a licensed subcontractor."
      - **expected reasoning:** Application mentions a subcontractor performed part of the work in one technical experience example, suggesting the conditional requirement may be triggered, but never provides the subcontractor's own technical experience examples in the required format.
  - true `technical_experience_examples_submission` — "Contractors shall provide evidence they have the technical qualifications and experience needed to meet the technical performance requirements of this solicitation. Offerors must submit no less than two (2) examples of their technical experience with contracts that involved technical requirements similar to the requirements of this solicitation." (acceptable: ['compliant'])
      - **expected evidence (true_verdicts.json):** "1. Sedgwick County Adult Detention Facility, Wichita, KS. Performance period: 01/2021-03/2021. 100% of labor self-performed by Heartland employees. Scope: NETA-standard testing of switchgear, transformers, and circuit breakers as prime contractor under NAICS 221122, technically similar to the work under this solicitation. 2. Olathe Medical Center, Olathe, KS. Performance period: 09/2020-11/2020. 90% of labor self-performed by Heartland employees, remainder by a licensed subcontractor. Scope: NETA-standard testing of the emergency power distribution system as prime contractor under NAICS 221122, technically similar to the work under this solicitation."
      - **expected reasoning:** Application provides two technical experience examples as prime contractor under NAICS 221122, each with location, performance period, percentage self-performed, and a scope description technically similar to this solicitation.
  - **retrieved context (shown to the model):** "Technical Experience Examples: 1. Sedgwick County Adult Detention Facility, Wichita, KS. Performance period: 01/2021-03/2021. 100% of labor self-performed by Heartland employees. Scope: NETA-standard testing of switchgear, transformers, and circuit breakers as prime contractor un [...truncated]"
  - **retrieved context (shown to the model):** "Prior Experience: Heartland Electrical Testing Services has performed electrical power distribution testing and maintenance services for healthcare and industrial clients for the past six years. Representative engagements include hospital electrical infrastructure testing contrac [...truncated]"
  - **retrieved context (shown to the model):** "From: bids@heartlandelectricaltesting.com To: James.horne@va.gov Subject: 36C25526Q0501 - Quote for Electrical Power Distribution Testing Solicitation Number: 36C25526Q0501 Heartland Electrical Testing Services, LLC 4820 Industrial Parkway Kansas City, MO 64120 (816) 555-2290 Uni [...truncated]"
  - predicted verdicts in this group:
    - predicted [6c880dce] "Contractors shall provide evidence they have the technical qualifications and experience needed to meet the technical performance requirements." — verdict: compliant
      - **model's evidence (what it chose to cite):** "Technical Experience Examples: 1. Sedgwick County Adult Detention Facility, Wichita, KS... Scope: NETA-standard testing of switchgear, transformers, and circuit breakers as prime contractor under NAICS 221122, technically similar to the work under this solicitation."
      - **model's evidence (what it chose to cite):** "Prior Experience: Heartland Electrical Testing Services has performed electrical power distribution testing and maintenance services for healthcare and industrial clients for the past six years."
      - **model's evidence (what it chose to cite):** "Technical Capabilities: Heartland Electrical Testing Services has over a decade of experience performing NETA-standard electrical testing and maintenance for hospital and industrial clients."
      - **model's reasoning:** The bidder provides extensive evidence of its technical qualifications and experience, including specific past performance contracts, NETA-standard testing experience for healthcare and industrial facilities, and technician training qualifications, which fully satisfies the requirement.
    - predicted [db32b26f] "Contractors shall provide evidence of subcontractors' technical qualifications and experience if applicable." — verdict: compliant
      - **model's evidence (what it chose to cite):** "90% of labor self-performed by Heartland employees, remainder by a licensed subcontractor."
      - **model's reasoning:** The requirement states that contractors shall provide evidence of subcontractors' technical qualifications and experience if applicable. The bidder mentions using a subcontractor for a portion of the labor on one project (Olathe Medical Center), but no further subcontractors are stated to be used for the current solicitation work, making the requirement conditionally applicable or fulfilled by noting the context. Furthermore, the instructions specify that if a requirement is conditional and the condition's applicability is not clearly triggered for the main scope, silence or minor mentions are handled appropriately. In this case, the bidder mentions a licensed subcontractor for past work, and since no subcontractors are proposed for the current contract, providing subcontractor qualifications is not applicable. Therefore, the application is compliant.
    - predicted [e0b4adcc] "Offerors must submit no less than two examples of their technical experience with contracts involving similar technical requirements." — verdict: compliant
      - **model's evidence (what it chose to cite):** "1. Sedgwick County Adult Detention Facility, Wichita, KS. Performance period: 01/2021-03/2021. 100% of labor self-performed by Heartland employees. Scope: NETA-standard testing of switchgear, transformers, and circuit breakers as prime contractor under NAICS 221122, technically similar to the work under this solicitation."
      - **model's evidence (what it chose to cite):** "2. Olathe Medical Center, Olathe, KS. Performance period: 09/2020-11/2020. 90% of labor self-performed by Heartland employees, remainder by a licensed subcontractor. Scope: NETA-standard testing of the emergency power distribution system as prime contractor under NAICS 221122, technically similar to the work under this solicitation."
      - **model's evidence (what it chose to cite):** "1. Contract: St. Luke's Hospital Electrical System Testing, Contract No. SLH-2022-0447, awarded by St. Luke's Health System, awarded 03/2022, contract value $62,000. Scope: annual electrical distribution testing and maintenance."
      - **model's evidence (what it chose to cite):** "2. Contract: Fort Leavenworth Commissary Electrical Testing, Contract No. W9124J-21-C-0083, awarded by U.S. Army, awarded 06/2021, contract value $41,500. Scope: triennial switchgear and transformer testing."
      - **model's reasoning:** The requirement states that offerors must submit no less than two examples of their technical experience with contracts involving similar technical requirements. The bidder provides multiple detailed examples of past contracts (such as the Sedgwick County Adult Detention Facility, Olathe Medical Center, St. Luke's Hospital, and Fort Leavenworth Commissary contracts) that involve NETA-standard testing of electrical infrastructure and are explicitly noted as technically similar to the work under the solicitation. This satisfies the requirement.

**False-issue rate** — mirror direction: the true verdict is `compliant` only, but the pipeline raised an issue anyway.
- rate: 12.5%

- `technical_capabilities_letter` — acceptable: ['compliant'], predicted: non_compliant
  - **requirement:** "Offerors shall provide a capabilities letter not exceeding five pages describing their technical approach, methodology, and technique."
  - **retrieved context (shown to the model):** "From: bids@heartlandelectricaltesting.com To: James.horne@va.gov Subject: 36C25526Q0501 - Quote for Electrical Power Distribution Testing Solicitation Number: 36C25526Q0501 Heartland Electrical Testing Services, LLC 4820 Industrial Parkway Kansas City, MO 64120 (816) 555-2290 Uni [...truncated]"
  - **retrieved context (shown to the model):** "Technical Experience Examples: 1. Sedgwick County Adult Detention Facility, Wichita, KS. Performance period: 01/2021-03/2021. 100% of labor self-performed by Heartland employees. Scope: NETA-standard testing of switchgear, transformers, and circuit breakers as prime contractor un [...truncated]"
  - **retrieved context (shown to the model):** "Prior Experience: Heartland Electrical Testing Services has performed electrical power distribution testing and maintenance services for healthcare and industrial clients for the past six years. Representative engagements include hospital electrical infrastructure testing contrac [...truncated]"
  - **model's evidence (what it chose to cite):** "Offerors shall provide a capabilities letter not exceeding five pages describing their technical approach, methodology, and technique."
  - **model's reasoning:** The requirement explicitly states that offerors shall provide a capabilities letter not exceeding five pages describing their technical approach, methodology, and technique. Although the bidder includes a short section titled 'Technical Capabilities' within their email body, they failed to provide a formal separate capabilities letter as required by the solicitation.
  - **expected evidence (true_verdicts.json):** "Heartland Electrical Testing Services has over a decade of experience performing NETA-standard electrical testing and maintenance for hospital and industrial clients. Our technical approach follows NETA Maintenance Testing Specifications for infrared scanning, breaker trip testing, ground fault protection testing, and transformer oil sampling, using calibrated diagnostic equipment and a documented verification checklist at each stage of the process."
  - **expected reasoning:** Application describes a specific technical approach, methodology, and technique (NETA-standard testing procedures, diagnostic equipment, verification checklist) rather than merely reciting the Performance Work Statement.

**Unscored** — split/merge groups excluded from the matrix above (still counted in the two rates above):
- group 1:
  - true `offer_content_minimum_elements` — "As a minimum, offers shall include— (1) The solicitation number; (2) The name, address, telephone number of the Offeror; (3) The Offeror’s Unique Entity Identifier (UEI) and, if applicable, Electronic Funds Transfer (EFT) indicator;" (acceptable: ['compliant'])
  - predicted [21db188f] "Offers shall include the solicitation number." — verdict: compliant
  - predicted [7d97d851] "Offers shall include the offeror's Unique Entity Identifier (UEI) and EFT indicator if applicable." — verdict: compliant
  - predicted [9467cb78] "Offers shall include the name, address, and telephone number of the offeror." — verdict: compliant
- group 2:
  - true `two_part_proposal_format` — "The proposal shall be prepared in two (2) parts: 1) price response and 2) a non-price response. The pricing response shall consist of the signed Standard Form (SF) 1449 and completion of the price schedule(s). The non-price response shall address the non-price factors." (acceptable: ['compliant'])
  - predicted [51a7a942] "The proposal shall be prepared in two parts: price response and non-price response." — verdict: compliant
  - predicted [5ddad1d9] "The non-price response shall address the non-price factors." — verdict: compliant
  - predicted [96f123ea] "The pricing response shall consist of the signed Standard Form 1449 and completion of the price schedule." — verdict: compliant
- group 3:
  - true `subcontractor_technical_experience_submission` — "Contractors shall provide evidence of subcontractors’ technical qualifications and experience needed to meet the technical performance requirements of this solicitation, if applicable. Offerors must submit no less than two (2) examples of their technical experience with contracts that involved technical requirements similar to the requirements of this solicitation." (acceptable: ['insufficient_information'])
  - true `technical_experience_examples_submission` — "Contractors shall provide evidence they have the technical qualifications and experience needed to meet the technical performance requirements of this solicitation. Offerors must submit no less than two (2) examples of their technical experience with contracts that involved technical requirements similar to the requirements of this solicitation." (acceptable: ['compliant'])
  - predicted [6c880dce] "Contractors shall provide evidence they have the technical qualifications and experience needed to meet the technical performance requirements." — verdict: compliant
  - predicted [db32b26f] "Contractors shall provide evidence of subcontractors' technical qualifications and experience if applicable." — verdict: compliant
  - predicted [e0b4adcc] "Offerors must submit no less than two examples of their technical experience with contracts involving similar technical requirements." — verdict: compliant
- group 4:
  - true `electrical_safety_training_certification_submission` — "Training certifications shall be submitted to the VA Contracting Officer with the proposal for this solicitation. If no training certifications are available, the contractor’s employer shall certify that he/she has met this requirement in writing and submit it to the VA Contracting Officer with the proposal for this solicitation." (acceptable: ['contradictory'])
  - predicted [827a40fd] "If no training certifications are available, the contractor's employer shall certify in writing that the requirement has been met and submit it with the proposal." — verdict: contradictory
  - predicted [a88a6ec2] "Training certifications shall be submitted to the VA Contracting Officer with the proposal." — verdict: contradictory

## Evidence

**Citation-verified rate** (evidence-level): fraction of evidence quotes actually located in application.txt.
- rate: 88.5% (9 unverified of 78)

**Evidence recall**: does the expected evidence span (from `true_verdicts.json`) show up somewhere in the requirement's retrieved chunks, before the verdict step chose what to cite? Topics never extracted as a requirement are excluded — that failure is already counted by requirement recall above.
- recall: 100.0% (9/9)
- missed:
  - none
