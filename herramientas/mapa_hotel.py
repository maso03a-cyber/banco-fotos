"""Mapa de alrededores de cada hotel de hoteles.txt (OpenStreetMap).

Renglon de hoteles.txt:  Ciudad/Carpeta | lat,lng | Nombre del hotel
Genera en <Ciudad>/<Carpeta>/:
  mapa.png   calles en gris, parques, el hotel al centro y lugares numerados
  mapa.json  lista de esos lugares: numero, categoria, nombre, minutos a pie
Solo se genera si la carpeta todavia no tiene mapa.png (borralo para rehacerlo).
"""
import json
import math
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Polygon
import requests

UA = {"User-Agent": "banco-fotos-college-traveler/1.0 (contacto@collegetraveler.com)"}
OVERPASS = ["https://overpass-api.de/api/interpreter", "https://overpass.kumi.systems/api/interpreter"]
DX, DY = 950, 594          # medio ancho y medio alto del mapa en metros (proporcion 16:10)
CATS = {
    "salud":   {"color": "#12A150", "max": 3, "titulo": "Farmacias y salud"},
    "tiendas": {"color": "#E8A317", "max": 3, "titulo": "Tiendas"},
    "comida":  {"color": "#E0533D", "max": 3, "titulo": "Para comer"},
    "plazas":  {"color": "#7A5CD6", "max": 2, "titulo": "Plazas comerciales"},
}
CALLES = {
    "motorway": (5.0, "#C9D3DF"), "trunk": (4.5, "#C9D3DF"), "primary": (3.8, "#CFD8E3"),
    "secondary": (3.0, "#D6DEE8"), "tertiary": (2.4, "#DCE3EC"),
}


def categoria(t):
    a, s = t.get("amenity", ""), t.get("shop", "")
    if a in ("pharmacy", "hospital", "clinic"):
        return "salud"
    if s in ("convenience", "supermarket"):
        return "tiendas"
    if a in ("restaurant", "fast_food", "cafe"):
        return "comida"
    if s in ("mall", "department_store") or a == "marketplace":
        return "plazas"
    return None


def nombre(t):
    n = t.get("name") or t.get("brand") or ""
    return n.strip()


def overpass(lat, lng):
    dlat, dlng = DY / 110540, DX / (111320 * math.cos(math.radians(lat)))
    bbox = f"{lat - dlat},{lng - dlng},{lat + dlat},{lng + dlng}"
    q = f"""[out:json][timeout:90];
(
 way["highway"~"^(motorway|trunk|primary|secondary|tertiary|residential|unclassified|living_street|pedestrian|service)$"]({bbox});
 way["leisure"="park"]({bbox});
 nwr["amenity"~"^(pharmacy|hospital|clinic|restaurant|fast_food|cafe|marketplace)$"]({bbox});
 nwr["shop"~"^(convenience|supermarket|mall|department_store)$"]({bbox});
);
out geom;"""
    ultimo = None
    for url in OVERPASS:
        try:
            r = requests.post(url, data={"data": q}, headers=UA, timeout=120)
            r.raise_for_status()
            return r.json()["elements"]
        except Exception as e:
            ultimo = e
    raise ultimo


def a_metros(lat0, lng0):
    k = 111320 * math.cos(math.radians(lat0))
    return lambda la, lo: ((lo - lng0) * k, (la - lat0) * 110540)


def mapa(carpeta, lat, lng, nombre_hotel):
    els = overpass(lat, lng)
    xy = a_metros(lat, lng)
    calles, parques, lugares = [], [], []
    for e in els:
        t = e.get("tags", {})
        geom = [xy(g["lat"], g["lon"]) for g in e.get("geometry", [])]
        if e["type"] == "way" and "highway" in t and geom:
            calles.append((t["highway"], geom))
        elif e["type"] == "way" and t.get("leisure") == "park" and len(geom) > 2:
            parques.append(geom)
        c = categoria(t)
        if c:
            if e["type"] == "node":
                x, y = xy(e["lat"], e["lon"])
            elif geom:
                x, y = sum(p[0] for p in geom) / len(geom), sum(p[1] for p in geom) / len(geom)
            else:
                continue
            n = nombre(t)
            if not n:
                continue
            if abs(x) > DX * 0.94 or abs(y) > DY * 0.92:
                continue
            sub = t.get("amenity") or t.get("shop")
            lugares.append({"cat": c, "sub": sub, "nombre": n, "x": x, "y": y, "d": math.hypot(x, y)})

    # Lo mas cercano de cada tipo, sin repetir nombre. Orden de preferencia:
    # 2 farmacias + 1 hospital; 2 tiendas de conveniencia (OXXO, 7-Eleven) +
    # 1 supermercado; 3 lugares para comer; 2 plazas.
    cupos = [("salud", ("pharmacy",), 2), ("salud", ("hospital", "clinic"), 1),
             ("tiendas", ("convenience",), 2), ("tiendas", ("supermarket",), 1),
             ("comida", ("restaurant", "fast_food", "cafe"), 3),
             ("plazas", ("mall", "department_store", "marketplace"), 2)]
    elegidos, vistos = [], set()
    for cat, subs, cupo in cupos:
        k = 0
        for l in sorted([l for l in lugares if l["cat"] == cat and l["sub"] in subs], key=lambda l: l["d"]):
            clave = l["nombre"].lower()
            if clave in vistos:
                continue
            vistos.add(clave)
            elegidos.append(l)
            k += 1
            if k == cupo:
                break
    for i, l in enumerate(elegidos, 1):
        l["n"] = i
        l["min"] = max(1, round(l["d"] * 1.3 / 80))     # caminando, 80 m/min, calles no rectas

    fig = plt.figure(figsize=(16, 10), dpi=100)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(-DX, DX)
    ax.set_ylim(-DY, DY)
    ax.set_aspect("equal")
    ax.axis("off")
    fig.patch.set_facecolor("#FFFFFF")
    for g in parques:
        ax.add_patch(Polygon(g, closed=True, facecolor="#E9F3E6", edgecolor="none", zorder=1))
    menores = [(h, g) for h, g in calles if h not in CALLES]
    for h, g in menores:
        ax.plot([p[0] for p in g], [p[1] for p in g], color="#E6EBF1", lw=1.6, zorder=2, solid_capstyle="round")
    for h, g in sorted([(h, g) for h, g in calles if h in CALLES], key=lambda x: CALLES[x[0]][0]):
        w, col = CALLES[h]
        ax.plot([p[0] for p in g], [p[1] for p in g], color=col, lw=w, zorder=3, solid_capstyle="round")
    ax.add_patch(Circle((0, 0), 500, fill=False, ls=(0, (4, 4)), lw=1.2, ec="#9DB4C8", zorder=4))
    ax.text(0, 512, "8 min caminando", ha="center", va="bottom", fontsize=11, color="#7C93A8", zorder=4)
    for l in elegidos:
        col = CATS[l["cat"]]["color"]
        ax.add_patch(Circle((l["x"], l["y"]), 30, color=col, ec="white", lw=2.5, zorder=6))
        ax.text(l["x"], l["y"], str(l["n"]), ha="center", va="center", fontsize=12.5, fontweight="bold",
                color="white", zorder=7)
    ax.add_patch(Circle((0, 0), 48, color="#009DE0", ec="white", lw=4, zorder=8))
    ax.text(0, 0, "H", ha="center", va="center", fontsize=19, fontweight="bold", color="white", zorder=9)
    ax.text(DX - 14, -DY + 12, "© OpenStreetMap contributors", ha="right", va="bottom", fontsize=9,
            color="#94A3B8", zorder=9)
    fig.savefig(os.path.join(carpeta, "mapa.png"), facecolor="white")
    plt.close(fig)
    salida = {"hotel": nombre_hotel, "lat": lat, "lng": lng,
              "categorias": {c: {"titulo": v["titulo"], "color": v["color"]} for c, v in CATS.items()},
              "lugares": [{k: l[k] for k in ("n", "cat", "nombre", "min")} for l in elegidos]}
    json.dump(salida, open(os.path.join(carpeta, "mapa.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"{carpeta}: {len(elegidos)} lugares", flush=True)


def main():
    if not os.path.exists("hoteles.txt"):
        return
    for linea in open("hoteles.txt", encoding="utf-8"):
        linea = linea.strip()
        if not linea or linea.startswith("#") or linea.count("|") < 2:
            continue
        carpeta, coords, nom = [x.strip() for x in linea.split("|", 2)]
        if os.path.exists(os.path.join(carpeta, "mapa.png")):
            continue
        os.makedirs(carpeta, exist_ok=True)
        lat, lng = [float(v) for v in coords.split(",")]
        try:
            mapa(carpeta, lat, lng, nom)
        except Exception as e:
            print(f"ERROR en {carpeta}: {e}", flush=True)


if __name__ == "__main__":
    main()
