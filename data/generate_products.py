import random
import string
from pathlib import Path
from typing import List, Dict, Any
import pandas as pd
from faker import Faker

# Directorios base
BASE_DIR = Path(__file__).parent
PRODUCTS_DIR = BASE_DIR / 'products'
SUPABASE_DIR = PRODUCTS_DIR / 'supabase'
MONGO_DIR = PRODUCTS_DIR / 'mongo'
NEO4J_DIR = PRODUCTS_DIR / 'neo4j'
MSSQL_DIR = PRODUCTS_DIR / 'mssql'
MYSQL_DIR = PRODUCTS_DIR / 'mysql'

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


# Crear directorios si no existen
for d in [SUPABASE_DIR, MONGO_DIR, NEO4J_DIR, MSSQL_DIR, MYSQL_DIR]:
    d.mkdir(parents=True, exist_ok=True)


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
    """
    Genera un nombre de producto realista en función de la categoría.
    Devuelve algo tipo:
    - 'Camiseta algodón básica Azul Talla M'
    - 'Arroz blanco 1 kg'
    - 'Smartphone gama media 128 GB'
    """
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

    # Otras categorías: dejar el nombre base tal cual para que no se vuelva demasiado largo
    return base

def generar_universo_productos(num_productos: int = 600) -> List[Dict[str, Any]]:
    """
    Genera un universo común de productos con:
    - sku:  SKU-1000, SKU-1001, ...
    - codigo_alt: ALT-AB12 (no coincide con sku)
    - codigo_mongo: MN-4000, MN-4001, ...
    - nombre y categoría coherentes entre sí
    """
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

# def generar_universo_productos(num_productos: int = 600) -> List[Dict[str, Any]]:
#     """
#     Genera un universo común de productos con:
#     - sku:  SKU-1000, SKU-1001, ...
#     - codigo_alt: ALT-AB12 (no coincide con sku)
#     - codigo_mongo: MN-4000, MN-4001, ...
#     """
#     fake = Faker('es_ES')
#     categorias = [
#         'Electrónica', 'Ropa', 'Hogar', 'Deportes',
#         'Libros', 'Juguetes', 'Automotriz', 'Salud',
#         'Alimentos', 'Oficina'
#     ]
#     productos = []
#     codigos_alt_usados: set = set()

#     for i in range(num_productos):
#         sku = f"SKU-{1000 + i}"
#         codigo_mongo = f"MN-{4000 + i}"
#         codigo_alt = generar_codigo_alt_unico(codigos_alt_usados)
#         nombre = fake.sentence(nb_words=3).rstrip('.')

#         producto = {
#             'sku': sku,
#             'codigo_alt': codigo_alt,
#             'codigo_mongo': codigo_mongo,
#             'nombre': nombre,
#             'categoria': random.choice(categorias),
#         }
#         productos.append(producto)

#     return productos


def distribuir_productos_entre_catalogos(
    productos_universo: List[Dict[str, Any]],
    p_mssql: float = 0.9,
    p_mysql: float = 0.9,
    p_supabase: float = 0.75,
    p_mongo: float = 0.65,
    p_neo4j: float = 0.85,
):
    """
    A partir de un universo común genera las listas específicas para cada catálogo,
    con solapamiento parcial controlado por probabilidades.
    """
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


def guardar_csv(datos: List[Dict[str, Any]], ruta: str) -> None:
    """Guarda una lista de diccionarios en un CSV."""
    df = pd.DataFrame(datos)
    df.to_csv(ruta, index=False)


def main(num_productos_universo: int = 600) -> None:
    print("Generando universo de productos...")
    universo = generar_universo_productos(num_productos_universo)

    (
        productos_mssql,
        productos_mysql,
        productos_supabase,
        productos_mongo,
        productos_neo4j,
    ) = distribuir_productos_entre_catalogos(universo)

    print(f"Universo total de productos: {len(universo)}")
    print(f"MSSQL   -> {len(productos_mssql)} filas")
    print(f"MySQL   -> {len(productos_mysql)} filas")
    print(f"Supabase-> {len(productos_supabase)} filas")
    print(f"Mongo   -> {len(productos_mongo)} filas")
    print(f"Neo4j   -> {len(productos_neo4j)} filas")

    # Guardar CSV para cada motor
    guardar_csv(productos_mssql, str(MSSQL_DIR / 'products_mssql.csv'))
    guardar_csv(productos_mysql, str(MYSQL_DIR / 'products_mysql.csv'))
    guardar_csv(productos_supabase, str(SUPABASE_DIR / 'products_supabase.csv'))
    guardar_csv(productos_mongo, str(MONGO_DIR / 'products_mongo.csv'))
    guardar_csv(productos_neo4j, str(NEO4J_DIR / 'products_neo4j.csv'))

    print("Generación de CSV de productos completada.")


if __name__ == '__main__':
    main()
