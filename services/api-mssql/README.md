# API Excel to MSSQL

API backend construida con Bun, Hono y Prisma que acepta archivos Excel y los inserta en SQL Server.

## Autor
<REMOVED_BCCR_NAME>

## Características

- ✅ Framework web ultrarrápido con Hono
- ✅ Runtime Bun para máximo rendimiento
- ✅ ORM Prisma con adaptador MSSQL
- ✅ Validación de datos con Zod
- ✅ Transacciones atomicas (todo o nada)
- ✅ Identificadores naturales (Email/SKU) para relaciones
- ✅ Soporte para archivos Excel (.xlsx, .xls)

## Requisitos

- Bun >= 1.0
- SQL Server con base de datos `DB_SALES`

## Instalación

```bash
# Instalar dependencias
bun install

# Configurar variables de entorno
cp .env.example .env
# Editar .env con tus credenciales de SQL Server

# Generar Prisma Client
bun run db:generate
```

## Configuración

Edita el archivo `.env`:

```env
DATABASE_URL="sqlserver://localhost:1433;database=DB_SALES;user=sa;password=TuPassword;encrypt=true;trustServerCertificate=true"
PORT=3000
NODE_ENV=development
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

- **Swagger UI**: http://localhost:3000/docs
- **Especificación OpenAPI JSON**: http://localhost:3000/openapi.json

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

Ver documentación completa en: http://localhost:3000/docs

## Estructura del archivo Excel

El archivo Excel debe contener sheets (hojas) con los siguientes nombres y estructuras:

### Sheet: Cliente (opcional)

| Nombre | Email | Genero | Pais | FechaRegistro |
|--------|-------|--------|------|---------------|
| Juan Pérez | juan@email.com | Masculino | Costa Rica | 2024-01-15 |
| María López | maria@email.com | Femenino | México | 2024-01-16 |

**Columnas:**
- `Nombre`: Requerido (string, max 120 caracteres)
- `Email`: Opcional (string, email válido, max 150 caracteres) - Identificador único
- `Genero`: Opcional ('Masculino' o 'Femenino')
- `Pais`: Requerido (string, max 60 caracteres)
- `FechaRegistro`: Opcional (fecha, por defecto fecha actual)

### Sheet: Producto (opcional)

| SKU | Nombre | Categoria |
|-----|--------|-----------|
| SKU001 | Laptop Dell | Electrónica |
| SKU002 | Mouse Logitech | Accesorios |

**Columnas:**
- `SKU`: Requerido (string, max 40 caracteres) - Identificador único
- `Nombre`: Requerido (string, max 150 caracteres)
- `Categoria`: Requerido (string, max 80 caracteres)

### Sheet: Orden (opcional)

| Email | Fecha | Canal | Moneda | Total |
|-------|-------|-------|--------|-------|
| juan@email.com | 2024-01-20 | WEB | USD | 1500.00 |
| maria@email.com | 2024-01-21 | APP | USD | 250.50 |

**Columnas:**
- `Email`: Requerido (email del cliente que debe existir)
- `Fecha`: Opcional (fecha, por defecto fecha actual)
- `Canal`: Requerido ('WEB', 'TIENDA', o 'APP')
- `Moneda`: Opcional (string 3 caracteres, por defecto 'USD')
- `Total`: Requerido (número decimal positivo)

### Sheet: OrdenDetalle (opcional)

| OrdenIndex | SKU | Cantidad | PrecioUnit | DescuentoPct |
|------------|-----|----------|------------|--------------|
| 1 | SKU001 | 1 | 1500.00 | 0 |
| 2 | SKU002 | 5 | 50.10 | 10 |

**Columnas:**
- `OrdenIndex`: Requerido (número entero, índice de la fila en la sheet Orden, base 1)
- `SKU`: Requerido (SKU del producto que debe existir)
- `Cantidad`: Requerido (número entero positivo)
- `PrecioUnit`: Requerido (número decimal positivo)
- `DescuentoPct`: Opcional (número 0-100, porcentaje de descuento)

## Reglas de Procesamiento

1. **Sheets opcionales**: No es necesario incluir todas las sheets, solo las que necesites.

2. **Orden de procesamiento**:
   - Primero: Cliente
   - Segundo: Producto
   - Tercero: Orden
   - Cuarto: OrdenDetalle

3. **Identificadores naturales**:
   - Los clientes se identifican por Email
   - Los productos se identifican por SKU
   - Las órdenes se referencian por su índice en el Excel

4. **Upsert automático**:
   - Si un cliente con el mismo Email ya existe, se actualiza
   - Si un producto con el mismo SKU ya existe, se actualiza

5. **Validación de integridad**:
   - Las órdenes deben referenciar clientes existentes (por Email)
   - Los detalles deben referenciar productos existentes (por SKU)
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
  "error": "Cliente with email \"invalid@email.com\" not found for orden at index 1"
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
services/api-mssql/
├── src/
│   ├── index.ts                      # Servidor principal con OpenAPI
│   ├── lib/
│   │   └── prisma.ts                 # Cliente Prisma con adaptador MSSQL
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

1. **Abrir en el navegador**: http://localhost:3000/docs
2. **Probar endpoints directamente** desde la interfaz Swagger
3. **Ver esquemas y ejemplos** de request/response

La especificación OpenAPI completa está disponible en JSON: http://localhost:3000/openapi.json

## Ejemplo con cURL

```bash
# Subir un archivo Excel
curl -X POST http://localhost:3000/upload/excel \
  -F "file=@tu-archivo.xlsx"

# Verificar estado de la API
curl http://localhost:3000/health

# Obtener especificación OpenAPI
curl http://localhost:3000/openapi.json
```

## Solución de problemas

### Error de conexión a la base de datos

Si aparece el error `Login failed for user 'sa'` o `Failed to connect to localhost:1433`:

1. Verificar que SQL Server está corriendo
2. Verificar las credenciales en el archivo `.env`
3. Verificar que el puerto 1433 está accesible
4. Probar la conexión manualmente con Azure Data Studio o SSMS

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

1. Asegurar que SQL Server está corriendo
2. Verificar que `DATABASE_URL` en `.env` es correcto
3. Ejecutar `bun run db:push` para sincronizar el schema
4. Limpiar datos de prueba si es necesario

## Tecnologías utilizadas

- **Runtime**: [Bun](https://bun.sh) - JavaScript runtime ultrarrápido
- **Framework web**: [Hono](https://hono.dev) - Framework web ligero y rápido
- **ORM**: [Prisma](https://prisma.io) - ORM de próxima generación para TypeScript
- **Validación**: [Zod](https://zod.dev) - Validación de schemas TypeScript-first
- **Excel**: [SheetJS](https://sheetjs.com) - Biblioteca para lectura/escritura de Excel
- **Base de datos**: Microsoft SQL Server

## Licencia

ISC
