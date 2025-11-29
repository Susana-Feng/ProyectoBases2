# API Mongo (FastAPI + uv)

Servicio FastAPI que consulta documentos en MongoDB y, cuando necesita reglas de asociación o metadatos de apoyo, llama procedimientos almacenados en el data warehouse MSSQL. Ahora todo el flujo usa [uv](https://docs.astral.sh/uv/) para administrar el entorno Python.

## Requisitos

- Python 3.10+
- [uv CLI](https://docs.astral.sh/uv/getting-started/installation/)
- MongoDB y MSSQL corriendo localmente o por red (las credenciales se toman del `.env`)

## Inicialización del proyecto

```bash
cd services/api-mongo
uv init --python 3.10  # crea .venv y pyproject si aún no existen
uv add fastapi uvicorn[standard] pymongo python-dotenv pydantic pyodbc
```

> Ya se incluye `pyproject.toml` con esas dependencias, por lo que basta correr `uv sync` para instalarlas en la `.venv` generada por uv.

## Variables de entorno

Crea `.env.local` o `.env` en este directorio y define al menos:

```env
MONGO_URI=mongodb://usuario:pass@localhost:27017
MONGO_DB=tiendaDB

# Conexión al data warehouse SQL Server usado para reglas de asociación
MSSQL_DW_HOST=localhost
MSSQL_DW_PORT=1434
MSSQL_DW_USER=sa
MSSQL_DW_PASS=YourStrong@Passw0rd1
MSSQL_DW_DB=DW_SALES

PORT=3002
```

Las variables `MSSQL_DW_*` son necesarias porque varias rutas consultan procedimientos almacenados (`dw.sp_obtener_consecuentes_por_skus`, etc.) que viven en el DW. Sin ellas, las peticiones que cruzan datos entre Mongo y MSSQL fallarán.

## Ejecución en desarrollo

```bash
uv run uvicorn main:app --reload --host 0.0.0.0 --port ${PORT:-3002}
```

También puedes usar el script configurado en `pyproject.toml`:

```bash
uv run dev
```

## Uso dentro de `scripts/dev.sh`

El script unificado de desarrollo detecta este servicio y lo levanta con:

```
PORT=<puerto> uv run uvicorn main:app --reload --host 0.0.0.0 --port <puerto>
```

Asegúrate de tener `uv` instalado antes de ejecutar `./scripts/dev.sh --up mongo` o `--up all`.
