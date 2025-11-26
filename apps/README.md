# Frontend de webs

Este README describe las aplicaciones frontend del monorepo ubicadas en la carpeta apps/, construidas con Vite + React + TypeScript.
## 📋 Requisitos

    Node.js 18+ (se recomienda versión LTS)

    pnpm (recomendado; también funciona con npm/yarn)

## 🗂️ Estructura de Apps

Dentro de apps/ encontrarás múltiples aplicaciones frontend especializadas:
Aplicaciones Disponibles

    apps/web-mongo - Interfaz para MongoDB

    apps/web-supabase - Interfaz para Supabase

    apps/web-neo4j - Interfaz para Neo4j

    apps/web-mssql - Interfaz para Mssql

    apps/web-mysql - Interfaz para Mysql

## Estructura Común de Cada App

Cada aplicación sigue esta estructura típica:
```bash
apps/[web-bd]/
├── public/                 # Archivos estáticos (index.html, favicon)
├── src/
│   ├── assets/            # Recursos estáticos (imágenes, estilos)
│   ├── components/        # Componentes React reutilizables
│   ├── pages/             # Páginas/views de la aplicación
│   ├── utils/             # Utilidades y helpers
│   └── main.tsx           # Punto de entrada
├── package.json           # Dependencias y scripts
├── vite.config.ts         # Configuración de Vite
└── tsconfig.json          # Configuración de TypeScript
```
## 🚀 Instalación y Desarrollo
Instalación Global (si no tienes pnpm)
```bash

npm install -g pnpm
```
## Para cada aplicación:
### Navegar a la aplicación deseada:

```bash
cd apps/web-mongo       # o apps/web-supabase, apps/web-neo4j,  apps/web-mssql, apps/web-mysql
```
### Instalar dependencias:
```bash

pnpm install
```
### Ejecutar en modo desarrollo:
```bash

pnpm dev
```
### URLs de Desarrollo

Cada aplicación estará disponible en:

http://localhost:5173/

Nota: Si ejecutas múltiples apps simultáneamente, Vite asignará puertos diferentes automáticamente.
### 🛠️ Comandos Disponibles

Cada aplicación incluye estos scripts en su package.json:
``` bash

pnpm dev          # Servidor de desarrollo
pnpm build        # Build para producción
pnpm preview      # Vista previa del build
pnpm lint         # Linting del código
```
### 📚 Stack Tecnológico
Core

    React 18 + React DOM

    TypeScript

    Vite (bundler y dev server)

UI Components

    shadcn/ui - Sistema de componentes UI

    Tailwind CSS - Framework de estilos

    lucide-react - Librería de iconos

Estado y Utilidades

    React Hook Form - Manejo de formularios

    React Query / SWR - Gestión de estado del servidor

    Zod - Validación de esquemas

### 🔧 Configuración
Variables de Entorno

Cada aplicación puede requerir variables específicas. Consulta el archivo .env.example en cada directorio de aplicación.
TypeScript

