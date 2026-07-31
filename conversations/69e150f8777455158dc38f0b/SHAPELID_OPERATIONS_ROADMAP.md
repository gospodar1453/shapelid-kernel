# SHAPELID ÜRETİM EKOSİSTEMİ YOL HARİTASI
## Client Portal Üretim Yönetimi Ek Ürün Geliştirme Planı

> Sentez: Glide (no-code MES), Odoo (ERP+MES), FlowTrac (WIP tracking), MRPEasy (MRP II), 
> Xometry/Hubs/Jiga/Craftcloud (marketplace operasyonları)

---

## MEVCUT DURUM ANALİZİ

### Shapelid'in Güçlü Yönleri
| Mevcut Kapasite | Detay |
|---|---|
| Çok Teknolojili Fiyatlama Motoru | 11 teknoloji, STL/DXF analizi, manuel quote tetikleyicileri |
| Malzeme Kataloğu | 135+ malzeme, display_mode (simple/advanced/both) |
| ML Kalibrasyon | CalibrationRecord + CalibrationFactor, exponential smoothing |
| Nesting Optimizasyon | SLS/MJF için parça yerleştirme |
| Ödeme Altyapısı | PayTR Direct API |
| Üretici Ağı | 19.353 üretici (Wix), ~3.000 yapılandırılmış (DB) |
| Partner Portal | partner.shapelid.com (üretici tarafı) |
| Geliştirici Dokümantasyon | Mintlify, 28 sayfa |

### Kritik Boşluklar (Rakip ve Platform Analizine Göre)
| Boşluk | Kaynak Referans | Öncelik |
|---|---|---|
| Üretim Takibi ve Sipariş Yaşam Döngüsü | Xometry, Hubs | 🔴 Yüksek |
| DFM (Design for Manufacturing) Görsel Geri Bildirim | Hubs, Xometry | 🔴 Yüksek |
| Kalite ve Uyumluluk Hub'ı | Xometry (CMM, CoC, FAI) | 🔴 Yüksek |
| Takım Çalışma Alanları ve RBAC | Xometry, Jiga | 🟡 Orta |
| Envanter ve WIP Takibi | FlowTrac, MRPeasy, Odoo | 🟡 Orta |
| Üretim Planlama ve Kapasite | Odoo, MRPeasy | 🟡 Orta |
| BOM Yönetimi | Odoo, MRPeasy | 🟠 Gelecek |
| Parça Bazlı İletişim (RFI) | Jiga | 🟡 Orta |
| Analitik Dashboard | Glide, Odoo | 🟡 Orta |
| Alt Yüklenici Yönetimi | Odoo, MRPeasy | 🟠 Gelecek |

---

## STRATEJİK KONUMLANMA

Shapelid bir ERP/MRP replacement değil — **üretim marketplace'i + operasyonel katman**'dır.

```
                    SHAPELID PLATFORM MİMARİSİ
                    
  ┌─────────────────────────────────────────────────────┐
  │              CLIENT PORTAL (app.shapelid.com)        │
  │                                                      │
  │  ┌──────────┐  ┌──────────┐  ┌──────────────────┐   │
  │  │ Quote &  │  │ 3D Viewer│  │  OPERATIONAL      │   │
  │  │ Upload   │  │ + DFM    │  │  MODULES (YENİ)   │   │
  │  │ Engine   │  │ Feedback │  │                   │   │
  │  └──────────┘  └──────────┘  │  • Order Tracking  │   │
  │                              │  • Team Workspace  │   │
  │                              │  • Quality Hub     │   │
  │                              │  • RFI / Chat      │   │
  │                              │  • Analytics       │   │
  │                              └──────────────────┘   │
  └───────────────────────┬─────────────────────────────┘
                          │
                    ┌─────┴─────┐
                    │  KATMAN   │  ← Gerçek zamanlı senkron
                    │  (Bridge) │
                    └─────┬─────┘
                          │
  ┌───────────────────────┴─────────────────────────────┐
  │            PARTNER PORTAL (partner.shapelid.com)      │
  │                                                        │
  │  ┌──────────┐  ┌──────────┐  ┌──────────────────┐     │
  │  │ Job      │  │ Shop     │  │  PRODUCTION       │     │
  │  │ Board    │  │ Floor    │  │  MANAGEMENT      │     │
  │  │          │  │ Dashboard│  │  (YENİ)           │     │
  │  └──────────┘  └──────────┘  │                   │     │
  │                              │  • WIP Tracking   │     │
  │                              │  • Scheduling     │     │
  │                              │  • QC Inspections │     │
  │                              │  • Inventory      │     │
  │                              │  • BOM Management │     │
  │                              └──────────────────┘     │
  └──────────────────────────────────────────────────────┘
```

---

## FAZLARA BÖLÜNMÜŞ YOL HARİTASI

### FAZ-1: SİPARİŞ YAŞAM DÖNGÜSÜ VE ÜRETİM TAKİBİ
**Süre:** 4-6 hafta | **Öncelik:** 🔴 Kritik

**Referans:** Xometry (multi-stage live tracking), Hubs (visual milestones), Jiga (line-item timeline)

#### 1.1 Order Status Pipeline
- **Entity:** `Order` entity'sine `production_stages` alanı eklenecek
- **Statü Akışı:**
  ```
  Order Confirmed → Material Sourced → Tooling Setup → 
  In Production → Quality Assurance → Packaging → 
  Dispatched → Delivered
  ```
- Her aşamada: timestamp, sorumlu üretici, notlar, görsel (opsiyonel)

#### 1.2 Partner Portal'dan Real-Time Güncelleme
- Partner Portal'da her sipariş için "Update Status" arayüzü
- Status güncellemesi otomatik Client Portal'a reflect edilir
- Müşteri real-time bildirim alır (WhatsApp/email/push)

#### 1.3 Görsel Üretim Güncellemeleri
- Üretici, üretim aşamasında parça fotoğrafı/video yükleyebilir
- "Before dispatch" görselleri (Hubs modeli)
- `Order` entity'sinde `production_media` alanı

#### 1.4 Sipariş Timeline Widget
- Client Portal'da her sipariş için görsel timeline
- Tamamlanan/adım bekleyen/aşamaların renk kodlu gösterimi
- Tahmini tamamlanma tarihi (üretici tarafından girilen lead time)

**Yeni Entity'ler:**
```
ProductionStage:
  - order_id: string (ref: Order)
  - stage_name: string (enum: material_sourced, tooling_setup, in_production, qa, packaging, dispatched, delivered)
  - status: string (enum: pending, in_progress, completed, skipped)
  - started_at: datetime
  - completed_at: datetime
  - operator_name: string
  - notes: string
  - media_urls: array
```

---

### FAZ-2: DFM GÖRSEL GERİ BİLDİRİM VE 3D VIEWER ENTEGRASYONU
**Süre:** 4-8 hafta | **Öncelik:** 🔴 Kritik

**Referans:** Hubs (automated visual DFM, heatmap overlays), Xometry (AI DFM)

#### 2.1 Geometrik Analiz Çıktıları
Kernel zaten hesaplıyor — bunları viewer'a aktar:
- **Wall Thickness** — ince duvarlar (< 0.8mm FDM, < 1.0mm SLA)
- **Overhang Angle** — destek gerektiren yüzeyler
- **Deep Pockets** — işlenemeyen derin cepler
- **Tight Radii** — min takım yarıçapından küçük köşeler
- **Support Area** — SLA/DMLS için destek hacmi

#### 2.2 DFM Heatmap Overlay
- Three.js viewer üzerinde renkli ısı haritası
- Kırmızı = işlenemez/uygunsuz, Sarı = riskli, Yeşil = uygun
- Tıklanınca detay tooltip: "Wall thickness: 0.6mm — minimum 0.8mm for FDM"

#### 2.3 DFM Raporu (PDF Export)
- Müşteriye indirilebilir DFM analizi raporu
- Geometrik özellikler, riskler, öneriler
- Kernel `/analyze` çıktısından otomatik üretilir

#### 2.4 Teknoloji Bazlı DFM Kuralları
```
FDM:  min_wall=0.8mm, max_overhang=45°, min_hole=1.5mm
SLA:  min_wall=1.0mm, support_required=true, min_hole=0.5mm
SLS:  min_wall=0.7mm, support_required=false, min_hole=1.5mm
MJF:  min_wall=0.8mm, support_required=false, min_hole=0.8mm
DMLS: min_wall=0.5mm, support_required=true, min_hole=1.0mm
CNC:  min_wall=1.5mm, max_depth/diameter=4:1, min_radius=0.5mm
EDM:  min_radius=0.1mm, max_depth=10x wire diameter
Laser: min_kerf=0.2mm, max_thickness=20mm, min_hole=1.0mm
Bending: min_bend_radius=1.0x material thickness, min_flange=3.0x thickness
```

---

### FAZ-3: KALİTE VE UYUMLULUK HUB'I
**Süre:** 3-5 hafta | **Öncelik:** 🔴 Yüksek

**Referans:** Xometry (CMM, CoC, FAI, AS9100), Hubs (Protolabs Network Standard)

#### 3.1 Kalite Dokümantasyon Sistemi
- Sipariş tamamlanınca üretici kalite dokümanları yükler
- **Desteklenen doküman tipleri:**
  - Certificate of Conformance (CoC)
  - Material Test Report (MTR)
  - First Article Inspection (FAI) raporu
  - CMM dimensional inspection sheet
  - RoHS/REACH compliance sertifikası
  - ISO 9001 / AS9100 / ISO 13485 uyumluluk

#### 3.2 Quality Status Badge
- Her sipariş için kalite rozeti: ✅ Verified / ⚠️ Pending / ❌ Non-Conform
- Müşteri dokümanları indirip inceleyebilir
- Doküman tarihleri ve versiyonları takip edilir

#### 3.3 Non-Conformance Management
- Müşteri uygunsuzluk bildirebilir (fotoğraf + açıklama)
- Otomatik RMA (Return Merchandise Authorization) akışı
- Üretici yanıtlama ve düzeltici aksiyon süreci
- İstatistik: üretici başına non-conformance oranı

**Yeni Entity'ler:**
```
QualityDocument:
  - order_id: string (ref: Order)
  - document_type: string (enum: coc, mtr, fai, cmm_report, rohs_reach, iso_cert)
  - file_url: string
  - uploaded_by: string
  - uploaded_at: datetime
  - verified: boolean
  - notes: string

NonConformance:
  - order_id: string (ref: Order)
  - reported_by: string
  - issue_type: string (enum: dimensional, surface_finish, material, missing_feature, other)
  - description: string
  - media_urls: array
  - severity: string (enum: minor, major, critical)
  - rma_status: string (enum: none, requested, approved, rejected, resolved)
  - resolution_notes: string
```

---

### FAZ-4: TAKIM ÇALIŞMA ALANLARI VE KURUMSAL HESAPLAR
**Süre:** 3-4 hafta | **Öncelik:** 🟡 Orta

**Referans:** Xometry (multi-user roles), Jiga (engineer/vendor chat), Hubs (team accounts)

#### 4.1 Organization Entity
- Şirket bazlı hesap yönetimi
- Takım üyeleri davetiyesi (email invite)
- Rol bazlı yetkilendirme: Owner, Admin, Buyer, Engineer, Viewer
- Ortak teklif klasörleri ve sipariş geçmişi

#### 4.2 Role-Based Access Control (RBAC)
```
Owner:    Tam yetki (fatura, kullanıcı yönetimi, tüm siparişler)
Admin:    Sipariş yönetimi, kullanıcı daveti, raporlama
Buyer:    Sipariş oluşturma, ödeme, teklif görüntüleme
Engineer: Teklif görüntüleme, CAD upload, DFM inceleme
Viewer:   Sadece görüntüleme (read-only)
```

#### 4.3 Ortak Sipariş ve Teklif Havuzu
- Şirket içinde paylaşılan teklif listesi
- "Benim tekliflerim" vs "Takım teklifleri" görünümü
- Sipariş onay akışı: Engineer teklif oluşturur → Buyer onaylar → Admin siparişi verir

#### 4.4 Purchase Order (PO) Desteği
- PO numarası ile sipariş ilişkilendirme
- Net 30/60 ödeme koşulları (kurumsal müşteriler)
- Kurumsal kredi limiti yönetimi

**Yeni Entity'ler:**
```
Organization:
  - name: string
  - tax_id: string
  - billing_address: string
  - po_enabled: boolean
  - credit_limit: number
  - net_terms_days: number (enum: 0, 15, 30, 60)

TeamMember:
  - organization_id: string (ref: Organization)
  - user_id: string (ref: User)
  - role: string (enum: owner, admin, buyer, engineer, viewer)
  - invited_email: string
  - status: string (enum: active, pending, removed)
```

---

### FAZ-5: PARÇA BAZLI İLETİŞİM VE RFI YÖNETİMİ
**Süre:** 2-3 hafta | **Öncelik:** 🟡 Orta

**Referans:** Jiga (part-level discussion threads, in-context messaging)

#### 5.1 Line-Item Chat System
- Her sipariş kalemi için ayrı discussion thread
- Müşteri ↔ Üretici direkt iletişim (Shapelid arabulucu)
- CAD revizyonu, tolerans sorgusu, malzeme alternatifi tartışması
- Thread'e dosya ekleme (revize CAD, teknik çizim, fotoğraf)

#### 5.2 RFI (Request for Information) Workflow
```
Müşteri RFI oluşturur → Üretici yanıtlar → Müşteri onaylar
                      → Redderse → Revizyon talebi
                      → Kabulse → Üretime devam
```

#### 5.3 Bildirim Sistemi
- Yeni mesaj: WhatsApp + email + portal push
- @mention desteği: "@producer tolerans 0.1mm mümkün mü?"
- Mesaj okundu/okunmadı durumu

**Yeni Entity:**
```
Message:
  - order_id: string (ref: Order)
  - line_item_id: string (opsiyonel, spesifik parça için)
  - sender_id: string
  - sender_role: string (enum: client, producer, shapelid_admin)
  - message_type: string (enum: text, file, rfi, rfi_response, revision_request)
  - content: string
  - attachments: array (file URLs)
  - read_at: datetime
  - created_at: datetime
```

---

### FAZ-6: PARTNER PORTAL ÜRETİM YÖNETİMİ (PRODUCTION SUITE)
**Süre:** 6-10 hafta | **Öncelik:** 🟡 Orta

**Referans:** FlowTrac (WIP, barcode), MRPeasy (shop floor kiosk, scheduling), Odoo (MES, Gantt)

#### 6.1 WIP (Work-in-Progress) Tracking
- Üretici mevcut siparişleri "production queue" olarak görür
- Her sipariş için: başlama → proses adımları → tamamlama
- İş istasyonu bazında durum takibi
- Scrap/waste kaydı

#### 6.2 Shop Floor Dashboard (Partner Portal)
- Gelen siparişler → Kabul/Red → Üretim Kuyruğu → Tamamlananlar
- Sipariş kabul etme akışı (Accept/Decline with reason)
- Üretici kapasite girişi: "Bu hafta X saat boş"
- Lead time güncelleme: "Bu sipariş 5 iş günü"

#### 6.3 Basit Üretim Planlama
- Gantt benzeri sipariş takvimi
- İş istasyonu kapasitesi bazında çakışma kontrolü
- Forward/backward scheduling
- Üretici için "bugün ne yapacağım" görünümü

#### 6.4 Kalite Kontrol Modülü (Üretici Tarafı)
- Üretim öncesi kontrol listesi (checklist)
- İlk parça kontrolü (First Article Inspection)
- Ölçüm girişi: "Diameter: 10.05mm (tol: ±0.1mm) → PASS"
- Parça fotoğrafı + kontrol sonucu kaydı

**Yeni Entity'ler:**
```
ProductionQueue:
  - partner_id: string
  - order_id: string (ref: Order)
  - status: string (enum: new, accepted, declined, queued, in_progress, completed)
  - accepted_at: datetime
  - estimated_completion: datetime
  - workstation: string
  - operator: string
  - scrap_qty: number
  - notes: string

InspectionChecklist:
  - production_queue_id: string (ref: ProductionQueue)
  - check_name: string
  - check_type: string (enum: visual, dimensional, material, functional)
  - expected_value: string
  - actual_value: string
  - result: string (enum: pass, fail, pending)
  - inspector: string
  - media_urls: array
  - checked_at: datetime
```

---

### FAZ-7: ANALİTİK DASHBOARD VE RAPORLAMA
**Süre:** 3-4 hafta | **Öncelik:** 🟡 Orta

**Referans:** Glide (real-time dashboards), Odoo (analytics), Xometry (enterprise reporting)

#### 7.1 Müşteri Dashboard
- Toplam sipariş sayısı, toplam harcama
- Teknoloji bazında dağılım (FDM %X, CNC %Y)
- Ortalama teslimat süresi
- Kalite rozeti istatistikleri
- Ay bazında harcama trendi

#### 7.2 Üretici Dashboard (Partner Portal)
- Toplam üretilen parça/adet
- Ortalama üretim süresi
- Non-conformance oranı
- Kapasite kullanım oranı
- Aylık gelir trendi

#### 7.3 Platform Admin Dashboard (Shapelid İçi)
- GMV (Gross Merchandise Value)
- Take-rate bazında komisyon geliri
- Sipariş tamamlanma oranı
- Ortalama fiyat doğruluk oranı (kalibrasyon metrikleri)
- Üretici performans sıralaması

---

### FAZ-8: İLERİ SEVİYE ÖZELLİKLER (FUTURE)
**Süre:** 8-12+ hafta | **Öncelik:** 🟠 Gelecek

**Referans:** Odoo (IoT, PLM, subcontracting), MRPeasy (matrix BOM, expiry tracking)

#### 8.1 BOM Yönetimi
- Çok seviyeli BOM oluşturma (assembly → sub-assembly → component)
- BOM versiyonlama ve ECO (Engineering Change Order)
- Maliyet hesabı: BOM × malzeme fiyatları → otomatik maliyet

#### 8.2 Envanter Yönetimi (Üretici Tarafı)
- Hammadde, yarı mamul, mamul stok takibi
- Çoklu depo / lokasyon
- Min-max stok seviyeleri ve otomatik uyarı
- Lot/serial numarası takibi
- FEFO/FIFO stok çıkış kuralı

#### 8.3 Alt Yüklenici Yönetimi
- Üreticinin alt tedarikçilere iş göndermesi
- Alt yüklenici performans takibi
- Malzeme dropship ve geri kabul akışı
- Maliyet zinciri: ana üretici → alt yüklenici → maliyet

#### 8.4 IoT / Makine Entegrasyonu
- Makine durumu (çalışıyor/durdu/bakım)
- OEE (Overall Equipment Effectiveness) hesabı
- Otomatik üretim sayacı
- Makine bakım takvimi

#### 8.5 CAD Plugin'leri
- SolidWorks, Fusion 360, Onshape entegrasyonu
- Tek tıkla upload → teklif alma
- CAD içinde fiyat karşılaştırma

---

## PLATFORM BAZLI KARŞILAŞTIRMA

| Özellik | Glide | Odoo | FlowTrac | MRPeasy | Xometry/Hubs | **Shapelid Hedef** |
|---|---|---|---|---|---|---|
| Fiyatlama Motoru | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ (mevcut) |
| 3D Viewer + DFM | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ (Faz-2) |
| Sipariş Takibi | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ (Faz-1) |
| Kalite Hub | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ (Faz-3) |
| Takım/RBAC | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ (Faz-4) |
| İletişim/RFI | ⚠️ | ⚠️ | ❌ | ⚠️ | ✅ | ✅ (Faz-5) |
| Shop Floor / WIP | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ (Faz-6) |
| Planlama/Gantt | ⚠️ | ✅ | ❌ | ✅ | ❌ | ✅ (Faz-6) |
| Analitik | ✅ | ✅ | ⚠️ | ✅ | ✅ | ✅ (Faz-7) |
| BOM Yönetimi | ⚠️ | ✅ | ❌ | ✅ | ❌ | ⚠️ (Faz-8) |
| Envanter | ✅ | ✅ | ✅ | ✅ | ❌ | ⚠️ (Faz-8) |
| IoT/Makine | ❌ | ✅ | ✅ | ❌ | ❌ | ⚠️ (Faz-8) |
| Ödeme/Marketplace | ⚠️ | ✅ | ❌ | ⚠️ | ✅ | ✅ (mevcut) |
| Malzeme Kataloğu | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ (mevcut) |

**Shapelid'in Diferansiyeli:** ERP/MRP değil — üretim marketplace'ine operasyonel katman ekliyoruz. 
Odoo/MRPeasy üreticinin iç sürecini yönetir; Shapelid müşteri↔üretici arasındaki süreci yönetir.

---

## ENTITY MİMARİSİ ÖZETİ

### Mevcut Entity'ler (değişiklik gerektirenler)
- `Order` → `production_stages`, `production_media`, `quality_status`, `organization_id` alanları eklenecek
- `ManufacturerLead` → `performance_score`, `on_time_rate`, `quality_rate` alanları eklenecek

### Yeni Entity'ler
1. **ProductionStage** — Sipariş üretim aşamaları (Faz-1)
2. **QualityDocument** — Kalite dokümanları (Faz-3)
3. **NonConformance** — Uygunsuzluk yönetimi (Faz-3)
4. **Organization** — Kurumsal hesap (Faz-4)
5. **TeamMember** — Takım üyeleri (Faz-4)
6. **Message** — Parça bazlı iletişim (Faz-5)
7. **ProductionQueue** — Üretici üretim kuyruğu (Faz-6)
8. **InspectionChecklist** — Kalite kontrol listesi (Faz-6)

---

## ÖNERİLEN GELİR MODELİ ENTEGRASYONU

| Modül | Ücretsiz | Pro | Enterprise |
|---|---|---|---|
| Fiyatlama & Upload | ✅ | ✅ | ✅ |
| Sipariş Takibi | ✅ | ✅ | ✅ |
| 3D Viewer | ✅ | ✅ | ✅ |
| DFM Heatmap | ❌ | ✅ | ✅ |
| Kalite Hub | ❌ | ✅ | ✅ |
| Takım Workspace (≤3 üye) | ❌ | ✅ | ✅ (sınırsız) |
| Parça Bazlı İletişim | ❌ | ✅ | ✅ |
| Analitik Dashboard | ❌ | ⚠️ (basic) | ✅ (advanced) |
| PO / Net Terms | ❌ | ❌ | ✅ |
| API Erişimi | ❌ | ❌ | ✅ |
