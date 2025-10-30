"""
bccr_tc_diario.py
Job programado para actualizar el tipo de cambio diario a las 5:00 a.m.
Consulta al WebService del BCCR el TC del día actual y lo almacena en stg.tipo_cambio.
"""

import sys
from datetime import datetime
from typing import Optional
import requests
import xml.etree.ElementTree as ET
from sqlalchemy import text
from configs.connections import (
    get_dw_engine,
    BCCR_ENDPOINT,
    BCCR_TOKEN,
    BCCR_EMAIL,
    BCCR_NOMBRE,
    BCCR_INDICADOR_COMPRA,
    BCCR_INDICADOR_VENTA,
)


def consultar_indicador(indicador: str, fecha: str) -> Optional[str]:
    """
    Consulta al WebService del BCCR un indicador para una fecha específica.

    Args:
        indicador: Código del indicador (e.g., '317' para compra, '318' para venta)
        fecha: Fecha en formato dd/mm/yyyy

    Returns:
        Respuesta XML como string, o None si hay error.
    """
    try:
        payload = {
            "Indicador": indicador,
            "FechaInicio": fecha,
            "FechaFinal": fecha,
            "Nombre": BCCR_NOMBRE,
            "SubNiveles": "N",
            "CorreoElectronico": BCCR_EMAIL,
            "Token": BCCR_TOKEN,
        }
        response = requests.post(
            BCCR_ENDPOINT,
            data=payload,
            timeout=10,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        print(
            f"Error consultando BCCR para indicador {indicador}: {e}", file=sys.stderr
        )
        return None


def extraer_valor_xml(xml_string: str) -> Optional[float]:
    """
    Extrae del XML del BCCR el valor numérico.

    Args:
        xml_string: Respuesta XML del BCCR

    Returns:
        Valor numérico o None si no se encuentra.
    """
    try:
        root = ET.fromstring(xml_string)
        # Buscar NUM_VALOR sin depender del namespace
        for elem in root.iter():
            if elem.tag.endswith("NUM_VALOR"):
                if elem.text:
                    return float(elem.text)
        return None
    except (ET.ParseError, ValueError) as e:
        print(f"Error parseando XML del BCCR: {e}", file=sys.stderr)
        return None


def guardar_tipo_cambio(fecha: str, compra: float, venta: float) -> bool:
    """
    Guarda los tipos de cambio en la tabla stg.tipo_cambio.

    Args:
        fecha: Fecha en formato YYYY-MM-DD
        compra: Tasa de compra (USD por CRC)
        venta: Tasa de venta (USD por CRC)

    Returns:
        True si se guardó exitosamente, False en caso contrario.
    """
    try:
        engine = get_dw_engine()
        with engine.connect() as conn:
            # Insertar con MERGE para evitar duplicados
            sql = text(
                """
                MERGE INTO stg.tipo_cambio AS target
                USING (SELECT CAST(:fecha AS DATE) AS fecha, :de AS de, :a AS a, CAST(:tasa AS DECIMAL(18,6)) AS tasa) AS source
                ON target.fecha = source.fecha AND target.de = source.de AND target.a = source.a
                WHEN MATCHED THEN
                    UPDATE SET tasa = source.tasa, fuente = 'BCCR WS Daily', 
                               LoadTS = SYSDATETIME()
                WHEN NOT MATCHED THEN
                    INSERT (fecha, de, a, tasa, fuente)
                    VALUES (source.fecha, source.de, source.a, source.tasa, 'BCCR WS Daily');
                """
            )

            # CRC -> USD (tasa de compra: cuántos USD por 1 CRC)
            conn.execute(sql, {"fecha": fecha, "de": "CRC", "a": "USD", "tasa": compra})

            # USD -> CRC (tasa de venta: cuántos CRC por 1 USD)
            conn.execute(
                sql,
                {"fecha": fecha, "de": "USD", "a": "CRC", "tasa": 1 / venta},
            )

            conn.commit()
            return True
    except Exception as e:
        print(
            f"Error guardando tipos de cambio para {fecha}: {e}",
            file=sys.stderr,
        )
        return False


def actualizar_tipo_cambio_diario(fecha: Optional[str] = None) -> None:
    """
    Actualiza el tipo de cambio para el día especificado (por defecto, hoy).

    Args:
        fecha: Fecha en formato dd/mm/yyyy (optional, default: hoy)
    """
    if fecha is None:
        fecha = datetime.now().strftime("%d/%m/%Y")

    print(f"Consultando tipo de cambio del BCCR para {fecha}...")

    # Consultar ambos indicadores
    xml_compra = consultar_indicador(BCCR_INDICADOR_COMPRA, fecha)
    xml_venta = consultar_indicador(BCCR_INDICADOR_VENTA, fecha)

    if not xml_compra or not xml_venta:
        print("Error: No se pudieron obtener datos del BCCR.", file=sys.stderr)
        return

    valor_compra = extraer_valor_xml(xml_compra)
    valor_venta = extraer_valor_xml(xml_venta)

    if valor_compra is None or valor_venta is None:
        print(
            "Error: No se pudieron extraer valores del XML del BCCR.",
            file=sys.stderr,
        )
        return

    # Convertir fecha a formato YYYY-MM-DD
    fecha_obj = datetime.strptime(fecha, "%d/%m/%Y")
    fecha_iso = fecha_obj.strftime("%Y-%m-%d")

    if guardar_tipo_cambio(fecha_iso, valor_compra, valor_venta):
        print(f"✓ Tipos de cambio actualizados para {fecha_iso}:")
        print(f"  - Compra (CRC->USD): {valor_compra:.6f}")
        print(f"  - Venta (USD->CRC): {valor_venta:.6f}")
    else:
        print(f"Error al guardar los tipos de cambio para {fecha_iso}.")


if __name__ == "__main__":
    fecha_param = sys.argv[1] if len(sys.argv) > 1 else None
    actualizar_tipo_cambio_diario(fecha_param)
