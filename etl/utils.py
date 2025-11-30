"""
utils.py
Utilidades comunes para el proceso ETL.

Funciones para:
- Resetear staging y Data Warehouse
- Validar datos
- Obtener estadísticas
- Helpers de transformación
"""

from datetime import datetime
from decimal import Decimal
from typing import Any, Optional

from sqlalchemy import text

from configs.connections import get_dw_engine


def reset_staging_all():
    """
    Elimina todos los datos de las tablas de staging.
    Útil para reiniciar el proceso ETL desde cero.
    """
    engine = get_dw_engine()
    sql = """
        DELETE FROM stg.orden_items;
        DELETE FROM stg.clientes;
        DELETE FROM stg.map_producto;
    """
    with engine.begin() as conn:
        conn.execute(text(sql))
    print("✓ Staging limpiado completamente")


def reset_staging_by_source(source_system: str):
    """
    Elimina datos de staging de un sistema fuente específico.

    Args:
        source_system: 'mssql', 'mongo', 'mysql', 'pg', 'neo4j'
    """
    engine = get_dw_engine()
    with engine.begin() as conn:
        conn.execute(
            text("DELETE FROM stg.orden_items WHERE source_system = :source"),
            {"source": source_system},
        )
        conn.execute(
            text("DELETE FROM stg.clientes WHERE source_system = :source"),
            {"source": source_system},
        )
        conn.execute(
            text("DELETE FROM stg.map_producto WHERE source_system = :source"),
            {"source": source_system},
        )
    print(f"✓ Staging limpiado para source_system = '{source_system}'")


def reset_datawarehouse():
    """
    Elimina todos los datos del Data Warehouse (dimensiones y hechos).
    ¡CUIDADO! Esta operación es destructiva.
    """
    response = input(
        "⚠️  ADVERTENCIA: Esto eliminará TODOS los datos del DW. ¿Continuar? (escriba 'SI' para confirmar): "
    )
    if response != "SI":
        print("Operación cancelada")
        return

    engine = get_dw_engine()
    sql = """
        DELETE FROM dw.FactVentas;
        DELETE FROM dw.MetasVentas;
        DELETE FROM analytics.AssociationRules;
        DELETE FROM dw.DimProducto;
        DELETE FROM dw.DimCliente;
        DELETE FROM dw.DimTiempo;
    """
    with engine.begin() as conn:
        conn.execute(text(sql))
    print("✓ Data Warehouse limpiado completamente")


def get_staging_stats():
    """
    Obtiene estadísticas de las tablas de staging.
    """
    engine = get_dw_engine()
    with engine.connect() as conn:
        # Estadísticas de map_producto
        result = conn.execute(
            text(
                """
            SELECT
                source_system,
                COUNT(*) as total,
                COUNT(DISTINCT sku_oficial) as skus_unicos,
                SUM(CASE WHEN es_servicio = 1 THEN 1 ELSE 0 END) as servicios
            FROM stg.map_producto
            GROUP BY source_system
            ORDER BY source_system
        """
            )
        )
        print("\n📊 ESTADÍSTICAS DE STAGING")
        print("=" * 70)
        print("\nProductos (stg.map_producto):")
        print(f"{'Sistema':<12} {'Total':<10} {'SKUs Únicos':<15} {'Servicios':<10}")
        print("-" * 70)
        for row in result:
            print(f"{row[0]:<12} {row[1]:<10} {row[2]:<15} {row[3]:<10}")

        # Estadísticas de clientes
        result = conn.execute(
            text(
                """
            SELECT
                source_system,
                COUNT(*) as total,
                COUNT(DISTINCT cliente_email) as emails_unicos,
                COUNT(DISTINCT pais_raw) as paises
            FROM stg.clientes
            GROUP BY source_system
            ORDER BY source_system
        """
            )
        )
        print("\nClientes (stg.clientes):")
        print(f"{'Sistema':<12} {'Total':<10} {'Emails Únicos':<15} {'Países':<10}")
        print("-" * 70)
        for row in result:
            print(f"{row[0]:<12} {row[1]:<10} {row[2]:<15} {row[3]:<10}")

        # Estadísticas de orden_items
        result = conn.execute(
            text(
                """
            SELECT
                source_system,
                COUNT(*) as total_items,
                COUNT(DISTINCT source_key_orden) as ordenes,
                SUM(total_num) as total_ventas,
                moneda
            FROM stg.orden_items
            GROUP BY source_system, moneda
            ORDER BY source_system, moneda
        """
            )
        )
        print("\nÓrdenes Items (stg.orden_items):")
        print(
            f"{'Sistema':<12} {'Items':<10} {'Órdenes':<10} {'Total Ventas':<15} {'Moneda':<8}"
        )
        print("-" * 70)
        for row in result:
            print(f"{row[0]:<12} {row[1]:<10} {row[2]:<10} {row[3]:>14.2f} {row[4]:<8}")


def get_dw_stats():
    """
    Obtiene estadísticas del Data Warehouse.
    """
    engine = get_dw_engine()
    with engine.connect() as conn:
        print("\n📊 ESTADÍSTICAS DEL DATA WAREHOUSE")
        print("=" * 70)

        # Dimensiones
        count_tiempo = conn.execute(text("SELECT COUNT(*) FROM dw.DimTiempo")).scalar()
        count_cliente = conn.execute(
            text("SELECT COUNT(*) FROM dw.DimCliente")
        ).scalar()
        count_producto = conn.execute(
            text("SELECT COUNT(*) FROM dw.DimProducto")
        ).scalar()

        print("\nDimensiones:")
        print(f"  DimTiempo:    {count_tiempo:>8} registros")
        print(f"  DimCliente:   {count_cliente:>8} registros")
        print(f"  DimProducto:  {count_producto:>8} registros")

        # Hechos
        result = conn.execute(
            text(
                """
            SELECT
                Fuente,
                COUNT(*) as registros,
                SUM(TotalUSD) as ventas_usd,
                MIN(TiempoID) as fecha_min,
                MAX(TiempoID) as fecha_max
            FROM dw.FactVentas
            GROUP BY Fuente
            ORDER BY Fuente
        """
            )
        )

        print("\nHechos (FactVentas):")
        print(
            f"{'Fuente':<12} {'Registros':<12} {'Ventas USD':<15} {'Fecha Min':<12} {'Fecha Max':<12}"
        )
        print("-" * 70)
        total_registros = 0
        total_ventas = 0
        for row in result:
            print(
                f"{row[0]:<12} {row[1]:<12} {row[2]:>14.2f} {row[3]:<12} {row[4]:<12}"
            )
            total_registros += row[1]
            total_ventas += float(row[2]) if row[2] else 0

        print("-" * 70)
        print(f"{'TOTAL':<12} {total_registros:<12} {total_ventas:>14.2f}")

        # Metas
        count_metas = conn.execute(text("SELECT COUNT(*) FROM dw.MetasVentas")).scalar()
        print(f"\nMetas de Ventas: {count_metas:>8} registros")


def normalize_gender(genero_raw: Optional[str]) -> str:
    """
    Normaliza el género a los valores estándar del DW.

    Args:
        genero_raw: Género en formato original ('M', 'F', 'Masculino', 'Femenino', etc.)

    Returns:
        str: 'Masculino', 'Femenino', o 'No especificado'
    """
    if not genero_raw:
        return "No especificado"

    genero = genero_raw.strip().upper()

    if genero in ("M", "MASCULINO", "MALE", "H", "HOMBRE"):
        return "Masculino"
    elif genero in ("F", "FEMENINO", "FEMALE", "M", "MUJER"):
        return "Femenino"
    else:
        return "No especificado"


def normalize_channel(canal_raw: Optional[str]) -> str:
    """
    Normaliza el canal de venta a valores estándar.

    Args:
        canal_raw: Canal en formato original

    Returns:
        str: 'WEB', 'TIENDA', 'APP', o 'PARTNER'
    """
    if not canal_raw:
        return "WEB"

    canal = canal_raw.strip().upper()

    if canal in ("WEB", "ONLINE", "ECOMMERCE"):
        return "WEB"
    elif canal in ("TIENDA", "STORE", "RETAIL", "FISICA"):
        return "TIENDA"
    elif canal in ("APP", "MOBILE", "MOVIL"):
        return "APP"
    elif canal in ("PARTNER", "SOCIO", "ASOCIADO"):
        return "PARTNER"
    else:
        return canal  # Mantener el valor original si no se reconoce


def safe_decimal(value: Any, default: Decimal = Decimal("0.0")) -> Decimal:
    """
    Convierte un valor a Decimal de forma segura.

    Args:
        value: Valor a convertir
        default: Valor por defecto si la conversión falla

    Returns:
        Decimal
    """
    if value is None:
        return default

    try:
        return Decimal(str(value).replace(",", ""))
    except (ValueError, TypeError):
        return default


def safe_int(value: Any, default: int = 0) -> int:
    """
    Convierte un valor a int de forma segura.

    Args:
        value: Valor a convertir
        default: Valor por defecto si la conversión falla

    Returns:
        int
    """
    if value is None:
        return default

    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def safe_float(value: Any, default: float = 0.0) -> float:
    """
    Convierte un valor a float de forma segura.

    Args:
        value: Valor a convertir
        default: Valor por defecto si la conversión falla

    Returns:
        float
    """
    if value is None:
        return default

    try:
        return float(str(value).replace(",", ""))
    except (ValueError, TypeError):
        return default


def safe_date(value: Any) -> Optional[datetime]:
    """
    Convierte un valor a datetime de forma segura.

    Args:
        value: Valor a convertir (string, datetime, date)

    Returns:
        datetime o None si no se puede convertir
    """
    if value is None:
        return None

    if isinstance(value, datetime):
        return value

    if isinstance(value, str):
        # Intentar varios formatos comunes
        formats = [
            "%Y-%m-%d",
            "%Y-%m-%d %H:%M:%S",
            "%Y/%m/%d",
            "%d/%m/%Y",
            "%d-%m-%Y",
        ]
        for fmt in formats:
            try:
                return datetime.strptime(value, fmt)
            except ValueError:
                continue

    return None


def validate_sku(sku: str) -> bool:
    """
    Valida que un SKU tenga un formato válido.

    Args:
        sku: SKU a validar

    Returns:
        bool: True si es válido
    """
    if not sku or not isinstance(sku, str):
        return False

    # SKU debe tener al menos 3 caracteres
    if len(sku.strip()) < 3:
        return False

    return True


def check_tc_availability(fecha_inicio: str, fecha_fin: str):
    """
    Verifica si existen tipos de cambio para un rango de fechas.

    Args:
        fecha_inicio: Fecha inicial (YYYY-MM-DD)
        fecha_fin: Fecha final (YYYY-MM-DD)
    """
    engine = get_dw_engine()
    with engine.connect() as conn:
        result = conn.execute(
            text(
                """
                        SELECT
                                COUNT(*) as registros,
                                MIN(fecha) as fecha_min,
                                MAX(fecha) as fecha_max
                        FROM stg.tipo_cambio
                        WHERE fecha BETWEEN :inicio AND :fin
                            AND de = 'USD' AND a = 'CRC'
        """
            ),
            {"inicio": fecha_inicio, "fin": fecha_fin},
        )
        row = result.fetchone()

        print("\n📅 TIPOS DE CAMBIO DISPONIBLES")
        print("=" * 70)
        print(f"Rango solicitado: {fecha_inicio} a {fecha_fin}")
        print(f"Registros encontrados: {row[0]}")
        if row[0] > 0:
            print(f"Rango real: {row[1]} a {row[2]}")
        else:
            print(
                "⚠️  No hay tipos de cambio. Ejecuta el job 'BCCR_TipoCambio_Diario' en SQL Server"
            )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Utilidades ETL")
    parser.add_argument(
        "--action",
        choices=[
            "reset-staging",
            "reset-dw",
            "staging-stats",
            "dw-stats",
            "check-tc",
        ],
        required=True,
        help="Acción a ejecutar",
    )
    parser.add_argument("--source", help="Sistema fuente (para reset-staging)")
    parser.add_argument("--fecha-inicio", help="Fecha inicio (YYYY-MM-DD)")
    parser.add_argument("--fecha-fin", help="Fecha fin (YYYY-MM-DD)")

    args = parser.parse_args()

    if args.action == "reset-staging":
        if args.source:
            reset_staging_by_source(args.source)
        else:
            reset_staging_all()
    elif args.action == "reset-dw":
        reset_datawarehouse()
    elif args.action == "staging-stats":
        get_staging_stats()
    elif args.action == "dw-stats":
        get_dw_stats()
    elif args.action == "check-tc":
        if args.fecha_inicio and args.fecha_fin:
            check_tc_availability(args.fecha_inicio, args.fecha_fin)
        else:
            print("Error: Se requieren --fecha-inicio y --fecha-fin")
