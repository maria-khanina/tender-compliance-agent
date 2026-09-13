# Evaluation report

## Summary metrics

Machine-readable numbers for averaging across tenders -- every value here is explained in the sections below. `null` means the metric doesn't apply to this run (e.g. no verdict-only artifact present).

```json
{
  "requirement_recall": 0.913,
  "requirement_recall_matched": 21,
  "requirement_recall_total": 23,
  "requirement_precision": 0.3125,
  "citation_verified_rate": 0.9688,
  "is_mandatory_accuracy": 0.875,
  "is_mandatory_scored": 8,
  "is_text_verifiable_accuracy": 0.75,
  "is_text_verifiable_scored": 8,
  "verdict_clean_match_count": 4,
  "verdict_accuracy": 0.5,
  "false_compliant_rate": 0.5,
  "false_issue_rate": 0.1667,
  "evidence_citation_verified_rate": 1.0,
  "evidence_recall": 1.0,
  "verdict_only_accuracy": 0.9444,
  "verdict_only_scored": 18
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

**Over-merge** (3) — one predicted requirement covering several distinct true topics:
- predicted [ca60cd14] "Offeror must meet Limitations on Subcontracting (LOS) requirements and comply with applicable VAAR subpart 819.70 and SBA regulations." — verdict: compliant, citation: UNVERIFIED — not located in tender.txt lumps together 3 true requirements:
  - true `los_compliance_assertion` — "Compliance with the LOS clauses must be asserted by the offeror in the email accompanying their quote."
  - true `los_requirements_met` — "Offeror must meet LOS (Limitations on Subcontracting) requirements and per the LOS listed clauses below."
  - true `sdvosb_certification_required` — "Offeror must be certified/verified as an SD/VOSB in the SBA SBS VIP (Veteran Information Pages) VetCert as an SD/VOSB."
- predicted [7f38e8d7] "The quoter must enter its Unique Entity Identifier and Electronic Funds Transfer indicator on the cover page of its quote." — verdict: non_compliant lumps together 2 true requirements:
  - true `eft_indicator_if_applicable` — "The quoter also must enter its Electronic Funds Transfer (EFT) indicator, if applicable."
  - true `uei_provided_on_quote` — "The quoter must enter, in the block with its name and address on the cover page of its quote, the annotation "Unique Entity Identifier" followed by the unique entity identifier that identifies the quoter's name and address."
- predicted [ed8fd964] "Quotes must show minimum required information including solicitation number, time specified for receipt, quoter contact details, technical description, warranty terms, price/discount terms, remit-to address, FAR representations/certifications, amendment acknowledgments, and statement of agreement with terms." — verdict: compliant lumps together 9 true requirements:
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
  - predicted [66da7d69] "Submit signed and dated quotes on letterhead or as specified in the RFQ at or before the exact time specified (no later than 11:00 AM EDT 09/18/26)." — verdict: non_compliant
  - predicted [ed36c45d] "Quotes must be submitted via email to the designated Government point of contact." — verdict: compliant

## Requirement precision

**Citation-verified rate** (hallucination check): fraction of predicted requirements whose citation was actually located in tender.txt (exactly or via fuzzy match).
- rate: 96.9%
- unverified:
  - predicted [ca60cd14] "Offeror must meet Limitations on Subcontracting (LOS) requirements and comply with applicable VAAR subpart 819.70 and SBA regulations." — verdict: compliant, citation: UNVERIFIED — not located in tender.txt

**Classification precision**: fraction of predicted requirements that matched a true requirement.
- rate: 31.2%
- unexplained (22) — the model recognized these as requirements, but they don't match any true requirement. "closest true topic" is a mechanical (no-LLM) embedding-similarity lookup against every true topic's description; "dedup visibility" checks whether dedup's own cosine pre-filter would have clustered this candidate with whatever predicted requirement DID match that topic -- i.e. whether the dedup LLM call ever had a chance to compare them:
  - predicted [14dced61] "Offeror must have the capability to provide all required Sorna Vertex 25ei & CD Burner products in accordance with the Statement of Work."
    - **similarity check:** closest true topic: `brand_name_no_substitutes` (cosine=0.71); vs matched predicted [919227ba]: cosine=0.75 (>= dedup threshold 0.6) -> would likely have been clustered together and compared by the dedup LLM call
  - predicted [1d4aafed] "Any award resulting from this solicitation shall be made only to a VIP-listed VOSB who is eligible at the time of submission of offer(s) and at time of award."
    - **similarity check:** closest true topic: `sdvosb_certification_required` (cosine=0.69); vs matched predicted [ca60cd14]: cosine=0.70 (>= dedup threshold 0.6) -> would likely have been clustered together and compared by the dedup LLM call
  - predicted [243f022c] "An otherwise eligible firm further agrees to comply with the required certification requirements in this solicitation."
    - **similarity check:** closest true topic: `los_compliance_assertion` (cosine=0.67); vs matched predicted [ca60cd14]: cosine=0.62 (>= dedup threshold 0.6) -> would likely have been clustered together and compared by the dedup LLM call
  - predicted [262f2564] "A joint venture may be considered eligible if listed in VIP and complying with 13 CFR 125.18(b) requirements."
    - **similarity check:** closest true topic: `sdvosb_certification_required` (cosine=0.74); vs matched predicted [ca60cd14]: cosine=0.80 (>= dedup threshold 0.6) -> would likely have been clustered together and compared by the dedup LLM call
  - predicted [2d3f1646] "For special trade contractors, no more than 75% of the amount paid by the government, excluding materials, may be paid to non-VIP-listed firms."
    - **similarity check:** closest true topic: `sdvosb_certification_required` (cosine=0.65); vs matched predicted [ca60cd14]: cosine=0.78 (>= dedup threshold 0.6) -> would likely have been clustered together and compared by the dedup LLM call
  - predicted [42fa3aa5] "Offers received from entities that are not VIP-listed at the time of offer shall not be considered."
    - **similarity check:** closest true topic: `uei_must_be_preexisting` (cosine=0.61); that true topic has no matched predicted requirement in this run, so there was nothing for dedup to compare it against
  - predicted [46be373e] "For service contracts, the SDVOSB prime contractor will not pay more than 50% of the amount paid by the government for contract performance to non-VIP-listed SDVOSBs, excluding direct costs."
    - **similarity check:** closest true topic: `sdvosb_certification_required` (cosine=0.62); vs matched predicted [ca60cd14]: cosine=0.78 (>= dedup threshold 0.6) -> would likely have been clustered together and compared by the dedup LLM call
  - predicted [6060b8c6] "The business has been verified for ownership and control and is listed in VA's Vendor Information Pages (VIP) database."
    - **similarity check:** closest true topic: `sdvosb_certification_required` (cosine=0.73); vs matched predicted [ca60cd14]: cosine=0.66 (>= dedup threshold 0.6) -> would likely have been clustered together and compared by the dedup LLM call
  - predicted [844687e9] "By submitting an offer, the prospective contractor represents that it is an eligible VOSB as defined in the clause."
    - **similarity check:** closest true topic: `sdvosb_certification_required` (cosine=0.64); vs matched predicted [ca60cd14]: cosine=0.69 (>= dedup threshold 0.6) -> would likely have been clustered together and compared by the dedup LLM call
  - predicted [895b0a90] "For supply or product contracts, the prime contractor will not pay more than 50% of the amount paid by the government, excluding the cost of materials, to firms that are not VIP-listed."
    - **similarity check:** closest true topic: `sdvosb_certification_required` (cosine=0.66); vs matched predicted [ca60cd14]: cosine=0.80 (>= dedup threshold 0.6) -> would likely have been clustered together and compared by the dedup LLM call
  - predicted [9e46f897] "A joint venture agrees that, in the performance of the contract, the applicable percentage specified in paragraph (d) of this clause will be performed by the aggregate of the joint venture participants."
    - **similarity check:** closest true topic: `los_compliance_assertion` (cosine=0.55); vs matched predicted [ca60cd14]: cosine=0.59 (< dedup threshold 0.6) -> dedup's cosine pre-filter would NOT have clustered these -- the dedup LLM call never saw them side by side
  - predicted [a5bd20af] "The term small business concern owned and controlled by Veterans has its standard meaning, except the firm must be listed in the VIP database."
    - **similarity check:** closest true topic: `sdvosb_certification_required` (cosine=0.62); vs matched predicted [ca60cd14]: cosine=0.65 (>= dedup threshold 0.6) -> would likely have been clustered together and compared by the dedup LLM call
  - predicted [adab89dc] "Any questions or concerns regarding this solicitation must be forwarded in writing via e-mail to the Point of Contact."
    - **similarity check:** closest true topic: `solicitation_number_stated` (cosine=0.67); vs matched predicted [ed8fd964]: cosine=0.66 (>= dedup threshold 0.6) -> would likely have been clustered together and compared by the dedup LLM call
  - predicted [b10785da] "The requirements apply to any contract, order, or subcontract where the firm receives a benefit or preference from its VOSB designation."
    - **similarity check:** closest true topic: `los_requirements_met` (cosine=0.62); vs matched predicted [ca60cd14]: cosine=0.71 (>= dedup threshold 0.6) -> would likely have been clustered together and compared by the dedup LLM call
  - predicted [b16b2c7b] "MOD P00003 replaces the initial Combined Synopsis and all subsequent amendments/modifications."
    - **similarity check:** closest true topic: `amendment_acknowledgment` (cosine=0.52); vs matched predicted [ed8fd964]: cosine=0.46 (< dedup threshold 0.6) -> dedup's cosine pre-filter would NOT have clustered these -- the dedup LLM call never saw them side by side
  - predicted [b579695d] "For contracts for supplies from a non-manufacturer, the prime contractor will supply the product of a domestic small business manufacturer or processor unless a waiver is granted."
    - **similarity check:** closest true topic: `sdvosb_certification_required` (cosine=0.65); vs matched predicted [ca60cd14]: cosine=0.78 (>= dedup threshold 0.6) -> would likely have been clustered together and compared by the dedup LLM call
  - predicted [bd2fdfbd] "MOD P0003 extends the RFQ due date to 09/18/26 at 11:00 AM EDT."
    - **similarity check:** closest true topic: `submission_deadline_and_channel` (cosine=0.66); vs matched predicted [66da7d69]: cosine=0.61 (>= dedup threshold 0.6) -> would likely have been clustered together and compared by the dedup LLM call
  - predicted [ccc013a8] "The business will comply with VAAR subpart 819.70 and SBA regulations regarding small business size and government contracting programs."
    - **similarity check:** closest true topic: `sdvosb_certification_required` (cosine=0.78); vs matched predicted [ca60cd14]: cosine=0.84 (>= dedup threshold 0.6) -> would likely have been clustered together and compared by the dedup LLM call
  - predicted [da216ab2] "The quoter agrees to hold the prices in its quote firm for 30 calendar days from the date specified for receipt of quotes."
    - **similarity check:** closest true topic: `time_specified_for_receipt_stated` (cosine=0.71); vs matched predicted [ed8fd964]: cosine=0.64 (>= dedup threshold 0.6) -> would likely have been clustered together and compared by the dedup LLM call
  - predicted [dcc3599a] "For general construction contracts, the prime contractor will not pay more than 85% of the amount paid by the government, excluding materials, to non-VIP-listed firms."
    - **similarity check:** closest true topic: `sdvosb_certification_required` (cosine=0.65); vs matched predicted [ca60cd14]: cosine=0.78 (>= dedup threshold 0.6) -> would likely have been clustered together and compared by the dedup LLM call
  - predicted [ddcc79c7] "All SD/VOSB eligibility requirements must be met, and the firm must be listed in the VIP database at the time of offer and award."
    - **similarity check:** closest true topic: `sdvosb_certification_required` (cosine=0.79); vs matched predicted [ca60cd14]: cosine=0.85 (>= dedup threshold 0.6) -> would likely have been clustered together and compared by the dedup LLM call
  - predicted [fe089efb] "When a contract includes both supply and services, the 50 percent limitation shall apply only to the supply portion of the contract."
    - **similarity check:** closest true topic: `los_requirements_met` (cosine=0.61); vs matched predicted [ca60cd14]: cosine=0.66 (>= dedup threshold 0.6) -> would likely have been clustered together and compared by the dedup LLM call

## Coverage flags

Clean 1:1 matches (recall counted them as found) whose citations don't fully overlap in length, split by which side is off. Over-split/over-merge/tangled matches are excluded here -- their predicted fragments are inherently partial by construction, already shown in the recall breakdown above.

**Requirements captured with extra text** (0) — the predicted citation is padded beyond the true one:
- none

**Requirements captured incompletely** (0) — the predicted citation misses part of the true one:
- none

## is_mandatory accuracy

For each clean or one-to-many match (tangled groups excluded — there's no single "one" to compare against), does `is_mandatory` agree with the true value? A one-to-many group counts as correct only if every member on the "many" side agrees with the "one".

**Accuracy: 87.5% (8 groups)**

Mismatched:
- true: `eft_indicator_if_applicable`=False, `uei_provided_on_quote`=True; predicted: `7f38e8d7`=True — "The quoter also must enter its Electronic Funds Transfer (EFT) indicator, if applicable."

## is_text_verifiable accuracy

For each clean or one-to-many match (tangled groups excluded), does `is_text_verifiable` agree with the true value (all-or-nothing on the "many" side, same rule as is_mandatory above)? A wrong `false` here means the pipeline skips verdict generation for a requirement that should get one.

**Accuracy: 75.0% (8 groups)**

Mismatched:
- true: `sam_registration_required`=False; predicted: `6b78b8b5`=True — "Offeror must be registered in SAM."
- true: `los_compliance_assertion`=True, `los_requirements_met`=False, `sdvosb_certification_required`=False; predicted: `ca60cd14`=True — "Compliance with the LOS clauses must be asserted by the offeror in the email accompanying their quote."

## Verdict accuracy

The confusion matrix covers only clean 1:1 matches — split/merge groups have no single pair to plot, but still count in the two rates below.

Clean matches scored: 4

| true \ pipeline said | `compliant` | `non_compliant` | `contradictory` | `insufficient_information` |
|---|---|---|---|---|
| `compliant` | 2 | 0 | 0 | 0 |
| `non_compliant` | 1 | 0 | 0 | 0 |
| `contradictory` | 1 | 0 | 0 | 0 |
| `insufficient_information` | 0 | 0 | 0 | 0 |

**Mismatched clean matches** — every off-diagonal cell above, in full: the full context retrieved and shown to the model, what it chose to cite from that context, and its reasoning ("model's ..."), next to what `true_verdicts.json` expects ("expected ...").

- `product_chart_full_pricing` — acceptable: ['contradictory', 'non_compliant'], predicted: compliant
  - **requirement:** "Pricing shall be entered for each line item as listed in the Product Chart."
  - **retrieved context (shown to the model):** "Terms and conditions: The terms and conditions in the solicitation are acceptable to be included in the award document without modification, deletion, or addition. Total quoted price for this solicitation: $21,540.00. Product Chart pricing: Item 951-707100, Vertex 25ei Platform w [...truncated]"
  - **retrieved context (shown to the model):** "We acknowledge receipt of Amendment/Modification P0003 dated 08/25/26, which extended the response date for this RFQ to 09/18/26 at 11:00 AM EDT and replaced the prior Combined Synopsis and all earlier amendments/modifications. Technical description of items quoted: We are quotin [...truncated]"
  - **retrieved context (shown to the model):** "From: quotes@meridianmedsystems.com To: carlos.ortiz3@va.gov Subject: Quote for Solicitation 36C24126Q0731 P0003 - Sorna Vertex 25ei Platform/CD Burner Dear Mr. Ortiz, Meridian Medical Systems, LLC is pleased to submit the following quote in response to Solicitation 36C24126Q0731 [...truncated]"
  - **model's evidence (what it chose to cite):** "Product Chart pricing: Item 951-707100, Vertex 25ei Platform w/ Sorna CD Burner, Qty 1, Unit Price $19,200.00, Total $19,200.00. Item 501-862406, Installation & Training Support, Qty 1, Unit Price $1,650.00, Total $1,650.00. UPS 1KVA - Tower, Qty 1, Unit Price $540.00, Total $540.00. Training Manuals, Qty 2, Unit Price $75.00, Total $150.00. Delivery, Qty 1, Unit Price $1,400.00, Total $1,400.00. Grand total of the line items above: $22,940.00."
  - **model's reasoning:** The bidder provided specific line-item pricing (unit prices and totals) for each of the items listed in the Product Chart, fully satisfying the requirement.
  - **expected evidence (true_verdicts.json):** "Total quoted price for this solicitation: $21,540.00."
  - **expected evidence (true_verdicts.json):** "Product Chart pricing: Item 951-707100, Vertex 25ei Platform w/ Sorna CD Burner, Qty 1, Unit Price $19,200.00, Total $19,200.00. Item 501-862406, Installation & Training Support, Qty 1, Unit Price $1,650.00, Total $1,650.00. UPS 1KVA - Tower, Qty 1, Unit Price $540.00, Total $540.00. Training Manuals, Qty 2, Unit Price $75.00, Total $150.00. Delivery, Qty 1, Unit Price $1,400.00, Total $1,400.00. Grand total of the line items above: $22,940.00."
  - **expected reasoning:** All five Product Chart line items are priced, but the quote states two different grand totals for the same quote: $21,540.00 up front and $22,940.00 from the itemized breakdown -- a direct numeric contradiction. non_compliant is also acceptable if a pipeline flags the mismatched total as a completeness/accuracy failure instead of naming it a contradiction.

- `shipping_cost_handling` — acceptable: ['non_compliant'], predicted: compliant
  - **requirement:** "Delivery or shipping costs must fall below $250.00; otherwise, the cost must be rolled into the line-item price for the Vertex 25ei/CD Burner."
  - **retrieved context (shown to the model):** "Terms and conditions: The terms and conditions in the solicitation are acceptable to be included in the award document without modification, deletion, or addition. Total quoted price for this solicitation: $21,540.00. Product Chart pricing: Item 951-707100, Vertex 25ei Platform w [...truncated]"
  - **retrieved context (shown to the model):** "We acknowledge receipt of Amendment/Modification P0003 dated 08/25/26, which extended the response date for this RFQ to 09/18/26 at 11:00 AM EDT and replaced the prior Combined Synopsis and all earlier amendments/modifications. Technical description of items quoted: We are quotin [...truncated]"
  - **retrieved context (shown to the model):** "From: quotes@meridianmedsystems.com To: carlos.ortiz3@va.gov Subject: Quote for Solicitation 36C24126Q0731 P0003 - Sorna Vertex 25ei Platform/CD Burner Dear Mr. Ortiz, Meridian Medical Systems, LLC is pleased to submit the following quote in response to Solicitation 36C24126Q0731 [...truncated]"
  - **model's evidence (what it chose to cite):** "Shipping for this order is $150.00 and will be invoiced as a separate line item on the purchase order, not included in the Vertex 25ei/CD Burner unit price above."
  - **model's reasoning:** The requirement states that delivery or shipping costs must fall below $250.00, or else be rolled into the line-item price for the Vertex 25ei/CD Burner. The bidder's quote explicitly states that shipping is $150.00, which is below the $250.00 threshold, thus satisfying the requirement.
  - **expected evidence (true_verdicts.json):** "Shipping for this order is $150.00 and will be invoiced as a separate line item on the purchase order, not included in the Vertex 25ei/CD Burner unit price above."
  - **expected reasoning:** Shipping is $150.00 (under the $250.00 threshold) but is billed as a separate line item instead of being rolled into the unit price, contradicting the requirement.

**False-compliant rate** — dangerous direction: the true verdict requires an issue (anything but `compliant`), but every predicted verdict in the group is `compliant`.
- rate: 50.0%

- group of 9 true topic(s) and 1 predicted requirement(s) (not a 1:1 match, so there is no single correct pairing between them):
  - true `amendment_acknowledgment` — "(9) Acknowledgment Request for Quotation amendments;" (acceptable: ['compliant'])
      - **expected evidence (true_verdicts.json):** "We acknowledge receipt of Amendment/Modification P0003 dated 08/25/26, which extended the response date for this RFQ to 09/18/26 at 11:00 AM EDT and replaced the prior Combined Synopsis and all earlier amendments/modifications."
      - **expected reasoning:** Application explicitly acknowledges receipt of Amendment P0003.
  - true `far_52_212_3_reps_and_certs` — "(8) A completed copy of the representations and certifications under the Federal Acquisition Regulation (FAR) 52.212-3 (see FAR 52.212-3(b) for those representations and certifications that the quoter shall complete electronically)." (acceptable: ['non_compliant'])
      - **expected evidence (true_verdicts.json):** "Our representations and certifications under FAR 52.212-3 are on file in SAM.gov and available upon request; we have not attached a completed copy to this email."
      - **expected reasoning:** Application explicitly states the FAR 52.212-3 representations and certifications are not attached, only available on request.
  - true `price_and_discount_terms_stated` — "(6) Price and any discount terms;" (acceptable: ['compliant'])
      - **expected evidence (true_verdicts.json):** "Price and discount terms: Net 30 days from invoice date. No prompt-payment discount is offered."
      - **expected reasoning:** Price and discount terms are stated.
  - true `quoter_contact_info_stated` — "(3) The name, address, and telephone number of the quoter;" (acceptable: ['compliant'])
      - **expected evidence (true_verdicts.json):** "Quoter name, address, and telephone number: Meridian Medical Systems, LLC 88 Harborview Drive, Suite 210 Providence, RI 02903 Telephone: (401) 555-0142"
      - **expected reasoning:** Quoter name, address, and phone number are stated.
  - true `remit_to_address_stated` — "(7) "Remit to" address, if different from the mailing address;" (acceptable: ['compliant'])
      - **expected evidence (true_verdicts.json):** ""Remit to" address: Same as the mailing address listed above."
      - **expected reasoning:** A remit-to address is stated.
  - true `solicitation_number_stated` — "(1) The solicitation number;" (acceptable: ['compliant'])
      - **expected evidence (true_verdicts.json):** "response to Solicitation 36C24126Q0731 P0003."
      - **expected reasoning:** Solicitation number is stated.
  - true `technical_description_stated` — "(4) A technical description of the items being quoted in sufficient detail to evaluate compliance with the requirements in the solicitation. This may include product literature, or other documents, if necessary." (acceptable: ['compliant'])
      - **expected evidence (true_verdicts.json):** "Technical description of items quoted: We are quoting the Sorna Vertex 25ei Platform with integrated Sorna CD Burner, brand name, exactly as specified in the Product Chart. This is the identical brand-name system required by the solicitation; Meridian is not offering a substitute or equivalent product. The package includes the Vertex Host software with unlimited Client and Media Importer licenses, automated DICOM profiles, a pre-configured Windows 11 Professional PC, monitor, keyboard, mouse, disc label design software, and all necessary cabling, matching the Statement of Work in full."
      - **expected reasoning:** A technical description of the quoted items is provided.
  - true `time_specified_for_receipt_stated` — "(2) The time specified in the solicitation for receipt of quotations;" (acceptable: ['compliant'])
      - **expected evidence (true_verdicts.json):** "We acknowledge the time specified in the solicitation for receipt of quotations as 11:00 AM EDT on 09/18/26, and our quote is submitted ahead of that deadline."
      - **expected reasoning:** Time specified for receipt is stated.
  - true `warranty_terms_stated` — "(5) Terms of any express warranty;" (acceptable: ['compliant'])
      - **expected evidence (true_verdicts.json):** "Terms of express warranty: The system is covered by the manufacturer's standard 3-year parts-and-labor warranty from the date of installation."
      - **expected reasoning:** Warranty terms are stated.
  - **retrieved context (shown to the model):** "We acknowledge receipt of Amendment/Modification P0003 dated 08/25/26, which extended the response date for this RFQ to 09/18/26 at 11:00 AM EDT and replaced the prior Combined Synopsis and all earlier amendments/modifications. Technical description of items quoted: We are quotin [...truncated]"
  - **retrieved context (shown to the model):** "Terms and conditions: The terms and conditions in the solicitation are acceptable to be included in the award document without modification, deletion, or addition. Total quoted price for this solicitation: $21,540.00. Product Chart pricing: Item 951-707100, Vertex 25ei Platform w [...truncated]"
  - **retrieved context (shown to the model):** "From: quotes@meridianmedsystems.com To: carlos.ortiz3@va.gov Subject: Quote for Solicitation 36C24126Q0731 P0003 - Sorna Vertex 25ei Platform/CD Burner Dear Mr. Ortiz, Meridian Medical Systems, LLC is pleased to submit the following quote in response to Solicitation 36C24126Q0731 [...truncated]"
  - predicted verdicts in this group:
    - predicted [ed8fd964] "Quotes must show minimum required information including solicitation number, time specified for receipt, quoter contact details, technical description, warranty terms, price/discount terms, remit-to address, FAR representations/certifications, amendment acknowledgments, and statement of agreement with terms." — verdict: compliant
      - **model's evidence (what it chose to cite):** "Quote for Solicitation 36C24126Q0731 P0003"
      - **model's evidence (what it chose to cite):** "We acknowledge the time specified in the solicitation for receipt of quotations as 11:00 AM EDT on 09/18/26"
      - **model's evidence (what it chose to cite):** "Quoter name, address, and telephone number: Meridian Medical Systems, LLC 88 Harborview Drive, Suite 210 Providence, RI 02903 Telephone: (401) 555-0142"
      - **model's evidence (what it chose to cite):** "Technical description of items quoted: We are quoting the Sorna Vertex 25ei Platform with integrated Sorna CD Burner,"
      - **model's evidence (what it chose to cite):** "Terms of express warranty: The system is covered by the manufacturer's standard 3-year parts-and-labor warranty from the date of installation."
      - **model's evidence (what it chose to cite):** "Price and discount terms: Net 30 days from invoice date. No prompt-payment discount is offered."
      - **model's evidence (what it chose to cite):** ""Remit to" address: Same as the mailing address listed above."
      - **model's evidence (what it chose to cite):** "Our representations and certifications under FAR 52.212-3 are on file in SAM.gov and available upon request"
      - **model's evidence (what it chose to cite):** "We acknowledge receipt of Amendment/Modification P0003 dated 08/25/26"
      - **model's evidence (what it chose to cite):** "Terms and conditions: The terms and conditions in the solicitation are acceptable to be included in the award document without modification, deletion, or addition."
      - **model's reasoning:** The bidder's application explicitly includes all required information: solicitation number, time specified for receipt, quoter contact details, technical description, warranty terms, price/discount terms, remit-to address, FAR representations/certifications, amendment acknowledgments, and a statement of agreement with the terms and conditions.

- `product_chart_full_pricing` — acceptable: ['contradictory', 'non_compliant'], predicted: compliant
  - **requirement:** "Pricing shall be entered for each line item as listed in the Product Chart."
  - **retrieved context (shown to the model):** "Terms and conditions: The terms and conditions in the solicitation are acceptable to be included in the award document without modification, deletion, or addition. Total quoted price for this solicitation: $21,540.00. Product Chart pricing: Item 951-707100, Vertex 25ei Platform w [...truncated]"
  - **retrieved context (shown to the model):** "We acknowledge receipt of Amendment/Modification P0003 dated 08/25/26, which extended the response date for this RFQ to 09/18/26 at 11:00 AM EDT and replaced the prior Combined Synopsis and all earlier amendments/modifications. Technical description of items quoted: We are quotin [...truncated]"
  - **retrieved context (shown to the model):** "From: quotes@meridianmedsystems.com To: carlos.ortiz3@va.gov Subject: Quote for Solicitation 36C24126Q0731 P0003 - Sorna Vertex 25ei Platform/CD Burner Dear Mr. Ortiz, Meridian Medical Systems, LLC is pleased to submit the following quote in response to Solicitation 36C24126Q0731 [...truncated]"
  - **model's evidence (what it chose to cite):** "Product Chart pricing: Item 951-707100, Vertex 25ei Platform w/ Sorna CD Burner, Qty 1, Unit Price $19,200.00, Total $19,200.00. Item 501-862406, Installation & Training Support, Qty 1, Unit Price $1,650.00, Total $1,650.00. UPS 1KVA - Tower, Qty 1, Unit Price $540.00, Total $540.00. Training Manuals, Qty 2, Unit Price $75.00, Total $150.00. Delivery, Qty 1, Unit Price $1,400.00, Total $1,400.00. Grand total of the line items above: $22,940.00."
  - **model's reasoning:** The bidder provided specific line-item pricing (unit prices and totals) for each of the items listed in the Product Chart, fully satisfying the requirement.
  - **expected evidence (true_verdicts.json):** "Total quoted price for this solicitation: $21,540.00."
  - **expected evidence (true_verdicts.json):** "Product Chart pricing: Item 951-707100, Vertex 25ei Platform w/ Sorna CD Burner, Qty 1, Unit Price $19,200.00, Total $19,200.00. Item 501-862406, Installation & Training Support, Qty 1, Unit Price $1,650.00, Total $1,650.00. UPS 1KVA - Tower, Qty 1, Unit Price $540.00, Total $540.00. Training Manuals, Qty 2, Unit Price $75.00, Total $150.00. Delivery, Qty 1, Unit Price $1,400.00, Total $1,400.00. Grand total of the line items above: $22,940.00."
  - **expected reasoning:** All five Product Chart line items are priced, but the quote states two different grand totals for the same quote: $21,540.00 up front and $22,940.00 from the itemized breakdown -- a direct numeric contradiction. non_compliant is also acceptable if a pipeline flags the mismatched total as a completeness/accuracy failure instead of naming it a contradiction.

- `shipping_cost_handling` — acceptable: ['non_compliant'], predicted: compliant
  - **requirement:** "Delivery or shipping costs must fall below $250.00; otherwise, the cost must be rolled into the line-item price for the Vertex 25ei/CD Burner."
  - **retrieved context (shown to the model):** "Terms and conditions: The terms and conditions in the solicitation are acceptable to be included in the award document without modification, deletion, or addition. Total quoted price for this solicitation: $21,540.00. Product Chart pricing: Item 951-707100, Vertex 25ei Platform w [...truncated]"
  - **retrieved context (shown to the model):** "We acknowledge receipt of Amendment/Modification P0003 dated 08/25/26, which extended the response date for this RFQ to 09/18/26 at 11:00 AM EDT and replaced the prior Combined Synopsis and all earlier amendments/modifications. Technical description of items quoted: We are quotin [...truncated]"
  - **retrieved context (shown to the model):** "From: quotes@meridianmedsystems.com To: carlos.ortiz3@va.gov Subject: Quote for Solicitation 36C24126Q0731 P0003 - Sorna Vertex 25ei Platform/CD Burner Dear Mr. Ortiz, Meridian Medical Systems, LLC is pleased to submit the following quote in response to Solicitation 36C24126Q0731 [...truncated]"
  - **model's evidence (what it chose to cite):** "Shipping for this order is $150.00 and will be invoiced as a separate line item on the purchase order, not included in the Vertex 25ei/CD Burner unit price above."
  - **model's reasoning:** The requirement states that delivery or shipping costs must fall below $250.00, or else be rolled into the line-item price for the Vertex 25ei/CD Burner. The bidder's quote explicitly states that shipping is $150.00, which is below the $250.00 threshold, thus satisfying the requirement.
  - **expected evidence (true_verdicts.json):** "Shipping for this order is $150.00 and will be invoiced as a separate line item on the purchase order, not included in the Vertex 25ei/CD Burner unit price above."
  - **expected reasoning:** Shipping is $150.00 (under the $250.00 threshold) but is billed as a separate line item instead of being rolled into the unit price, contradicting the requirement.

**False-issue rate** — mirror direction: the true verdict is `compliant` only, but the pipeline raised an issue anyway.
- rate: 16.7%

- group of 2 true topic(s) and 1 predicted requirement(s) (not a 1:1 match, so there is no single correct pairing between them):
  - true `eft_indicator_if_applicable` — "The quoter also must enter its Electronic Funds Transfer (EFT) indicator, if applicable." (acceptable: ['compliant', 'insufficient_information'])
      - **expected evidence (true_verdicts.json):** none
      - **expected reasoning:** The application never mentions an EFT indicator. Since the requirement is conditional ('if applicable'), text alone cannot distinguish 'not applicable to this quoter' from 'applicable but omitted' -- both compliant (nothing was owed) and insufficient_information (can't tell) are defensible; non_compliant would wrongly assume it was owed.
  - true `uei_provided_on_quote` — "The quoter must enter, in the block with its name and address on the cover page of its quote, the annotation "Unique Entity Identifier" followed by the unique entity identifier that identifies the quoter's name and address." (acceptable: ['compliant'])
      - **expected evidence (true_verdicts.json):** "Unique Entity Identifier: NL8K4TQ9XPW3"
      - **expected reasoning:** UEI is entered in the cover block, annotated as required.
  - **retrieved context (shown to the model):** "From: quotes@meridianmedsystems.com To: carlos.ortiz3@va.gov Subject: Quote for Solicitation 36C24126Q0731 P0003 - Sorna Vertex 25ei Platform/CD Burner Dear Mr. Ortiz, Meridian Medical Systems, LLC is pleased to submit the following quote in response to Solicitation 36C24126Q0731 [...truncated]"
  - **retrieved context (shown to the model):** "Terms and conditions: The terms and conditions in the solicitation are acceptable to be included in the award document without modification, deletion, or addition. Total quoted price for this solicitation: $21,540.00. Product Chart pricing: Item 951-707100, Vertex 25ei Platform w [...truncated]"
  - **retrieved context (shown to the model):** "We acknowledge receipt of Amendment/Modification P0003 dated 08/25/26, which extended the response date for this RFQ to 09/18/26 at 11:00 AM EDT and replaced the prior Combined Synopsis and all earlier amendments/modifications. Technical description of items quoted: We are quotin [...truncated]"
  - predicted verdicts in this group:
    - predicted [7f38e8d7] "The quoter must enter its Unique Entity Identifier and Electronic Funds Transfer indicator on the cover page of its quote." — verdict: non_compliant
      - **model's evidence (what it chose to cite):** "Unique Entity Identifier: NL8K4TQ9XPW3"
      - **model's reasoning:** The requirement states that the quoter must enter both its Unique Entity Identifier and Electronic Funds Transfer (EFT) indicator on the cover page of its quote. While the bidder provided its Unique Entity Identifier in chunk 0, the excerpts do not show any mention of an Electronic Funds Transfer (EFT) indicator.

**Unscored** — split/merge groups excluded from the matrix above (still counted in the two rates above):
- group 1:
  - true `eft_indicator_if_applicable` — "The quoter also must enter its Electronic Funds Transfer (EFT) indicator, if applicable." (acceptable: ['compliant', 'insufficient_information'])
  - true `uei_provided_on_quote` — "The quoter must enter, in the block with its name and address on the cover page of its quote, the annotation "Unique Entity Identifier" followed by the unique entity identifier that identifies the quoter's name and address." (acceptable: ['compliant'])
  - predicted [7f38e8d7] "The quoter must enter its Unique Entity Identifier and Electronic Funds Transfer indicator on the cover page of its quote." — verdict: non_compliant
- group 2:
  - true `amendment_acknowledgment` — "(9) Acknowledgment Request for Quotation amendments;" (acceptable: ['compliant'])
  - true `far_52_212_3_reps_and_certs` — "(8) A completed copy of the representations and certifications under the Federal Acquisition Regulation (FAR) 52.212-3 (see FAR 52.212-3(b) for those representations and certifications that the quoter shall complete electronically)." (acceptable: ['non_compliant'])
  - true `price_and_discount_terms_stated` — "(6) Price and any discount terms;" (acceptable: ['compliant'])
  - true `quoter_contact_info_stated` — "(3) The name, address, and telephone number of the quoter;" (acceptable: ['compliant'])
  - true `remit_to_address_stated` — "(7) "Remit to" address, if different from the mailing address;" (acceptable: ['compliant'])
  - true `solicitation_number_stated` — "(1) The solicitation number;" (acceptable: ['compliant'])
  - true `technical_description_stated` — "(4) A technical description of the items being quoted in sufficient detail to evaluate compliance with the requirements in the solicitation. This may include product literature, or other documents, if necessary." (acceptable: ['compliant'])
  - true `time_specified_for_receipt_stated` — "(2) The time specified in the solicitation for receipt of quotations;" (acceptable: ['compliant'])
  - true `warranty_terms_stated` — "(5) Terms of any express warranty;" (acceptable: ['compliant'])
  - predicted [ed8fd964] "Quotes must show minimum required information including solicitation number, time specified for receipt, quoter contact details, technical description, warranty terms, price/discount terms, remit-to address, FAR representations/certifications, amendment acknowledgments, and statement of agreement with terms." — verdict: compliant

## Evidence

**Citation-verified rate** (evidence-level): fraction of evidence quotes actually located in application.txt.
- rate: 100.0% (0 unverified of 52)

**Evidence recall**: does the expected evidence span (from `true_verdicts.json`) show up somewhere in the requirement's retrieved chunks, before the verdict step chose what to cite? Topics never extracted as a requirement are excluded — that failure is already counted by requirement recall above.
- recall: 100.0% (14/14)
- missed:
  - none

## Verdict-only evaluation

Runs verdict generation directly on true_requirements.json's own text and citations against application.txt, bypassing requirement extraction and match-group sequencing entirely -- isolates whether generate_verdict, given a perfect requirement, makes the right call. Only mismatches are listed below.

**Accuracy: 94.4% (17/18)**

- `product_chart_full_pricing` — acceptable: ['contradictory', 'non_compliant'], predicted: insufficient_information
  - **requirement:** "Quote must enter pricing for every line item listed in the Product Chart."
  - **retrieved context (shown to the model):** "Terms and conditions: The terms and conditions in the solicitation are acceptable to be included in the award document without modification, deletion, or addition. Total quoted price for this solicitation: $21,540.00. Product Chart pricing: Item 951-707100, Vertex 25ei Platform w/ Sorna CD Burner, Qty 1, Unit Price $19,200.00, Total $19,200.00. Item 501-862406, Installation & Training Support, Qty 1, Unit Price $1,650.00, Total $1,650.00. UPS 1KVA - Tower, Qty 1, Unit Price $540.00, Total $540.00. Training Manuals, Qty 2, Unit Price $75.00, Total $150.00. Delivery, Qty 1, Unit Price $1,400.00, Total $1,400.00. Grand total of the line items above: $22,940.00. We are also pleased to offer an alternative configuration for your consideration: Option A (as priced above): Standard configuration, grand total $22,940.00. Option B: Extended 5-year warranty configuration, grand total $23,100.00. Please let us know which option you would prefer to award. Shipping for this order is $150.00 and will be invoiced as a separate line item on the purchase order, not included in the Vertex 25ei/CD Burner unit price above. Please contact us with any questions regarding this quote. Sincerely, Diane Kowalski Contracts Manager Meridian Medical Systems, LLC"
  - **retrieved context (shown to the model):** "We acknowledge receipt of Amendment/Modification P0003 dated 08/25/26, which extended the response date for this RFQ to 09/18/26 at 11:00 AM EDT and replaced the prior Combined Synopsis and all earlier amendments/modifications. Technical description of items quoted: We are quoting the Sorna Vertex 25ei Platform with integrated Sorna CD Burner, brand name, exactly as specified in the Product Chart. This is the identical brand-name system required by the solicitation; Meridian is not offering a substitute or equivalent product. The package includes the Vertex Host software with unlimited Client and Media Importer licenses, automated DICOM profiles, a pre-configured Windows 11 Professional PC, monitor, keyboard, mouse, disc label design software, and all necessary cabling, matching the Statement of Work in full. Terms of express warranty: The system is covered by the manufacturer's standard 3-year parts-and-labor warranty from the date of installation. Price and discount terms: Net 30 days from invoice date. No prompt-payment discount is offered. "Remit to" address: Same as the mailing address listed above. Our representations and certifications under FAR 52.212-3 are on file in SAM.gov and available upon request; we have not attached a completed copy to this email. Terms and conditions: The terms and conditions in the solicitation are acceptable to be included in the award document without modification, deletion, or addition."
  - **retrieved context (shown to the model):** "From: quotes@meridianmedsystems.com To: carlos.ortiz3@va.gov Subject: Quote for Solicitation 36C24126Q0731 P0003 - Sorna Vertex 25ei Platform/CD Burner Dear Mr. Ortiz, Meridian Medical Systems, LLC is pleased to submit the following quote in response to Solicitation 36C24126Q0731 P0003. We acknowledge the time specified in the solicitation for receipt of quotations as 11:00 AM EDT on 09/18/26, and our quote is submitted ahead of that deadline. Quoter name, address, and telephone number: Meridian Medical Systems, LLC 88 Harborview Drive, Suite 210 Providence, RI 02903 Telephone: (401) 555-0142 Unique Entity Identifier: NL8K4TQ9XPW3 Meridian Medical Systems, LLC is registered and active in the System for Award Management (SAM). Meridian Medical Systems, LLC is a VIP-listed Service-Disabled Veteran-Owned Small Business (SDVOSB), verified under SBA SBS VetCert Case #DV-2024-01187. We acknowledge receipt of Amendment/Modification P0003 dated 08/25/26, which extended the response date for this RFQ to 09/18/26 at 11:00 AM EDT and replaced the prior Combined Synopsis and all earlier amendments/modifications."
  - **model's evidence (what it chose to cite):** "Product Chart pricing: Item 951-707100, Vertex 25ei Platform w/ Sorna CD Burner, Qty 1, Unit Price $19,200.00, Total $19,200.00. Item 501-862406, Installation & Training Support, Qty 1, Unit Price $1,650.00, Total $1,650.00. UPS 1KVA - Tower, Qty 1, Unit Price $540.00, Total $540.00. Training Manuals, Qty 2, Unit Price $75.00, Total $150.00. Delivery, Qty 1, Unit Price $1,400.00, Total $1,400.00. Grand total of the line items above: $22,940.00."
  - **model's reasoning:** The bidder provides a Product Chart pricing section containing several line items. However, the text does not include the actual Product Chart from the tender's requirements document, making it impossible to verify whether pricing was entered for every single line item listed in the original Product Chart.
  - **expected evidence (true_verdicts.json):** "Total quoted price for this solicitation: $21,540.00."
  - **expected evidence (true_verdicts.json):** "Product Chart pricing: Item 951-707100, Vertex 25ei Platform w/ Sorna CD Burner, Qty 1, Unit Price $19,200.00, Total $19,200.00. Item 501-862406, Installation & Training Support, Qty 1, Unit Price $1,650.00, Total $1,650.00. UPS 1KVA - Tower, Qty 1, Unit Price $540.00, Total $540.00. Training Manuals, Qty 2, Unit Price $75.00, Total $150.00. Delivery, Qty 1, Unit Price $1,400.00, Total $1,400.00. Grand total of the line items above: $22,940.00."
  - **expected reasoning (true_verdicts.json):** All five Product Chart line items are priced, but the quote states two different grand totals for the same quote: $21,540.00 up front and $22,940.00 from the itemized breakdown -- a direct numeric contradiction. non_compliant is also acceptable if a pipeline flags the mismatched total as a completeness/accuracy failure instead of naming it a contradiction.
