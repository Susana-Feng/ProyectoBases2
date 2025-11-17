from pprint import pprint
import pandas as pd
from sqlalchemy import text
from configs.connections import get_dw_engine
from datetime import datetime

engine = get_dw_engine()

''' -----------------------------------------------------------------------
            Queries de SQL para transformación de datos de MongoDB
    ----------------------------------------------------------------------- ''' 

query_insert_map_producto = """
    INSERT INTO stg.map_producto(
        source_system, 
        source_code, 
        sku_oficial, 
        nombre_norm, 
        categoria_norm, 
        es_servicio )
    VALUES (
        :source_system, 
        :source_code,
        :sku_oficial, 
        :nombre_norm, 
        :categoria_norm, 
        :es_servicio );
"""

query_select_map_producto_sku = """
    SELECT TOP 1
        sku_oficial AS SKU
    FROM 
        stg.map_producto 
    ORDER BY 
        map_id DESC
"""

query_insert_orden_item_stg = """
    INSERT INTO stg.orden_items(
        source_system, 
        source_key_orden, 
        source_key_item, 
        source_code_prod,
        cliente_key,
        fecha_raw,
        canal_raw,
        moneda,
        cantidad_raw,
        precio_unit_raw,
        total_raw,
        fecha_dt ,
        cantidad_num,
        precio_unit_num,
        total_num   )
    VALUES (
        :source_system, 
        :source_key_orden,
        :source_key_item,
        :source_code_prod,
        :cliente_key,
        :fecha_raw,
        :canal_raw,
        :moneda,
        :cantidad_raw,
        :precio_unit_raw,
        :total_raw,
        :fecha_dt,
        :cantidad_num,
        :precio_unit_num,
        :total_num  )
"""

query_insert_clientes_stg = """
    INSERT INTO stg.clientes(
        source_system ,
        source_code,
        cliente_email,
        cliente_nombre,
        genero_raw,
        pais_raw,
        fecha_creado_raw,
        fecha_creado_dt,
        genero_norm )
    VALUES (
        :source_system, 
        :source_code,
        :cliente_email, 
        :cliente_nombre, 
        :genero_raw, 
        :pais_raw,
        :fecha_creado_raw,
        :fecha_creado_dt,
        :genero_norm );
"""

''' -----------------------------------------------------------------------
            Funciones de preparacion de datos para staging de MongoDB
    ----------------------------------------------------------------------- ''' 


def find_sku():

    result = (pd.read_sql(query_select_map_producto_sku, engine))['SKU'].iloc[0] #convertir a dataframe y obtener valor de SKU
    sku = int(result.split('SKU')[1]) + 1 #obtener siguiente numero de SKU
    sku = 'SKU' + str(sku).zfill(4) # Cambiar formato a SKUxxxx
    
    return sku

def insert_map_producto(codigo_original, sku_nueva, nombre, categoria):

    # SKU puede estar vacío, obtener uno existente si es así
    if not sku_nueva:
        sku_nueva = find_sku()

    with engine.connect() as conn:
        result = conn.execute(text(query_insert_map_producto), {
                    'source_system': 'mongo',
                    'source_code': codigo_original,
                    'sku_oficial': sku_nueva,
                    'nombre_norm': nombre,
                    'categoria_norm': categoria,
                    'es_servicio': False # Mongo solo tiene productos físicos
                })
                
        conn.commit()

def flatten_items(orden, items_flat):

    id_orden = str(orden.get('_id')) # ObjectId → string
    cliente_id = orden.get('cliente_id')
    fecha_orden = orden.get('fecha')
    canal = orden.get('canal')
    moneda = orden.get('moneda')
    total = orden.get('total')
    items = orden.get('items', [])
    metadatos = orden.get('metadatos', {})

    for i in items: # estableciendo relación 1 a N de ordenes con items separados

        items_flat.append({
            'orden_id': id_orden,
            'cliente_id': cliente_id,
            'fecha': fecha_orden,
            'canal': canal,
            'moneda': moneda,
            'total_orden': total,
            'producto_id': i.get('producto_id'),
            'cantidad': i.get('cantidad'),
            'precio_unitario': i.get('precio_unit'),
            'metadatos': metadatos })

def insert_orden_items_stg(items_flat):

    for i in items_flat:

        fecha_dt = i.get('fecha').date()   # Convierte datetime a date, Formato fechas: YYYY-MM-DD
        cantidad_num = float(i.get('cantidad'))     #Formato numeros: DECIMAL
        precio_unit_num = float(i.get('precio_unitario'))
        total_num = float(i.get('total_orden'))

        with engine.connect() as conn:
            conn.execute(text(query_insert_orden_item_stg), {
                    'source_system': 'mongo',
                    'source_key_orden': i.get('orden_id'),
                    'source_key_item': i.get('producto_id'),
                    'source_code_prod': i.get('producto_id'),
                    'cliente_key': i.get('cliente_id'),
                    'fecha_raw': i.get('fecha'),
                    'canal_raw': i.get('canal'),
                    'moneda': i.get('moneda'),
                    'cantidad_raw': i.get('cantidad'),
                    'precio_unit_raw': i.get('precio_unitario'),
                    'total_raw': i.get('total_orden'),
                    'fecha_dt': fecha_dt,
                    'cantidad_num': cantidad_num,
                    'precio_unit_num': precio_unit_num,
                    'total_num': total_num
                })
            conn.commit()

def insert_clientes_stg(clientes):

    for cliente in clientes:
        source_code = str(cliente.get('_id'))  # ObjectId → string
        fecha_creado_nuevo = cliente.get('creado').date()  # Convierte datetime a date, Formato fechas: YYYY-MM-DD
        genero_raw = cliente.get('genero')

        if genero_raw == 'Otro': # Mongo utiliza nombres estandarizados excepto para 'Otro'
            genero_nuevo= 'No especificado'
        else:
            genero_nuevo= genero_raw

        with engine.connect() as conn:
            conn.execute(text(query_insert_clientes_stg),{ 
                    'source_system': 'mongo',
                    'source_code': source_code,
                    'cliente_email': cliente.get('email'),
                    'cliente_nombre': cliente.get('nombre'),
                    'genero_raw': genero_raw,
                    'pais_raw': cliente.get('pais'),
                    'fecha_creado_raw': cliente.get('creado'),
                    'fecha_creado_dt': fecha_creado_nuevo,
                    'genero_norm': genero_nuevo
                })
            conn.commit()

''' -----------------------------------------------------------------------
            Función principal de transformación de datos de MongoDB
    ----------------------------------------------------------------------- ''' 

def transform_mongo(productos, clientes, ordenes):

    for producto in productos:
        codigo_original = producto.get('codigo_mongo')
        sku_nueva = producto.get('equivalencias', {}).get('sku')
        nombre = producto.get('nombre')
        categoria = producto.get('categoria')

        insert_map_producto(codigo_original, sku_nueva, nombre, categoria)
    
    items_flat = []
    for orden in ordenes:
        flatten_items(orden, items_flat) # 'normalizar' items en ordenes
    
    insert_orden_items_stg(items_flat) 
    insert_clientes_stg(clientes)
    
