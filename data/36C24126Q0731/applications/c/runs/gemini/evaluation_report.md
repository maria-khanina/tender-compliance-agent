# Evaluation report

## Summary metrics

Machine-readable numbers for averaging across tenders -- every value here is explained in the sections below. `null` means the metric doesn't apply to this run (e.g. no verdict-only artifact present).

```json
{
  "requirement_recall": 0.913,
  "requirement_recall_matched": 21,
  "requirement_recall_total": 23,
  "requirement_precision": 0.3443,
  "citation_verified_rate": 1.0,
  "is_mandatory_accuracy": 0.9474,
  "is_mandatory_scored": 19,
  "is_text_verifiable_accuracy": 0.7895,
  "is_text_verifiable_scored": 19,
  "verdict_clean_match_count": 13,
  "verdict_accuracy": 0.6923,
  "false_compliant_rate": 0.1333,
  "false_issue_rate": 0.1333,
  "evidence_citation_verified_rate": 1.0,
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

**Over-split** (2) — one true topic extracted as several separate predicted requirements:
- true `terms_and_conditions_acceptance_statement` — "To facilitate the award process, all quotes must include a statement regarding the terms and conditions herein as follows: "The terms and conditions in the solicitation are acceptable to be included in the award document without modification, deletion, or addition." OR "The terms and conditions in the solicitation are acceptable to be included in the award document with the exception, deletion, or addition of the following:" Quoters shall list exception(s) and rationale for the exception(s), if any." split into 2 predicted requirements:
  - predicted [23ef7ab9] "All quotes must include a statement accepting the solicitation terms and conditions without modification, deletion, or addition." — verdict: compliant, citation: fuzzy match — worth a second look
  - predicted [319afa90] "Quoters shall list exception(s) and rationale for the exception(s), if any." — verdict: compliant
- true `brand_name_no_substitutes` — "The quotations shall be brand name for the for Sorna Vertex 25ei & CD Burner listed in the Product Chart above and as described in detail in the combined synopsis solicitation, Intent to Compete/ RFQ as posted on Contract Opportunities starting on Page 1 (P1). ... No substitutions can be considered." split into 2 predicted requirements:
  - predicted [51d4322f] "No substitutions can be considered." — verdict: compliant
  - predicted [b04d87d0] "The quotation must be for the Sorna Vertex 25ei & CD Burner brand name products as described in the Product Chart and Statement of Work." — verdict: compliant

**Over-merge** (2) — one predicted requirement covering several distinct true topics:
- predicted [31b07502] "Offeror must meet and assert compliance with Limitations on Subcontracting (LOS) requirements in the accompanying email." — verdict: compliant lumps together 2 true requirements:
  - true `los_compliance_assertion` — "Compliance with the LOS clauses must be asserted by the offeror in the email accompanying their quote."
  - true `los_requirements_met` — "Offeror must meet LOS (Limitations on Subcontracting) requirements and per the LOS listed clauses below."
- predicted [b2c851c6] "Quotes must be submitted via email to the specified government point of contact at or before the exact time specified." — verdict: insufficient_information lumps together 2 true requirements:
  - true `quote_signed_and_dated` — "Submit signed and dated quotes to the office specified in this Combined Synopsis: Intent to Compete/RFQ"
  - true `submission_deadline_and_channel` — "All quotations shall be emailed to: carlos.ortiz3@va.gov ... E-mailed quotes will be accepted. Submission shall be received no later than 11:00 AM EDT 09/18/26."

**Tangled** (0) — several true and several predicted requirements all overlapping at once:
- none

## Requirement precision

**Citation-verified rate** (hallucination check): fraction of predicted requirements whose citation was actually located in tender.txt (exactly or via fuzzy match).
- rate: 100.0%
- unverified:
  - none

**Classification precision**: fraction of predicted requirements that matched a true requirement.
- rate: 34.4%
- unexplained (40) — the model recognized these as requirements, but they don't match any true requirement. "closest true topic" is a mechanical (no-LLM) embedding-similarity lookup against every true topic's description; "dedup visibility" checks whether dedup's own cosine pre-filter would have clustered this candidate with whatever predicted requirement DID match that topic -- i.e. whether the dedup LLM call ever had a chance to compare them:
  - predicted [0089b36a] "Management and daily business operations must be controlled by one or more Veterans or service-disabled Veterans (or eligible spouses/caregivers)."
    - **similarity check:** closest true topic: `sdvosb_certification_required` (cosine=0.54); vs matched predicted [e8209ee8]: cosine=0.54 (< dedup threshold 0.6) -> dedup's cosine pre-filter would NOT have clustered these -- the dedup LLM call never saw them side by side
  - predicted [03aa446d] "Requirements apply to any contract, order, or subcontract where the firm receives benefit or preference from VOSB designation."
    - **similarity check:** closest true topic: `los_requirements_met` (cosine=0.62); vs matched predicted [31b07502]: cosine=0.70 (>= dedup threshold 0.6) -> would likely have been clustered together and compared by the dedup LLM call
  - predicted [19237a9a] "When a contract includes both supply and services, limitations apply to the portion or preponderance of expenditure based on assigned NAICS."
    - **similarity check:** closest true topic: `los_requirements_met` (cosine=0.60); vs matched predicted [31b07502]: cosine=0.63 (>= dedup threshold 0.6) -> would likely have been clustered together and compared by the dedup LLM call
  - predicted [292fffac] "Input Capacity: 2 Bins (50 Discs EA)"
    - **similarity check:** closest true topic: `price_and_discount_terms_stated` (cosine=0.50); vs matched predicted [55d9cf9f]: cosine=0.52 (< dedup threshold 0.6) -> dedup's cosine pre-filter would NOT have clustered these -- the dedup LLM call never saw them side by side
  - predicted [2ee8bec6] "Definition of small business concern owned and controlled by Veterans requires VIP database listing for VA contracts."
    - **similarity check:** closest true topic: `sdvosb_certification_required` (cosine=0.62); vs matched predicted [e8209ee8]: cosine=0.63 (>= dedup threshold 0.6) -> would likely have been clustered together and compared by the dedup LLM call
  - predicted [3ae81f43] "Quote should include a statement specifying the extent of agreement with all terms, conditions, and provisions."
    - **similarity check:** closest true topic: `terms_and_conditions_acceptance_statement` (cosine=0.79); vs matched predicted [23ef7ab9]: cosine=0.74 (>= dedup threshold 0.6) -> would likely have been clustered together and compared by the dedup LLM call
  - predicted [3e16a579] "Any work that a first tier VIP-listed subcontractor further subcontracts counts towards the non-exceeded subcontract amount percent."
    - **similarity check:** closest true topic: `sdvosb_certification_required` (cosine=0.69); vs matched predicted [e8209ee8]: cosine=0.72 (>= dedup threshold 0.6) -> would likely have been clustered together and compared by the dedup LLM call
  - predicted [429f583a] "Media types: CD-R, DVD-R, BD-R with white inkjet print media"
    - **similarity check:** closest true topic: `brand_name_no_substitutes` (cosine=0.55); vs matched predicted [b04d87d0]: cosine=0.59 (< dedup threshold 0.6) -> dedup's cosine pre-filter would NOT have clustered these -- the dedup LLM call never saw them side by side
  - predicted [43da5d80] "A joint venture may be considered eligible if listed in VIP and compliant with 13 CFR 125.18(b)."
    - **similarity check:** closest true topic: `sdvosb_certification_required` (cosine=0.74); vs matched predicted [e8209ee8]: cosine=0.77 (>= dedup threshold 0.6) -> would likely have been clustered together and compared by the dedup LLM call
  - predicted [53f209f5] "Output Capacity: 10-Disc Drawer and 50-Disc Bin"
    - **similarity check:** closest true topic: `brand_name_no_substitutes` (cosine=0.48); vs matched predicted [b04d87d0]: cosine=0.50 (< dedup threshold 0.6) -> dedup's cosine pre-filter would NOT have clustered these -- the dedup LLM call never saw them side by side
  - predicted [553fed92] "The business must be verified for ownership and control and listed in VA's VIP database."
    - **similarity check:** closest true topic: `sdvosb_certification_required` (cosine=0.72); vs matched predicted [e8209ee8]: cosine=0.71 (>= dedup threshold 0.6) -> would likely have been clustered together and compared by the dedup LLM call
  - predicted [5d572fad] "Delivery Hours are 0800-1530."
    - **similarity check:** closest true topic: `time_specified_for_receipt_stated` (cosine=0.58); vs matched predicted [dcce8a25]: cosine=0.59 (< dedup threshold 0.6) -> dedup's cosine pre-filter would NOT have clustered these -- the dedup LLM call never saw them side by side
  - predicted [6b592c6f] "Small business concern must be not less than 51 percent owned by one or more service-disabled Veterans or eligible surviving spouses."
    - **similarity check:** closest true topic: `sdvosb_certification_required` (cosine=0.59); vs matched predicted [e8209ee8]: cosine=0.59 (< dedup threshold 0.6) -> dedup's cosine pre-filter would NOT have clustered these -- the dedup LLM call never saw them side by side
  - predicted [6e62410b] "By submitting an offer, the prospective contractor represents that it is an eligible SDVOSB/VOSB."
    - **similarity check:** closest true topic: `sdvosb_certification_required` (cosine=0.71); vs matched predicted [e8209ee8]: cosine=0.74 (>= dedup threshold 0.6) -> would likely have been clustered together and compared by the dedup LLM call
  - predicted [749819ea] "Vertex Host software with unlimited Client and Media Importer licenses"
    - **similarity check:** closest true topic: `brand_name_no_substitutes` (cosine=0.57); vs matched predicted [b04d87d0]: cosine=0.58 (< dedup threshold 0.6) -> dedup's cosine pre-filter would NOT have clustered these -- the dedup LLM call never saw them side by side
  - predicted [762c9477] "Business must be not less than 51 percent owned by one or more Veterans."
    - **similarity check:** closest true topic: `sdvosb_certification_required` (cosine=0.58); vs matched predicted [e8209ee8]: cosine=0.57 (< dedup threshold 0.6) -> dedup's cosine pre-filter would NOT have clustered these -- the dedup LLM call never saw them side by side
  - predicted [7a5b6e82] "Disc Label Design Software and All Necessary Cabling"
    - **similarity check:** closest true topic: `brand_name_no_substitutes` (cosine=0.55); vs matched predicted [b04d87d0]: cosine=0.56 (< dedup threshold 0.6) -> dedup's cosine pre-filter would NOT have clustered these -- the dedup LLM call never saw them side by side
  - predicted [7d23c9e8] "For special trade contractors, no more than 75% of the amount paid (excluding materials) may be paid to non-VIP-listed firms."
    - **similarity check:** closest true topic: `sdvosb_certification_required` (cosine=0.65); vs matched predicted [e8209ee8]: cosine=0.67 (>= dedup threshold 0.6) -> would likely have been clustered together and compared by the dedup LLM call
  - predicted [874e7100] "The business must meet Federal small business size standards for the applicable NAICS code identified in the solicitation."
    - **similarity check:** closest true topic: `solicitation_number_stated` (cosine=0.64); vs matched predicted [50a46b6e]: cosine=0.65 (>= dedup threshold 0.6) -> would likely have been clustered together and compared by the dedup LLM call
  - predicted [8a3cbb86] "MOD P0003 extends the RFQ due date to 09/18/26 at 11:00 AM EDT."
    - **similarity check:** closest true topic: `submission_deadline_and_channel` (cosine=0.66); vs matched predicted [b2c851c6]: cosine=0.55 (< dedup threshold 0.6) -> dedup's cosine pre-filter would NOT have clustered these -- the dedup LLM call never saw them side by side
  - predicted [8a3da08b] "For service contracts, prime contractor will not pay more than 50% of the amount paid by the government to non-VIP-listed firms."
    - **similarity check:** closest true topic: `sdvosb_certification_required` (cosine=0.67); vs matched predicted [e8209ee8]: cosine=0.70 (>= dedup threshold 0.6) -> would likely have been clustered together and compared by the dedup LLM call
  - predicted [925d687b] "For supply contracts, prime contractor will not pay more than 50% of the amount paid by the government (excluding materials) to non-VIP-listed firms."
    - **similarity check:** closest true topic: `sdvosb_certification_required` (cosine=0.66); vs matched predicted [e8209ee8]: cosine=0.69 (>= dedup threshold 0.6) -> would likely have been clustered together and compared by the dedup LLM call
  - predicted [92722445] "Automated DICOM profiles and local burning capabilities"
    - **similarity check:** closest true topic: `brand_name_no_substitutes` (cosine=0.49); vs matched predicted [b04d87d0]: cosine=0.58 (< dedup threshold 0.6) -> dedup's cosine pre-filter would NOT have clustered these -- the dedup LLM call never saw them side by side
  - predicted [a16912fb] "Requirements in 13 CFR parts 121 and 125 applying to SDVO SBC apply to VIP-listed SDVOSB/VOSB unless otherwise stated."
    - **similarity check:** closest true topic: `sdvosb_certification_required` (cosine=0.78); vs matched predicted [e8209ee8]: cosine=0.80 (>= dedup threshold 0.6) -> would likely have been clustered together and compared by the dedup LLM call
  - predicted [aec71abe] "Dimensions: 13.7”H x 14.8” W x 20.2” D"
    - **similarity check:** closest true topic: `price_and_discount_terms_stated` (cosine=0.49); vs matched predicted [55d9cf9f]: cosine=0.47 (< dedup threshold 0.6) -> dedup's cosine pre-filter would NOT have clustered these -- the dedup LLM call never saw them side by side
  - predicted [af14264f] "For supply or construction contracts, the cost of materials is excluded and not considered subcontracted."
    - **similarity check:** closest true topic: `price_and_discount_terms_stated` (cosine=0.51); vs matched predicted [55d9cf9f]: cosine=0.52 (< dedup threshold 0.6) -> dedup's cosine pre-filter would NOT have clustered these -- the dedup LLM call never saw them side by side
  - predicted [affdc42a] "For general construction contracts, prime contractor will not pay more than 85% of the amount paid (excluding materials) to non-VIP-listed firms."
    - **similarity check:** closest true topic: `sdvosb_certification_required` (cosine=0.65); vs matched predicted [e8209ee8]: cosine=0.67 (>= dedup threshold 0.6) -> would likely have been clustered together and compared by the dedup LLM call
  - predicted [b07dedfe] "Dual Recorders and High-Resolution Inkjet Printer (Black and Color Cartridges)"
    - **similarity check:** closest true topic: `brand_name_no_substitutes` (cosine=0.48); vs matched predicted [b04d87d0]: cosine=0.49 (< dedup threshold 0.6) -> dedup's cosine pre-filter would NOT have clustered these -- the dedup LLM call never saw them side by side
  - predicted [b148bce8] "Pre-configured Windows 11 Professional PC"
    - **similarity check:** closest true topic: `brand_name_no_substitutes` (cosine=0.45); vs matched predicted [b04d87d0]: cosine=0.44 (< dedup threshold 0.6) -> dedup's cosine pre-filter would NOT have clustered these -- the dedup LLM call never saw them side by side
  - predicted [b6dbc256] "Deliver to: VAMC CWM (Northampton) 421 N. Main Street Leeds, MA 01053"
    - **similarity check:** closest true topic: `remit_to_address_stated` (cosine=0.48); vs matched predicted [9acea79a]: cosine=0.51 (< dedup threshold 0.6) -> dedup's cosine pre-filter would NOT have clustered these -- the dedup LLM call never saw them side by side
  - predicted [bd420405] "Any questions or concerns must be forwarded in writing via email to the Point of Contact."
    - **similarity check:** closest true topic: `solicitation_number_stated` (cosine=0.67); vs matched predicted [50a46b6e]: cosine=0.69 (>= dedup threshold 0.6) -> would likely have been clustered together and compared by the dedup LLM call
  - predicted [c69893ab] "Keyboard"
    - **similarity check:** closest true topic: `price_and_discount_terms_stated` (cosine=0.47); vs matched predicted [55d9cf9f]: cosine=0.54 (< dedup threshold 0.6) -> dedup's cosine pre-filter would NOT have clustered these -- the dedup LLM call never saw them side by side
  - predicted [c906acaf] "A joint venture agrees that, in the performance of the contract, the applicable percentage specified in paragraph (d) of this clause will be performed by the aggregate of the joint venture participants."
    - **similarity check:** closest true topic: `los_compliance_assertion` (cosine=0.55); vs matched predicted [31b07502]: cosine=0.60 (< dedup threshold 0.6) -> dedup's cosine pre-filter would NOT have clustered these -- the dedup LLM call never saw them side by side
  - predicted [d5b1d687] "Monitor"
    - **similarity check:** closest true topic: `price_and_discount_terms_stated` (cosine=0.51); vs matched predicted [55d9cf9f]: cosine=0.51 (< dedup threshold 0.6) -> dedup's cosine pre-filter would NOT have clustered these -- the dedup LLM call never saw them side by side
  - predicted [d5ffa98a] "For non-manufacturer supply contracts, the prime contractor will supply the product of a domestic small business manufacturer unless waived."
    - **similarity check:** closest true topic: `sdvosb_certification_required` (cosine=0.65); vs matched predicted [e8209ee8]: cosine=0.67 (>= dedup threshold 0.6) -> would likely have been clustered together and compared by the dedup LLM call
  - predicted [e65a5d34] "The quoter agrees to hold prices firm for 30 calendar days from the date specified for receipt of quotes."
    - **similarity check:** closest true topic: `time_specified_for_receipt_stated` (cosine=0.71); vs matched predicted [dcce8a25]: cosine=0.66 (>= dedup threshold 0.6) -> would likely have been clustered together and compared by the dedup LLM call
  - predicted [f0c59aa3] "Only VIP-listed SDVOSBs/VOSBs meeting NAICS size standards shall be considered eligible and similarly situated for subcontracting purposes."
    - **similarity check:** closest true topic: `sdvosb_certification_required` (cosine=0.73); vs matched predicted [e8209ee8]: cosine=0.76 (>= dedup threshold 0.6) -> would likely have been clustered together and compared by the dedup LLM call
  - predicted [f2d2a312] "Mouse"
    - **similarity check:** closest true topic: `price_and_discount_terms_stated` (cosine=0.45); vs matched predicted [55d9cf9f]: cosine=0.50 (< dedup threshold 0.6) -> dedup's cosine pre-filter would NOT have clustered these -- the dedup LLM call never saw them side by side
  - predicted [f3a9a8af] "The FOB point is “Destination.”"
    - **similarity check:** closest true topic: `quote_signed_and_dated` (cosine=0.53); vs matched predicted [b2c851c6]: cosine=0.48 (< dedup threshold 0.6) -> dedup's cosine pre-filter would NOT have clustered these -- the dedup LLM call never saw them side by side
  - predicted [f4df3037] "All SD/VOSB and VIP-listing eligibility requirements must be met for quotes to be considered for award."
    - **similarity check:** closest true topic: `sdvosb_certification_required` (cosine=0.77); vs matched predicted [e8209ee8]: cosine=0.80 (>= dedup threshold 0.6) -> would likely have been clustered together and compared by the dedup LLM call

## Coverage flags

Clean 1:1 matches (recall counted them as found) whose citations don't fully overlap in length, split by which side is off. Over-split/over-merge/tangled matches are excluded here -- their predicted fragments are inherently partial by construction, already shown in the recall breakdown above.

**Requirements captured with extra text** (0) — the predicted citation is padded beyond the true one:
- none

**Requirements captured incompletely** (0) — the predicted citation misses part of the true one:
- none

## is_mandatory accuracy

For each clean or one-to-many match (tangled groups excluded — there's no single "one" to compare against), does `is_mandatory` agree with the true value? A one-to-many group counts as correct only if every member on the "many" side agrees with the "one".

**Accuracy: 94.7% (19 groups)**

Mismatched:
- true: `eft_indicator_if_applicable`=False; predicted: `fc903e9b`=True — "The quoter also must enter its Electronic Funds Transfer (EFT) indicator, if applicable."

## is_text_verifiable accuracy

For each clean or one-to-many match (tangled groups excluded), does `is_text_verifiable` agree with the true value (all-or-nothing on the "many" side, same rule as is_mandatory above)? A wrong `false` here means the pipeline skips verdict generation for a requirement that should get one.

**Accuracy: 78.9% (19 groups)**

Mismatched:
- true: `sam_registration_required`=False; predicted: `794ab891`=True — "Offeror must be registered in SAM."
- true: `sdvosb_certification_required`=False; predicted: `e8209ee8`=True — "Offeror must be certified/verified as an SD/VOSB in the SBA SBS VIP (Veteran Information Pages) VetCert as an SD/VOSB."
- true: `los_compliance_assertion`=True, `los_requirements_met`=False; predicted: `31b07502`=True — "Compliance with the LOS clauses must be asserted by the offeror in the email accompanying their quote."
- true: `quote_signed_and_dated`=True, `submission_deadline_and_channel`=False; predicted: `b2c851c6`=True — "Submit signed and dated quotes to the office specified in this Combined Synopsis: Intent to Compete/RFQ"

## Verdict accuracy

The confusion matrix covers only clean 1:1 matches — split/merge groups have no single pair to plot, but still count in the two rates below.

Clean matches scored: 13

| true \ pipeline said | `compliant` | `non_compliant` | `contradictory` | `insufficient_information` |
|---|---|---|---|---|
| `compliant` | 8 | 2 | 0 | 0 |
| `non_compliant` | 1 | 0 | 0 | 0 |
| `contradictory` | 1 | 0 | 0 | 0 |
| `insufficient_information` | 0 | 0 | 0 | 1 |

**Mismatched clean matches** — every off-diagonal cell above, in full: the full context retrieved and shown to the model, what it chose to cite from that context, and its reasoning ("model's ..."), next to what `true_verdicts.json` expects ("expected ...").

- `uei_provided_on_quote` — acceptable: ['compliant'], predicted: non_compliant
  - **requirement:** "The quoter must enter the Unique Entity Identifier annotation in the block with its name and address."
  - **retrieved context (shown to the model):** "From: sales@quantumimagingsolutions.com To: carlos.ortiz3@va.gov Subject: Quote for Solicitation 36C24126Q0731 P0003 - Sorna Vertex 25ei Platform/CD Burner Dear Mr. Ortiz, Quantum Imaging Solutions, LLC submits the following quote in response to Solicitation 36C24126Q0731 P0003 f [...truncated]"
  - **retrieved context (shown to the model):** "Price and discount terms: Net 30 days from invoice date. No prompt-payment discount is offered. "Remit to" address: Same as the mailing address listed above. Representations and Certifications under FAR 52.212-3: Quantum Imaging Solutions, LLC's representations and certifications [...truncated]"
  - **model's evidence (what it chose to cite):** "Quoter name, address, and telephone number: Quantum Imaging Solutions, LLC 615 Innovation Parkway Cary, NC 27513 Telephone: (919) 555-0286 Unique Entity Identifier: QIS7K4RTM392"
  - **model's reasoning:** The requirement states that the Unique Entity Identifier annotation must be entered in the block with the quoter's name and address. In the bidder's application, while the Unique Entity Identifier is provided, it is placed separately below the telephone number rather than integrated directly within the block containing the name and address.
  - **expected evidence (true_verdicts.json):** "Unique Entity Identifier: QIS7K4RTM392"
  - **expected reasoning:** UEI is explicitly entered and annotated as such.

- `technical_description_stated` — acceptable: ['contradictory'], predicted: compliant
  - **requirement:** "Quote must include a technical description of the items being quoted in sufficient detail to evaluate compliance."
  - **retrieved context (shown to the model):** "From: sales@quantumimagingsolutions.com To: carlos.ortiz3@va.gov Subject: Quote for Solicitation 36C24126Q0731 P0003 - Sorna Vertex 25ei Platform/CD Burner Dear Mr. Ortiz, Quantum Imaging Solutions, LLC submits the following quote in response to Solicitation 36C24126Q0731 P0003 f [...truncated]"
  - **retrieved context (shown to the model):** "Price and discount terms: Net 30 days from invoice date. No prompt-payment discount is offered. "Remit to" address: Same as the mailing address listed above. Representations and Certifications under FAR 52.212-3: Quantum Imaging Solutions, LLC's representations and certifications [...truncated]"
  - **model's evidence (what it chose to cite):** "Technical description of items quoted: We are quoting one (1) Sorna Vertex 25ei Platform with integrated Sorna CD Burner, brand name, exactly as specified in the Product Chart. This is the identical brand-name system required by the solicitation; Quantum Imaging Solutions is not offering a substitute or equivalent product."
  - **model's evidence (what it chose to cite):** "Product Chart pricing: Item 951-707100, Vertex 25ei Platform w/ Sorna CD Burner, Qty 2, Unit Price $19,400.00, Total $19,400.00. Item 501-862406, Installation & Training Support, Qty 1, Unit Price $1,700.00, Total $1,700.00. UPS 1KVA - Tower, Qty 1, Unit Price $540.00, Total $540.00. Training Manuals, Qty 2, Unit Price $75.00, Total $150.00."
  - **model's reasoning:** The bidder provides a clear technical description of the items being quoted, identifying the exact brand-name system (Sorna Vertex 25ei Platform with integrated Sorna CD Burner) along with specific product chart line items and quantities, satisfying the requirement to include a technical description in sufficient detail.
  - **expected evidence (true_verdicts.json):** "Quantum Imaging Solutions, LLC submits the following quote in response to Solicitation 36C24126Q0731 P0003 for one (1) Sorna Vertex 25ei Platform/CD Burner."
  - **expected evidence (true_verdicts.json):** "Item 951-707100, Vertex 25ei Platform w/ Sorna CD Burner, Qty 2, Unit Price $19,400.00, Total $19,400.00."
  - **expected reasoning:** The introduction and technical description both state the quote is for one (1) Sorna Vertex 25ei Platform, but the Product Chart pricing lists a quantity of 2 for the same line item -- the stated quantity being quoted conflicts with the priced quantity.

- `far_52_212_3_reps_and_certs` — acceptable: ['compliant'], predicted: non_compliant
  - **requirement:** "Quote must include a completed copy of the representations and certifications under FAR 52.212-3."
  - **retrieved context (shown to the model):** "From: sales@quantumimagingsolutions.com To: carlos.ortiz3@va.gov Subject: Quote for Solicitation 36C24126Q0731 P0003 - Sorna Vertex 25ei Platform/CD Burner Dear Mr. Ortiz, Quantum Imaging Solutions, LLC submits the following quote in response to Solicitation 36C24126Q0731 P0003 f [...truncated]"
  - **retrieved context (shown to the model):** "Price and discount terms: Net 30 days from invoice date. No prompt-payment discount is offered. "Remit to" address: Same as the mailing address listed above. Representations and Certifications under FAR 52.212-3: Quantum Imaging Solutions, LLC's representations and certifications [...truncated]"
  - **model's evidence (what it chose to cite):** "Representations and Certifications under FAR 52.212-3: Quantum Imaging Solutions, LLC's representations and certifications under FAR 52.212-3 are current and up to date in SAM.gov as of the date of this quote."
  - **model's reasoning:** The requirement states that the quote must include a completed copy of the representations and certifications under FAR 52.212-3. The bidder's application only states that they are current and up to date in SAM.gov, rather than providing a completed copy of the representations and certifications in the quote.
  - **expected evidence (true_verdicts.json):** "Quantum Imaging Solutions, LLC's representations and certifications under FAR 52.212-3 are current and up to date in SAM.gov as of the date of this quote."
  - **expected reasoning:** Application states representations and certifications under FAR 52.212-3 are current in SAM.gov.

- `shipping_cost_handling` — acceptable: ['non_compliant'], predicted: compliant
  - **requirement:** "Delivery cost must be under $250.00; otherwise, shipping costs must be rolled into the line-item price for the Vertex 25ei/CD Burner."
  - **retrieved context (shown to the model):** "Price and discount terms: Net 30 days from invoice date. No prompt-payment discount is offered. "Remit to" address: Same as the mailing address listed above. Representations and Certifications under FAR 52.212-3: Quantum Imaging Solutions, LLC's representations and certifications [...truncated]"
  - **retrieved context (shown to the model):** "From: sales@quantumimagingsolutions.com To: carlos.ortiz3@va.gov Subject: Quote for Solicitation 36C24126Q0731 P0003 - Sorna Vertex 25ei Platform/CD Burner Dear Mr. Ortiz, Quantum Imaging Solutions, LLC submits the following quote in response to Solicitation 36C24126Q0731 P0003 f [...truncated]"
  - **model's evidence (what it chose to cite):** "Shipping for this order is $150.00 and will be invoiced as a separate line item on the purchase order."
  - **model's reasoning:** The requirement specifies that delivery cost must be under $250.00. The bidder states that shipping is $150.00, which is under the $250.00 threshold, thus satisfying the requirement.
  - **expected evidence (true_verdicts.json):** "Shipping for this order is $150.00 and will be invoiced as a separate line item on the purchase order."
  - **expected reasoning:** Application states shipping of $150.00 (below the $250.00 threshold) will be invoiced as a separate line item, rather than rolled into the Vertex 25ei/CD Burner unit price as the requirement demands.

**False-compliant rate** — dangerous direction: the true verdict requires an issue (anything but `compliant`), but every predicted verdict in the group is `compliant`.
- rate: 13.3%

- `technical_description_stated` — acceptable: ['contradictory'], predicted: compliant
  - **requirement:** "Quote must include a technical description of the items being quoted in sufficient detail to evaluate compliance."
  - **retrieved context (shown to the model):** "From: sales@quantumimagingsolutions.com To: carlos.ortiz3@va.gov Subject: Quote for Solicitation 36C24126Q0731 P0003 - Sorna Vertex 25ei Platform/CD Burner Dear Mr. Ortiz, Quantum Imaging Solutions, LLC submits the following quote in response to Solicitation 36C24126Q0731 P0003 f [...truncated]"
  - **retrieved context (shown to the model):** "Price and discount terms: Net 30 days from invoice date. No prompt-payment discount is offered. "Remit to" address: Same as the mailing address listed above. Representations and Certifications under FAR 52.212-3: Quantum Imaging Solutions, LLC's representations and certifications [...truncated]"
  - **model's evidence (what it chose to cite):** "Technical description of items quoted: We are quoting one (1) Sorna Vertex 25ei Platform with integrated Sorna CD Burner, brand name, exactly as specified in the Product Chart. This is the identical brand-name system required by the solicitation; Quantum Imaging Solutions is not offering a substitute or equivalent product."
  - **model's evidence (what it chose to cite):** "Product Chart pricing: Item 951-707100, Vertex 25ei Platform w/ Sorna CD Burner, Qty 2, Unit Price $19,400.00, Total $19,400.00. Item 501-862406, Installation & Training Support, Qty 1, Unit Price $1,700.00, Total $1,700.00. UPS 1KVA - Tower, Qty 1, Unit Price $540.00, Total $540.00. Training Manuals, Qty 2, Unit Price $75.00, Total $150.00."
  - **model's reasoning:** The bidder provides a clear technical description of the items being quoted, identifying the exact brand-name system (Sorna Vertex 25ei Platform with integrated Sorna CD Burner) along with specific product chart line items and quantities, satisfying the requirement to include a technical description in sufficient detail.
  - **expected evidence (true_verdicts.json):** "Quantum Imaging Solutions, LLC submits the following quote in response to Solicitation 36C24126Q0731 P0003 for one (1) Sorna Vertex 25ei Platform/CD Burner."
  - **expected evidence (true_verdicts.json):** "Item 951-707100, Vertex 25ei Platform w/ Sorna CD Burner, Qty 2, Unit Price $19,400.00, Total $19,400.00."
  - **expected reasoning:** The introduction and technical description both state the quote is for one (1) Sorna Vertex 25ei Platform, but the Product Chart pricing lists a quantity of 2 for the same line item -- the stated quantity being quoted conflicts with the priced quantity.

- `shipping_cost_handling` — acceptable: ['non_compliant'], predicted: compliant
  - **requirement:** "Delivery cost must be under $250.00; otherwise, shipping costs must be rolled into the line-item price for the Vertex 25ei/CD Burner."
  - **retrieved context (shown to the model):** "Price and discount terms: Net 30 days from invoice date. No prompt-payment discount is offered. "Remit to" address: Same as the mailing address listed above. Representations and Certifications under FAR 52.212-3: Quantum Imaging Solutions, LLC's representations and certifications [...truncated]"
  - **retrieved context (shown to the model):** "From: sales@quantumimagingsolutions.com To: carlos.ortiz3@va.gov Subject: Quote for Solicitation 36C24126Q0731 P0003 - Sorna Vertex 25ei Platform/CD Burner Dear Mr. Ortiz, Quantum Imaging Solutions, LLC submits the following quote in response to Solicitation 36C24126Q0731 P0003 f [...truncated]"
  - **model's evidence (what it chose to cite):** "Shipping for this order is $150.00 and will be invoiced as a separate line item on the purchase order."
  - **model's reasoning:** The requirement specifies that delivery cost must be under $250.00. The bidder states that shipping is $150.00, which is under the $250.00 threshold, thus satisfying the requirement.
  - **expected evidence (true_verdicts.json):** "Shipping for this order is $150.00 and will be invoiced as a separate line item on the purchase order."
  - **expected reasoning:** Application states shipping of $150.00 (below the $250.00 threshold) will be invoiced as a separate line item, rather than rolled into the Vertex 25ei/CD Burner unit price as the requirement demands.

**False-issue rate** — mirror direction: the true verdict is `compliant` only, but the pipeline raised an issue anyway.
- rate: 13.3%

- `uei_provided_on_quote` — acceptable: ['compliant'], predicted: non_compliant
  - **requirement:** "The quoter must enter the Unique Entity Identifier annotation in the block with its name and address."
  - **retrieved context (shown to the model):** "From: sales@quantumimagingsolutions.com To: carlos.ortiz3@va.gov Subject: Quote for Solicitation 36C24126Q0731 P0003 - Sorna Vertex 25ei Platform/CD Burner Dear Mr. Ortiz, Quantum Imaging Solutions, LLC submits the following quote in response to Solicitation 36C24126Q0731 P0003 f [...truncated]"
  - **retrieved context (shown to the model):** "Price and discount terms: Net 30 days from invoice date. No prompt-payment discount is offered. "Remit to" address: Same as the mailing address listed above. Representations and Certifications under FAR 52.212-3: Quantum Imaging Solutions, LLC's representations and certifications [...truncated]"
  - **model's evidence (what it chose to cite):** "Quoter name, address, and telephone number: Quantum Imaging Solutions, LLC 615 Innovation Parkway Cary, NC 27513 Telephone: (919) 555-0286 Unique Entity Identifier: QIS7K4RTM392"
  - **model's reasoning:** The requirement states that the Unique Entity Identifier annotation must be entered in the block with the quoter's name and address. In the bidder's application, while the Unique Entity Identifier is provided, it is placed separately below the telephone number rather than integrated directly within the block containing the name and address.
  - **expected evidence (true_verdicts.json):** "Unique Entity Identifier: QIS7K4RTM392"
  - **expected reasoning:** UEI is explicitly entered and annotated as such.

- `far_52_212_3_reps_and_certs` — acceptable: ['compliant'], predicted: non_compliant
  - **requirement:** "Quote must include a completed copy of the representations and certifications under FAR 52.212-3."
  - **retrieved context (shown to the model):** "From: sales@quantumimagingsolutions.com To: carlos.ortiz3@va.gov Subject: Quote for Solicitation 36C24126Q0731 P0003 - Sorna Vertex 25ei Platform/CD Burner Dear Mr. Ortiz, Quantum Imaging Solutions, LLC submits the following quote in response to Solicitation 36C24126Q0731 P0003 f [...truncated]"
  - **retrieved context (shown to the model):** "Price and discount terms: Net 30 days from invoice date. No prompt-payment discount is offered. "Remit to" address: Same as the mailing address listed above. Representations and Certifications under FAR 52.212-3: Quantum Imaging Solutions, LLC's representations and certifications [...truncated]"
  - **model's evidence (what it chose to cite):** "Representations and Certifications under FAR 52.212-3: Quantum Imaging Solutions, LLC's representations and certifications under FAR 52.212-3 are current and up to date in SAM.gov as of the date of this quote."
  - **model's reasoning:** The requirement states that the quote must include a completed copy of the representations and certifications under FAR 52.212-3. The bidder's application only states that they are current and up to date in SAM.gov, rather than providing a completed copy of the representations and certifications in the quote.
  - **expected evidence (true_verdicts.json):** "Quantum Imaging Solutions, LLC's representations and certifications under FAR 52.212-3 are current and up to date in SAM.gov as of the date of this quote."
  - **expected reasoning:** Application states representations and certifications under FAR 52.212-3 are current in SAM.gov.

**Unscored** — split/merge groups excluded from the matrix above (still counted in the two rates above):
- group 1:
  - true `terms_and_conditions_acceptance_statement` — "To facilitate the award process, all quotes must include a statement regarding the terms and conditions herein as follows: "The terms and conditions in the solicitation are acceptable to be included in the award document without modification, deletion, or addition." OR "The terms and conditions in the solicitation are acceptable to be included in the award document with the exception, deletion, or addition of the following:" Quoters shall list exception(s) and rationale for the exception(s), if any." (acceptable: ['compliant'])
  - predicted [23ef7ab9] "All quotes must include a statement accepting the solicitation terms and conditions without modification, deletion, or addition." — verdict: compliant, citation: fuzzy match — worth a second look
  - predicted [319afa90] "Quoters shall list exception(s) and rationale for the exception(s), if any." — verdict: compliant
- group 2:
  - true `brand_name_no_substitutes` — "The quotations shall be brand name for the for Sorna Vertex 25ei & CD Burner listed in the Product Chart above and as described in detail in the combined synopsis solicitation, Intent to Compete/ RFQ as posted on Contract Opportunities starting on Page 1 (P1). ... No substitutions can be considered." (acceptable: ['compliant'])
  - predicted [51d4322f] "No substitutions can be considered." — verdict: compliant
  - predicted [b04d87d0] "The quotation must be for the Sorna Vertex 25ei & CD Burner brand name products as described in the Product Chart and Statement of Work." — verdict: compliant

## Evidence

**Citation-verified rate** (evidence-level): fraction of evidence quotes actually located in application.txt.
- rate: 100.0% (0 unverified of 43)

**Evidence recall**: does the expected evidence span (from `true_verdicts.json`) show up somewhere in the requirement's retrieved chunks, before the verdict step chose what to cite? Topics never extracted as a requirement are excluded — that failure is already counted by requirement recall above.
- recall: 100.0% (16/16)
- missed:
  - none
