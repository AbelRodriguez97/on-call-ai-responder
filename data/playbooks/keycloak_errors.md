# Playbook Operativo: Errores Críticos en Servicios de Identidad (Keycloak)

## Error: AUTH_TIMEOUT_500 (Timeout en Autenticación)
* **Gravedad:** Alta
* **Impacto:** Los usuarios no pueden iniciar sesión en el catálogo digital.
* **Causa Común:** Saturación en el pool de conexiones entre Keycloak y la base de datos PostgreSQL debido a un pico de tráfico involuntario.
* **Acciones de Mitigación Inmediatas:**
  1. Verificar el estado del contenedor o pod de Keycloak.
  2. Si las conexiones exceden el 90%, reiniciar el pool de conexiones de la base de datos ejecutando el script de mantenimiento interno `db_flush_connections.sh`.
  3. Incrementar temporalmente el parámetro `max_connections` a 200 en el archivo de configuración si el tráfico persiste.
* **Reporte Requerido:** Indicar el pico de transacciones por segundo (TPS) afectadas.