# FAEPO — Piloto visual 2.0

Aplicación de prueba creada con **Python + Streamlit**. Reproduce una interfaz de gestión institucional inspirada de manera general en los modelos visuales enviados por el usuario (sin utilizar recursos gráficos oficiales originales).

## Cómo actualizar el proyecto anterior

1. Descomprima `FAEPO_Sistema_V2.zip`.
2. Abra la carpeta `FAEPO_Sistema_V2` en VS Code.
3. Abra una terminal en esta carpeta.
4. Ejecute:

```powershell
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Se abrirá `http://localhost:8501` (o el siguiente puerto disponible).

Si el sistema anterior está abierto, termine ese servidor desde su terminal con **Ctrl+C** antes de ejecutar esta versión.

## Funcionalidades
- Dashboard con indicadores y gráficos.
- Consulta detallada por comunicación GS (una comunicación puede incluir varios programas).
- Consulta por programa (comunicaciones y unidades que pidieron cupos).
- Registro de nuevos programas por GS y catálogo ampliable.
- Modificación de cupos solicitados/asignados y del estado.
- Exportación a Excel con detalle, resumen por programa y por GS.

## Limitaciones de seguridad y datos
- Es una **prueba con datos completamente ficticios** (`GS-DEMO-*`).
- Al recargar sesión o reiniciar servidor se pierden los cambios.
- No hay autenticación ni base de datos compartida.
- No cargar comunicaciones, datos personales ni información institucional real en un alojamiento público sin aprobación de seguridad institucional.
- Acceso a un sitio web ≠ autorización para almacenar datos institucionales.

## Próximo desarrollo
Persistencia multiusuario en base de datos autorizada, control de acceso y auditoría de modificaciones.
