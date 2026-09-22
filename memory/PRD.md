# DEADZONE — Ürün ve geliştirme kaydı

## Orijinal problem statement
Bir zombi project oyunu istiyorum. Webde çalışacak grafikleri ise görselde attığım gibi olacak ve online bir oyun olacak. Harita ise büyük bir alan olacak etrafta ağaç ev gibi rastgele renderlensin oynayış tarzı ise GTA gibi olacak. W A S D ve mouse ile oynanabilecek olacak. Harita büyüklüğü ise 200 oyuncuyu rahat şekilde sığacak bir alan olacak. Kamera ise oyuncuyu takip edecek ve sadece gittiği alanı görebilecek. Oyuna başlamak için ise Start game olacak ve silahını seçecek. Silahlar ise AK47,Ak117,AK107,Otomatik fişek atan tüfek ve bu tüfekler kaliteli görünsün oyuncunun elinde net belli olsun. Frendly fire açık olacak etrafta rastgele zombiler olacak öldürdükçe puan gelecek.

## Kullanıcının açık seçimleri
- Tarayıcıda 3D izometrik gerçek çok oyunculu oyun. Referans: Project Zomboid kasabaları ve siyah metal AK serisi silah fotoğrafları.
- 200 eşzamanlı oyuncu kapasitesinin ayrıca yük testi gerektirdiği açıklandı; harita 1.600×1.600 m. Kapasite doğrulaması henüz yapılmadı.
- Ana sayfada yalnız dinamik yeşil arka plan ve START GAME. Ardından navbar, silah seçimi, OYUNA KATIL. Kamera fare tekerleği ile karaktere yaklaşabilmeli.
- Son istek: Daha akıcı yürüyüş/koşu ve düşük gecikmeli atış. Gerçek AK47 sesi ve her silaha farklı gerçekçi ses. M4, roketatar, minigun, alev püskürtücü VE yerde ateş bırakan lav fırlatıcı.
- Girilebilir benzinlik, otel ve ev: sadece saklanma/gerçek duvar engelleri; ekstra hasar koruması OLMAYACAK.
- Zombiler kendi hallerinde dolaşmalı. Yalnızca 5 m yakınlıkta saldırmalı, uzaklaşınca takibi bırakmalı.
- Lisansı uygun ses kayıtları geliştirici tarafından bulunabilir. Kullanıcı uzun testing-agent turları istemiyor; kısa odaklı kontroller kullanılmalı.

## Kullanıcı profili
- WASD ve fare ile masaüstünde oynayan, GTA benzeri hızlı tepki bekleyen hayatta kalma oyuncusu.
- Aynı dünyaya çağrı adıyla katılan arkadaş grupları; PvP/dost ateşi açık.
- Mobil ziyaretçiler: tek düğmeli giriş, dokunmatik hareket/ateş ve duyarlı teçhizat arayüzü.

## Mimari
- React + React Router, Shadcn Dialog/Button, Turkish Barlow/Bebas UI.
- `/`: yeşil hareketli WebGL shader + tek START GAME. `/loadout`: 9 silah, çağrı adı, navbar. `/play`: oyun. `/settings`, `/leaderboard`: mevcut oturum üstü modallar.
- Three.js ortografik izometrik dünya, oyuncu merkezli kamera, 4–40 zoom sınırları, yumuşak tekerlek hareketi.
- PBR silah geometrisi hem önizlemede hem oyuncunun elinde aynı. Köşeleri yumuşatılmış gövdeler, kavisli şarjörler; 9 farklı model. Karakterin diz/kalça adım animasyonu, yürüyüş/koşu harmanlaması ve geri tepme.
- Cannon-es yerel hareket tahmini: sunucunun ürettiği duvar/furniture dikdörtgenleri. Pymunk sunucu çarpışmaları, otoriter hareket/hasar/puan/cephane.
- Dedicated Web Worker WebSocket, 20Hz girdi ve ağ zamanlaması; GPU/UI çizimi ağı durdurmaz. Tuş ve fare değişiklikleri anlık gönderilir. Kısa tıklama için sunucu `fire_pressed` tetiği, istemci anlık ses/muzzle/recoil; kendi sunucu efektleri tekrar oynatılmaz.
- FastAPI 8001, MongoDB/Motor kalıcı pozitif tur skorları. Ortak deterministik 1.6km dünya, 20Hz tek sunucu simülasyonu, 85m ilgi bölgesi. Zombiler in-memory.
- Aynı duvarlar silah görüş hattını ve hareketi keser. Girilebilir binaların çatısı/yüksek duvarları içeride gizlenir, zemini/eşyaları görünür.
- Tüm API URL'leri `REACT_APP_BACKEND_URL`; Mongo yalnız mevcut `MONGO_URL`/`DB_NAME`. Mevcut korumalı ortam değişkenleri değiştirilmedi.

## Statik gereksinimler
1. Çalışan gerçek çok oyunculu oturum, WASD, Shift koşu, fare nişan/ateş, R şarjör.
2. Dost ateşi, rastgele zombiler, öldürme puanı, ölüm/yeniden doğma ve sıralama.
3. Başlangıç akışı ve görsel sadelik kullanıcı seçimlerine uymalı.
4. Gerçek kayıtların lisansları sağlanmalı; tüm silah seslerinin birebir gerçek model kaydı olduğu iddia edilmemeli.
5. İç mekânlar dokunulmaz bölge değil, fiziksel saklanma alanı.

## Tamamlananlar — 2026-09-22
- Temel gerçek WebSocket çok oyunculu oyun, 4 silah, skor, Mongo sıralama, yenileme, ikmal, takip kamerası, mobil kontroller.
- İkinci düzenleme: tek düğmeli yeşil shader giriş, ayrı teçhizat aşaması; yeniden modellenen silahlar; tekerlek zoom 4–40.
- Yavaş UI çiziminde komut gecikmesi için ağ worker'ı; başlangıçta ilk hareket/ateşe kadar hazırlık koruması, ateş korumayı sonlandırır.
- Son özellik seti: 9 silah. AK47 / AK117 / AK107 / AA12 / M4A1 / RPG7 / M134 / ALEV21 / LAV6.
- Otoriter roket uçuşu ve alan patlaması; minigun hızlı büyük şarjör; kısa mesafe konik alev hasarı; lav mermisi yayı + 8 saniye kalıcı hasarlı ateş alanı. Dost ateşi ve fiziksel görüş hattı uygulanır.
- 402 girilebilir yapı: benzinlik, otel, ev; açık kapılar, odalar, yatak, kanepe, raf, tezgâh. Duvar ve eşyalar fiziksel engel. İçeride çatı kaldırma ve HUD mekân adı. Ek dokunulmazlık yok.
- Zombi idle/wander/attack davranışı: yalnız LOS açık ve mesafe ≤5m ise saldırı; >5m olunca dolaşmaya dönüş. Uzakta oyuncuya doğru otomatik avlanma kaldırıldı.
- İstemci hareket tahmini, hızlı hızlanma/durma, diz bükümlü adım, yürüyüş/koşu geçişi, kamera tepkisi. Yerel atış geri bildirimi sunucu cevabından önce gerçekleşir; hasar sunucuda kalır.
- Vertex-color geometry batching: örnek screenshot oturumunda sahne draw call sayısı 387'den 50'ye düştü. Otomatik grafik kalitesi ve gölge/piksel yoğunluğu uyarlaması var. Bu bir FPS veya 200 oyuncu performans garantisi değildir.
- 11 yerel WAV ses dosyası, 9 ayrı silah sesi. Silah sesleri artık önceki sentezlenmiş gürültü yerine kayıt tabanlı. Sesler önceden yüklenir/decode edilir; WebAudio düşük gecikmeli çalışır.

### Ses kaynakları ve doğruluk
- Gerçek AK47 (C_28P), AR15/M4 (D_32P) ve Nova 12ga: Free Firearm Sound Library, CC0. AK117/AK107 bu AK kayıtlarının farklı uyarlamalarıdır; AA12 için gerçek 12ga Nova kaydı uyarlanmıştır.
- Gerçek M134 kaydı: rob762x51 / Freesound 85246, CC0.
- Alev: Joseph SARDIN / BigSoundBank 0931 gerçek gaz şaloması kaydı, CC0. Askeri alev silahının birebir kaydı olduğu iddia edilmez.
- Roket/lav/patlama/şarjör: Q009 efektleri, CC BY-SA 3.0; uyarlanan WAV'ler aynı lisansla dağıtılır. Lav kurgusal silah; sesi tasarlanmış efekt.
- Lisans ve kaynaklar `/audio/CREDITS.txt`, `/audio/Q009-LICENSE.txt`; ayarlarda görünür bağlantı. Kalıcı ham kaynaklar `/root/deadzone-source-audio`; hazırlama aracı `/app/scripts/prepare_audio.py`.

## Doğrulama
- Önceki `/app/test_reports/iteration_1.json` giriş/zoom testinde erken ölüm engeli bildirmişti; hazırlık koruması ve ağ worker'ı sonrasında ana ajan hareket, ateş, zoom ve modalları yeniden denedi.
- Son derleme `yarn build` başarılı. Dış URL üzerinden 9 silah, 402 iç mekân ve ses HTTP200 doğrulandı.
- Playwright kısa son kontrolde 9 kart, M4 oturumu, gerçek hareket x2.94→-0.85, atış 30→23, yerel efekt, Shift koşu ve zoom doğrulandı. Çizim 50 call. Uygulama console hatası yok; platform telemetry iptalleri uygulamaya ait değil.
- Kullanıcının kısa kontrol tercihiyle tek kısa backend smoke turu: `/app/test_reports/iteration_2.json`, 6/6 geçti. API, 5m AI, kapı/duvar/oda, iç mekânda hasar, yeni silah mekaniği, farklı ses hash'leri ve lisanslar. Uzun e2e ve 200 oyuncu testi yapılmadı.
- Combat smoke testinde görüş hattı izole edildi; gerçek geometri için kapı/duvar kontrolleri ayrıca var. Tüm binaların tarayıcı içi yürüyerek kapsamlı gezilmesi yapılmadı.

## Öncelikli backlog / sonraki işler
- P0: Son kısa kontrol kapsamında bilinen engelleyici hata yok.
- P1: 200 eşzamanlı oyuncu için ayrı yük testi ve gerekirse mekânsal indeks/tick dağıtımı; kapasiteyi doğrulamadan 200 oyuncu garantisi verme.
- P1: Daha geniş ağ gecikmesi altında tahmin/uzlaşma ve gecikme telafisi; deterministik LOS combat regresyonu.
- P2: İsteğe bağlı yüksek kaliteli lisanslı insan iskeleti/motion-capture animasyonları, silah aksesuarları ve daha ayrıntılı iç dekorasyon.
- P2: Kullanıcı isterse silah dengeleme, daha ayrıntılı mekânsal ses/yankı ve çevre sesleri.
- Uzun testing-agent turlarını kendiliğinden tekrarlama; yeni talebin kapsamına uygun kısa kontrollerle ilerle.