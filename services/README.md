# FastAPI Web Apps: MongoDB, Neo4j y Supabase Integradas

## 🛠 Requisitos previos

- Python 3.10+

- Node.js 18+

- MongoDB, Neo4j y Supabase configurados localmente o en la nube

- npm / yarn instalados para el frontend
---
## 📁 Estructura del proyecto
```bash
Apps/
│
├── MongoDB/
│ ├── api/ # Backend con FastAPI y conexión a MongoDB
│ └── ui/ # Frontend con Vite + TypeScript
│
├── Neo4j/
│ ├── api/ # Backend con FastAPI y conexión a Neo4j
│ └── ui/ # Frontend con Vite + TypeScript
│
└── Supabase/
├── api/ # Backend con FastAPI y conexión a Supabase
└── ui/ # Frontend con Vite + TypeScript
```
---


## 🧱 Estructura interna de cada servicio

Cada carpeta `api/` tiene la siguiente estructura:
```bash
api/
├── config/ # Configuración de conexiones y entorno
├── controllers/ # Lógica de negocio / manejo de peticiones
├── repositories/ # Operaciones CRUD o queries específicas
├── routers/ # Rutas (endpoints FastAPI)
├── schemas/ # Modelos Pydantic para validación de datos
├── .env # Variables de entorno (URIs, credenciales, etc.)
├── config.py # Carga de configuración global
└── main.py # Punto de entrada del servidor FastAPI
```

Y el frontend `ui/` usa esta estructura:
```bash
ui/
├── public/ # Archivos estáticos
├── src/ # Componentes, vistas, hooks, contextos, etc.
├── package.json # Dependencias y scripts de npm
├── vite.config.ts # Configuración de Vite
└── tsconfig*.json # Configuración de TypeScript
```
---
## ⚙️ Componentes principales
```bash
| Componente                               | Descripción                                    |
|------------------------------------------|------------------------------------------------|
| **FastAPI**                              | Framework backend rápido y asíncrono en Python |
| **Vite + TypeScript**                    | Framework frontend moderno para desarrollo SPA |
| **MongoDB**                              | Base de datos NoSQL de documentos              |
| **Neo4j**                                | Base de datos de grafos                        |
| **Supabase**                             | Backend relacional (PostgreSQL + API REST)     |
| **Uvicorn**                              | Servidor ASGI para ejecutar FastAPI            |
| **PyMongo**, **Py2Neo**, **Supabase-py** | SDKs oficiales de conexión                     |
| **Dotenv**                               | Gestión de variables de entorno                |
```

---

## 🧠 Instalación por módulo

### 1️⃣ Backend (FastAPI)

```bash
cd apps/mongodb_web/api     # o apps/neo4j_web/api o apps/supabase_web/api <--- hacer esto para cada bd
python -m venv venv
source venv/bin/activate      # Linux / Mac
venv\Scripts\activate         # Windows

pip install -r requirements.txt
```

Crea un archivo .env con tus credenciales siguiendo como referencia los archivos .env.example respectivos de cada base

Luego ejecutar el servidor:
```bash
uvicorn main:app --reload
```
- API: http://localhost:8000
- Swagger Docs: http://localhost:8000/docs

### Eliminación de entorno
Si se desea reiniciar todo, correr:
```bash
deactivate
```
Y luego 
```bash
Remove-Item -Recurse -Force venv
```
### 2️⃣ Frontend (Vite)
```bash
cd apps/mongodb_web/ui     # o apps/neo4j_web/ui o apps/supabase_web/ui
npm install -g pnpm
pnpm install
pnpm dev
```
El frontend estará disponible en:
```bash
http://localhost:5174/
```
