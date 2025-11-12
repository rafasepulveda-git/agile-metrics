"""
Funciones auxiliares para el analizador de métricas ágiles.

Este módulo contiene utilidades para validación, formateo y procesamiento
de datos comunes utilizados en todo el proyecto.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
import pandas as pd
from config import COPY_SUFFIXES, HOLIDAYS


# Configurar logging
def setup_logging(verbose: bool = False) -> None:
    """
    Configura el sistema de logging.

    Args:
        verbose: Si es True, muestra logs de nivel DEBUG.
    """
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


def is_copied_task(task_name: str) -> bool:
    """
    Determina si una tarea es una copia basándose en su nombre.

    Args:
        task_name: Nombre de la tarea.

    Returns:
        True si la tarea es una copia, False de lo contrario.
    """
    if not isinstance(task_name, str):
        return False

    return any(suffix in task_name for suffix in COPY_SUFFIXES)


def parse_sprint_mapping(mapping_str: str) -> Dict[str, str]:
    """
    Parsea un string de mapeo de sprints a meses.

    Formato esperado: "Sprint 2:Julio,Sprint 3:Agosto,Sprint 4:Agosto"

    Args:
        mapping_str: String con el mapeo.

    Returns:
        Diccionario con el mapeo de sprint a mes.

    Raises:
        ValueError: Si el formato es inválido.
    """
    mapping = {}

    try:
        pairs = mapping_str.split(',')
        for pair in pairs:
            sprint, month = pair.split(':')
            mapping[sprint.strip()] = month.strip()
    except Exception as e:
        raise ValueError(
            f"Formato de mapeo inválido. Use: 'Sprint 2:Julio,Sprint 3:Agosto'. Error: {e}"
        )

    return mapping


def safe_float_conversion(value: Any) -> Optional[float]:
    """
    Convierte un valor a float de manera segura.

    Args:
        value: Valor a convertir.

    Returns:
        Valor convertido a float, o None si no es posible.
    """
    if pd.isna(value):
        return None

    if isinstance(value, (int, float)):
        return float(value)

    if isinstance(value, str):
        # Intentar limpiar el string
        cleaned = value.strip().replace(',', '.')
        try:
            return float(cleaned)
        except ValueError:
            return None

    return None


def safe_date_conversion(value: Any) -> Optional[datetime]:
    """
    Convierte un valor a datetime de manera segura.

    Args:
        value: Valor a convertir.

    Returns:
        Valor convertido a datetime, o None si no es posible.
    """
    if pd.isna(value):
        return None

    if isinstance(value, datetime):
        return value

    if isinstance(value, pd.Timestamp):
        return value.to_pydatetime()

    if isinstance(value, str):
        # Intentar varios formatos comunes
        formats = [
            '%Y-%m-%d',
            '%d/%m/%Y',
            '%m/%d/%Y',
            '%Y-%m-%d %H:%M:%S',
            '%d/%m/%Y %H:%M:%S',
        ]

        for fmt in formats:
            try:
                return datetime.strptime(value.strip(), fmt)
            except ValueError:
                continue

    return None


def calculate_days_between(start_date: Any, end_date: Any) -> Optional[float]:
    """
    Calcula los días entre dos fechas.

    Args:
        start_date: Fecha de inicio.
        end_date: Fecha de fin.

    Returns:
        Número de días entre las fechas, o None si no es posible calcular.
    """
    start = safe_date_conversion(start_date)
    end = safe_date_conversion(end_date)

    if start is None or end is None:
        return None

    delta = end - start
    return delta.days


def calculate_business_days(start_date: Any, end_date: Any, holidays: List[str] = None) -> Optional[int]:
    """
    Calcula los días hábiles entre dos fechas, excluyendo fines de semana y feriados.

    Args:
        start_date: Fecha de inicio.
        end_date: Fecha de fin.
        holidays: Lista de fechas de feriados en formato 'YYYY-MM-DD'. Si es None, usa HOLIDAYS de config.

    Returns:
        Número de días hábiles entre las fechas, o None si no es posible calcular.
    """
    start = safe_date_conversion(start_date)
    end = safe_date_conversion(end_date)

    if start is None or end is None:
        return None

    # Usar feriados de config si no se proporcionan
    if holidays is None:
        holidays = HOLIDAYS

    # Convertir feriados a set de fechas para búsqueda rápida
    holiday_dates = set()
    for holiday_str in holidays:
        try:
            holiday_date = datetime.strptime(holiday_str, '%Y-%m-%d').date()
            holiday_dates.add(holiday_date)
        except ValueError:
            logging.warning(f"Fecha de feriado inválida: {holiday_str}")

    # Contar días hábiles
    business_days = 0
    current_date = start.date() if isinstance(start, datetime) else start
    end_date_obj = end.date() if isinstance(end, datetime) else end

    while current_date <= end_date_obj:
        # Verificar si es día de semana (lunes=0, domingo=6)
        if current_date.weekday() < 5:  # 0-4 son días laborables
            # Verificar si no es feriado
            if current_date not in holiday_dates:
                business_days += 1

        current_date += timedelta(days=1)

    return business_days


def format_percentage(value: Optional[float], decimals: int = 1) -> str:
    """
    Formatea un valor como porcentaje.

    Args:
        value: Valor a formatear (0-100).
        decimals: Número de decimales.

    Returns:
        String formateado como porcentaje.
    """
    if value is None or pd.isna(value):
        return 'N/A'

    return f"{value:.{decimals}f}%"


def format_number(value: Optional[float], decimals: int = 2) -> str:
    """
    Formatea un valor numérico.

    Args:
        value: Valor a formatear.
        decimals: Número de decimales.

    Returns:
        String formateado.
    """
    if value is None or pd.isna(value):
        return 'N/A'

    return f"{value:.{decimals}f}"


def is_sprint_completed(sprint_completed_value: Any) -> bool:
    """
    Determina si un sprint está completado basándose en el valor de la columna.

    Args:
        sprint_completed_value: Valor de la columna 'Sprint Completed?'.

    Returns:
        True si el sprint está completado, False de lo contrario.
    """
    if pd.isna(sprint_completed_value):
        return False

    if isinstance(sprint_completed_value, str):
        return sprint_completed_value.strip().lower() == 'v'

    # Si es booleano
    return bool(sprint_completed_value)


def get_completion_stats(df: pd.DataFrame, column: str) -> Dict[str, Any]:
    """
    Calcula estadísticas de completitud para una columna.

    Args:
        df: DataFrame a analizar.
        column: Nombre de la columna.

    Returns:
        Diccionario con estadísticas de completitud.
    """
    total = len(df)
    if total == 0:
        return {
            'total': 0,
            'complete': 0,
            'missing': 0,
            'percentage': 0.0
        }

    missing = df[column].isna().sum()
    complete = total - missing
    percentage = (complete / total) * 100

    return {
        'total': total,
        'complete': int(complete),
        'missing': int(missing),
        'percentage': percentage
    }


def print_section_header(title: str, char: str = '=') -> None:
    """
    Imprime un encabezado de sección formateado.

    Args:
        title: Título de la sección.
        char: Carácter para la línea decorativa.
    """
    line = char * 60
    print(f"\n{line}")
    print(f"{title}")
    print(line)


def print_success(message: str) -> None:
    """Imprime un mensaje de éxito."""
    print(f"✓ {message}")


def print_warning(message: str) -> None:
    """Imprime un mensaje de advertencia."""
    print(f"⚠ {message}")


def print_error(message: str) -> None:
    """Imprime un mensaje de error."""
    print(f"✗ {message}")


def print_info(message: str) -> None:
    """Imprime un mensaje informativo."""
    print(f"• {message}")


def format_file_size(size_bytes: int) -> str:
    """
    Formatea un tamaño de archivo en bytes a una representación legible.

    Args:
        size_bytes: Tamaño en bytes.

    Returns:
        String formateado (ej: "234 KB", "1.5 MB").
    """
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.0f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.0f} TB"


def validate_team_size(team_size: Any) -> int:
    """
    Valida y convierte el tamaño del equipo a entero.

    Args:
        team_size: Valor del tamaño del equipo.

    Returns:
        Tamaño del equipo como entero.

    Raises:
        ValueError: Si el valor no es válido.
    """
    try:
        size = int(team_size)
        if size <= 0:
            raise ValueError("El tamaño del equipo debe ser mayor a 0")
        return size
    except (ValueError, TypeError) as e:
        raise ValueError(f"Tamaño de equipo inválido: {e}")


def extract_sprint_number(sprint_name: str) -> str:
    """
    Extrae el número base de un sprint para agrupar sprints con el mismo número.

    Ejemplos:
        'Sprint 07 FIDSIN' -> 'Sprint 7'
        'Sprint 07 Auto3P' -> 'Sprint 7'
        'Sprint 7' -> 'Sprint 7'
        'Sprint 03' -> 'Sprint 3'

    Args:
        sprint_name: Nombre completo del sprint.

    Returns:
        Nombre unificado del sprint (ej: 'Sprint 7').
    """
    import re

    if pd.isna(sprint_name):
        return None

    sprint_str = str(sprint_name).strip()

    # Buscar patrón: "Sprint" seguido de números (con o sin ceros a la izquierda)
    # y opcionalmente seguido de más texto
    match = re.search(r'Sprint\s*(\d+)', sprint_str, re.IGNORECASE)

    if match:
        sprint_number = int(match.group(1))  # Convertir a int para quitar ceros a la izquierda
        return f'Sprint {sprint_number}'

    # Si no coincide con el patrón, retornar el nombre original
    return sprint_str
