import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field
from app.core.config import settings
from app.database.vector_store import vector_store
from app.agents.incident_agent import incident_agent, IncidentReport
from app.notifications.slack import slack_notifier
import uvicorn

# 1. Definimos el ciclo de vida (Lifespan) para indexar el manual al arrancar
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🎬 Inicializando sistemas y cargando playbooks en Qdrant...")
    base_dir = os.path.dirname(os.path.abspath(__file__))
    playbook_path = os.path.join(base_dir, "data", "playbooks", "keycloak_errors.md")
    vector_store.index_playbook(playbook_path)
    yield
    print("🛑 Apagando servidor de incidencias...")

# 2. Inicializamos la aplicación FastAPI expuesta de forma global
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="API Enterprise para la ingesta automatizada de alertas y triaje mediante agentes de IA.",
    lifespan=lifespan
)

# 3. Definimos el esquema del Webhook o JSON de entrada
class IncomingAlert(BaseModel):
    alert_id: str
    source_service: str
    raw_message: str
    environment: str

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "alert_id": "ALR-2026-992",
                    "source_service": "Keycloak-Identity-Provider",
                    "raw_message": "CRITICAL: Authentication failed with AUTH_TIMEOUT_500. Database pool exhausted.",
                    "environment": "production",
                }
            ]
        }
    }

@app.get("/", tags=["Health Check"])
def read_root():
    """Endpoint básico para comprobar que el microservicio está vivo."""
    return {"status": "online", "service": settings.PROJECT_NAME, "version": settings.VERSION}

@app.post(
    f"{settings.API_V1_STR}/alerts",
    response_model=IncidentReport,
    status_code=status.HTTP_200_OK,
    tags=["Incident Response"]
)
async def process_incoming_alert(alert: IncomingAlert):
    """
    Endpoint crítico: Ingiere una alerta de producción, invoca al agente autónomo
    para que realice el triaje usando RAG sobre Qdrant y devuelve el reporte estructurado.
    Si requires_escalation es True, envía automáticamente una notificación a Slack.
    """
    try:
        agent_input = (
            f"Alerta ID: {alert.alert_id}\n"
            f"Servicio Afectado: {alert.source_service}\n"
            f"Entorno: {alert.environment}\n"
            f"Mensaje de Error: {alert.raw_message}"
        )

        agent_result = await incident_agent.run(agent_input)
        report = agent_result.data

        # Send Slack notification if escalation is required  ← NUEVO
        if report.requires_escalation:                       # ← NUEVO
            slack_notifier.send_incident_alert(              # ← NUEVO
                report=report,
                alert_id=alert.alert_id,
                source_service=alert.source_service,
                environment=alert.environment,
            )

        return report
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error en el procesamiento del agente de IA: {str(e)}"
        )

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)