# Evaluation report

## Summary metrics

Machine-readable numbers for averaging across tenders -- every value here is explained in the sections below. `null` means the metric doesn't apply to this run (e.g. no verdict-only artifact present).

```json
{
  "requirement_recall": 0.9375,
  "requirement_recall_matched": 15,
  "requirement_recall_total": 16,
  "requirement_precision": 0.4583,
  "citation_verified_rate": 1.0,
  "is_mandatory_accuracy": 0.9091,
  "is_mandatory_scored": 11,
  "is_text_verifiable_accuracy": 1.0,
  "is_text_verifiable_scored": 11,
  "verdict_clean_match_count": 9,
  "verdict_accuracy": 0.5556,
  "false_compliant_rate": 0.4,
  "false_issue_rate": 0.1,
  "evidence_citation_verified_rate": 0.8571,
  "evidence_recall": 1.0,
  "verdict_only_accuracy": null,
  "verdict_only_scored": null
}
```

## Requirement recall

For each `true_requirements.json` topic, did the pipeline extract something whose tender.txt citation overlaps the true one? A pure text-offset check, not a judgment of meaning — see coverage flags below for extractions that are technically "found" but sloppy.

**Recall: 93.8% (15/16)**

**Missed** (1) — no overlapping predicted requirement at all. "chunk check" is a mechanical (no-LLM) re-chunking of the source document: whether this topic's matching text ever appeared whole in one chunk handed to the extraction model, or was split across chunks.
- true `quote_due_date` — "Quotations are due September 18, 2026, 17:00 local time"
    - **chunk check:** [458:513] whole, in chunk 0 -- the model saw this text intact

**Over-split** (0) — one true topic extracted as several separate predicted requirements:
- none

**Over-merge** (1) — one predicted requirement covering several distinct true topics:
- predicted [69799e48] "As a minimum, offers shall include the solicitation number, offeror contact details, UEI and EFT indicators, information to evaluate factors, completed representations and certifications, a statement of agreement with terms, and a completed SF-1449 cover page and Section 1." — verdict: compliant lumps together 5 true requirements:
  - true `offeror_contact_info_stated` — "(2) The name, address, telephone number of the Offeror;"
  - true `sf1449_section1_completion` — "1. A completed solicitation, in which the SF-1449 cover page (blocks 12, 17, 19-24, and 30 as appropriate), and Section 1 has been filled out."
  - true `solicitation_number_stated` — "(1) The solicitation number;"
  - true `statement_of_agreement_with_terms` — "(6) A statement specifying the extent of agreement with all terms, conditions, and provisions included in the solicitation and any solicitation amendments."
  - true `uei_eft_indicator_stated` — "(3) The Offeror’s Unique Entity Identifier (UEI) and, if applicable, Electronic Funds Transfer (EFT) indicator;"

**Tangled** (0) — several true and several predicted requirements all overlapping at once:
- none

## Requirement precision

**Citation-verified rate** (hallucination check): fraction of predicted requirements whose citation was actually located in tender.txt (exactly or via fuzzy match).
- rate: 100.0%
- unverified:
  - none

**Classification precision**: fraction of predicted requirements that matched a true requirement.
- rate: 45.8%
- unexplained (13) — the model recognized these as requirements, but they don't match any true requirement. "closest true topic" is a mechanical (no-LLM) embedding-similarity lookup against every true topic's description; "dedup visibility" checks whether dedup's own cosine pre-filter would have clustered this candidate with whatever predicted requirement DID match that topic -- i.e. whether the dedup LLM call ever had a chance to compare them:
  - predicted [0aa19fb3] "If the offeror has not performed comparable services in Estonia, then the offeror shall provide its international experience."
    - **similarity check:** closest true topic: `past_performance_references` (cosine=0.73); vs matched predicted [8672ed55]: cosine=0.48 (< dedup threshold 0.6) -> dedup's cosine pre-filter would NOT have clustered these -- the dedup LLM call never saw them side by side
  - predicted [1f73f24c] "Contractor will be responsible for providing individually packed lunch and dinner meals for seven people per day (98 meals per week), and shall schedule cooking, packaging, and delivery requirements to ensure the availability of daily meals as specified."
    - **similarity check:** closest true topic: `menu_plan_sample_20day` (cosine=0.52); vs matched predicted [02a27b0d]: cosine=0.60 (>= dedup threshold 0.6) -> would likely have been clustered together and compared by the dedup LLM call
  - predicted [373f21ab] "All food is to be delivered to the MSGR at Toom-Kuninga 20A, Tallinn."
    - **similarity check:** closest true topic: `menu_plan_sample_20day` (cosine=0.55); vs matched predicted [02a27b0d]: cosine=0.59 (< dedup threshold 0.6) -> dedup's cosine pre-filter would NOT have clustered these -- the dedup LLM call never saw them side by side
  - predicted [3fe87815] "Contractor may use discretion on when to transport meals (three times a week or multiple days per trip) to the residence in Tallinn to minimize daily transportation."
    - **similarity check:** closest true topic: `past_performance_references` (cosine=0.59); vs matched predicted [8672ed55]: cosine=0.48 (< dedup threshold 0.6) -> dedup's cosine pre-filter would NOT have clustered these -- the dedup LLM call never saw them side by side
  - predicted [586594c9] "The Contractor shall be responsible for quality control, performing regular surprise inspection visits to the work site, and coordinating these visits with the COR."
    - **similarity check:** closest true topic: `past_performance_references` (cosine=0.56); vs matched predicted [8672ed55]: cosine=0.51 (< dedup threshold 0.6) -> dedup's cosine pre-filter would NOT have clustered these -- the dedup LLM call never saw them side by side
  - predicted [596e4a9c] "The Contractor shall provide a supervisor as the main point of contact with U.S. Government personnel, who shall have sufficient English language skill to communicate with the staff."
    - **similarity check:** closest true topic: `project_manager_english_liaison` (cosine=0.69); vs matched predicted [c9426017]: cosine=0.71 (>= dedup threshold 0.6) -> would likely have been clustered together and compared by the dedup LLM call
  - predicted [80fcc169] "The Contractor shall furnish all managerial, administrative, and direct labor personnel that are necessary to accomplish the work in this contract."
    - **similarity check:** closest true topic: `capability_evidence_personnel_equipment_financial` (cosine=0.60); vs matched predicted [65ed0a81]: cosine=0.58 (< dedup threshold 0.6) -> dedup's cosine pre-filter would NOT have clustered these -- the dedup LLM call never saw them side by side
  - predicted [8ec18f7f] "Contractor employees shall be on site only for contractual duties and not for other business purposes."
    - **similarity check:** closest true topic: `solicitation_number_stated` (cosine=0.49); vs matched predicted [69799e48]: cosine=0.41 (< dedup threshold 0.6) -> dedup's cosine pre-filter would NOT have clustered these -- the dedup LLM call never saw them side by side
  - predicted [a747a848] "The Contractor shall prepare general instructions for the work force and provide drafts to the Contracting Officer's Representative (COR) for review within thirty days after contract award."
    - **similarity check:** closest true topic: `signed_dated_offer_submission` (cosine=0.64); vs matched predicted [33046e86]: cosine=0.60 (>= dedup threshold 0.6) -> would likely have been clustered together and compared by the dedup LLM call
  - predicted [d071076f] "The Contractor shall maintain schedules that take into consideration the hours that staff can effectively perform services without burdening Post security personnel."
    - **similarity check:** closest true topic: `past_performance_references` (cosine=0.55); vs matched predicted [8672ed55]: cosine=0.48 (< dedup threshold 0.6) -> dedup's cosine pre-filter would NOT have clustered these -- the dedup LLM call never saw them side by side
  - predicted [de9f3efa] "Proposals must be in English"
    - **similarity check:** closest true topic: `solicitation_number_stated` (cosine=0.66); vs matched predicted [69799e48]: cosine=0.57 (< dedup threshold 0.6) -> dedup's cosine pre-filter would NOT have clustered these -- the dedup LLM call never saw them side by side
  - predicted [f245b0eb] "The Contractor will be responsible for removing used food containers and any uneaten meals from the MSGR and disposing of them at contractor facilities during meal deliveries."
    - **similarity check:** closest true topic: `risk_management_plan_with_proposal` (cosine=0.47); vs matched predicted [0779b642]: cosine=0.47 (< dedup threshold 0.6) -> dedup's cosine pre-filter would NOT have clustered these -- the dedup LLM call never saw them side by side
  - predicted [f78dc5be] "The offeror must have adequate financial resources, ability to comply with performance periods, a satisfactory record of integrity and business ethics, necessary organization, equipment, and facilities, and be otherwise qualified and eligible to receive an award."
    - **similarity check:** closest true topic: `capability_evidence_personnel_equipment_financial` (cosine=0.66); vs matched predicted [65ed0a81]: cosine=0.65 (>= dedup threshold 0.6) -> would likely have been clustered together and compared by the dedup LLM call

## Coverage flags

Clean 1:1 matches (recall counted them as found) whose citations don't fully overlap in length, split by which side is off. Over-split/over-merge/tangled matches are excluded here -- their predicted fragments are inherently partial by construction, already shown in the recall breakdown above.

**Requirements captured with extra text** (1) — the predicted citation is padded beyond the true one:
- true `signed_dated_offer_submission` is contained in predicted [33046e86] — 22.2%:
    predicted: "Submit signed and dated offers to the specified office at or before the exact time specified in the solicitation."
    true: "Submit signed and dated offers"

**Requirements captured incompletely** (2) — the predicted citation misses part of the true one:
- predicted [0779b642] is contained in true `risk_management_plan_with_proposal` — 46.4%:
    predicted: "Provide as part of proposal response and updated/maintained throughout performance."
    true: "Risk Management Plan (Risk management and mitigation-quality control & assurance, etc.) 1 COR Provide as part of proposal response and updated/maintained throughout performance"

- predicted [ad1e20f1] is contained in true `submission_format_and_channel` — 38.9%:
    predicted: "file size must not exceed 30MB per email (split into separate emails if larger)"
    true: "submitted electronically to TallinnGSOProcurement@state.gov in MS-Word 2007/2010, MS-Excel 2007/2010, or Adobe PDF format; file size must not exceed 30MB per email (split into separate emails if larger)."

## is_mandatory accuracy

For each clean or one-to-many match (tangled groups excluded — there's no single "one" to compare against), does `is_mandatory` agree with the true value? A one-to-many group counts as correct only if every member on the "many" side agrees with the "one".

**Accuracy: 90.9% (11 groups)**

Mismatched:
- true: `local_license_permit_conditional`=False; predicted: `bc82f10e`=True — "5. If providing this service requires special license or permit, then the offeror shall address its plan to obtain all licenses and permits required by local law. If offeror already possesses the locally required licenses and permits, a copy shall be provided."

## is_text_verifiable accuracy

For each clean or one-to-many match (tangled groups excluded), does `is_text_verifiable` agree with the true value (all-or-nothing on the "many" side, same rule as is_mandatory above)? A wrong `false` here means the pipeline skips verdict generation for a requirement that should get one.

**Accuracy: 100.0% (11 groups)**

Mismatched:
- none

## Verdict accuracy

The confusion matrix covers only clean 1:1 matches — split/merge groups have no single pair to plot, but still count in the two rates below.

Clean matches scored: 9

| true \ pipeline said | `compliant` | `non_compliant` | `contradictory` | `insufficient_information` |
|---|---|---|---|---|
| `compliant` | 4 | 0 | 0 | 1 |
| `non_compliant` | 0 | 1 | 0 | 0 |
| `contradictory` | 2 | 0 | 0 | 0 |
| `insufficient_information` | 1 | 0 | 0 | 0 |

**Mismatched clean matches** — every off-diagonal cell above, in full: the full context retrieved and shown to the model, what it chose to cite from that context, and its reasoning ("model's ..."), next to what `true_verdicts.json` expects ("expected ...").

- `past_performance_references` — acceptable: ['contradictory'], predicted: compliant
  - **requirement:** "List of clients over the past two years demonstrating prior experience with relevant past performance information and references."
  - **retrieved context (shown to the model):** "SAM Registration: proof of SAM registration and our SAM UEI number are provided above under Cover Page Information. Capability: Tallinn Fresh Kitchen OÜ employs 9 kitchen and delivery staff and operates one delivery van. An unaudited internal financial statement is available on r [...truncated]"
  - **retrieved context (shown to the model):** "Tallinn Fresh Kitchen OÜ Väike-Ameerika 22, 10129 Tallinn, Estonia RE: Solicitation 19EN1026Q0383 -- Commercial Cook Services, Marine Security Guard Residence, U.S. Embassy Tallinn Tallinn Fresh Kitchen OÜ submits this quotation in agreement with all terms, conditions, and provis [...truncated]"
  - **retrieved context (shown to the model):** "PAYMENT INSTRUCTIONS Please remit payment via Electronic Funds Transfer to IBAN EE38 2200 0011 2033 1234. ADDITIONAL REFERENCE Our ongoing catering contract with a Nordic shipping firm's Tallinn office (2022-2023) further demonstrates our reliability delivering to secured facilit [...truncated]"
  - **model's evidence (what it chose to cite):** "We have not previously performed comparable services in Estonia, so we provide our international experience: catering services for the Netherlands Embassy in Riga, Latvia (2023-2024), contract value EUR 38,500, point of contact Mr. Aivars Ozols, Facilities Officer, +371 6721 4408."
  - **model's evidence (what it chose to cite):** "Our ongoing catering contract with a Nordic shipping firm's Tallinn office (2022-2023) further demonstrates our reliability delivering to secured facilities within Estonia."
  - **model's reasoning:** The bidder provided a list of clients over the past two years, which includes past performance information and references such as the Netherlands Embassy in Riga and a Nordic shipping firm's Tallinn office.
  - **expected evidence (true_verdicts.json):** "We have not previously performed comparable services in Estonia, so we provide our international experience: catering services for the Netherlands Embassy in Riga, Latvia (2023-2024), contract value EUR 38,500, point of contact Mr. Aivars Ozols, Facilities Officer, +371 6721 4408."
  - **expected evidence (true_verdicts.json):** "Our ongoing catering contract with a Nordic shipping firm's Tallinn office (2022-2023) further demonstrates our reliability delivering to secured facilities within Estonia."
  - **expected reasoning:** Application states it has 'not previously performed comparable services in Estonia' and offers only international (Latvia) experience on that basis, but then separately cites an ongoing reference explicitly located within Estonia -- the two statements conflict on whether the offeror has Estonia experience at all.

- `capability_evidence_personnel_equipment_financial` — acceptable: ['insufficient_information'], predicted: compliant
  - **requirement:** "Evidence that the offeror can provide necessary personnel, equipment, and financial resources, which may be in the form of an annual fiscal report or a link thereto."
  - **retrieved context (shown to the model):** "SAM Registration: proof of SAM registration and our SAM UEI number are provided above under Cover Page Information. Capability: Tallinn Fresh Kitchen OÜ employs 9 kitchen and delivery staff and operates one delivery van. An unaudited internal financial statement is available on r [...truncated]"
  - **retrieved context (shown to the model):** "PAYMENT INSTRUCTIONS Please remit payment via Electronic Funds Transfer to IBAN EE38 2200 0011 2033 1234. ADDITIONAL REFERENCE Our ongoing catering contract with a Nordic shipping firm's Tallinn office (2022-2023) further demonstrates our reliability delivering to secured facilit [...truncated]"
  - **retrieved context (shown to the model):** "Tallinn Fresh Kitchen OÜ Väike-Ameerika 22, 10129 Tallinn, Estonia RE: Solicitation 19EN1026Q0383 -- Commercial Cook Services, Marine Security Guard Residence, U.S. Embassy Tallinn Tallinn Fresh Kitchen OÜ submits this quotation in agreement with all terms, conditions, and provis [...truncated]"
  - **model's evidence (what it chose to cite):** "Tallinn Fresh Kitchen OÜ employs 9 kitchen and delivery staff and operates one delivery van. An unaudited internal financial statement is available on request."
  - **model's reasoning:** The bidder provides evidence of personnel and equipment by stating they employ 9 kitchen and delivery staff and operate a delivery van. They also mention that an unaudited internal financial statement is available on request, which addresses the financial resources requirement.
  - **expected evidence (true_verdicts.json):** "Capability: Tallinn Fresh Kitchen OÜ employs 9 kitchen and delivery staff and operates one delivery van. An unaudited internal financial statement is available on request."
  - **expected reasoning:** Application describes staffing and vehicle capacity but offers only an unaudited internal financial statement 'on request' rather than an annual fiscal report or link, so financial capacity cannot be confirmed from the application text alone.

- `local_license_permit_conditional` — acceptable: ['contradictory'], predicted: compliant
  - **requirement:** "If providing the service requires special licenses or permits, the offeror shall address its plan to obtain them or provide a copy of already possessed locally required licenses and permits."
  - **retrieved context (shown to the model):** "SAM Registration: proof of SAM registration and our SAM UEI number are provided above under Cover Page Information. Capability: Tallinn Fresh Kitchen OÜ employs 9 kitchen and delivery staff and operates one delivery van. An unaudited internal financial statement is available on r [...truncated]"
  - **retrieved context (shown to the model):** "Tallinn Fresh Kitchen OÜ Väike-Ameerika 22, 10129 Tallinn, Estonia RE: Solicitation 19EN1026Q0383 -- Commercial Cook Services, Marine Security Guard Residence, U.S. Embassy Tallinn Tallinn Fresh Kitchen OÜ submits this quotation in agreement with all terms, conditions, and provis [...truncated]"
  - **retrieved context (shown to the model):** "PAYMENT INSTRUCTIONS Please remit payment via Electronic Funds Transfer to IBAN EE38 2200 0011 2033 1234. ADDITIONAL REFERENCE Our ongoing catering contract with a Nordic shipping firm's Tallinn office (2022-2023) further demonstrates our reliability delivering to secured facilit [...truncated]"
  - **model's evidence (what it chose to cite):** "Licenses and Permits: this type of food-delivery service does not require any special license or permit under Estonian law, so none is enclosed with this quotation. Our current Health Board (Terviseamet) food handling permit, renewed this year, is attached to this quotation for the Contracting Officer's reference."
  - **model's reasoning:** The requirement states that if special licenses or permits are required, the offeror shall address its plan or provide a copy of already possessed locally required licenses and permits. The bidder explicitly addressed the local legal status regarding special licenses and furthermore provided a copy of their currently held Health Board food handling permit, thereby satisfying the requirement.
  - **expected evidence (true_verdicts.json):** "Licenses and Permits: this type of food-delivery service does not require any special license or permit under Estonian law, so none is enclosed with this quotation."
  - **expected evidence (true_verdicts.json):** "Our current Health Board (Terviseamet) food handling permit, renewed this year, is attached to this quotation for the Contracting Officer's reference."
  - **expected reasoning:** Application states that this type of service 'does not require any special license or permit under Estonian law,' but immediately after attaches a current Health Board food handling permit -- the two statements conflict on whether a permit is actually required/held.

- `risk_management_plan_with_proposal` — acceptable: ['compliant'], predicted: insufficient_information
  - **requirement:** "Provide as part of proposal response and updated/maintained throughout performance."
  - **retrieved context (shown to the model):** "SAM Registration: proof of SAM registration and our SAM UEI number are provided above under Cover Page Information. Capability: Tallinn Fresh Kitchen OÜ employs 9 kitchen and delivery staff and operates one delivery van. An unaudited internal financial statement is available on r [...truncated]"
  - **retrieved context (shown to the model):** "PAYMENT INSTRUCTIONS Please remit payment via Electronic Funds Transfer to IBAN EE38 2200 0011 2033 1234. ADDITIONAL REFERENCE Our ongoing catering contract with a Nordic shipping firm's Tallinn office (2022-2023) further demonstrates our reliability delivering to secured facilit [...truncated]"
  - **retrieved context (shown to the model):** "Tallinn Fresh Kitchen OÜ Väike-Ameerika 22, 10129 Tallinn, Estonia RE: Solicitation 19EN1026Q0383 -- Commercial Cook Services, Marine Security Guard Residence, U.S. Embassy Tallinn Tallinn Fresh Kitchen OÜ submits this quotation in agreement with all terms, conditions, and provis [...truncated]"
  - **model's evidence (what it chose to cite):** "Provide as part of proposal response and updated/maintained throughout performance."
  - **model's reasoning:** The requirement states that a certain unspecified item must be provided as part of the proposal response and updated/maintained throughout performance. However, the requirement description itself is incomplete or lacks a clear subject (it does not specify *what* needs to be provided and maintained). Furthermore, the bidder's excerpts do not contain any mention of this specific obligation or whether they intend to provide and maintain it, leaving insufficient information to make a definitive compliance determination.
  - **expected evidence (true_verdicts.json):** "Our Risk Management Plan is enclosed as Appendix A with this proposal, covering identification of delivery-route risks, mitigation steps, and our quality-control checklist."
  - **expected reasoning:** Application states the Risk Management Plan is enclosed as Appendix A with the proposal, addressing risk identification, mitigation, and quality control.

**False-compliant rate** — dangerous direction: the true verdict requires an issue (anything but `compliant`), but every predicted verdict in the group is `compliant`.
- rate: 40.0%

- group of 5 true topic(s) and 1 predicted requirement(s) (not a 1:1 match, so there is no single correct pairing between them):
  - true `offeror_contact_info_stated` — "(2) The name, address, telephone number of the Offeror;" (acceptable: ['compliant'])
      - **expected evidence (true_verdicts.json):** "Offeror: Tallinn Fresh Kitchen OÜ, Väike-Ameerika 22, 10129 Tallinn, Estonia Telephone: +372 5566 3390"
      - **expected reasoning:** Application states the offeror's name, address, and telephone number.
  - true `sf1449_section1_completion` — "1. A completed solicitation, in which the SF-1449 cover page (blocks 12, 17, 19-24, and 30 as appropriate), and Section 1 has been filled out." (acceptable: ['compliant'])
      - **expected evidence (true_verdicts.json):** "SF-1449 blocks 12, 17, 19-24, and 30, and Section 1 of the solicitation, have been completed and are enclosed with this quotation."
      - **expected reasoning:** Application states the SF-1449 blocks and Section 1 are completed and enclosed.
  - true `solicitation_number_stated` — "(1) The solicitation number;" (acceptable: ['compliant'])
      - **expected evidence (true_verdicts.json):** "Solicitation Number: 19EN1026Q0383"
      - **expected reasoning:** Application states the solicitation number in the cover block.
  - true `statement_of_agreement_with_terms` — "(6) A statement specifying the extent of agreement with all terms, conditions, and provisions included in the solicitation and any solicitation amendments." (acceptable: ['compliant'])
      - **expected evidence (true_verdicts.json):** "Tallinn Fresh Kitchen OÜ submits this quotation in agreement with all terms, conditions, and provisions of the solicitation and its amendments."
      - **expected reasoning:** Application explicitly states agreement with all terms, conditions, and provisions of the solicitation and its amendments.
  - true `uei_eft_indicator_stated` — "(3) The Offeror’s Unique Entity Identifier (UEI) and, if applicable, Electronic Funds Transfer (EFT) indicator;" (acceptable: ['contradictory'])
      - **expected evidence (true_verdicts.json):** "EFT Indicator: N/A -- no Electronic Funds Transfer is required for this quote."
      - **expected evidence (true_verdicts.json):** "Please remit payment via Electronic Funds Transfer to IBAN EE38 2200 0011 2033 1234."
      - **expected reasoning:** Application states 'EFT Indicator: N/A -- no Electronic Funds Transfer is required for this quote,' but later gives EFT payment instructions (an IBAN for Electronic Funds Transfer) -- the two statements directly conflict on whether EFT applies to this quote.
  - **retrieved context (shown to the model):** "SAM Registration: proof of SAM registration and our SAM UEI number are provided above under Cover Page Information. Capability: Tallinn Fresh Kitchen OÜ employs 9 kitchen and delivery staff and operates one delivery van. An unaudited internal financial statement is available on r [...truncated]"
  - **retrieved context (shown to the model):** "Tallinn Fresh Kitchen OÜ Väike-Ameerika 22, 10129 Tallinn, Estonia RE: Solicitation 19EN1026Q0383 -- Commercial Cook Services, Marine Security Guard Residence, U.S. Embassy Tallinn Tallinn Fresh Kitchen OÜ submits this quotation in agreement with all terms, conditions, and provis [...truncated]"
  - **retrieved context (shown to the model):** "PAYMENT INSTRUCTIONS Please remit payment via Electronic Funds Transfer to IBAN EE38 2200 0011 2033 1234. ADDITIONAL REFERENCE Our ongoing catering contract with a Nordic shipping firm's Tallinn office (2022-2023) further demonstrates our reliability delivering to secured facilit [...truncated]"
  - predicted verdicts in this group:
    - predicted [69799e48] "As a minimum, offers shall include the solicitation number, offeror contact details, UEI and EFT indicators, information to evaluate factors, completed representations and certifications, a statement of agreement with terms, and a completed SF-1449 cover page and Section 1." — verdict: compliant
      - **model's evidence (what it chose to cite):** "Solicitation Number: 19EN1026Q0383"
      - **model's evidence (what it chose to cite):** "Offeror: Tallinn Fresh Kitchen OÜ, Väike-Ameerika 22, 10129 Tallinn, Estonia Telephone: +372 5566 3390"
      - **model's evidence (what it chose to cite):** "Unique Entity Identifier (UEI): TF83LQ2K9RN7 EFT Indicator: N/A -- no Electronic Funds Transfer is required for this quote."
      - **model's evidence (what it chose to cite):** "Tallinn Fresh Kitchen OÜ submits this quotation in agreement with all terms, conditions, and provisions of the solicitation and its amendments."
      - **model's evidence (what it chose to cite):** "SF-1449 blocks 12, 17, 19-24, and 30, and Section 1 of the solicitation, have been completed and are enclosed with this quotation."
      - **model's reasoning:** The bidder's application explicitly includes the solicitation number, offeror contact details, UEI and EFT indicators, information to evaluate factors, a statement of agreement with terms, and a completed SF-1449 cover page and Section 1, thereby satisfying all aspects of the requirement.

- `past_performance_references` — acceptable: ['contradictory'], predicted: compliant
  - **requirement:** "List of clients over the past two years demonstrating prior experience with relevant past performance information and references."
  - **retrieved context (shown to the model):** "SAM Registration: proof of SAM registration and our SAM UEI number are provided above under Cover Page Information. Capability: Tallinn Fresh Kitchen OÜ employs 9 kitchen and delivery staff and operates one delivery van. An unaudited internal financial statement is available on r [...truncated]"
  - **retrieved context (shown to the model):** "Tallinn Fresh Kitchen OÜ Väike-Ameerika 22, 10129 Tallinn, Estonia RE: Solicitation 19EN1026Q0383 -- Commercial Cook Services, Marine Security Guard Residence, U.S. Embassy Tallinn Tallinn Fresh Kitchen OÜ submits this quotation in agreement with all terms, conditions, and provis [...truncated]"
  - **retrieved context (shown to the model):** "PAYMENT INSTRUCTIONS Please remit payment via Electronic Funds Transfer to IBAN EE38 2200 0011 2033 1234. ADDITIONAL REFERENCE Our ongoing catering contract with a Nordic shipping firm's Tallinn office (2022-2023) further demonstrates our reliability delivering to secured facilit [...truncated]"
  - **model's evidence (what it chose to cite):** "We have not previously performed comparable services in Estonia, so we provide our international experience: catering services for the Netherlands Embassy in Riga, Latvia (2023-2024), contract value EUR 38,500, point of contact Mr. Aivars Ozols, Facilities Officer, +371 6721 4408."
  - **model's evidence (what it chose to cite):** "Our ongoing catering contract with a Nordic shipping firm's Tallinn office (2022-2023) further demonstrates our reliability delivering to secured facilities within Estonia."
  - **model's reasoning:** The bidder provided a list of clients over the past two years, which includes past performance information and references such as the Netherlands Embassy in Riga and a Nordic shipping firm's Tallinn office.
  - **expected evidence (true_verdicts.json):** "We have not previously performed comparable services in Estonia, so we provide our international experience: catering services for the Netherlands Embassy in Riga, Latvia (2023-2024), contract value EUR 38,500, point of contact Mr. Aivars Ozols, Facilities Officer, +371 6721 4408."
  - **expected evidence (true_verdicts.json):** "Our ongoing catering contract with a Nordic shipping firm's Tallinn office (2022-2023) further demonstrates our reliability delivering to secured facilities within Estonia."
  - **expected reasoning:** Application states it has 'not previously performed comparable services in Estonia' and offers only international (Latvia) experience on that basis, but then separately cites an ongoing reference explicitly located within Estonia -- the two statements conflict on whether the offeror has Estonia experience at all.

- `capability_evidence_personnel_equipment_financial` — acceptable: ['insufficient_information'], predicted: compliant
  - **requirement:** "Evidence that the offeror can provide necessary personnel, equipment, and financial resources, which may be in the form of an annual fiscal report or a link thereto."
  - **retrieved context (shown to the model):** "SAM Registration: proof of SAM registration and our SAM UEI number are provided above under Cover Page Information. Capability: Tallinn Fresh Kitchen OÜ employs 9 kitchen and delivery staff and operates one delivery van. An unaudited internal financial statement is available on r [...truncated]"
  - **retrieved context (shown to the model):** "PAYMENT INSTRUCTIONS Please remit payment via Electronic Funds Transfer to IBAN EE38 2200 0011 2033 1234. ADDITIONAL REFERENCE Our ongoing catering contract with a Nordic shipping firm's Tallinn office (2022-2023) further demonstrates our reliability delivering to secured facilit [...truncated]"
  - **retrieved context (shown to the model):** "Tallinn Fresh Kitchen OÜ Väike-Ameerika 22, 10129 Tallinn, Estonia RE: Solicitation 19EN1026Q0383 -- Commercial Cook Services, Marine Security Guard Residence, U.S. Embassy Tallinn Tallinn Fresh Kitchen OÜ submits this quotation in agreement with all terms, conditions, and provis [...truncated]"
  - **model's evidence (what it chose to cite):** "Tallinn Fresh Kitchen OÜ employs 9 kitchen and delivery staff and operates one delivery van. An unaudited internal financial statement is available on request."
  - **model's reasoning:** The bidder provides evidence of personnel and equipment by stating they employ 9 kitchen and delivery staff and operate a delivery van. They also mention that an unaudited internal financial statement is available on request, which addresses the financial resources requirement.
  - **expected evidence (true_verdicts.json):** "Capability: Tallinn Fresh Kitchen OÜ employs 9 kitchen and delivery staff and operates one delivery van. An unaudited internal financial statement is available on request."
  - **expected reasoning:** Application describes staffing and vehicle capacity but offers only an unaudited internal financial statement 'on request' rather than an annual fiscal report or link, so financial capacity cannot be confirmed from the application text alone.

- `local_license_permit_conditional` — acceptable: ['contradictory'], predicted: compliant
  - **requirement:** "If providing the service requires special licenses or permits, the offeror shall address its plan to obtain them or provide a copy of already possessed locally required licenses and permits."
  - **retrieved context (shown to the model):** "SAM Registration: proof of SAM registration and our SAM UEI number are provided above under Cover Page Information. Capability: Tallinn Fresh Kitchen OÜ employs 9 kitchen and delivery staff and operates one delivery van. An unaudited internal financial statement is available on r [...truncated]"
  - **retrieved context (shown to the model):** "Tallinn Fresh Kitchen OÜ Väike-Ameerika 22, 10129 Tallinn, Estonia RE: Solicitation 19EN1026Q0383 -- Commercial Cook Services, Marine Security Guard Residence, U.S. Embassy Tallinn Tallinn Fresh Kitchen OÜ submits this quotation in agreement with all terms, conditions, and provis [...truncated]"
  - **retrieved context (shown to the model):** "PAYMENT INSTRUCTIONS Please remit payment via Electronic Funds Transfer to IBAN EE38 2200 0011 2033 1234. ADDITIONAL REFERENCE Our ongoing catering contract with a Nordic shipping firm's Tallinn office (2022-2023) further demonstrates our reliability delivering to secured facilit [...truncated]"
  - **model's evidence (what it chose to cite):** "Licenses and Permits: this type of food-delivery service does not require any special license or permit under Estonian law, so none is enclosed with this quotation. Our current Health Board (Terviseamet) food handling permit, renewed this year, is attached to this quotation for the Contracting Officer's reference."
  - **model's reasoning:** The requirement states that if special licenses or permits are required, the offeror shall address its plan or provide a copy of already possessed locally required licenses and permits. The bidder explicitly addressed the local legal status regarding special licenses and furthermore provided a copy of their currently held Health Board food handling permit, thereby satisfying the requirement.
  - **expected evidence (true_verdicts.json):** "Licenses and Permits: this type of food-delivery service does not require any special license or permit under Estonian law, so none is enclosed with this quotation."
  - **expected evidence (true_verdicts.json):** "Our current Health Board (Terviseamet) food handling permit, renewed this year, is attached to this quotation for the Contracting Officer's reference."
  - **expected reasoning:** Application states that this type of service 'does not require any special license or permit under Estonian law,' but immediately after attaches a current Health Board food handling permit -- the two statements conflict on whether a permit is actually required/held.

**False-issue rate** — mirror direction: the true verdict is `compliant` only, but the pipeline raised an issue anyway.
- rate: 10.0%

- `risk_management_plan_with_proposal` — acceptable: ['compliant'], predicted: insufficient_information
  - **requirement:** "Provide as part of proposal response and updated/maintained throughout performance."
  - **retrieved context (shown to the model):** "SAM Registration: proof of SAM registration and our SAM UEI number are provided above under Cover Page Information. Capability: Tallinn Fresh Kitchen OÜ employs 9 kitchen and delivery staff and operates one delivery van. An unaudited internal financial statement is available on r [...truncated]"
  - **retrieved context (shown to the model):** "PAYMENT INSTRUCTIONS Please remit payment via Electronic Funds Transfer to IBAN EE38 2200 0011 2033 1234. ADDITIONAL REFERENCE Our ongoing catering contract with a Nordic shipping firm's Tallinn office (2022-2023) further demonstrates our reliability delivering to secured facilit [...truncated]"
  - **retrieved context (shown to the model):** "Tallinn Fresh Kitchen OÜ Väike-Ameerika 22, 10129 Tallinn, Estonia RE: Solicitation 19EN1026Q0383 -- Commercial Cook Services, Marine Security Guard Residence, U.S. Embassy Tallinn Tallinn Fresh Kitchen OÜ submits this quotation in agreement with all terms, conditions, and provis [...truncated]"
  - **model's evidence (what it chose to cite):** "Provide as part of proposal response and updated/maintained throughout performance."
  - **model's reasoning:** The requirement states that a certain unspecified item must be provided as part of the proposal response and updated/maintained throughout performance. However, the requirement description itself is incomplete or lacks a clear subject (it does not specify *what* needs to be provided and maintained). Furthermore, the bidder's excerpts do not contain any mention of this specific obligation or whether they intend to provide and maintain it, leaving insufficient information to make a definitive compliance determination.
  - **expected evidence (true_verdicts.json):** "Our Risk Management Plan is enclosed as Appendix A with this proposal, covering identification of delivery-route risks, mitigation steps, and our quality-control checklist."
  - **expected reasoning:** Application states the Risk Management Plan is enclosed as Appendix A with the proposal, addressing risk identification, mitigation, and quality control.

**Unscored** — split/merge groups excluded from the matrix above (still counted in the two rates above):
- group 1:
  - true `offeror_contact_info_stated` — "(2) The name, address, telephone number of the Offeror;" (acceptable: ['compliant'])
  - true `sf1449_section1_completion` — "1. A completed solicitation, in which the SF-1449 cover page (blocks 12, 17, 19-24, and 30 as appropriate), and Section 1 has been filled out." (acceptable: ['compliant'])
  - true `solicitation_number_stated` — "(1) The solicitation number;" (acceptable: ['compliant'])
  - true `statement_of_agreement_with_terms` — "(6) A statement specifying the extent of agreement with all terms, conditions, and provisions included in the solicitation and any solicitation amendments." (acceptable: ['compliant'])
  - true `uei_eft_indicator_stated` — "(3) The Offeror’s Unique Entity Identifier (UEI) and, if applicable, Electronic Funds Transfer (EFT) indicator;" (acceptable: ['contradictory'])
  - predicted [69799e48] "As a minimum, offers shall include the solicitation number, offeror contact details, UEI and EFT indicators, information to evaluate factors, completed representations and certifications, a statement of agreement with terms, and a completed SF-1449 cover page and Section 1." — verdict: compliant

## Evidence

**Citation-verified rate** (evidence-level): fraction of evidence quotes actually located in application.txt.
- rate: 85.7% (4 unverified of 28)

**Evidence recall**: does the expected evidence span (from `true_verdicts.json`) show up somewhere in the requirement's retrieved chunks, before the verdict step chose what to cite? Topics never extracted as a requirement are excluded — that failure is already counted by requirement recall above.
- recall: 100.0% (14/14)
- missed:
  - none
