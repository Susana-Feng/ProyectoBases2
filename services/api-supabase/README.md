# API Supabase (FastAPI + uv)

Servicio FastAPI que expone endpoints apoyados en Supabase/PostgreSQL para la plataforma de datos. Toda la gestión del entorno Python se realiza con [uv](https://docs.astral.sh/uv/).

## Requisitos

- Python 3.10+
- [uv CLI](https://docs.astral.sh/uv/getting-started/installation/)
- Proyecto Supabase corriendo (revisa `.env.example` para las variables necesarias).

## Inicialización del proyecto

```bash
cd services/api-supabase
uv init --python 3.10  # solo si aún no existe pyproject.toml
uv add fastapi uvicorn[standard] supabase python-dotenv pydantic
```

> Este repositorio ya incluye `pyproject.toml`, por lo que normalmente basta con ejecutar `uv sync` para instalar las dependencias en la `.venv` gestionada por uv.

## Variables de entorno

Crea un `.env` en este directorio (o copia `.env.example`) con, al menos:

```env
SUPABASE_URL=https://YOUR-PROJECT.supabase.co
SUPABASE_KEY=service-role-key
PORT=3004
```

## Ejecución en desarrollo

```bash
uv sync
uv run uvicorn main:app --reload --host 0.0.0.0 --port ${PORT:-3004}
```

O usa el script expuesto en `pyproject.toml`:

```bash
uv run dev
```

## Uso dentro de `scripts/dev.sh`

El script unificado levanta este servicio con:

```
PORT=<puerto> uv run uvicorn main:app --reload --host 0.0.0.0 --port <puerto>
```

Asegúrate de tener `uv` instalado antes de ejecutar `./scripts/dev.sh --up supabase` o `--up all`.
