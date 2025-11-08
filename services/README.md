# Servicios (carpeta services)

Este README describe las APIs y utilidades del directorio `services/` del repositorio. Contiene instrucciones rápidas para ejecutar cada servicio, referencias a los ficheros más importantes y notas de despliegue.

## Resumen rápido
- `services/api-mongo` — FastAPI (Python) para operaciones sobre órdenes (MongoDB).
- `services/api-neo4j` — FastAPI (Python) que usa Neo4j.
- `services/api-mysql` — Bun + Hono + Prisma (TypeScript) para MySQL.
- `services/api-mssql` — Bun + Hono + Prisma (TypeScript) para MSSQL.
- `services/api-supabase` — FastAPI (Python) con rutas y helpers para integrarse con Supabase.

## Requisitos
- Python 3.10+ (servicios en Python: `api-mongo`, `api-neo4j`, `api-supabase`).
- Bun (recomendado) o Node.js + npm/yarn (servicios TypeScript: `api-mysql`, `api-mssql`).
- Bases de datos/servicios locales o remotos según cada API (MongoDB, Neo4j, MySQL, MSSQL, Supabase).

## Estructura (árbol de carpetas)

A continuación se listan únicamente las carpetas que existen dentro de cada API (estructura en árbol):

```bash
services/
├─ api-mongo/
│  ├─ config/
│  ├─ controllers/
│  ├─ repositories/
│  ├─ routers/
│  └─ schemas/
├─ api-neo4j/
│  ├─ config/
│  ├─ controllers/
│  ├─ repositories/
│  ├─ routes/
│  └─ schemas/
├─ api-mysql/
│  ├─ src/
│  └─ prisma/
├─ api-mssql/
│  ├─ src/
│  └─ prisma/
└─ api-supabase/
   ├─ config/
   ├─ controllers/
   ├─ repositories/
   ├─ routes/
   └─ schemas/
```

Cada subcarpeta también suele incluir un `requirements.txt` o `package.json` y un `.env.example` cuando aplica.


## Cómo ejecutar cada servicio (Windows / Linux)

Las instrucciones muestran tanto Windows (PowerShell) como Linux/macOS cuando difieren. Reemplaza `python` por `python3` si tu sistema lo requiere.

1) API Mongo (FastAPI)

```powershell
cd services/api-mongo
python -m venv venv 
venv\Scripts\activate # Windows
source venv/bin/activate #Linux
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```


2) API Neo4j (FastAPI)

```powershell
cd services/api-neo4j
python -m venv venv 
venv\Scripts\activate # Windows
source venv/bin/activate #Linux
pip install -r requirements.txt
uvicorn main:app --reload --port 8001
```


3) API MySQL (Bun + Hono + Prisma)

```bash
cd services/api-mysql
bun install
# Ejecutar en modo desarrollo:
bun run --watch src/index.ts
# Prisma (si aplica): bunx prisma generate
```

4) API MSSQL (Bun + Hono + Prisma)

```bash
cd services/api-mssql
bun install
bun run --watch src/index.ts
```

5) API Supabase (FastAPI — Python)

```powershell
cd services/api-neo4j
python -m venv venv 
venv\Scripts\activate # Windows
source venv/bin/activate #Linux
pip install -r requirements.txt
uvicorn main:app --reload --port 8002
```



