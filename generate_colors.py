import json

data = [
    # SLS
    {
        "material_key": "PA12 / Nylon 12",
        "color_name": "Off-White / Cream",
        "hex_code": "#F4F0EA",
        "notes": "Un-dyed SLS PA12 powder produces parts with a slightly porous, matte off-white appearance."
    },
    {
        "material_key": "PA11 / Nylon 11",
        "color_name": "Warm Off-White / Light Cream",
        "hex_code": "#EFE8D8",
        "notes": "Bio-based polyamide powder with a warm cream/yellowish off-white tone and matte finish."
    },
    {
        "material_key": "PA12 Carbon Fiber",
        "color_name": "Matte Charcoal / Black",
        "hex_code": "#2B2B2C",
        "notes": "Dark charcoal gray to matte black finish due to integrated carbon fibers."
    },
    {
        "material_key": "PA12 Glass Beads",
        "color_name": "Light Grayish Off-White",
        "hex_code": "#E5E2DC",
        "notes": "Matte off-white to pale gray finish with a slightly textured surface from embedded glass beads."
    },
    {
        "material_key": "PP Polypropylene SLS",
        "color_name": "Translucent Off-White / Milky White",
        "hex_code": "#F0EFEA",
        "notes": "Semi-translucent milky white color with a smooth, wax-like matte surface."
    },
    {
        "material_key": "TPE Flexible SLS",
        "color_name": "Off-White / Bright Cream",
        "hex_code": "#F6F5F2",
        "notes": "Soft elastomeric polymer with a matte, rubbery off-white finish."
    },
    {
        "material_key": "PrimeCast Investment Casting SLS",
        "color_name": "Medium Gray",
        "hex_code": "#7D8288",
        "notes": "EOS PrimeCast 101 polystyrene powder is grey for easy pattern inspection and clean burnout."
    },
    {
        "material_key": "TPA Elastomer MJF",
        "color_name": "Natural White",
        "hex_code": "#FAFAFA",
        "notes": "HP 3D HR TPA produces white, lightweight flexible elastomeric parts in Multi Jet Fusion."
    },

    # MJF
    {
        "material_key": "PA12 Glass Beads MJF",
        "color_name": "Dark Stone Gray",
        "hex_code": "#5A5E61",
        "notes": "Un-dyed raw MJF parts have a stone gray/graphite matte finish caused by the fusing agent."
    },

    # DMLS
    {
        "material_key": "Titanium CP Grade 2",
        "color_name": "Dark Metallic Gray",
        "hex_code": "#8D9194",
        "notes": "Matte dark gray metallic surface characteristic of unpolished 3D printed pure titanium."
    },
    {
        "material_key": "Titanium Grade 5 / Ti-6Al-4V",
        "color_name": "Dark Metallic Gray",
        "hex_code": "#82868A",
        "notes": "Satin dark gray metal finish on sintered aerospace titanium alloy."
    },
    {
        "material_key": "Stainless Steel 316L",
        "color_name": "Metallic Silver-Gray",
        "hex_code": "#C4C6C8",
        "notes": "Satin silver-gray metal appearance with minor surface roughness."
    },
    {
        "material_key": "Stainless Steel 17-4PH",
        "color_name": "Metallic Silver-Gray",
        "hex_code": "#B8BABC",
        "notes": "Metallic silver-gray finish with high strength and corrosion resistance."
    },
    {
        "material_key": "Maraging Steel MS1",
        "color_name": "Dark Steel Gray",
        "hex_code": "#787C80",
        "notes": "Matte dark steel gray metallic finish typical of tool steel grade alloys."
    },
    {
        "material_key": "Maraging Steel",
        "color_name": "Dark Steel Gray",
        "hex_code": "#787C80",
        "notes": "Matte dark gray metallic surface prior to heat treatment and polishing."
    },
    {
        "material_key": "Tool Steel 1.2709/MS1",
        "color_name": "Dark Steel Gray",
        "hex_code": "#75797D",
        "notes": "Matte dark gray metallic appearance on as-printed tool steel components."
    },
    {
        "material_key": "Inconel 625",
        "color_name": "Dark Nickel Silver-Gray",
        "hex_code": "#8C8F92",
        "notes": "Dark metallic gray finish typical of nickel-chromium superalloys."
    },
    {
        "material_key": "Inconel 718",
        "color_name": "Dark Nickel Silver-Gray",
        "hex_code": "#8A8D90",
        "notes": "Satin dark nickel-gray metal finish with high heat resistance."
    },
    {
        "material_key": "Copper Pure",
        "color_name": "Reddish Copper / Orange",
        "hex_code": "#C87D55",
        "notes": "Matte metallic reddish-copper color of high-purity sintered copper."
    },

    # SLA
    {
        "material_key": "Standard Transparent ABS-like",
        "color_name": "Translucent Clear / Slight Yellow Tint",
        "hex_code": "#E8ECEB",
        "notes": "High transparency with a faint yellowish tint typical of unpigmented acrylic UV resin."
    },
    {
        "material_key": "Standard Grey ABS-like",
        "color_name": "Opaque Medium Gray",
        "hex_code": "#8A8D8F",
        "notes": "Smooth opaque neutral grey finish designed for visual prototyping and defect inspection."
    },
    {
        "material_key": "Standard Black ABS-like",
        "color_name": "Opaque Matte Black",
        "hex_code": "#22252A",
        "notes": "Opaque dark black smooth finish."
    },
    {
        "material_key": "Standard White ABS-like",
        "color_name": "Opaque Bright White",
        "hex_code": "#F8F9FA",
        "notes": "Clean opaque white smooth surface."
    },
    {
        "material_key": "Dental Model Resin",
        "color_name": "Opaque Matte Peach / Beige",
        "hex_code": "#E3C5AA",
        "notes": "Matte beige/peach tone optimized for visual contrast of dental margins and crown preparations."
    },
    {
        "material_key": "Rigid/Glass-Filled Engineering Resin",
        "color_name": "Opaque Light Gray / Off-White",
        "hex_code": "#E3E5E7",
        "notes": "Smooth opaque light gray or off-white finish composite reinforced with glass micro-particles."
    },
    {
        "material_key": "Water-Washable Resin",
        "color_name": "Opaque Neutral Gray",
        "hex_code": "#9FA2A6",
        "notes": "Default standard resin formulation cleanable with water, typically dyed neutral gray."
    },
    {
        "material_key": "Plant-Based/Eco Resin",
        "color_name": "Translucent Light Green / Pale Clear",
        "hex_code": "#A8C69F",
        "notes": "Unpigmented soybean-based eco resin has a distinct translucent pale green/yellowish tint."
    },
    {
        "material_key": "Castable Wax Resin",
        "color_name": "Translucent Deep Royal Blue",
        "hex_code": "#2A4480",
        "notes": "Translucent dark blue/violet tint designed for clean investment casting burnout and detail checking."
    },

    # Polyjet
    {
        "material_key": "Photopolymer Rubber-like",
        "color_name": "Translucent Clear / Off-White",
        "hex_code": "#E6E9E8",
        "notes": "Natural unpigmented PolyJet flexible photopolymer (e.g., Agilus30 Clear, TangoPlus) is translucent clear."
    },
    {
        "material_key": "Photopolymer Rigid",
        "color_name": "Opaque Bright White",
        "hex_code": "#F8F9FA",
        "notes": "Standard default rigid PolyJet material (e.g., VeroWhite) is opaque bright white."
    },

    # CNC Machining
    {
        "material_key": "Aluminum 6061, 5083, 6082, 2024, 1050",
        "color_name": "Bright Metallic Silver",
        "hex_code": "#D4D7D9",
        "notes": "Bright silver metallic luster with visible directional tool machining marks."
    },
    {
        "material_key": "Stainless Steel 303, 304, 304L, 316, 316L, 316Ti",
        "color_name": "Lustrous Silver-Gray",
        "hex_code": "#C8CBCE",
        "notes": "Clean silver metallic sheen with high corrosion resistance."
    },
    {
        "material_key": "Steel C45, S235JR, S355, 4130, 42CrMo4, 25CrMo4, 1.0511",
        "color_name": "Metallic Medium Gray",
        "hex_code": "#8E9296",
        "notes": "Medium steel gray metallic surface; requires oil or coating to prevent oxidation."
    },
    {
        "material_key": "Titanium Grade 2, Grade 5",
        "color_name": "Metallic Dark Silver-Gray",
        "hex_code": "#92969A",
        "notes": "Satin dark gray metallic appearance, darker and cooler tone than aluminum."
    },
    {
        "material_key": "Brass Ms58",
        "color_name": "Warm Metallic Gold / Yellow Brass",
        "hex_code": "#D1A751",
        "notes": "Bright yellowish-gold metallic appearance."
    },
    {
        "material_key": "Copper",
        "color_name": "Metallic Reddish Orange / Copper",
        "hex_code": "#B86D43",
        "notes": "High reflectivity bright reddish-orange copper metal finish."
    },
    {
        "material_key": "POM/Delrin",
        "color_name": "Natural Opaque White",
        "hex_code": "#FAF9F5",
        "notes": "Opaque milky white smooth engineered acetal plastic finish."
    },
    {
        "material_key": "PEEK",
        "color_name": "Natural Tan / Beige",
        "hex_code": "#C8B195",
        "notes": "Opaque light brownish-tan/beige color characteristic of raw polyether ether ketone."
    },
    {
        "material_key": "PC Polycarbonate",
        "color_name": "Water Clear / Transparent",
        "hex_code": "#EBF3F5",
        "notes": "High optical transparency; machined parts can be polished to water-clear clarity."
    },
    {
        "material_key": "Acrylic",
        "color_name": "Optically Clear / Transparent",
        "hex_code": "#F0F8FF",
        "notes": "Exceptional optical clarity, glass-like transparent acrylic (PMMA)."
    },
    {
        "material_key": "UHMW PE",
        "color_name": "Natural Milky Off-White",
        "hex_code": "#F3F2EE",
        "notes": "Opaque to semi-translucent milky white with a low-friction waxy feel."
    },
    {
        "material_key": "Nylon 6",
        "color_name": "Natural Off-White / Cream",
        "hex_code": "#EFECE6",
        "notes": "Semi-translucent light off-white/cream colored thermoplastic."
    },

    # Injection Molding
    {
        "material_key": "ABS",
        "color_name": "Natural Cream / Light Ivory",
        "hex_code": "#F3EED9",
        "notes": "Unpigmented raw ABS resin pellets yield an opaque light yellowish-cream appearance."
    },
    {
        "material_key": "PP",
        "color_name": "Natural Translucent Milky White",
        "hex_code": "#F4F3ED",
        "notes": "Semi-translucent milky white flexible polymer finish."
    },
    {
        "material_key": "PC",
        "color_name": "Optically Clear / Transparent",
        "hex_code": "#EAF2F5",
        "notes": "High clarity amorphous transparent plastic."
    },
    {
        "material_key": "Nylon 6, Nylon 66",
        "color_name": "Natural Off-White / Cream",
        "hex_code": "#EFEBE4",
        "notes": "Semi-translucent light off-white/cream unfilled polyamide resin."
    },
    {
        "material_key": "POM/Delrin",
        "color_name": "Natural Opaque White",
        "hex_code": "#FBF9F3",
        "notes": "Opaque clean white acetal homopolymer/copolymer."
    },
    {
        "material_key": "HDPE",
        "color_name": "Natural Milky White",
        "hex_code": "#F2F1EA",
        "notes": "Semi-translucent milky white waxy polyolefin finish."
    },
    {
        "material_key": "PVC",
        "color_name": "Natural Translucent Off-White",
        "hex_code": "#EDEDE6",
        "notes": "Unpigmented rigid or flexible PVC is semi-translucent to grayish off-white."
    },
    {
        "material_key": "PET",
        "color_name": "Crystal Clear / Transparent",
        "hex_code": "#EAF3F6",
        "notes": "Optically clear amorphous transparent resin."
    },
    {
        "material_key": "PS",
        "color_name": "Glass Clear / Transparent",
        "hex_code": "#F2F7FA",
        "notes": "General purpose crystal polystyrene (GPPS) is transparent clear."
    },
    {
        "material_key": "PBT",
        "color_name": "Natural Opaque White",
        "hex_code": "#F6F4EE",
        "notes": "Opaque white/off-white semi-crystalline polyester thermoplastic."
    },
    {
        "material_key": "PPS",
        "color_name": "Natural Dark Brownish Tan",
        "hex_code": "#78624C",
        "notes": "Opaque dark brown/tan tone due to intrinsic polyphenylene sulfide structure."
    },
    {
        "material_key": "PEI",
        "color_name": "Natural Amber / Translucent Honey",
        "hex_code": "#C88A36",
        "notes": "Characteristic transparent golden-amber/honey color of unfilled PEI (Ultem)."
    },
    {
        "material_key": "PEEK",
        "color_name": "Natural Tan / Beige",
        "hex_code": "#C8B195",
        "notes": "Opaque light brown-beige tone characteristic of raw PEEK resin."
    },
    {
        "material_key": "TPE",
        "color_name": "Natural Translucent Off-White",
        "hex_code": "#F5F4EF",
        "notes": "Semi-translucent off-white flexible elastomer pellets."
    },
    {
        "material_key": "TPV",
        "color_name": "Natural Dark Charcoal / Black",
        "hex_code": "#333638",
        "notes": "Thermoplastic vulcanizate (e.g. Santoprene) naturally cured rubber phase gives a dark charcoal finish."
    },
    {
        "material_key": "Acrylic PMMA",
        "color_name": "Optically Clear / Transparent",
        "hex_code": "#F0F7FA",
        "notes": "High optical transparency, water-clear finish."
    },
    {
        "material_key": "PA6-GF",
        "color_name": "Opaque Off-White / Light Stone Gray",
        "hex_code": "#DDD8D0",
        "notes": "Glass fiber reinforcement produces an opaque light greyish off-white finish."
    },

    # Die Casting
    {
        "material_key": "Aluminium 46100/ADC12",
        "color_name": "Metallic Silver-Gray",
        "hex_code": "#ADB0B3",
        "notes": "As-cast metallic silver-gray surface finish typical of Japanese/global aluminum die castings."
    },
    {
        "material_key": "Aluminium 46500/A380",
        "color_name": "Metallic Silver-Gray",
        "hex_code": "#ABAEB1",
        "notes": "Standard North American die casting aluminum alloy with a matte metallic silver-gray skin."
    },

    # Sheet Metal
    {
        "material_key": "Galvanized Steel",
        "color_name": "Spangled Zinc Metallic Gray",
        "hex_code": "#B2B8BC",
        "notes": "Metallic light gray finish with characteristic zinc crystal spangle visual pattern."
    },
    {
        "material_key": "Steel S235JR, S355, DC01",
        "color_name": "Dark Steel Gray",
        "hex_code": "#6C7074",
        "notes": "Matte dark steel gray metallic surface from mill scale or cold-rolled finish."
    },
    {
        "material_key": "Stainless Steel 304, 316L",
        "color_name": "Satin Metallic Silver",
        "hex_code": "#C5C8CB",
        "notes": "Clean satin silver metallic surface with mill finish."
    },
    {
        "material_key": "Aluminium 5754, 5083, 6082, 1050, 7075",
        "color_name": "Bright Metallic Silver",
        "hex_code": "#D2D5D8",
        "notes": "Bright reflective silver aluminum sheet surface."
    },

    # Vacuum Casting
    {
        "material_key": "ABS PR700, PR2000, PRA794",
        "color_name": "Opaque Off-White / Cream (PR700/PR2000)",
        "hex_code": "#F2EFE9",
        "notes": "Synthene PR700 and PR2000 polyurethane resins yield opaque off-white/cream ABS-like parts; PRA794 flame retardant variant is dark brown."
    },
    {
        "material_key": "HDPE/PP PR777",
        "color_name": "Translucent Off-White / Cream",
        "hex_code": "#EDE8DE",
        "notes": "Synthene PR777 yields semi-flexible off-white/cream parts simulating HDPE and PP."
    },
    {
        "material_key": "PC/ABS PRF100",
        "color_name": "Water Clear / Transparent",
        "hex_code": "#E8F0F2",
        "notes": "Synthene PRF100 is a food-grade transparent water-clear polyurethane resin."
    },
    {
        "material_key": "PC/PMMA Cristal HRI 35, PRC1819",
        "color_name": "Optically Clear / Water Clear",
        "hex_code": "#ECF5F8",
        "notes": "Synthene Cristal HRI 35 and PRC1819 are high-clarity UV-stable clear polyurethane resins simulating optical PC and PMMA."
    }
]

with open("output.json", "w") as f:
    json.dump(data, f, indent=2)

print("Saved output.json successfully!")
