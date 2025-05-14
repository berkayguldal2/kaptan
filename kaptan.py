#!/usr/bin/env python3
import argparse
import json
import os
import zipfile
import requests
from tqdm import tqdm

SÜRÜM = "Kaptan 3"
DEPO_URL = "https://raw.githubusercontent.com/berkayguldal2/kaptan/main/paketler"
KAPTAN_KLASÖRÜ = "kaptan"

def kaptan_dizini_oluştur():
    os.makedirs(KAPTAN_KLASÖRÜ, exist_ok=True)

def kaptan_dosya_yolu(dosya_adı):
    return os.path.join(KAPTAN_KLASÖRÜ, dosya_adı)

def dosya_indir(url, hedef_dosya):
    try:
        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            toplam_boyut = int(r.headers.get('content-length', 0))
            with open(hedef_dosya, 'wb') as f, tqdm(
                desc=os.path.basename(hedef_dosya),
                total=toplam_boyut,
                unit='B',
                unit_scale=True,
                unit_divisor=1024,
            ) as bar:
                for veri in r.iter_content(chunk_size=8192):
                    f.write(veri)
                    bar.update(len(veri))
        return True
    except Exception as e:
        print(f"{url} indirilemedi: {e}")
        return False

def json_ve_zipi_getir(paket_adı):
    json_dosya = kaptan_dosya_yolu(f"ikametgah-{paket_adı}.json")
    zip_dosya = kaptan_dosya_yolu(f"{paket_adı}.zip")

    if os.path.exists(json_dosya) and os.path.exists(zip_dosya):
        print(f"Önbellekten yüklenecek: {paket_adı}")
        return json_dosya, zip_dosya

    print(f"{paket_adı} internetten indiriliyor...")
    json_url = f"{DEPO_URL}/ikametgah-{paket_adı}.json"
    zip_url = f"{DEPO_URL}/{paket_adı}.zip"

    if not dosya_indir(json_url, json_dosya):
        return None, None
    if not dosya_indir(zip_url, zip_dosya):
        return None, None

    return json_dosya, zip_dosya

def paket_yükle(paket_adı):
    json_dosya, zip_dosya = json_ve_zipi_getir(paket_adı)
    if not json_dosya or not zip_dosya:
        print("Paket yüklenemedi.")
        return

    with open(json_dosya, "r", encoding="utf-8") as f:
        veri = json.load(f)

    print(f"ZIP açılıyor: {zip_dosya}")
    with zipfile.ZipFile(zip_dosya, 'r') as zip_ref:
        for kaynak, hedef in veri.get("dosyalar", {}).items():
            try:
                içerik = zip_ref.read(kaynak)
                os.makedirs(os.path.dirname(hedef), exist_ok=True)
                with open(hedef, 'wb') as hedef_dosya:
                    hedef_dosya.write(içerik)
                print(f"{kaynak} → {hedef}")
            except KeyError:
                print(f"{kaynak} ZIP içinde bulunamadı.")
            except Exception as e:
                print(f"{hedef} yazılamadı: {e}")

def paket_sil(paket_adı):
    json_dosya, _ = json_ve_zipi_getir(paket_adı)
    if not json_dosya:
        print("Paket silinemedi.")
        return

    with open(json_dosya, "r", encoding="utf-8") as f:
        veri = json.load(f)

    for _, hedef in veri.get("dosyalar", {}).items():
        try:
            if os.path.exists(hedef):
                os.remove(hedef)
                print(f"Silindi: {hedef}")
            else:
                print(f"Zaten yok: {hedef}")
        except Exception as e:
            print(f"{hedef} silinemedi: {e}")

def sürüm_göster():
    print(SÜRÜM)

def paketleri_listele():
    liste_yolu = kaptan_dosya_yolu("paketler.txt")
    if not os.path.exists(liste_yolu):
        print("[HATA] 'kaptan/paketler.txt' bulunamadı.")
        return

    print("Kullanılabilir Paketler:")
    with open(liste_yolu, "r", encoding="utf-8") as f:
        for satır in f:
            satır = satır.strip()
            if ":" in satır:
                ad, açıklama = satır.split(":", 1)
                print(f"• {ad.strip()} → {açıklama.strip()}")

def main():
    kaptan_dizini_oluştur()

    parser = argparse.ArgumentParser(description="Kaptan Paket Yöneticisi")
    parser.add_argument("-y", metavar="paket", help="Paket yükler")
    parser.add_argument("-s", metavar="paket", help="Paket siler")
    parser.add_argument("-v", action="store_true", help="Sürüm bilgisi gösterir")
    parser.add_argument("-l", action="store_true", help="Paket listesini gösterir")

    args = parser.parse_args()

    if args.y:
        paket_yükle(args.y)
    elif args.s:
        paket_sil(args.s)
    elif args.v:
        sürüm_göster()
    elif args.l:
        paketleri_listele()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
