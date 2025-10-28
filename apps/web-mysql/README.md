# React + TypeScript + Vite

This template provides a minimal setup to get React working in Vite with HMR and some ESLint rules.

Currently, two official plugins are available:

- [@vitejs/plugin-react](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react) uses [Babel](https://babeljs.io/) (or [oxc](https://oxc.rs) when used in [rolldown-vite](https://vite.dev/guide/rolldown)) for Fast Refresh
- [@vitejs/plugin-react-swc](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react-swc) uses [SWC](https://swc.rs/) for Fast Refresh

## React Compiler

The React Compiler is not enabled on this template because of its impact on dev & build performances. To add it, see [this documentation](https://react.dev/learn/react-compiler/installation).

## Expanding the ESLint configuration

If you are developing a production application, we recommend updating the configuration to enable type-aware lint rules:

# Web MySQL - Interfaz de Usuario

Aplicación web para visualizar y gestionar datos de clientes, productos, órdenes y detalles de órdenes desde la base de datos MySQL.

## Características

- **Listado de Clientes**: Visualiza todos los clientes con filtros por nombre, email, país y género
- **Listado de Productos**: Explora productos con filtros por nombre, código y categoría
- **Listado de Órdenes**: Consulta órdenes con filtros por cliente, canal, moneda y rango de precios
- **Listado de Detalles de Órdenes**: Visualiza detalles de órdenes con filtros por orden y producto
- **Paginación**: Navegación eficiente por grandes conjuntos de datos
- **Ordenamiento**: Ordena los resultados por cualquier columna
- **Búsqueda**: Búsqueda rápida y filtrado de datos

## Requisitos Previos

- Node.js (versión 18 o superior)
- npm, yarn o bun
- Backend MySQL API ejecutándose en `http://localhost:3001`

## Instalación

```bash
# Instalar dependencias
npm install
# o
yarn install
# o
bun install
```

## Desarrollo

```bash
# Iniciar servidor de desarrollo
npm run dev
# o
yarn dev
# o
bun dev
```

La aplicación estará disponible en `http://localhost:5173` (o el puerto que indique Vite).

## Build

```bash
# Compilar para producción
npm run build
# o
yarn build
# o
bun build
```

## Estructura del Proyecto

```
src/
├── routes/           # Páginas principales
│   ├── clientes.tsx
│   ├── productos.tsx
│   ├── ordenes.tsx
│   ├── orden-detalles.tsx
│   └── index.tsx
├── components/       # Componentes reutilizables
│   ├── data-table.tsx
│   ├── date-range-picker.tsx
│   ├── excel-uploader.tsx
│   ├── mode-toggle.tsx
│   ├── numeric-range-input.tsx
│   ├── related-data-cell.tsx
│   ├── theme-provider.tsx
│   └── ui/
├── lib/              # Utilidades y configuración
│   ├── api.ts        # Funciones para llamar a la API
│   └── utils.ts
├── types/            # Definiciones de tipos TypeScript
│   └── api.ts
└── contexts/         # React Context
    └── sidebar-context.tsx
```

## API

La aplicación se comunica con la API MySQL en `http://localhost:3001` usando los siguientes endpoints:

- `GET /clientes` - Listar clientes
- `GET /clientes/:id` - Obtener cliente por ID
- `GET /productos` - Listar productos
- `GET /productos/:id` - Obtener producto por ID
- `GET /ordenes` - Listar órdenes
- `GET /ordenes/:id` - Obtener orden por ID
- `GET /orden-detalles` - Listar detalles de órdenes
- `GET /orden-detalles/:id` - Obtener detalle por ID

Consulta la documentación de la API en `http://localhost:3001/docs` para más información.

## Tecnologías Utilizadas

- **React 19** - Biblioteca de UI
- **TypeScript** - Lenguaje con tipos estáticos
- **Vite** - Herramienta de compilación rápida
- **Tailwind CSS** - Framework de CSS
- **TanStack Router** - Enrutamiento moderno
- **Radix UI** - Componentes accesibles
- **date-fns** - Manipulación de fechas
- **sonner** - Notificaciones

## Configuración

### API Base URL

La URL base de la API está configurada en `src/lib/api.ts`:

```typescript
const API_BASE = "http://localhost:3001";
```

Modifica esta variable si tu servidor API está en una ubicación diferente.

### Temas

La aplicación soporta temas claros y oscuros. El selector está disponible en la barra de herramientas.

## Scripts Disponibles

- `npm run dev` - Inicia servidor de desarrollo
- `npm run build` - Compilar para producción
- `npm run lint` - Ejecutar ESLint
- `npm run preview` - Previsualizar build de producción

You can also install [eslint-plugin-react-x](https://github.com/Rel1cx/eslint-react/tree/main/packages/plugins/eslint-plugin-react-x) and [eslint-plugin-react-dom](https://github.com/Rel1cx/eslint-react/tree/main/packages/plugins/eslint-plugin-react-dom) for React-specific lint rules:

```js
// eslint.config.js
import reactX from 'eslint-plugin-react-x'
import reactDom from 'eslint-plugin-react-dom'

export default defineConfig([
  globalIgnores(['dist']),
  {
    files: ['**/*.{ts,tsx}'],
    extends: [
      // Other configs...
      // Enable lint rules for React
      reactX.configs['recommended-typescript'],
      // Enable lint rules for React DOM
      reactDom.configs.recommended,
    ],
    languageOptions: {
      parserOptions: {
        project: ['./tsconfig.node.json', './tsconfig.app.json'],
        tsconfigRootDir: import.meta.dirname,
      },
      // other options...
    },
  },
])
```
