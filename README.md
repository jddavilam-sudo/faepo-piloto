# FAEPO | Piloto 3.0: lectura compartida

Versión de demostración con consultas desde Supabase PostgreSQL, preservando la interfaz V2.

## Publicación
Reemplaza `app.py` y `requirements.txt` en el repositorio GitHub. Configura secretos de Streamlit (`SUPABASE_URL` y `SUPABASE_PUBLISHABLE_KEY`) en su gestor privado. Nunca subas `.streamlit/secrets.toml` ni credenciales a GitHub.

La app consulta las tablas `comunicaciones`, `programas` y `solicitudes` mediante la API REST y políticas RLS de lectura. No admite escritura compartida hasta incorporar control de acceso.

No introduzcas información institucional real en servicios públicos.
