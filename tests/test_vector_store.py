import os
import sys
import asyncio

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.vector_store import vector_store
from app.agents.incident_agent import incident_agent

async def run_full_pipeline_test():
    print("🚀 Iniciando prueba del pipeline completo (RAG + Agente Inteligente)...")
    
    # 1. Aseguramos la indexación de los playbooks
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    playbook_path = os.path.join(base_dir, "data", "playbooks", "keycloak_errors.md")
    vector_store.index_playbook(playbook_path)
    
    # 2. Definimos una alerta de simulación crítica
    alerta_produccion = "CRITICAL ALERT: Keycloak login failed with AUTH_TIMEOUT_500. Database pool exhausted."
    print(f"\n🚨 Nueva Alerta Recibida: '{alerta_produccion}'")
    print("🧠 Pasando alerta al Agente de PydanticAI (esto invocará la Tool automáticamente)... \n")
    
    # 3. Ejecutamos el agente de forma asíncrona (PydanticAI es nativamente async)
    result = await incident_agent.run(alerta_produccion)
    
    # 4. Mostramos el resultado estructurado final
    report = result.data
    print("\n🎉 ¡Flujo Completado con Éxito! Reporte de IA Estructurado:")
    print("=========================================================")
    print(f"🔴 Gravedad: {report.incident_severity}")
    print(f"🔍 Causa Raíz: {report.root_cause_analysis}")
    print(f"🛠️ Pasos de Mitigación:")
    for idx, step in enumerate(report.mitigation_steps, 1):
        print(f"   {idx}. {step}")
    print(f"📞 ¿Escalar a Senior?: {'SÍ' if report.requires_escalation else 'NO'}")
    print(f"💬 Mensaje para Slack: {report.slack_summary}")
    print("=========================================================")

if __name__ == "__main__":
    # Ejecutamos el bucle asíncrono
    asyncio.run(run_full_pipeline_test())