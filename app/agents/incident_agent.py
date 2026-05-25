import os
from pydantic import BaseModel, Field
from google import genai
from google.genai import types
from app.database.vector_store import vector_store
from dotenv import load_dotenv

load_dotenv()

# 1. Mantenemos el esquema estricto de salida
class IncidentReport(BaseModel):
    incident_severity: str = Field(description="Gravedad asignada: CRITICAL, HIGH, MEDIUM o LOW.")
    root_cause_analysis: str = Field(description="Breve análisis de la causa raíz basada en los logs y el playbook.")
    mitigation_steps: list[str] = Field(description="Lista ordenada de pasos inmediatos para resolver la incidencia.")
    requires_escalation: bool = Field(description="True si el problema supera el playbook y requiere llamar a un Senior/SRE.")
    slack_summary: str = Field(description="Un resumen de una sola línea amigable para mandar por canal de alertas de Slack.")

class NativeIncidentAgent:
    def __init__(self):
        # Usamos el cliente oficial que ya tienes instalado y configurado
        self.client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        self.model_name = "gemini-2.5-flash"  # Modelo de chat ultrarrápido y compatible por defecto

    async def run(self, alert_message: str) -> 'AgentResultWrapper':
        """Ejecuta el flujo RAG y genera la respuesta estructurada de forma nativa."""
        print(f"🔍 [RAG] Buscando de forma directa en Qdrant para: '{alert_message}'")
        
        # Hacemos la consulta al motor de vectores que ya tenemos validado
        context_matches = vector_store.search_relevant_playbooks(alert_message, limit=1)
        
        context_text = ""
        if context_matches:
            context_text = f"Playbook Contexto Encontrado:\n{context_matches[0]['text']}"
        else:
            context_text = "No se encontraron playbooks específicos en la base de datos."

        # Construimos el prompt del sistema y usuario juntos
        prompt = (
            f"Eres un Agente de IA experto en Operaciones de Software y SRE de guardia 24x7.\n"
            f"Analiza la siguiente alerta de producción utilizando el contexto del manual provisto.\n\n"
            f"--- CONTEXTO DE PLAYBOOK ---\n{context_text}\n\n"
            f"--- ALERTA RECIBIDA ---\n{alert_message}\n\n"
            f"Genera un reporte estructurado que cumpla estrictamente con el esquema JSON requerido."
        )

        # Llamamos a la API oficial usando 'response_schema' para forzar el JSON estructurado de Pydantic
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=IncidentReport,
                temperature=0.1
            ),
        )

        # Convertimos el string JSON que devuelve Gemini directamente en nuestro objeto Pydantic validado
        structured_data = IncidentReport.model_validate_json(response.text)
        return AgentResultWrapper(structured_data)

class AgentResultWrapper:
    """Wrapper simple para mantener compatibilidad con el formato '.data' de tu archivo de test."""
    def __init__(self, data: IncidentReport):
        self.data = data

# Instanciamos el agente de contingencia
incident_agent = NativeIncidentAgent()