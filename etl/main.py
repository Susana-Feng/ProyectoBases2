import argparse
import signal
import sys
import warnings

from extract.mssql import extract_mssql
from extract.mysql import extract_mysql
from extract.supabase import extract_supabase
from extract.mongo import extract_mongo
from extract.neo4j import extract_neo4j
from equivalences import build_equivalence_map
from transform.mssql import transform_mssql
from transform.mysql import transform_mysql
from transform.supabase import transform_supabase
from transform.mongo import transform_mongo
from transform.neo4j import transform_Neo4j
from load.general import load_datawarehouse
from association_rules.load_rules import carga_reglas_asociacion

# Suppress SQLAlchemy SAWarning about unrecognized SQL Server versions
warnings.filterwarnings("ignore", message=".*Unrecognized server version info.*")
# Suppress Supabase deprecation warnings (internal library issue)
warnings.filterwarnings("ignore", category=DeprecationWarning, module="supabase")

SUPPORTED_DBS = {"mssql", "mysql", "supabase", "mongo", "neo4j"}
DEFAULT_DBS = ["mssql", "mysql", "supabase", "mongo", "neo4j"]

# Global variable to control interruptions
interrupted = False


def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully - just set the flag, don't exit immediately"""
    global interrupted
    if interrupted:
        # Second Ctrl+C - force exit
        print("\n\nForce quit (second Ctrl+C)")
        sys.exit(1)
    print("\n\nInterrupted (Ctrl+C). Finishing current operation...")
    interrupted = True


class InterruptedError(Exception):
    """Custom exception for clean interruption"""

    pass


def check_interrupt():
    """Check if interruption was requested and raise exception if so"""
    if interrupted:
        raise InterruptedError("Process interrupted by user")


def verificar_tipos_cambio():
    """Check if exchange rates are loaded, warn if not."""
    from sqlalchemy import text
    from configs.connections import get_dw_engine

    try:
        engine = get_dw_engine()
        with engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM stg.tipo_cambio"))
            count = result.fetchone()[0]

            if count == 0:
                print("    WARNING: No exchange rates loaded")
                print("    Run: EXEC DW_SALES.jobs.sp_BCCR_CargarTiposCambio")
                return 0
            else:
                return count
    except Exception as e:
        print(f"    Could not verify exchange rates: {e}")
        return -1


def get_max_existing_sku():
    """Get the highest SKU number already in stg.map_producto."""
    from sqlalchemy import text
    from configs.connections import get_dw_engine

    try:
        engine = get_dw_engine()
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT MAX(
                    CAST(
                        CASE 
                            WHEN SUBSTRING(sku_oficial, 4, 1) = '-' 
                                THEN SUBSTRING(sku_oficial, 5, LEN(sku_oficial))
                            ELSE SUBSTRING(sku_oficial, 4, LEN(sku_oficial))
                        END
                    AS INT)
                )
                FROM stg.map_producto
                WHERE sku_oficial LIKE 'SKU%'
            """))
            max_num = result.fetchone()[0]
            return max_num if max_num else 0
    except Exception:
        return 0


def parse_db_filters(raw_filters):
    if not raw_filters:
        return list(DEFAULT_DBS)

    selected = set()
    for chunk in raw_filters:
        for value in chunk.split(","):
            db = value.strip().lower()
            if not db:
                continue
            if db == "all":
                return sorted(SUPPORTED_DBS)
            if db not in SUPPORTED_DBS:
                raise ValueError(
                    f"Unknown source '{db}'. Valid options: {', '.join(sorted(SUPPORTED_DBS))}"
                )
            selected.add(db)

    return sorted(selected) if selected else list(DEFAULT_DBS)


def build_arg_parser():
    parser = argparse.ArgumentParser(
        description="ETL process for the sales Data Warehouse"
    )
    parser.add_argument(
        "--db",
        "-d",
        action="append",
        help=(
            "Data sources to process (can repeat or use commas). "
            "Example: --db mssql --db mysql,supabase. Use 'all' for all sources."
        ),
    )
    parser.add_argument(
        "--log-level",
        choices=["info", "debug"],
        default="info",
        help="Log level: 'info' (default) or 'debug' for verbose output.",
    )
    return parser


if __name__ == "__main__":
    arg_parser = build_arg_parser()
    try:
        cli_args = arg_parser.parse_args()
        selected_dbs = parse_db_filters(cli_args.db)
        debug_mode = cli_args.log_level == "debug"
    except ValueError as parse_err:
        print(f"Error: {parse_err}")
        sys.exit(1)

    # Configure signal handling
    signal.signal(signal.SIGINT, signal_handler)

    print(f"\nETL - Sources: {', '.join(selected_dbs)}")

    try:
        # ========== EXCHANGE RATES ==========
        print("\n[1] Exchange rates")
        count = verificar_tipos_cambio()
        if count > 0:
            print(f"    {count} records OK")
        check_interrupt()

        objetos_mssql = None
        objetos_mysql = None
        objetos_supabase = None
        objetos_mongo = None
        objetos_neo4j = None

        # ========== EXTRACTION ==========
        print("\n[2] Extraction")

        if "mssql" in selected_dbs:
            try:
                objetos_mssql = extract_mssql()
                check_interrupt()
            except InterruptedError:
                raise
            except Exception as e:
                if interrupted:
                    raise InterruptedError("MSSQL extraction interrupted")
                print(f"    Error extracting from MSSQL: {e}")
                import traceback

                traceback.print_exc()
                sys.exit(1)

        if "mysql" in selected_dbs:
            try:
                objetos_mysql = extract_mysql()
                check_interrupt()
            except InterruptedError:
                raise
            except Exception as e:
                if interrupted:
                    raise InterruptedError("MySQL extraction interrupted")
                print(f"    Error extracting from MySQL: {e}")
                import traceback

                traceback.print_exc()
                sys.exit(1)

        if "supabase" in selected_dbs:
            try:
                objetos_supabase = extract_supabase()
                check_interrupt()
            except InterruptedError:
                raise
            except Exception as e:
                if interrupted:
                    raise InterruptedError("Supabase extraction interrupted")
                print(f"    Error extracting from Supabase: {e}")
                import traceback

                traceback.print_exc()
                sys.exit(1)

        if "mongo" in selected_dbs:
            try:
                objetos_mongo = extract_mongo()
                check_interrupt()
            except InterruptedError:
                raise
            except Exception as e:
                if interrupted:
                    raise InterruptedError("MongoDB extraction interrupted")
                print(f"    Error extracting from MongoDB: {e}")
                import traceback

                traceback.print_exc()
                sys.exit(1)

        if "neo4j" in selected_dbs:
            try:
                objetos_neo4j = extract_neo4j()
                check_interrupt()
            except InterruptedError:
                raise
            except Exception as e:
                if interrupted:
                    raise InterruptedError("Neo4j extraction interrupted")
                print(f"    Error extracting from Neo4j: {e}")
                import traceback

                traceback.print_exc()
                sys.exit(1)

        # ========== EQUIVALENCES ==========
        # Build product equivalence map from ALL sources BEFORE transformation.
        # This ensures that SKUs are resolved correctly across all sources.
        print("\n[3] Building product equivalences")
        
        try:
            # Get the highest existing SKU to avoid duplicates
            max_sku = get_max_existing_sku()
            
            # Extract product lists from each source
            productos_mssql = objetos_mssql[1] if objetos_mssql else None
            productos_mysql = objetos_mysql[1] if objetos_mysql else None
            productos_supabase = objetos_supabase[1] if objetos_supabase else None
            productos_mongo = objetos_mongo[0] if objetos_mongo else None  # mongo returns (productos, clientes, ordenes)
            productos_neo4j = objetos_neo4j["nodes"].get("Producto", []) if objetos_neo4j else None
            
            # Build equivalence map
            eq_map = build_equivalence_map(
                productos_mssql=productos_mssql,
                productos_mysql=productos_mysql,
                productos_supabase=productos_supabase,
                productos_mongo=productos_mongo,
                productos_neo4j=productos_neo4j,
                existing_max_sku=max_sku,
                debug=debug_mode,
            )
            
            stats = eq_map.get_stats()
            print(f"    {stats['total_products']} unique products across all sources")
            print(f"    SKU sources: MSSQL={stats['sku_from']['mssql']}, Supabase={stats['sku_from']['supabase']}, "
                  f"Mongo={stats['sku_from']['mongo']}, Neo4j={stats['sku_from']['neo4j']}, Generated={stats['sku_from']['generated']}")
            
            check_interrupt()
        except InterruptedError:
            raise
        except Exception as e:
            print(f"    Error building equivalences: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)

        # ========== TRANSFORMATION ==========
        # Each source uses the equivalence map to get the correct SKU
        print("\n[4] Transformation")

        # All transforms now use the equivalence map for SKU resolution
        if "mssql" in selected_dbs and objetos_mssql:
            try:
                transform_mssql(
                    objetos_mssql[0],
                    objetos_mssql[1],
                    objetos_mssql[2],
                    objetos_mssql[3],
                    eq_map,
                )
                check_interrupt()
            except InterruptedError:
                raise
            except Exception as e:
                if interrupted:
                    raise InterruptedError("MSSQL transformation interrupted")
                print(f"    Error transforming MSSQL data: {e}")
                import traceback

                traceback.print_exc()
                sys.exit(1)

        if "mysql" in selected_dbs and objetos_mysql:
            try:
                transform_mysql(
                    objetos_mysql[0],
                    objetos_mysql[1],
                    objetos_mysql[2],
                    objetos_mysql[3],
                    eq_map,
                )
                check_interrupt()
            except InterruptedError:
                raise
            except Exception as e:
                if interrupted:
                    raise InterruptedError("MySQL transformation interrupted")
                print(f"    Error transforming MySQL data: {e}")
                import traceback

                traceback.print_exc()
                sys.exit(1)

        if "supabase" in selected_dbs and objetos_supabase:
            try:
                transform_supabase(
                    objetos_supabase[0],
                    objetos_supabase[1],
                    objetos_supabase[2],
                    objetos_supabase[3],
                    eq_map,
                )
                check_interrupt()
            except InterruptedError:
                raise
            except Exception as e:
                if interrupted:
                    raise InterruptedError("Supabase transformation interrupted")
                print(f"    Error transforming Supabase data: {e}")
                import traceback

                traceback.print_exc()
                sys.exit(1)

        if "mongo" in selected_dbs and objetos_mongo:
            try:
                transform_mongo(
                    objetos_mongo[0],
                    objetos_mongo[1],
                    objetos_mongo[2],
                    eq_map,
                )
                check_interrupt()
            except InterruptedError:
                raise
            except Exception as e:
                if interrupted:
                    raise InterruptedError("MongoDB transformation interrupted")
                print(f"    Error transforming MongoDB data: {e}")
                import traceback

                traceback.print_exc()
                sys.exit(1)

        if "neo4j" in selected_dbs and objetos_neo4j:
            try:
                nodes = objetos_neo4j["nodes"]
                rels = objetos_neo4j["relationships"]
                transform_Neo4j(
                    nodes.get("Producto", []),
                    nodes.get("Cliente", []),
                    rels.get("REALIZO", []),
                    rels.get("CONTIENE", []),
                    eq_map,
                )
                check_interrupt()
            except InterruptedError:
                raise
            except Exception as e:
                if interrupted:
                    raise InterruptedError("Neo4j transformation interrupted")
                print(f"    Error transforming Neo4j data: {e}")
                import traceback

                traceback.print_exc()
                sys.exit(1)

        # ========== LOAD ==========
        print("\n[5] Load to Data Warehouse")
        load_datawarehouse()
        check_interrupt()

        # ========== ASSOCIATION RULES ==========
        print("\n[6] Association Rules (Apriori/FP-Growth)")
        try:
            carga_reglas_asociacion()
        except Exception as e:
            print(f"    Warning: Could not generate association rules: {e}")

        print("\nETL completed successfully\n")

    except InterruptedError:
        print("\nProcess stopped cleanly by user")
        sys.exit(0)
    except KeyboardInterrupt:
        print("\n\nProcess interrupted by user (Ctrl+C)")
        sys.exit(0)
    except Exception as e:
        print(f"\n\nUnexpected error in ETL process: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


# Function to reset the DataWarehouse (delete test data)
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


# Uncomment the following line to reset the DataWarehouse
# reset_datawarehouse()
