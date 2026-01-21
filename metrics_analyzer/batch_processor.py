"""
Procesamiento batch de múltiples archivos de equipos.

Este módulo permite procesar múltiples archivos Excel de diferentes
equipos y generar métricas consolidadas.
"""

import logging
import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Literal
from dataclasses import dataclass
import pandas as pd

from config import (
    DEVELOPMENT_TEAMS,
    BATCH_CONFIG,
    DEFAULT_TEAM_SIZE,
    DEFAULT_SPRINT_MAPPING,
    DELIVERY_DATE_COLUMNS_PRODUCTIVE,
    DELIVERY_DATE_COLUMNS_DEVELOPMENT,
)
from data_loader import load_and_validate_data
from data_processor import process_data
from metrics_calculator import MetricsCalculator
from utils import print_info, print_success, print_warning, print_error


logger = logging.getLogger(__name__)


@dataclass
class TeamResult:
    """Resultado del procesamiento de un equipo."""
    team_name: str
    team_type: Literal['Productivo', 'En Desarrollo']
    team_size: int
    sprint_metrics: pd.DataFrame
    month_metrics: pd.DataFrame
    summary: Dict
    file_path: str
    success: bool
    error_message: Optional[str] = None


class BatchProcessor:
    """Procesador batch de múltiples archivos de equipos."""

    def __init__(
        self,
        folder_path: str,
        team_sizes: Dict[str, int] = None,
        sprint_mapping: Dict[str, str] = None,
        verbose: bool = False
    ):
        """
        Inicializa el procesador batch.

        Args:
            folder_path: Ruta a la carpeta con archivos Excel.
            team_sizes: Diccionario opcional {nombre_equipo: tamaño}.
            sprint_mapping: Mapeo de sprints a meses.
            verbose: Modo verbose para logging.
        """
        self.folder_path = Path(folder_path)
        self.team_sizes = team_sizes or {}
        self.sprint_mapping = sprint_mapping or DEFAULT_SPRINT_MAPPING
        self.verbose = verbose
        self.results: List[TeamResult] = []

        if not self.folder_path.exists():
            raise FileNotFoundError(f"Carpeta no encontrada: {folder_path}")

        if not self.folder_path.is_dir():
            raise ValueError(f"La ruta no es una carpeta: {folder_path}")

    def discover_files(self) -> List[Tuple[Path, str]]:
        """
        Descubre archivos válidos y extrae nombres de equipos.

        Returns:
            Lista de tuplas (path_archivo, nombre_equipo).
        """
        pattern = BATCH_CONFIG['file_pattern']
        files = list(self.folder_path.glob(pattern))

        discovered = []
        for file_path in files:
            team_name = self._extract_team_name(file_path.name)
            if team_name:
                discovered.append((file_path, team_name))
                logger.info(f"Archivo descubierto: {file_path.name} -> Equipo: {team_name}")
            else:
                logger.warning(f"No se pudo extraer nombre de equipo: {file_path.name}")

        return discovered

    def _extract_team_name(self, filename: str) -> Optional[str]:
        """
        Extrae el nombre del equipo del nombre del archivo.

        Formato esperado: Backlog_Planning_<<NombreEquipo>>_All_Tasks_<<ID>>.xlsx

        Args:
            filename: Nombre del archivo.

        Returns:
            Nombre del equipo o None si no se puede extraer.
        """
        regex = BATCH_CONFIG['team_name_regex']
        match = re.search(regex, filename)

        if match:
            team_name = match.group(1)
            return team_name.strip()

        return None

    def _determine_team_type(self, team_name: str) -> Literal['Productivo', 'En Desarrollo']:
        """
        Determina el tipo de equipo (Productivo o En Desarrollo).

        Args:
            team_name: Nombre del equipo.

        Returns:
            'En Desarrollo' si está en DEVELOPMENT_TEAMS, 'Productivo' en caso contrario.
        """
        team_name_normalized = team_name.strip().upper()

        for dev_team in DEVELOPMENT_TEAMS:
            dev_team_normalized = dev_team.upper()
            if dev_team_normalized in team_name_normalized or team_name_normalized in dev_team_normalized:
                return 'En Desarrollo'

        return 'Productivo'

    def _get_team_size(self, team_name: str) -> int:
        """
        Obtiene el tamaño del equipo.

        Args:
            team_name: Nombre del equipo.

        Returns:
            Tamaño del equipo desde configuración o valor por defecto.
        """
        return self.team_sizes.get(team_name, DEFAULT_TEAM_SIZE)

    def _get_delivery_date_column(self, df: pd.DataFrame, team_type: str) -> str:
        """
        Determina la columna de fecha de entrega a usar.

        Args:
            df: DataFrame con los datos.
            team_type: Tipo de equipo.

        Returns:
            Nombre de la columna de fecha a usar.
        """
        if team_type == 'Productivo':
            date_columns = DELIVERY_DATE_COLUMNS_PRODUCTIVE
            default = 'Fecha Término'
        else:
            date_columns = DELIVERY_DATE_COLUMNS_DEVELOPMENT
            default = 'Fecha Certificado QA'

        for col in date_columns:
            if col in df.columns and df[col].notna().sum() > 0:
                return col

        return default

    def process_single_team(
        self,
        file_path: Path,
        team_name: str
    ) -> TeamResult:
        """
        Procesa un solo archivo de equipo.

        Args:
            file_path: Ruta al archivo Excel.
            team_name: Nombre del equipo.

        Returns:
            TeamResult con los resultados del procesamiento.
        """
        team_type = self._determine_team_type(team_name)
        team_size = self._get_team_size(team_name)

        logger.info(f"Procesando equipo: {team_name} (Tipo: {team_type}, Tamaño: {team_size})")

        try:
            # 1. Cargar y validar datos
            df = load_and_validate_data(str(file_path), verbose=self.verbose)

            # 2. Determinar columna de fecha
            delivery_date_column = self._get_delivery_date_column(df, team_type)

            # 3. Procesar datos
            processed_df = process_data(
                df,
                team_type=team_type,
                sprint_mapping=self.sprint_mapping,
                delivery_date_column=delivery_date_column,
                verbose=self.verbose
            )

            if len(processed_df) == 0:
                return TeamResult(
                    team_name=team_name,
                    team_type=team_type,
                    team_size=team_size,
                    sprint_metrics=pd.DataFrame(),
                    month_metrics=pd.DataFrame(),
                    summary={},
                    file_path=str(file_path),
                    success=False,
                    error_message="No hay datos válidos después del procesamiento"
                )

            # 4. Calcular métricas
            calculator = MetricsCalculator(processed_df, team_size)
            calculator.calculate_all_metrics()

            return TeamResult(
                team_name=team_name,
                team_type=team_type,
                team_size=team_size,
                sprint_metrics=calculator.get_sprint_metrics(),
                month_metrics=calculator.get_month_metrics(),
                summary=calculator.get_summary(),
                file_path=str(file_path),
                success=True
            )

        except Exception as e:
            logger.error(f"Error procesando {team_name}: {e}")
            return TeamResult(
                team_name=team_name,
                team_type=team_type,
                team_size=team_size,
                sprint_metrics=pd.DataFrame(),
                month_metrics=pd.DataFrame(),
                summary={},
                file_path=str(file_path),
                success=False,
                error_message=str(e)
            )

    def process_all(self) -> List[TeamResult]:
        """
        Procesa todos los archivos descubiertos.

        Returns:
            Lista de TeamResult con resultados de cada equipo.
        """
        discovered_files = self.discover_files()

        if not discovered_files:
            raise ValueError(f"No se encontraron archivos válidos en: {self.folder_path}")

        print_info(f"Se encontraron {len(discovered_files)} archivos para procesar")

        self.results = []
        for file_path, team_name in discovered_files:
            print_info(f"Procesando: {team_name}...")
            result = self.process_single_team(file_path, team_name)
            self.results.append(result)

            if result.success:
                print_success(f"  {team_name}: {result.summary.get('total_delivered', 0)} tareas entregadas")
            else:
                print_error(f"  {team_name}: {result.error_message}")

        successful = sum(1 for r in self.results if r.success)
        print_info(f"Procesamiento completado: {successful}/{len(self.results)} equipos exitosos")

        return self.results

    def get_successful_results(self) -> List[TeamResult]:
        """Retorna solo los resultados exitosos."""
        return [r for r in self.results if r.success]

    def get_failed_results(self) -> List[TeamResult]:
        """Retorna solo los resultados fallidos."""
        return [r for r in self.results if not r.success]


def extract_team_name_from_filename(filename: str) -> Optional[str]:
    """
    Función de utilidad para extraer nombre de equipo.

    Args:
        filename: Nombre del archivo.

    Returns:
        Nombre del equipo o None.
    """
    regex = BATCH_CONFIG['team_name_regex']
    match = re.search(regex, filename)
    if match:
        return match.group(1).strip()
    return None


def determine_team_type(team_name: str) -> Literal['Productivo', 'En Desarrollo']:
    """
    Función de utilidad para determinar tipo de equipo.

    Args:
        team_name: Nombre del equipo.

    Returns:
        'En Desarrollo' o 'Productivo'.
    """
    team_name_upper = team_name.strip().upper()
    for dev_team in DEVELOPMENT_TEAMS:
        if dev_team.upper() in team_name_upper:
            return 'En Desarrollo'
    return 'Productivo'
