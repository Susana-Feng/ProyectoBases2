import signal
import sys

from extract.mongo import extract_mongo
from extract.mssql import extract_mssql
from extract.mysql import extract_mysql
from extract.supabase import extract_supabase
from extract.neo4j_ import extract_neo4j
from load.general import load_datawarehouse
from transform.mongo import transform_mongo
from transform.mssql import transform_mssql
from transform.mysql import transform_mysql
from transform.supabase import transform_supabase
from transform.neo4j import transform_Neo4j
from association_rules.load_rules import carga_reglas_asociacion

# Variable global para controlar interrupciones
interrupted = False


def signal_handler(sig, frame):
    """Maneja Ctrl+C de forma elegante"""
    global interrupted
    print("\n\n⚠️  Interrupción detectada (Ctrl+C). Finalizando proceso ETL...")
    interrupted = True
    sys.exit(0)


def check_interrupt():
    """Verifica si se solicitó interrumpir el proceso"""
    if interrupted:
        print("⚠️  Proceso interrumpido por el usuario")
        sys.exit(0)


def verificar_tipos_cambio():
    """
    Verifica si hay tipos de cambio cargados y si no, carga el histórico.
    """
    from sqlalchemy import text
    from configs.connections import get_dw_engine
    
    try:
        engine = get_dw_engine()
        with engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM stg.tipo_cambio"))
            count = result.fetchone()[0]
            
            if count == 0:
                print("\n⚠️  No hay tipos de cambio cargados.")
                print("   Ejecuta el job SQL Server 'BCCR_TipoCambio_Diario' o corre:")
                print("   EXEC DW_SALES.jobs.sp_BCCR_CargarTiposCambio @FechaInicio='2010-01-01', @FechaFinal=GETDATE();")
            else:
                print(f"\n✓ Tipos de cambio ya cargados: {count} registros")
    except Exception as e:
        print(f"⚠️  No se pudo verificar tipos de cambio: {e}")
        print("   Verifica la instancia de SQL Server antes de continuar...")


if __name__ == "__main__":
    # Configurar manejo de señales
    signal.signal(signal.SIGINT, signal_handler)

    print("=" * 60)
    print("INICIANDO PROCESO ETL")
    print("=" * 60)

    try:
        # ========== TIPOS DE CAMBIO ==========
        print("\n[0] VERIFICACIÓN DE TIPOS DE CAMBIO")
        print("-" * 60)
        verificar_tipos_cambio()
        check_interrupt()

        # ========== EXTRACCIÓN ==========
        print("\n[1] EXTRACCIÓN DE DATOS")
        print("-" * 60)

        # # Extraer datos de MongoDB
        # print("\n[MongoDB] Extrayendo datos...")
        # try:
        #     objetos_mongo = extract_mongo()
        #     check_interrupt()
        # except Exception as e:
        #     print(f"❌ Error extrayendo de MongoDB: {e}")
        #     import traceback

        #     traceback.print_exc()
        #     sys.exit(1)

        # Extraer datos de MS SQL Server
        print("\n[MS SQL Server] Extrayendo datos...")
        try:
            objetos_mssql = extract_mssql()
            check_interrupt()
        except Exception as e:
            print(f"❌ Error extrayendo de MS SQL Server: {e}")
            import traceback

            traceback.print_exc()
            sys.exit(1)

        # Extraer datos de MySQL
        print("\n[MySQL] Extrayendo datos...")
        try:
            objetos_mysql = extract_mysql()
            check_interrupt()
        except Exception as e:
            print(f"❌ Error extrayendo de MySQL: {e}")
            import traceback

            traceback.print_exc()
            sys.exit(1)

        # Extraer datos de Supabase
        # print("\n[Supabase] Extrayendo datos...")
        # try:
        #     objetos_supabase = extract_supabase()
        #     check_interrupt()
        # except Exception as e:
        #     print(f"❌ Error extrayendo de Supabase: {e}")
        #     import traceback

        #     traceback.print_exc()
        #     sys.exit(1)

        # Extraer datos de Neo4j
        print("\n[Neo4j] Extrayendo datos...")
        try:
            objetos_neo4j = extract_neo4j()
            check_interrupt()
        except Exception as e:
            print(f"❌ Error extrayendo de Supabase: {e}")
            import traceback

            traceback.print_exc()
            sys.exit(1)

        # ========== TRANSFORMACIÓN ==========
        # print("\n[2] TRANSFORMACIÓN DE DATOS")
        # print("-" * 60)

        # # Transformar datos de MongoDB
        # print("\n[MongoDB] Transformando datos...")
        # try:
        #     transform_mongo(objetos_mongo[0], objetos_mongo[1], objetos_mongo[2])
        #     check_interrupt()
        # except Exception as e:
        #     print(f"❌ Error transformando datos de MongoDB: {e}")
        #     import traceback

        #     traceback.print_exc()
        #     sys.exit(1)

        # Transformar datos de MS SQL Server
        print("\n[MS SQL Server] Transformando datos...")
        try:
            transform_mssql(
                objetos_mssql[0], objetos_mssql[1], objetos_mssql[2], objetos_mssql[3]
            )
            check_interrupt()
        except Exception as e:
            print(f"❌ Error transformando datos de MS SQL Server: {e}")
            import traceback

            traceback.print_exc()
            sys.exit(1)

        # Transformar datos de MySQL
        print("\n[MySQL] Transformando datos...")
        try:
            transform_mysql(
                objetos_mysql[0], objetos_mysql[1], objetos_mysql[2], objetos_mysql[3]
            )
            check_interrupt()
        except Exception as e:
            print(f"❌ Error transformando datos de MySQL: {e}")
            import traceback

            traceback.print_exc()
            sys.exit(1)

        # # Transformar datos de Supabase
        # print("\n[Supabase] Transformando datos...")
        # try:
        #     transform_supabase(objetos_supabase[2], objetos_supabase[0], objetos_supabase[1])
        #     check_interrupt()
        # except Exception as e:
        #     print(f"❌ Error transformando datos de Supabase: {e}")
        #     import traceback

        #     traceback.print_exc()
        #     sys.exit(1)

        # Transformar datos de Supabase
        print("\n[Neo4j] Transformando datos...")
        try:
            #print(objetos_neo4j["nodes"].get("Producto"))
            transform_Neo4j(objetos_neo4j["nodes"].get("Producto"), objetos_neo4j["nodes"].get("Cliente"), objetos_neo4j["relationships"].get("REALIZO"), objetos_neo4j["relationships"].get("CONTIENE"))
            check_interrupt()
        except Exception as e:
            print(f"❌ Error transformando datos de Neo4j: {e}")
            import traceback

            traceback.print_exc()
            sys.exit(1)

        # # ========== CARGA ==========
        print("\n[3] CARGA AL DATA WAREHOUSE")
        print("-" * 60)
        try:
            load_datawarehouse()
            check_interrupt()
        except Exception as e:
            print(f"❌ Error cargando al Data Warehouse: {e}")
            import traceback

            traceback.print_exc()
            sys.exit(1)

        print("\n" + "=" * 60)
        print("✅ PROCESO ETL COMPLETADO EXITOSAMENTE")
        print("=" * 60)

        # ========== REGLAS DE ASOCIACIÓN ==========
        carga_reglas_asociacion()



        # Nota: Los tipos de cambio se aplican mediante los jobs de SQL Server
        # Usa DW_SALES.jobs.sp_BCCR_CargarTiposCambio para reconstruir históricos

    except KeyboardInterrupt:
        print("\n\n⚠️  Proceso interrumpido por el usuario (Ctrl+C)")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n❌ Error inesperado en el proceso ETL: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


# Función para resetear el DataWarehouse (eliminar datos cargados de prueba)
def reset_datawarehouse():
    from sqlalchemy import text

    from configs.connections import get_dw_engine

    engine = get_dw_engine()
    sql = """
        DELETE FROM dw.FactVentas;
        DELETE FROM dw.DimProducto;
        DELETE FROM dw.DimCliente;
        DELETE FROM dw.DimTiempo;
        DELETE FROM stg.map_producto;
        DELETE FROM stg.orden_items;
        DELETE FROM stg.clientes;
        DELETE FROM stg.tipo_cambio;
    """

    with engine.begin() as conn:
        conn.execute(text(sql))


# Descomentar la siguiente línea para resetear el DataWarehouse
#reset_datawarehouse()
