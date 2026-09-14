# Evaluation report

## Summary metrics

Machine-readable numbers for averaging across tenders -- every value here is explained in the sections below. `null` means the metric doesn't apply to this run (e.g. no verdict-only artifact present).

```json
{
  "requirement_recall": 0.913,
  "requirement_recall_matched": 21,
  "requirement_recall_total": 23,
  "requirement_precision": 0.2857,
  "citation_verified_rate": 1.0,
  "is_mandatory_accuracy": 1.0,
  "is_mandatory_scored": 10,
  "is_text_verifiable_accuracy": 0.7,
  "is_text_verifiable_scored": 10,
  "verdict_clean_match_count": 6,
  "verdict_accuracy": 1.0,
  "false_compliant_rate": 0.1429,
  "false_issue_rate": 0.0,
  "evidence_citation_verified_rate": 0.9429,
  "evidence_recall": 1.0,
  "verdict_only_accuracy": null,
  "verdict_only_scored": null
}
```

## Requirement recall

For each `true_requirements.json` topic, did the pipeline extract something whose tender.txt citation overlaps the true one? A pure text-offset check, not a judgment of meaning — see coverage flags below for extractions that are technically "found" but sloppy.

**Recall: 91.3% (21/23)**

**Missed** (2) — no overlapping predicted requirement at all. "chunk check" is a mechanical (no-LLM) re-chunking of the source document: whether this topic's matching text ever appeared whole in one chunk handed to the extraction model, or was split across chunks.
- true `uei_must_be_preexisting` — "Due to the requirement falling in the 4th Quarter of FY26, this competition will require an existing SAM UEI."
    - **chunk check:** [11808:11917] whole, in chunk 9 -- the model saw this text intact
- true `single_best_price_quote` — "(e) Multiple Quotes. Quoters are requested to submit one (1) quote presenting their best price for the required Sorna Vertex 25ei & CD Burner."
    - **chunk check:** [8468:8610] whole, in chunk 7 -- the model saw this text intact

**Over-split** (0) — one true topic extracted as several separate predicted requirements:
- none

**Over-merge** (2) — one predicted requirement covering several distinct true topics:
- predicted [ed7c5986] "Offeror must meet and assert compliance with Limitations on Subcontracting (LOS) requirements in the accompanying email." — verdict: compliant lumps together 2 true requirements:
  - true `los_compliance_assertion` — "Compliance with the LOS clauses must be asserted by the offeror in the email accompanying their quote."
  - true `los_requirements_met` — "Offeror must meet LOS (Limitations on Subcontracting) requirements and per the LOS listed clauses below."
- predicted [8ba4dc86] "Quotes must include minimum required information such as solicitation number, receipt time, quoter details, technical description, warranty, price, remit-to address, FAR representations and certifications, amendment acknowledgments, and terms agreement statement." — verdict: compliant lumps together 9 true requirements:
  - true `amendment_acknowledgment` — "(9) Acknowledgment Request for Quotation amendments;"
  - true `far_52_212_3_reps_and_certs` — "(8) A completed copy of the representations and certifications under the Federal Acquisition Regulation (FAR) 52.212-3 (see FAR 52.212-3(b) for those representations and certifications that the quoter shall complete electronically)."
  - true `price_and_discount_terms_stated` — "(6) Price and any discount terms;"
  - true `quoter_contact_info_stated` — "(3) The name, address, and telephone number of the quoter;"
  - true `remit_to_address_stated` — "(7) "Remit to" address, if different from the mailing address;"
  - true `solicitation_number_stated` — "(1) The solicitation number;"
  - true `technical_description_stated` — "(4) A technical description of the items being quoted in sufficient detail to evaluate compliance with the requirements in the solicitation. This may include product literature, or other documents, if necessary."
  - true `time_specified_for_receipt_stated` — "(2) The time specified in the solicitation for receipt of quotations;"
  - true `warranty_terms_stated` — "(5) Terms of any express warranty;"

**Tangled** (1) — several true and several predicted requirements all overlapping at once:
- tangle of 2 true and 2 predicted requirements, all overlapping — needs manual untangling:
  - true `quote_signed_and_dated` — "Submit signed and dated quotes to the office specified in this Combined Synopsis: Intent to Compete/RFQ"
  - true `submission_deadline_and_channel` — "All quotations shall be emailed to: carlos.ortiz3@va.gov ... E-mailed quotes will be accepted. Submission shall be received no later than 11:00 AM EDT 09/18/26."
  - predicted [1797118e] "Quotes must be submitted via email to the specified Government point of contact." — verdict: compliant
  - predicted [75b14e27] "Submit signed and dated quotes to the specified office at or before the exact time specified (no later than 11:00 AM EDT 09/18/26)." — verdict: compliant

## Requirement precision

**Citation-verified rate** (hallucination check): fraction of predicted requirements whose citation was actually located in tender.txt (exactly or via fuzzy match).
- rate: 100.0%
- unverified:
  - none

**Classification precision**: fraction of predicted requirements that matched a true requirement.
- rate: 28.6%
- unexplained (30) — the model recognized these as requirements, but they don't match any true requirement. "closest true topic" is a mechanical (no-LLM) embedding-similarity lookup against every true topic's description; "dedup visibility" checks whether dedup's own cosine pre-filter would have clustered this candidate with whatever predicted requirement DID match that topic -- i.e. whether the dedup LLM call ever had a chance to compare them:
  - predicted [0f432020] "In general construction contracts, the prime contractor will not pay more than 85% of the amount paid by the government (excluding materials) to non-VIP-listed firms."
    - **similarity check:** closest true topic: `sdvosb_certification_required` (cosine=0.65); vs matched predicted [a91ebbd0]: cosine=0.76 (>= dedup threshold 0.6) -> would likely have been clustered together and compared by the dedup LLM call
  - predicted [1a45d0ba] "Input Capacity: 2 Bins (50 Discs EA)"
    - **similarity check:** closest true topic: `price_and_discount_terms_stated` (cosine=0.50); vs matched predicted [8ba4dc86]: cosine=0.47 (< dedup threshold 0.6) -> dedup's cosine pre-filter would NOT have clustered these -- the dedup LLM call never saw them side by side
  - predicted [1f3e9f49] "Automated DICOM profiles and local burning capabilities"
    - **similarity check:** closest true topic: `brand_name_no_substitutes` (cosine=0.49); vs matched predicted [285d3bea]: cosine=0.48 (< dedup threshold 0.6) -> dedup's cosine pre-filter would NOT have clustered these -- the dedup LLM call never saw them side by side
  - predicted [2dee47f9] "An SDVOSB/VOSB must meet the NAICS size standard and be listed in VIP to count as similarly situated."
    - **similarity check:** closest true topic: `sdvosb_certification_required` (cosine=0.73); vs matched predicted [a91ebbd0]: cosine=0.83 (>= dedup threshold 0.6) -> would likely have been clustered together and compared by the dedup LLM call
  - predicted [38a2b6f6] "The quoter agrees to hold prices firm for 30 calendar days from the date specified for receipt of quotes."
    - **similarity check:** closest true topic: `time_specified_for_receipt_stated` (cosine=0.71); vs matched predicted [8ba4dc86]: cosine=0.63 (>= dedup threshold 0.6) -> would likely have been clustered together and compared by the dedup LLM call
  - predicted [3cb8fd0d] "Work that a first-tier VIP-listed subcontractor further subcontracts counts towards the maximum allowable subcontract amount percentage."
    - **similarity check:** closest true topic: `sdvosb_certification_required` (cosine=0.69); vs matched predicted [a91ebbd0]: cosine=0.78 (>= dedup threshold 0.6) -> would likely have been clustered together and compared by the dedup LLM call
  - predicted [4166d1fa] "A joint venture agrees that, in the performance of the contract, the applicable percentage specified in paragraph (d) of this clause will be performed by the aggregate of the joint venture participants."
    - **similarity check:** closest true topic: `los_compliance_assertion` (cosine=0.55); vs matched predicted [ed7c5986]: cosine=0.59 (< dedup threshold 0.6) -> dedup's cosine pre-filter would NOT have clustered these -- the dedup LLM call never saw them side by side
  - predicted [4ebb9284] "The RFQ due date is extended to 09/18/26 at 11:00 AM EDT."
    - **similarity check:** closest true topic: `submission_deadline_and_channel` (cosine=0.58); vs matched predicted [75b14e27]: cosine=0.68 (>= dedup threshold 0.6) -> would likely have been clustered together and compared by the dedup LLM call
  - predicted [4fdb3e23] "Mouse"
    - **similarity check:** closest true topic: `price_and_discount_terms_stated` (cosine=0.45); vs matched predicted [8ba4dc86]: cosine=0.40 (< dedup threshold 0.6) -> dedup's cosine pre-filter would NOT have clustered these -- the dedup LLM call never saw them side by side
  - predicted [5e842e9c] "Disc Label Design Software and All Necessary Cabling"
    - **similarity check:** closest true topic: `brand_name_no_substitutes` (cosine=0.55); vs matched predicted [285d3bea]: cosine=0.52 (< dedup threshold 0.6) -> dedup's cosine pre-filter would NOT have clustered these -- the dedup LLM call never saw them side by side
  - predicted [6556cd45] "Deliver to: VAMC CWM (Northampton) 421 N. Main Street Leeds, MA 01053"
    - **similarity check:** closest true topic: `remit_to_address_stated` (cosine=0.48); vs matched predicted [8ba4dc86]: cosine=0.44 (< dedup threshold 0.6) -> dedup's cosine pre-filter would NOT have clustered these -- the dedup LLM call never saw them side by side
  - predicted [65732fc0] "Delivery Hours are 0800-1530."
    - **similarity check:** closest true topic: `time_specified_for_receipt_stated` (cosine=0.58); vs matched predicted [8ba4dc86]: cosine=0.52 (< dedup threshold 0.6) -> dedup's cosine pre-filter would NOT have clustered these -- the dedup LLM call never saw them side by side
  - predicted [6c8f4cd8] "Any questions or concerns regarding the solicitation must be forwarded in writing via email to the Point of Contact."
    - **similarity check:** closest true topic: `solicitation_number_stated` (cosine=0.67); vs matched predicted [8ba4dc86]: cosine=0.64 (>= dedup threshold 0.6) -> would likely have been clustered together and compared by the dedup LLM call
  - predicted [79d52f9f] "Media types: CD-R, DVD-R, BD-R with white inkjet print media"
    - **similarity check:** closest true topic: `brand_name_no_substitutes` (cosine=0.55); vs matched predicted [285d3bea]: cosine=0.52 (< dedup threshold 0.6) -> dedup's cosine pre-filter would NOT have clustered these -- the dedup LLM call never saw them side by side
  - predicted [81ee3c8c] "MOD P00003 replaces the initial Combined Synopsis and all subsequent amendments/modifications."
    - **similarity check:** closest true topic: `amendment_acknowledgment` (cosine=0.52); vs matched predicted [8ba4dc86]: cosine=0.46 (< dedup threshold 0.6) -> dedup's cosine pre-filter would NOT have clustered these -- the dedup LLM call never saw them side by side
  - predicted [8646a307] "Building has a receiving dock;"
    - **similarity check:** closest true topic: `solicitation_number_stated` (cosine=0.55); vs matched predicted [8ba4dc86]: cosine=0.48 (< dedup threshold 0.6) -> dedup's cosine pre-filter would NOT have clustered these -- the dedup LLM call never saw them side by side
  - predicted [8bcbf417] "For non-manufacturer supply contracts, the prime contractor will supply the product of a domestic small business manufacturer or processor unless a waiver is granted."
    - **similarity check:** closest true topic: `sdvosb_certification_required` (cosine=0.65); vs matched predicted [a91ebbd0]: cosine=0.75 (>= dedup threshold 0.6) -> would likely have been clustered together and compared by the dedup LLM call
  - predicted [a6f81cdc] "The package includes all associated software, hardware, implementation services, project management, installation, UPS backup power supply, and required accessories."
    - **similarity check:** closest true topic: `los_requirements_met` (cosine=0.52); vs matched predicted [ed7c5986]: cosine=0.46 (< dedup threshold 0.6) -> dedup's cosine pre-filter would NOT have clustered these -- the dedup LLM call never saw them side by side
  - predicted [afc56988] "Output Capacity: 10-Disc Drawer and 50-Disc Bin"
    - **similarity check:** closest true topic: `brand_name_no_substitutes` (cosine=0.48); vs matched predicted [285d3bea]: cosine=0.45 (< dedup threshold 0.6) -> dedup's cosine pre-filter would NOT have clustered these -- the dedup LLM call never saw them side by side
  - predicted [b2a66fe1] "Pre-configured Windows 11 Professional PC"
    - **similarity check:** closest true topic: `brand_name_no_substitutes` (cosine=0.45); vs matched predicted [285d3bea]: cosine=0.40 (< dedup threshold 0.6) -> dedup's cosine pre-filter would NOT have clustered these -- the dedup LLM call never saw them side by side
  - predicted [b6f5bfae] "Vertex Host software with unlimited Client and Media Importer licenses"
    - **similarity check:** closest true topic: `brand_name_no_substitutes` (cosine=0.57); vs matched predicted [285d3bea]: cosine=0.50 (< dedup threshold 0.6) -> dedup's cosine pre-filter would NOT have clustered these -- the dedup LLM call never saw them side by side
  - predicted [bdd60e18] "In special trade contractor contracts, no more than 75% of the amount paid by the government (excluding materials) may be paid to non-VIP-listed firms."
    - **similarity check:** closest true topic: `sdvosb_certification_required` (cosine=0.65); vs matched predicted [a91ebbd0]: cosine=0.76 (>= dedup threshold 0.6) -> would likely have been clustered together and compared by the dedup LLM call
  - predicted [c0d9ceb1] "Monitor"
    - **similarity check:** closest true topic: `price_and_discount_terms_stated` (cosine=0.51); vs matched predicted [8ba4dc86]: cosine=0.43 (< dedup threshold 0.6) -> dedup's cosine pre-filter would NOT have clustered these -- the dedup LLM call never saw them side by side
  - predicted [cdf7b04f] "Acquisition of one (1) Vertex 25ei Optical Media Package is required for the VA Central Western Massachusetts Healthcare System."
    - **similarity check:** closest true topic: `shipping_cost_handling` (cosine=0.61); vs matched predicted [e3832d29]: cosine=0.58 (< dedup threshold 0.6) -> dedup's cosine pre-filter would NOT have clustered these -- the dedup LLM call never saw them side by side
  - predicted [cf1bf81f] "Dimensions: 13.7”H x 14.8” W x 20.2” D"
    - **similarity check:** closest true topic: `price_and_discount_terms_stated` (cosine=0.49); vs matched predicted [8ba4dc86]: cosine=0.48 (< dedup threshold 0.6) -> dedup's cosine pre-filter would NOT have clustered these -- the dedup LLM call never saw them side by side
  - predicted [d7367a7f] "Dual Recorders and High-Resolution Inkjet Printer (Black and Color Cartridges)"
    - **similarity check:** closest true topic: `brand_name_no_substitutes` (cosine=0.48); vs matched predicted [285d3bea]: cosine=0.45 (< dedup threshold 0.6) -> dedup's cosine pre-filter would NOT have clustered these -- the dedup LLM call never saw them side by side
  - predicted [e413da39] "Keyboard"
    - **similarity check:** closest true topic: `price_and_discount_terms_stated` (cosine=0.47); vs matched predicted [8ba4dc86]: cosine=0.44 (< dedup threshold 0.6) -> dedup's cosine pre-filter would NOT have clustered these -- the dedup LLM call never saw them side by side
  - predicted [e445d079] "Limitations on subcontracting percentages apply based on contract type (supplies, services, or combined), excluding material costs and specific direct costs."
    - **similarity check:** closest true topic: `sdvosb_certification_required` (cosine=0.64); vs matched predicted [a91ebbd0]: cosine=0.75 (>= dedup threshold 0.6) -> would likely have been clustered together and compared by the dedup LLM call
  - predicted [eea40629] "Provide all required Sorna Vertex 25ei & CD Burner products in accordance with the Statement of Work."
    - **similarity check:** closest true topic: `brand_name_no_substitutes` (cosine=0.71); vs matched predicted [285d3bea]: cosine=0.75 (>= dedup threshold 0.6) -> would likely have been clustered together and compared by the dedup LLM call
  - predicted [f948901a] "All SDVOSB eligibility requirements must be met for quotes to be considered."
    - **similarity check:** closest true topic: `sdvosb_certification_required` (cosine=0.72); vs matched predicted [a91ebbd0]: cosine=0.71 (>= dedup threshold 0.6) -> would likely have been clustered together and compared by the dedup LLM call

## Coverage flags

Clean 1:1 matches (recall counted them as found) whose citations don't fully overlap in length, split by which side is off. Over-split/over-merge/tangled matches are excluded here -- their predicted fragments are inherently partial by construction, already shown in the recall breakdown above.

**Requirements captured with extra text** (0) — the predicted citation is padded beyond the true one:
- none

**Requirements captured incompletely** (0) — the predicted citation misses part of the true one:
- none

## is_mandatory accuracy

For each clean or one-to-many match (tangled groups excluded — there's no single "one" to compare against), does `is_mandatory` agree with the true value? A one-to-many group counts as correct only if every member on the "many" side agrees with the "one".

**Accuracy: 100.0% (10 groups)**

Mismatched:
- none

## is_text_verifiable accuracy

For each clean or one-to-many match (tangled groups excluded), does `is_text_verifiable` agree with the true value (all-or-nothing on the "many" side, same rule as is_mandatory above)? A wrong `false` here means the pipeline skips verdict generation for a requirement that should get one.

**Accuracy: 70.0% (10 groups)**

Mismatched:
- true: `sam_registration_required`=False; predicted: `b7ee07c0`=True — "Offeror must be registered in SAM."
- true: `sdvosb_certification_required`=False; predicted: `a91ebbd0`=True — "Offeror must be certified/verified as an SD/VOSB in the SBA SBS VIP (Veteran Information Pages) VetCert as an SD/VOSB."
- true: `los_compliance_assertion`=True, `los_requirements_met`=False; predicted: `ed7c5986`=True — "Compliance with the LOS clauses must be asserted by the offeror in the email accompanying their quote."

## Verdict accuracy

The confusion matrix covers only clean 1:1 matches — split/merge groups have no single pair to plot, but still count in the two rates below.

Clean matches scored: 6

| true \ pipeline said | `compliant` | `non_compliant` | `contradictory` | `insufficient_information` |
|---|---|---|---|---|
| `compliant` | 3 | 0 | 0 | 0 |
| `non_compliant` | 0 | 1 | 1 | 0 |
| `contradictory` | 0 | 0 | 0 | 0 |
| `insufficient_information` | 1 | 0 | 0 | 0 |

Why some rows are empty:
- `contradictory` row is empty: true `warranty_terms_stated` — over_merge match — no single pair to plot

**Mismatched clean matches** — every off-diagonal cell above, in full: the full context retrieved and shown to the model, what it chose to cite from that context, and its reasoning ("model's ..."), next to what `true_verdicts.json` expects ("expected ...").

- none

**False-compliant rate** — dangerous direction: the true verdict requires an issue (anything but `compliant`), but every predicted verdict in the group is `compliant`.
- rate: 14.3%

- group of 9 true topic(s) and 1 predicted requirement(s) (not a 1:1 match, so there is no single correct pairing between them):
  - true `amendment_acknowledgment` — "(9) Acknowledgment Request for Quotation amendments;" (acceptable: ['compliant'])
      - **expected evidence (true_verdicts.json):** "No amendments to this solicitation had been issued as of the date of this quote."
      - **expected reasoning:** Application explicitly states no amendments had been issued, addressing the requirement directly.
  - true `far_52_212_3_reps_and_certs` — "(8) A completed copy of the representations and certifications under the Federal Acquisition Regulation (FAR) 52.212-3 (see FAR 52.212-3(b) for those representations and certifications that the quoter shall complete electronically)." (acceptable: ['compliant'])
      - **expected evidence (true_verdicts.json):** "a completed copy of these representations is attached to this email as Exhibit A."
      - **expected reasoning:** Application states a completed copy of the FAR 52.212-3 representations and certifications is attached to the email as Exhibit A.
  - true `price_and_discount_terms_stated` — "(6) Price and any discount terms;" (acceptable: ['compliant'])
      - **expected evidence (true_verdicts.json):** "Net 30 days from invoice date. A 1% discount applies if paid within 10 days."
      - **expected reasoning:** Application states Net 30 payment terms and a 1% early-payment discount.
  - true `quoter_contact_info_stated` — "(3) The name, address, and telephone number of the quoter;" (acceptable: ['compliant'])
      - **expected evidence (true_verdicts.json):** "Coastal Imaging Solutions, Inc. 410 Harbor Commerce Way New Bedford, MA 02740 Telephone: (508) 555-0193"
      - **expected reasoning:** Name, address, and telephone number are all provided.
  - true `remit_to_address_stated` — "(7) "Remit to" address, if different from the mailing address;" (acceptable: ['compliant'])
      - **expected evidence (true_verdicts.json):** "900 Financial Plaza, Suite 4, Providence, RI 02903"
      - **expected reasoning:** Application provides an explicit remit-to address different from the mailing address.
  - true `solicitation_number_stated` — "(1) The solicitation number;" (acceptable: ['compliant'])
      - **expected evidence (true_verdicts.json):** "Subject: Quote for Solicitation 36C24126Q0731 P0003 - Sorna Vertex 25ei Platform/CD Burner"
      - **expected reasoning:** Solicitation number is stated in the subject line.
  - true `technical_description_stated` — "(4) A technical description of the items being quoted in sufficient detail to evaluate compliance with the requirements in the solicitation. This may include product literature, or other documents, if necessary." (acceptable: ['compliant'])
      - **expected evidence (true_verdicts.json):** "Technical description of items quoted: We are quoting the Sorna Vertex 25ei Platform with integrated Sorna CD Burner, matching the brand and model specified in the Product Chart"
      - **expected reasoning:** Application describes the quoted platform, software, and configuration in sufficient detail.
  - true `time_specified_for_receipt_stated` — "(2) The time specified in the solicitation for receipt of quotations;" (acceptable: ['compliant'])
      - **expected evidence (true_verdicts.json):** "We acknowledge the time specified in the solicitation for receipt of quotations as 11:00 AM EDT on 09/18/26."
      - **expected reasoning:** Application explicitly states the 11:00 AM EDT on 09/18/26 receipt time.
  - true `warranty_terms_stated` — "(5) Terms of any express warranty;" (acceptable: ['contradictory'])
      - **expected evidence (true_verdicts.json):** "carries the manufacturer's 3-year parts-and-labor warranty."
      - **expected evidence (true_verdicts.json):** "coverage is limited to a 2-year parts-and-labor warranty per the manufacturer's component schedule."
      - **expected reasoning:** Application states the base configuration carries a 3-year warranty, but then states the burner drive specifically carries only a 2-year warranty under the manufacturer's schedule -- the two stated warranty durations for the same overall system conflict without reconciling which governs.
  - **retrieved context (shown to the model):** "From: sales@coastalimagingsolutions.com To: carlos.ortiz3@va.gov Subject: Quote for Solicitation 36C24126Q0731 P0003 - Sorna Vertex 25ei Platform/CD Burner Dear Mr. Ortiz, Coastal Imaging Solutions, Inc. submits the following quote in response to Solicitation 36C24126Q0731 P0003. [...truncated]"
  - **retrieved context (shown to the model):** "Price and discount terms: Net 30 days from invoice date. A 1% discount applies if paid within 10 days. "Remit to" address: 900 Financial Plaza, Suite 4, Providence, RI 02903 (different from the mailing address above). Representations and Certifications under FAR 52.212-3: Coastal [...truncated]"
  - **retrieved context (shown to the model):** "For the disc-burner component specifically, we propose to substitute a compatible high-speed burner drive from an alternate manufacturer, which meets or exceeds the write-speed and reliability specifications of the drive bundled with the named brand-name unit. This quote presents [...truncated]"
  - predicted verdicts in this group:
    - predicted [8ba4dc86] "Quotes must include minimum required information such as solicitation number, receipt time, quoter details, technical description, warranty, price, remit-to address, FAR representations and certifications, amendment acknowledgments, and terms agreement statement." — verdict: compliant
      - **model's evidence (what it chose to cite):** "Coastal Imaging Solutions, Inc. submits the following quote in response to Solicitation 36C24126Q0731 P0003. We acknowledge the time specified in the solicitation for receipt of quotations as 11:00 AM EDT on 09/18/26. Quoter name, address, and telephone number: Coastal Imaging Solutions, Inc. 410 Harbor Commerce Way New Bedford, MA 02740 Telephone: (508) 555-0193. No amendments to this solicitation had been issued as of the date of this quote. Technical description of items quoted: We are quoting the Sorna Vertex 25ei Platform with integrated Sorna CD Burner... Terms of express warranty: The base configuration above is our standard offering and carries the manufacturer's 3-year parts-and-labor warranty."
      - **model's evidence (what it chose to cite):** ""Remit to" address: 900 Financial Plaza, Suite 4, Providence, RI 02903 (different from the mailing address above). Representations and Certifications under FAR 52.212-3: Coastal Imaging Solutions, Inc. represents that it is a small business concern... Terms and conditions: The terms and conditions in the solicitation are acceptable to be included in the award document without modification, deletion, or addition. Total quoted price for this solicitation: $23,410.00."
      - **model's reasoning:** The bidder's application includes all the required minimum information items: solicitation number (36C24126Q0731 P0003), receipt time acknowledgment, quoter details (name, address, telephone), technical description, warranty terms, price ($23,410.00), remit-to address, FAR representations and certifications, amendment acknowledgments (stating none issued), and a terms agreement statement.

**False-issue rate** — mirror direction: the true verdict is `compliant` only, but the pipeline raised an issue anyway.
- rate: 0.0%

- none

**Unscored** — split/merge groups excluded from the matrix above (still counted in the two rates above):
- group 1:
  - true `amendment_acknowledgment` — "(9) Acknowledgment Request for Quotation amendments;" (acceptable: ['compliant'])
  - true `far_52_212_3_reps_and_certs` — "(8) A completed copy of the representations and certifications under the Federal Acquisition Regulation (FAR) 52.212-3 (see FAR 52.212-3(b) for those representations and certifications that the quoter shall complete electronically)." (acceptable: ['compliant'])
  - true `price_and_discount_terms_stated` — "(6) Price and any discount terms;" (acceptable: ['compliant'])
  - true `quoter_contact_info_stated` — "(3) The name, address, and telephone number of the quoter;" (acceptable: ['compliant'])
  - true `remit_to_address_stated` — "(7) "Remit to" address, if different from the mailing address;" (acceptable: ['compliant'])
  - true `solicitation_number_stated` — "(1) The solicitation number;" (acceptable: ['compliant'])
  - true `technical_description_stated` — "(4) A technical description of the items being quoted in sufficient detail to evaluate compliance with the requirements in the solicitation. This may include product literature, or other documents, if necessary." (acceptable: ['compliant'])
  - true `time_specified_for_receipt_stated` — "(2) The time specified in the solicitation for receipt of quotations;" (acceptable: ['compliant'])
  - true `warranty_terms_stated` — "(5) Terms of any express warranty;" (acceptable: ['contradictory'])
  - predicted [8ba4dc86] "Quotes must include minimum required information such as solicitation number, receipt time, quoter details, technical description, warranty, price, remit-to address, FAR representations and certifications, amendment acknowledgments, and terms agreement statement." — verdict: compliant

## Evidence

**Citation-verified rate** (evidence-level): fraction of evidence quotes actually located in application.txt.
- rate: 94.3% (2 unverified of 35)

**Evidence recall**: does the expected evidence span (from `true_verdicts.json`) show up somewhere in the requirement's retrieved chunks, before the verdict step chose what to cite? Topics never extracted as a requirement are excluded — that failure is already counted by requirement recall above.
- recall: 100.0% (16/16)
- missed:
  - none
