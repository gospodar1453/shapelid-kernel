import sys
sys.path.insert(0, 'kernel_service')
sys.path.insert(0, '/app/kernel_service')

from analyzers.cnc_analyzer import analyze_cnc
from pricing.cnc_pricing import price_cnc

stl_path = "/app/incoming_files/69e150f8777455158dc38f0b/4c19ef5ca_14plug2.stl"

print("=== CNC Pricing Test ===")
geometry = analyze_cnc(stl_path, technology="cnc_milling", auto_repair=True)

params = {
    "technology": "cnc_milling",
    "material": "aluminum",
    "quantity": 1,
    "tolerance": "standard",
    "finish": "standard",
}

pricing = price_cnc(geometry, params)

print(f"\nUnit Price: ${pricing['unit_price']}")
print(f"Total Price: ${pricing['total_price']}")
print(f"\nBreakdown:")
for k, v in pricing['breakdown'].items():
    print(f"  {k}: {v}")

print(f"\nFeatures Summary:")
fs = pricing['features_summary']
print(f"  Holes: {fs['hole_count']}")
print(f"  Pockets: {fs['pocket_count']}")
print(f"  Slots: {fs['slot_count']}")
print(f"  Complexity: {fs['complexity_score']} ({fs['complexity_level']})")
print(f"  Notable: {fs['notable_features']}")

print(f"\nConfidence: {pricing['confidence']}")
print(f"Routing: {pricing['routing']}")
print("\n=== PRICING TEST PASSED ===")
