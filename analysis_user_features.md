# Shapelid User-Centric Feature Analysis & Platform Roadmap
**Author:** Superagent Background Researcher  
**Target Market:** Turkey (EMEA Manufacturing Hub)  
**Business Model:** Manufacturer of Record (MoR)  
**Date:** July 29, 2026  

---

## 1. Executive Summary & Market Context

Shapelid is uniquely positioned as a digital manufacturing marketplace in Turkey, a region with a highly dense, capable, yet highly fragmented manufacturing SME ecosystem (clustered in industrial hubs like OSTİM/İvedik in Ankara, İMES/DES in Istanbul, and OSBs in Bursa, Kocaeli, and Izmir). 

Currently, Shapelid possesses a powerful technical core: a multi-format 3D CAD viewer (STL/OBJ/GLTF), a geometry and pricing engine (FastAPI kernel) supporting multiple manufacturing technologies with surface finish/color parameters, and a pre-qualified lead database of ~4,124 Turkish manufacturers. 

However, the platform currently **lacks order flow, payment processing, and manufacturer onboarding**. To bridge the gap from a "pricing calculator" to a highly liquid, multi-million dollar transaction marketplace, Shapelid must adopt the **Manufacturer of Record (MoR)** model—similar to Xometry and Protolabs Network (Hubs). Under the MoR model, Shapelid is the single contractual partner for the customer, managing billing, quality guarantees, and customer service, while outsourcing production to its vetted Turkish manufacturer network.

### The Competitive Threat: Xometry Turkey (Formerly Tridi)
In 2023, the global titan **Xometry acquired Tridi**, Turkey's leading on-demand manufacturing marketplace. Tridi’s local manufacturing network and team were integrated into Xometry’s global tech ecosystem (operating as `xometry.com.tr`). To compete, Shapelid must offer a highly localized, agile, and friction-free user experience tailored to Turkish commercial realities (such as cash flow constraints, e-Fatura mandates, installment payments, and WhatsApp-centric manufacturer operations).

This document provides a comprehensive, prioritized feature roadmap from a user perspective for **Customers**, **Manufacturers**, and **Platform Admins**, followed by a competitive analysis and a development dependency map.

---

## 2. Competitive Feature Comparison

To successfully position Shapelid, we analyze the feature sets of market leaders: **Xometry**, **Protolabs Network (formerly Hubs)**, and **Protolabs (In-House)**, and map out where Shapelid stands and what it must build.

| Feature Category | Xometry (Global & TR) | Protolabs Network (Hubs) | Protolabs (In-House) | Shapelid (Current State) | Shapelid (Proposed Feature State) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Business Model** | Manufacturer of Record (MoR) | Manufacturer of Record (MoR) | Direct Manufacturer (In-house) | Core Pricing Engine only | **Manufacturer of Record (MoR)** with local Turkish legal entity. |
| **Instant Quoting** | AI-driven pricing for CNC, 3D, Sheet Metal, Injection Molding. | Geometric analysis-driven pricing for CNC, 3D, Sheet Metal. | Proprietary automated software (extreme speed). | Supported (FastAPI kernel for STL/DXF, geometry + material + finish). | **Enhanced Quoting** with STEP/IGES CAD support and automated multi-part project carts. |
| **DfM Feedback** | Basic interactive flags (thin walls, tight tolerances, size limits). | **Industry-leading DfM**: Interactive heatmaps of hard-to-machine areas. | Automated, deep DfM analysis with 3D graphical suggestions. | None (Static pricing and analysis). | **Visual DfM Engine**: Interactive warnings on 3D viewer for tool clearance and wall thickness. |
| **Turkish Payments & Tax** | Fully integrated with local e-Fatura, local bank transfers, credit cards. | Limited/Global billing, mostly USD/EUR focus. | Global billing, mostly USD/EUR focus, high-end pricing. | None (Settings page placeholder). | **Turkish B2B Checkout**: Iyzico corporate CC, multi-installment (taksit), bank EFT, and automated GİB e-Fatura/e-Arşiv. |
| **Manufacturer Matching** | Automated matching based on Partner Success Score (PSS) & Capabilities. | Curated manual/semi-automated dispatch to "Premium Partners." | In-house scheduling algorithms. | None (Lead list exists as static database). | **Smart Job Board**: Capacity-aware, geolocation-optimized job feed with 1-click acceptance. |
| **Supplier Vetting** | 3-Step online application + Test Part validation. | Strict 8-Step onboarding including virtual audits and benchmark part validation. | Employees only (In-house factories). | None (~4,124 static leads). | **5-Step Onboarding Pipeline**: Vergi Levhası check, machinery audit, physical Test Order. |
| **Quality Control (QC)** | Hybrid: Self-QC by partners via app photos + Centralized random audits. | Decentralized partner QC according to Hubs standard + random hub checks. | Strict, standardized in-house QC (CMM, optical, certifications). | None. | **Central QC Hub in Istanbul** for high-value orders, and **App-Guided Self-QC** for low-value orders. |
| **Supplier Cash Flow** | **Xometry Pay / FastPay**: instant payment post-delivery for a small fee. | Net 30/45 standard payouts. | Regular payroll. | None (Balance page placeholder). | **Shapelid FastPay**: Accelerated payouts (Net-3) post-QC to solve high-inflation liquidity issues. |

---

## 3. Customer (Buyer) Feature Recommendations

Customers of custom manufacturing services in Turkey are primarily **SME product designers, mechanical engineers, R&D departments in corporate enterprises, and procurement managers**. They demand extreme speed, price clarity, transactional trust, and seamless corporate billing.

### 🔴 MUST-HAVE (Phase 1 & 2)

#### 1. End-to-End Multi-Part B2B Checkout & Cart
*   **The Feature:** A persistent shopping cart that aggregates multiple CAD designs (STL, OBJ, GLTF, and newly integrated STEP/IGES formats) into a single "Project." Customers configure materials, finishes, tolerances, and quantities for each part, seeing an instant subtotal, estimated lead time, and bulk discounts.
*   **Turkish Payment Integration:** Integrate with a robust gateway like **Iyzico** or **Paynet**. It must support:
    *   **Corporate Credit Cards** with business installment options ("Ticari Kart Taksit Seçenekleri" is mandatory for Turkish SME buyers to manage cash flow).
    *   **Bank Transfer / EFT (Havale)**: The checkout must generate a unique virtual IBAN or order reference code. Buyers upload proof of transfer (Dekont) or the system auto-reconciles bank feeds.
*   **e-Fatura / e-Arşiv Automation:** Since B2B buyers must account for corporate expenses, the checkout must capture:
    *   Company Name (Unvan), Tax Office (Vergi Dairesi), and Tax Number (Vergi Kimlik Numarası - VKN).
    *   Automated integration with e-billing services (e.g., Paraşüt or QNB e-Finans) to instantly query the Revenue Administration (GİB) registry, determine if the buyer is an e-Fatura user, and generate the correct compliant invoice.

#### 2. Shapelid MoR Quality Guarantee & Escrow
*   **The Feature:** Turkish buyers are highly risk-averse when dealing with decentralized small shops. Shapelid must act as the **Manufacturer of Record (MoR)**. The platform guarantees that all parts will meet the selected geometric tolerances, material standards, and surface finishes.
*   **Value Proposition:** If a part fails physical inspection, Shapelid bears the cost of refabrication or issues a refund. This removes the "trust friction" of sourcing from unknown suppliers.

#### 3. Real-Time Logistics Integration
*   **The Feature:** Automated shipping estimation and tracking integration with Turkish logistics leaders:
    *   **Standard Cargo:** **Kolay Gelsin** (highly rated for B2C/B2B speed), **Yurtiçi Kargo**, or **UPS Turkey**.
    *   **Industrial Heavy Freight (Ambar / Pallet):** Integration with B2B freight networks (like **Borusan Lojistik**) for heavy metal CNC parts, sheet metal bending, and injection molding tools.
*   **Execution:** Customers see automated shipping fees dynamically calculated based on packed part weight/volume, and receive a tracking link in their Dashboard.

---

### 🟡 SHOULD-HAVE (Phase 3)

#### 1. Instant Design for Manufacturability (DfM) Feedback
*   **The Feature:** As soon as a user uploads a CAD file to the 3D Viewer, a background script runs trimesh/numpy analysis (integrated with the FastAPI kernel) to inspect the geometry and highlight risk zones directly on the 3D mesh:
    *   **Thin Walls:** Highlight in RED walls thinner than 1.0mm for FDM, or 1.5mm for CNC machining.
    *   **Unreachable Deep Pockets:** For CNC machining, flag pockets where depth-to-width ratio exceeds 4:1 (which causes CNC tool chatter/breakage).
    *   **Sharp Internal Edges:** Warn users that CNC mills cannot cut 90-degree internal sharp vertical corners and suggest adding corner fillets.
*   **Value:** Dramatically reduces the back-and-forth manual engineering reviews and prevents unmanufacturable orders.

#### 2. Digital Inspection & Certification Vault
*   **The Feature:** A dedicated tab inside the Project view where advanced engineering users can request and download compliance documents:
    *   **Dimensional Inspection Reports:** PDF caliper/CMM reports.
    *   **Material Certifications:** Mill Test Reports (MTR) or CoC (Certificate of Conformance) proving the raw material (e.g., Al 6061-T6, AISI 304) is genuine.
*   **Target Segment:** Defense, aerospace (ASELSAN, TAI supply chains in Ankara), and medical device manufacturers who cannot buy custom parts without documentation.

#### 3. Formal B2B PDF Quote Generator
*   **The Feature:** Corporate purchasing departments in Turkey rarely buy directly with credit cards on a website. They require a formal PDF quotation with a unique Quote ID, expiration date (usually 14 days due to TRY exchange rate volatility), company logo, and official signature/stamp (Kaşe/İmza).
*   **Execution:** Provide a "Download Official Quote PDF" button in the Pricing page. The backend generates a stamped PDF locked to the current USD/TRY rate, allowing the engineer to forward it to their finance department for payment.

---

### 🟢 COULD-HAVE (Phase 4)

#### 1. Shapelid Touch & Feel Material Sample Kit
*   **The Feature:** Allow users to order a standardized "Shapelid Sample Kit" for a nominal fee (refunded on their first order). The kit contains actual physical samples of:
    *   3D Printing: PLA, ABS, Nylon (SLS), Tough Resin (SLA) showcasing standard layer heights.
    *   CNC Machining: Aluminum 6061 and POM showing bead blast, anodized, and raw milled finishes.
    *   Sheet Metal: Bent steel plates with powder coating.
*   **Value:** Bridges the tactile gap for product designers, driving high conversion rates.

#### 2. AI-Driven Cost Reduction Suggestions (Design to Cost - DTC)
*   **The Feature:** Inside the Order Assistant, provide suggestions like:
    *   *"Changing SLA to FDM PLA would reduce your price by 65% while keeping similar dimensions."*
    *   *"Increasing your tolerance from ±0.05mm to ±0.15mm on CNC parts will decrease machining time and save 22% of the cost."*
    *   *"Increasing quantity from 5 to 50 parts reduces unit cost by 40%."*

---

## 4. Manufacturer (Supplier) Feature Recommendations

SME manufacturers in Turkey operate on thin margins and face severe cash flow bottlenecks caused by high inflation and delayed payments. They are highly skilled but lack modern operational tools and digital sales pipelines.

### 🔴 MUST-HAVE (Phase 1 & 2)

#### 1. The Shapelid Partner Portal & Job Board
*   **The Feature:** A secure dashboard specifically for onboarded manufacturers to view and claim open production orders.
    *   **Direct Job Claims (No RFQ bidding):** Instead of wasteful bidding wars that drive down prices and quality, the Shapelid algorithm uses the auto-pricing engine to calculate a "Supplier Payout Price" (Customer Price minus Shapelid Take-Rate).
    *   **Capacity-Matching Filters:** Suppliers only see jobs matching their registered capabilities (e.g., "SLA Printer", "3-Axis CNC Machining") and materials they keep in stock. If the supplier is happy with the payout, they click **"Accept Job"** to instantly lock it.

```
+-----------------------------------------------------------------+
|                     SHAPELID PARTNER PORTAL                     |
+-----------------------------------------------------------------+
| [Open Jobs]   [My Active Queue]   [My Balance]   [Shop Profile] |
+-----------------------------------------------------------------+
| Match found!                                                    |
| Job ID: #9832 - CNC Machining (Al 6061-T6)                      |
| Finish: Anodizing Blue | Qty: 50 pcs                            |
| Payout Price: 34,500 TRY (Excl. VAT)                             |
| Required Delivery: August 12, 2026 (14 Days)                   |
|                                                                 |
| [ Download STEP File ]   [ View Specs PDF ]                     |
|                                                                 |
|                   >>>>  [ ACCEPT JOB ]  <<<<                    |
+-----------------------------------------------------------------+
```

#### 2. Automated Job Package Creator (Single-ZIP Download)
*   **The Feature:** Once a manufacturer claims a job, the system packages all necessary assets into a single ZIP file:
    *   The CAD files (converted to the correct production format, e.g., STEP, DXF for laser cutting).
    *   A standardized **Production Specification Sheet (PDF)** detailing quantities, tolerances, material requirements, surface finishes, and delivery dates.
    *   Automated pre-paid **Shipping Label (PDF)** generated via shipping partner API (Yurtiçi/Kolay Gelsin). The supplier simply packs the parts, sticks the label on the box, and hands it to the courier.

#### 3. Compliant Turkish B2B Payout Engine
*   **The Feature:** Standardized billing flow where the manufacturer acts as a sub-contractor.
    *   Once an order is approved by Shapelid QC, the supplier is prompted to upload their official **e-Fatura** addressed to Shapelid's Turkish legal entity for the locked payout amount (e.g., including 20% VAT).
    *   **Bank Transfer Integration:** Payouts are made directly to the supplier's registered IBAN via standard EFT/FAST.

---

### 🟡 SHOULD-HAVE (Phase 3)

#### 1. Shapelid "FastPay" (Accelerated Payouts)
*   **The Feature:** In Turkey's high-inflation environment, waiting Net 30 or Net 45 days for payment is highly detrimental to small workshops. It forces them to decline work or charge inflated rates.
*   **Solution:** Offer a "FastPay" toggle:
    *   *Standard Payout:* Net 30 days (0% fee).
    *   *FastPay:* Payout is issued within 3 business days of successful QC inspection for a **3.5% factoring fee**.
*   **Value:** Solves supplier cash flow crises, incentivizes fast delivery, and generates an additional pure-margin revenue stream for Shapelid.

#### 2. Partner Success Score (PSS) & Quality Tiering
*   **The Feature:** An automated scoring system (0 to 100) that evaluates each supplier on three critical metrics:
    1.  **On-Time Delivery (OTD):** Did they ship on or before the agreed date?
    2.  **Quality Rate:** What percentage of their parts passed QC? (Non-conformance rate).
    3.  **Responsiveness:** How quickly do they accept jobs or respond to customer/admin support tickets?
*   **SLA Tiering:**
    *   **Tier 1 (Silver, PSS 70-85):** Standard access to the job board.
    *   **Tier 2 (Gold, PSS 85-95):** Early access to newly posted high-margin jobs (4 hours before Silver).
    *   **Tier 3 (Platinum, PSS 95+):** 12 hours early access, automated matching for premium aerospace/corporate clients, and eligibility for lower FastPay rates (e.g., 2% fee instead of 3.5%).

#### 3. Mobile-First Responsive PWA (WhatsApp Integrated)
*   **The Feature:** Small workshop owners (atölyeler) do not sit in front of computers; they are on the shop floor running machines. A desktop-only portal fails.
*   **Solution:** Build a progressive web app (PWA) with push notifications, and deeply integrate **WhatsApp Business API**:
    *   When a highly matching, high-payout job is posted, send an automated WhatsApp message: *"Hi Ahmet, we have a CNC Machining job in Al 6061 with a payout of 42,000 TRY. Click here to view CAD and accept instantly on your phone!"*

---

### 🟢 COULD-HAVE (Phase 4)

#### 1. Shapelid Consolidated Sourcing Program (Material/Tool Sourcing)
*   **The Feature:** Leverage the buying power of the entire 4,124-supplier network. Shapelid negotiates bulk discounts on raw materials (aluminum billets, steel plates, PLA filaments, resins) and cutting tools (endmills, inserts) from major distributors in Turkey.
*   **Execution:** Manufacturers can purchase materials directly through their **Manufacturer Balance** page inside the portal at a 15-25% discount, with materials delivered directly to their workshop.

---

## 5. The 5-Step Manufacturer Vetting & Onboarding Pipeline

To guarantee the quality that buyers expect from a MoR platform, Shapelid cannot simply open the floodgates to its ~4,124 leads. It must funnel these leads through a standardized onboarding pipeline:

```
  [1. Apply] ---> [2. Doc Audit] ---> [3. Virtual/Physical Audit] ---> [4. Test Order] ---> [5. Board Active]
   (Online info)    (Tax Plate, NDA)      (Machines, Capacity)          (Benchmark Part)    (Full System Access)
```

1.  **Step 1: Digital Application & Equipment Profiling**
    *   The manufacturer signs up, lists their active equipment (e.g., *"Hass VF-2 3-Axis CNC, Formlabs Form 3L SLA"*), maximum build volumes, and materials regularly stocked.
2.  **Step 2: Legal & Financial Verification (Document Audit)**
    *   Upload tax plate (**Vergi Levhası**), signatory circular (**İmza Sirküleri**), and trade registry gazette (**Ticaret Sicil Gazetesi**).
    *   Sign a comprehensive Mutual Non-Disclosure Agreement (NDA) to protect buyer intellectual property (critical for aerospace/military clients).
3.  **Step 3: Technical Capacity Audit**
    *   For standard 3D printing (FDM/SLA), a photo-verification of setup is sufficient.
    *   For high-precision CNC, injection molding, and die casting, a platform admin conducts a virtual video audit or a physical visit (utilizing Istanbul/Ankara/Bursa-based local regional reps) to inspect Quality Control systems (calipers, micrometers, CMMs).
4.  **Step 4: The Benchmark Test Order (Critical Step)**
    *   Shapelid sends a complex, proprietary "Benchmark CAD File" containing deep slots, thin ribs, tight holes, and surface textures.
    *   The manufacturer must fabricate this part using their own materials and ship it to Shapelid's central facility.
    *   Shapelid's engineering team inspects the parts using 3D scanners and metrology tools.
5.  **Step 5: Active Board Status**
    *   Upon passing the test order, the partner is activated on the Job Board and receives a default PSS of 90. They are restricted to low-to-mid value orders until they complete 5 successful customer deliveries.

---

## 6. Platform Admin Feature Recommendations

The Platform Admin operates the system, maintains marketplace liquidity, settles disputes, and monitors quality control.

### 🔴 MUST-HAVE (Phase 1 & 2)

#### 1. Onboarding CRM & Pipeline Manager
*   **The Feature:** A dedicated dashboard to manage the ~4,124 static manufacturer leads. Admins filter leads by city, technology, and size, and move them through the "Applied -> Document Check -> Audited -> Test Order -> Active" pipeline using a Kanban-style interface.
*   **Mass Outreach Tool:** Built-in email/SMS campaign manager to trigger onboarding invitations in batches (e.g., *"We have excess CNC machining demand in Bursa. Emailing 200 Bursa-based CNC leads to start onboarding"*).

#### 2. Order Dispatch & Pricing Override Panel
*   **The Feature:** A central order dashboard where admins monitor all customer orders.
    *   **Manual Quote Review:** When the auto-pricing engine triggers a `manual_quote` (due to highly complex geometries, huge volumes, or special certifications), admins can manually inspect the CAD, request bids from top-tier manufacturers, and input a manual quote price for the customer.
    *   **Take-Rate Calibration:** Slide control to adjust the marketplace take-rate dynamically. If a customer is high-profile, admin can drop the take-rate from 25% to 10% to secure the order.

#### 3. Centralized vs. Decentralized Quality Control (QC) Console
*   **The Feature:**
    *   **Centralized Hub (Istanbul):** For orders exceeding a specific price threshold (e.g., 20,000 TRY) or requiring strict compliance, the shipping label automatically routes the package from the supplier to **Shapelid's Istanbul Warehouse/QC Lab**. The admin performs metrology inspections, packages the part in premium Shapelid-branded boxes, and ships it to the customer.
    *   **Self-QC Portal:** For standard 3D printing or low-value orders, the supplier uploads high-res photos and dimension logs to the platform via the Supplier Portal. The admin approves these photos digitally, and the shipping label routes the package directly from the supplier to the customer.

---

### 🟡 SHOULD-HAVE (Phase 3)

#### 1. B2B Dispute Resolution Dashboard
*   **The Feature:** When a customer triggers a dispute (e.g., *"Parts are out of tolerance"* or *"Surface is scratched"*), the admin acts as the arbitrator:
    *   Admin reviews: Uploaded CAD, customer's photo proof, manufacturer's QC logs.
    *   Admin can click:
        *   **"Approve Refabrication"**: Automatically clones the order, assigns it to a high-performing Tier 3 manufacturer, and pays them.
        *   **"Issue Refund"**: Refunds the customer and penalizes the manufacturer's balance.
        *   **"Reject Dispute"**: Releases escrowed funds to the manufacturer if parts match the agreed specs.

#### 2. Financial Dashboard & Tax Compliance Hub
*   **The Feature:** Real-time visibility into financial health:
    *   Gross Merchandise Value (GMV) and Net Revenue (Marketplace Take-Rate).
    *   Outstanding manufacturer balances and pending payouts.
    *   TCMB Exchange Rate buffer analytics (monitoring if the 4% currency buffer is covering TRY-USD volatility).
    *   e-Fatura reconciliation status.

---

## 7. Feature Dependency Map

To avoid building monolithic features that fail, the development must follow a logical sequence where each database table, API, and UI element is laid down in progressive phases:

```
+-------------------------------------------------------------------------------------------------------------------+
|  PHASE 1: FOUNDATION (Database & Payments)                                                                        |
|                                                                                                                   |
|  [Customer Page] ------------> [Iyzico Checkout API] -----------> [Order, Payment, Shipping Tables]               |
|  Multi-part shopping cart      Corporate CC / Havale              Define relationships, statuses, and logs        |
|                                                                                                                   |
|  [Manufacturer Lead CRM] ----> [Onboarding Document Upload] ---> [GİB e-Fatura / e-Arşiv API]                     |
|  Kanban pipeline               Tax Plate / NDA validation         Automated invoicing engine                      |
+-------------------------------------------------------------------------------------------------------------------+
                                          |
                                          v
+-------------------------------------------------------------------------------------------------------------------+
|  PHASE 2: FULFILLMENT & ROUTING (The Marketplace Engine)                                                          |
|                                                                                                                   |
|  [Shapelid Partner Portal] --> [Job Board Engine] --------------> [Logistics API Integration]                     |
|  Basic supplier profile        Match capabilities & claim jobs    Yurtiçi/Kolay Gelsin Shipping Labels             |
|                                                                                                                   |
|  [Admin QC Console] ---------> [Manual Quote Overrides] --------> [Manufacturer Balance Payouts]                 |
|  Digital Photo-QC check        Admin dashboard pricing control    Bank EFT / e-Fatura uploads                     |
+-------------------------------------------------------------------------------------------------------------------+
                                          |
                                          v
+-------------------------------------------------------------------------------------------------------------------+
|  PHASE 3: TRUST, CASH FLOW & AUTOMATION                                                                           |
|                                                                                                                   |
|  [Interactive DfM Viewer] ---> [Partner Success Score (PSS)] ---> [Shapelid "FastPay" factoring]                 |
|  Wall-thickness/CNC checks     Automated supplier metrics         3-day payout for 3.5% fee                       |
|                                                                                                                   |
|  [PDF Official Quoting] -----> [Dispute Arbitration Dashboard] -> [WhatsApp Job Alert Bot]                       |
|  Kaşe/İmza stamped quotes      Resolve QC complaints              SMS/WhatsApp direct supplier notifications     |
+-------------------------------------------------------------------------------------------------------------------+
                                          |
                                          v
+-------------------------------------------------------------------------------------------------------------------+
|  PHASE 4: ENTERPRISE OPTIMIZATION                                                                                 |
|                                                                                                                   |
|  [STEP / IGES CAD Parser] ----> [Design to Cost (DTC) Engine] --> [Consolidated Sourcing Program]                 |
|  Advanced 3D analysis          AI cost reduction prompts          Bulk material marketplace for partners          |
+-------------------------------------------------------------------------------------------------------------------+
```

### Technical Prerequisites & Dependency Details:
1.  **STEP/IGES Parsing vs. STL/DXF:** The current pricing kernel only supports STL and DXF. CNC machining and Injection Molding require 3D boundary representation files (STEP/IGES) because STL only contains a flat triangulated mesh, which strips out exact cylindrical tolerances, hole diameters, and thread specifications. Therefore, Phase 1 and 2 can operate with STL/DXF for 3D printing and sheet metal, but **STEP/IGES support is a prerequisite before launching premium CNC machining or Injection Molding orders.**
2.  **e-Fatura Integration:** Must be built in Phase 1. It is legally impossible to run high-volume B2B transactions in Turkey without immediate, automated e-Fatura verification and generation. Delaying this to later phases will result in massive manual accountant bottlenecks.
3.  **PSS Algorithm Dependency:** The Partner Success Score (PSS) cannot be built in Phase 1 because it requires operational telemetry (delivery times, QC non-conformance records, response times). Thus, Phase 2 will use a simple first-come-first-served or manual admin matching logic, transitioning to PSS in Phase 3 as transaction history accumulates.

---

## 8. Summary of Actionable Next Steps

For the development team to transition the current Shapelid codebase into this highly competitive model, they should focus immediately on:

1.  **Database Migration (Phase 1 Database Schemas):** Define the relational architecture of `Orders`, `OrderParts`, `Payments`, `Shipments`, `Disputes`, and `SupplierProfiles`.
2.  **Iyzico & Paraşüt API Integrations:** Initiate accounts and mock integration tests for Turkish payments and automated GİB e-Fatura queries.
3.  **Supplier Registration Portal:** Create a secure gateway for the ~4,124 static manufacturer leads to begin claiming their profiles, verifying their identity, and listing their machinery capabilities.
4.  **Central QC Hub Setup:** Secure a small physical verification lab space in Istanbul (near major industrial manufacturing areas like İMES or İkitelli) to act as the primary inspection bottleneck for Phase 1 high-value orders.
