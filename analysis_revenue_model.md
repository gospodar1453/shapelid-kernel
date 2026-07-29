# Shapelid Revenue Model Analysis & Strategic Design

**Date:** July 2026  
**Target Market:** Turkey (Manufacturing Marketplace connecting custom-parts customers with a network of manufacturers)  
**Base Exchange Rate:** 1 USD = 47.16 TRY (Standardized based on TCMB Central Bank rates and the Shapelid Geometry Kernel operational buffer of 4.0%)

This document details the strategic design, ranking, and modeling of the revenue streams for **Shapelid**. By moving toward a hybrid **SaaS-enabled Marketplace** using a **Manufacturer of Record (MoR)** structure, Shapelid can align transaction incentives, secure recurring revenue, and establish defensible barriers to entry in Turkey's massive manufacturing sector.

---

## Executive Summary

Shapelid operates in a unique sweet spot. Turkey is Europe's primary nearshoring and manufacturing hub, with over **4,124 qualified manufacturer leads** already in Shapelid's database (targeting 20,000–50,000 suppliers). 

To monetize this high-value, two-sided market, the platform will utilize:
1. **Manufacturer of Record (MoR) Transaction Model:** Customers buy directly from Shapelid, which takes liability, guarantees quality (QA), and streamlines billing (one supplier to onboard for the buyer).
2. **Dynamic Pricing Engine Margins:** Automatic quoting via the *Shapelid Geometry Kernel* built with an integrated take-rate (currently 28% default).
3. **Dual-Sided Subscription Tiers:** Adding high-margin SaaS recurring revenues (Pro/Enterprise packages for both manufacturers and customers) to accelerate payment terms, offer volume rebates, and provide advanced tooling.

---

## 1. Revenue Stream Options: Ranked by Feasibility & Impact

The 12 potential revenue streams for Shapelid are evaluated below, ranked from highest to lowest feasibility and impact:

### 1. Transaction Take-Rate / Margin (MoR Model)
* **Rank:** 1
* **Impact:** Critical (80% of total revenue)
* **Feasibility:** Maximum (Already integrated into the Geometry Kernel)
* **Description:** Shapelid acts as the Manufacturer of Record. The Kernel Pricing Engine quotes the customer a final price that incorporates a dynamic take-rate (average 22% - 35% depending on technology). The partner network is presented with the remaining payout (the supplier price).
* **Why it works:** Corporate buyers do not want to onboard 10,000 micro-workshops; they onboard Shapelid. Shapelid manages the billing, liability, and NDAs, capturing a large gross margin without holding inventory.

### 2. Subscription Tiers for Manufacturers
* **Rank:** 2
* **Impact:** High (Steady monthly recurring revenue - MRR)
* **Feasibility:** High
* **Description:** SaaS tiers for manufacturers. Free tier receives jobs with standard payout terms (Net-45). Paid tiers (Pro / Enterprise) unlock **Net-15 or Next-Day payouts**, higher priority for jobs, reduced take-rates, and advanced analytical tools.
* **Why it works:** Cash flow is the #1 pain point for Turkish SMEs. Manufacturers will happily pay a recurring fee (e.g., 2,500 TRY/month) to receive next-day or weekly payouts, which provides Shapelid with predictable SaaS income and massive float capital.

### 3. Subscription Tiers for Customers (B2B SaaS)
* **Rank:** 3
* **Impact:** High (Locks in procurement volume)
* **Feasibility:** High
* **Description:** SaaS subscription packages for corporate customers and engineering teams.
* **Why it works:** Unlocks premium features such as dedicated QA testing, custom NDAs, API access to ERP systems, priority production slots, and volume-based margin discounts (e.g., Kernel dynamic margin capped at 18-20%).

### 4. Quality Assurance & Material Verification Fees
* **Rank:** 4
* **Impact:** Medium-High
* **Feasibility:** High (Operationally feasible through in-house lab or certified network)
* **Description:** charging customers flat or percentage-based fees for specialized certifications (e.g., CoC, AS9100, Material Test Reports (MTR), 3D scanning measurement reports).
* **Why it works:** Aerospace, defense, and automotive buyers *require* verification. These fees are easily added as options in the check-out screen and processed automatically by the pricing engine.

### 5. Design for Manufacturability (DFM) & Consultative Engineering
* **Rank:** 5
* **Impact:** Medium
* **Feasibility:** High (Utilizes in-house engineer or contract experts)
* **Description:** Offering expert manual design review, weight optimization, or CNC toolpath planning for CAD files that trigger "manual quote" warnings in the pricing engine.
* **Why it works:** Many engineers upload designs that cannot be physically machined without modifications. Shapelid can offer "1-click engineer assist" for a flat fee.

### 6. API & Integration Access Fees
* **Rank:** 6
* **Impact:** Medium
* **Feasibility:** Medium (Requires robust external API documentation)
* **Description:** Charging large B2B enterprise customers for direct API integrations into their CAD (SolidWorks, Fusion360) or ERP (SAP, ERP5) systems for instant internal purchasing.
* **Why it works:** Increases platform stickiness and integrates Shapelid directly into the customer's daily procurement workflow.

### 7. White-Label or Custom Enterprise Solutions
* **Rank:** 7
* **Impact:** Medium
* **Feasibility:** Low-Medium (Requires significant engineering overhead)
* **Description:** Licensing the Shapelid Geometry Kernel and portal to large OEM manufacturers to manage their internal supplier networks.
* **Why it works:** High-ticket, long-sale B2B software contracts, but distracts from building the core marketplace liquidity. Highly valuable in the long term.

### 8. Escrow / Split Payment Fees
* **Rank:** 8
* **Impact:** Low (Included in base margin)
* **Feasibility:** High (PayTR Marketplace native capability)
* **Description:** Charging a small processing fee for splitting payments or keeping funds secure.
* **Why it works:** In Turkey, this is best bundled into the overall transaction commission rather than charged as an extra line-item to avoid fee-fatigue.

### 9. Shipping & Transit Insurance
* **Rank:** 9
* **Impact:** Low
* **Feasibility:** High (Integrated with logistics partners like Yurtiçi Kargo or DHL)
* **Description:** Automatic opt-in shipping insurance and secure packaging fees.
* **Why it works:** High-value custom parts (e.g., aerospace titanium components) are highly fragile. Small margins can be added here.

### 10. Industry Data & Analytics Packages
* **Rank:** 10
* **Impact:** Low
* **Feasibility:** Medium-Low
* **Description:** Selling aggregated, anonymized pricing and demand trends to raw material suppliers or enterprise buyers.
* **Why it works:** Secondary revenue stream only viable after reaching hundreds of thousands of monthly transactions.

### 11. Premium Placement & Manufacturer Advertising
* **Rank:** 11
* **Impact:** Low (Potential negative impact on marketplace quality)
* **Feasibility:** High
* **Description:** Allowing manufacturers to bid for featured status or advertisement on the directory.
* **Why it works:** **Not recommended.** In an MoR model, the platform chooses the supplier dynamically to guarantee quality and cost optimization. Showing "featured" suppliers to customers violates the MoR black-box security and introduces supplier bypass risk (leakage).

### 12. Listing Fees for Manufacturers
* **Rank:** 12
* **Impact:** Negative (Kills liquidity)
* **Feasibility:** High
* **Description:** Charging manufacturers to create a profile.
* **Why it works:** **Strongly discouraged.** Introducing listing fees creates extreme friction for suppliers, making it impossible to scale the database from 4,124 to the targeted 20,000–50,000. Onboarding must remain 100% free.

---

## 2. Two-Sided Pricing Strategy & The "Chicken-and-Egg" Solution

Marketplaces face the perpetual risk of starvation: no customers without manufacturers, and no manufacturers without customers. 

### Solving the Liquidity Dilemma for Shapelid:
The **Manufacturer of Record (MoR)** model elegantly bypasses this obstacle. 

```
  ┌────────────────────────────────────────────────────────────┐
  │                         SHAPELID                           │
  │                   Manufacturer of Record                   │
  └──────────────┬──────────────────────────────┬──────────────┘
                 │ (1) Quote & VAT              │ (4) Dispatch &
                 │     Invoice                  │     Payout (Net 15/45)
                 ▼                              ▼
  ┌──────────────────────────────┐        ┌──────────────────────────────┐
  │          CUSTOMER            │        │         MANUFACTURER         │
  │     (Engineers & Buyers)     │        │     (Machine & 3D Shops)     │
  └──────────────────────────────┘        └──────────────────────────────┘
```

1. **The Manufacturer Side Value Proposition (Zero Friction):**
   * **Zero Acquisition Cost:** Manufacturers do not pay to join, list, or bid. Onboarding is entirely free.
   * **No Customer Management:** They do not deal with sales, customer support, RFQ drafting, or invoice collection. They receive pre-vetted, ready-to-run digital jobs with complete CAD/STEP files.
   * **Guaranteed Payment:** Shapelid absorbs bad-debt and customer payment delay risk.

2. **The Customer Side Value Proposition (High Convenience):**
   * **Instant Quoting:** Instead of waiting 3–5 days for shop quotes, they upload a CAD file and get an immediate price via Kernel.
   * **Single Supplier Onboarding:** Corporate procurement departments only need to onboard *one* vendor (Shapelid) instead of managing compliance for hundreds of machine shops.
   * **Liability Protection:** Shapelid guarantees part quality, handling inspections and remakes if a part is out of spec.

### Defending Against Platform Leakage (Disintermediation):
In standard directory marketplaces, once a customer finds a supplier, they transact offline to bypass the platform fee. Shapelid’s MoR model actively prevents leakage because:
* **Anonymity:** The customer does not know which of the 20,000 suppliers produced their part, and the manufacturer does not know which customer ordered it.
* **Procurement convenience:** Large corporate buyers *prefer* paying Shapelid's premium because dealing directly with small, non-ISO-certified machine shops violates their compliance guidelines.

---

## 3. Commission Rate Recommendations & Technological Tiers

The default platform margin of **28%** in the Kernel pricing engine is an excellent starting point, but applying a flat rate across all technologies will result in market misalignment:
* **For 3D Printing (FDM, SLA, Polyjet, SLS, MJF, DMLS):** High-margin opportunities (30% to 40%). High convenience, low raw material cost, rapid prototyping demand.
* **For Subtractive/Deformative (CNC Milling, CNC Turning, EDM, Laser, Bending):** Lower margins (15% to 22%). Highly price-sensitive, high metal/raw material cost. A flat 28% on a 100,000 TRY CNC job will price Shapelid out of the market or starve the manufacturer's operational margins.

### Recommended Pricing Engine Margin Matrix:

| Manufacturing Technology | Baseline Margin (Kernel) | Minimum Payout (to Partner) | Strategic Justification |
|-------------------------|--------------------------|----------------------------|------------------------|
| **FDM / SLA (Simple Mode)** | **35.0%** | 65.0% | Low material cost, extreme focus on speed. Can be routed to the in-house workshop to capture 100% margin. |
| **SLS / MJF / Polyjet** | **30.0%** | 70.0% | Industrial 3D printing, high value-add, limited local competition. |
| **DMLS (Metal 3D Printing)** | **28.0%** | 72.0% | Highly specialized, premium tooling, high corporate demand. |
| **CNC Milling / Turning** | **20.0%** | 80.0% | Material-intensive, highly competitive local market. 28% margin is too high; 20% maintains competitiveness. |
| **EDM (Wire Cutting)** | **18.0%** | 82.0% | Extremely slow, high-wear process. High supplier cost. Lower margin protects supplier retention. |
| **Laser Cutting / Bending** | **18.0%** | 82.0% | High volume, low unit price. Scaled volume offsets lower margin. |
| **Injection / Casting** | **22.0%** | 78.0% | Mold creation represents high initial capital cost. Amortized over production run. |

---

## 4. Dual-Sided Subscription Tier Designs

### A. Manufacturer Tiers (SaaS for Suppliers)
Designed to solve cash flow and utilization constraints.

1. **Free Tier (Standby Partner):**
   * **Subscription Fee:** 0 TRY
   * **Payout Terms:** Net-45 days.
   * **Access:** View standard-tier open bids, FDM/SLA jobs only.
   * **Limit:** Max 3 concurrent active jobs.

2. **Pro Tier (Active Workshop):**
   * **Subscription Fee:** **2,500 TRY/month** (Annual discount: 24,000 TRY/year)
   * **Payout Terms:** **Net-15 days** (Accelerates cash flow significantly).
   * **Access:** Unlock all technologies (CNC, SLS, DMLS, EDM), priority job allocation.
   * **Features:** Standard CAD viewer, automated shipping label generation, SMS/WhatsApp instant job notifications.
   * **Limit:** Max 15 concurrent active jobs.

3. **Enterprise Tier (Certified Factory):**
   * **Subscription Fee:** **12,000 TRY/month** (Annual discount: 110,000 TRY/year)
   * **Payout Terms:** **Next-Day Payout** (Paid within 24 hours of QA approval).
   * **Access:** Unlimited active jobs, exclusive access to high-value aerospace/automotive orders (ISO9001/AS9100 required).
   * **Features:** API integration into internal shop ERP, custom manufacturing dashboard, dedicated partner manager.

---

### B. Customer Tiers (SaaS for Buyers)
Designed to lock in volume and optimize B2B procurement operations.

1. **Free Tier (Simple Mode / Prototyping):**
   * **Subscription Fee:** 0 TRY
   * **Payment Method:** Credit card / PayTR installment checkout only. No invoice-payout terms.
   * **Features:** Instant automated quoting, standard shipping, standard lead times.

2. **Pro Tier (R&D Teams):**
   * **Subscription Fee:** **5,000 TRY/month**
   * **Payment Method:** Net-30 invoice term (after credit scoring).
   * **Features:** 5% constant rebate on all orders, priority production queue, 2 hours of manual DFM engineer assistance/month.
   * **Shipping:** Free standard local shipping (Yurtiçi/Aras).

3. **Enterprise Tier (Corporate Procurement):**
   * **Subscription Fee:** **20,000 TRY/month** (or customized annual contract)
   * **Payment Method:** Net-45/60 invoice billing, custom contracting, custom NDAs.
   * **Features:** **10% constant rebate** on all orders, custom ERP/CAD API integration, dedicated QA engineer, physical 3D coordinate-measuring machine (CMM) verification reports included for every part.

---

## 5. 12-Month Revenue Projection Model

Calculated with a standardized rate of **1 USD = 47.16 TRY**. High-value, complex transactions are modeled to scale as corporate buyer confidence grows.

### Scenario Comparison (Annual Totals)
| Metric | Conservative | Moderate | Aggressive |
| --- | --- | --- | --- |
| Total GMV (TRY) | 40,580,727.27 | 115,240,000.00 | 292,244,727.27 |
| Avg Take Rate (%) | 25.0% | 26.5% | 28.0% |
| Marketplace Revenue (TRY) | 10,145,181.82 | 30,538,600.00 | 81,828,523.64 |
| Subscription Revenue (TRY) | 1,692,500.00 | 5,142,500.00 | 11,652,500.00 |
| Total Revenue (TRY) | 11,837,681.82 | 35,681,100.00 | 93,481,023.64 |
| Total Revenue (USD) | $251,011.06 | $756,596.69 | $1,982,210.00 |

---

### A. Conservative Scenario (Slow adoption, basic 3D prototyping focus)
* **Marketplace Commission:** Blended **25.0%**
* **Manufacturer Pro Tiers:** Scaling from 10 to 60.
* **Customer Pro Tiers:** Scaling from 2 to 12.
* **Customer Enterprise Tiers:** Scaling from 0 to 3.

| Month | Vol | AOV (TRY) | GMV (TRY) | Mkt Rev (TRY) | Sub Rev (TRY) | Total Rev (TRY) | Total Rev (USD) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Month 1 | 50 | 15,000.00 | 750,000.00 | 187,500.00 | 35,000.00 | 222,500.00 | $4,717.98 |
| Month 2 | 77 | 15,272.73 | 1,176,000.00 | 294,000.00 | 45,000.00 | 339,000.00 | $7,188.30 |
| Month 3 | 104 | 15,545.45 | 1,616,727.27 | 404,181.82 | 62,500.00 | 466,681.82 | $9,895.71 |
| Month 4 | 131 | 15,818.18 | 2,072,181.82 | 518,045.45 | 77,500.00 | 595,545.45 | $12,628.19 |
| Month 5 | 159 | 16,090.91 | 2,558,454.55 | 639,613.64 | 115,000.00 | 754,613.64 | $16,001.14 |
| Month 6 | 186 | 16,363.64 | 3,043,636.36 | 760,909.09 | 130,000.00 | 890,909.09 | $18,891.20 |
| Month 7 | 213 | 16,636.36 | 3,543,545.45 | 885,886.36 | 147,500.00 | 1,033,386.36 | $21,912.35 |
| Month 8 | 240 | 16,909.09 | 4,058,181.82 | 1,014,545.45 | 162,500.00 | 1,177,045.45 | $24,958.56 |
| Month 9 | 268 | 17,181.82 | 4,604,727.27 | 1,151,181.82 | 200,000.00 | 1,351,181.82 | $28,651.01 |
| Month 10 | 295 | 17,454.55 | 5,149,090.91 | 1,287,272.73 | 215,000.00 | 1,502,272.73 | $31,854.81 |
| Month 11 | 322 | 17,727.27 | 5,708,181.82 | 1,427,045.45 | 232,500.00 | 1,659,545.45 | $35,189.68 |
| Month 12 | 350 | 18,000.00 | 6,300,000.00 | 1,575,000.00 | 270,000.00 | 1,845,000.00 | $39,122.14 |

---

### B. Moderate Scenario (Strong steady adoption, blended 3D & CNC machining)
* **Marketplace Commission:** Blended **26.5%**
* **Manufacturer Pro Tiers:** Scaling from 20 to 180.
* **Customer Pro Tiers:** Scaling from 5 to 35.
* **Customer Enterprise Tiers:** Scaling from 1 to 8.

| Month | Vol | AOV (TRY) | GMV (TRY) | Mkt Rev (TRY) | Sub Rev (TRY) | Total Rev (TRY) | Total Rev (USD) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Month 1 | 80 | 18,000.00 | 1,440,000.00 | 381,600.00 | 95,000.00 | 476,600.00 | $10,106.02 |
| Month 2 | 150 | 18,363.64 | 2,754,545.45 | 729,954.55 | 140,000.00 | 869,954.55 | $18,446.87 |
| Month 3 | 220 | 18,727.27 | 4,120,000.00 | 1,091,800.00 | 212,500.00 | 1,304,300.00 | $27,656.91 |
| Month 4 | 290 | 19,090.91 | 5,536,363.64 | 1,467,136.36 | 262,500.00 | 1,729,636.36 | $36,675.92 |
| Month 5 | 360 | 19,454.55 | 7,003,636.36 | 1,855,963.64 | 330,000.00 | 2,185,963.64 | $46,352.07 |
| Month 6 | 430 | 19,818.18 | 8,521,818.18 | 2,258,281.82 | 400,000.00 | 2,658,281.82 | $56,367.30 |
| Month 7 | 500 | 20,181.82 | 10,090,909.09 | 2,674,090.91 | 452,500.00 | 3,126,590.91 | $66,297.52 |
| Month 8 | 570 | 20,545.45 | 11,710,909.09 | 3,103,390.91 | 522,500.00 | 3,625,890.91 | $76,884.88 |
| Month 9 | 640 | 20,909.09 | 13,381,818.18 | 3,546,181.82 | 590,000.00 | 4,136,181.82 | $87,705.30 |
| Month 10 | 710 | 21,272.73 | 15,103,636.36 | 4,002,463.64 | 640,000.00 | 4,642,463.64 | $98,440.70 |
| Month 11 | 780 | 21,636.36 | 16,876,363.64 | 4,472,236.36 | 712,500.00 | 5,184,736.36 | $109,939.28 |
| Month 12 | 850 | 22,000.00 | 18,700,000.00 | 4,955,500.00 | 785,000.00 | 5,740,500.00 | $121,723.92 |

---

### C. Aggressive Scenario (Hyper-scale, aerospace/defense CNC & DMLS dominance)
* **Marketplace Commission:** Blended **28.0%** (Maintaining pricing engine default)
* **Manufacturer Pro Tiers:** Scaling from 30 to 400.
* **Customer Pro Tiers:** Scaling from 10 to 80.
* **Customer Enterprise Tiers:** Scaling from 2 to 25.

| Month | Vol | AOV (TRY) | GMV (TRY) | Mkt Rev (TRY) | Sub Rev (TRY) | Total Rev (TRY) | Total Rev (USD) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Month 1 | 120 | 20,000.00 | 2,400,000.00 | 672,000.00 | 165,000.00 | 837,000.00 | $17,748.09 |
| Month 2 | 272 | 20,727.27 | 5,637,818.18 | 1,578,589.09 | 297,500.00 | 1,876,089.09 | $39,781.36 |
| Month 3 | 425 | 21,454.55 | 9,118,181.82 | 2,553,090.91 | 452,500.00 | 3,005,590.91 | $63,731.78 |
| Month 4 | 578 | 22,181.82 | 12,821,090.91 | 3,589,905.45 | 590,000.00 | 4,179,905.45 | $88,632.43 |
| Month 5 | 730 | 22,909.09 | 16,723,636.36 | 4,682,618.18 | 745,000.00 | 5,427,618.18 | $115,089.44 |
| Month 6 | 883 | 23,636.36 | 20,870,909.09 | 5,843,854.55 | 900,000.00 | 6,743,854.55 | $142,999.46 |
| Month 7 | 1036 | 24,363.64 | 25,240,727.27 | 7,067,403.64 | 1,037,500.00 | 8,104,903.64 | $171,859.70 |
| Month 8 | 1189 | 25,090.91 | 29,833,090.91 | 8,353,265.45 | 1,192,500.00 | 9,545,765.45 | $202,412.33 |
| Month 9 | 1341 | 25,818.18 | 34,622,181.82 | 9,694,210.91 | 1,347,500.00 | 11,041,710.91 | $234,132.97 |
| Month 10 | 1494 | 26,545.45 | 39,658,909.09 | 11,104,494.55 | 1,485,000.00 | 12,589,494.55 | $266,952.81 |
| Month 11 | 1647 | 27,272.73 | 44,918,181.82 | 12,577,090.91 | 1,640,000.00 | 14,217,090.91 | $301,465.03 |
| Month 12 | 1800 | 28,000.00 | 50,400,000.00 | 14,112,000.00 | 1,800,000.00 | 15,912,000.00 | $337,404.58 |

---

## 6. Turkey-Specific Strategic Recommendations

Operating a manufacturing marketplace in Turkey in 2026 demands specific adaptations to local economic and infrastructure realities.

### A. PayTR Marketplace Payment Splitting
* **The Legal Challenge:** The Central Bank of the Republic of Turkey (CBRT - TCMB) enforces strict regulations on online marketplace facilitators. Platforms are prohibited from holding or escrowing client funds in their own bank accounts unless they possess a payment institution license.
* **The PayTR Solution:** Shapelid must integrate **PayTR Marketplace (Pazaryeri)** solution. 
  1. The customer pays the total invoice amount (including 20% VAT).
  2. PayTR's split payment API immediately divides the transaction based on the instruction from Shapelid’s backend.
  3. **The Supplier Share (72% to 82% of net + supplier VAT)** is routed directly into the manufacturer’s bank account, which is cleared on the designated settlement day (Net 15/45).
  4. **The Shapelid Share (18% to 35% of net + Shapelid margin VAT)** is routed directly to Shapelid's corporate account.
* **Benefit:** Ensures absolute compliance with TCMB regulations, reduces legal overhead, and automates multi-vendor payout bookkeeping.

### B. Local Card Installments (Taksit)
* **The Dynamic:** In Turkey, credit card installments are crucial even for B2B transactions. Turkish SME procurement departments frequently use corporate credit cards (Commercial Cards) and expect installment choices (e.g., 3, 6, 9, or 12 months) via local card families (Bonus, Maximum, World, Axess).
* **Implementation:** PayTR provides virtual POS coverage for all major card networks. Shapelid should offer:
  * *Interest-free installments* up to 3 months for Pro/Enterprise customer subscribers (absorbing the 3-4% bank commission as a marketing cost).
  * *Installment options with a maturity fee (Vade Farkı)* for standard Free-tier customers, automatically calculated and appended by the checkout page.

### C. Inflation and Currency Volatility Management (TRY vs. USD/EUR)
* **The Risk:** Turkish manufacturing raw materials (metal blocks, polymer resins, SLA resins) are entirely import-dependent and priced in USD or EUR. Quoting in TRY and paying out 45 days later can fully erode Shapelid's margin if the Lira depreciates.
* **Kernel Adaptations:**
  1. **TCMB Live Feed:** The *Shapelid Geometry Kernel* must query the live Forex rates from TCMB API every hour.
  2. **Base Currency Anchoring:** All internal cost formulas in the pricing engine (machine rate, material rate per kg) must be stored in **USD or EUR**.
  3. **Quote Expiration:** Quoted prices in TRY must have a strict **24-hour expiration window** written clearly on the checkout page.
  4. **Buffer Percentage:** Maintain the **4.0% operational currency buffer** in the exchange rate module (as currently implemented in `exchange_rate.py`) to absorb intra-day currency shocks.

### D. Taxation & VAT (KDV) Flow
* **VAT Rate:** Custom manufacturing and engineering services in Turkey carry a standard **20% VAT (KDV)**.
* **MoR Invoice Execution:**
  * **Step 1:** Shapelid issues a VAT invoice of 120,000 TRY (100,000 TRY parts + 20,000 TRY VAT) to the customer.
  * **Step 2:** The manufacturer issues a VAT invoice of 86,400 TRY (72,000 TRY parts + 14,400 TRY VAT) to Shapelid.
  * **Step 3:** Shapelid pays the net VAT difference to the tax authority (5,600 TRY, which represents exactly 20% of Shapelid’s 28,000 TRY margin).
  * **Compliance Note:** This flow is highly transparent, standard, and easy to audit.

### E. Nearshoring & Export Arbitrage (The Ultimate Scale Strategy)
* **The Opportunity:** Turkish manufacturing is highly competitive on labor and overhead costs compared to Western Europe.
* **Execution:** While sourcing parts from Turkish manufacturers (paying them in TRY or USD-pegged rates), Shapelid can launch a **European Client Portal** (quoting in EUR).
* **The Arbitrage:** European customers pay EUR standard pricing (similar to Xometry Europe). Shapelid routes these jobs to its Turkish partner database. The effective take-rate on export orders can easily reach **45% to 55%** due to lower local manufacturing costs, creating an incredibly high-yield engine for Shapelid.

---

## 7. Recommended Next Steps for Implementation

1. **Kernel Margin Update:** Modify `PLATFORM_MARGIN` inside `pricing/cnc_engine.py` and `pricing/finish_rates.py` from a static `0.28` to a dynamic lookup based on the selected `technology` parameter.
2. **PayTR Sub-Merchant Integration:** Develop the backend onboarding pipeline to register the 4,124 manufacturer leads as sub-merchants on PayTR as they are activated.
3. **Launch SaaS Subscriptions:** Deploy the recurring billing modules on the client and partner portals, tying payout speeds (Net-15 vs. Net-45) directly to the manufacturer subscription database fields.
