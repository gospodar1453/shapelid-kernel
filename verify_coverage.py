import json

with open("output.json") as f:
    json_data = json.load(f)

json_keys = set(item["material_key"] for item in json_data)

prompt_items = [
    # SLS
    "PA12 / Nylon 12",
    "PA11 / Nylon 11",
    "PA12 Carbon Fiber",
    "PA12 Glass Beads",
    "PP Polypropylene SLS",
    "TPE Flexible SLS",
    "PrimeCast Investment Casting SLS",
    "TPA Elastomer MJF",
    
    # MJF
    "PA12 Glass Beads MJF",
    "TPA Elastomer MJF",
    
    # DMLS
    "Titanium CP Grade 2",
    "Titanium Grade 5 / Ti-6Al-4V",
    "Stainless Steel 316L",
    "Stainless Steel 17-4PH",
    "Maraging Steel MS1",
    "Maraging Steel",
    "Tool Steel 1.2709/MS1",
    "Inconel 625",
    "Inconel 718",
    "Copper Pure",
    
    # SLA
    "Standard Transparent ABS-like",
    "Standard Grey ABS-like",
    "Standard Black ABS-like",
    "Standard White ABS-like",
    "Dental Model Resin",
    "Rigid/Glass-Filled Engineering Resin",
    "Water-Washable Resin",
    "Plant-Based/Eco Resin",
    "Castable Wax Resin",
    
    # Polyjet
    "Photopolymer Rubber-like",
    "Photopolymer Rigid",
    
    # CNC
    "Aluminum 6061, 5083, 6082, 2024, 1050",
    "Stainless Steel 303, 304, 304L, 316, 316L, 316Ti",
    "Steel C45, S235JR, S355, 4130, 42CrMo4, 25CrMo4, 1.0511",
    "Titanium Grade 2, Grade 5",
    "Brass Ms58",
    "Copper",
    "POM/Delrin",
    "PEEK",
    "PC Polycarbonate",
    "Acrylic",
    "UHMW PE",
    "Nylon 6",
    
    # Injection Molding
    "ABS",
    "PP",
    "PC",
    "Nylon 6, Nylon 66",
    "POM/Delrin",
    "HDPE",
    "PVC",
    "PET",
    "PS",
    "PBT",
    "PPS",
    "PEI",
    "PEEK",
    "TPE",
    "TPV",
    "Acrylic PMMA",
    "PA6-GF",
    
    # Die Casting
    "Aluminium 46100/ADC12",
    "Aluminium 46500/A380",
    
    # Sheet metal
    "Galvanized Steel",
    "Steel S235JR, S355, DC01",
    "Stainless Steel 304, 316L",
    "Aluminium 5754, 5083, 6082, 1050, 7075",
    
    # Vacuum casting
    "ABS PR700, PR2000, PRA794",
    "HDPE/PP PR777",
    "PC/ABS PRF100",
    "PC/PMMA Cristal HRI 35, PRC1819"
]

print("Total prompt items listed:", len(prompt_items))
print("Total JSON keys in output:", len(json_keys))

missing = [item for item in prompt_items if item not in json_keys]
if missing:
    print("MISSING ITEMS:", missing)
else:
    print("ALL PROMPT ITEMS ARE COVERED!")

