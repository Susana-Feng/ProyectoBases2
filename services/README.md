# WebApps & WebLoaders APIs

Este README documenta la carpeta `services/` del repositorio. Aquí encontrarás APIs y utilidades para distintas bases de datos.

Contenido rápido
- `services/api-mongo` — API en Python (FastAPI) que expone endpoints para la colección `ordenes`.
- `services/api-neo4j` — API en Python (FastAPI) que usa Neo4j como grafo.
- `services/api-mysql` — API en TypeScript (Bun + Hono + Prisma) para operaciones con MySQL (incluye scripts Prisma).
- `services/api-mssql` — API en TypeScript (Bun + Hono + Prisma) para MSSQL.
- `services/api-supabase` — Carpeta creada como placeholder para integraciones con Supabase (actualmente vacía); ver `scripts/Supabase/` para funciones y SQL relacionadas.

Requisitos previos

- Python 3.10+ (para los servicios en Python: `api-mongo`, `api-neo4j`)
- Bun (recomendado) o Node.js + npm/yarn (para `api-mysql` y `api-mssql`)
- Bases de datos según el servicio que quieras ejecutar: MongoDB, MySQL, MSSQL, Neo4j, o Supabase

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
├─ api-neo4j/      # FastAPI + Neo4j (Python)
│  ├─ config/
│  ├─ controllers/
│  ├─ repositories/
│  ├─ routes/
│  ├─ requirements.txt
│  └─ main.py
│
├─ api-mysql/      # Bun + Hono + Prisma (MySQL)
│  ├─ src/
│  ├─ package.json
│  └─ prisma/
│
├─ api-mssql/      # Bun + Hono + Prisma (MSSQL)
│  ├─ src/
│  ├─ package.json
│  └─ prisma/
│
└─ api-supabase/   # Placeholder (vacío actualmente) — ver scripts/Supabase/
```

**Nota:** cada subcarpeta puede contener ejemplos de `.env` (p. ej. `api-mongo/.env.example`, `api-neo4j/.env.example`).

## Cómo ejecutar cada servicio

Abajo tienes instrucciones mínimas y comandos de ejemplo. Ajusta puertos y variables de entorno según tu entorno local.

### 1) API Mongo (FastAPI)

Requisitos: Python 3.10+, MongoDB disponible (local o remota).

```powershell
cd services/api-mongo
python -m venv venv
venv\Scripts\activate    # Windows
# Linux / Mac: source venv/bin/activate
pip install -r requirements.txt
```

Crea un archivo `.env` con tus credenciales usando `api-mongo/.env.example` como referencia.

Ejecuta el servidor (puerto por defecto 8000):

```powershell
uvicorn main:app --reload
# Si se desea usar otro puerto, p. ej. 8002:
uvicorn main:app --reload --port 8002
```

Endpoints de ejemplo:
- API: http://localhost:8000
- Swagger Docs: http://localhost:8000/docs

### 2) API Neo4j (FastAPI)

Requisitos: Python 3.10+ y una instancia de Neo4j accesible.

```powershell
cd services/api-neo4j
python -m venv venv
venv\Scripts\activate    # Windows
pip install -r requirements.txt
```

Ejecuta el servidor (por defecto 8000; cambia puerto si tienes otro FastAPI corriendo):

```powershell
uvicorn main:app --reload --port 8001
```

Notas:
- Swagger Docs: http://localhost:8001/docs
- Revisa `services/api-neo4j/.env.example` para las variables que necesita la conexión al grafo (URL, usuario, contraseña).

### 3) API MySQL (Bun + Hono + Prisma)

Requiere Bun: https://bun.sh

```powershell
cd services/api-mysql
bun install
# Ejecuta en modo desarrollo (observa cambios):
bun run --watch src/index.ts   # o `bun run dev` si está definido

# Prisma (si necesitas generar o aplicar esquema):
bunx prisma generate
bunx prisma db push
```

### 4) API MSSQL (Bun + Hono + Prisma)

```powershell
cd services/api-mssql
bun install
bun run --watch src/index.ts

# Prisma commands
bunx prisma generate
bunx prisma db push
```

### 5) API Supabase (estado actual)

La carpeta `services/api-supabase` existe pero está vacía actualmente (es un placeholder para futuras funciones/handlers). Si buscas SQL o funciones relacionadas con Supabase, revisa `scripts/Supabase/` donde están las funciones y vistas SQL (`fn_actualizar_orden_completa.sql`, `fn_crear_orden.sql`, `fn_eliminar_orden.sql`, `query_crear_tabla.sql`, `vista_orden_completa.sql`).

Si más adelante agregas un servicio (por ejemplo, un Hono/Bun o FastAPI que actúe sobre Supabase), documenta aquí el `package.json` o `requirements.txt` y los pasos de arranque.



