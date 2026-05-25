import os
from app.database.vector_store import vector_store

def run_test():
    print("🚀 Iniciando prueba del motor de vectores...")
    
    # 1. Definimos la ruta del playbook de Keycloak que creamos en la Fase 1
    playbook_path = os.path.join("data", "playbooks", "keycloak_errors.md")
    
    # 2. Intentamos indexar el manual en nuestra base de datos Qdrant en memoria
    print("\n--- Paso 1: Indexando Playbook ---")
    vector_store.index_playbook(playbook_path)
    
    # 3. Simulamos una consulta de una alerta real
    print("\n--- Paso 2: Buscando solución conceptual (RAG) ---")
    alerta_simulada = "Alerta crítica: El flujo de login está caído y da un código de estado 500 en la base de datos"
    print(f"Consulta simulada: '{alerta_simulada}'\n")
    
    resultados = vector_store.search_relevant_playbooks(alerta_simulada, limit=1)
    
    # 4. Mostramos los resultados obtenidos
    if resultados:
        print("🎉 ¡ÉXITO! Qdrant ha recuperado el contexto correcto:")
        print(f"📄 Origen: {resultados[0]['source']}")
        print(f"📝 Contenido recuperado:\n\n{resultados[0]['text']}")
    else:
        print("❌ Error: No se ha recuperado ningún fragmento relevante.")

if __name__ == "__main__":
    run_test()