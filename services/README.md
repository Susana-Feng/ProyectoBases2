# WebApps & WebLoaders APIs

Este README documenta la carpeta `services/` del repo. Dentro encontrarás APIs y utilidades para distintas bases de datos: `api-mongo` (FastAPI + MongoDB), `api-mysql` (Bun + Hono + Prisma) y `api-mssql` (Bun + Hono + Prisma).

Contenido rápido
- `services/api-mongo` — API en Python (FastAPI) que expone endpoints para la colección `ordenes`.
- `services/api-mysql` — API en TypeScript (Bun + Hono + Prisma) para operaciones con MySQL (incluye scripts Prisma).
- `services/api-mssql` — API en TypeScript (Bun + Hono + Prisma) para MSSQL.

## Requisitos previos

- Python 3.10+ (para `api-mongo`)
- Bun (recomendado) o Node.js + npm/yarn (para `api-mysql` y `api-mssql`)
- MongoDB / MySQL / MSSQL según el servicio que quieras ejecutar

## Estructura (resumen)
```bash
services/
├─ api-mongo/      # FastAPI + PyMongo
│  ├─ config/
│  ├─ controllers/
│  ├─ repositories/
│  ├─ routers/
│  ├─ schemas/
│  ├─ requirements.txt
│  └─ main.py
│
├─ api-mysql/      # Bun + Hono + Prisma (MySQL)
│  ├─ src/
│  ├─ package.json
│  └─ prisma/
│
└─ api-mssql/      # Bun + Hono + Prisma (MSSQL)
	├─ src/
	├─ package.json
	└─ prisma/
```
**Nota:** cada subcarpeta contiene sus propios ejemplos de `.env` si aplica (p. ej. `api-mongo/.env.example`).

## Cómo ejecutar cada servicio

### 1) API Mongo (FastAPI)

```powershell
cd services/api-mongo
python -m venv venv
source venv/bin/activate      # Linux / Mac
venv\Scripts\activate         # Windows
pip install -r requirements.txt
```
Crea un archivo .env con tus credenciales siguiendo como referencia los archivos .env.example respectivos de cada base

Luego ejecutar el servidor:
```powershell
uvicorn main:app --reload
```
Endpoints de ejemplo:
- API: http://localhost:8000
- Swagger Docs: http://localhost:8000/docs

**Nota:** En caso de querer reiniciar el entorno de Python, ejecute:
```bash
deactivate

Remove-Item -Recurse -Force venv
```
### 2) API MySQL (Bun + Hono + Prisma)

Requiere Bun instalado: https://bun.sh

```bash
cd services/api-mysql
bun install        # instala dependencias
bun run --watch src/index.ts   # o `bun run dev` si está definido

# Prisma (si necesitas generar o aplicar esquema):
bunx prisma generate
bunx prisma db push
```

### 3) API MSSQL (Bun + Hono + Prisma)

```bash
cd services/api-mssql
bun install
bun run --watch src/index.ts

# Prisma commands
bunx prisma generate
bunx prisma db push
```

