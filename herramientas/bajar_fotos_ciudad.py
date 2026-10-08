"""Baja 4 fotos horizontales de cada ciudad de ciudades.txt que todavia no
tenga fotos en <Carpeta>/Destino. Fuente: Pexels (si hay PEXELS_API_KEY,
fotos libres de uso comercial sin atribucion obligatoria); si no, Openverse
(solo licencias CC0 y dominio publico). Guarda 1.jpg..4.jpg de 1600 px de
ancho y CREDITOS.txt con autor y fuente de cada foto."""
import io
import os
import sys

import requests
from PIL import Image

UA = {"User-Agent": "banco-fotos-college-traveler/1.0"}
ANCHO = 1600


def pexels(q, key):
    r = requests.get("https://api.pexels.com/v1/search", headers={"Authorization": key, **UA},
                     params={"query": q, "orientation": "landscape", "size": "large", "per_page": 15}, timeout=30)
    r.raise_for_status()
    for p in r.json().get("photos", []):
        yield p["src"]["large2x"], f'{p["photographer"]} (Pexels) {p["url"]}'


def openverse(q):
    r = requests.get("https://api.openverse.org/v1/images/", headers=UA,
                     params={"q": q, "license": "cc0,pdm", "aspect_ratio": "wide", "size": "large",
                             "page_size": 20, "mature": "false"}, timeout=30)
    r.raise_for_status()
    for p in r.json().get("results", []):
        yield p["url"], f'{p.get("creator") or "autor desconocido"} ({p.get("license", "").upper()}) {p.get("foreign_landing_url", "")}'


def guardar(url, ruta):
    r = requests.get(url, headers=UA, timeout=60)
    r.raise_for_status()
    im = Image.open(io.BytesIO(r.content)).convert("RGB")
    if im.width < 1200 or im.width < im.height * 1.2:
        return False
    if im.width > ANCHO:
        im = im.resize((ANCHO, round(im.height * ANCHO / im.width)), Image.LANCZOS)
    im.save(ruta, "JPEG", quality=85, optimize=True)
    return True


def main():
    key = os.environ.get("PEXELS_API_KEY", "").strip()
    errores = 0
    for linea in open("ciudades.txt", encoding="utf-8"):
        linea = linea.strip()
        if not linea or linea.startswith("#") or "|" not in linea:
            continue
        carpeta, q = [x.strip() for x in linea.split("|", 1)]
        destino = os.path.join(carpeta, "Destino")
        if os.path.isdir(destino) and any(f.lower().endswith((".jpg", ".jpeg", ".png")) for f in os.listdir(destino)):
            continue
        os.makedirs(destino, exist_ok=True)
        fuente = pexels(q, key) if key else openverse(q)
        creditos, n = [], 0
        try:
            for url, credito in fuente:
                if n == 4:
                    break
                try:
                    if guardar(url, os.path.join(destino, f"{n + 1}.jpg")):
                        n += 1
                        creditos.append(f"{n}.jpg: {credito}")
                except Exception as e:  # una foto rota no detiene la ciudad
                    print(f"  saltada: {e}")
        except Exception as e:
            print(f"ERROR en {carpeta}: {e}")
            errores += 1
        if creditos:
            open(os.path.join(destino, "CREDITOS.txt"), "w", encoding="utf-8").write("\n".join(creditos) + "\n")
        print(f"{carpeta}: {n} fotos")
    sys.exit(1 if errores else 0)


if __name__ == "__main__":
    main()
