"""
Nesting Fiyatlandırma Modülü — Faz-6
Shapelid Kernel v3.1.0

SLS/MJF/DMLS için çoklu parça batch fiyatlandırması.

Fiyat modeli:
  - Tek seferde birden fazla parça aynı build volume'a yerleştirilir
  - Machine setup cost bir kez (build başına)
  - Baskı süresi: en yüksek parça + Z dolgu oranı
  - Malzeme maliyeti: parça başına (hacim × fiyat)
  - Machine cost: build süresi × saatlik ücret → parçalara prorata
  - Platform margin aynı (28%)

Prorata hesabı:
  part_machine_cost = (build_machine_cost × part_volume / total_volume)
"""

from .machine_rates import MACHINE_RATES

PLATFORM_MARGIN = 0.28

# Build başına ek maliyetler (toz, gaz, enerji overhead)
BUILD_OVERHEAD = {
    "sls" : {"powder_cost_per_build": 45.0,  "gas_cost": 5.0,  "cooling_min": 120},
    "mjf" : {"powder_cost_per_build": 55.0,  "gas_cost": 0.0,  "cooling_min": 90},
    "dmls": {"powder_cost_per_build": 120.0, "gas_cost": 25.0, "cooling_min": 60},
}

# Layer kalınlıkları (mm)
LAYER_HEIGHTS = {
    "sls" : 0.10,   # 100µm
    "mjf" : 0.08,   # 80µm
    "dmls": 0.03,   # 30µm
}


def calculate_nesting_price(
    nesting_result: dict,
    parts: list,
    technology: str = "sls",
    material_price_kg: float = None,
) -> dict:
    """
    Nesting sonucuna göre batch fiyatlandırma yapar.

    Args:
        nesting_result: analyze_nesting() çıktısı (dict'e çevrilmiş)
        parts: [{ part_id, volume_cm3, material_cost_per_part }]
        technology: "sls" | "mjf" | "dmls"
        material_price_kg: DB'den gelen canlı malzeme fiyatı

    Returns:
        dict: toplam fiyat + parça başına fiyat dökümü
    """
    build_volume = nesting_result.get("build_volume", {"x": 340, "y": 340, "z": 600})
    placed_parts = nesting_result.get("parts_placed", [])
    batch_count  = nesting_result.get("batch_count", 1)
    build_height_mm = nesting_result.get("build_height_mm", 0)
    packing_eff = nesting_result.get("packing_efficiency", 0)

    machine = MACHINE_RATES.get(technology, MACHINE_RATES.get("sls"))
    overhead = BUILD_OVERHEAD.get(technology, BUILD_OVERHEAD["sls"])
    layer_h  = LAYER_HEIGHTS.get(technology, 0.1)

    bx, by = build_volume["x"], build_volume["y"]

    # ── 1. Build süresi hesabı ─────────────────────────────────────────────
    # SLS/MJF: her layer için tüm XY alanı taranır
    layer_count = int(build_height_mm / layer_h) if build_height_mm > 0 else 0
    bbox_area_cm2 = (bx * by) / 100  # cm²

    # Süre/layer: bbox alanına orantılı (makine tarama hızı)
    if technology == "sls":
        time_per_layer_min = bbox_area_cm2 * 0.002 + 0.1
    elif technology == "mjf":
        time_per_layer_min = bbox_area_cm2 * 0.0015 + 0.08
    else:  # dmls
        time_per_layer_min = bbox_area_cm2 * 0.008 + 0.5

    print_time_min = layer_count * time_per_layer_min
    cooling_min = overhead["cooling_min"]

    total_build_time_min = print_time_min + cooling_min
    total_build_time_hr = total_build_time_min / 60

    # ── 2. Build maliyeti ──────────────────────────────────────────────────
    machine_cost = total_build_time_hr * machine["hourly_rate"]
    setup_cost   = machine["setup_cost"] * batch_count  # Her batch için ayrı setup
    powder_cost  = overhead["powder_cost_per_build"] * batch_count
    gas_cost     = overhead["gas_cost"] * batch_count

    total_build_cost = machine_cost + setup_cost + powder_cost + gas_cost

    # ── 3. Parça başına malzeme maliyeti ────────────────────────────────────
    total_part_volume = 0
    part_volumes = {}

    for p in placed_parts:
        vol = p.get("volume_cm3", 0)
        part_volumes[p["part_id"]] = vol
        total_part_volume += vol

    # ── 4. Prorata dağıtım ──────────────────────────────────────────────────
    # Build maliyetini parçalara hacim oranıyla dağıt
    part_pricings = []

    for p in placed_parts:
        pid = p["part_id"]
        vol = part_volumes.get(pid, 0)

        # Malzeme maliyeti (parça başına)
        material_cost = _material_cost(vol, technology, material_price_kg)

        # Prorata machine cost
        if total_part_volume > 0:
            volume_ratio = vol / total_part_volume
        else:
            volume_ratio = 1 / max(len(placed_parts), 1)

        prorata_build_cost = total_build_cost * volume_ratio

        # Toplam parça maliyeti
        part_cost_raw = material_cost + prorata_build_cost
        part_price = part_cost_raw / (1 - PLATFORM_MARGIN)

        part_pricings.append({
            "part_id"            : pid,
            "unit_price"         : round(part_price, 2),
            "material_cost"      : round(material_cost, 4),
            "prorata_build_cost" : round(prorata_build_cost, 4),
            "volume_cm3"         : vol,
            "volume_ratio_pct"   : round(volume_ratio * 100, 1),
        })

    # ── 5. Topamlar ────────────────────────────────────────────────────────
    total_price = sum(p["unit_price"] for p in part_pricings)

    return {
        "currency"          : "USD",
        "total_price"        : round(total_price, 2),
        "batch_count"        : batch_count,
        "part_count"         : len(placed_parts),
        "phase"              : "faz-6",
        "build_summary": {
            "machine_cost"     : round(machine_cost, 4),
            "setup_cost"        : round(setup_cost, 4),
            "powder_cost"       : round(powder_cost, 4),
            "gas_cost"          : round(gas_cost, 4),
            "total_build_cost"  : round(total_build_cost, 4),
            "build_time_min"    : round(total_build_time_min, 2),
            "print_time_min"    : round(print_time_min, 2),
            "cooling_min"       : cooling_min,
            "layer_count"       : layer_count,
            "build_height_mm"   : build_height_mm,
            "packing_efficiency": packing_eff,
        },
        "part_pricings"      : part_pricings,
        "savings_vs_separate": _calculate_savings(parts, placed_parts, machine, technology, material_price_kg, total_price),
    }


# ── Yardımcı fonksiyonlar ────────────────────────────────────────────────────

# SLS/MJF için ortalama malzeme yoğunlukları
MATERIAL_DENSITIES = {
    "pa12": 1.01, "pa11": 1.02, "pa12gb": 1.13, "tpu": 1.10,
    "pa6": 1.13, "pa66": 1.14, "peek": 1.30, "pekk": 1.30,
    "316l": 8.00, "ti64": 4.43, "default": 1.05,
}

MATERIAL_FALLBACK_PRICES = {
    # USD/kg statik fallback (DB yoksa)
    "pa12": 80.0, "pa11": 85.0, "pa12gb": 95.0, "tpu": 120.0,
    "peek": 500.0, "316l": 45.0, "ti64": 350.0,
    "default": 80.0,
}


def _material_cost(volume_cm3: float, technology: str, material_price_kg: float = None) -> float:
    """Parça malzeme maliyeti (hacim × yoğunluk × fiyat/kg)."""
    density = 1.05  # SLS/MJF ortalama

    if material_price_kg and material_price_kg > 0:
        price_per_kg = material_price_kg
    else:
        price_per_kg = MATERIAL_FALLBACK_PRICES.get("default", 80.0)

    # SLS/MJF: powder waste factor (~1.3x — toz geri dönüşümü sonrası net)
    waste_factor = 1.3 if technology in ("sls", "mjf") else 1.15
    weight_kg = (volume_cm3 * density * waste_factor) / 1000

    return weight_kg * price_per_kg


def _calculate_savings(parts: list, placed_parts: list, machine: dict,
                       technology: str, material_price_kg: float,
                       batch_total: float) -> dict:
    """
    Ayrı ayrı baskı vs nesting baskı maliyet karşılaştırması.
    """
    if not placed_parts:
        return {"saved_usd": 0, "saved_pct": 0}

    # Ayrı baskı: her parça için ayrı setup + kendi baskı süresi
    separate_total = 0
    for p in placed_parts:
        vol = p.get("volume_cm3", 0)
        # Ayrı setup + minimum baskı süresi (60 dk minimum)
        separate_machine_cost = machine["hourly_rate"] * 1.0  # Min 1 saat
        separate_setup = machine["setup_cost"]
        separate_material = _material_cost(vol, technology, material_price_kg)
        separate_cost = (separate_machine_cost + separate_setup + separate_material) / (1 - PLATFORM_MARGIN)
        separate_total += separate_cost

    saved = round(separate_total - batch_total, 2)
    saved_pct = round((saved / separate_total * 100), 1) if separate_total > 0 else 0

    return {
        "separate_printing_total": round(separate_total, 2),
        "batch_printing_total"   : round(batch_total, 2),
        "saved_usd"              : saved,
        "saved_pct"              : saved_pct,
    }
