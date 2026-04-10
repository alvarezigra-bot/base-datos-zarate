import os
import json

def generar():
    path_leyes = 'api_leyes'
    output_file = 'base_ligera.json'
    
    if not os.path.exists(path_leyes):
        print(f"Error: No se encuentra la carpeta {path_leyes}")
        return

    archivos = [f for f in os.listdir(path_leyes) if f.endswith('.json')]
    total = len(archivos)
    
    # Estructura básica del índice
    indice = {
        "total_normativas": total,
        "ultima_actualizacion": "2026-04-10",
        "clasificacion": {
            "Ordenanza": 0,
            "Decreto": 0,
            "Resolucion": 0,
            "Comunicacion": 0,
            "Otros": 0
        },
        "normativas": []
    }

    print(f"Procesando {total} archivos...")

    for nombre_archivo in archivos:
        with open(os.path.join(path_leyes, nombre_archivo), 'r') as f:
            try:
                data = json.load(f)
                tipo = data.get('tipo', 'Otros')
                if tipo in indice['clasificacion']:
                    indice['clasificacion'][tipo] += 1
                else:
                    indice['clasificacion']['Otros'] += 1
                
                # Agregamos data mínima para el listado rápido
                indice['normativas'].append({
                    "id": data.get('id'),
                    "tipo": tipo,
                    "anio": data.get('anio'),
                    "titulo": data.get('titulo', 'Sin título')[:100]
                })
            except:
                continue

    # Ordenar por año descendente
    indice['normativas'].sort(key=lambda x: str(x.get('anio', '0')), reverse=True)

    with open(output_file, 'w') as f:
        json.dump(indice, f, indent=4)
    
    print(f"Éxito: {output_file} generado con {total} registros.")

if __name__ == "__main__":
    generar()
