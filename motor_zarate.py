#!/usr/bin/env python3
import json
import re
import pickle
import os
import time
from collections import defaultdict

class MotorZarate:
    def __init__(self, db_path="api_unificado.json", index_path="indice_zarate.pkl"):
        self.db_path = db_path
        self.index_path = index_path
        self.documentos = {}
        self.indice = defaultdict(lambda: defaultdict(int))

    def limpiar_texto(self, texto):
        if not texto: return []
        texto = str(texto).lower()
        texto = texto.replace('á','a').replace('é','e').replace('í','i').replace('ó','o').replace('ú','u')
        texto = re.sub(r'[^a-z0-9\s]', ' ', texto)
        stopwords = {'de', 'la', 'que', 'el', 'en', 'y', 'a', 'los', 'del', 'se', 'las', 'por', 'un', 'para', 'con', 'no', 'una', 'su', 'al', 'es'}
        return [w for w in texto.split() if w not in stopwords and len(w) > 2]

    def extraer_adn(self, doc):
        adn = {"num": None, "anio": doc.get('anio'), "exp": None}
        titulo = str(doc.get('titulo', '')).lower()
        # Captura N° seguido de números
        match_n = re.search(r'(?:n[°º]?\s*)(\d+)', titulo)
        if match_n: adn["num"] = match_n.group(1)
        # Captura ID Exp de la URL
        match_url = re.search(r'id_exp=(\d+)', str(doc.get('url_oficial', '')))
        if match_url: adn["exp"] = match_url.group(1)
        return adn

    def construir_indice(self):
        print(f"⚙️ Procesando {self.db_path}...")
        try:
            with open(self.db_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            print(f"❌ Error: {e}"); return False

        for doc in data:
            doc_id = str(doc.get('id'))
            if not doc_id: continue
            adn = self.extraer_adn(doc)
            self.documentos[doc_id] = {
                "titulo": doc.get('titulo', 'Sin Título'),
                "anio": adn["anio"],
                "num": adn["num"],
                "exp": adn["exp"],
                "tipo": doc.get('tipo', 'Norma')
            }
            # Pesos de búsqueda
            if adn["num"]: self.indice[adn["num"]][doc_id] += 2000
            if adn["exp"]: self.indice[adn["exp"]][doc_id] += 2000
            if adn["anio"]: self.indice[str(adn["anio"])][doc_id] += 500
            
            for p in self.limpiar_texto(doc.get('titulo', '')): self.indice[p][doc_id] += 100
            for p in self.limpiar_texto(doc.get('texto_completo', '')): self.indice[p][doc_id] += 1

        with open(self.index_path, 'wb') as f:
            pickle.dump((self.documentos, dict(self.indice)), f)
        return True

    def cargar(self):
        if not os.path.exists(self.index_path): return self.construir_indice()
        with open(self.index_path, 'rb') as f:
            self.documentos, idx = pickle.load(f)
            self.indice = defaultdict(lambda: defaultdict(int), idx)
        return True

    def buscar(self, query):
        query = query.strip().lower()
        filtro_anio = None
        
        # LÓGICA INTELIGENTE: ¿Es un año o un número de ordenanza?
        if query.isdigit():
            val = int(query)
            if 1980 <= val <= 2030: # Es un año
                filtro_anio = val
                palabras = []
                print(f"📅 Filtrando por Período Legislativo: {val}")
            else: # Es un número de ordenanza (ej: 5338)
                palabras = [query]
        else:
            # Soporte para "año:2026 palabra"
            match_cmd = re.search(r'a[nñ]o:(\d{4})', query)
            if match_cmd:
                filtro_anio = int(match_cmd.group(1))
                query = query.replace(match_cmd.group(0), '')
            palabras = self.limpiar_texto(query)

        scores = defaultdict(int)
        for p in palabras:
            if p in self.indice:
                for d_id, s in self.indice[p].items(): scores[d_id] += s

        res = []
        for d_id, s in scores.items() if palabras else [(id, 500) for id in self.documentos]:
            doc = self.documentos[d_id]
            if filtro_anio and str(doc['anio']) != str(filtro_anio): continue
            res.append({"score": s, "doc": doc})

        res.sort(key=lambda x: (x['score'], int(x['doc']['num'] or 0)), reverse=True)
        return res[:15]

if __name__ == "__main__":
    motor = MotorZarate()
    motor.cargar()
    while True:
        q = input("\n🔍 Buscar en Zárate (o 'salir'): ")
        if q.lower() == 'salir': break
        results = motor.buscar(q)
        if not results: print("❌ Sin resultados."); continue
        for i, r in enumerate(results):
            d = r['doc']
            print(f"{i+1}. [{d['anio']}] {d['tipo']} N° {d['num']} | Exp: {d['exp']}")
            print(f"   {d['titulo'][:90]}...")

