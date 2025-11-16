# ETLs & Jobs

Este paquete contiene extractores, transformaciones y cargas (ETL) y jobs programados usados por el proyecto.

## Resumen rápido
- Directorio principal: `etl/`
- Script de entrada: `main.py`
- Jobs: `jobs/` (ej.: `bccr_tc_diario.py`, `bccr_tc_historico.py`, `scheduler.py`)

## Requisitos
- Python: la versión objetivo está en `.python-version` (por ejemplo 3.13+). Verifica con `python --version` o `python3 --version`.
- Recomendado: crear un entorno virtual para aislar dependencias.

## Instalación

```powershell
cd etl
uv sync          # instala dependencias de producción
uv sync --dev    # instala dependencias de desarrollo
```

### Variables de entorno
- Usa `.env.example` como plantilla. Hay un archivo ` .env.local` en el repositorio de ejemplo para desarrollo local.
- Antes de ejecutar, copia y edita:
```bash
cd etl
cp .env.example .env.local
# editar .env con tus credenciales/URLs
```

## Ejecución

```bash
cd etl
uv run python main.py
```

### Ejecutar jobs individuales
- Ejecutar el scheduler o jobs puntuales: por ejemplo
```bash
python -m jobs.scheduler
python -m jobs.bccr_tc_diario
```

## Estructura del proyecto 
```bash
etl/
├─ configs/
├─ extract/
├─ jobs/
├─ load/
├─ transform/
├─ .env.example
├─ .env.local
├─ main.py
├─ pyproject.toml
└─ README.md
```
