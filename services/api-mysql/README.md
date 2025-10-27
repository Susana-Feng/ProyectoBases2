# API Excel to MySQL

API backend construida con Bun, Hono y Prisma que acepta archivos Excel y los inserta en MySQL.

## Autor
<REMOVED_BCCR_NAME>

## Características

- ✅ Framework web ultrarrápido con Hono
- ✅ Runtime Bun para máximo rendimiento
- ✅ ORM Prisma para MySQL
- ✅ Validación de datos con Zod
- ✅ Transacciones atomicas (todo o nada)
- ✅ Identificadores naturales (correo/codigo_alt) para relaciones
- ✅ Soporte para archivos Excel (.xlsx, .xls)

## Requisitos

- Bun >= 1.0
- MySQL con base de datos `DB_SALES`

## Instalación

```bash
# Instalar dependencias
bun install

# Configurar variables de entorno
cp .env.example .env
# Editar .env con tus credenciales de MySQL

# Generar Prisma Client
bun run db:generate
```

## Configuración

Edita el archivo `.env`:

```env
DATABASE_URL="mysql://sales_user:vmE6X9VQzc6mqttrfERf@localhost:3306/DB_SALES"
PORT=3001
```

## Uso

### Iniciar servidor en modo desarrollo

```bash
bun run dev
```

### Iniciar servidor en producción

```bash
bun run start
```

## Endpoints

### Documentación API

La API incluye documentación OpenAPI 3.1 interactiva:

- **Swagger UI**: http://localhost:3001/docs
- **Especificación OpenAPI JSON**: http://localhost:3001/openapi.json

### Health Check

```http
GET /
GET /health
```

### Subir archivo Excel

```http
POST /upload/excel
Content-Type: multipart/form-data

file: archivo.xlsx
```

Ver documentación completa en: http://localhost:3001/docs

## Estructura del archivo Excel

El archivo Excel debe contener sheets (hojas) con los siguientes nombres y estructuras:

### Sheet: Cliente (opcional)

| nombre | correo | genero | pais | created_at |
|--------|--------|--------|------|------------|
| Juan Pérez | juan@email.com | M | Costa Rica | 2024-01-15 |
| María López | maria@email.com | F | México | 2024-01-16 |

**Columnas:**
- `nombre`: Requerido (string, max 120 caracteres)
- `correo`: Opcional (string, email válido, max 150 caracteres) - Identificador único
- `genero`: Opcional ('M', 'F', o 'X')
- `pais`: Requerido (string, max 60 caracteres)
- `created_at`: Opcional (fecha en formato VARCHAR YYYY-MM-DD)

### Sheet: Producto (opcional)

| codigo_alt | nombre | categoria |
|------------|--------|-----------|
| PROD001 | Laptop Dell | Electrónica |
| PROD002 | Mouse Logitech | Accesorios |

**Columnas:**
- `codigo_alt`: Requerido (string, max 64 caracteres) - Identificador único (código alternativo, no SKU oficial)
- `nombre`: Requerido (string, max 150 caracteres)
- `categoria`: Requerido (string, max 80 caracteres)

### Sheet: Orden (opcional)

| correo | fecha | canal | moneda | total |
|--------|-------|-------|--------|-------|
| juan@email.com | 2024-01-20 10:30:00 | WEB | USD | 1500.00 |
| maria@email.com | 2024-01-21 14:15:00 | APP | CRC | 250.50 |

**Columnas:**
- `correo`: Requerido (correo del cliente que debe existir)
- `fecha`: Opcional (fecha y hora en formato VARCHAR YYYY-MM-DD HH:MM:SS)
- `canal`: Requerido (texto libre, max 20 caracteres, ej: 'WEB', 'TIENDA', 'APP', 'TELEFONO', etc.)
- `moneda`: Opcional ('USD' o 'CRC' solamente, por defecto 'USD')
- `total`: Requerido (monto en formato VARCHAR, puede ser '1200.50' o '1,200.50')

### Sheet: OrdenDetalle (opcional)

| OrdenIndex | codigo_alt | cantidad | precio_unit |
|------------|------------|----------|-------------|
| 1 | PROD001 | 1 | 1500.00 |
| 2 | PROD002 | 5 | 50.10 |

**Columnas:**
- `OrdenIndex`: Requerido (número entero, índice de la fila en la sheet Orden, base 1)
- `codigo_alt`: Requerido (código alternativo del producto que debe existir)
- `cantidad`: Requerido (número entero positivo)
- `precio_unit`: Requerido (precio unitario en formato VARCHAR, puede ser '100.50' o '100,50')

## Reglas de Procesamiento

1. **Sheets opcionales**: No es necesario incluir todas las sheets, solo las que necesites.

2. **Orden de procesamiento**:
   - Primero: Cliente
   - Segundo: Producto
   - Tercero: Orden
   - Cuarto: OrdenDetalle

3. **Identificadores naturales**:
   - Los clientes se identifican por correo
   - Los productos se identifican por codigo_alt
   - Las órdenes se referencian por su índice en el Excel

4. **Upsert automático**:
   - Si un cliente con el mismo correo ya existe, se actualiza
   - Si un producto con el mismo codigo_alt ya existe, se actualiza

5. **Validación de integridad**:
   - Las órdenes deben referenciar clientes existentes (por correo)
   - Los detalles deben referenciar productos existentes (por codigo_alt)
   - Los detalles deben referenciar órdenes válidas (por índice)

6. **Transacciones**:
   - Todo el procesamiento se hace en una transacción
   - Si algo falla, se hace rollback completo (no se inserta nada)

## Respuesta de la API

### Éxito (200)

```json
{
  "success": true,
  "message": "Excel data processed successfully",
  "stats": {
    "clientesInsertados": 2,
    "productosInsertados": 2,
    "ordenesInsertadas": 2,
    "detallesInsertados": 2
  }
}
```

### Error de validación (400/422)

```json
{
  "success": false,
  "message": "Failed to process Excel data",
  "error": "Cliente with correo \"invalid@email.com\" not found for orden at index 1"
}
```

## Scripts disponibles

### Desarrollo

```bash
# Iniciar servidor en modo desarrollo con hot reload
bun run dev

# Iniciar servidor en modo producción
bun run start
```

### Base de datos

```bash
# Generar Prisma Client
bun run db:generate

# Sincronizar schema con la base de datos
bun run db:push

# Abrir Prisma Studio (GUI para la base de datos)
bun run db:studio
```

### Testing

```bash
# Ejecutar todos los tests
bun test

# Ejecutar tests en modo watch (recarga automática)
bun test --watch

# Ejecutar un archivo de test específico
bun test src/validators/__tests__/excel-schemas.test.ts

# Ejecutar tests con cobertura
bun test --coverage
```

## Testing

El proyecto incluye tests unitarios e integración usando el test runner nativo de Bun.

### Estructura de tests

```
src/
├── services/
│   ├── excel-processor.ts
│   └── __tests__/
│       └── excel-processor.test.ts
├── validators/
│   ├── excel-schemas.ts
│   └── __tests__/
│       └── excel-schemas.test.ts
└── routes/
    ├── upload.ts
    └── __tests__/
        └── upload.test.ts
```

### Tests disponibles

#### Validación de Schemas (excel-schemas.test.ts)
Tests para validar que los schemas Zod funcionan correctamente:
- Validación de campos requeridos y opcionales
- Validación de tipos de datos
- Validación de valores enum (Genero, Canal)
- Validación de rangos numéricos

#### Procesamiento de Excel (excel-processor.test.ts)
Tests de integración para el procesamiento de archivos Excel:
- Parsing de archivos Excel con múltiples sheets
- Inserción de datos en la base de datos
- Upsert de clientes por Email y productos por SKU
- Validación de integridad referencial
- Rollback de transacciones en caso de error
- Manejo de datos parciales

#### Endpoints HTTP (upload.test.ts)
Tests para los endpoints de la API:
- Validación de tipos de archivo
- Manejo de archivos vacíos
- Respuestas HTTP correctas

### Ejecutar tests antes de desplegar

```bash
# 1. Asegurarse que la base de datos está corriendo
# 2. Verificar que las variables de entorno están configuradas
# 3. Ejecutar los tests
bun test

# Si todos los tests pasan, el código está listo para desplegar
```

## Estructura del proyecto

```
services/api-mysql/
├── src/
│   ├── index.ts                      # Servidor principal con OpenAPI
│   ├── lib/
│   │   └── prisma.ts                 # Cliente Prisma para MySQL
│   ├── routes/
│   │   ├── upload.ts                 # Endpoints de upload
│   │   ├── upload.openapi.ts         # Definiciones OpenAPI para upload
│   │   ├── health.openapi.ts         # Definiciones OpenAPI para health
│   │   └── __tests__/
│   │       └── upload.test.ts        # Tests de endpoints
│   ├── services/
│   │   ├── excel-processor.ts        # Lógica de procesamiento Excel
│   │   └── __tests__/
│   │       └── excel-processor.test.ts  # Tests de procesamiento
│   ├── types/
│   │   └── excel.ts                  # Tipos TypeScript
│   └── validators/
│       ├── excel-schemas.ts          # Schemas Zod
│       └── __tests__/
│           └── excel-schemas.test.ts # Tests de validación
├── prisma/
│   └── schema.prisma                 # Schema de base de datos
├── .env                              # Variables de entorno (no commitear)
├── .env.example                      # Ejemplo de variables de entorno
├── package.json
├── tsconfig.json
└── README.md
```

## Acceder a la documentación Swagger UI

Una vez que el servidor esté corriendo, puedes acceder a la documentación interactiva:

1. **Abrir en el navegador**: http://localhost:3001/docs
2. **Probar endpoints directamente** desde la interfaz Swagger
3. **Ver esquemas y ejemplos** de request/response

La especificación OpenAPI completa está disponible en JSON: http://localhost:3001/openapi.json

## Ejemplo con cURL

```bash
# Subir un archivo Excel
curl -X POST http://localhost:3001/upload/excel \
  -F "file=@tu-archivo.xlsx"

# Verificar estado de la API
curl http://localhost:3001/health

# Obtener especificación OpenAPI
curl http://localhost:3001/openapi.json
```

## Solución de problemas

### Error de conexión a la base de datos

Si aparece el error de conexión a MySQL:

1. Verificar que MySQL está corriendo
2. Verificar las credenciales en el archivo `.env`
3. Verificar que el puerto 3306 está accesible
4. Probar la conexión manualmente con MySQL Workbench o DBeaver

### Error en Prisma Client

Si hay errores relacionados con Prisma Client:

```bash
# Regenerar el cliente
bun run db:generate

# Sincronizar el schema con la base de datos
bun run db:push
```

### Tests fallan

Si los tests fallan por problemas de base de datos:

1. Asegurar que MySQL está corriendo
2. Verificar que `DATABASE_URL` en `.env` es correcto
3. Ejecutar `bun run db:push` para sincronizar el schema
4. Limpiar datos de prueba si es necesario

## Tecnologías utilizadas

- **Runtime**: [Bun](https://bun.sh) - JavaScript runtime ultrarrápido
- **Framework web**: [Hono](https://hono.dev) - Framework web ligero y rápido
- **ORM**: [Prisma](https://prisma.io) - ORM de próxima generación para TypeScript
- **Validación**: [Zod](https://zod.dev) - Validación de schemas TypeScript-first
- **Excel**: [SheetJS](https://sheetjs.com) - Biblioteca para lectura/escritura de Excel
- **Base de datos**: MySQL

## Licencia

ISC
