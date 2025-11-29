import random
import string
import unicodedata
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Tuple

from faker import Faker
import pandas as pd


BASE_DIR = Path(__file__).parent
OUT_DIR = BASE_DIR / "out"
OUT_DIR.mkdir(exist_ok=True)

faker_es = Faker("es_ES")

# Catálogo de productos
CATALOGO_PRODUCTOS: Dict[str, list] = {
    "Electrónica": [
        "Televisor LED 32 pulgadas",
        "Televisor LED 55 pulgadas",
        "Smartphone gama básica",
        "Smartphone gama media",
        "Smartphone gama alta",
        "Laptop ultraligera 14 pulgadas",
        "Laptop para juegos 15 pulgadas",
        "Tablet 10 pulgadas",
        "Barra de sonido",
        "Auriculares inalámbricos",
        "Cámara digital básica",
        "Router WiFi doble banda",
        "Disco duro externo 1 TB",
    ],
    "Ropa": [
        "Camiseta algodón básica",
        "Pantalón de mezclilla",
        "Sudadera con capucha",
        "Chaqueta deportiva",
        "Vestido casual",
        "Camisa formal",
        "Short deportivo",
        "Pantalón de vestir",
        "Blusa manga larga",
        "Jacket impermeable",
    ],
    "Hogar": [
        "Juego de sábanas matrimoniales",
        "Almohada ortopédica",
        "Sartén antiadherente",
        "Juego de vasos de vidrio",
        "Tendedero plegable",
        "Cafetera eléctrica",
        "Lámpara de mesa",
        "Organizador de zapatos",
        "Cortinas blackout",
        "Cojín decorativo",
    ],
    "Deportes": [
        "Balón de fútbol tamaño 5",
        "Balón de baloncesto",
        "Bicicleta de montaña",
        "Mancuernas 5 kg",
        "Tapete para yoga",
        "Raqueta de tenis",
        "Casco para ciclismo",
        "Guantes de boxeo",
        "Lazo para saltar",
        "Botella deportiva",
    ],
    "Libros": [
        "Novela de ciencia ficción",
        "Novela histórica",
        "Manual de programación en Python",
        "Libro de cocina saludable",
        "Libro de desarrollo personal",
        "Cuentos infantiles ilustrados",
        "Libro de matemáticas básicas",
        "Guía de viaje",
        "Colección de poesía moderna",
        "Ensayo sobre economía",
    ],
    "Juguetes": [
        "Bloques de construcción",
        "Muñeca articulada",
        "Carro a control remoto",
        "Rompecabezas 1000 piezas",
        "Juego de mesa familiar",
        "Figura de acción",
        "Set de plastilina",
        "Pelota sensorial",
        "Pista de carreras",
        "Juego didáctico de letras",
    ],
    "Automotriz": [
        "Aceite de motor sintético",
        "Limpiador de parabrisas",
        "Juego de tapetes para auto",
        "Cargador de batería portátil",
        "Soporte para celular",
        "Limpiador de interiores",
        "Cera para autos",
        "Lámpara LED para faros",
        "Compresor de aire portátil",
        "Kit de emergencia para auto",
    ],
    "Salud": [
        "Vitamina C en tabletas",
        "Suplemento de magnesio",
        "Termómetro digital",
        "Tensiómetro de brazo",
        "Mascarilla desechable",
        "Gel antibacterial",
        "Collarín cervical suave",
        "Botiquín de primeros auxilios",
        "Báscula digital",
        "Almohadilla térmica eléctrica",
    ],
    "Alimentos": [
        "Arroz blanco",
        "Frijoles negros",
        "Aceite vegetal",
        "Pasta corta",
        "Leche descremada",
        "Cereal de avena",
        "Galletas integrales",
        "Café molido",
        "Azúcar morena",
        "Salsa de tomate",
    ],
    "Oficina": [
        "Cuaderno de rayas",
        "Paquete de hojas tamaño carta",
        "Bolígrafos de tinta azul",
        "Marcadores permanentes",
        "Carpeta plástica con aros",
        "Engrapadora metálica",
        "Resaltadores fluorescentes",
        "Cinta adhesiva transparente",
        "Organizador de escritorio",
        "Calculadora básica",
    ],
}

COLORES = ["Negro", "Blanco", "Azul", "Rojo", "Gris", "Verde"]
TALLAS = ["S", "M", "L", "XL"]
PRESENTACIONES_ALIMENTO = ["250 g", "500 g", "1 kg", "2 kg"]

# Variables globales para unicidad de clientes
nombres_usados = set()
correos_usados = set()


# ============================================================================
# FUNCIONES PARA GENERAR CLIENTES
# ============================================================================

def limpiar_texto(texto: str) -> str:
    """Elimina acentos y caracteres no ASCII del texto."""
    return ''.join(
        c for c in unicodedata.normalize('NFD', texto)
        if unicodedata.category(c) != 'Mn'
    )


def generar_email_desde_nombre(nombre: str) -> str:
    """Genera un email basado en el nombre."""
    nombre_limpio = limpiar_texto(nombre.lower().replace(" ", "."))
    return f"{nombre_limpio}@example.com"


def generar_datos_clientes_supabase(num_clientes: int = 600) -> List[Dict[str, Any]]:
    """Genera datos ficticios para clientes Supabase."""
    global nombres_usados, correos_usados

    fake = Faker('es_ES')
    clientes = []
    while len(clientes) < num_clientes:
        nombre = fake.name()
        email = generar_email_desde_nombre(nombre)

        # Verificar unicidad
        if nombre in nombres_usados:
            continue
        if email in correos_usados:
            continue

        # Registrar como usados
        nombres_usados.add(nombre)
        correos_usados.add(email)

        cliente = {
            'nombre': nombre,
            'email': email,
            'genero': random.choice(['M', 'F']),
            'pais': fake.country(),
            'fecha_registro': fake.date_between(start_date='-2y', end_date='today').isoformat()
        }
        clientes.append(cliente)
    return clientes


def generar_datos_clientes_mongo(num_clientes: int = 600) -> List[Dict[str, Any]]:
    """Genera datos ficticios para clientes MongoDB."""
    global nombres_usados, correos_usados

    fake = Faker('es_ES')
    clientes = []
    CANALES = ["WEB", "TIENDA"]

    while len(clientes) < num_clientes:
        nombre = fake.name()
        email = generar_email_desde_nombre(nombre)

        # Evitar duplicados
        if nombre in nombres_usados:
            continue
        if email in correos_usados:
            continue

        # Registrar como usados
        nombres_usados.add(nombre)
        correos_usados.add(email)

        # Seleccionar 1 o 2 canales distintos
        canales = random.sample(CANALES, random.randint(1, 2))

        cliente = {
            "nombre": nombre,
            "email": email,
            "genero": random.choice(["Masculino", "Femenino", "Otro"]),
            "pais": fake.country_code(),
            "preferencias": {
                "canal": canales
            },
            "creado": {
                "$date": fake.date_between(start_date='-2y', end_date='today').isoformat()
            }
        }
        clientes.append(cliente)

    return clientes


def generar_datos_clientes_neo4j(num_clientes: int = 600) -> List[Dict[str, Any]]:
    """Genera datos ficticios para clientes Neo4j."""
    global nombres_usados

    fake = Faker('es_ES')
    clientes = []
    generos_posibles = ['M', 'F', 'Otro', 'Masculino', 'Femenino']
    contador = 1

    while len(clientes) < num_clientes:
        nombre = fake.name()

        # Verificar unicidad del nombre
        if nombre in nombres_usados:
            continue

        # Registrar como usado
        nombres_usados.add(nombre)

        # Crear ID autogenerado C00001, C00002, ...
        id_cliente = f"C{contador:05d}"

        cliente = {
            'id': id_cliente,
            'nombre': nombre,
            'genero': random.choice(generos_posibles),
            'pais': fake.country()
        }

        clientes.append(cliente)
        contador += 1

    return clientes


def generar_datos_clientes_mssql(num_clientes: int = 600) -> List[Dict[str, Any]]:
    """Genera datos ficticios para clientes MSSQL."""
    global nombres_usados, correos_usados

    fake = Faker('es_ES')
    clientes = []

    while len(clientes) < num_clientes:
        nombre = fake.name()
        email = generar_email_desde_nombre(nombre)

        # Evitar duplicados
        if nombre in nombres_usados:
            continue
        if email in correos_usados:
            continue

        # Registrar como usados
        nombres_usados.add(nombre)
        correos_usados.add(email)

        cliente = {
            'Nombre': nombre,
            'Email': email,
            'Genero': random.choice(['Masculino', 'Femenino']),
            'Pais': fake.country(),
            'FechaRegistro': fake.date_between(start_date='-2y', end_date='today').isoformat()
        }
        clientes.append(cliente)
    return clientes


def generar_datos_clientes_mysql(num_clientes: int = 600) -> List[Dict[str, Any]]:
    """Genera datos ficticios para clientes MySQL."""
    global nombres_usados, correos_usados

    fake = Faker('es_ES')
    clientes = []

    while len(clientes) < num_clientes:
        nombre = fake.name()
        email = generar_email_desde_nombre(nombre)

        # Evitar duplicados
        if nombre in nombres_usados:
            continue
        if email in correos_usados:
            continue

        # Registrar como usados
        nombres_usados.add(nombre)
        correos_usados.add(email)

        cliente = {
            'nombre': nombre,
            'correo': email,
            'genero': random.choice(['M', 'F', 'X']),
            'pais': fake.country(),
            'created_at': fake.date_between(start_date='-2y', end_date='today').isoformat()
        }
        clientes.append(cliente)
    return clientes


# ============================================================================
# FUNCIONES PARA GENERAR PRODUCTOS
# ============================================================================

def generar_codigo_alt_unico(usados: set) -> str:
    """Genera un codigo_alt único con formato ALT-AB12."""
    while True:
        letras = ''.join(random.choices(string.ascii_uppercase, k=2))
        digitos = ''.join(random.choices(string.digits, k=2))
        codigo = f"ALT-{letras}{digitos}"
        if codigo not in usados:
            usados.add(codigo)
            return codigo


def generar_nombre_producto(categoria: str) -> str:
    """Genera un nombre de producto realista en función de la categoría."""
    base = random.choice(CATALOGO_PRODUCTOS[categoria])

    if categoria == "Ropa":
        color = random.choice(COLORES)
        talla = random.choice(TALLAS)
        return f"{base} {color} Talla {talla}"

    if categoria == "Alimentos":
        presentacion = random.choice(PRESENTACIONES_ALIMENTO)
        return f"{base} {presentacion}"

    if categoria == "Electrónica":
        variante = random.choice(["", "32 GB", "64 GB", "128 GB", "256 GB"])
        if variante:
            return f"{base} {variante}"
        return base

    return base


def generar_universo_productos(num_productos: int = 600) -> List[Dict[str, Any]]:
    """Genera un universo común de productos con códigos únicos."""
    productos = []
    codigos_alt_usados: set = set()
    categorias = list(CATALOGO_PRODUCTOS.keys())

    for i in range(num_productos):
        sku = f"SKU-{1000 + i}"
        codigo_mongo = f"MN-{4000 + i}"
        codigo_alt = generar_codigo_alt_unico(codigos_alt_usados)

        categoria = random.choice(categorias)
        nombre = generar_nombre_producto(categoria)

        producto = {
            "sku": sku,
            "codigo_alt": codigo_alt,
            "codigo_mongo": codigo_mongo,
            "nombre": nombre,
            "categoria": categoria,
        }
        productos.append(producto)

    return productos


def distribuir_productos_entre_catalogos(
    productos_universo: List[Dict[str, Any]],
    p_mssql: float = 0.9,
    p_mysql: float = 0.9,
    p_supabase: float = 0.75,
    p_mongo: float = 0.65,
    p_neo4j: float = 0.85,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Distribuye el universo de productos entre los diferentes catálogos."""
    productos_mssql: List[Dict[str, Any]] = []
    productos_mysql: List[Dict[str, Any]] = []
    productos_supabase: List[Dict[str, Any]] = []
    productos_mongo: List[Dict[str, Any]] = []
    productos_neo4j: List[Dict[str, Any]] = []

    for prod in productos_universo:
        # MSSQL: sku, nombre, categoria
        if random.random() < p_mssql:
            productos_mssql.append(
                {
                    'sku': prod['sku'],
                    'nombre': prod['nombre'],
                    'categoria': prod['categoria'],
                }
            )

        # MySQL: codigo_alt, nombre, categoria
        if random.random() < p_mysql:
            productos_mysql.append(
                {
                    'codigo_alt': prod['codigo_alt'],
                    'nombre': prod['nombre'],
                    'categoria': prod['categoria'],
                }
            )

        # Supabase: sku (a veces vacío), nombre, categoria
        if random.random() < p_supabase:
            sku_value = prod['sku']
            # Dejar algunos registros sin SKU (vacío) para reflejar que puede venir vacío
            if random.random() < 0.1:
                sku_value = ''
            productos_supabase.append(
                {
                    'sku': sku_value,
                    'nombre': prod['nombre'],
                    'categoria': prod['categoria'],
                }
            )

        # Mongo: codigo_mongo, nombre, categoria, equivalencias
        if random.random() < p_mongo:
            equivalencias = {
                'codigo_alt': prod['codigo_alt']
            }
            # El sku en equivalencias solo aparece algunas veces
            if random.random() < 0.7:
                equivalencias['sku'] = prod['sku']

            productos_mongo.append(
                {
                    'codigo_mongo': prod['codigo_mongo'],
                    'nombre': prod['nombre'],
                    'categoria': prod['categoria'],
                    'equivalencias': equivalencias,
                }
            )

        # Neo4j: sku, codigo_alt, codigo_mongo, nombre, categoria
        if random.random() < p_neo4j:
            productos_neo4j.append(
                {
                    'sku': prod['sku'],
                    'codigo_alt': prod['codigo_alt'],
                    'codigo_mongo': prod['codigo_mongo'],
                    'nombre': prod['nombre'],
                    'categoria': prod['categoria'],
                }
            )

    return (
        productos_mssql,
        productos_mysql,
        productos_supabase,
        productos_mongo,
        productos_neo4j,
    )


# ============================================================================
# FUNCIONES PARA GENERAR ÓRDENES
# ============================================================================

def _sample_order_dates(n: int) -> List[datetime]:
    start = datetime(2024, 1, 1)
    end = datetime(2025, 12, 31, 23, 59, 59)
    delta = (end - start).total_seconds()
    return [start + timedelta(seconds=random.randint(0, int(delta))) for _ in range(n)]


def generate_orders_mysql(num_orders: int, clientes: List[Dict[str, Any]], productos: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    orders: List[Dict[str, Any]] = []
    details: List[Dict[str, Any]] = []
    dates = _sample_order_dates(num_orders)
    canales = ["WEB", "TIENDA", "APP", "PARTNER"]
    
    # Build codigo_alt to index mapping (1-based for MySQL AUTO_INCREMENT)
    codigo_to_idx = {p["codigo_alt"]: idx for idx, p in enumerate(productos, start=1)}
    
    for i, fecha in enumerate(dates, start=1):
        # Select a random client (1-based index since MySQL AUTO_INCREMENT starts at 1)
        cliente_idx = random.randint(1, len(clientes))
        moneda = random.choice(["USD", "CRC"])
        num_items = random.randint(1, 5)
        total_decimal = 0.0
        order_details: List[Dict[str, Any]] = []
        for _ in range(num_items):
            prod = random.choice(productos)
            prod_idx = codigo_to_idx.get(prod["codigo_alt"], 1)
            cantidad = random.randint(1, 5)
            precio = round(random.uniform(5, 500), 2)
            total_decimal += cantidad * precio
            precio_str = f"{precio:,.2f}" if random.random() < 0.3 else f"{precio:.2f}"
            order_details.append({
                "orden_id": i,
                "producto_id": prod_idx,
                "cantidad": cantidad,
                "precio_unit": precio_str,
                "codigo_alt": prod["codigo_alt"],
            })
        if moneda == "CRC":
            total_decimal *= 540
        total_str = f"{total_decimal:,.2f}" if random.random() < 0.3 else f"{total_decimal:.2f}"
        orders.append({
            "id": i,
            "cliente_id": cliente_idx,
            "fecha": fecha.strftime("%Y-%m-%d %H:%M:%S"),
            "canal": random.choice(canales),
            "moneda": moneda,
            "total": total_str,
        })
        details.extend(order_details)
    return orders, details


def generate_orders_mssql(num_orders: int, clientes: List[Dict[str, Any]], productos: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    orders = []
    details = []
    dates = _sample_order_dates(num_orders)
    canales = ["WEB", "TIENDA", "APP"]
    
    # Build SKU to index mapping (1-based for SQL Server IDENTITY)
    sku_to_idx = {p["sku"]: idx for idx, p in enumerate(productos, start=1)}
    
    for i, fecha in enumerate(dates, start=1):
        # Select a random client (1-based index since SQL Server IDENTITY starts at 1)
        cliente_idx = random.randint(1, len(clientes))
        num_items = random.randint(1, 5)
        total = 0.0
        line_items = []
        for _ in range(num_items):
            prod = random.choice(productos)
            prod_idx = sku_to_idx.get(prod["sku"], 1)
            cantidad = random.randint(1, 5)
            precio = round(random.uniform(5, 500), 2)
            descuento = round(random.uniform(0, 15), 2) if random.random() < 0.3 else None
            total += cantidad * precio * (1 - (descuento or 0) / 100)
            line_items.append({
                "OrdenId": i,
                "ProductoId": prod_idx,
                "Cantidad": cantidad,
                "PrecioUnit": precio,
                "DescuentoPct": descuento,
                "SKU": prod["sku"],
            })
        orders.append({
            "OrdenId": i,
            "ClienteId": cliente_idx,
            "Fecha": fecha.strftime("%Y-%m-%d %H:%M:%S"),
            "Canal": random.choice(canales),
            "Moneda": "USD",
            "Total": round(total, 2),
        })
        details.extend(line_items)
    return orders, details


def write_mysql_sql(clientes, productos, orders, details, path: Path) -> None:
    lines: List[str] = ["USE DB_SALES;", ""]
    for c in clientes:
        nombre = c["nombre"].replace("'", "''")
        correo = c["correo"].replace("'", "''")
        pais = c["pais"].replace("'", "''")
        lines.append(
            f"INSERT INTO Cliente (nombre, correo, genero, pais, created_at) VALUES ('{nombre}', '{correo}', '{c['genero']}', '{pais}', '{c['created_at']}');"
        )
    lines.append("")
    for p in productos:
        nombre = p["nombre"].replace("'", "''")
        categoria = p["categoria"].replace("'", "''")
        lines.append(
            f"INSERT INTO Producto (codigo_alt, nombre, categoria) VALUES ('{p['codigo_alt']}', '{nombre}', '{categoria}');"
        )
    lines.append("")
    for o in orders:
        lines.append(
            "INSERT INTO Orden (cliente_id, fecha, canal, moneda, total) "
            f"VALUES ({o['cliente_id']}, '{o['fecha']}', '{o['canal']}', '{o['moneda']}', '{o['total']}');"
        )
    lines.append("")
    for d in details:
        precio = d["precio_unit"].replace("'", "''")
        lines.append(
            "INSERT INTO OrdenDetalle (orden_id, producto_id, cantidad, precio_unit) "
            f"VALUES ({d['orden_id']}, {d['producto_id']}, {d['cantidad']}, '{precio}');"
        )
    path.write_text("\n".join(lines), encoding="utf-8")


def write_mssql_sql(clientes, productos, orders, details, path: Path) -> None:
    lines: List[str] = ["USE DB_SALES;", "GO", ""]
    for c in clientes:
        nombre = c["Nombre"].replace("'", "''")
        email = c["Email"].replace("'", "''")
        pais = c["Pais"].replace("'", "''")
        lines.append(
            "INSERT INTO dbo.Cliente (Nombre, Email, Genero, Pais, FechaRegistro) "
            f"VALUES (N'{nombre}', N'{email}', N'{c['Genero']}', N'{pais}', '{c['FechaRegistro']}');"
        )
    lines.append("GO\n")
    for p in productos:
        nombre = p["nombre"].replace("'", "''")
        categoria = p["categoria"].replace("'", "''")
        lines.append(
            "INSERT INTO dbo.Producto (SKU, Nombre, Categoria) "
            f"VALUES (N'{p['sku']}', N'{nombre}', N'{categoria}');"
        )
    lines.append("GO\n")
    for o in orders:
        lines.append(
            "INSERT INTO dbo.Orden (ClienteId, Fecha, Canal, Moneda, Total) "
            f"VALUES ({o['ClienteId']}, '{o['Fecha']}', N'{o['Canal']}', '{o['Moneda']}', {o['Total']});"
        )
    lines.append("GO\n")
    for d in details:
        descuento = "NULL" if d["DescuentoPct"] is None else f"{d['DescuentoPct']}"
        lines.append(
            "INSERT INTO dbo.OrdenDetalle (OrdenId, ProductoId, Cantidad, PrecioUnit, DescuentoPct) "
            f"VALUES ({d['OrdenId']}, {d['ProductoId']}, {d['Cantidad']}, {d['PrecioUnit']}, {descuento});"
        )
    lines.append("GO")
    path.write_text("\n".join(lines), encoding="utf-8")


def generate_orders_supabase(num_orders: int, clientes: List[Dict[str, Any]], productos: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    orders: List[Dict[str, Any]] = []
    details: List[Dict[str, Any]] = []
    dates = _sample_order_dates(num_orders)
    canales = ["WEB", "APP", "PARTNER"]
    
    # Assign indices to clientes and productos for referencing
    for idx, c in enumerate(clientes, start=1):
        c['_idx'] = idx
    for idx, p in enumerate(productos, start=1):
        p['_idx'] = idx
    
    for i, fecha in enumerate(dates, start=1):
        cliente = random.choice(clientes)
        moneda = random.choice(["USD", "CRC"])
        num_items = random.randint(1, 5)
        total = 0.0
        line_items = []
        for _ in range(num_items):
            prod = random.choice(productos)
            cantidad = random.randint(1, 5)
            precio = round(random.uniform(5, 500), 2)
            total += cantidad * precio
            line_items.append(
                {
                    "orden_idx": i,
                    "producto_idx": prod['_idx'],
                    "cantidad": cantidad,
                    "precio_unit": precio,
                    "sku": prod["sku"],
                    "nombre": prod["nombre"],
                }
            )
        orders.append(
            {
                "orden_idx": i,
                "cliente_idx": cliente['_idx'],
                "fecha": fecha.isoformat(),
                "canal": random.choice(canales),
                "moneda": moneda,
                "total": round(total, 2),
            }
        )
        details.extend(line_items)
    return orders, details


def write_supabase_sql(clientes, productos, orders, details, path: Path) -> None:
    lines: List[str] = []
    
    # Insert clientes
    for c in clientes:
        nombre = c["nombre"].replace("'", "''")
        email = (c["email"] or "").replace("'", "''") if c.get("email") is not None else ""
        pais = c["pais"].replace("'", "''")
        lines.append(
            "INSERT INTO cliente (nombre, email, genero, pais, fecha_registro) "
            f"VALUES ('{nombre}', '{email or ''}', '{c['genero']}', '{pais}', '{c['fecha_registro']}');"
        )
    lines.append("")
    
    # Insert productos
    for p in productos:
        nombre = p["nombre"].replace("'", "''")
        categoria = p["categoria"].replace("'", "''")
        sku = p["sku"]
        sku_val = f"'{sku}'" if sku else "NULL"
        lines.append(
            "INSERT INTO producto (sku, nombre, categoria) "
            f"VALUES ({sku_val}, '{nombre}', '{categoria}');"
        )
    lines.append("")
    
    # Create temporary mapping tables
    lines.append("-- Create temporary tables for mapping")
    lines.append("CREATE TEMP TABLE _cliente_map AS SELECT cliente_id, ROW_NUMBER() OVER (ORDER BY cliente_id) AS idx FROM cliente;")
    lines.append("CREATE TEMP TABLE _producto_map AS SELECT producto_id, ROW_NUMBER() OVER (ORDER BY producto_id) AS idx FROM producto;")
    lines.append("")
    
    # Insert orders with proper cliente_id lookup
    for o in orders:
        lines.append(
            "INSERT INTO orden (cliente_id, fecha, canal, moneda, total) "
            f"SELECT cliente_id, '{o['fecha']}', '{o['canal']}', '{o['moneda']}', {o['total']} "
            f"FROM _cliente_map WHERE idx = {o['cliente_idx']};"
        )
    lines.append("")
    
    # Create orden mapping table
    lines.append("CREATE TEMP TABLE _orden_map AS SELECT orden_id, ROW_NUMBER() OVER (ORDER BY orden_id) AS idx FROM orden;")
    lines.append("")
    
    # Insert order details with proper orden_id and producto_id lookups
    for d in details:
        lines.append(
            "INSERT INTO orden_detalle (orden_id, producto_id, cantidad, precio_unit) "
            f"SELECT o.orden_id, p.producto_id, {d['cantidad']}, {d['precio_unit']} "
            f"FROM _orden_map o, _producto_map p WHERE o.idx = {d['orden_idx']} AND p.idx = {d['producto_idx']};"
        )
    
    lines.append("")
    lines.append("-- Clean up temporary tables")
    lines.append("DROP TABLE IF EXISTS _cliente_map;")
    lines.append("DROP TABLE IF EXISTS _producto_map;")
    lines.append("DROP TABLE IF EXISTS _orden_map;")
    
    path.write_text("\n".join(lines), encoding="utf-8")


def generate_orders_mongo(num_orders: int, clientes: List[Dict[str, Any]], productos: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Generates orders for MongoDB that properly reference clients and products.
    Returns: (clientes_with_ids, productos_with_ids, orders_with_refs)
    """
    orders: List[Dict[str, Any]] = []
    dates = _sample_order_dates(num_orders)
    
    # Assign indices to clientes and productos for referencing in the JS output
    for idx, c in enumerate(clientes):
        c['_idx'] = idx
    for idx, p in enumerate(productos):
        p['_idx'] = idx
    
    for i, fecha in enumerate(dates):
        cliente = random.choice(clientes)
        num_items = random.randint(1, 5)
        items = []
        total = 0
        for _ in range(num_items):
            prod = random.choice(productos)
            cantidad = random.randint(1, 5)
            precio_unit = random.randint(1000, 60000)
            total += cantidad * precio_unit
            items.append(
                {
                    "producto_idx": prod['_idx'],
                    "cantidad": cantidad,
                    "precio_unit": precio_unit,
                }
            )
        orders.append(
            {
                "cliente_idx": cliente['_idx'],
                "fecha": fecha,
                "canal": random.choice(["WEB", "TIENDA"]),
                "moneda": "CRC",
                "total": total,
                "items": items,
            }
        )
    return clientes, productos, orders


def write_mongo_js(clientes, productos, orders, path: Path) -> None:
    def js_str(value: str) -> str:
        return value.replace("'", "\\'").replace("\\", "\\\\")

    lines: List[str] = ["use('tiendaDB');", ""]
    
    # Insert clientes and capture their IDs
    lines.append("// Insertar clientes y obtener IDs")
    lines.append("const clientesDocs = [")
    cliente_docs = []
    for c in clientes:
        canales = ", ".join(f"'{ch}'" for ch in c["preferencias"]["canal"])
        doc = (
            "  {nombre: '%s', email: '%s', genero: '%s', pais: '%s', "
            "preferencias: { canal: [%s] }, creado: new Date('%s')}"
            % (
                js_str(c["nombre"]),
                js_str(c["email"]),
                js_str(c["genero"]),
                js_str(c["pais"]),
                canales,
                c["creado"]["$date"],
            )
        )
        cliente_docs.append(doc)
    lines.append(",\n".join(cliente_docs))
    lines.append("];")
    lines.append("const clientesResult = db.clientes.insertMany(clientesDocs);")
    lines.append("const clienteIds = Object.values(clientesResult.insertedIds);")
    lines.append("")

    # Insert productos and capture their IDs
    lines.append("// Insertar productos y obtener IDs")
    lines.append("const productosDocs = [")
    prod_docs = []
    for p in productos:
        eq = p["equivalencias"]
        sku = eq.get("sku")
        codigo_alt = eq.get("codigo_alt")
        eq_parts = []
        if sku is not None:
            eq_parts.append(f"sku: '{js_str(sku)}'")
        if codigo_alt is not None:
            eq_parts.append(f"codigo_alt: '{js_str(codigo_alt)}'")
        eq_str = ", ".join(eq_parts)
        doc = (
            "  {codigo_mongo: '%s', nombre: '%s', categoria: '%s', equivalencias: {%s}}"
            % (
                js_str(p["codigo_mongo"]),
                js_str(p["nombre"]),
                js_str(p["categoria"]),
                eq_str,
            )
        )
        prod_docs.append(doc)
    lines.append(",\n".join(prod_docs))
    lines.append("];")
    lines.append("const productosResult = db.productos.insertMany(productosDocs);")
    lines.append("const productoIds = Object.values(productosResult.insertedIds);")
    lines.append("")

    # Insert ordenes with proper references
    lines.append("// Insertar ordenes con referencias correctas")
    lines.append("const ordenesDocs = [")
    order_docs = []
    for o in orders:
        items_js = []
        for it in o["items"]:
            items_js.append(
                "    { producto_id: productoIds[%d], cantidad: %d, precio_unit: %d }"
                % (it["producto_idx"], it["cantidad"], it["precio_unit"])
            )
        items_block = ",\n".join(items_js)
        doc = (
            "  {\n"
            "    cliente_id: clienteIds[%d],\n"
            "    fecha: new Date('%s'),\n"
            "    canal: '%s',\n"
            "    moneda: 'CRC',\n"
            "    total: %d,\n"
            "    items: [\n%s\n    ]\n"
            "  }"
            % (
                o["cliente_idx"],
                o["fecha"].isoformat(),
                o["canal"],
                o["total"],
                items_block,
            )
        )
        order_docs.append(doc)
    lines.append(",\n".join(order_docs))
    lines.append("];")
    lines.append("db.ordenes.insertMany(ordenesDocs);")
    lines.append("")
    lines.append("print('Datos insertados correctamente');")
    lines.append(f"print('Clientes: ' + clienteIds.length);")
    lines.append(f"print('Productos: ' + productoIds.length);")
    lines.append(f"print('Ordenes: ' + ordenesDocs.length);")
    
    path.write_text("\n".join(lines), encoding="utf-8")


def generate_orders_neo4j(num_orders: int, clientes: List[Dict[str, Any]], productos: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    orders: List[Dict[str, Any]] = []
    rels: List[Dict[str, Any]] = []
    dates = _sample_order_dates(num_orders)
    canales = ["WEB", "TIENDA", "APP", "PARTNER"]
    monedas = ["USD", "CRC"]
    for i, fecha in enumerate(dates, start=1):
        order_id = f"ORD-{i:06d}"
        cliente = random.choice(clientes)
        moneda = random.choice(monedas)
        num_items = random.randint(1, 5)
        total = 0.0
        for _ in range(num_items):
            prod = random.choice(productos)
            cantidad = random.randint(1, 5)
            precio = round(random.uniform(5, 500), 2)
            total += cantidad * precio
            rels.append(
                {
                    "cliente_id": cliente["id"],
                    "orden_id": order_id,
                    "producto_sku": prod["sku"],
                    "producto_alt": prod["codigo_alt"],
                    "producto_mongo": prod["codigo_mongo"],
                    "cantidad": cantidad,
                    "precio_unit": precio,
                    "fecha": fecha,
                }
            )
        orders.append(
            {
                "id": order_id,
                "cliente_id": cliente["id"],
                "fecha": fecha,
                "canal": random.choice(canales),
                "moneda": moneda,
                "total": round(total, 2),
            }
        )
    return orders, rels


def write_neo4j_cypher(clientes, productos, orders, rels, path: Path) -> None:
    lines: List[str] = []
    for c in clientes:
        nombre = c["nombre"].replace("'", "''")
        pais = c["pais"].replace("'", "''")
        lines.append(
            "CREATE (:Cliente {id: '%s', nombre: '%s', genero: '%s', pais: '%s'});"
            % (c["id"], nombre, c["genero"], pais)
        )
    lines.append("")
    categorias = sorted(set(p["categoria"] for p in productos))
    for i, cat in enumerate(categorias, start=1):
        nombre = cat.replace("'", "''")
        lines.append(
            "CREATE (:Categoria {id: 'CAT-%03d', nombre: '%s'});" % (i, nombre)
        )
    lines.append("")
    for p in productos:
        nombre = p["nombre"].replace("'", "''")
        categoria = p["categoria"].replace("'", "''")
        lines.append(
            "MATCH (c:Categoria {nombre: '%s'}) "
            "CREATE (p:Producto {id: '%s', nombre: '%s', categoria: '%s', sku: '%s', codigo_alt: '%s', codigo_mongo: '%s'})-[:PERTENECE_A]->(c);"
            % (
                categoria,
                p["sku"],
                nombre,
                categoria,
                p["sku"],
                p["codigo_alt"],
                p["codigo_mongo"],
            )
        )
    lines.append("")
    for o in orders:
        lines.append(
            "MATCH (c:Cliente {id: '%s'}) "
            "CREATE (c)-[:REALIZO]->(:Orden {id: '%s', fecha: datetime('%s'), canal: '%s', moneda: '%s', total: %s});"
            % (
                o["cliente_id"],
                o["id"],
                o["fecha"].isoformat(),
                o["canal"],
                o["moneda"],
                o["total"],
            )
        )
    lines.append("")
    for r in rels:
        lines.append(
            "MATCH (o:Orden {id: '%s'}), (p:Producto {sku: '%s'}) "
            "CREATE (o)-[:CONTIENTE {cantidad: %d, precio_unit: %s}]->(p);"
            % (
                r["orden_id"],
                r["producto_sku"],
                r["cantidad"],
                r["precio_unit"],
            )
        )
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    num_clientes_total = 3000
    num_productos_universo = 600
    num_ordenes_total = 25000

    clientes_supabase = generar_datos_clientes_supabase(num_clientes_total // 5)
    clientes_mongo = generar_datos_clientes_mongo(num_clientes_total // 5)
    clientes_neo4j = generar_datos_clientes_neo4j(num_clientes_total // 5)
    clientes_mssql = generar_datos_clientes_mssql(num_clientes_total // 5)
    clientes_mysql = generar_datos_clientes_mysql(num_clientes_total // 5)

    universo = generar_universo_productos(num_productos_universo)
    (
        productos_mssql,
        productos_mysql,
        productos_supabase,
        productos_mongo,
        productos_neo4j,
    ) = distribuir_productos_entre_catalogos(universo)

    ordenes_mysql, detalles_mysql = generate_orders_mysql(num_ordenes_total // 5, clientes_mysql, productos_mysql)
    ordenes_mssql, detalles_mssql = generate_orders_mssql(num_ordenes_total // 5, clientes_mssql, productos_mssql)
    ordenes_supabase, detalles_supabase = generate_orders_supabase(num_ordenes_total // 5, clientes_supabase, productos_supabase)
    clientes_mongo_out, productos_mongo_out, ordenes_mongo = generate_orders_mongo(num_ordenes_total // 5, clientes_mongo, productos_mongo)
    ordenes_neo4j, rels_neo4j = generate_orders_neo4j(num_ordenes_total // 5, clientes_neo4j, productos_neo4j)

    write_mysql_sql(
        clientes_mysql,
        productos_mysql,
        ordenes_mysql,
        detalles_mysql,
        OUT_DIR / "mysql_data.sql",
    )
    write_mssql_sql(
        clientes_mssql,
        productos_mssql,
        ordenes_mssql,
        detalles_mssql,
        OUT_DIR / "mssql_data.sql",
    )
    write_supabase_sql(
        clientes_supabase,
        productos_supabase,
        ordenes_supabase,
        detalles_supabase,
        OUT_DIR / "supabase_data.sql",
    )
    write_mongo_js(
        clientes_mongo_out,
        productos_mongo_out,
        ordenes_mongo,
        OUT_DIR / "mongo_data.js",
    )
    write_neo4j_cypher(
        clientes_neo4j,
        productos_neo4j,
        ordenes_neo4j,
        rels_neo4j,
        OUT_DIR / "neo4j_data.cypher",
    )


if __name__ == "__main__":
    main()
