#!/usr/bin/env python3
import json
import re
from pathlib import Path
from datetime import datetime

class AuditorSuelo:
    def __init__(self, input_db):
        self.input_db = input_db
        # Diccionario de pesos para el "Índice de Impacto Territorial"
        self.sensores = {
            "CONVENIOS": ["convenio urbanístico", "convenio de gestión", "acuerdo urbanístico", "donación de tierra"],
            "USO_SUELO": ["cambio de zonificación", "uso no permitido", "re-zonificación", "indicadores urbanísticos", "fos", "fot"],
            "8912_PROVINCIAL": ["8912/77", "8912", "convalidación provincial", "decreto 27/98", "mantenimiento de zona"],
            "URBANIZACIONES": ["loteo", "barrio cerrado", "club de campo", "subdivisión", "mensura y división"],
            "EXCEPCIONES": ["excepción", "exceptúase", "transgresión al código", "fuera de norma"]
        }

    def auditar(self):
        if not Path(self.input_db).exists():
            print("❌ No se encontró la base de datos.")
            return

        with open(self.input_db, 'r', encoding='utf-8') as f:
            data = json.load(f)
            normas = data.get('normas', [])

        auditoria = []
        for n in normas:
            texto = n['asunto'].lower()
            hallazgos = {}
            score = 0
            
            for cat, keywords in self.sensores.items():
                matches = [k for k in keywords if k in texto]
                if matches:
                    hallazgos[cat] = matches
                    score += len(matches) * 2 # Peso por cada match
            
            if score > 0:
                # Si menciona el código de planeamiento (3125) y una excepción, sube el score
                if "3125" in texto and "excepción" in texto:
                    score += 10
                
                n['auditoria_suelo'] = {
                    "score": score,
                    "alertas": hallazgos,
                    "requiere_convalidacion": "8912" in texto or "convenio" in texto
                }
                auditoria.append(n)

        # Ordenar por nivel de criticidad (Score más alto primero)
        auditoria.sort(key=lambda x: x['auditoria_suelo']['score'], reverse=True)

        resultado = {
            "meta": {
                "total_analizado": len(normas),
                "hallazgos_suelo": len(auditoria),
                "fecha_auditoria": datetime.now().isoformat()
            },
            "normas_criticas": auditoria
        }

        with open('db_suelo_auditoria.json', 'w', encoding='utf-8') as f:
            json.dump(resultado, f, ensure_ascii=False, indent=2)
        
        print(f"✅ Auditoría completada. Se detectaron {len(auditoria)} normas con impacto en suelo.")
        print("📁 Resultados en: db_suelo_auditoria.json")

if __name__ == "__main__":
    auditor = AuditorSuelo('db_zet_hcd.json')
    auditor.auditar()
