import sys
sys.path.insert(0, 'kernel_service')
sys.path.insert(0, '/app/kernel_service')

from analyzers.cnc_analyzer import analyze_cnc

stl_path = "/app/incoming_files/69e150f8777455158dc38f0b/4c19ef5ca_14plug2.stl"

print("=== CNC Feature Recognition Test ===")
print(f"File: {stl_path}")
print(f"Technology: cnc_milling")
print()

try:
    result = analyze_cnc(stl_path, technology="cnc_milling", auto_repair=True)
    
    print("--- Basic Geometry ---")
    print(f"Volume: {result['volume_cm3']} cm³")
    print(f"Surface Area: {result['surface_area_cm2']} cm²")
    print(f"Dimensions: {result['dimensions_mm']}")
    print(f"Bounding Box Volume: {result['bounding_box_volume_cm3']} cm³")
    print(f"Packing Density: {result['packing_density']}")
    print(f"Watertight: {result['is_watertight']}")
    print(f"Triangle Count: {result['triangle_count']}")
    print()
    
    print("--- CNC Features ---")
    print(f"Holes: {len(result['holes'])}")
    for h in result['holes'][:5]:
        print(f"  - Ø{h['diameter_mm']}mm × {h['depth_mm']}mm depth ({h['type']}, complexity={h['complexity']}, time={h['est_drill_time_min']}min)")
    
    print(f"Pockets: {len(result['pockets'])}")
    for p in result['pockets'][:5]:
        print(f"  - {p['width_mm']}×{p['height_mm']}mm ({p['type']}, depth={p['estimated_depth_mm']}mm, time={p['est_mill_time_min']}min)")
    
    print(f"Slots: {len(result['slots'])}")
    for s in result['slots'][:5]:
        print(f"  - {s['width_mm']}×{s['length_mm']}mm ({s['type']}, time={s['est_mill_time_min']}min)")
    
    print()
    print("--- Edge Analysis ---")
    edges = result['edges']
    print(f"  Sharp: {edges['sharp_edges']}")
    print(f"  Fillets: {edges['fillets']}")
    print(f"  Chamfers: {edges['chamfers']}")
    print(f"  Smooth: {edges['smooth_edges']}")
    print(f"  Total: {edges['total_edges']}")
    
    print()
    print("--- Planar Faces ---")
    print(f"  Count: {len(result['planar_faces'])}")
    for f in result['planar_faces'][:3]:
        print(f"  - Area: {f['area_mm2']}mm², Normal: {f['normal']}")
    
    print()
    print("--- Cylindrical Faces ---")
    print(f"  Count: {len(result['cylindrical_faces'])}")
    for c in result['cylindrical_faces'][:3]:
        print(f"  - Ø{c['diameter_mm']}mm × {c['length_mm']}mm length, area={c['area_mm2']}mm²")
    
    print()
    print("--- CNC Metrics ---")
    print(f"  Complexity Score: {result['cnc_complexity_score']}/100")
    print(f"  Est. Machine Time: {result['estimated_machine_time_min']} min")
    print(f"  Time Breakdown:")
    for k, v in result['machine_time_breakdown'].items():
        print(f"    {k}: {v} min")
    
    print()
    print("--- Warnings ---")
    for w in result['warnings']:
        print(f"  [{w['severity']}] {w['code']}: {w['message']}")
    
    print()
    print("=== TEST PASSED ===")
    
except Exception as e:
    import traceback
    print(f"ERROR: {e}")
    traceback.print_exc()
    print("=== TEST FAILED ===")
