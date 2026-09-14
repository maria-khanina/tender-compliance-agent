# Evaluation report

## Summary metrics

Machine-readable numbers for averaging across tenders -- every value here is explained in the sections below. `null` means the metric doesn't apply to this run (e.g. no verdict-only artifact present).

```json
{
  "requirement_recall": 0.9583,
  "requirement_recall_matched": 23,
  "requirement_recall_total": 24,
  "requirement_precision": 0.6842,
  "citation_verified_rate": 1.0,
  "is_mandatory_accuracy": 0.7826,
  "is_mandatory_scored": 23,
  "is_text_verifiable_accuracy": 0.9565,
  "is_text_verifiable_scored": 23,
  "verdict_clean_match_count": 21,
  "verdict_accuracy": 0.9524,
  "false_compliant_rate": 0.0455,
  "false_issue_rate": 0.0,
  "evidence_citation_verified_rate": 1.0,
  "evidence_recall": 1.0,
  "verdict_only_accuracy": 0.9565,
  "verdict_only_scored": 23
}
```

## Requirement recall

For each `true_requirements.json` topic, did the pipeline extract something whose tender.txt citation overlaps the true one? A pure text-offset check, not a judgment of meaning — see coverage flags below for extractions that are technically "found" but sloppy.

**Recall: 95.8% (23/24)**

**Missed** (1) — no overlapping predicted requirement at all. "chunk check" is a mechanical (no-LLM) re-chunking of the source document: whether this topic's matching text ever appeared whole in one chunk handed to the extraction model, or was split across chunks.
- true `nmr_certification_signed` — "The Contractor hereby certifies that it complies with the Non-Manufacturing Rule (NMR) as outlined by the U.S. Small Business Administration (SBA) regulations and the Federal Acquisition Regulation (FAR). By entering into this contract, the Contractor certifies that: ... Signature: _______________________ Name: ___________________________ Title: ____________________________ Date: ____________________________ Business Name: ____________________________"
    - **chunk check:** [17809:18076] whole, in chunk 15 -- the model saw this text intact; [19781:19964] whole, in chunk 16 -- the model saw this text intact

**Over-split** (2) — one true topic extracted as several separate predicted requirements:
- true `equal_product_identification_and_literature` — "(2) Clearly identify the item by— (i) Brand name, if any; and (ii) Make or model number; (3) Include descriptive literature such as illustrations, drawings, or a clear reference to previously furnished descriptive data or information available to the Contracting Officer; and (4) Clearly describe any modification the offeror plans to make in a product to make it conform to the solicitation requirements. Mark any descriptive material to clearly show the modification." split into 3 predicted requirements:
  - predicted [3b24b775] "Clearly identify the item by brand name, make, or model number." — verdict: compliant
  - predicted [714a7812] "Include descriptive literature such as illustrations, drawings, or clear reference to previously furnished descriptive data." — verdict: non_compliant
  - predicted [7578fc4a] "Clearly describe and mark any modification the offeror plans to make in a product to make it conform to the solicitation requirements." — verdict: non_compliant
- true `submission_deadline_and_channel` — "All offeror quotes for this solicitation must be received electronically through email no later than Friday, August 28th, 2026 10:00am PT. ... Offers shall be sent by email to Rochelle.Malveaux@va.gov" split into 2 predicted requirements:
  - predicted [35cedb52] "All offeror quotes must be received electronically through email no later than Friday, August 28th, 2026 10:00am PT." — verdict: insufficient_information
  - predicted [547a76d1] "Offers shall be sent by email to Rochelle.Malveaux@va.gov." — verdict: compliant

**Over-merge** (0) — one predicted requirement covering several distinct true topics:
- none

**Tangled** (0) — several true and several predicted requirements all overlapping at once:
- none

## Requirement precision

**Citation-verified rate** (hallucination check): fraction of predicted requirements whose citation was actually located in tender.txt (exactly or via fuzzy match).
- rate: 100.0%
- unverified:
  - none

**Classification precision**: fraction of predicted requirements that matched a true requirement.
- rate: 68.4%
- unexplained (12) — the model recognized these as requirements, but they don't match any true requirement. "closest true topic" is a mechanical (no-LLM) embedding-similarity lookup against every true topic's description; "dedup visibility" checks whether dedup's own cosine pre-filter would have clustered this candidate with whatever predicted requirement DID match that topic -- i.e. whether the dedup LLM call ever had a chance to compare them:
  - predicted [1e3a63cd] "The Contractor will supply the product of a small business manufacturer or processor, unless a waiver has been granted by the SBA."
    - **similarity check:** closest true topic: `small_or_large_business_designation` (cosine=0.67); vs matched predicted [3128c34c]: cosine=0.68 (>= dedup threshold 0.6) -> would likely have been clustered together and compared by the dedup LLM call
  - predicted [2868da47] "The Contractor qualifies as a small business under the SBA size standards."
    - **similarity check:** closest true topic: `small_or_large_business_designation` (cosine=0.69); vs matched predicted [3128c34c]: cosine=0.69 (>= dedup threshold 0.6) -> would likely have been clustered together and compared by the dedup LLM call
  - predicted [42bdf1a0] "The Contractor has made this certification at the time of submitting the offer in response to the solicitation."
    - **similarity check:** closest true topic: `nmr_certification_signed` (cosine=0.63); that true topic has no matched predicted requirement in this run, so there was nothing for dedup to compare it against
  - predicted [50a9aa4c] "The Contractor does not manufacture the products being supplied under this contract."
    - **similarity check:** closest true topic: `gray_market_verification` (cosine=0.62); vs matched predicted [30b2bf78]: cosine=0.59 (< dedup threshold 0.6) -> dedup's cosine pre-filter would NOT have clustered these -- the dedup LLM call never saw them side by side
  - predicted [7849fd9f] "The Contractor will flow down this certification requirement to any subcontractors where applicable."
    - **similarity check:** closest true topic: `nmr_certification_signed` (cosine=0.54); that true topic has no matched predicted requirement in this run, so there was nothing for dedup to compare it against
  - predicted [87552165] "The Contractor will not alter, modify, repackage, or rebrand the products supplied under this contract."
    - **similarity check:** closest true topic: `gray_market_verification` (cosine=0.61); vs matched predicted [30b2bf78]: cosine=0.58 (< dedup threshold 0.6) -> dedup's cosine pre-filter would NOT have clustered these -- the dedup LLM call never saw them side by side
  - predicted [99555047] "All software licensing, warranty, and service associated with medical supplies and equipment shall be in accordance with OEM terms and conditions."
    - **similarity check:** closest true topic: `authorized_distributor_letter` (cosine=0.59); vs matched predicted [c7416fbc]: cosine=0.77 (>= dedup threshold 0.6) -> would likely have been clustered together and compared by the dedup LLM call
  - predicted [9ae9cb7f] "The Contractor agrees to maintain and provide documentation that verifies compliance with the NMR, upon request by the Contracting Officer or the SBA."
    - **similarity check:** closest true topic: `nmr_certification_signed` (cosine=0.70); that true topic has no matched predicted requirement in this run, so there was nothing for dedup to compare it against
  - predicted [b58078e6] "The Contractor is primarily engaged in the retail or wholesale trade and normally supplies the type of product being provided."
    - **similarity check:** closest true topic: `small_or_large_business_designation` (cosine=0.58); vs matched predicted [3128c34c]: cosine=0.59 (< dedup threshold 0.6) -> dedup's cosine pre-filter would NOT have clustered these -- the dedup LLM call never saw them side by side
  - predicted [daa17053] "All information provided in this certification is accurate and truthful to the best of the Contractor’s knowledge and belief."
    - **similarity check:** closest true topic: `far_52_212_3_reps_and_certs` (cosine=0.56); vs matched predicted [934324be]: cosine=0.54 (< dedup threshold 0.6) -> dedup's cosine pre-filter would NOT have clustered these -- the dedup LLM call never saw them side by side
  - predicted [ede5f667] "Offers that include any items that are not determined as Brand Name or Equal shall result in an unacceptable offer, and the offeror shall provide the brand name product unless indicating an equal product is offered."
    - **similarity check:** closest true topic: `country_of_origin_specified` (cosine=0.69); vs matched predicted [dffb4f52]: cosine=0.66 (>= dedup threshold 0.6) -> would likely have been clustered together and compared by the dedup LLM call
  - predicted [f00d1e30] "The Delivery Timeframe shall be 30 Days ARO."
    - **similarity check:** closest true topic: `submission_deadline_and_channel` (cosine=0.62); vs matched predicted [35cedb52]: cosine=0.57 (< dedup threshold 0.6) -> dedup's cosine pre-filter would NOT have clustered these -- the dedup LLM call never saw them side by side

## Coverage flags

Clean 1:1 matches (recall counted them as found) whose citations don't fully overlap in length, split by which side is off. Over-split/over-merge/tangled matches are excluded here -- their predicted fragments are inherently partial by construction, already shown in the recall breakdown above.

**Requirements captured with extra text** (0) — the predicted citation is padded beyond the true one:
- none

**Requirements captured incompletely** (0) — the predicted citation misses part of the true one:
- none

## is_mandatory accuracy

For each clean or one-to-many match (tangled groups excluded — there's no single "one" to compare against), does `is_mandatory` agree with the true value? A one-to-many group counts as correct only if every member on the "many" side agrees with the "one".

**Accuracy: 78.3% (23 groups)**

Mismatched:
- true: `air_driven_high_speed_sterile_pathway`=True; predicted: `80415ea5`=False — "Air driven high speed (4-hole) with sterile irrigation through a sterile pathway"
- true: `detachable_waterline_system`=True; predicted: `4b4220e1`=False — "Detachable waterline system"
- true: `fits_midwest_4_hole_handpieces`=True; predicted: `a30f6bed`=False — "Fits Midwest 4 hole handpieces"
- true: `includes_two_8oz_autoclavable_bottles`=True; predicted: `0faa864e`=False — "Includes (2) 8 ounce autoclavables bottles"
- true: `autoclavable_tubing_sterile_pathway`=True; predicted: `67fd249d`=False — "Uses autoclavable tubing for sterile delivery pathway, eliminating possible waterline contamination."

## is_text_verifiable accuracy

For each clean or one-to-many match (tangled groups excluded), does `is_text_verifiable` agree with the true value (all-or-nothing on the "many" side, same rule as is_mandatory above)? A wrong `false` here means the pipeline skips verdict generation for a requirement that should get one.

**Accuracy: 95.7% (23 groups)**

Mismatched:
- true: `submission_deadline_and_channel`=False; predicted: `35cedb52`=True, `547a76d1`=True — "All offeror quotes for this solicitation must be received electronically through email no later than Friday, August 28th, 2026 10:00am PT. ... Offers shall be sent by email to Rochelle.Malveaux@va.gov"

## Verdict accuracy

The confusion matrix covers only clean 1:1 matches — split/merge groups have no single pair to plot, but still count in the two rates below.

Clean matches scored: 21

| true \ pipeline said | `compliant` | `non_compliant` | `contradictory` | `insufficient_information` |
|---|---|---|---|---|
| `compliant` | 14 | 0 | 0 | 0 |
| `non_compliant` | 1 | 3 | 0 | 0 |
| `contradictory` | 0 | 2 | 0 | 0 |
| `insufficient_information` | 0 | 0 | 0 | 1 |

**Mismatched clean matches** — every off-diagonal cell above, in full: the full context retrieved and shown to the model, what it chose to cite from that context, and its reasoning ("model's ..."), next to what `true_verdicts.json` expects ("expected ...").

- `buy_american_certificate` — acceptable: ['non_compliant'], predicted: compliant
  - **requirement:** "Product must comply with the Buy American Act, Trade Agreement Act, and all other relevant clauses found in the FAR and agency-specific regulations."
  - **retrieved context (shown to the model):** "We acknowledge and certify compliance with the Non-Manufacturing Rule as outlined by the U.S. Small Business Administration and the Federal Acquisition Regulation, including that DentaFlow Systems is primarily engaged in the wholesale trade of dental equipment and does not manufa [...truncated]"
  - **retrieved context (shown to the model):** "From: contracts@dentaflowsystems.com To: Rochelle.Malveaux@va.gov Subject: Quote for RFQ 36C2626Q1384 - AquaSept Handpieces or Equal Dear Ms. Malveaux, DentaFlow Systems, LLC is pleased to submit the following quote in response to solicitation 36C26226Q1384 for the AquaSept High [...truncated]"
  - **retrieved context (shown to the model):** "DentaFlow Systems does not hold a current FSS contract for this item. Attachment A, Columns F-K: Equivalent Brand: HydroClear Equivalent Nomenclature: HydroClear Pro 4H Waterline Delivery System Equivalent Part Number: HC-4H-2026 Equivalent Description Matching Salient Characteri [...truncated]"
  - **model's evidence (what it chose to cite):** "DentaFlow Systems' representations and certifications under FAR 52.212-3 are current and up to date in SAM.gov as of the date of this quote."
  - **model's evidence (what it chose to cite):** "DentaFlow Systems concurs with all terms, conditions, and provisions of this solicitation without exception."
  - **model's evidence (what it chose to cite):** "Buy American Certificate (FAR 52.225-2): DentaFlow Systems certifies that the offered HydroClear Pro 4H is a foreign end product, manufactured in Malaysia, and does not exceed 55% domestic content. No domestic end products or critical components are being offered under this line item."
  - **model's reasoning:** The bidder explicitly concurs with all terms and conditions of the solicitation without exception, certifies that their representations and certifications under FAR 52.212-3 are up to date in SAM.gov, and properly completes the required Buy American Certificate (FAR 52.225-2) for the foreign end product being supplied. Therefore, the requirement to comply with the Buy American Act, Trade Agreement Act, and relevant FAR and agency clauses is satisfied.
  - **expected evidence (true_verdicts.json):** "Buy American Certificate (FAR 52.225-2): DentaFlow Systems certifies that the offered HydroClear Pro 4H is a foreign end product, manufactured in Malaysia, and does not exceed 55% domestic content. No domestic end products or critical components are being offered under this line item."
  - **expected reasoning:** The certificate itself is filled out honestly and completely (foreign end product, Malaysia, does not exceed 55% domestic content) -- there is no missing paperwork and no contradiction. But item (e) requires the product itself to comply with the Buy American Act, and Malaysia is neither a domestic nor a TAA-designated-country origin, so the disclosed fact fails that substantive requirement, independent of how well the certificate form was completed.

**False-compliant rate** — dangerous direction: the true verdict requires an issue (anything but `compliant`), but every predicted verdict in the group is `compliant`.
- rate: 4.5%

- `buy_american_certificate` — acceptable: ['non_compliant'], predicted: compliant
  - **requirement:** "Product must comply with the Buy American Act, Trade Agreement Act, and all other relevant clauses found in the FAR and agency-specific regulations."
  - **retrieved context (shown to the model):** "We acknowledge and certify compliance with the Non-Manufacturing Rule as outlined by the U.S. Small Business Administration and the Federal Acquisition Regulation, including that DentaFlow Systems is primarily engaged in the wholesale trade of dental equipment and does not manufa [...truncated]"
  - **retrieved context (shown to the model):** "From: contracts@dentaflowsystems.com To: Rochelle.Malveaux@va.gov Subject: Quote for RFQ 36C2626Q1384 - AquaSept Handpieces or Equal Dear Ms. Malveaux, DentaFlow Systems, LLC is pleased to submit the following quote in response to solicitation 36C26226Q1384 for the AquaSept High [...truncated]"
  - **retrieved context (shown to the model):** "DentaFlow Systems does not hold a current FSS contract for this item. Attachment A, Columns F-K: Equivalent Brand: HydroClear Equivalent Nomenclature: HydroClear Pro 4H Waterline Delivery System Equivalent Part Number: HC-4H-2026 Equivalent Description Matching Salient Characteri [...truncated]"
  - **model's evidence (what it chose to cite):** "DentaFlow Systems' representations and certifications under FAR 52.212-3 are current and up to date in SAM.gov as of the date of this quote."
  - **model's evidence (what it chose to cite):** "DentaFlow Systems concurs with all terms, conditions, and provisions of this solicitation without exception."
  - **model's evidence (what it chose to cite):** "Buy American Certificate (FAR 52.225-2): DentaFlow Systems certifies that the offered HydroClear Pro 4H is a foreign end product, manufactured in Malaysia, and does not exceed 55% domestic content. No domestic end products or critical components are being offered under this line item."
  - **model's reasoning:** The bidder explicitly concurs with all terms and conditions of the solicitation without exception, certifies that their representations and certifications under FAR 52.212-3 are up to date in SAM.gov, and properly completes the required Buy American Certificate (FAR 52.225-2) for the foreign end product being supplied. Therefore, the requirement to comply with the Buy American Act, Trade Agreement Act, and relevant FAR and agency clauses is satisfied.
  - **expected evidence (true_verdicts.json):** "Buy American Certificate (FAR 52.225-2): DentaFlow Systems certifies that the offered HydroClear Pro 4H is a foreign end product, manufactured in Malaysia, and does not exceed 55% domestic content. No domestic end products or critical components are being offered under this line item."
  - **expected reasoning:** The certificate itself is filled out honestly and completely (foreign end product, Malaysia, does not exceed 55% domestic content) -- there is no missing paperwork and no contradiction. But item (e) requires the product itself to comply with the Buy American Act, and Malaysia is neither a domestic nor a TAA-designated-country origin, so the disclosed fact fails that substantive requirement, independent of how well the certificate form was completed.

**False-issue rate** — mirror direction: the true verdict is `compliant` only, but the pipeline raised an issue anyway.
- rate: 0.0%

- none

**Unscored** — split/merge groups excluded from the matrix above (still counted in the two rates above):
- group 1:
  - true `equal_product_identification_and_literature` — "(2) Clearly identify the item by— (i) Brand name, if any; and (ii) Make or model number; (3) Include descriptive literature such as illustrations, drawings, or a clear reference to previously furnished descriptive data or information available to the Contracting Officer; and (4) Clearly describe any modification the offeror plans to make in a product to make it conform to the solicitation requirements. Mark any descriptive material to clearly show the modification." (acceptable: ['non_compliant'])
  - predicted [3b24b775] "Clearly identify the item by brand name, make, or model number." — verdict: compliant
  - predicted [714a7812] "Include descriptive literature such as illustrations, drawings, or clear reference to previously furnished descriptive data." — verdict: non_compliant
  - predicted [7578fc4a] "Clearly describe and mark any modification the offeror plans to make in a product to make it conform to the solicitation requirements." — verdict: non_compliant

## Evidence

**Citation-verified rate** (evidence-level): fraction of evidence quotes actually located in application.txt.
- rate: 100.0% (0 unverified of 48)

**Evidence recall**: does the expected evidence span (from `true_verdicts.json`) show up somewhere in the requirement's retrieved chunks, before the verdict step chose what to cite? Topics never extracted as a requirement are excluded — that failure is already counted by requirement recall above.
- recall: 100.0% (20/20)
- missed:
  - none

## Verdict-only evaluation

Runs verdict generation directly on true_requirements.json's own text and citations against application.txt, bypassing requirement extraction and match-group sequencing entirely -- isolates whether generate_verdict, given a perfect requirement, makes the right call. Only mismatches are listed below.

**Accuracy: 95.7% (22/23)**

- `buy_american_certificate` — acceptable: ['non_compliant'], predicted: compliant
  - **requirement:** "Product must comply with the Buy American Act and Trade Agreements Act, and the quote must certify -- per the Buy American Certificate (FAR 52.225-2) -- whether each end product is a domestic or foreign end product, and whether foreign end products exceed 55% domestic content."
  - **retrieved context (shown to the model):** "We acknowledge and certify compliance with the Non-Manufacturing Rule as outlined by the U.S. Small Business Administration and the Federal Acquisition Regulation, including that DentaFlow Systems is primarily engaged in the wholesale trade of dental equipment and does not manufacture the products being supplied under this contract. (Signature block to be completed upon award.) DentaFlow Systems' representations and certifications under FAR 52.212-3 are current and up to date in SAM.gov as of the date of this quote. This quote is submitted via email in advance of the response deadline. Please contact us with any questions regarding this quote. Sincerely, Marcus Webb Contracts Manager DentaFlow Systems, LLC"
  - **retrieved context (shown to the model):** "From: contracts@dentaflowsystems.com To: Rochelle.Malveaux@va.gov Subject: Quote for RFQ 36C2626Q1384 - AquaSept Handpieces or Equal Dear Ms. Malveaux, DentaFlow Systems, LLC is pleased to submit the following quote in response to solicitation 36C26226Q1384 for the AquaSept High Speed Kit or Equal. Vendor Information: DentaFlow Systems, LLC, 4410 Corridor Park Blvd, Austin, TX 78744. SAM UEI: QK7RT2LM9XN4. DentaFlow Systems concurs with all terms, conditions, and provisions of this solicitation without exception. All items are quoted FOB Destination. Manufacturer: Veridian MedTech. Part Number: HC-4H-2026. DentaFlow Systems is an authorized distributor of Veridian MedTech's HydroClear product line, verified directly through the manufacturer's official partner program, with full OEM warranty and service backing. Sourcing and Availability: Due to current inventory constraints on this specific model, please note that this order may be fulfilled using units obtained through a secondary distribution network, which can include units originally allocated for other regional markets. We do not anticipate this affecting delivery timelines. Country of Origin: Malaysia (final assembly). Buy American Certificate (FAR 52.225-2): DentaFlow Systems certifies that the offered HydroClear Pro 4H is a foreign end product, manufactured in Malaysia, and does not exceed 55% domestic content. No domestic end products or critical components are being offered under this line item."
  - **retrieved context (shown to the model):** "DentaFlow Systems does not hold a current FSS contract for this item. Attachment A, Columns F-K: Equivalent Brand: HydroClear Equivalent Nomenclature: HydroClear Pro 4H Waterline Delivery System Equivalent Part Number: HC-4H-2026 Equivalent Description Matching Salient Characteristics: air-driven high-speed 4-hole handpiece system compatible with Midwest-style connections, with a sterile irrigation pathway and autoclavable components; see technical description below for full comparison. Country of Origin: Malaysia Quantity: 25 Technical Description: The HydroClear Pro 4H is an air-driven, high speed (4-hole) system fitting Midwest 4-hole handpieces, using autoclavable tubing for a sterile delivery pathway and (2) 8 ounce autoclavable bottles. The full unit is autoclavable to ensure sterility between uses, and it is designed to provide high-speed cutting power rivaling electric handpieces while maintaining precision and responsiveness. Irrigation is controlled with a simple instant on/off mechanism and no added footprint. Note: the HydroClear Pro 4H utilizes a fixed, non-detachable waterline routing integrated into the handpiece body, rather than a detachable waterline system."
  - **model's evidence (what it chose to cite):** "Buy American Certificate (FAR 52.225-2): DentaFlow Systems certifies that the offered HydroClear Pro 4H is a foreign end product, manufactured in Malaysia, and does not exceed 55% domestic content. No domestic end products or critical components are being offered under this line item."
  - **model's reasoning:** The bidder explicitly provided the Buy American Certificate (FAR 52.225-2) as required, identifying the product as a foreign end product and confirming it does not exceed 55% domestic content.
  - **expected evidence (true_verdicts.json):** "Buy American Certificate (FAR 52.225-2): DentaFlow Systems certifies that the offered HydroClear Pro 4H is a foreign end product, manufactured in Malaysia, and does not exceed 55% domestic content. No domestic end products or critical components are being offered under this line item."
  - **expected reasoning (true_verdicts.json):** The certificate itself is filled out honestly and completely (foreign end product, Malaysia, does not exceed 55% domestic content) -- there is no missing paperwork and no contradiction. But item (e) requires the product itself to comply with the Buy American Act, and Malaysia is neither a domestic nor a TAA-designated-country origin, so the disclosed fact fails that substantive requirement, independent of how well the certificate form was completed.
