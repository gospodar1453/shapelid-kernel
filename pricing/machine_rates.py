"""
Makine Saatlik Maliyet Tablosu — USD bazlı
Amortisman + enerji + bakım + işçilik dahil
"""

MACHINE_RATES = {
    "fdm": {
        "hourly_rate": 3.50,   # USD/saat — desktop FDM
        "setup_cost": 2.00,    # USD — plaka hazırlık + kalibrasyon
        "name": "FDM Yazıcı",
    },
    "sla": {
        "hourly_rate": 8.00,
        "setup_cost": 3.00,    # reçine hazırlık
        "name": "SLA Yazıcı",
    },
    "sls": {
        "hourly_rate": 25.00,  # endüstriyel makine
        "setup_cost": 45.00,   # toz yükleme + ısınma
        "name": "SLS Sistemi",
    },
    "mjf": {
        "hourly_rate": 30.00,
        "setup_cost": 50.00,
        "name": "HP MJF Sistemi",
    },
    "laser": {
        "hourly_rate": 35.00,  # fiber lazer (3kW+)
        "setup_cost": 15.00,   # program yükleme + malzeme yerleştirme
        "name": "Fiber Lazer Kesim",
    },
    "bending": {
        "hourly_rate": 45.00,  # CNC abkant pres
        "setup_cost": 20.00,   # kalıp kurulum
        "name": "CNC Abkant Pres",
    },
}
