import requests
from bs4 import BeautifulSoup
import json
import time

# Configuración: Vamos a buscar los últimos expedientes (rango 2026)
# El ID 13622 es el de Bomberos, buscamos alrededor de ese número
ID_INICIO = 13500 
ID_FIN = 13650 
ARCHIVO_SALIDA = "datos_2026_nuevos.json"

def extraer_datos_hcd(id_exp):
    url = f"https://www.hcdzarate.gob.ar/popup_concejodeliberante2.php?id_exp={id_exp}"
    try:
        res = requests.get(url, timeout=10)
        res.encoding = 'utf-8'
        if res.status_code != 200: return None
        
        soup = BeautifulSoup(res.text, 'html.parser')
        texto = soup.get_text(separator=' ', strip=True)
        
        # Si el texto es muy corto, probablemente es una página de error o vacía
        if len(texto) < 100: return None
        
        # Intentamos extraer el número de ordenanza del texto
        match_norma = "N/A"
        if "ORDENANZA Nº" in texto:
            idx = texto.find("ORDENANZA Nº")
            match_norma = texto[idx:idx+20].split()[2].replace('.', '')

        return {
            "id": id_exp,
            "tipo": "Ordenanza",
            "anio": 2026,
            "titulo": f"Ordenanza N° {match_norma}",
            "texto_completo": texto,
            "url_oficial": url
        }
    except:
        return None

print(f"🚀 Iniciando captura de datos 2026 (IDs {ID_INICIO} al {ID_FIN})...")
resultados = []

for i in range(ID_INICIO, ID_FIN + 1):
    print(f"⏳ Procesando ID: {i}...", end="\r")
    data = extraer_datos_hcd(i)
    if data:
        resultados.append(data)
    time.sleep(0.5) # Pausa para que el servidor del HCD no nos bloquee

with open(ARCHIVO_SALIDA, "w", encoding="utf-8") as f:
    json.dump(resultados, f, ensure_ascii=False, indent=2)

print(f"\n✅ ¡Listo! Se guardaron {len(resultados)} expedientes nuevos en {ARCHIVO_SALIDA}")

