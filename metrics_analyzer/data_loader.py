"""
Carga y validación de archivos Excel de Monday.com.

Este módulo se encarga de leer archivos Excel exportados de Monday.com,
validar su estructura y contenido, y retornar un DataFrame limpio.
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import pandas as pd
from config import REQUIRED_COLUMNS, OPTIONAL_COLUMNS
from utils import (
    print_error,
    print_success,
    print_warning,
    get_completion_stats
)


logger = logging.getLogger(__name__)


class DataLoader:
    """Cargador y validador de datos de Monday.com."""

    def __init__(self, file_path: str):
        """
        Inicializa el cargador de datos.

        Args:
            file_path: Ruta al archivo Excel de Monday.com.

        Raises:
            FileNotFoundError: Si el archivo no existe.
        """
        self.file_path = Path(file_path)
        if not self.file_path.exists():
            raise FileNotFoundError(f"Archivo no encontrado: {file_path}")

        self.df: Optional[pd.DataFrame] = None
        self.validation_results: Dict[str, any] = {}

    def load(self) -> pd.DataFrame:
        """
        Carga el archivo Excel.

        Returns:
            DataFrame con los datos cargados.

        Raises:
            ValueError: Si el archivo no puede ser leído o no tiene el formato esperado.
        """
        try:
            logger.info(f"Cargando archivo: {self.file_path}")

            # Leer el archivo Excel
            # La fila 0 tiene el título del board, fila 1 es "All Tasks", fila 2 tiene los headers
            df = pd.read_excel(self.file_path, header=2)

            # Verificar que hay datos
            if df.empty:
                raise ValueError("El archivo está vacío (no tiene datos después de los headers)")

            # Aplicar normalización de nombres de columnas (tolerar errores tipográficos menores)
            df = self._normalize_column_names(df)

            # Agregar columnas opcionales faltantes con valores por defecto
            df = self._add_missing_optional_columns(df)

            self.df = df
            logger.info(f"Archivo cargado exitosamente: {len(df)} filas encontradas")

            return df

        except Exception as e:
            error_msg = f"Error al cargar el archivo: {e}"
            logger.error(error_msg)
            raise ValueError(error_msg)

    def _normalize_column_names(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Normaliza nombres de columnas para tolerar errores tipográficos menores.

        Args:
            df: DataFrame con columnas a normalizar.

        Returns:
            DataFrame con columnas normalizadas.
        """
        # Mapa de correcciones conocidas
        column_fixes = {
            'Asigando': 'Asignado',  # Error tipográfico común
        }

        # Aplicar correcciones
        df = df.rename(columns=column_fixes)

        return df

    def _add_missing_optional_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Agrega columnas opcionales faltantes con valores por defecto.

        Args:
            df: DataFrame con columnas existentes.

        Returns:
            DataFrame con columnas opcionales agregadas.
        """
        import numpy as np

        for col in OPTIONAL_COLUMNS:
            if col not in df.columns:
                # Valores por defecto según tipo de columna
                if 'Fecha' in col:
                    df[col] = pd.NaT  # NaT para fechas
                elif col in ['Carry over']:
                    df[col] = ''  # String vacío para flags
                else:
                    df[col] = np.nan  # NaN para numéricos

                logger.info(f"Columna opcional '{col}' no encontrada - agregada con valores por defecto")

        return df

    def validate(self) -> Tuple[bool, List[str]]:
        """
        Valida la estructura y contenido del DataFrame.

        Returns:
            Tupla (es_válido, lista_de_errores).
        """
        if self.df is None:
            return False, ["No hay datos cargados. Ejecute load() primero."]

        errors = []

        # Validar columnas requeridas
        missing_columns = self._validate_columns()
        if missing_columns:
            errors.append(f"Columnas faltantes: {', '.join(missing_columns)}")

        # Validar que hay al menos una fila de datos
        if len(self.df) == 0:
            errors.append("No hay filas de datos en el archivo")

        # Validar tipos de datos básicos
        data_errors = self._validate_data_types()
        errors.extend(data_errors)

        # Guardar resultados de validación
        self.validation_results = {
            'total_rows': len(self.df),
            'missing_columns': missing_columns,
            'data_errors': data_errors,
            'is_valid': len(errors) == 0
        }

        is_valid = len(errors) == 0

        if is_valid:
            logger.info("Validación exitosa")
        else:
            logger.warning(f"Validación falló con {len(errors)} errores")

        return is_valid, errors

    def _validate_columns(self) -> List[str]:
        """
        Valida que todas las columnas requeridas estén presentes.

        Returns:
            Lista de columnas faltantes.
        """
        current_columns = set(self.df.columns)
        required_columns = set(REQUIRED_COLUMNS)

        missing = required_columns - current_columns

        if missing:
            logger.warning(f"Columnas faltantes: {missing}")

        return list(missing)

    def _validate_data_types(self) -> List[str]:
        """
        Valida que los tipos de datos sean apropiados.

        Returns:
            Lista de errores de validación.
        """
        errors = []

        # Validar que hay sprints
        if 'Sprint' in self.df.columns:
            valid_sprints = self.df['Sprint'].notna().sum()
            if valid_sprints == 0:
                errors.append("No hay sprints válidos en los datos")
        else:
            errors.append("Columna 'Sprint' no encontrada")

        return errors

    def print_validation_report(self) -> None:
        """Imprime un reporte detallado de validación."""
        if not self.validation_results:
            print_warning("No hay resultados de validación. Ejecute validate() primero.")
            return

        print("\n" + "=" * 60)
        print("REPORTE DE VALIDACIÓN")
        print("=" * 60)

        total_rows = self.validation_results.get('total_rows', 0)
        print(f"\nFilas encontradas: {total_rows}")

        # Estado de columnas
        missing_columns = self.validation_results.get('missing_columns', [])
        if missing_columns:
            print_error(f"Columnas faltantes: {', '.join(missing_columns)}")
        else:
            print_success("Todas las columnas requeridas presentes")

        # Errores de datos
        data_errors = self.validation_results.get('data_errors', [])
        if data_errors:
            print("\nErrores de datos:")
            for error in data_errors:
                print_error(error)

        # Estadísticas de completitud
        if self.df is not None:
            print("\nCompletitud de datos críticos:")
            critical_columns = [
                'Sprint',
                'Estado',
                'Estimación Original',
                'Puntos Logrados',
                'Fecha Inicio',
                'Fecha Ready for Production'
            ]

            for col in critical_columns:
                if col in self.df.columns:
                    stats = get_completion_stats(self.df, col)
                    percentage = stats['percentage']
                    symbol = '✓' if percentage > 80 else '⚠' if percentage > 50 else '✗'
                    print(f"  {symbol} {col}: {stats['complete']}/{stats['total']} ({percentage:.1f}%)")

        # Estado final
        is_valid = self.validation_results.get('is_valid', False)
        print()
        if is_valid:
            print_success("Validación exitosa - Archivo listo para procesar")
        else:
            print_error("Validación fallida - Corrija los errores antes de continuar")

    def get_dataframe(self) -> pd.DataFrame:
        """
        Obtiene el DataFrame cargado.

        Returns:
            DataFrame con los datos.

        Raises:
            ValueError: Si no hay datos cargados.
        """
        if self.df is None:
            raise ValueError("No hay datos cargados. Ejecute load() primero.")

        return self.df.copy()


def load_and_validate_data(file_path: str, verbose: bool = False) -> pd.DataFrame:
    """
    Función de conveniencia para cargar y validar datos en un solo paso.

    Args:
        file_path: Ruta al archivo Excel.
        verbose: Si es True, imprime el reporte de validación.

    Returns:
        DataFrame con los datos validados.

    Raises:
        ValueError: Si la validación falla.
    """
    loader = DataLoader(file_path)

    # Cargar datos
    loader.load()
    print_success(f"Archivo cargado: {len(loader.df)} tareas encontradas")

    # Validar
    is_valid, errors = loader.validate()

    if verbose:
        loader.print_validation_report()

    if not is_valid:
        error_msg = "Validación fallida:\n" + "\n".join(f"  - {err}" for err in errors)
        raise ValueError(error_msg)

    print_success("Validación completada: Todas las columnas requeridas presentes")

    return loader.get_dataframe()
