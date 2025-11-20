import pandas as pd
from datetime import datetime
from sqlalchemy import text
from configs.connections import get_dw_engine
from association_rules.get_rules import generar_reglas_asociacion

engine = get_dw_engine()


query_insert = """
    INSERT INTO analytics.AssociationRules 
    (Antecedent, Consequent, Support, Confidence, Lift, GeneratedAt)
    VALUES 
    (:Antecedent, :Consequent, :Support, :Confidence, :Lift, :GeneratedAt)
"""

query_delete = """
    DELETE FROM analytics.AssociationRules
"""

def limpiar_reglas():
    with engine.begin() as conn:
        conn.execute(text(query_delete))

def preparar_datos_para_insercion(rules):
    #Prepara los datos en formato de diccionarios para inserción
    
    if rules.empty:
        print("⚠️ No hay reglas para preparar")
        return []
    
    datos_para_insertar = []
    
    for index, row in rules.iterrows():
        dato = {
            'Antecedent': ', '.join(sorted(list(row['antecedents']))),
            'Consequent': ', '.join(sorted(list(row['consequents']))),
            'Support': float(row['support']),
            'Confidence': float(row['confidence']),
            'Lift': float(row['lift']),
            'GeneratedAt': datetime.now()
        }
        datos_para_insertar.append(dato)

    return datos_para_insertar

def insertar_reglas_sql(datos_para_insertar):
    if not datos_para_insertar:
        print("⚠️ No hay datos para insertar")
        return
    
    try:
        registros_insertados = 0
        with engine.connect() as conn:
            for dato in datos_para_insertar:
                conn.execute(text(query_insert), dato)
                conn.commit()
                registros_insertados += 1
                    
    except Exception as e:
        print(f"❌ Error al insertar: {str(e)}")


def carga_reglas_asociacion():
    """Función principal"""    

    # Limpiar tabla de reglas existentes
    limpiar_reglas()

    # Obtener reglas
    rules = generar_reglas_asociacion()
    
    if rules.empty:
        print("❌ No se generaron reglas de asociación.")
        return

    # Preparar datos para inserción
    datos_para_insertar = preparar_datos_para_insercion(rules)
    
    if not datos_para_insertar:
        print("❌ No se pudieron preparar los datos.")
        return

    # Insertar en SQL
    insertar_reglas_sql(datos_para_insertar)
    
    print("Reglas de asociación procesadas correctamente.")
