import random
import string
import unicodedata
from datetime import datetime, timedelta
from io import StringIO
from pathlib import Path
from typing import List, Dict, Any, Tuple
from uuid import uuid4

from faker import Faker
import pandas as pd
import csv


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

# Asociación entre categorías: (categoria1, categoria2, probabilidad)
CATEGORIAS_RELACIONADAS = [
    ("Electrónica", "Electrónica", 0.4),
    ("Ropa", "Ropa", 0.5),
    ("Deportes", "Ropa", 0.3),
    ("Deportes", "Deportes", 0.4),
    ("Hogar", "Hogar", 0.35),
    ("Oficina", "Oficina", 0.45),
    ("Alimentos", "Alimentos", 0.5),
    ("Juguetes", "Juguetes", 0.4),
    ("Electrónica", "Hogar", 0.2),
    ("Libros", "Libros", 0.35),
]

# Bundles: grupos de productos que se compran juntos frecuentemente
# Más bundles pequeños = patrones más fuertes para FP-Growth
PRODUCT_BUNDLES = []
random.seed(42)  # Seed fijo para bundles consistentes entre ejecuciones
for i in range(100):
    bundle_size = random.choice([2, 2, 2, 2, 3, 3])  # Mayoría de 2 productos
    base_idx = random.randint(0, 400)
    # Productos cercanos en el catálogo (más realista)
    bundle_indices = [base_idx + j * random.randint(1, 5) for j in range(bundle_size)]
    bundle_indices = [idx % 500 for idx in bundle_indices]
    PRODUCT_BUNDLES.append(bundle_indices)
random.seed()  # Restaurar aleatoriedad

BUNDLE_PROBABILITY = 0.50  # 50% de órdenes usarán bundles

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
            'cliente_id': str(uuid4()),
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
        # Only add GB variant to products that don't already have specs (TB, pulgadas, etc.)
        has_specs = any(spec in base.lower() for spec in ["tb", "pulgadas", "gb", "mhz"])
        if not has_specs:
            variante = random.choice(["", "32 GB", "64 GB", "128 GB", "256 GB"])
            if variante:
                return f"{base} {variante}"
        return base

    return base


def generar_universo_productos(num_productos: int = 600) -> List[Dict[str, Any]]:
    """
    Genera un universo común de productos con códigos únicos.
    Garantiza que cada producto tenga un nombre+categoría único.
    """
    productos = []
    codigos_alt_usados: set = set()
    nombres_usados: set = set()  # Track (nombre, categoria) pairs
    categorias = list(CATALOGO_PRODUCTOS.keys())

    for i in range(num_productos):
        sku = f"SKU-{1000 + i}"
        codigo_mongo = f"MN-{4000 + i}"
        codigo_alt = generar_codigo_alt_unico(codigos_alt_usados)

        # Try to generate a unique name+category combination
        max_attempts = 100
        nombre = None
        categoria = None
        
        for attempt in range(max_attempts):
            categoria = random.choice(categorias)
            base_nombre = generar_nombre_producto(categoria)
            
            # Check if this combination is unique
            key = (base_nombre, categoria)
            if key not in nombres_usados:
                nombre = base_nombre
                nombres_usados.add(key)
                break
            
            # If not unique and running out of attempts, add a variant suffix
            if attempt >= max_attempts - 10:
                variant_num = attempt - (max_attempts - 10) + 1
                nombre = f"{base_nombre} v{variant_num}"
                key = (nombre, categoria)
                if key not in nombres_usados:
                    nombres_usados.add(key)
                    break
        
        # Fallback: use SKU-based name if still no unique name found
        if nombre is None:
            categoria = random.choice(categorias)
            nombre = f"Producto {sku}"
            nombres_usados.add((nombre, categoria))

        producto = {
            "sku": sku,
            "codigo_alt": codigo_alt,
            "codigo_mongo": codigo_mongo,
            "nombre": nombre,
            "categoria": categoria,
        }
        productos.append(producto)

    return productos


def seleccionar_productos_con_asociacion(
    productos: List[Dict[str, Any]], 
    num_items: int,
    probabilidad_asociacion: float = 0.6
) -> List[Dict[str, Any]]:
    """Selecciona productos aplicando patrones de asociación (bundles y categorías)."""
    if num_items <= 0:
        return []
    
    seleccionados: List[Dict[str, Any]] = []
    productos_ids_usados: set = set()
    
    # Intentar usar un bundle predefinido
    if random.random() < BUNDLE_PROBABILITY and len(productos) >= 2:
        bundle = random.choice(PRODUCT_BUNDLES)
        for idx in bundle:
            if idx < len(productos) and len(seleccionados) < num_items:
                prod = productos[idx]
                if id(prod) not in productos_ids_usados:
                    seleccionados.append(prod)
                    productos_ids_usados.add(id(prod))
        
        if len(seleccionados) >= num_items:
            return seleccionados[:num_items]
    
    # Agrupar por categoría
    por_categoria: Dict[str, List[Dict[str, Any]]] = {}
    for p in productos:
        cat = p.get("categoria", "Otros")
        if cat not in por_categoria:
            por_categoria[cat] = []
        por_categoria[cat].append(p)
    
    if not seleccionados:
        primer_prod = random.choice(productos)
        seleccionados.append(primer_prod)
        productos_ids_usados.add(id(primer_prod))
    
    intentos = 0
    max_intentos = num_items * 10  # Evitar loops infinitos
    
    while len(seleccionados) < num_items and intentos < max_intentos:
        intentos += 1
        
        # Decidir si aplicar asociación o selección aleatoria
        if random.random() < probabilidad_asociacion and seleccionados:
            # Tomar el último producto y buscar uno relacionado
            ultimo = seleccionados[-1]
            cat_ultimo = ultimo.get("categoria", "Otros")
            
            # Buscar categorías relacionadas
            categorias_candidatas = []
            for cat1, cat2, prob in CATEGORIAS_RELACIONADAS:
                if cat1 == cat_ultimo and random.random() < prob:
                    categorias_candidatas.append(cat2)
            
            # Si hay categorías candidatas, seleccionar una
            if categorias_candidatas:
                cat_relacionada = random.choice(categorias_candidatas)
                if cat_relacionada in por_categoria:
                    candidatos = [p for p in por_categoria[cat_relacionada] 
                                  if id(p) not in productos_ids_usados]
                    if candidatos:
                        nuevo = random.choice(candidatos)
                        seleccionados.append(nuevo)
                        productos_ids_usados.add(id(nuevo))
                        continue
        
        # Selección aleatoria si no se aplicó asociación
        candidatos = [p for p in productos if id(p) not in productos_ids_usados]
        if candidatos:
            nuevo = random.choice(candidatos)
            seleccionados.append(nuevo)
            productos_ids_usados.add(id(nuevo))
    
    return seleccionados


def distribuir_productos_entre_catalogos(
    productos_universo: List[Dict[str, Any]],
    p_mssql: float = 0.90,
    p_mysql: float = 0.85,
    p_supabase: float = 0.75,
    p_mongo: float = 0.70,
    p_neo4j: float = 0.80,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Distribuye el universo de productos entre los diferentes catálogos.
    
    GARANTIZA que cada producto esté en al menos una fuente con SKU recuperable:
    - MSSQL (siempre tiene SKU)
    - Neo4j (siempre tiene SKU + codigo_alt + codigo_mongo)
    - Supabase con SKU no vacío
    - MongoDB con equivalencias.sku
    """
    productos_mssql: List[Dict[str, Any]] = []
    productos_mysql: List[Dict[str, Any]] = []
    productos_supabase: List[Dict[str, Any]] = []
    productos_mongo: List[Dict[str, Any]] = []
    productos_neo4j: List[Dict[str, Any]] = []

    for prod in productos_universo:
        # Track if this product will have SKU in at least one source
        has_sku_source = False
        
        # Decide distribution for each source
        in_mssql = random.random() < p_mssql
        in_mysql = random.random() < p_mysql
        in_supabase = random.random() < p_supabase
        in_mongo = random.random() < p_mongo
        in_neo4j = random.random() < p_neo4j
        
        # Determine if Supabase will have SKU (90% chance if in Supabase)
        supabase_has_sku = in_supabase and random.random() >= 0.1
        
        # Determine if Mongo will have equivalencias.sku (70% chance if in Mongo)
        mongo_has_sku = in_mongo and random.random() < 0.7
        
        # Check if any source will have SKU
        has_sku_source = in_mssql or in_neo4j or supabase_has_sku or mongo_has_sku
        
        # If no source has SKU, force at least one (prefer MSSQL, then Neo4j)
        if not has_sku_source:
            # Force into MSSQL or Neo4j (both always have SKU)
            if random.random() < 0.7:
                in_mssql = True
            else:
                in_neo4j = True
        
        # MSSQL: sku, nombre, categoria
        if in_mssql:
            productos_mssql.append(
                {
                    'sku': prod['sku'],
                    'nombre': prod['nombre'],
                    'categoria': prod['categoria'],
                }
            )

        # MySQL: codigo_alt, nombre, categoria
        if in_mysql:
            productos_mysql.append(
                {
                    'codigo_alt': prod['codigo_alt'],
                    'nombre': prod['nombre'],
                    'categoria': prod['categoria'],
                }
            )

        # Supabase: sku (sometimes empty), nombre, categoria
        if in_supabase:
            sku_value = prod['sku'] if supabase_has_sku else ''
            productos_supabase.append(
                {
                    'producto_id': str(uuid4()),
                    'sku': sku_value,
                    'nombre': prod['nombre'],
                    'categoria': prod['categoria'],
                }
            )

        # Mongo: codigo_mongo, nombre, categoria, equivalencias
        if in_mongo:
            equivalencias = {
                'codigo_alt': prod['codigo_alt']
            }
            if mongo_has_sku:
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
        if in_neo4j:
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
    # Start 2 years ago (within the 3-year BCCR exchange rate history)
    start = datetime.now() - timedelta(days=2*365)
    # Use yesterday as the end date to avoid future orders that won't match DimTiempo
    end = datetime.now().replace(hour=23, minute=59, second=59) - timedelta(days=1)
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
        
        # Seleccionar productos con patrones de asociación
        productos_orden = seleccionar_productos_con_asociacion(productos, num_items)
        
        for prod in productos_orden:
            prod_idx = codigo_to_idx.get(prod["codigo_alt"], 1)
            cantidad = random.randint(1, 5)
            precio = round(random.uniform(5, 500), 2)
            total_decimal += cantidad * precio
            # MySQL: precios como string con formatos variados (comas/puntos)
            fmt_choice = random.random()
            if fmt_choice < 0.33:
                # Formato con coma decimal (europeo): "500,32"
                precio_str = f"{precio:.2f}".replace(".", ",")
            elif fmt_choice < 0.66:
                # Formato con punto decimal y coma de miles: "1,500.32"
                precio_str = f"{precio:,.2f}"
            else:
                # Formato simple con punto decimal: "500.32"
                precio_str = f"{precio:.2f}"
            order_details.append({
                "orden_id": i,
                "producto_id": prod_idx,
                "cantidad": cantidad,
                "precio_unit": precio_str,
                "codigo_alt": prod["codigo_alt"],
            })
        if moneda == "CRC":
            total_decimal *= 540
        # MySQL: totales como string con formatos variados (comas/puntos)
        fmt_choice = random.random()
        if fmt_choice < 0.33:
            # Formato con coma decimal (europeo): "1234,56"
            total_str = f"{total_decimal:.2f}".replace(".", ",")
        elif fmt_choice < 0.66:
            # Formato con punto decimal y coma de miles: "1,234.56"
            total_str = f"{total_decimal:,.2f}"
        else:
            # Formato simple con punto decimal: "1234.56"
            total_str = f"{total_decimal:.2f}"
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
        
        # Seleccionar productos con patrones de asociación
        productos_orden = seleccionar_productos_con_asociacion(productos, num_items)
        
        for prod in productos_orden:
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
    """Generate optimized MySQL SQL using multi-row INSERTs."""
    BATCH_SIZE = 500  # MySQL handles up to 1000 rows per INSERT
    
    lines: List[str] = [
        "SET NAMES utf8mb4;",
        "SET CHARACTER SET utf8mb4;",
        "SET character_set_connection=utf8mb4;",
        "",
        "USE DB_SALES;",
        "",
        "-- Disable checks for faster inserts",
        "SET FOREIGN_KEY_CHECKS = 0;",
        "SET UNIQUE_CHECKS = 0;",
        "SET AUTOCOMMIT = 0;",
        ""
    ]
    
    # Batch insert Clientes
    for i in range(0, len(clientes), BATCH_SIZE):
        batch = clientes[i:i + BATCH_SIZE]
        values = []
        for c in batch:
            nombre = c["nombre"].replace("'", "''")
            correo = c["correo"].replace("'", "''")
            pais = c["pais"].replace("'", "''")
            values.append(f"('{nombre}', '{correo}', '{c['genero']}', '{pais}', '{c['created_at']}')")
        lines.append("INSERT INTO Cliente (nombre, correo, genero, pais, created_at) VALUES")
        lines.append(",\n".join(values) + ";")
    lines.append("")
    
    # Batch insert Productos
    for i in range(0, len(productos), BATCH_SIZE):
        batch = productos[i:i + BATCH_SIZE]
        values = []
        for p in batch:
            nombre = p["nombre"].replace("'", "''")
            categoria = p["categoria"].replace("'", "''")
            values.append(f"('{p['codigo_alt']}', '{nombre}', '{categoria}')")
        lines.append("INSERT INTO Producto (codigo_alt, nombre, categoria) VALUES")
        lines.append(",\n".join(values) + ";")
    lines.append("")
    
    # Batch insert Ordenes
    for i in range(0, len(orders), BATCH_SIZE):
        batch = orders[i:i + BATCH_SIZE]
        values = []
        for o in batch:
            values.append(f"({o['cliente_id']}, '{o['fecha']}', '{o['canal']}', '{o['moneda']}', '{o['total']}')")
        lines.append("INSERT INTO Orden (cliente_id, fecha, canal, moneda, total) VALUES")
        lines.append(",\n".join(values) + ";")
    lines.append("")
    
    # Batch insert OrdenDetalle
    for i in range(0, len(details), BATCH_SIZE):
        batch = details[i:i + BATCH_SIZE]
        values = []
        for d in batch:
            precio = d["precio_unit"].replace("'", "''")
            values.append(f"({d['orden_id']}, {d['producto_id']}, {d['cantidad']}, '{precio}')")
        lines.append("INSERT INTO OrdenDetalle (orden_id, producto_id, cantidad, precio_unit) VALUES")
        lines.append(",\n".join(values) + ";")
    
    lines.append("")
    lines.append("-- Re-enable checks and commit")
    lines.append("SET FOREIGN_KEY_CHECKS = 1;")
    lines.append("SET UNIQUE_CHECKS = 1;")
    lines.append("COMMIT;")
    lines.append("SET AUTOCOMMIT = 1;")
    
    path.write_text("\n".join(lines), encoding="utf-8")


def write_mssql_sql(clientes, productos, orders, details, path: Path) -> None:
    """Generate optimized MSSQL SQL using multi-row INSERTs."""
    BATCH_SIZE = 500  # MSSQL supports up to 1000 rows per INSERT
    
    lines: List[str] = ["USE DB_SALES;", "GO", ""]
    
    # Batch insert Clientes
    for i in range(0, len(clientes), BATCH_SIZE):
        batch = clientes[i:i + BATCH_SIZE]
        values = []
        for c in batch:
            nombre = c["Nombre"].replace("'", "''")
            email = c["Email"].replace("'", "''")
            pais = c["Pais"].replace("'", "''")
            values.append(f"(N'{nombre}', N'{email}', N'{c['Genero']}', N'{pais}', '{c['FechaRegistro']}')")
        lines.append("INSERT INTO dbo.Cliente (Nombre, Email, Genero, Pais, FechaRegistro) VALUES")
        lines.append(",\n".join(values) + ";")
    lines.append("GO\n")
    
    # Batch insert Productos
    for i in range(0, len(productos), BATCH_SIZE):
        batch = productos[i:i + BATCH_SIZE]
        values = []
        for p in batch:
            nombre = p["nombre"].replace("'", "''")
            categoria = p["categoria"].replace("'", "''")
            values.append(f"(N'{p['sku']}', N'{nombre}', N'{categoria}')")
        lines.append("INSERT INTO dbo.Producto (SKU, Nombre, Categoria) VALUES")
        lines.append(",\n".join(values) + ";")
    lines.append("GO\n")
    
    # Batch insert Ordenes
    for i in range(0, len(orders), BATCH_SIZE):
        batch = orders[i:i + BATCH_SIZE]
        values = []
        for o in batch:
            values.append(f"({o['ClienteId']}, '{o['Fecha']}', N'{o['Canal']}', '{o['Moneda']}', {o['Total']})")
        lines.append("INSERT INTO dbo.Orden (ClienteId, Fecha, Canal, Moneda, Total) VALUES")
        lines.append(",\n".join(values) + ";")
    lines.append("GO\n")
    
    # Batch insert OrdenDetalle
    for i in range(0, len(details), BATCH_SIZE):
        batch = details[i:i + BATCH_SIZE]
        values = []
        for d in batch:
            descuento = "NULL" if d["DescuentoPct"] is None else f"{d['DescuentoPct']}"
            values.append(f"({d['OrdenId']}, {d['ProductoId']}, {d['Cantidad']}, {d['PrecioUnit']}, {descuento})")
        lines.append("INSERT INTO dbo.OrdenDetalle (OrdenId, ProductoId, Cantidad, PrecioUnit, DescuentoPct) VALUES")
        lines.append(",\n".join(values) + ";")
    lines.append("GO")
    
    path.write_text("\n".join(lines), encoding="utf-8")


def generate_orders_supabase(num_orders: int, clientes: List[Dict[str, Any]], productos: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    orders: List[Dict[str, Any]] = []
    details: List[Dict[str, Any]] = []
    dates = _sample_order_dates(num_orders)
    canales = ["WEB", "APP", "PARTNER"]

    for c in clientes:
        c.setdefault('cliente_id', str(uuid4()))
    for p in productos:
        p.setdefault('producto_id', str(uuid4()))

    for fecha in dates:
        cliente = random.choice(clientes)
        orden_id = str(uuid4())
        moneda = random.choice(["USD", "CRC"])
        num_items = random.randint(1, 5)
        total = 0.0

        # Seleccionar productos con patrones de asociación
        productos_orden = seleccionar_productos_con_asociacion(productos, num_items)

        for prod in productos_orden:
            cantidad = random.randint(1, 5)
            precio = round(random.uniform(5, 500), 2)
            total += cantidad * precio
            details.append(
                {
                    "orden_detalle_id": str(uuid4()),
                    "orden_id": orden_id,
                    "producto_id": prod['producto_id'],
                    "cantidad": cantidad,
                    "precio_unit": round(precio, 2),
                }
            )

        orders.append(
            {
                "orden_id": orden_id,
                "cliente_id": cliente['cliente_id'],
                "fecha": fecha.isoformat(),
                "canal": random.choice(canales),
                "moneda": moneda,
                "total": round(total, 2),
            }
        )

    return orders, details


def write_supabase_sql(clientes, productos, orders, details, path: Path) -> None:
    def write_copy_section(fh, statement: str, rows: List[List[Any]]) -> None:
        fh.write(statement + "\n")
        if rows:
            buffer = StringIO()
            writer = csv.writer(buffer, quoting=csv.QUOTE_MINIMAL, lineterminator="\n")
            for row in rows:
                normalized = ["\\N" if value is None else value for value in row]
                writer.writerow(normalized)
            fh.write(buffer.getvalue())
        fh.write("\\.\n\n")

    cliente_rows = [
        [
            c['cliente_id'],
            c['nombre'],
            c.get('email') or '',
            c['genero'],
            c['pais'],
            c['fecha_registro'],
        ]
        for c in clientes
    ]

    producto_rows = [
        [
            p['producto_id'],
            p['sku'] or None,
            p['nombre'],
            p['categoria'],
        ]
        for p in productos
    ]

    orden_rows = [
        [
            o['orden_id'],
            o['cliente_id'],
            o['fecha'],
            o['canal'],
            o['moneda'],
            f"{o['total']:.2f}",
        ]
        for o in orders
    ]

    detalle_rows = [
        [
            d['orden_detalle_id'],
            d['orden_id'],
            d['producto_id'],
            d['cantidad'],
            f"{d['precio_unit']:.2f}",
        ]
        for d in details
    ]

    with path.open('w', encoding='utf-8', newline='\n') as fh:
        write_copy_section(
            fh,
            "COPY cliente (cliente_id, nombre, email, genero, pais, fecha_registro) FROM STDIN WITH (FORMAT csv, NULL '\\N');",
            cliente_rows,
        )
        write_copy_section(
            fh,
            "COPY producto (producto_id, sku, nombre, categoria) FROM STDIN WITH (FORMAT csv, NULL '\\N');",
            producto_rows,
        )
        write_copy_section(
            fh,
            "COPY orden (orden_id, cliente_id, fecha, canal, moneda, total) FROM STDIN WITH (FORMAT csv, NULL '\\N');",
            orden_rows,
        )
        write_copy_section(
            fh,
            "COPY orden_detalle (orden_detalle_id, orden_id, producto_id, cantidad, precio_unit) FROM STDIN WITH (FORMAT csv, NULL '\\N');",
            detalle_rows,
        )


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
        
        # Seleccionar productos con patrones de asociación
        productos_orden = seleccionar_productos_con_asociacion(productos, num_items)
        
        for prod in productos_orden:
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
        
        # Seleccionar productos con patrones de asociación
        productos_orden = seleccionar_productos_con_asociacion(productos, num_items)
        
        for prod in productos_orden:
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
    """Generate optimized Cypher using UNWIND with smaller batches for better performance."""
    BATCH_SIZE = 200  # Smaller batches to avoid parser overload
    
    def escape_cypher(s: str) -> str:
        """Escape strings for Cypher - backslash first, then quotes."""
        return s.replace("\\", "\\\\").replace("'", "\\'")
    
    def to_cypher_map(d: Dict[str, Any]) -> str:
        """Convert a Python dict to Cypher map literal syntax."""
        parts = []
        for k, v in d.items():
            if isinstance(v, str):
                parts.append(f"{k}: '{escape_cypher(v)}'")
            elif isinstance(v, (int, float)):
                parts.append(f"{k}: {v}")
            elif v is None:
                parts.append(f"{k}: null")
            else:
                parts.append(f"{k}: '{escape_cypher(str(v))}'")
        return "{" + ", ".join(parts) + "}"
    
    def to_cypher_list(items: List[Dict[str, Any]]) -> str:
        """Convert a list of dicts to Cypher list of maps."""
        return "[" + ", ".join(to_cypher_map(item) for item in items) + "]"
    
    lines: List[str] = []
    
    # Create indexes first for faster MATCH operations
    lines.append("// Create indexes for faster lookups")
    lines.append("CREATE INDEX cliente_id IF NOT EXISTS FOR (c:Cliente) ON (c.id);")
    lines.append("CREATE INDEX producto_sku IF NOT EXISTS FOR (p:Producto) ON (p.sku);")
    lines.append("CREATE INDEX orden_id IF NOT EXISTS FOR (o:Orden) ON (o.id);")
    lines.append("CREATE INDEX categoria_nombre IF NOT EXISTS FOR (cat:Categoria) ON (cat.nombre);")
    lines.append("")
    
    # Batch insert Clientes using UNWIND in smaller batches
    lines.append("// Insert Clientes in batches")
    cliente_data = [
        {"id": c["id"], "nombre": c["nombre"], "genero": c["genero"], "pais": c["pais"]}
        for c in clientes
    ]
    for i in range(0, len(cliente_data), BATCH_SIZE):
        batch = cliente_data[i:i + BATCH_SIZE]
        lines.append(f"UNWIND {to_cypher_list(batch)} AS c")
        lines.append("CREATE (:Cliente {id: c.id, nombre: c.nombre, genero: c.genero, pais: c.pais});")
    lines.append("")
    
    # Batch insert Categorias (small list, no need to batch)
    lines.append("// Insert Categorias")
    categorias = sorted(set(p["categoria"] for p in productos))
    categoria_data = [{"id": f"CAT-{i:03d}", "nombre": cat} for i, cat in enumerate(categorias, start=1)]
    lines.append(f"UNWIND {to_cypher_list(categoria_data)} AS cat")
    lines.append("CREATE (:Categoria {id: cat.id, nombre: cat.nombre});")
    lines.append("")
    
    # Batch insert Productos with relationship to Categoria
    lines.append("// Insert Productos in batches with PERTENECE_A relationship")
    producto_data = [
        {
            "id": p["sku"],
            "nombre": p["nombre"],
            "categoria": p["categoria"],
            "sku": p["sku"],
            "codigo_alt": p["codigo_alt"],
            "codigo_mongo": p["codigo_mongo"]
        }
        for p in productos
    ]
    for i in range(0, len(producto_data), BATCH_SIZE):
        batch = producto_data[i:i + BATCH_SIZE]
        lines.append(f"UNWIND {to_cypher_list(batch)} AS p")
        lines.append("MATCH (cat:Categoria {nombre: p.categoria})")
        lines.append("CREATE (prod:Producto {id: p.id, nombre: p.nombre, categoria: p.categoria, sku: p.sku, codigo_alt: p.codigo_alt, codigo_mongo: p.codigo_mongo})-[:PERTENECE_A]->(cat);")
    lines.append("")
    
    # Batch insert Ordenes with REALIZO relationship
    lines.append("// Insert Ordenes in batches with REALIZO relationship")
    orden_data = [
        {
            "id": o["id"],
            "cliente_id": o["cliente_id"],
            "fecha": o["fecha"].isoformat(),
            "canal": o["canal"],
            "moneda": o["moneda"],
            "total": o["total"]
        }
        for o in orders
    ]
    for i in range(0, len(orden_data), BATCH_SIZE):
        batch = orden_data[i:i + BATCH_SIZE]
        lines.append(f"UNWIND {to_cypher_list(batch)} AS o")
        lines.append("MATCH (c:Cliente {id: o.cliente_id})")
        lines.append("CREATE (c)-[:REALIZO]->(:Orden {id: o.id, fecha: datetime(o.fecha), canal: o.canal, moneda: o.moneda, total: o.total});")
    lines.append("")
    
    # Batch insert CONTIENE relationships
    lines.append("// Insert CONTIENE relationships in batches")
    rel_data = [
        {
            "orden_id": r["orden_id"],
            "producto_sku": r["producto_sku"],
            "cantidad": r["cantidad"],
            "precio_unit": r["precio_unit"]
        }
        for r in rels
    ]
    for i in range(0, len(rel_data), BATCH_SIZE):
        batch = rel_data[i:i + BATCH_SIZE]
        lines.append(f"UNWIND {to_cypher_list(batch)} AS r")
        lines.append("MATCH (o:Orden {id: r.orden_id}), (p:Producto {sku: r.producto_sku})")
        lines.append("CREATE (o)-[:CONTIENE {cantidad: r.cantidad, precio_unit: r.precio_unit}]->(p);")
    
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    num_clientes_total = 3000
    num_productos_universo = 500  # Total products with partial overlap between DBs
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
