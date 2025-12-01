from mlxtend.frequent_patterns import fpgrowth, association_rules
import pandas as pd
from configs.connections import get_dw_engine


engine = get_dw_engine()

# Parámetros del algoritmo
# MIN_SUPPORT: Un itemset debe aparecer en al menos este % de transacciones
# Con datos generados, necesitamos un soporte muy bajo para encontrar patrones
MIN_SUPPORT = 0.0005  # 0.05% = ~3 transacciones en 5000
MIN_CONFIDENCE = 0.05  # confianza mínima (5%) - bajo para datos generados
MIN_ITEM_FREQUENCY = 3  # Productos que aparecen en menos de N transacciones se ignoran

# Only get transactions with 2+ items for meaningful association rules
query_get_transactions = """
    SELECT transaction_id, item
    FROM dw.vw_Transacciones
    WHERE LEN(item) - LEN(REPLACE(item, ',', '')) >= 1
"""


def cargar_datos():
    return pd.read_sql(query_get_transactions, engine)


def transformar_a_one_hot(df):
    """Transforma la lista (transaction_id, item) a formato one-hot:
    una fila por transacción, una columna por ítem, 1 si aparece, 0 si no.
    Filtra productos poco frecuentes para reducir uso de memoria.
    """

    # Paso 1: Explotar los items que vienen como strings separados por comas
    df_exploded = df.assign(item=df["item"].str.split(", ")).explode("item")
    
    # Filtrar items vacíos
    df_exploded = df_exploded[df_exploded["item"].str.strip() != ""]
    
    # Paso 2: Filtrar productos poco frecuentes (reducir dimensionalidad)
    item_counts = df_exploded["item"].value_counts()
    frequent_items = item_counts[item_counts >= MIN_ITEM_FREQUENCY].index
    df_exploded = df_exploded[df_exploded["item"].isin(frequent_items)]
    
    print(f"    Productos únicos después de filtrar: {len(frequent_items)}")
    print(f"    Transacciones después de filtrar: {df_exploded['transaction_id'].nunique()}")

    # Crear una tabla transacción x item usando sparse matrix
    basket = (
        df_exploded.groupby(["transaction_id", "item"])["item"]
        .count()
        .unstack()
        .fillna(0)
    )
    
    # Convertimos a bool (más eficiente en memoria)
    basket = basket.astype(bool)
    return basket


def generar_reglas_asociacion():
    try:
        print("\n=== Iniciando Generación de Reglas de Asociación ===")
        df = cargar_datos()
        
        if df.empty:
            print("❌ No hay transacciones con múltiples items para analizar")
            return None
            
        print(f"    Transacciones cargadas: {len(df)}")

        basket = transformar_a_one_hot(df)
        
        if basket.empty:
            print("❌ No hay datos suficientes después de filtrar")
            return None

        print(f"    Ejecutando FP-Growth con min_support={MIN_SUPPORT}...")
        # FP-Growth es más eficiente que Apriori para datasets grandes
        frequent_itemsets = fpgrowth(basket, min_support=MIN_SUPPORT, use_colnames=True)

        if frequent_itemsets.empty:
            print("❌ No se encontraron itemsets frecuentes. Intenta reducir MIN_SUPPORT.")
            return None

        # Agregar columna con el tamaño del itemset
        frequent_itemsets["length"] = frequent_itemsets["itemsets"].apply(len)
        print(f"    Itemsets frecuentes encontrados: {len(frequent_itemsets)}")

        print(f"    Generando reglas con min_confidence={MIN_CONFIDENCE}...")
        rules = association_rules(
            frequent_itemsets, metric="confidence", min_threshold=MIN_CONFIDENCE
        )

        if not rules.empty:
            print(f"\n=== {len(rules)} Reglas de asociación generadas ===")
            rules_to_show = rules[
                ["antecedents", "consequents", "support", "confidence", "lift"]
            ].head(20)
            print(rules_to_show)

            return rules
        else:
            print("No se encontraron reglas con los parámetros especificados.")
            return None
    except Exception as e:
        print(f"❌ Error en la generación de reglas de asociación: {e}")
        return None
