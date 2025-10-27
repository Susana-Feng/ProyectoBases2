# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "faker",
#     "openpyxl",
#     "pandas",
# ]
# ///

import random
from pathlib import Path
from typing import List, Dict, Any
import pandas as pd
from faker import Faker


# Directorios base
BASE_DIR = Path(__file__).parent
SAMPLES_DIR = BASE_DIR / 'samples'
MSSQL_DIR = SAMPLES_DIR / 'mssql'
MYSQL_DIR = SAMPLES_DIR / 'mysql'

# Crear directorios si no existen
MSSQL_DIR.mkdir(parents=True, exist_ok=True)
MYSQL_DIR.mkdir(parents=True, exist_ok=True)


def generar_datos_clientes(num_clientes: int = 600) -> List[Dict[str, Any]]:
    """Genera datos ficticios para clientes."""
    fake = Faker('es_ES')  # Usar español para nombres y países
    clientes = []
    for _ in range(num_clientes):
        cliente = {
            'Nombre': fake.name(),
            'Email': fake.email(),
            'Genero': random.choice(['Masculino', 'Femenino']),
            'Pais': fake.country(),
            'FechaRegistro': fake.date_between(start_date='-2y', end_date='today').isoformat()
        }
        clientes.append(cliente)
    return clientes


def generar_datos_clientes_mysql(num_clientes: int = 600) -> List[Dict[str, Any]]:
    """Genera datos ficticios para clientes (MySQL - heterogeneidades)."""
    fake = Faker('es_ES')
    clientes = []
    for _ in range(num_clientes):
        cliente = {
            'nombre': fake.name(),
            'correo': fake.email(),
            'genero': random.choice(['M', 'F', 'X']),  # Valores heterogéneos: M, F, X
            'pais': fake.country(),
            'created_at': fake.date_between(start_date='-2y', end_date='today').isoformat()  # VARCHAR: YYYY-MM-DD
        }
        clientes.append(cliente)
    return clientes


def generar_datos_productos(num_productos: int = 100) -> List[Dict[str, Any]]:
    """Genera datos ficticios para productos."""
    fake = Faker()
    categorias = ['Electrónica', 'Ropa', 'Hogar', 'Deportes', 'Libros', 'Juguetes', 'Automotriz', 'Salud']
    productos = []
    for i in range(num_productos):
        sku = f"SKU{i+1:04d}"
        producto = {
            'SKU': sku,
            'Nombre': fake.sentence(nb_words=3)[:-1],  # Quitar el punto final
            'Categoria': random.choice(categorias)
        }
        productos.append(producto)
    return productos


def generar_datos_productos_mysql(num_productos: int = 100) -> List[Dict[str, Any]]:
    """Genera datos ficticios para productos (MySQL - heterogeneidades)."""
    fake = Faker()
    categorias = ['Electrónica', 'Ropa', 'Hogar', 'Deportes', 'Libros', 'Juguetes', 'Automotriz', 'Salud']
    productos = []
    for i in range(num_productos):
        codigo_alt = f"ALT{i+1:05d}"  # Código alternativo (NO es SKU oficial)
        producto = {
            'codigo_alt': codigo_alt,
            'nombre': fake.sentence(nb_words=3)[:-1],  # Quitar el punto final
            'categoria': random.choice(categorias)
        }
        productos.append(producto)
    return productos


def generar_datos_ordenes(num_ordenes: int = 5000, clientes: List[Dict[str, Any]] = None, productos: List[Dict[str, Any]] = None) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Genera datos ficticios para órdenes y detalles de órdenes."""
    if not clientes or not productos:
        raise ValueError("Se requieren listas de clientes y productos")
    
    fake = Faker()
    ordenes = []
    detalles = []
    orden_index = 1  # Para OrdenIndex en detalles
    
    for _ in range(num_ordenes):
        cliente = random.choice(clientes)
        fecha = fake.date_time_between(start_date='-1y', end_date='now')
        canal = random.choice(['WEB', 'TIENDA', 'APP'])
        moneda = 'USD'
        
        # Generar detalles para esta orden (1-5 productos)
        num_detalles = random.randint(1, 5)
        total = 0
        orden_detalles = []
        
        for _ in range(num_detalles):
            producto = random.choice(productos)
            cantidad = random.randint(1, 10)
            precio_unit = round(random.uniform(10, 500), 2)
            descuento_pct = round(random.uniform(0, 20), 2) if random.random() < 0.3 else None
            subtotal = cantidad * precio_unit
            if descuento_pct:
                subtotal *= (1 - descuento_pct / 100)
            total += subtotal
            
            detalle = {
                'OrdenIndex': orden_index,
                'SKU': producto['SKU'],
                'Cantidad': cantidad,
                'PrecioUnit': precio_unit,
                'DescuentoPct': descuento_pct
            }
            orden_detalles.append(detalle)
        
        orden = {
            'Email': cliente['Email'],
            'Fecha': fecha.isoformat(),
            'Canal': canal,
            'Moneda': moneda,
            'Total': round(total, 2)
        }
        ordenes.append(orden)
        detalles.extend(orden_detalles)
        orden_index += 1
    
    return ordenes, detalles


def generar_datos_ordenes_mysql(num_ordenes: int = 5000, clientes: List[Dict[str, Any]] = None, productos: List[Dict[str, Any]] = None) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Genera datos ficticios para órdenes y detalles (MySQL - heterogeneidades)."""
    if not clientes or not productos:
        raise ValueError("Se requieren listas de clientes y productos")
    
    fake = Faker()
    ordenes = []
    detalles = []
    orden_index = 1
    
    for _ in range(num_ordenes):
        cliente = random.choice(clientes)
        fecha = fake.date_time_between(start_date='-1y', end_date='now')
        # Canal libre (no controlado) - heterogeneidad
        canal = random.choice(['WEB', 'TIENDA', 'APP', 'Telefono', 'whatsapp', 'Facebook'])
        # Moneda: ENUM('USD', 'CRC')
        moneda = random.choice(['USD', 'CRC'])
        
        # Generar detalles para esta orden (1-5 productos)
        num_detalles = random.randint(1, 5)
        total = 0
        orden_detalles = []
        
        for _ in range(num_detalles):
            producto = random.choice(productos)
            cantidad = random.randint(1, 10)
            precio_unit = round(random.uniform(10, 500), 2)
            subtotal = cantidad * precio_unit
            total += subtotal
            
            # Precio como VARCHAR con formato aleatorio (heterogeneidad)
            if random.random() < 0.5:
                precio_str = f"{precio_unit:.2f}"  # Formato: 100.50
            else:
                precio_str = f"{precio_unit:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')  # Formato: 100,50
            
            detalle = {
                'OrdenIndex': orden_index,
                'codigo_alt': producto['codigo_alt'],
                'cantidad': cantidad,
                'precio_unit': precio_str  # VARCHAR con formato variable
            }
            orden_detalles.append(detalle)
        
        # Total como VARCHAR con formato aleatorio (heterogeneidad)
        if random.random() < 0.5:
            total_str = f"{total:.2f}"  # Formato: 1200.50
        else:
            total_str = f"{total:,.2f}"  # Formato: 1,200.50
        
        orden = {
            'correo': cliente['correo'],
            'fecha': fecha.strftime('%Y-%m-%d %H:%M:%S'),  # VARCHAR: YYYY-MM-DD HH:MM:SS
            'canal': canal,
            'moneda': moneda,
            'total': total_str  # VARCHAR con formato variable
        }
        ordenes.append(orden)
        detalles.extend(orden_detalles)
        orden_index += 1
    
    return ordenes, detalles


def guardar_csv(datos: List[Dict[str, Any]], filename: str) -> None:
    """Guarda una lista de diccionarios en un archivo CSV."""
    df = pd.DataFrame(datos)
    df.to_csv(filename, index=False)
    print(f"Guardado {filename} con {len(datos)} registros")


def guardar_excel(data_dict: Dict[str, List[Dict[str, Any]]], filename: str) -> None:
    """Guarda múltiples DataFrames en un archivo Excel con tipos de datos correctos."""
    with pd.ExcelWriter(filename, engine='openpyxl') as writer:
        for sheet_name, datos in data_dict.items():
            df = pd.DataFrame(datos)
            
            # Convertir columnas numéricas al tipo correcto (solo para MSSQL)
            # MySQL usa VARCHAR para precios/totales (heterogeneidad)
            for col in df.columns:
                # Detectar si la columna debe ser numérica
                if col in ['PrecioUnit', 'Cantidad', 'Total', 'DescuentoPct', 'OrdenIndex']:
                    if col == 'Cantidad' or col == 'OrdenIndex':
                        df[col] = pd.to_numeric(df[col], errors='coerce').astype('Int64')
                    else:
                        df[col] = pd.to_numeric(df[col], errors='coerce').astype('float64')
                # Para MySQL: cantidad como número, pero precio_unit y total quedan como strings
                elif col == 'cantidad':
                    df[col] = pd.to_numeric(df[col], errors='coerce').astype('Int64')
                # precio_unit y total en MySQL quedan como VARCHAR (strings)
            
            df.to_excel(writer, sheet_name=sheet_name, index=False)


def generar_excel_mssql() -> None:
    """Genera el archivo Excel para MSSQL con todas las hojas."""
    print("Generando datos para MSSQL...")
    
    # Generar datos
    clientes = generar_datos_clientes(600)
    productos = generar_datos_productos(100)
    ordenes, detalles = generar_datos_ordenes(5000, clientes, productos)
    
    # Guardar CSVs en samples/mssql/
    guardar_csv(clientes, str(MSSQL_DIR / 'clients.csv'))
    guardar_csv(productos, str(MSSQL_DIR / 'products.csv'))
    guardar_csv(ordenes, str(MSSQL_DIR / 'orders.csv'))
    guardar_csv(detalles, str(MSSQL_DIR / 'order_details.csv'))
    
    # Crear Excel con tipos de datos correctos en samples/mssql/
    data_dict = {
        'Cliente': clientes,
        'Producto': productos,
        'Orden': ordenes,
        'OrdenDetalle': detalles
    }
    guardar_excel(data_dict, str(MSSQL_DIR / 'data_mssql.xlsx'))
    
    print(f"Archivos generados en {MSSQL_DIR}")
    print("Archivo data_mssql.xlsx generado exitosamente")


def generar_excel_mysql() -> None:
    """Genera el archivo Excel para MySQL con heterogeneidades."""
    print("Generando datos para MySQL...")
    print("Nota: Datos con heterogeneidades según esquema MySQL")
    
    # Generar datos con funciones específicas para MySQL
    clientes = generar_datos_clientes_mysql(600)
    productos = generar_datos_productos_mysql(100)
    ordenes, detalles = generar_datos_ordenes_mysql(5000, clientes, productos)
    
    # Guardar CSVs en samples/mysql/
    guardar_csv(clientes, str(MYSQL_DIR / 'clients.csv'))
    guardar_csv(productos, str(MYSQL_DIR / 'products.csv'))
    guardar_csv(ordenes, str(MYSQL_DIR / 'orders.csv'))
    guardar_csv(detalles, str(MYSQL_DIR / 'order_details.csv'))
    
    # Crear Excel con tipos de datos correctos en samples/mysql/
    data_dict = {
        'Cliente': clientes,
        'Producto': productos,
        'Orden': ordenes,
        'OrdenDetalle': detalles
    }
    guardar_excel(data_dict, str(MYSQL_DIR / 'data_mysql.xlsx'))
    
    print(f"Archivos generados en {MYSQL_DIR}")
    print("Archivo data_mysql.xlsx generado exitosamente con heterogeneidades")


def main() -> None:
    """Función principal del script."""
    print("=== Generador de Datos de Prueba ===\n")
    generar_excel_mssql()
    print()
    generar_excel_mysql()
    print("\n=== Generación completada ===")


if __name__ == "__main__":
    main()
