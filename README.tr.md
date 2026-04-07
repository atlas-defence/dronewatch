# DroneWatch

RF, ses ve görsel sinyalleri kullanarak açık kaynaklı drone tespiti ve takip sistemi.

- **Diller**: [English](README.md) · Türkçe (bu sayfa)

---

## Ekran görüntüsü

![DroneWatch dashboard ekran görüntüsü](screenshot.png)

---

## Genel Bakış

DroneWatch, üç sensör hattı etrafında kurgulanmış modüler bir izleme sistemidir:

- RF tarama
- Akustik tespit
- Kamera tabanlı görsel hareket tespiti

Proje artık hem simülasyon hem de gerçek giriş iş akışlarını destekler. Simülasyon, uygulamanın özel donanım olmadan açılabilmesi için varsayılan olarak kalır; ancak her modül bağımsız olarak gerçek bir arka uca geçirilebilir.

---

## Mevcut Arka Uçlar

### RF

- `simulation`: tohumlanmış sentetik RF okumaları
- `real`: HackRF spektrum yakalama için `hackrf_sweep` komut entegrasyonu

### Ses

- `simulation`: tohumlanmış sentetik akustik okumalar
- `real`: `sounddevice` kullanarak yerel mikrofon yakalama

### Görüntü

- `simulation`: tohumlanmış sentetik görsel izler
- `real`: OpenCV arka plan çıkarımı ve hareket sezgisel yöntemleriyle RTSP IP kamera alımı

---

## Önemli Kapsam Notu

Gerçek arka uçlar, operasyonel veri alım yollarıdır; askerî düzeyde drone sınıflandırıcıları değildir.

- HackRF modu, yapılandırılan bantta yükselmiş RF enerjisini tespit eder
- Mikrofon modu, genlik ve FFT sezgisel yöntemleriyle rotor benzeri ton enerjisini tespit eder
- RTSP modu, hareket segmentasyonu ile hareket eden görsel hedefleri tespit eder

Bunlar gerçek iş akışları ve gerçek cihaz entegrasyonlarıdır; ancak hâlâ sezgisel tespit mantığı kullanırlar. Üretime hazır nihai bir tespit yığını olarak değil, saha testleri ve iterasyon için bir mühendislik tabanı olarak ele alınmalıdır.

---

## Donanım Desteği

- `hackrf_sweep` yüklü ve `PATH` üzerinde olan HackRF
- PortAudio / `sounddevice` tarafından desteklenen dahili veya USB mikrofon
- Ana makineden erişilebilen RTSP IP kamera

---

## Gereksinimler

- Python 3.10+
- RF gerçek modu için HackRF araçları yüklü olmalı
- Mikrofon gerçek modu için PortAudio uyumlu ses girişi
- RTSP gerçek modu için OpenCV uyumlu ortam

Python paketlerini kurun:

```bash
pip install -r requirements.txt
```

---

## Çalıştırma

```bash
python main.py
```

Varsayılan olarak tüm modüller simülasyon modunda çalışır.

---

## Yapılandırma

Her sensör, ortam değişkenleriyle etkinleştirilebilir, devre dışı bırakılabilir veya simülasyon ile gerçek mod arasında değiştirilebilir.

### RF gerçek modu

```bash
DRONEWATCH_RF_SIMULATION=false
DRONEWATCH_RF_BACKEND=real
DRONEWATCH_RF_HACKRF_SWEEP_PATH=hackrf_sweep
DRONEWATCH_RF_START_MHZ=2400
DRONEWATCH_RF_STOP_MHZ=2485
DRONEWATCH_RF_BIN_WIDTH_HZ=1000000
DRONEWATCH_RF_SIGNAL_THRESHOLD_DB=-55
```

### Ses gerçek modu

```bash
DRONEWATCH_AUDIO_SIMULATION=false
DRONEWATCH_AUDIO_BACKEND=real
DRONEWATCH_AUDIO_INPUT_DEVICE=
DRONEWATCH_AUDIO_SAMPLE_RATE=48000
DRONEWATCH_AUDIO_CAPTURE_SECONDS=1.5
DRONEWATCH_AUDIO_AMPLITUDE_THRESHOLD=0.03
DRONEWATCH_AUDIO_BAND_MIN_HZ=120
DRONEWATCH_AUDIO_BAND_MAX_HZ=700
```

Varsayılan dahili mikrofonu kullanmak için `DRONEWATCH_AUDIO_INPUT_DEVICE` değerini boş bırakın.

### Görüntü gerçek modu

```bash
DRONEWATCH_VISION_SIMULATION=false
DRONEWATCH_VISION_BACKEND=real
DRONEWATCH_VISION_RTSP_URL=rtsp://user:password@camera-ip:554/stream
DRONEWATCH_VISION_CAMERA_ID=cam-01
DRONEWATCH_VISION_FRAME_WIDTH=960
DRONEWATCH_VISION_MIN_MOTION_AREA=1400
```

### Karma mod örneği

Bu örnek, sesi simülasyonda bırakırken RF ve görüntüyü gerçek donanımda çalıştırır:

```bash
DRONEWATCH_RF_SIMULATION=false
DRONEWATCH_RF_BACKEND=real
DRONEWATCH_AUDIO_SIMULATION=true
DRONEWATCH_VISION_SIMULATION=false
DRONEWATCH_VISION_BACKEND=real
DRONEWATCH_VISION_RTSP_URL=rtsp://user:password@camera-ip:554/stream
```

---

## Modüller

- `rf/`: RF tarama ve HackRF entegrasyonu
- `audio/`: simülasyon ve canlı mikrofon alımı
- `vision/`: simülasyon ve RTSP kamera alımı
- `core/`: motor, modeller ve yapılandırma
- `api/`: kontrol paneli ve JSON API'leri

---

## Doğrulama Notları

Bir gerçek arka uç başlatılamazsa, modül ayakta kalır ve açıklayıcı bir hata mesajıyla birlikte “tespit yok” okumaları raporlar. Bu sayede kontrol paneli çevrimiçi kalır ve hangi bağımlılığın veya cihazın eksik olduğu görülebilir.

---

## Lisans

MIT Lisansı

