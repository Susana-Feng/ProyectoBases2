"""
bccr_tc_historico.py
Consulta al WebService del BCCR los tipos de cambio históricos (3+ años hacia atrás)
y los almacena en la tabla stg.tipo_cambio de la BD del Data Warehouse.
"""

import sys
from datetime import datetime, timedelta
from typing import Optional, Tuple
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


def consultar_indicador(
    indicador: str, fecha_inicio: str, fecha_final: str
) -> Optional[str]:
    """
    Consulta al WebService del BCCR un indicador en un rango de fechas.

    Args:
        indicador: Código del indicador (e.g., '317' para compra, '318' para venta)
        fecha_inicio: Fecha en formato dd/mm/yyyy
        fecha_final: Fecha en formato dd/mm/yyyy

    Returns:
        Respuesta XML como string, o None si hay error.
    """
    try:
        payload = {
            "Indicador": indicador,
            "FechaInicio": fecha_inicio,
            "FechaFinal": fecha_final,
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


def extraer_datos_xml(xml_string: str) -> list[Tuple[str, str]]:
    """
    Extrae del XML del BCCR las fechas y valores.

    Args:
        xml_string: Respuesta XML del BCCR

    Returns:
        Lista de tuplas (fecha, valor)
    """
    try:
        root = ET.fromstring(xml_string)

        datos = []
        # Buscar elementos con local-name para evitar problemas de namespace
        for elem in root.iter():
            if elem.tag.endswith("DES_FECHA"):
                fecha_elem = elem
                # Buscar el siguiente NUM_VALOR
                for siguiente in root.iter():
                    if siguiente.tag.endswith("NUM_VALOR"):
                        valor_text = siguiente.text
                        if valor_text:
                            fecha_text = fecha_elem.text
                            if fecha_text:
                                datos.append((fecha_text.split("T")[0], valor_text))
                        break
        return datos
    except ET.ParseError as e:
        print(f"Error parseando XML del BCCR: {e}", file=sys.stderr)
        return []


def guardar_tipos_cambio(fecha: str, compra: float, venta: float) -> bool:
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
            sql = text(
                """
                MERGE INTO stg.tipo_cambio AS target
                USING (SELECT CAST(:fecha AS DATE) AS fecha, :de AS de, :a AS a, CAST(:tasa AS DECIMAL(18,6)) AS tasa) AS source
                ON target.fecha = source.fecha AND target.de = source.de AND target.a = source.a
                WHEN MATCHED THEN
                    UPDATE SET tasa = source.tasa, fuente = 'BCCR WS', 
                               LoadTS = SYSDATETIME()
                WHEN NOT MATCHED THEN
                    INSERT (fecha, de, a, tasa, fuente, LoadTS)
                    VALUES (source.fecha, source.de, source.a, source.tasa, 'BCCR WS', SYSDATETIME());
                """
            )

            # CRC -> USD (tasa de compra: cuántos USD por 1 CRC)
            conn.execute(sql, {"fecha": fecha, "de": "CRC", "a": "USD", "tasa": compra})

            # USD -> CRC (tasa de venta: cuántos CRC por 1 USD)
            conn.execute(sql, {"fecha": fecha, "de": "USD", "a": "CRC", "tasa": venta})

            conn.commit()
            return True
    except Exception as e:
        print(f"Error guardando tipos de cambio para {fecha}: {e}", file=sys.stderr)
        return False


def cargar_historico(años_atras: int = 3) -> None:
    """
    Carga los tipos de cambio históricos de BCCR para los últimos N años.

    Args:
        años_atras: Número de años hacia atrás a consultar (default: 3)
    """
    hoy = datetime.now()
    inicio = hoy - timedelta(days=365 * años_atras)

    fecha_inicio_str = inicio.strftime("%d/%m/%Y")
    fecha_final_str = hoy.strftime("%d/%m/%Y")

    print(
        f"Consultando tipos de cambio del BCCR desde {fecha_inicio_str} hasta {fecha_final_str}..."
    )

    # Consultar ambos indicadores
    xml_compra = consultar_indicador(
        BCCR_INDICADOR_COMPRA, fecha_inicio_str, fecha_final_str
    )
    xml_venta = consultar_indicador(
        BCCR_INDICADOR_VENTA, fecha_inicio_str, fecha_final_str
    )

    if not xml_compra or not xml_venta:
        print("Error: No se pudieron obtener datos del BCCR.", file=sys.stderr)
        return

    datos_compra = extraer_datos_xml(xml_compra)
    datos_venta = extraer_datos_xml(xml_venta)

    if not datos_compra or not datos_venta:
        print("Error: No se pudieron extraer datos del XML del BCCR.", file=sys.stderr)
        return

    # Crear diccionarios indexados por fecha
    dict_compra = {fecha: float(valor) for fecha, valor in datos_compra}
    dict_venta = {fecha: float(valor) for fecha, valor in datos_venta}

    # Iterar sobre todas las fechas únicas
    fechas = sorted(set(dict_compra.keys()) & set(dict_venta.keys()))

    insertados = 0
    errores = 0

    for fecha in fechas:
        compra = dict_compra[fecha]
        venta = dict_venta[fecha]

        if guardar_tipos_cambio(fecha, compra, venta):
            insertados += 1
        else:
            errores += 1

        if (insertados + errores) % 50 == 0:
            print(f"  Procesados: {insertados + errores} registros...")

    print("\n✓ Carga completada:")
    print(f"  - Registros insertados/actualizados: {insertados}")
    print(f"  - Errores: {errores}")


if __name__ == "__main__":
    años = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    cargar_historico(años)
