"""Mapa de emergencias alrededor de cada hotel de hoteles.txt (OpenStreetMap).

Renglon de hoteles.txt:  Ciudad/Carpeta | lat,lng | Nombre del hotel [| telefono del hotel]
Genera en <Ciudad>/<Carpeta>/:
  emergencia.png   mapa limpio: hotel al centro, hospitales (rojo) y farmacias (verde) numerados
  emergencia.json  hospitales y farmacias: numero, tipo, nombre, km, minutos en auto, telefono, direccion, link de Maps
Lo usa la Ficha de emergencia (Apps Script) que llega 3 dias antes de cada viaje.
Solo se genera si la carpeta todavia no tiene emergencia.png (borralo para rehacerlo).
"""
import json
import math
import os
import re
import time

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle
import requests

UA = {"User-Agent": "banco-fotos-college-traveler/1.0 (contacto@collegetraveler.com)"}
OVERPASS = ["https://overpass-api.de/api/interpreter", "https://overpass.kumi.systems/api/interpreter"]
R = 4500                      # radio de busqueda en metros
AZUL, ROJO, VERDE = "#009DE0", "#E5484D", "#12A150"
CALLES = {"motorway": (3.6, "#D3DAE3"), "trunk": (3.2, "#D3DAE3"), "primary": (2.6, "#D9DFE7"),
          "secondary": (2.0, "#DEE4EB"), "tertiary": (1.5, "#E3E8EE")}
NO_SIRVE = re.compile(r"veterinari|dental|dentist|laborator|logistic|distribu|optica|óptica|oftalm|ojos|visi[oó]n|"
                      r"de la luz|psicolog|psiquiatr|spa\b|estetica|estética|nutri|fisioterap|rehabilit|consultorio|"
                      r"cirug[ií]a pl[aá]stica|fertilidad|s\.a\.|s\. de r\.l|de c\.v", re.I)
# Hospitales privados con urgencias 24 h (primera opcion para un grupo de alumnos)
PRIVADOS = re.compile(r"\babc\b|[aá]ngeles|star m[eé]dica|m[eé]dica sur|hospital espa[nñ]ol|san [aá]ngel inn|christus|"
                      r"puerta de hierro|\bhmg\b|hospitales mac|\bmac\b|galenia|san jos[eé]|amerimed|hospital country|"
                      r"real san jos[eé]|m[eé]xico americano|joya|dalinde|santa fe|hospital mig|torre m[eé]dica|"
                      r"sanatorio|hospital privado", re.I)
CRUZ_ROJA = re.compile(r"cruz roja", re.I)
PRIMER_NIVEL = re.compile(r"c\.?\s?m\.?\s?f\b|u\.?\s?m\.?\s?f\b|medicina familiar|centro de salud|dispensario|unidad m[eé]dica", re.I)


def nivel(l):
    """0 = privado con urgencias, 1 = Cruz Roja / urgencias, 2 = hospital general, 3 = clinica, 4 = primer nivel."""
    n = l["nombre"]
    if PRIMER_NIVEL.search(n):
        return 4
    if PRIVADOS.search(n):
        return 0
    if CRUZ_ROJA.search(n) or l["emerg"]:
        return 1
    if l["tipo"] == "hospital":
        return 2
    return 3


def normal(n):
    import unicodedata
    n = unicodedata.normalize("NFD", n.lower())
    return re.sub(r"[^a-z0-9 ]", "", "".join(c for c in n if unicodedata.category(c) != "Mn")).strip()


def log(msg):
    print(msg, flush=True)
    with open("herramientas/registro_mapas.txt", "a", encoding="utf-8") as f:
        f.write(msg + "\n")


def overpass(lat, lng):
    dlat, dlng = R / 110540, R / (111320 * math.cos(math.radians(lat)))
    bbox = f"{lat - dlat},{lng - dlng},{lat + dlat},{lng + dlng}"
    q = f"""[out:json][timeout:120];
(
 way["highway"~"^(motorway|trunk|primary|secondary|tertiary)$"]({bbox});
 nwr["amenity"~"^(hospital|clinic|pharmacy)$"]({bbox});
 nwr["healthcare"~"^(hospital|clinic)$"]({bbox});
);
out geom;"""
    ultimo = None
    for _ in range(3):
        for url in OVERPASS:
            try:
                r = requests.post(url, data={"data": q}, headers=UA, timeout=180)
                r.raise_for_status()
                return r.json()["elements"]
            except Exception as e:
                ultimo = e
                log(f"  overpass {url}: {e}")
        time.sleep(20)
    raise ultimo


def centro(e, xy):
    if e["type"] == "node":
        return xy(e["lat"], e["lon"]), (e["lat"], e["lon"])
    g = e.get("geometry") or []
    if g:
        la = sum(p["lat"] for p in g) / len(g)
        lo = sum(p["lon"] for p in g) / len(g)
        return xy(la, lo), (la, lo)
    b = e.get("bounds")
    if b:
        la, lo = (b["minlat"] + b["maxlat"]) / 2, (b["minlon"] + b["maxlon"]) / 2
        return xy(la, lo), (la, lo)
    return None, None


def direccion(t):
    calle = t.get("addr:street", "")
    num = t.get("addr:housenumber", "")
    col = t.get("addr:suburb") or t.get("addr:neighbourhood") or ""
    d = (calle + (" " + num if num else "")).strip()
    return ", ".join([x for x in (d, col) if x])


def mapa(carpeta, lat, lng, nombre_hotel, tel_hotel):
    els = overpass(lat, lng)
    k = 111320 * math.cos(math.radians(lat))
    xy = lambda la, lo: ((lo - lng) * k, (la - lat) * 110540)
    calles, hosp, farm = [], [], []
    for e in els:
        t = e.get("tags", {})
        if e["type"] == "way" and t.get("highway") in CALLES and e.get("geometry"):
            calles.append((t["highway"], [xy(g["lat"], g["lon"]) for g in e["geometry"]]))
            continue
        tipo = t.get("amenity") or t.get("healthcare")
        if tipo not in ("hospital", "clinic", "pharmacy"):
            continue
        n = (t.get("name") or t.get("brand") or "").strip()
        if not n or NO_SIRVE.search(n):
            continue
        c, ll = centro(e, xy)
        if c is None:
            continue
        (x, y), (la, lo) = c, ll
        d = math.hypot(x, y)
        lugar = {"nombre": n, "x": x, "y": y, "d": d, "lat": la, "lng": lo,
                 "tel": t.get("phone") or t.get("contact:phone") or "",
                 "dir": direccion(t), "24h": "24/7" in (t.get("opening_hours") or ""),
                 "emerg": t.get("emergency") == "yes", "tipo": tipo}
        (farm if tipo == "pharmacy" else hosp).append(lugar)

    def unicos(lista, cupo, clave):
        out, vistos = [], set()
        for l in sorted(lista, key=clave):
            c = normal(l["nombre"])
            if c in vistos:
                continue
            vistos.add(c)
            out.append(l)
            if len(out) == cupo:
                break
        return out

    # Hospitales: primero los que atienden urgencias (hospital > clinica), luego lo mas cercano.
    # Hospitales: el privado con urgencias mas cercano, luego Cruz Roja / hospital general; lo de primer nivel al final.
    hs = unicos([l for l in hosp if l["d"] < 4200], 3, lambda l: (nivel(l), l["d"]))
    hs = sorted(hs, key=lambda l: l["d"])
    # Farmacias: las 2 mas cercanas, y una 24 h si existe a menos de 2 km.
    fs = unicos(farm, 2, lambda l: l["d"])
    f24 = [l for l in unicos([l for l in farm if l["24h"]], 1, lambda l: l["d"]) if l["d"] < 2000]
    if f24 and normal(f24[0]["nombre"]) not in [normal(f["nombre"]) for f in fs]:
        fs = fs[:1] + f24
    elegidos = [dict(l, cat="hospital") for l in hs] + [dict(l, cat="farmacia") for l in fs]
    for i, l in enumerate(elegidos, 1):
        l["n"] = i
        l["km"] = round(l["d"] * 1.35 / 1000, 1)                 # por calle, no en linea recta
        l["min"] = max(2, round(l["d"] * 1.35 / 420))            # auto en ciudad, ~25 km/h

    # Encuadre: lo justo para que quepan todos los puntos, con aire.
    lejos = max([abs(l["x"]) for l in elegidos] + [abs(l["y"]) * 1.6 for l in elegidos] + [700])
    DX = min(R, lejos * 1.28 + 250)
    DY = DX / 1.6
    fig = plt.figure(figsize=(10, 6.25), dpi=170)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(-DX, DX)
    ax.set_ylim(-DY, DY)
    ax.set_aspect("equal")
    ax.axis("off")
    fig.patch.set_facecolor("#FFFFFF")
    for h, g in sorted(calles, key=lambda c: CALLES[c[0]][0]):
        w, col = CALLES[h]
        ax.plot([p[0] for p in g], [p[1] for p in g], color=col, lw=w, zorder=2, solid_capstyle="round")
    esc = DX / 600
    puestos = [(0.0, 0.0, 46 * esc)]
    for l in elegidos:
        for _ in range(12):
            choca = [p for p in puestos if math.hypot(l["x"] - p[0], l["y"] - p[1]) < (30 * esc + p[2]) * 1.05]
            if not choca:
                break
            p = choca[0]
            dx, dy = l["x"] - p[0], l["y"] - p[1]
            dd = math.hypot(dx, dy) or 1.0
            l["x"] += dx / dd * 18 * esc
            l["y"] += dy / dd * 18 * esc
        puestos.append((l["x"], l["y"], 30 * esc))
    for l in elegidos:
        col = ROJO if l["cat"] == "hospital" else VERDE
        ax.add_patch(Circle((l["x"], l["y"]), 30 * esc, color=col, ec="white", lw=2.5, zorder=6))
        ax.text(l["x"], l["y"], str(l["n"]), ha="center", va="center", fontsize=11, fontweight="bold",
                color="white", zorder=7)
    ax.add_patch(Circle((0, 0), 46 * esc, color=AZUL, ec="white", lw=4, zorder=8))
    ax.text(0, 0, "H", ha="center", va="center", fontsize=16, fontweight="bold", color="white", zorder=9)
    # Escala
    paso = 500 if DX < 1500 else 1000
    x0, y0 = -DX + 40 * esc, -DY + 40 * esc
    ax.plot([x0, x0 + paso], [y0, y0], color="#8A93A1", lw=1.5, zorder=9)
    ax.text(x0 + paso / 2, y0 + 12 * esc, f"{paso if paso < 1000 else paso // 1000}{' m' if paso < 1000 else ' km'}",
            ha="center", va="bottom", fontsize=8, color="#8A93A1", zorder=9)
    ax.text(DX - 14 * esc, -DY + 12 * esc, "© OpenStreetMap contributors", ha="right", va="bottom", fontsize=7,
            color="#A0AAB6", zorder=9)
    fig.savefig(os.path.join(carpeta, "emergencia.png"), facecolor="white")
    plt.close(fig)
    salida = {"hotel": nombre_hotel, "tel_hotel": tel_hotel, "lat": lat, "lng": lng, "generado": time.strftime("%Y-%m-%d"),
              "lugares": [{"n": l["n"], "cat": l["cat"], "nombre": l["nombre"], "km": l["km"], "min": l["min"],
                           "tel": l["tel"], "dir": l["dir"], "24h": l["24h"],
                           "maps": f"https://www.google.com/maps/dir/?api=1&origin={lat},{lng}&destination={l['lat']:.6f},{l['lng']:.6f}"}
                          for l in elegidos]}
    json.dump(salida, open(os.path.join(carpeta, "emergencia.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    log(f"{carpeta}: emergencia {len(hs)} hospitales, {len(fs)} farmacias")


def main():
    if not os.path.exists("hoteles.txt"):
        return
    for linea in open("hoteles.txt", encoding="utf-8"):
        linea = linea.strip()
        if not linea or linea.startswith("#") or linea.count("|") < 2:
            continue
        partes = [x.strip() for x in linea.split("|")]
        carpeta, coords, nom = partes[:3]
        tel = partes[3] if len(partes) > 3 else ""
        if os.path.exists(os.path.join(carpeta, "emergencia.png")):
            continue
        os.makedirs(carpeta, exist_ok=True)
        lat, lng = [float(v) for v in coords.split(",")]
        try:
            mapa(carpeta, lat, lng, nom, tel)
        except Exception as e:
            log(f"ERROR emergencia en {carpeta}: {e}")


if __name__ == "__main__":
    main()
