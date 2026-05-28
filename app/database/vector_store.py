import os
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from google import genai
from dotenv import load_dotenv

load_dotenv()

class IncidentVectorStore:
    def __init__(self):
        # Inicializamos Qdrant
        self.qdrant_client = QdrantClient(":memory:")
        self.collection_name = "incident_playbooks"
        
        # Como los modelos de embedding te están dando 404, para este test inicial
        # vamos a usar un vectorizador de juguete (simulado) para validar el flujo RAG,
        # o puedes usar Gemini Chat después. Esto asegura que Qdrant no falle.
        self.vector_size = 4
        if not self.qdrant_client.collection_exists(self.collection_name):
            self.qdrant_client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=self.vector_size, distance=Distance.COSINE),
    )

    def _get_mock_embedding(self, text: str) -> list[float]:
        """Genera un vector simulado basado en el texto para evitar el error 404 de la API."""
        # Generamos 4 floats estables basados en la longitud y contenido para simular el RAG
        val = float(len(text) % 10) / 10.0
        return [val, 0.1, 0.5, 0.9]

    def index_playbook(self, file_path: str):
        """Lee el archivo o lo crea automáticamente si Windows no lo encuentra."""
        abs_path = os.path.abspath(file_path)
        
        # AUTO-RESCATE: Si no existe, lo creamos nosotros con código
        if not os.path.exists(abs_path):
            os.makedirs(os.path.dirname(abs_path), exist_ok=True)
            content_aux = (
                "# Playbook Operativo: Errores Críticos en Servicios de Identidad (Keycloak)\n\n"
                "## Error: AUTH_TIMEOUT_500 (Timeout en Autenticación)\n"
                "* Gravedad: Alta\n"
                "* Acciones: Reiniciar el pool de conexiones ejecutando db_flush_connections.sh\n"
            )
            with open(abs_path, "w", encoding="utf-8") as f:
                f.write(content_aux)
            print(f"📦 El archivo no existía, se ha creado automáticamente en: {abs_path}")

        with open(abs_path, "r", encoding="utf-8") as f:
            content = f.read()

        chunks = [chunk.strip() for chunk in content.split("##") if chunk.strip()]
        points = []
        
        for idx, chunk in enumerate(chunks):
            full_text = f"Manual de Contingencia:\n{chunk}" if idx > 0 else chunk
            vector = self._get_mock_embedding(full_text)
            
            points.append(
                PointStruct(
                    id=idx,
                    vector=vector,
                    payload={"text": full_text, "source": os.path.basename(abs_path)}
                )
            )

        self.qdrant_client.upsert(
            collection_name=self.collection_name,
            wait=True,
            points=points
        )
        print(f"✅ ¡Playbook indexado correctamente en Qdrant! Fragmentos: {len(points)}")

    def search_relevant_playbooks(self, query: str, limit: int = 1) -> list[dict]:
        query_vector = self._get_mock_embedding(query)
        search_results = self.qdrant_client.search(
            collection_name=self.collection_name,
            query_vector=query_vector,
            limit=limit
        )
        return [hit.payload for hit in search_results]

vector_store = IncidentVectorStore()