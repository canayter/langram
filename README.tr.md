# Langram

*[English](README.md)*

İngilizce konuşanlar için, araştırmaya dayalı bir Türkçe kursu. Onu bir flashcard uygulamasından ayıran iki şey var: biçimbilgisi kurallarla öğretilir, çekim tablosuyla değil; ve telaffuz, gerçek formant ölçümlerine karşı çalıştırılır.

**Şu an neredeyiz.** Biçimbilgisi motoru, içerik hattı, bir FastAPI arka ucu ve bir React ön ucu uçtan uca çalışıyor: bir öğrenci misafir olarak giriş yapar, bir dilbilgisi kavramıyla ilk kez karşılaşmadan önce ona dair açık bir bilgi görür, sabit bir listeden değil, doğrudan dilbilgisinden canlı üretilen alıştırmalar yanıtlar, geri bildirim bir ipucundan tam türetime doğru kademeli olarak açılır, ve hangi kuralda tam olarak zorlandığını gösteren bir tanı raporu görür. 459 test var. Proje planından geriye kalan: algı eğitimi ve üretim geri bildirimi, anadili konuşucularıyla kayıt oturumları mümkün olana kadar erteleniyor (bkz. `docs/deferred-audio.md`), ve register/günlük dil parçası (Aşama 8) büyük ölçüde mühendislik değil, anadili konuşucusu değerlendirmesi gerektiriyor.

## Bugün çalışan

```
$ inflect kitap ACC
kitap + ACC
  1. kök sessiz /p/ ile bitiyor ve ek ünlüyle başlıyor
     -> ünlüler arası ötümlüleşme kitab- verir [final_voicing]: kitab
  2. kök bir ünsüzle bitiyor
     -> y kaynaştırma harfi eklenmez [buffer]: kitab
  3. son ünlü /a/ kalın, düz
     -> dörtlü uyum I'yı ı'ya çözer [harmony]: kitabı
  = kitabı
```

Bu türetim bir hata ayıklama yardımcısı değil, ürünün kendisi. Kuralın işlediğini gören bir öğrenci kuralı öğrenir; `kitabı`'yı gören bir öğrenci bir diziyi ezberler.

Daha zor durumlar da aynı şekilde çalışır:

```
$ inflect kayıp ACC          # tek türetimde hem ünlü düşmesi hem ötümlüleşme
$ inflect ev POSS3SG LOC     # evinde, kaynaştırma n'siyle
$ inflect saat PL            # saatler, ön ekler alan uyumsuz bir alıntı kelime
$ inflect çocuk --paradigm   # tam isim çekim tablosu
$ inflect --review           # bir anadili konuşucusunu bekleyen her iddia
```

## Nasıl kurulmuş

Ekler bir kez, arkifonem gösterimiyle yazılır; motor her alomorfu kendisi üretir:

```yaml
- id: ACC
  surface: "-(y)I"      # -i, -ı, -u, -ü değil
  category: case
```

Projede motorun kendi çıktısı dışında hiçbir yerde çekimlenmiş bir yüzey biçimi yoktur. Uygulamanın sabit bir cümle listesi yerine bir dilbilgisinden sınırsız alıştırma üretebilmesini sağlayan kısıtlama tam olarak budur.

Motor kendiliğinden hiçbir Türkçe bilgisi taşımaz. Ünlü envanterleri, uyum tabloları, sessiz sessizler kümesi ve alternasyon eşlemeleri hepsi `content/l2/tr/morphology/phonology.yaml` içinde yaşar. Aynı uyum makinesine sahip akraba bir dil (Tatarca, Azerbaycan Türkçesi) bir çatallanma değil, yeni bir içerik dizinidir.

## Çalıştırmak

**Motor ve testleri:**

```
python -m venv .venv
.venv/Scripts/python.exe -m pip install -e ".[dev]"     # Windows
.venv/Scripts/python.exe -m pytest
```

Gerçek Türkçe yüzey biçimlerinden bir referans seti, tüm sözlük ve her geçerli ek zinciri boyunca hiçbir üretilen biçimin uyumu bozamayacağını doğrulayan özellik tabanlı testler, sesbilgisel ilkeler için birim testleri, ve API ile öğretmenin zamanlama mantığı için bütünleşme testleri.

**Tüm uygulama**, arka uç ve ön uç, yerel bir SQLite veritabanına karşı:

```
python -m langram.validate                                   # içerik CI'da da kontrol edilir
alembic upgrade head                                          # hedefi LANGRAM_DATABASE_URL belirler
python -m langram.db.seed --database-url sqlite:///langram.db --create-tables

uvicorn langram.api.main:app --reload                          # API :8000'de
cd web && npm install && npm run dev                            # arayüz :5173'te, /api'yi yönlendirir
```

Gerçek bir dağıtımda `LANGRAM_SECRET_KEY` ayarlanmalı; ayarlanmazsa her süreç için yeni bir imzalama anahtarı üretilir ve bu da yeniden başlatmada her öğrenciyi oturumdan düşürür.

## Dilbilimsel dürüstlük

Bir anadili konuşucusunun onaylaması gereken her şey, tahmin edilmek yerine içerik dosyalarında işaretlenir; `inflect --review` bunları listeler. `docs/provenance.md`, her iddianın nereden geldiğini ve bilerek eksik bırakılanı kaydeder. Derlem sıklık bantları, uydurulmak yerine yoktur; gerçek bir derlem listesiyle birlikte gelecekler, ondan önce değil.

## Sırada ne var

Register ve günlük dil parçası (Aşama 8): söylem parçacıkları, register çiftleri, konuşma dilindeki kısaltmalar, hitap biçimleri, İngilizcede karşılığı olmayan kalıp ifadeler. İçindeki neredeyse her iddia, yayınlanabilmesi için bir anadili konuşucusunun onayını gerektiriyor; bu da onu zor değil, yavaş aşama yapan şey.

Algı eğitimi ve üretim geri bildirimi (projenin 5. ve 6. aşamaları) ertelendi, terk edilmedi değil. Birkaç anadili konuşucusuyla kayıt oturumları olmadan başlayamazlar. `docs/deferred-audio.md` dosyasında şu an hazır olan ve yeniden başlamak için neyin gerektiği yazılı.
