import json

materials = [
    {
        "isim": "EOS PA 2200 (PA12)",
        "marka_platform": "EOS",
        "teknoloji": "SLS",
        "mekanik_ozellikler": {
            "cekme_dayanimi": "48 MPa",
            "kopma_uzamasi": "%18"
        },
        "yaklasik_fiyat_usd_kg": "70 - 90",
        "tipik_kullanim": "Fonksiyonel prototipler, dişliler, menteşeler, otomotiv ve tüketici elektroniği parçaları."
    },
    {
        "isim": "EOS PA 1101 (PA11)",
        "marka_platform": "EOS",
        "teknoloji": "SLS",
        "mekanik_ozellikler": {
            "cekme_dayanimi": "48 MPa",
            "kopma_uzamasi": "%45"
        },
        "yaklasik_fiyat_usd_kg": "90 - 110",
        "tipik_kullanim": "Yüksek darbe dayanımı ve esneklik gerektiren fonksiyonel parçalar, menteşeler, protezler, otomotiv iç parçaları."
    },
    {
        "isim": "EOS PA 1102 Black",
        "marka_platform": "EOS",
        "teknoloji": "SLS",
        "mekanik_ozellikler": {
            "cekme_dayanimi": "48 MPa",
            "kopma_uzamasi": "%45"
        },
        "yaklasik_fiyat_usd_kg": "90 - 110",
        "tipik_kullanim": "Siyah renk gerektiren otomotiv, makine ve tüketici ürünleri, yüksek mekanik ve kimyasal dayanım gerektiren işlevsel parçalar."
    },
    {
        "isim": "EOS Alumide",
        "marka_platform": "EOS",
        "teknoloji": "SLS",
        "mekanik_ozellikler": {
            "cekme_dayanimi": "48 MPa",
            "kopma_uzamasi": "%4"
        },
        "yaklasik_fiyat_usd_kg": "100 - 130",
        "tipik_kullanim": "Metalik görünüm ve yüksek rijitlik gerektiren parçalar, rüzgar tüneli modelleri, kalıp prototipleri."
    },
    {
        "isim": "EOS PrimePart Plus (PA 2221)",
        "marka_platform": "EOS",
        "teknoloji": "SLS",
        "mekanik_ozellikler": {
            "cekme_dayanimi": "48 MPa",
            "kopma_uzamasi": "%24"
        },
        "yaklasik_fiyat_usd_kg": "80 - 100",
        "tipik_kullanim": "Düşük yenileme oranına (refresh rate) sahip, ekonomik ve yüksek performanslı fonksiyonel plastik parçalar."
    },
    {
        "isim": "EOS TPU 1301",
        "marka_platform": "EOS",
        "teknoloji": "SLS",
        "mekanik_ozellikler": {
            "cekme_dayanimi": "9 MPa",
            "kopma_uzamasi": "%300"
        },
        "yaklasik_fiyat_usd_kg": "120 - 150",
        "tipik_kullanim": "Ayakkabı tabanları, sızdırmazlık elemanları, hortumlar ve darbe emici esnek endüstriyel parçalar."
    },
    {
        "isim": "EOS PrimeCast 101",
        "marka_platform": "EOS",
        "teknoloji": "SLS",
        "mekanik_ozellikler": {
            "cekme_dayanimi": "6 MPa",
            "kopma_uzamasi": "%2"
        },
        "yaklasik_fiyat_usd_kg": "90 - 120",
        "tipik_kullanim": "Hassas döküm (investment casting) modelleri ve master modeller için eriyebilir polistiren malzeme."
    },
    {
        "isim": "EOS PP 3000",
        "marka_platform": "EOS",
        "teknoloji": "SLS",
        "mekanik_ozellikler": {
            "cekme_dayanimi": "30 MPa",
            "kopma_uzamasi": "%15"
        },
        "yaklasik_fiyat_usd_kg": "110 - 140",
        "tipik_kullanim": "Kimyasal tanklar, sıvı taşıma sistemleri, ambalaj prototipleri ve yüksek kimyasal direnç gerektiren parçalar."
    },
    {
        "isim": "EOS Aluminium AlSi10Mg",
        "marka_platform": "EOS",
        "teknoloji": "DMLS/SLM",
        "mekanik_ozellikler": {
            "cekme_dayanimi": "340 - 410 MPa",
            "kopma_uzamasi": "%9 - %11"
        },
        "yaklasik_fiyat_usd_kg": "80 - 110",
        "tipik_kullanim": "Otomotiv, havacılık ve genel makine sektöründe hafif, yüksek mukavemetli ve iyi ısıl iletkenliğe sahip parçalar."
    },
    {
        "isim": "EOS Titanium Ti6Al4V",
        "marka_platform": "EOS",
        "teknoloji": "DMLS/SLM",
        "mekanik_ozellikler": {
            "cekme_dayanimi": "950 - 1050 MPa",
            "kopma_uzamasi": "%10 - %14"
        },
        "yaklasik_fiyat_usd_kg": "250 - 400",
        "tipik_kullanim": "Havacılık, savunma ve biyo-uyumlu medikal implantlar, yüksek mukavemet/ağırlık oranı gerektiren kritik yapılar."
    },
    {
        "isim": "EOS StainlessSteel 316L",
        "marka_platform": "EOS",
        "teknoloji": "DMLS/SLM",
        "mekanik_ozellikler": {
            "cekme_dayanimi": "540 - 640 MPa",
            "kopma_uzamasi": "%35 - %50"
        },
        "yaklasik_fiyat_usd_kg": "70 - 100",
        "tipik_kullanim": "Korozyon direnci yüksek gıda, kimya ve denizcilik sektörü ekipmanları, cerrahi aletler ve lüks tüketim ürünleri."
    },
    {
        "isim": "EOS NickelAlloy IN718",
        "marka_platform": "EOS",
        "teknoloji": "DMLS/SLM",
        "mekanik_ozellikler": {
            "cekme_dayanimi": "1000 - 1400 MPa",
            "kopma_uzamasi": "%12 - %20"
        },
        "yaklasik_fiyat_usd_kg": "180 - 260",
        "tipik_kullanim": "Gaz türbini kanatları, roket motoru parçaları, yüksek sıcaklık ve basınç altında çalışan kimyasal tesis elemanları."
    },
    {
        "isim": "EOS CobaltChrome SP2",
        "marka_platform": "EOS",
        "teknoloji": "DMLS/SLM",
        "mekanik_ozellikler": {
            "cekme_dayanimi": "1100 - 1350 MPa",
            "kopma_uzamasi": "%10 - %15"
        },
        "yaklasik_fiyat_usd_kg": "220 - 320",
        "tipik_kullanim": "Diş protezleri, kuronlar ve köprüler, aşınmaya dayanıklı endüstriyel makine bileşenleri."
    },
    {
        "isim": "EOS CobaltChrome MP1",
        "marka_platform": "EOS",
        "teknoloji": "DMLS/SLM",
        "mekanik_ozellikler": {
            "cekme_dayanimi": "1000 - 1100 MPa",
            "kopma_uzamasi": "%15 - %18"
        },
        "yaklasik_fiyat_usd_kg": "240 - 340",
        "tipik_kullanim": "Medikal implantlar (kalça, diz, omuz eklemleri), kemik protezleri, biyo-uyumluluk ve yüksek mukavemet gerektiren endüstriyel fırın parçaları."
    },
    {
        "isim": "EOS Titanium Ti CP (Commercially Pure)",
        "marka_platform": "EOS",
        "teknoloji": "DMLS/SLM",
        "mekanik_ozellikler": {
            "cekme_dayanimi": "570 MPa",
            "kopma_uzamasi": "%20"
        },
        "yaklasik_fiyat_usd_kg": "200 - 300",
        "tipik_kullanim": "Üstün korozyon direnci ve biyo-uyumluluk gerektiren kimyasal işleme tesisleri, cerrahi implantlar ve denizcilik donanımları."
    },
    {
        "isim": "EOS NickelAlloy IN625",
        "marka_platform": "EOS",
        "teknoloji": "DMLS/SLM",
        "mekanik_ozellikler": {
            "cekme_dayanimi": "900 - 980 MPa",
            "kopma_uzamasi": "%30 - %40"
        },
        "yaklasik_fiyat_usd_kg": "190 - 270",
        "tipik_kullanim": "Deniz altı borulama sistemleri, açık deniz petrol platform ekipmanları ve yüksek korozyon ile sıcaklık dayanımı gerektiren kimyasal reaktörler."
    },
    {
        "isim": "EOS MaragingSteel MS1",
        "marka_platform": "EOS",
        "teknoloji": "DMLS/SLM",
        "mekanik_ozellikler": {
            "cekme_dayanimi": "1150 - 2000 MPa",
            "kopma_uzamasi": "%2 - %5"
        },
        "yaklasik_fiyat_usd_kg": "120 - 180",
        "tipik_kullanim": "Enjeksiyon kalıpları (iç soğutma kanallı), yüksek mukavemet ve sertlik gerektiren şaftlar, miller ve dişliler."
    },
    {
        "isim": "EOS StainlessSteel 17-4PH",
        "marka_platform": "EOS",
        "teknoloji": "DMLS/SLM",
        "mekanik_ozellikler": {
            "cekme_dayanimi": "1050 - 1150 MPa",
            "kopma_uzamasi": "%12 - %15"
        },
        "yaklasik_fiyat_usd_kg": "80 - 110",
        "tipik_kullanim": "Yüksek mukavemet, sertlik ve korozyon direnci kombinasyonu gerektiren valfler, pompa çarkları ve mekanik bağlantı elemanları."
    },
    {
        "isim": "EOS StainlessSteel CX",
        "marka_platform": "EOS",
        "teknoloji": "DMLS/SLM",
        "mekanik_ozellikler": {
            "cekme_dayanimi": "1100 - 1700 MPa",
            "kopma_uzamasi": "%10 - %12"
        },
        "yaklasik_fiyat_usd_kg": "100 - 140",
        "tipik_kullanim": "Korozyona dayanıklı kalıp parçaları, plastik enjeksiyon kalıplarında su soğutmalı maça ve ekler."
    },
    {
        "isim": "EOS NickelAlloy HX",
        "marka_platform": "EOS",
        "teknoloji": "DMLS/SLM",
        "mekanik_ozellikler": {
            "cekme_dayanimi": "750 - 800 MPa",
            "kopma_uzamasi": "%35 - %40"
        },
        "yaklasik_fiyat_usd_kg": "190 - 280",
        "tipik_kullanim": "Havacılık ve gaz türbini yanma odası bileşenleri, yüksek sıcaklıkta oksidasyon direnci gerektiren endüstriyel fırın parçaları."
    },
    {
        "isim": "EOS Copper Cu",
        "marka_platform": "EOS",
        "teknoloji": "DMLS/SLM",
        "mekanik_ozellikler": {
            "cekme_dayanimi": "220 MPa",
            "kopma_uzamasi": "%35"
        },
        "yaklasik_fiyat_usd_kg": "130 - 190",
        "tipik_kullanim": "Elektrik ve ısıl iletkenliğin kritik olduğu ısı değiştiriciler, indüksiyon bobinleri ve elektrik kontak elemanları."
    },
    {
        "isim": "HP 3D HR PA 12",
        "marka_platform": "HP Multi Jet Fusion",
        "teknoloji": "MJF",
        "mekanik_ozellikler": {
            "cekme_dayanimi": "48 MPa",
            "kopma_uzamasi": "%20"
        },
        "yaklasik_fiyat_usd_kg": "50 - 65",
        "tipik_kullanim": "Yüksek boyutsal hassasiyete sahip fonksiyonel parçalar, muhafazalar, montaj aparatları ve düşük adetli seri üretim parçaları."
    },
    {
        "isim": "HP 3D HR PA 11",
        "marka_platform": "HP Multi Jet Fusion",
        "teknoloji": "MJF",
        "mekanik_ozellikler": {
            "cekme_dayanimi": "50 MPa",
            "kopma_uzamasi": "%50"
        },
        "yaklasik_fiyat_usd_kg": "75 - 95",
        "tipik_kullanim": "Yüksek darbe dayanımı ve esneklik gerektiren menteşeler, klipsler, spor ekipmanları ve otomotiv iç parçaları."
    },
    {
        "isim": "HP 3D HR PP",
        "marka_platform": "HP Multi Jet Fusion",
        "teknoloji": "MJF",
        "mekanik_ozellikler": {
            "cekme_dayanimi": "30 MPa",
            "kopma_uzamasi": "%15"
        },
        "yaklasik_fiyat_usd_kg": "85 - 110",
        "tipik_kullanim": "Asitlere ve kimyasallara dayanıklı ambalajlar, sıvı taşıma boruları ve otomotiv motor içi akışkan kapları."
    },
    {
        "isim": "HP 3D HR PA 12 Glass Beads",
        "marka_platform": "HP Multi Jet Fusion",
        "teknoloji": "MJF",
        "mekanik_ozellikler": {
            "cekme_dayanimi": "30 MPa",
            "kopma_uzamasi": "%6"
        },
        "yaklasik_fiyat_usd_kg": "60 - 80",
        "tipik_kullanim": "Cam boncuk takviyeli, yüksek rijitlik ve aşınma direnci gerektiren muhafazalar, otomotiv dış trim parçaları ve fikstürler."
    },
    {
        "isim": "HP 3D HR TPU (Ultrasint TPU 01)",
        "marka_platform": "HP Multi Jet Fusion",
        "teknoloji": "MJF",
        "mekanik_ozellikler": {
            "cekme_dayanimi": "9 MPa",
            "kopma_uzamasi": "%220"
        },
        "yaklasik_fiyat_usd_kg": "90 - 120",
        "tipik_kullanim": "Esnek sızdırmazlık elemanları, contalar, koruyucu kılıflar, ayakkabı tabanları ve şok emici endüstriyel aparatlar."
    },
    {
        "isim": "HP 3D HR TPA (Evonik)",
        "marka_platform": "HP Multi Jet Fusion",
        "teknoloji": "MJF",
        "mekanik_ozellikler": {
            "cekme_dayanimi": "9 MPa",
            "kopma_uzamasi": "%190"
        },
        "yaklasik_fiyat_usd_kg": "110 - 140",
        "tipik_kullanim": "Çok yüksek geri esneme (rebound) ve esneklik gerektiren hafif spor ekipmanları ve otomotiv esnek bileşenleri."
    },
    {
        "isim": "Sinterit PA12 Smooth",
        "marka_platform": "Sinterit",
        "teknoloji": "SLS",
        "mekanik_ozellikler": {
            "cekme_dayanimi": "53 MPa",
            "kopma_uzamasi": "%12"
        },
        "yaklasik_fiyat_usd_kg": "90 - 120",
        "tipik_kullanim": "Detaylı yüzey kalitesi ve yüksek mukavemet gerektiren prototipler, eğitim ve AR-GE modelleri."
    },
    {
        "isim": "Sinterit PA11 Onyx",
        "marka_platform": "Sinterit",
        "teknoloji": "SLS",
        "mekanik_ozellikler": {
            "cekme_dayanimi": "48 MPa",
            "kopma_uzamasi": "%40"
        },
        "yaklasik_fiyat_usd_kg": "130 - 160",
        "tipik_kullanim": "Yüksek darbe dayanımı ve esneklik gerektiren endüstriyel muhafazalar, klipsler ve zorlu ortam prototipleri."
    },
    {
        "isim": "Sinterit Flexa Grey (TPU)",
        "marka_platform": "Sinterit",
        "teknoloji": "SLS",
        "mekanik_ozellikler": {
            "cekme_dayanimi": "3.7 MPa",
            "kopma_uzamasi": "%137"
        },
        "yaklasik_fiyat_usd_kg": "140 - 170",
        "tipik_kullanim": "Orta esneklikte contalar, hortumlar, giyilebilir teknoloji aksesuarları ve darbe emici modeller."
    },
    {
        "isim": "Sinterit Flexa Bright (TPU)",
        "marka_platform": "Sinterit",
        "teknoloji": "SLS",
        "mekanik_ozellikler": {
            "cekme_dayanimi": "4 MPa",
            "kopma_uzamasi": "%135"
        },
        "yaklasik_fiyat_usd_kg": "150 - 180",
        "tipik_kullanim": "Renklendirilebilir (boyanabilir) esnek parçalar, medikal simülatörler ve esnek tasarım prototipleri."
    },
    {
        "isim": "Sinterit PA11 CF (Carbon Fiber)",
        "marka_platform": "Sinterit",
        "teknoloji": "SLS",
        "mekanik_ozellikler": {
            "cekme_dayanimi": "66 MPa",
            "kopma_uzamasi": "%18"
        },
        "yaklasik_fiyat_usd_kg": "170 - 210",
        "tipik_kullanim": "Karbon fiber takviyeli, ekstrem rijitlik ve hafiflik gerektiren drone gövdeleri, motor sporları parçaları ve yapısal aparatlar."
    },
    {
        "isim": "Sinterit PA11 ESD",
        "marka_platform": "Sinterit",
        "teknoloji": "SLS",
        "mekanik_ozellikler": {
            "cekme_dayanimi": "48 MPa",
            "kopma_uzamasi": "%27"
        },
        "yaklasik_fiyat_usd_kg": "170 - 210",
        "tipik_kullanim": "Antistatik (ESD güvenli) hassas elektronik montaj aparatları, patlayıcı ortamlar için koruyucu muhafazalar."
    },
    {
        "isim": "Sinterit PP",
        "marka_platform": "Sinterit",
        "teknoloji": "SLS",
        "mekanik_ozellikler": {
            "cekme_dayanimi": "24 MPa",
            "kopma_uzamasi": "%33"
        },
        "yaklasik_fiyat_usd_kg": "110 - 140",
        "tipik_kullanim": "Kimyasal dayanım gerektiren endüstriyel borular, su depoları, sızdırmaz kutular ve otomotiv sıvı kapları."
    },
    {
        "isim": "Formlabs Nylon 12 Powder",
        "marka_platform": "Formlabs",
        "teknoloji": "SLS",
        "mekanik_ozellikler": {
            "cekme_dayanimi": "50 MPa",
            "kopma_uzamasi": "%11"
        },
        "yaklasik_fiyat_usd_kg": "90 - 110",
        "tipik_kullanim": "Genel amaçlı fonksiyonel prototipler, mekanik montaj parçaları ve düşük adetli son kullanım parçaları."
    },
    {
        "isim": "Formlabs Nylon 11 Powder",
        "marka_platform": "Formlabs",
        "teknoloji": "SLS",
        "mekanik_ozellikler": {
            "cekme_dayanimi": "49 MPa",
            "kopma_uzamasi": "%40"
        },
        "yaklasik_fiyat_usd_kg": "110 - 130",
        "tipik_kullanim": "Yüksek süneklik ve darbe dayanımı gerektiren menteşeler, ince duvarlı borular, protezler ve klipsler."
    },
    {
        "isim": "Formlabs Nylon 12 GF Powder",
        "marka_platform": "Formlabs",
        "teknoloji": "SLS",
        "mekanik_ozellikler": {
            "cekme_dayanimi": "38 MPa",
            "kopma_uzamasi": "%8"
        },
        "yaklasik_fiyat_usd_kg": "110 - 130",
        "tipik_kullanim": "Cam dolgulu, yüksek rijitlik ve ısıl dayanım gerektiren motor bölmesi parçaları, endüstriyel muhafazalar ve fikstürler."
    },
    {
        "isim": "Formlabs Nylon 11 CF Powder",
        "marka_platform": "Formlabs",
        "teknoloji": "SLS",
        "mekanik_ozellikler": {
            "cekme_dayanimi": "69 MPa",
            "kopma_uzamasi": "%9"
        },
        "yaklasik_fiyat_usd_kg": "140 - 170",
        "tipik_kullanim": "Karbon fiber takviyeli, yüksek mukavemet ve hafiflik gerektiren havacılık ve motor sporları aparatları, robot kollar ve yapısal braketler."
    },
    {
        "isim": "Formlabs TPU 90A Powder",
        "marka_platform": "Formlabs",
        "teknoloji": "SLS",
        "mekanik_ozellikler": {
            "cekme_dayanimi": "26 MPa",
            "kopma_uzamasi": "%310"
        },
        "yaklasik_fiyat_usd_kg": "120 - 150",
        "tipik_kullanim": "Esnek koruyucu kılıflar, ayakkabı tabanları, contalar, sızdırmazlık halkaları ve yumuşak dokulu tüketici ürünleri."
    },
    {
        "isim": "Formlabs Nylon 12 Tough Powder",
        "marka_platform": "Formlabs",
        "teknoloji": "SLS",
        "mekanik_ozellikler": {
            "cekme_dayanimi": "48 MPa",
            "kopma_uzamasi": "%18"
        },
        "yaklasik_fiyat_usd_kg": "100 - 120",
        "tipik_kullanim": "Yüksek süneklik, geri dönüşüm oranı yüksek, boyutsal doğruluk ve mükemmel mekanik kararlılık sunan fonksiyonel parçalar."
    },
    {
        "isim": "Formlabs Polypropylene Powder",
        "marka_platform": "Formlabs",
        "teknoloji": "SLS",
        "mekanik_ozellikler": {
            "cekme_dayanimi": "25 MPa",
            "kopma_uzamasi": "%20"
        },
        "yaklasik_fiyat_usd_kg": "110 - 130",
        "tipik_kullanim": "Laboratuvar ekipmanları, asit direnci gerektiren kaplar, sızdırmaz borulama parçaları ve esnek kapaklar."
    },
    {
        "isim": "BASF Ultrasint PA12",
        "marka_platform": "BASF Forward AM",
        "teknoloji": "SLS",
        "mekanik_ozellikler": {
            "cekme_dayanimi": "48 MPa",
            "kopma_uzamasi": "%18"
        },
        "yaklasik_fiyat_usd_kg": "70 - 90",
        "tipik_kullanim": "Çok yönlü endüstriyel parçalar, otomotiv iç kaplamaları, karmaşık borulama sistemleri ve makine korumaları."
    },
    {
        "isim": "BASF Ultrasint PA11",
        "marka_platform": "BASF Forward AM",
        "teknoloji": "SLS",
        "mekanik_ozellikler": {
            "cekme_dayanimi": "45 MPa",
            "kopma_uzamasi": "%45"
        },
        "yaklasik_fiyat_usd_kg": "85 - 110",
        "tipik_kullanim": "Bio-tabanlı esnek parçalar, yüksek dinamik yüke maruz kalan menteşeler ve darbe dayanımlı bileşenler."
    },
    {
        "isim": "BASF Ultrasint PA11 Black CF",
        "marka_platform": "BASF Forward AM",
        "teknoloji": "SLS",
        "mekanik_ozellikler": {
            "cekme_dayanimi": "71 MPa",
            "kopma_uzamasi": "%11"
        },
        "yaklasik_fiyat_usd_kg": "150 - 180",
        "tipik_kullanim": "Karbon fiber dolgulu, çok yüksek rijitlik ve mukavemet gerektiren endüstriyel makine gövdeleri ve aparatlar."
    },
    {
        "isim": "BASF Ultrasint PA11 ESD",
        "marka_platform": "BASF Forward AM",
        "teknoloji": "SLS",
        "mekanik_ozellikler": {
            "cekme_dayanimi": "49 MPa",
            "kopma_uzamasi": "%25"
        },
        "yaklasik_fiyat_usd_kg": "140 - 170",
        "tipik_kullanim": "Elektrostatik deşarj koruması gerektiren elektronik test fikstürleri, yarı iletken taşıma tepsileri ve patlayıcı sıvı boruları."
    },
    {
        "isim": "BASF Ultrasint TPU 88A",
        "marka_platform": "BASF Forward AM",
        "teknoloji": "SLS",
        "mekanik_ozellikler": {
            "cekme_dayanimi": "11 MPa",
            "kopma_uzamasi": "%280"
        },
        "yaklasik_fiyat_usd_kg": "100 - 130",
        "tipik_kullanim": "Esneklik, darbe sönümleme ve mükemmel yüzey kalitesi gerektiren otomotiv amortisör körükleri, kılıflar ve contalar."
    },
    {
        "isim": "BASF Ultrasint TPU 01",
        "marka_platform": "BASF Forward AM",
        "teknoloji": "MJF",
        "mekanik_ozellikler": {
            "cekme_dayanimi": "9 MPa",
            "kopma_uzamasi": "%220"
        },
        "yaklasik_fiyat_usd_kg": "90 - 120",
        "tipik_kullanim": "HP Jet Fusion 5200 sistemleri için optimize edilmiş, ayakkabı tabanları, koruyucu başlık içlikleri ve karmaşık esnek lattice yapıları."
    },
    {
        "isim": "BASF Ultrasint PP (Polypropylene)",
        "marka_platform": "BASF Forward AM",
        "teknoloji": "SLS",
        "mekanik_ozellikler": {
            "cekme_dayanimi": "21 MPa",
            "kopma_uzamasi": "%30"
        },
        "yaklasik_fiyat_usd_kg": "80 - 100",
        "tipik_kullanim": "Mükemmel kimyasal direnç ve yüksek kopma uzaması kombinasyonu sunan akışkan boruları, kaplar ve otomotiv sıvı hazneleri."
    },
    {
        "isim": "BASF Ultrasint PA12 GF",
        "marka_platform": "BASF Forward AM",
        "teknoloji": "SLS",
        "mekanik_ozellikler": {
            "cekme_dayanimi": "40 MPa",
            "kopma_uzamasi": "%7"
        },
        "yaklasik_fiyat_usd_kg": "80 - 105",
        "tipik_kullanim": "Cam elyaf takviyeli, ısıl kararlılığı ve bükülme mukavemeti yüksek rüzgar tüneli modelleri, fikstürler ve motor parçaları."
    },
    {
        "isim": "Materialise Polyamide (PA 12)",
        "marka_platform": "Materialise",
        "teknoloji": "SLS",
        "mekanik_ozellikler": {
            "cekme_dayanimi": "48 MPa",
            "kopma_uzamasi": "%15"
        },
        "yaklasik_fiyat_usd_kg": "80 - 100",
        "tipik_kullanim": "Tıbbi cihazlar, fonksiyonel prototipler, karmaşık geometrilere sahip endüstriyel muhafazalar ve dayanıklı montaj aparatları."
    },
    {
        "isim": "Materialise Alumide",
        "marka_platform": "Materialise",
        "teknoloji": "SLS",
        "mekanik_ozellikler": {
            "cekme_dayanimi": "48 MPa",
            "kopma_uzamasi": "%4"
        },
        "yaklasik_fiyat_usd_kg": "100 - 120",
        "tipik_kullanim": "Metalik görünüm ve his gerektiren estetik prototipler, yüksek rijitliğe sahip rüzgar tüneli modelleri."
    },
    {
        "isim": "Materialise Bluesint PA12",
        "marka_platform": "Materialise",
        "teknoloji": "SLS",
        "mekanik_ozellikler": {
            "cekme_dayanimi": "46 MPa",
            "kopma_uzamasi": "%15"
        },
        "yaklasik_fiyat_usd_kg": "60 - 80",
        "tipik_kullanim": "%100 oranında geri dönüştürülmüş toz kullanılan, sürdürülebilir fonksiyonel prototipler ve görsel modeller."
    },
    {
        "isim": "Materialise PA-GF",
        "marka_platform": "Materialise",
        "teknoloji": "SLS",
        "mekanik_ozellikler": {
            "cekme_dayanimi": "42 MPa",
            "kopma_uzamasi": "%6"
        },
        "yaklasik_fiyat_usd_kg": "90 - 110",
        "tipik_kullanim": "Cam dolgulu yapısıyla termal ve boyutsal kararlılık gerektiren otomotiv motor bölmesi parçaları ve fikstürler."
    },
    {
        "isim": "Materialise TPU (Laser Sintering)",
        "marka_platform": "Materialise",
        "teknoloji": "SLS",
        "mekanik_ozellikler": {
            "cekme_dayanimi": "8 MPa",
            "kopma_uzamasi": "%250"
        },
        "yaklasik_fiyat_usd_kg": "110 - 140",
        "tipik_kullanim": "Elastik özellikler sunan endüstriyel contalar, hortumlar ve darbe sönümleme gerektiren tasarımlar."
    },
    {
        "isim": "Materialise Polypropylene (PP)",
        "marka_platform": "Materialise",
        "teknoloji": "SLS",
        "mekanik_ozellikler": {
            "cekme_dayanimi": "22 MPa",
            "kopma_uzamasi": "%25"
        },
        "yaklasik_fiyat_usd_kg": "90 - 115",
        "tipik_kullanim": "Laboratuvar araç gereçleri, kimyasal tank parçaları, otomotiv sıvı kapları ve esnek klips mekanizmaları."
    },
    {
        "isim": "Stratasys High Yield PA11 (SAF)",
        "marka_platform": "Stratasys (H350)",
        "teknoloji": "SLS",
        "mekanik_ozellikler": {
            "cekme_dayanimi": "51 MPa",
            "kopma_uzamasi": "%45"
        },
        "yaklasik_fiyat_usd_kg": "80 - 100",
        "tipik_kullanim": "%100 biyolojik kökenli, yüksek darbe ve dinamik yorulma dayanımı gerektiren fonksiyonel son kullanım parçaları, menteşeler."
    },
    {
        "isim": "Stratasys High Yield PA12 (SAF)",
        "marka_platform": "Stratasys (H350)",
        "teknoloji": "SLS",
        "mekanik_ozellikler": {
            "cekme_dayanimi": "48 MPa",
            "kopma_uzamasi": "%15"
        },
        "yaklasik_fiyat_usd_kg": "70 - 90",
        "tipik_kullanim": "Yüksek boyutsal kararlılık ve yüzey kalitesi sunan, düşük adetli seri üretim parçaları, elektrik muhafazaları ve montaj aparatları."
    }
]

print(f"Toplam malzeme sayısı: {len(materials)}")
with open('materials.json', 'w', encoding='utf-8') as f:
    json.dump(materials, f, ensure_ascii=False, indent=4)
print("materials.json başarıyla oluşturuldu.")
