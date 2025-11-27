# Generador de Datos

## Configuración

1. Crea un archivo `.env.local` dentro de la carpeta `/data`
2. Copia y pega los mismos datos usados en el `.env.local` de la carpeta `/etl`

## Instalación de dependencias

```bash
uv sync
```

## Ejecución

Para ejecutar el generador de datos:

```bash
uv run generate.py
```

O alternativamente:

```bash
uv run python generate.py
```