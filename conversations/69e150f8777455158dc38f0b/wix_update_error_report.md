# Wix CMS Bulk Update — Hata Raporu

**Tarih:** 31 Temmuz 2026  
**Operasyon:** Excel iletişim verisi → Wix manufacturers koleksiyonu  
**Wix toplam kayıt:** 19,353  
**Excel toplam kayıt:** 11,402  

---

## Özet

| Metrik | Değer |
|---|---|
| Eşleşen kayıt | 11,403 |
| Güncelleme gereken | 8,969 |
| İlk denemede başarılı | 8,656 |
| İlk denemede hata | 313 |
| Retry'da düzelen | 14 |
| **Kalıcı hata** | **0** |
| **Toplam başarı** | **8,969 / 8,969 (%100)** |

---

## Hata Analizi

### 313 Hatanın Dağılımı

| Hata Tipi | Adet | Açıklama |
|---|---|---|
| Geçici API timeout | 299 | Wix API yanıt vermedi, ancak kayıt aslında güncellenmişti |
| Fetch hatası ($in filtresi) | 14 | Batch fetch sırasında kayıt bulunamadı, update yapılamadı |
| **Toplam** | **313** | |

### 299 Geçici Hata
Bu kayıtlar ilk denemede API tarafından hata olarak işaretlendi, ancak doğrulama sonucunda email alanlarının başarıyla yazıldığı teyit edildi. Sebep: Wix Data API'sinin batch update sırasında rate-limit veya geçici yanıt kesintisi.

### 14 Fetch Hatası (Retry'da Düzelen)

| # | Firma Adı | Email |
|---|---|---|
| 1 | ERD Galvaniz | cemile.oruc@erdgalvaniz.com |
| 2 | Emin Kauçuk Conta | ali.kurnazoglu@eminkaucuk.com |
| 3 | Milltech-Degpa-Değirmencioğlu | maksim.rozyyev@milltech.com.tr |
| 4 | Sağlam Metal - Eskişehir | cihan.saglam@saglammetal.com |
| 5 | Fera Metal Sac İşleme Merkezi | canan.dundar@ferametal.com.tr |
| 6 | Elfamak | ahmet.sahin@elfamak.com.tr |
| 7 | SÖNMEZ TİCARET | yusuf.dogruel@sonmezticaret.com |
| 8 | Uludağ Kumlama Boya | muzaffer.dilmac@uludagkumlamaboya.com |
| 9 | Fedai Forklift | onur.ardic@fedaiforklift.com |
| 10 | YAPAR PASLANMAZ MAKİNE A.Ş. | lutfi.emirmahmutoglu@yaparpaslanmaz.com.tr |
| 11 | Çetinkaya Endüstriyel Ürünler Rulman | sercan.cetinkaya@esanayim.com |
| 12 | Karadeniz Yay Sanayi | can.karadeniz@karadenizyay.com |
| 13 | SBS Transformatör | mehmet.balkoca@sbstransformator.com |
| 14 | ERKEKOĞLU PRES | mustafa.kilic@erkekoglu.com.tr |

**Durum:** Tümü retry'da başarıyla güncellendi ✅

---

## Güncellenen Alanlar

Her kayda aşağıdaki alanlar eklendi/güncellendi:

| Alan | Kaynak | Açıklama |
|---|---|---|
| `email` | Excel Company Email / Contact Email | Şirket veya kişi e-postası |
| `website` | Excel Website | Sadece Wix'te boş ise eklendi |
| `contactDataFull` | true | İletişim verisi tamamlandı işareti |
| `picName` | Excel PIC Name | Yetkili kişi adı |
| `picTitle` | Excel PIC Title | Unvanı |
| `picLinkedIn` | Excel PIC LinkedIn | LinkedIn profili |
| `contactEmail` | Excel Contact Email | Doğrudan iletişim e-postası |

Mevcut alanlar (title, capabilities, manufacturing, description, slug, img, cover, location, verified, certified) korundu.

---

## Teknik Notlar

- Wix Data API v2 `items/update` endpoint'i kullanıldı (PATCH yok, UPDATE replaces all fields)
- Her kayıt için önce full data fetch edildi, sonra email/PIC fields merge edildi
- Pagination: `_id` filtresi ile `$gt` manual pagination (cursor/skip Wix'te döngüye giriyor)
- Batch fetch: 40 kayıt/chunk (`$in` filtresi limiti)
- Rate limit: ~0.15s/update → ~6-7 kayıt/saniye
