#!/usr/bin/env python3
import requests
import json
import re
import time
import sys
import argparse
from pathlib import Path
from datetime import datetime, timezone
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed

CFG = {
    "id_inicio": 11000,
    "id_fin": 14000,
    "url_base": "https://www.hcdzarate.gob.ar/popup_concejodeliberante2.php?id_exp={id}",
    "workers": 3,
    "delay_seg": 0.5,
    "archivo_db": "db_zet_hcd.json",
}

KW_SUELO = ["excepción", "excepcion", "exceptúase", "exceptuase", "código", "suelo", "zonificación", "fos", "fot", "loteo"]

def limpiar(texto):
    return re.sub(r'\s+', ' ', texto.strip()) if texto else ""

def parsear_hcd(html, id_exp):
    soup = BeautifulSoup(html, "html.parser")
    # Buscamos todo el texto del body para no errarle a la celda
    texto_full = limpiar(soup.get_text(separator=" ", strip=True))
    
    if len(texto_full) < 50 or "no se encontró" in texto_full.lower():
        return None

    tipo_match = re.search(r'(Ordenanza|Decreto|Resolución|Comunicación)\s+Nro?\.?\s*([\d\.]+)', texto_full, re.I)
    
    return {
        "id_exp": id_exp,
        "tipo": tipo_match.group(1) if tipo_match else "Norma",
        "numero": tipo_match.group(2) if tipo_match else "S/N",
        "asunto": texto_full[:400] + "...",
        "es_suelo": any(k in texto_full.lower() for k in KW_SUELO),
        "url_hcd": CFG["url_base"].format(id=id_exp),
        "scraped_at": datetime.now(timezone.utc).isoformat()
    }

def procesar_id(id_exp, session):
    try:
        time.sleep(CFG["delay_seg"])
        resp = session.get(CFG["url_base"].format(id=id_exp), timeout=10)
        if resp.status_code == 200:
            html = resp.content.decode("iso-8859-1", errors="replace")
            return parsear_hcd(html, id_exp)
    except: pass
    return None

def main():
    db_path = Path(CFG["archivo_db"])
    db = []
    if db_path.exists():
        with open(db_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            db = data.get("normas", []) if isinstance(data, dict) else data

    ya_procesados = {n["id_exp"] for n in db}
    pendientes = [i for i in range(CFG["id_inicio"], CFG["id_fin"]) if i not in ya_procesados]

    print(f"🚀 ZET Motor iniciado. Pendientes: {len(pendientes)}")
    
    with requests.Session() as session:
        with ThreadPoolExecutor(max_workers=CFG["workers"]) as executor:
            futures = {executor.submit(procesar_id, idx, session): idx for idx in pendientes}
            for i, future in enumerate(as_completed(futures)):
                res = future.result()
                if res:
                    db.append(res)
                    print(f"✅ Encontrado: ID {res['id_exp']} - {res['tipo']} {res['numero']}")
                
                if (i + 1) % 20 == 0:
                    with open(db_path, "w", encoding="utf-8") as f:
                        json.dump({"normas": db}, f, ensure_ascii=False, indent=2)
                    print(f"[*] Guardado. Total en DB: {len(db)}")

if __name__ == "__main__":
    main()
