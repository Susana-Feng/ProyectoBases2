# API Neo4j (FastAPI + uv)

Servicio FastAPI que expone datos relacionales del grafo Neo4j y sirve como backend para la aplicación web correspondiente. Toda la gestión del entorno Python se realiza con [uv](https://docs.astral.sh/uv/).

## Requisitos

- Python 3.10+
- [uv CLI](https://docs.astral.sh/uv/getting-started/installation/)
- Una instancia Neo4j accesible (local o remota) con los datos cargados.

## Inicialización del proyecto

```bash
cd services/api-neo4j
uv init --python 3.10  # solo si no existen pyproject.toml/uv.lock
uv add fastapi uvicorn[standard] neo4j python-dotenv pydantic
```

> Ya se incluye `pyproject.toml` con esas dependencias, así que basta ejecutar `uv sync` para instalar todo dentro de la `.venv` que crea uv.

## Variables de entorno

Crea un `.env` en este directorio (o usa el `.env.example`) con al menos:

```env
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=devpass
PORT=3003
```

`PORT` es opcional: por defecto el servicio expone el puerto `3003`, pero puedes sobrescribirlo para integrarlo con otros servicios.

## Ejecución en desarrollo

```bash
uv sync  # instala/actualiza dependencias declaradas en pyproject.toml
uv run uvicorn main:app --reload --host 0.0.0.0 --port ${PORT:-3003}
```

También puedes usar el script declarado en `pyproject.toml`:

```bash
uv run dev
```

## Uso dentro de `scripts/dev.sh`

El script unificado de desarrollo detecta este servicio y lo levanta con:

```
PORT=<puerto> uv run uvicorn main:app --reload --host 0.0.0.0 --port <puerto>
```

Asegúrate de tener `uv` instalado antes de ejecutar `./scripts/dev.sh --up neo4j` o `--up all`.
