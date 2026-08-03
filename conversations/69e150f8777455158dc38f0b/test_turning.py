import sys
sys.path.insert(0, 'kernel_service')
sys.path.insert(0, '/app/kernel_service')

from analyzers.cnc_analyzer import analyze_cnc
from pricing.cnc_pricing import price_cnc

stl_path = "/app/incoming_files/69e150f8777455158dc38f0b/4c19ef5ca_14plug2.stl"

print("=== CNC Turning Test ===")
geometry = analyze_cnc(stl_path, technology="cnc_turning", auto_repair=True)

turning = geometry.get("turning_features")
if turning:
    print(f"Turning candidate: {turning['is_turning_candidate']}")
    print(f"Rotation axis: {turning['rotation_axis']}")
    print(f"Length: {turning['length_mm']}mm")
    print(f"Max diameter: {turning['max_diameter_mm']}mm")
    print(f"Roundness: {turning['roundness_score']}")
    print(f"Turning time: {turning['total_turning_time_min']} min")
    print(f"Operations: {turning['operations']}")
else:
    print("No turning features detected")

params = {
    "technology": "cnc_turning",
    "material": "aluminum",
    "quantity": 1,
}
pricing = price_cnc(geometry, params)
print(f"\nUnit Price (turning): ${pricing['unit_price']}")
print(f"Machine time: {pricing['breakdown']['machine_time_min']} min")
print(f"Routing: {pricing['routing']}")
print("\n=== TURNING TEST PASSED ===")
