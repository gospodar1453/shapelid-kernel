import json

with open('materials.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Verification
required_keys = {
    "material_name": str,
    "brand": str,
    "category": str,
    "subcategory": str,
    "key_properties": list,
    "approx_price_usd_kg": (int, float),
    "colors_available": bool,
    "notes": str
}

errors = []
for index, item in enumerate(data):
    for key, expected_type in required_keys.items():
        if key not in item:
            errors.append(f"Item {index} is missing key: '{key}'")
        else:
            val = item[key]
            if not isinstance(val, expected_type):
                errors.append(f"Item {index} key '{key}' has type {type(val)} instead of {expected_type}")
            if key == "key_properties":
                if not all(isinstance(x, str) for x in val):
                    errors.append(f"Item {index} key 'key_properties' has non-string elements.")

if errors:
    print("Verification failed! Errors:")
    for error in errors:
        print(f"  - {error}")
else:
    print(f"Verification passed! All {len(data)} items match the requested schema perfectly.")
