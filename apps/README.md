# WebApps & WebLoaders Frontend

Este README describe el frontend del monorepo que está bajo la carpeta `apps/` (interfaces web construidas con Vite + React + TypeScript).

## Requisitos

- Node.js 18+ (se recomienda LTS)
- pnpm (recomendado; también funciona con npm/yarn)

## ¿Qué hay en `apps/`?

Dentro de `apps/` encontrarás varias apps frontales. La principal que contiene el UI para MongoDB es `apps/web-mongo` (puede aparecer con otro nombre en tu repo). Cada UI normalmente contiene:

- `public/` — estáticos públicos (index.html, favicon)
- `src/` — código fuente (components, pages, assets)
- `package.json` — scripts y dependencias del frontend
- `tsconfig*.json`, `vite.config.ts` (configuración de compilación y estilos)

Ejemplo (ruta típica):

```
apps/web-mongo/
├─ public/
├─ src/
│  ├─ assets/
│  ├─ components/
│  ├─ pages/
│  └─ main.tsx
├─ package.json
└─ vite.config.ts
```

## Variables de entorno importantes

- VITE_API_BASE — URL base para las peticiones al backend (p. ej. `http://localhost:8000`).

Coloca variables en un archivo `.env` o `.env.local` dentro de la carpeta del UI (p. ej. `apps/web-mongo/ui/.env`). Ejemplo:

```
VITE_API_BASE=http://localhost:8000
```

## Instalación

Ejecuta lo siguiente:

```bash
cd apps/web-mongo       # ó apps/web-mysql , apps/web-mssql    
npm install -g pnpm
pnpm install
pnpm dev
```
El frontend estará disponible en:
```bash
http://localhost:5173/
```

## Componentes y librerías usadas

- shadcn-ui (componentes UI)
- lucide-react (iconos)
- react + react-dom
- Vite + TypeScript

Comprueba `package.json` de la app para la lista completa de dependencias.
