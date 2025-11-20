from mlxtend.frequent_patterns import apriori, association_rules
import pandas as pd
from configs.connections import get_dw_engine


engine = get_dw_engine()

# Parámetros del algoritmo
MIN_SUPPORT = 0.4     # soporte mínimo (40%)
MIN_CONFIDENCE = 0.6  # confianza mínima (60%)

query_get_transactions = """
    SELECT * 
    FROM
        dw.vw_Transacciones
"""  

def cargar_datos():
    return pd.read_sql(query_get_transactions, engine)


def transformar_a_one_hot(df):
    """Transforma la lista (transaction_id, item) a formato one-hot:
    una fila por transacción, una columna por ítem, 1 si aparece, 0 si no.
    """
    # Crear una tabla transacción x item
    basket = (
        df
        .groupby(['transaction_id', 'item'])['item']
        .count()
        .unstack()
        .fillna(0)
    )
    # Convertimos a 1/0
    #basket = basket.applymap(lambda x: 1 if x > 0 else 0)
    basket = basket.astype(bool)
    return basket

def generar_reglas_asociacion():
    try:
        print("\n=== Iniciando Generación de Reglas de Asociación ===")
        df = cargar_datos()
        basket = transformar_a_one_hot(df)

        print("\n=== Fase 1: Conjuntos frecuentes (Apriori con mlxtend) ===")
        frequent_itemsets = apriori(
            basket,
            min_support=MIN_SUPPORT,
            use_colnames=True
        )
        # Agregar columna con el tamaño del itemset para ordenar un poco
        frequent_itemsets['length'] = frequent_itemsets['itemsets'].apply(len)
        print(frequent_itemsets)

        print("\n=== Fase 2: Reglas de asociación ===")
        rules = association_rules(
            frequent_itemsets,
            metric="confidence",
            min_threshold=MIN_CONFIDENCE
        )

        # Seleccionamos solo algunas columnas para mostrar
        if not rules.empty:
            rules_to_show = rules[[
                'antecedents',
                'consequents',
                'support',
                'confidence',
                'lift'
            ]]
            print(rules_to_show)
        else:
            print("No se encontraron reglas con los parámetros especificados.")
    except Exception as e:
        print(f"❌ Error en la generación de reglas de asociación: {e}")