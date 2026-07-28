import json

resins = [
    # --- FORMLABS (10 Resins) ---
    {
        "material_name": "Standard Grey V4",
        "brand": "Formlabs",
        "technology": "SLA",
        "category": "Standard",
        "shore_hardness": "82D",
        "tensile_strength_mpa": 65.0,
        "approx_price_usd_liter": 149.0,
        "use_case": "General prototyping, high-detail models, and visual presentations.",
        "notes": "Excellent surface finish and fine detail. Matte finish after curing."
    },
    {
        "material_name": "Clear V4",
        "brand": "Formlabs",
        "technology": "SLA",
        "category": "Standard",
        "shore_hardness": "82D",
        "tensile_strength_mpa": 65.0,
        "approx_price_usd_liter": 149.0,
        "use_case": "Optical clarity, fluidics, LED packaging, and clear housings.",
        "notes": "Can be polished or clear-coated to achieve near-optical transparency."
    },
    {
        "material_name": "Draft V2",
        "brand": "Formlabs",
        "technology": "SLA",
        "category": "Rapid/Standard",
        "shore_hardness": "80D",
        "tensile_strength_mpa": 49.0,
        "approx_price_usd_liter": 149.0,
        "use_case": "Rapid design iterations, print speed testing, and bulk prototypes.",
        "notes": "Prints up to 4 times faster than standard resins. Grey/Blue in appearance."
    },
    {
        "material_name": "Tough 2000",
        "brand": "Formlabs",
        "technology": "SLA",
        "category": "Tough/ABS-Like",
        "shore_hardness": "82D",
        "tensile_strength_mpa": 46.0,
        "approx_price_usd_liter": 149.0,
        "use_case": "Rugged prototyping, mechanical assemblies, and snap-fits under stress.",
        "notes": "Formulated to simulate ABS plastic properties with high strength and stiffness."
    },
    {
        "material_name": "Tough 1500",
        "brand": "Formlabs",
        "technology": "SLA",
        "category": "Tough/Engineering",
        "shore_hardness": "74D",
        "tensile_strength_mpa": 35.0,
        "approx_price_usd_liter": 179.0,
        "use_case": "Stiff and pliable parts, spring back joints, hinges, and skin-contact wearables.",
        "notes": "Certified for skin contact. Simulates polypropylene (PP) plastic properties."
    },
    {
        "material_name": "Durable V2",
        "brand": "Formlabs",
        "technology": "SLA",
        "category": "Tough/Engineering",
        "shore_hardness": "66D",
        "tensile_strength_mpa": 28.0,
        "approx_price_usd_liter": 179.0,
        "use_case": "Low-friction assemblies, high-impact prototypes, and flexible squeezable containers.",
        "notes": "Simulates polyethylene (PE) plastic properties. High impact resistance."
    },
    {
        "material_name": "Rigid 10K",
        "brand": "Formlabs",
        "technology": "SLA",
        "category": "Rigid/Engineering",
        "shore_hardness": "90D",
        "tensile_strength_mpa": 88.0,
        "approx_price_usd_liter": 299.0,
        "use_case": "Wind tunnel testing, manifolds, molds, dies, and high thermal resistance housings.",
        "notes": "Highly glass-filled. The stiffest material in Formlabs' desktop portfolio."
    },
    {
        "material_name": "Flexible 80A",
        "brand": "Formlabs",
        "technology": "SLA",
        "category": "Flexible",
        "shore_hardness": "80A",
        "tensile_strength_mpa": 8.9,
        "approx_price_usd_liter": 199.0,
        "use_case": "Rubber/TPU simulation, gaskets, seals, dampening parts, and soft-touch handles.",
        "notes": "Excellent tear strength and rebound. Simulates medium-durometer vulcanized rubber."
    },
    {
        "material_name": "Elastic 50A",
        "brand": "Formlabs",
        "technology": "SLA",
        "category": "Flexible",
        "shore_hardness": "50A",
        "tensile_strength_mpa": 3.2,
        "approx_price_usd_liter": 199.0,
        "use_case": "Silicone-like parts, wearable straps, medical models, and compressible buttons.",
        "notes": "Softest engineering resin. Extremely high elongation and flexibility."
    },
    {
        "material_name": "Surgical Guide",
        "brand": "Formlabs",
        "technology": "SLA",
        "category": "Dental",
        "shore_hardness": "85D",
        "tensile_strength_mpa": 73.0,
        "approx_price_usd_liter": 299.0,
        "use_case": "Biocompatible dental implant surgical guides, drilling templates, and pilot guides.",
        "notes": "Class I biocompatible resin, autoclavable and highly dimensionally stable."
    },

    # --- ELEGOO (6 Resins) ---
    {
        "material_name": "Standard Resin 2.0 (8K)",
        "brand": "Elegoo",
        "technology": "MSLA/LCD",
        "category": "Standard",
        "shore_hardness": "84D",
        "tensile_strength_mpa": 33.2,
        "approx_price_usd_liter": 22.0,
        "use_case": "Hobbyist miniatures, model display pieces, and general prototyping.",
        "notes": "Highly affordable, low odor, and optimized for high-resolution MSLA screens."
    },
    {
        "material_name": "ABS-Like Resin 3.0",
        "brand": "Elegoo",
        "technology": "MSLA/LCD",
        "category": "ABS-Like",
        "shore_hardness": "84D",
        "tensile_strength_mpa": 43.0,
        "approx_price_usd_liter": 27.0,
        "use_case": "Functional prototypes requiring higher impact resistance and less brittleness.",
        "notes": "Lower shrinkage and improved toughness compared to Standard 2.0."
    },
    {
        "material_name": "Water-Washable ABS-Like Resin",
        "brand": "Elegoo",
        "technology": "MSLA/LCD",
        "category": "Water-Washable",
        "shore_hardness": "82D",
        "tensile_strength_mpa": 39.0,
        "approx_price_usd_liter": 28.0,
        "use_case": "Eco-friendlier/easy cleanup functional models and mechanical parts.",
        "notes": "Can be cleaned using warm water instead of Isopropyl Alcohol (IPA)."
    },
    {
        "material_name": "Standard Plant-Based Resin",
        "brand": "Elegoo",
        "technology": "MSLA/LCD",
        "category": "Eco-friendly/Standard",
        "shore_hardness": "82D",
        "tensile_strength_mpa": 24.4,
        "approx_price_usd_liter": 25.0,
        "use_case": "Indoor prototyping, school projects, and eco-conscious hobbyist modeling.",
        "notes": "Derived from soybean oil. Low odor, low skin irritation, biodegradable."
    },
    {
        "material_name": "Tough Resin",
        "brand": "Elegoo",
        "technology": "MSLA/LCD",
        "category": "Tough",
        "shore_hardness": "75D",
        "tensile_strength_mpa": 33.0,
        "approx_price_usd_liter": 30.0,
        "use_case": "Shock-absorbing models, structural components, and high-impact assemblies.",
        "notes": "Combines flexibility with decent structural strength to prevent cracking under impact."
    },
    {
        "material_name": "Orthodontic Model Resin",
        "brand": "Elegoo",
        "technology": "MSLA/LCD",
        "category": "Dental",
        "shore_hardness": "86D",
        "tensile_strength_mpa": 50.0,
        "approx_price_usd_liter": 55.0,
        "use_case": "Vacuum-forming orthodontic aligner models and dental arches.",
        "notes": "High temperature resistance, able to withstand vacuum forming heat without deforming."
    },

    # --- ANYCUBIC (6 Resins) ---
    {
        "material_name": "Standard Resin V2",
        "brand": "Anycubic",
        "technology": "MSLA/LCD",
        "category": "Standard",
        "shore_hardness": "82D",
        "tensile_strength_mpa": 38.0,
        "approx_price_usd_liter": 21.0,
        "use_case": "Action figures, visual models, toys, and architectural prototypes.",
        "notes": "Outstanding price-to-performance ratio. Very popular entry-level resin."
    },
    {
        "material_name": "ABS-Like Resin V2",
        "brand": "Anycubic",
        "technology": "MSLA/LCD",
        "category": "ABS-Like",
        "shore_hardness": "80D",
        "tensile_strength_mpa": 45.0,
        "approx_price_usd_liter": 29.0,
        "use_case": "Durable consumer electronics shells, casing assemblies, and snap-fits.",
        "notes": "Significantly higher impact strength and elongation at break than Standard V2."
    },
    {
        "material_name": "Water-Wash ABS-Like V3.0",
        "brand": "Anycubic",
        "technology": "MSLA/LCD",
        "category": "Water-Washable",
        "shore_hardness": "82D",
        "tensile_strength_mpa": 42.0,
        "approx_price_usd_liter": 34.0,
        "use_case": "Hobbyists wanting ABS-like strength but easy, chemical-free cleanup.",
        "notes": "Cleans easily in pure water. Combines water-wash convenience with tough mechanical properties."
    },
    {
        "material_name": "Plant-Based Tough Resin",
        "brand": "Anycubic",
        "technology": "MSLA/LCD",
        "category": "Eco-friendly/Tough",
        "shore_hardness": "76D",
        "tensile_strength_mpa": 32.0,
        "approx_price_usd_liter": 26.0,
        "use_case": "Sturdy educational toys, display models, and general engineering prototypes.",
        "notes": "Bio-derived, eco-friendly with lower brittleness than standard plant-based options."
    },
    {
        "material_name": "High Clear Resin",
        "brand": "Anycubic",
        "technology": "MSLA/LCD",
        "category": "Standard/Clear",
        "shore_hardness": "84D",
        "tensile_strength_mpa": 40.0,
        "approx_price_usd_liter": 28.0,
        "use_case": "Lenses, hollow decorations, lighting enclosures, and jewelry masters.",
        "notes": "Highly resistant to yellowing compared to standard clear resins."
    },
    {
        "material_name": "Tough Flexible Resin",
        "brand": "Anycubic",
        "technology": "MSLA/LCD",
        "category": "Tough/Flexible",
        "shore_hardness": "76D",
        "tensile_strength_mpa": 25.0,
        "approx_price_usd_liter": 32.0,
        "use_case": "Bumper guards, handles, dampeners, and wear-and-tear protective shells.",
        "notes": "High elasticity combined with durability. Great for cushioning parts."
    },

    # --- SIRAYA TECH (6 Resins) ---
    {
        "material_name": "Blu Tough Resin",
        "brand": "Siraya Tech",
        "technology": "MSLA/LCD/DLP",
        "category": "Tough/Engineering",
        "shore_hardness": "85D",
        "tensile_strength_mpa": 44.0,
        "approx_price_usd_liter": 50.0,
        "use_case": "Functional mechanical assemblies, brackets, custom jigs, and load-bearing fixtures.",
        "notes": "Industry standard for desktop engineering. Excellent strength, shock resistance, and precision."
    },
    {
        "material_name": "Fast Easy Grey",
        "brand": "Siraya Tech",
        "technology": "MSLA/LCD",
        "category": "Standard/Rapid",
        "shore_hardness": "80D",
        "tensile_strength_mpa": 35.0,
        "approx_price_usd_liter": 33.0,
        "use_case": "Tabletop gaming miniatures, rapid design concepts, and large architectural mockups.",
        "notes": "Exceedingly popular due to fast print speeds, low viscosity, and ease of cleaning."
    },
    {
        "material_name": "Sculpt High Temp",
        "brand": "Siraya Tech",
        "technology": "MSLA/LCD/DLP",
        "category": "Engineering/High-Temp",
        "shore_hardness": "85D",
        "tensile_strength_mpa": 48.0,
        "approx_price_usd_liter": 45.0,
        "use_case": "Mold making for injection molding, vacuum forming inserts, and high-temp air/gas ducts.",
        "notes": "Heat deflection temperature (HDT) up to 160C (220C for Sculpt Ultra). Extremely rigid."
    },
    {
        "material_name": "Tenacious Flexible",
        "brand": "Siraya Tech",
        "technology": "MSLA/LCD",
        "category": "Flexible",
        "shore_hardness": "65D",
        "tensile_strength_mpa": 15.0,
        "approx_price_usd_liter": 65.0,
        "use_case": "Adding impact resistance to other resins (as an additive), custom gaskets, and RC car tires.",
        "notes": "Incredibly durable and impact-resistant. Often mixed with standard resins to prevent brittleness."
    },
    {
        "material_name": "Build Drillable",
        "brand": "Siraya Tech",
        "technology": "MSLA/LCD",
        "category": "Engineering",
        "shore_hardness": "77D",
        "tensile_strength_mpa": 33.0,
        "approx_price_usd_liter": 40.0,
        "use_case": "Tapped parts (threading), drilled brackets, and custom tool attachments.",
        "notes": "Engineered specifically to be drillable and tappable without cracking or shattering."
    },
    {
        "material_name": "Cast Purple",
        "brand": "Siraya Tech",
        "technology": "MSLA/LCD/DLP",
        "category": "Castable",
        "shore_hardness": "75D",
        "tensile_strength_mpa": 22.0,
        "approx_price_usd_liter": 65.0,
        "use_case": "Lost-wax investment casting of jewelry, art pieces, and custom metal accessories.",
        "notes": "Burns cleanly with minimal ash residue, ensuring clean molds for metal casting."
    },

    # --- PHROZEN (6 Resins) ---
    {
        "material_name": "Aqua-Gray 8K",
        "brand": "Phrozen",
        "technology": "MSLA/LCD",
        "category": "Standard",
        "shore_hardness": "85D",
        "tensile_strength_mpa": 35.0,
        "approx_price_usd_liter": 49.0,
        "use_case": "Ultra-high detail 3D figures, historical miniatures, and showcase products.",
        "notes": "Specially formulated for 8K LCD screens to render insanely sharp details and fine lines."
    },
    {
        "material_name": "Speed Resin",
        "brand": "Phrozen",
        "technology": "MSLA/LCD",
        "category": "Rapid",
        "shore_hardness": "79D",
        "tensile_strength_mpa": 25.0,
        "approx_price_usd_liter": 35.0,
        "use_case": "Same-day architectural models, massive volume prototype testing, and design checks.",
        "notes": "Formulated to cure extremely fast, making it possible to print large models in hours."
    },
    {
        "material_name": "TR300 Ultra-High Temp",
        "brand": "Phrozen",
        "technology": "MSLA/LCD/DLP",
        "category": "Engineering/High-Temp",
        "shore_hardness": "80D",
        "tensile_strength_mpa": 32.0,
        "approx_price_usd_liter": 80.0,
        "use_case": "Dental thermoforming molds, industrial hot air nozzles, and testing in hot environments.",
        "notes": "Resists temperatures up to 300C. Excellent stiffness and low thermal expansion."
    },
    {
        "material_name": "Onyx Rigid Pro410",
        "brand": "Phrozen",
        "technology": "MSLA/LCD",
        "category": "Engineering/Tough",
        "shore_hardness": "78D",
        "tensile_strength_mpa": 43.0,
        "approx_price_usd_liter": 75.0,
        "use_case": "Functional engineering parts, replacement brackets, handles, and mechanical casing.",
        "notes": "Co-developed with Henkel. Excellent strength, rigidity, and dimensional stability."
    },
    {
        "material_name": "Rock-Black Stiff",
        "brand": "Phrozen",
        "technology": "MSLA/LCD",
        "category": "Rigid/Engineering",
        "shore_hardness": "81D",
        "tensile_strength_mpa": 30.0,
        "approx_price_usd_liter": 45.0,
        "use_case": "High-stiffness brackets, model chassis, structural boxes, and snap-on parts.",
        "notes": "High heat deflection temperature (~97C) and high resistance to deformation."
    },
    {
        "material_name": "Wax-like Castable W40",
        "brand": "Phrozen",
        "technology": "MSLA/LCD/DLP",
        "category": "Castable",
        "shore_hardness": "70D",
        "tensile_strength_mpa": 15.0,
        "approx_price_usd_liter": 99.0,
        "use_case": "Jewelry investment casting (rings, earrings, crowns, intricate filigree).",
        "notes": "Contains 40% real wax. Low shrinkage, reliable burnout with no ash residue."
    },

    # --- MONOCURE3D (6 Resins) ---
    {
        "material_name": "Rapid Standard Grey",
        "brand": "Monocure3D",
        "technology": "MSLA/LCD",
        "category": "Standard",
        "shore_hardness": "80D",
        "tensile_strength_mpa": 35.0,
        "approx_price_usd_liter": 35.0,
        "use_case": "Hobbyist models, general-purpose display pieces, and rapid low-cost prototypes.",
        "notes": "Australian manufactured. Wide UV curing range (225nm to 420nm) for great compatibility."
    },
    {
        "material_name": "Rapid TUFF Grey",
        "brand": "Monocure3D",
        "technology": "MSLA/LCD/DLP",
        "category": "Tough/ABS-Like",
        "shore_hardness": "84D",
        "tensile_strength_mpa": 52.0,
        "approx_price_usd_liter": 65.0,
        "use_case": "Heavy-duty functional prototypes, high-stress enclosures, and industrial fixtures.",
        "notes": "Advanced polyurethane blend offering high tensile strength, stiffness, and durability."
    },
    {
        "material_name": "Rapid FLEX",
        "brand": "Monocure3D",
        "technology": "MSLA/LCD",
        "category": "Flexible",
        "shore_hardness": "60A",
        "tensile_strength_mpa": 5.0,
        "approx_price_usd_liter": 80.0,
        "use_case": "Custom rubber handles, cushioning pads, stamp templates, and orthotic inserts.",
        "notes": "Highly elastic, rubber-like feel. Can be mixed with Standard/Tuff resins to tune flexibility."
    },
    {
        "material_name": "Rapid Dental Model",
        "brand": "Monocure3D",
        "technology": "MSLA/LCD/DLP",
        "category": "Dental",
        "shore_hardness": "85D",
        "tensile_strength_mpa": 45.0,
        "approx_price_usd_liter": 75.0,
        "use_case": "High-precision orthodontic dental models, study casts, and prosthetics.",
        "notes": "Ultra-low shrinkage and high gypsum-like matte texture for professional dental offices."
    },
    {
        "material_name": "Rapid CAST",
        "brand": "Monocure3D",
        "technology": "MSLA/LCD/DLP",
        "category": "Castable",
        "shore_hardness": "72D",
        "tensile_strength_mpa": 18.0,
        "approx_price_usd_liter": 95.0,
        "use_case": "Direct investment casting for jewelry makers and dental lab castings.",
        "notes": "Formulated to burn out fully at standard casting ramp-up schedules without cracking molds."
    },
    {
        "material_name": "Big Vat Resin (Industrial)",
        "brand": "Monocure3D",
        "technology": "SLA/MSLA",
        "category": "Industrial/Standard",
        "shore_hardness": "82D",
        "tensile_strength_mpa": 38.0,
        "approx_price_usd_liter": 45.0,
        "use_case": "Large-format 3D printing, bulk industrial manufacturing, and large prototypes.",
        "notes": "Designed with low viscosity and low settlement rate for large-volume printers."
    },

    # --- LIQCREATE (6 Resins) ---
    {
        "material_name": "Premium Tough",
        "brand": "Liqcreate",
        "technology": "MSLA/LCD/DLP",
        "category": "Tough/ABS-Like",
        "shore_hardness": "78D",
        "tensile_strength_mpa": 42.0,
        "approx_price_usd_liter": 75.0,
        "use_case": "Functional covers, prototype housings, mechanical snap-fits, and structural parts.",
        "notes": "Excellent impact resistance combined with a beautiful semi-matte finish."
    },
    {
        "material_name": "Strong-X",
        "brand": "Liqcreate",
        "technology": "SLA/MSLA/DLP",
        "category": "Rigid/Engineering",
        "shore_hardness": "85D",
        "tensile_strength_mpa": 91.0,
        "approx_price_usd_liter": 135.0,
        "use_case": "Injection molding inserts, heavy-duty mechanical brackets, and high-temp components.",
        "notes": "One of the strongest resins on the market with a tensile strength exceeding 90 MPa."
    },
    {
        "material_name": "Flexible-X",
        "brand": "Liqcreate",
        "technology": "SLA/MSLA/DLP",
        "category": "Flexible",
        "shore_hardness": "55A",
        "tensile_strength_mpa": 4.5,
        "approx_price_usd_liter": 120.0,
        "use_case": "Engineered bellows, protective boots, heavy-duty gaskets, and robotic soft grippers.",
        "notes": "Outstanding rebound, durability, and elongation. Exceptionally high fatigue resistance."
    },
    {
        "material_name": "Clear Impact",
        "brand": "Liqcreate",
        "technology": "SLA/MSLA/DLP",
        "category": "Tough/Clear",
        "shore_hardness": "75D",
        "tensile_strength_mpa": 40.0,
        "approx_price_usd_liter": 110.0,
        "use_case": "Transparent protective covers, flow-visualization models, lenses, and functional covers.",
        "notes": "An optically clear resin with high impact resistance and structural durability."
    },
    {
        "material_name": "Wax Castable",
        "brand": "Liqcreate",
        "technology": "MSLA/LCD/DLP",
        "category": "Castable",
        "shore_hardness": "74D",
        "tensile_strength_mpa": 20.0,
        "approx_price_usd_liter": 125.0,
        "use_case": "Precision jewelry models, crowns, and bridges for casting or pressing.",
        "notes": "Infused with real wax. Assures clean burnout and smooth metal surfaces."
    },
    {
        "material_name": "Composite-X",
        "brand": "Liqcreate",
        "technology": "SLA/MSLA/DLP",
        "category": "Rigid/Composite",
        "shore_hardness": "90D",
        "tensile_strength_mpa": 140.0,
        "approx_price_usd_liter": 198.0,
        "use_case": "Wind tunnel testing models, aerospace brackets, tooling fixtures, and extreme-load molds.",
        "notes": "Micro-ceramic reinforced. Insanely high flexural modulus (9000+ MPa) and strength."
    },

    # --- APPLYLABWORK (6 Resins) ---
    {
        "material_name": "MSLA Modeling Series Olive",
        "brand": "ApplyLabWork",
        "technology": "MSLA/LCD",
        "category": "Standard",
        "shore_hardness": "82D",
        "tensile_strength_mpa": 38.0,
        "approx_price_usd_liter": 55.0,
        "use_case": "Tabletop gaming figures, decorative hobby models, and highly-detailed show pieces.",
        "notes": "Outstanding dimensional accuracy, low shrinkage, and sharp details."
    },
    {
        "material_name": "MSLA Spring Pink",
        "brand": "ApplyLabWork",
        "technology": "MSLA/LCD",
        "category": "Flexible",
        "shore_hardness": "57A",
        "tensile_strength_mpa": 1.5,
        "approx_price_usd_liter": 70.0,
        "use_case": "Soft gasket seals, footwear modeling, vibration isolators, and squeezable parts.",
        "notes": "Features super quick spring back characteristics and high tear strength."
    },
    {
        "material_name": "SLA Modeling Series Formlabs Comp",
        "brand": "ApplyLabWork",
        "technology": "SLA",
        "category": "Standard",
        "shore_hardness": "82D",
        "tensile_strength_mpa": 42.0,
        "approx_price_usd_liter": 60.0,
        "use_case": "Everyday functional prototypes and visual mockups printed on Formlabs SLA machines.",
        "notes": "Direct drop-in replacement for Formlabs Standard Grey/Clear resins. Save cartridge costs."
    },
    {
        "material_name": "SLA Spring Pink Formlabs Comp",
        "brand": "ApplyLabWork",
        "technology": "SLA",
        "category": "Flexible",
        "shore_hardness": "58A",
        "tensile_strength_mpa": 1.8,
        "approx_price_usd_liter": 90.0,
        "use_case": "Rubber-like mechanical parts, custom soft grips, and dampers printed on Formlabs SLA.",
        "notes": "Formlabs-compatible formulation. Stretches and rebounds quickly like commercial elastomers."
    },
    {
        "material_name": "Castable Plus Black",
        "brand": "ApplyLabWork",
        "technology": "MSLA/LCD/DLP",
        "category": "Castable",
        "shore_hardness": "70D",
        "tensile_strength_mpa": 14.0,
        "approx_price_usd_liter": 99.0,
        "use_case": "Fine-filigree jewelry design, organic patterns, and direct metal investment casting.",
        "notes": "Specifically designed to minimize thermal expansion during burnout to avoid mold cracking."
    },
    {
        "material_name": "BioModeling Sand",
        "brand": "ApplyLabWork",
        "technology": "MSLA/LCD/SLA",
        "category": "Dental/Medical",
        "shore_hardness": "85D",
        "tensile_strength_mpa": 46.0,
        "approx_price_usd_liter": 55.0,
        "use_case": "Biocompatible dental models, surgical templates, and custom medical prototypes.",
        "notes": "ISO 10993-5 certified for biocompatibility. High accuracy and stable dimensions."
    },

    # --- BASF ULTRACUR3D (6 Resins) ---
    {
        "material_name": "Ultracur3D RG 35",
        "brand": "BASF Ultracur3D",
        "technology": "MSLA/LCD/DLP/SLA",
        "category": "Rigid/Engineering",
        "shore_hardness": "85D",
        "tensile_strength_mpa": 80.0,
        "approx_price_usd_liter": 115.0,
        "use_case": "Automotive interior housings, electrical connectors, custom mounting brackets, and jigs.",
        "notes": "Excellent combination of mechanical strength, stiffness, and high dimensional accuracy."
    },
    {
        "material_name": "Ultracur3D RG 1100",
        "brand": "BASF Ultracur3D",
        "technology": "MSLA/LCD/DLP/SLA",
        "category": "Rigid/Engineering",
        "shore_hardness": "84D",
        "tensile_strength_mpa": 70.0,
        "approx_price_usd_liter": 130.0,
        "use_case": "High-stiffness industrial gears, engineering housings, and structural connectors.",
        "notes": "Superior aging and chemical resistance. Extremely low water absorption."
    },
    {
        "material_name": "Ultracur3D ST 45",
        "brand": "BASF Ultracur3D",
        "technology": "MSLA/LCD/DLP/SLA",
        "category": "Tough/Engineering",
        "shore_hardness": "80D",
        "tensile_strength_mpa": 60.0,
        "approx_price_usd_liter": 110.0,
        "use_case": "High-performance functional parts, outdoor enclosures, brackets, and protective covers.",
        "notes": "Offers long-term UV resistance, very high impact strength, and excellent surface finish."
    },
    {
        "material_name": "Ultracur3D EL 60",
        "brand": "BASF Ultracur3D",
        "technology": "DLP/MSLA",
        "category": "Flexible/Elastic",
        "shore_hardness": "60A",
        "tensile_strength_mpa": 5.0,
        "approx_price_usd_liter": 140.0,
        "use_case": "Robotic soft-grippers, athletic shoe midsoles, industrial dampers, and elastic seals.",
        "notes": "An elastomeric resin with exceptional tear resistance and rapid energy rebound."
    },
    {
        "material_name": "Ultracur3D FL 60",
        "brand": "BASF Ultracur3D",
        "technology": "DLP/MSLA",
        "category": "Flexible",
        "shore_hardness": "62A",
        "tensile_strength_mpa": 3.0,
        "approx_price_usd_liter": 135.0,
        "use_case": "Flexible hose connections, custom rubber bellows, dampening gaskets, and wire boots.",
        "notes": "High elasticity and low hardness. Outstanding fatigue behavior under repeated load."
    },
    {
        "material_name": "Ultracur3D DM 2505",
        "brand": "BASF Ultracur3D",
        "technology": "LCD/DLP",
        "category": "Dental",
        "shore_hardness": "83D",
        "tensile_strength_mpa": 50.0,
        "approx_price_usd_liter": 120.0,
        "use_case": "High-accuracy dental models, prosthetic study arches, and orthodontic tooling.",
        "notes": "Engineered for high dimensional stability and precision. Matte surface helps scanning."
    },

    # --- 3DRESYNS (6 Resins) ---
    {
        "material_name": "3DRESYN RIC-UHTD90 Bio",
        "brand": "3DRESYNS",
        "technology": "SLA/MSLA/DLP",
        "category": "Dental/Engineering",
        "shore_hardness": "90D",
        "tensile_strength_mpa": 65.0,
        "approx_price_usd_liter": 195.0,
        "use_case": "Biocompatible surgical templates, dental arches, and high-stiffness micro-molds.",
        "notes": "Biocompatible ultra-hard & tough resin. Excellent chemical and heat resistance."
    },
    {
        "material_name": "3DRESYN Soft SR (A30)",
        "brand": "3DRESYNS",
        "technology": "SLA/MSLA/DLP",
        "category": "Flexible",
        "shore_hardness": "30A",
        "tensile_strength_mpa": 2.0,
        "approx_price_usd_liter": 215.0,
        "use_case": "Silicone-like gaskets, medical training organs, soft prosthetic pads, and soft grips.",
        "notes": "One of the softest elastomeric resins available, simulating low-durometer silicone rubber."
    },
    {
        "material_name": "3DRESYN RIC-TFD60 Bio",
        "brand": "3DRESYNS",
        "technology": "SLA/MSLA/DLP",
        "category": "Tough/Foldable",
        "shore_hardness": "60D",
        "tensile_strength_mpa": 35.0,
        "approx_price_usd_liter": 195.0,
        "use_case": "Snap-fit functional containers, foldable living hinges, and wearable device bands.",
        "notes": "Unique polymer design that can fold completely and return to shape without crease marks."
    },
    {
        "material_name": "3DRESYN HDT1 High Temp",
        "brand": "3DRESYNS",
        "technology": "SLA/MSLA/DLP",
        "category": "Engineering/High-Temp",
        "shore_hardness": "88D",
        "tensile_strength_mpa": 40.0,
        "approx_price_usd_liter": 220.0,
        "use_case": "Ultra-high temperature gas channels, heat-exchanger prototypes, and electronic sockets.",
        "notes": "Withstands temperatures over 290C. Highly rigid and dimensionally stable."
    },
    {
        "material_name": "3DRESYN CR-UT Chemical Resistant",
        "brand": "3DRESYNS",
        "technology": "SLA/MSLA/DLP",
        "category": "Tough/Chemical-Resistant",
        "shore_hardness": "82D",
        "tensile_strength_mpa": 50.0,
        "approx_price_usd_liter": 240.0,
        "use_case": "Industrial chemical pipes, fuel tank fittings, acid/alkali storage caps, and fluidic manifolds.",
        "notes": "Engineered to withstand prolonged exposure to aggressive chemicals, fuels, and solvents."
    },
    {
        "material_name": "3DRESYN Nylon-like",
        "brand": "3DRESYNS",
        "technology": "SLA/MSLA/DLP",
        "category": "Engineering/Nylon-Like",
        "shore_hardness": "75D",
        "tensile_strength_mpa": 38.0,
        "approx_price_usd_liter": 195.0,
        "use_case": "Screws, nuts, industrial gears, sliding tracks, and durable low-friction functional parts.",
        "notes": "Mimics the self-lubricating, tough, and slightly flexible properties of Nylon-12 polyamide."
    }
]

# Verify counts and structure
print(f"Total resins: {len(resins)}")
brand_counts = {}
for r in resins:
    brand_counts[r['brand']] = brand_counts.get(r['brand'], 0) + 1
print("Brand counts:")
for b, c in brand_counts.items():
    print(f"  {b}: {c}")

with open("resins.json", "w") as f:
    json.dump(resins, f, indent=4)
