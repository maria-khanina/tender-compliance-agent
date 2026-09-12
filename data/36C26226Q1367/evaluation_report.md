# Evaluation report

## Summary metrics

Machine-readable numbers for averaging across tenders -- every value here is explained in the sections below. `null` means the metric doesn't apply to this run (e.g. no verdict-only artifact present).

```json
{
  "requirement_recall": 1.0,
  "requirement_recall_matched": 14,
  "requirement_recall_total": 14,
  "requirement_precision": 0.5918,
  "citation_verified_rate": 1.0,
  "is_mandatory_accuracy": 0.6667,
  "is_mandatory_scored": 12,
  "is_text_verifiable_accuracy": 0.6667,
  "is_text_verifiable_scored": 12,
  "verdict_clean_match_count": 5,
  "verdict_accuracy": 1.0,
  "false_compliant_rate": 0.1667,
  "false_issue_rate": 0.0,
  "evidence_citation_verified_rate": 0.7407,
  "evidence_recall": 1.0,
  "verdict_only_accuracy": null,
  "verdict_only_scored": null
}
```

## Requirement recall

For each `true_requirements.json` topic, did the pipeline extract something whose tender.txt citation overlaps the true one? A pure text-offset check, not a judgment of meaning — see coverage flags below for extractions that are technically "found" but sloppy.

**Recall: 100.0% (14/14)**

**Missed** (0) — no overlapping predicted requirement at all:
- none

**Over-split** (3) — one true topic extracted as several separate predicted requirements:
- true `fob_destination_manufacturer_part_number` — "Items shall be FOB destination. Please specify offered item manufacturer and part number." split into 2 predicted requirements:
  - predicted [6041a2ce] "Please specify the offered item manufacturer and part number." — verdict: compliant
  - predicted [a6aac6b4] "Items shall be FOB destination." — verdict: compliant
- true `or_equal_submission_requirements` — "Offerors shall fill out columns “F-K” of Attachment A conforming to requirements stated by the salient characteristics which includes exact measurements and the instructions below. ... (b) To be considered for award, offers of “equal” products, including “equal” products of the brand name manufacturer, must— (1) Meet the salient physical, functional, or performance characteristic specified in this solicitation; (2) Clearly identify the item by— (i) Brand name, if any; and (ii) Make or model number; (3) Include descriptive literature such as illustrations, drawings, or a clear reference to previously furnished descriptive data or information available to the Contracting Officer; and (4) Clearly describe any modification the offeror plans to make in a product to make it conform to the solicitation requirements. Mark any descriptive material to clearly show the modification." split into 5 predicted requirements:
  - predicted [127f2b3b] "(3) Include descriptive literature such as illustrations, drawings, or a clear reference to previously furnished descriptive data or information available to the Contracting Officer; and" — not verifiable by text
  - predicted [693e3f30] "Clearly describe any modification the offeror plans to make in a product to make it conform to the solicitation requirements, and mark any descriptive material to clearly show the modification." — verdict: compliant
  - predicted [a2a86ac8] "To be considered for award, offers of equal products must clearly identify the item by brand name, make, or model number." — verdict: compliant, citation: fuzzy match — worth a second look
  - predicted [c5ad1be1] "Offerors shall fill out columns “F-K” of Attachment A conforming to requirements stated by the salient characteristics which includes exact measurements and the instructions below." — verdict: insufficient_information
  - predicted [e75d2517] "Offeror quotations and offers of equal products must demonstrate and meet the salient physical, functional, or performance characteristics specified in this solicitation to be considered for award and responsive." — verdict: insufficient_information, citation: fuzzy match — worth a second look
- true `submission_deadline_and_channel` — "All offeror quotes for this solicitation must be received electronically through email no later than Thursday, August 27th, 2026 9:00am PT. Ensure to reference solicitation number [36C26226Q1367] within subject line of the email. Any offeror quotes received after the prescribed date/time shall be considered non-responsive and will not be considered for award. ... Offers shall be sent by email to Rochelle.Malveaux@va.gov" split into 3 predicted requirements:
  - predicted [70550ba3] "All offeror quotes for this solicitation must be received electronically through email no later than Thursday, August 27th, 2026 9:00am PT." — not verifiable by text
  - predicted [a5bace5c] "Ensure to reference solicitation number [36C26226Q1367] within subject line of the email." — not verifiable by text
  - predicted [d0d8ba6f] "Offers shall be sent by email to Rochelle.Malveaux@va.gov" — not verifiable by text

**Over-merge** (0) — one predicted requirement covering several distinct true topics:
- none

**Tangled** (1) — several true and several predicted requirements all overlapping at once:
- tangle of 2 true and 10 predicted requirements, all overlapping — needs manual untangling:
  - true `buy_american_certificate_completed` — "(a)(1) The Offeror certifies that each end product, except those listed in paragraph (b) of this provision, is a domestic end product and that each domestic end product listed in paragraph (c) of this provision contains a critical component. (2) The Offeror shall list as foreign end products those end products manufactured in the United States that do not qualify as domestic end products. For those foreign end products that do not consist wholly or predominantly of iron or steel or a combination of both, the Offeror shall also indicate whether these foreign end products exceed 55 percent domestic content, except for those that are COTS items. If the percentage of the domestic content is unknown, select “no”. (3) The Offeror shall separately list the line item numbers of domestic end products that contain a critical component (see FAR 25.105). (4) The terms “commercially available off-the-shelf (COTS) item,” “critical component,” "domestic end product," "end product," and "foreign end product" are defined in the clause of this solicitation entitled "Buy American-Supplies." Line Item No. Country of Origin Exceeds 55% domestic content (yes/no) ______________ _________________ _________________ ______________ _________________ _________________ ______________ _________________ _________________ (b)Foreign End Products: (b)[List as necessary] (c) Domestic end products containing a critical component: Line Item No. ___ [List as necessary]"
  - true `nmr_certification_signed` — "Non-Manufacturing Rule (NMR) Certification Clause The Contractor hereby certifies that it complies with the Non-Manufacturing Rule (NMR) as outlined by the U.S. Small Business Administration (SBA) regulations and the Federal Acquisition Regulation (FAR). By entering into this contract, the Contractor certifies that: Small Business Status: The Contractor qualifies as a small business under the SBA size standards. Non-Manufacturer Status: The Contractor is primarily engaged in the retail or wholesale trade and normally supplies the type of product being provided in this contract. The Contractor does not manufacture the products being supplied under this contract. Source of Supply: The Contractor will supply the product of a small business manufacturer or processor, unless a waiver of this requirement has been granted by the SBA. The Echo Bed Cardiac Imaging Table falls under medical ultrasound equipment and accessories, which are covered in an NMR class waiver for Electromedical Apparatus Manufacturing under NAICS code 334510 posted in the Federal Register on 12/20/2007 under Register Notice number 72 FedReg 72433. The products supplied will be manufactured or produced in the United States, unless an exception is permitted by applicable regulations. Documentation and Compliance: The Contractor agrees to maintain and provide documentation that verifies compliance with the NMR, upon request by the Contracting Officer or the SBA. The Contractor will flow down this certification requirement to any subcontractors where applicable. No Alteration of Goods: The Contractor will not alter, modify, repackage, or rebrand the products supplied under this contract. Timeliness and Accuracy: The Contractor has made this certification at the time of submitting the offer in response to the solicitation. All information provided in this certification is accurate and truthful to the best of the Contractor’s knowledge and belief. Consequences of Non-Compliance: The Contractor acknowledges that failure to comply with this certification may result in termination of the contract, debarment, suspension, or other legal action as deemed appropriate by the Contracting Officer or SBA. Signature: _______________________ Name: ___________________________ Title: ____________________________ Date: ____________________________ Business Name: ____________________________"
  - predicted [1ce55394] "The contractor shall deliver domestic end products unless specified otherwise, certify compliance with domestic content and critical component requirements, list foreign end products or domestic end products containing critical components, and indicate domestic content percentages where applicable." — verdict: contradictory
  - predicted [3efcbe08] "By entering into this contract, the Contractor certifies that: ... The Contractor does not manufacture the products being supplied under this contract." — not verifiable by text
  - predicted [4274b404] "The Contractor will not alter, modify, repackage, or rebrand the products supplied under this contract." — not verifiable by text
  - predicted [52512c94] "Signature: _______________________ Name: ___________________________ Title: ____________________________ Date: ____________________________ Business Name: ____________________________" — verdict: non_compliant
  - predicted [698da687] "If the percentage of the domestic content is unknown, select “no”." — verdict: compliant
  - predicted [8b2695d3] "The Contractor certifies that it will supply the product of a small business manufacturer or processor upon entering into this contract, unless a waiver has been granted by the SBA." — verdict: insufficient_information
  - predicted [bdab2b7d] "The Contractor will flow down this certification requirement to any subcontractors where applicable." — not verifiable by text
  - predicted [c5de44f7] "By entering into this contract, the Contractor certifies that: ... The Contractor is primarily engaged in the retail or wholesale trade and normally supplies the type of product being provided in this contract." — not verifiable by text
  - predicted [d01abeef] "The Contractor agrees to maintain and provide documentation that verifies compliance with the NMR, upon request by the Contracting Officer or the SBA." — not verifiable by text
  - predicted [ffbf2da4] "The Contractor certifies that it qualifies as a small business under the SBA size standards upon entering into this contract." — verdict: insufficient_information

## Requirement precision

**Citation-verified rate** (hallucination check): fraction of predicted requirements whose citation was actually located in tender.txt (exactly or via fuzzy match).
- rate: 100.0%
- unverified:
  - none

**Classification precision**: fraction of predicted requirements that matched a true requirement.
- rate: 59.2%
- unexplained (20) — the model recognized these as requirements, but they don't match any true requirement:
  - predicted [04765bab] "If providing an equivalent product, offerors shall either provide information regarding how their product meets the salient characteristics or state where in the offeror's overall submission that information can be found."
  - predicted [062eb129] "Echocardiography examination tables must have the following features- ... ELECTRIC LOCKING CASTERS"
  - predicted [0f469d7b] "No remanufactures or gray market items will be acceptable."
  - predicted [1e91428f] "Echocardiography examination tables must have the following features- ... Height adjustment: Adjustable range (e.g., 24"–34" on many models) for optimal sonographer access"
  - predicted [2a0abf75] "The offeror shall provide the brand name product referenced in the solicitation."
  - predicted [3b7465a8] "Vendor shall be an OEM, authorized dealer, authorized distributor or authorized reseller for the proposed medical supplies, medical equipment and/or services contracts for maintenance of medical equipment (i.e. replacement parts), verified by an authorization letter or other documents from the OEM, such that the OEM’s warranty and service are provided and maintained by the OEM."
  - predicted [3e6479ff] "Echocardiography examination tables must feature Trendelenburg and Reverse Trendelenburg positioning with adjustable tilt for specific imaging angles (e.g., +/-15°), or Trendelenburg capability on certain models for enhanced imaging access."
  - predicted [460c119c] "The cost of its components mined, produced, or manufactured in the United States exceeds 60 percent of the cost of all its components, except that the percentage will be 65 percent for items delivered in calendar years 2024 through 2028 and 75 percent for items delivered starting in calendar year 2029."
  - predicted [5858d4a2] "The Delivery Timeframe shall be 30 Days ARO."
  - predicted [5e299605] "All software licensing, warranty and service associated with the medical supplies, medical equipment and/or services contracts for maintenance of medical equipment shall be in accordance with the OEM terms and conditions."
  - predicted [5e3dce66] "Echocardiography examination tables must feature an open apical window with a large cardiac scanning cutout (e.g., 9.5" W x 15.75" L) for unobstructed imaging."
  - predicted [5fd6f6a4] "Echocardiography examination tables must have the following features- ... 4 FLEXIBLE HAND CONTROL STORAGE LOOPS"
  - predicted [6e34f1d7] "Echocardiography examination tables must have an appropriate patient weight and bariatric-rated load capacity (supporting up to 750 lbs on standard models and up to 1,250 lbs with a 500 lb powered lift on bariatric-rated versions for stability and strength during complex exams)."
  - predicted [819b5319] "Echocardiography examination tables must include dual rapid release imaging drop sections or walk-away models for left, right, or multi-access scanning."
  - predicted [aa192d35] "Echocardiography examination tables must feature an electrically adjustable patient back support / Fowler backrest (positionable from 0° to at least 65° or up to 80° depending on variants) to support natural body extension and reduce strain."
  - predicted [bf8a231e] "Echocardiography examination tables must feature a standard 14" x 14" drop section to reduce repositioning during exams."
  - predicted [c0070d58] "Echocardiography examination tables must have the following features- ... PATIENT SURFACE FOOTPRINT 30"Wx83"L"
  - predicted [cca36642] "Submissions to this solicitation must show clear, compelling and convincing evidence that equal-to items meet all the salient characteristics (see Attachment A and B)."
  - predicted [f60d3a9f] "Echocardiography examination tables must have the following features- ... ADA-compliant low-entry height: Entry heights from 17" to 19" (or 19"–37" on some models) to accommodate wheelchair transfers and patients with mobility challenges"
  - predicted [f9ab94a3] "Drop-down cushion that releases from either side for barrier-free access"

## Coverage flags

Clean 1:1 matches (recall counted them as found) whose citations don't fully overlap in length, split by which side is off. Over-split/over-merge/tangled matches are excluded here -- their predicted fragments are inherently partial by construction, already shown in the recall breakdown above.

**Requirements captured with extra text** (0) — the predicted citation is padded beyond the true one:
- none

**Requirements captured incompletely** (0) — the predicted citation misses part of the true one:
- none

## is_mandatory accuracy

For each clean or one-to-many match (tangled groups excluded — there's no single "one" to compare against), does `is_mandatory` agree with the true value? A one-to-many group counts as correct only if every member on the "many" side agrees with the "one".

**Accuracy: 66.7% (12 groups)**

Mismatched:
- true: `fob_destination_manufacturer_part_number`=True; predicted: `6041a2ce`=False, `a6aac6b4`=True — "Items shall be FOB destination. Please specify offered item manufacturer and part number."
- true: `country_of_origin_disclosure`=True; predicted: `1a6b2fef`=False — "Please include a Country of Origin for the items being offered (see column A)"
- true: `fss_contract_listing`=False; predicted: `d9433d87`=True — "All items must be listed on FSS contract if vendor is an FSS contract holder: please list number and expiration date if applicable"
- true: `or_equal_submission_requirements`=True; predicted: `127f2b3b`=False, `693e3f30`=True, `a2a86ac8`=True, `c5ad1be1`=True, `e75d2517`=True — "Offerors shall fill out columns “F-K” of Attachment A conforming to requirements stated by the salient characteristics which includes exact measurements and the instructions below. ... (b) To be considered for award, offers of “equal” products, including “equal” products of the brand name manufacturer, must— (1) Meet the salient physical, functional, or performance characteristic specified in this solicitation; (2) Clearly identify the item by— (i) Brand name, if any; and (ii) Make or model number; (3) Include descriptive literature such as illustrations, drawings, or a clear reference to previously furnished descriptive data or information available to the Contracting Officer; and (4) Clearly describe any modification the offeror plans to make in a product to make it conform to the solicitation requirements. Mark any descriptive material to clearly show the modification."

## is_text_verifiable accuracy

For each clean or one-to-many match (tangled groups excluded), does `is_text_verifiable` agree with the true value (all-or-nothing on the "many" side, same rule as is_mandatory above)? A wrong `false` here means the pipeline skips verdict generation for a requirement that should get one.

**Accuracy: 66.7% (12 groups)**

Mismatched:
- true: `sam_uei_vendor_info`=True; predicted: `e4ac5a3e`=False — "Vendor Information with SAM UEI."
- true: `fss_contract_listing`=True; predicted: `d9433d87`=False — "All items must be listed on FSS contract if vendor is an FSS contract holder: please list number and expiration date if applicable"
- true: `or_equal_submission_requirements`=True; predicted: `127f2b3b`=False, `693e3f30`=True, `a2a86ac8`=True, `c5ad1be1`=True, `e75d2517`=True — "Offerors shall fill out columns “F-K” of Attachment A conforming to requirements stated by the salient characteristics which includes exact measurements and the instructions below. ... (b) To be considered for award, offers of “equal” products, including “equal” products of the brand name manufacturer, must— (1) Meet the salient physical, functional, or performance characteristic specified in this solicitation; (2) Clearly identify the item by— (i) Brand name, if any; and (ii) Make or model number; (3) Include descriptive literature such as illustrations, drawings, or a clear reference to previously furnished descriptive data or information available to the Contracting Officer; and (4) Clearly describe any modification the offeror plans to make in a product to make it conform to the solicitation requirements. Mark any descriptive material to clearly show the modification."
- true: `far_52_212_3_reps_and_certs`=True; predicted: `6a1cd3b4`=False — "Must include a completed copy of the provision at 52.212-3 -- Offeror Representations and Certifications -- Commercial Items, with this solicitation or ensure SAM.gov is updated with current information."

## Verdict accuracy

The confusion matrix covers only clean 1:1 matches — split/merge groups have no single pair to plot, but still count in the two rates below.

Clean matches scored: 5

| true \ pipeline said | `compliant` | `non_compliant` | `contradictory` | `insufficient_information` |
|---|---|---|---|---|
| `compliant` | 2 | 0 | 0 | 0 |
| `non_compliant` | 0 | 2 | 0 | 0 |
| `contradictory` | 0 | 0 | 1 | 0 |
| `insufficient_information` | 0 | 0 | 0 | 0 |

Why some rows are empty:
- `insufficient_information` row is empty: true `buy_american_certificate_completed` — tangled match — no single pair to plot
- `insufficient_information` row is empty: true `nmr_certification_signed` — tangled match — no single pair to plot

**Mismatched clean matches** — every off-diagonal cell above, in full: the full context retrieved and shown to the model, what it chose to cite from that context, and its reasoning ("model's ..."), next to what `true_verdicts.json` expects ("expected ...").

- none

**False-compliant rate** — dangerous direction: the true verdict requires an issue (anything but `compliant`), but every predicted verdict in the group is `compliant`.
- rate: 16.7%

- true `fob_destination_manufacturer_part_number` — "Items shall be FOB destination. Please specify offered item manufacturer and part number." (acceptable: ['non_compliant'])
    - **expected evidence (true_verdicts.json):** "Item offered: SonoRest CV-200 Cardiac Imaging Table, manufactured by Apex Medical Positioning Corp. FOB Destination: Yes."
    - **expected reasoning:** Application names the manufacturer and confirms FOB destination, but never states a manufacturer part number for the SonoRest CV-200.
  - predicted [6041a2ce] "Please specify the offered item manufacturer and part number." — verdict: compliant
    - **requirement:** "Please specify the offered item manufacturer and part number."
    - **retrieved context (shown to the model):** "From: quotes@summitdiagnosticequip.com To: Rochelle.Malveaux@va.gov Subject: Quote for Solicitation 36C26226Q1367 - Echo Bed Cardiac Imaging Table or Equal Dear Ms. Malveaux, Summit Diagnostic Equipment, LLC is pleased to submit the following quote in response to Solicitation 36C26226Q1367. Vendor Information: Summit Diagnostic Equipment, LLC 4420 Corbin Street Dallas, TX 75247 SAM UEI: QK7M2XH9RT84 Terms and Conditions: Summit Diagnostic Equipment, LLC concurs with all terms, conditions, and provisions of this solicitation. Item offered: SonoRest CV-200 Cardiac Imaging Table, manufactured by Apex Medical Positioning Corp. FOB Destination: Yes. Authorized Distributor status: Summit Diagnostic Equipment, LLC is an authorized reseller of Apex Medical Positioning Corp. products. The formal Authorized Distributor Letter will be provided upon request after contract award. Country of Origin: The SonoRest CV-200 is manufactured in Kuala Lumpur, Malaysia. Buy American Certification: Summit Diagnostic Equipment, LLC certifies full compliance with the Buy American Act and Trade Agreements Act for all items in this quote. All components of the SonoRest CV-200 are proudly Made in the USA, supporting full compliance with the Buy American Act."
    - **retrieved context (shown to the model):** "All components of the SonoRest CV-200 are proudly Made in the USA, supporting full compliance with the Buy American Act. Gray Market Verification: Summit Diagnostic Equipment, LLC is an authorized reseller of Apex Medical Positioning Corp. equipment, confirmed via the attached authorization documentation, and does not source or distribute any gray market goods. FSS Contract Status: Summit Diagnostic Equipment, LLC does not currently hold a Federal Supply Schedule (FSS) contract. Or-Equal Submission: We are offering the SonoRest CV-200 as an equal to the MPI Echo Bed Cardiac Imaging Table (EB924). The SonoRest CV-200 is a comparable cardiac imaging table suitable for echocardiography procedures. FAR 52.212-3 Representations and Certifications: Summit Diagnostic Equipment, LLC's representations and certifications under FAR 52.212-3 are current and up to date in SAM.gov. Non-Manufacturing Rule Certification: Summit Diagnostic Equipment, LLC maintains an executed Non-Manufacturing Rule certification on file with our corporate compliance department. Delivery: Summit Diagnostic Equipment, LLC can meet the 30-day ARO delivery timeframe to VA Greater Los Angeles Healthcare System. Please contact us with any questions regarding this quote. Sincerely, Marcus Feldman Contracts Manager Summit Diagnostic Equipment, LLC"
    - **model's evidence (what it chose to cite):** "Item offered: SonoRest CV-200 Cardiac Imaging Table, manufactured by Apex Medical Positioning Corp."
    - **model's reasoning:** The bidder clearly specifies both the manufacturer (Apex Medical Positioning Corp.) and the part number/item name (SonoRest CV-200 Cardiac Imaging Table), thereby satisfying the requirement.
  - predicted [a6aac6b4] "Items shall be FOB destination." — verdict: compliant
    - **requirement:** "Items shall be FOB destination."
    - **retrieved context (shown to the model):** "From: quotes@summitdiagnosticequip.com To: Rochelle.Malveaux@va.gov Subject: Quote for Solicitation 36C26226Q1367 - Echo Bed Cardiac Imaging Table or Equal Dear Ms. Malveaux, Summit Diagnostic Equipment, LLC is pleased to submit the following quote in response to Solicitation 36C26226Q1367. Vendor Information: Summit Diagnostic Equipment, LLC 4420 Corbin Street Dallas, TX 75247 SAM UEI: QK7M2XH9RT84 Terms and Conditions: Summit Diagnostic Equipment, LLC concurs with all terms, conditions, and provisions of this solicitation. Item offered: SonoRest CV-200 Cardiac Imaging Table, manufactured by Apex Medical Positioning Corp. FOB Destination: Yes. Authorized Distributor status: Summit Diagnostic Equipment, LLC is an authorized reseller of Apex Medical Positioning Corp. products. The formal Authorized Distributor Letter will be provided upon request after contract award. Country of Origin: The SonoRest CV-200 is manufactured in Kuala Lumpur, Malaysia. Buy American Certification: Summit Diagnostic Equipment, LLC certifies full compliance with the Buy American Act and Trade Agreements Act for all items in this quote. All components of the SonoRest CV-200 are proudly Made in the USA, supporting full compliance with the Buy American Act."
    - **retrieved context (shown to the model):** "All components of the SonoRest CV-200 are proudly Made in the USA, supporting full compliance with the Buy American Act. Gray Market Verification: Summit Diagnostic Equipment, LLC is an authorized reseller of Apex Medical Positioning Corp. equipment, confirmed via the attached authorization documentation, and does not source or distribute any gray market goods. FSS Contract Status: Summit Diagnostic Equipment, LLC does not currently hold a Federal Supply Schedule (FSS) contract. Or-Equal Submission: We are offering the SonoRest CV-200 as an equal to the MPI Echo Bed Cardiac Imaging Table (EB924). The SonoRest CV-200 is a comparable cardiac imaging table suitable for echocardiography procedures. FAR 52.212-3 Representations and Certifications: Summit Diagnostic Equipment, LLC's representations and certifications under FAR 52.212-3 are current and up to date in SAM.gov. Non-Manufacturing Rule Certification: Summit Diagnostic Equipment, LLC maintains an executed Non-Manufacturing Rule certification on file with our corporate compliance department. Delivery: Summit Diagnostic Equipment, LLC can meet the 30-day ARO delivery timeframe to VA Greater Los Angeles Healthcare System. Please contact us with any questions regarding this quote. Sincerely, Marcus Feldman Contracts Manager Summit Diagnostic Equipment, LLC"
    - **model's evidence (what it chose to cite):** "Item offered: SonoRest CV-200 Cardiac Imaging Table, manufactured by Apex Medical Positioning Corp. FOB Destination: Yes."
    - **model's reasoning:** The bidder explicitly states "FOB Destination: Yes" in their quote, which directly satisfies the requirement that items shall be FOB destination.

**False-issue rate** — mirror direction: the true verdict is `compliant` only, but the pipeline raised an issue anyway.
- rate: 0.0%

- none

**Unscored** — split/merge groups excluded from the matrix above (still counted in the two rates above):
- group 1:
  - true `fob_destination_manufacturer_part_number` — "Items shall be FOB destination. Please specify offered item manufacturer and part number." (acceptable: ['non_compliant'])
  - predicted [6041a2ce] "Please specify the offered item manufacturer and part number." — verdict: compliant
  - predicted [a6aac6b4] "Items shall be FOB destination." — verdict: compliant

## Evidence

**Citation-verified rate** (evidence-level): fraction of evidence quotes actually located in application.txt.
- rate: 74.1% (7 unverified of 27)

**Evidence recall**: does the expected evidence span (from `true_verdicts.json`) show up somewhere in the requirement's retrieved chunks, before the verdict step chose what to cite? Topics never extracted as a requirement are excluded — that failure is already counted by requirement recall above.
- recall: 100.0% (11/11)
- missed:
  - none
