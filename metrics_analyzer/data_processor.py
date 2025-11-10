"""
Procesamiento y limpieza de datos de Monday.com.

Este módulo se encarga de limpiar, transformar y preparar los datos
para el cálculo de métricas.
"""

import logging
from typing import Dict, List, Literal
import pandas as pd
import numpy as np
from config import (
    DELIVERY_STATES_PRODUCTIVE,
    DELIVERY_STATES_DEVELOPMENT,
    DEFAULT_SPRINT_MAPPING
)
from utils import (
    is_copied_task,
    safe_float_conversion,
    safe_date_conversion,
    is_sprint_completed,
    print_warning,
    print_info
)


logger = logging.getLogger(__name__)


class DataProcessor:
    """Procesador de datos de Monday.com."""

    def __init__(
        self,
        df: pd.DataFrame,
        team_type: Literal['Productivo', 'En Desarrollo'] = 'Productivo',
        sprint_mapping: Dict[str, str] = None
    ):
        """
        Inicializa el procesador de datos.

        Args:
            df: DataFrame con los datos crudos.
            team_type: Tipo de equipo ('Productivo' o 'En Desarrollo').
            sprint_mapping: Mapeo de sprints a meses. Si es None, usa el por defecto.
        """
        self.raw_df = df.copy()
        self.df = df.copy()
        self.team_type = team_type
        self.sprint_mapping = sprint_mapping or DEFAULT_SPRINT_MAPPING

        # Definir estados de entrega según tipo de equipo
        if team_type == 'Productivo':
            self.delivery_states = DELIVERY_STATES_PRODUCTIVE
        else:
            self.delivery_states = DELIVERY_STATES_DEVELOPMENT

        logger.info(f"Procesador inicializado para equipo tipo: {team_type}")

    def process(self) -> pd.DataFrame:
        """
        Ejecuta todo el pipeline de procesamiento.

        Returns:
            DataFrame procesado.
        """
        logger.info("Iniciando procesamiento de datos...")

        # 1. Limpiar datos básicos
        self._clean_basic_data()

        # 2. Convertir tipos de datos
        self._convert_data_types()

        # 3. Agregar columnas calculadas
        self._add_calculated_columns()

        # 4. Filtrar datos no válidos
        self._filter_invalid_data()

        # 5. Agregar mapeo de meses
        self._add_month_mapping()

        logger.info(f"Procesamiento completado. Filas resultantes: {len(self.df)}")

        return self.df

    def _clean_basic_data(self) -> None:
        """Limpieza básica de datos."""
        logger.debug("Limpiando datos básicos...")

        # Eliminar filas completamente vacías
        self.df = self.df.dropna(how='all')

        # Limpiar espacios en columnas de texto
        text_columns = ['Name', 'Estado', 'Sprint', 'Tipo Tarea']
        for col in text_columns:
            if col in self.df.columns:
                self.df[col] = self.df[col].astype(str).str.strip()

    def _convert_data_types(self) -> None:
        """Convierte columnas a los tipos de datos apropiados."""
        logger.debug("Convirtiendo tipos de datos...")

        # Convertir columnas numéricas
        numeric_columns = ['Estimación Original', 'Puntos Logrados', 'Ciclos UAT']
        for col in numeric_columns:
            if col in self.df.columns:
                self.df[col] = self.df[col].apply(safe_float_conversion)

        # Convertir columnas de fecha
        date_columns = [
            'Fecha Inicio',
            'Fecha Término',
            'Fecha Ready for Production',
            'Fecha paso a Producción'
        ]
        for col in date_columns:
            if col in self.df.columns:
                self.df[col] = self.df[col].apply(safe_date_conversion)

    def _add_calculated_columns(self) -> None:
        """Agrega columnas calculadas."""
        logger.debug("Agregando columnas calculadas...")

        # Es tarea copiada?
        self.df['Is_Copy'] = self.df['Name'].apply(is_copied_task)

        # Sprint está completado?
        if 'Sprint Completed?' in self.df.columns:
            self.df['Sprint_Completed'] = self.df['Sprint Completed?'].apply(is_sprint_completed)
        else:
            self.df['Sprint_Completed'] = False

        # Es tarea entregada?
        self.df['Is_Delivered'] = self.df['Estado'].isin(self.delivery_states)

        # Tiene carry over?
        if 'Carry over' in self.df.columns:
            self.df['Has_Carry_Over'] = self.df['Carry over'].apply(
                lambda x: str(x).strip().lower() == 'v' if pd.notna(x) else False
            )
        else:
            self.df['Has_Carry_Over'] = False

        # Cycle Time en días
        self.df['Cycle_Time_Days'] = self.df.apply(
            lambda row: self._calculate_cycle_time(row),
            axis=1
        )

        # Puntos efectivos (Puntos Logrados si existe, sino Estimación Original)
        self.df['Effective_Points'] = self.df.apply(
            lambda row: self._get_effective_points(row),
            axis=1
        )

        # Es bug?
        if 'Tipo Tarea' in self.df.columns:
            self.df['Is_Bug'] = self.df['Tipo Tarea'].str.lower().str.contains('bug', na=False)
        else:
            self.df['Is_Bug'] = False

    def _calculate_cycle_time(self, row: pd.Series) -> float:
        """
        Calcula el cycle time para una tarea.

        Args:
            row: Fila del DataFrame.

        Returns:
            Cycle time en días, o NaN si no es posible calcular.
        """
        start = row.get('Fecha Inicio')
        end = row.get('Fecha Ready for Production')

        if pd.isna(start) or pd.isna(end):
            return np.nan

        try:
            delta = end - start
            return delta.days
        except:
            return np.nan

    def _get_effective_points(self, row: pd.Series) -> float:
        """
        Obtiene los puntos efectivos para una tarea.

        Prioridad: Puntos Logrados > Estimación Original

        Args:
            row: Fila del DataFrame.

        Returns:
            Puntos efectivos.
        """
        puntos_logrados = row.get('Puntos Logrados')
        estimacion_original = row.get('Estimación Original')

        # Si hay Puntos Logrados, usar esos
        if pd.notna(puntos_logrados) and puntos_logrados > 0:
            return puntos_logrados

        # Si no, usar Estimación Original
        if pd.notna(estimacion_original):
            return estimacion_original

        return 0.0

    def _filter_invalid_data(self) -> None:
        """Filtra datos no válidos para el análisis."""
        logger.debug("Filtrando datos no válidos...")

        initial_count = len(self.df)

        # Filtrar solo sprints completados
        self.df = self.df[self.df['Sprint_Completed'] == True]

        # Filtrar tareas con sprint válido
        self.df = self.df[self.df['Sprint'].notna() & (self.df['Sprint'] != 'nan')]

        filtered_count = initial_count - len(self.df)
        if filtered_count > 0:
            logger.info(f"Filtradas {filtered_count} filas (sprints no completados o inválidos)")

    def _add_month_mapping(self) -> None:
        """Agrega el mapeo de sprints a meses."""
        logger.debug("Agregando mapeo de meses...")

        self.df['Month'] = self.df['Sprint'].map(self.sprint_mapping)

        # Verificar sprints sin mapeo
        unmapped_sprints = self.df[self.df['Month'].isna()]['Sprint'].unique()
        if len(unmapped_sprints) > 0:
            logger.warning(f"Sprints sin mapeo a mes: {unmapped_sprints}")
            print_warning(f"Sprints sin mapeo a mes: {', '.join(unmapped_sprints)}")

    def get_processed_data(self) -> pd.DataFrame:
        """
        Obtiene el DataFrame procesado.

        Returns:
            DataFrame procesado.
        """
        return self.df.copy()

    def get_summary_stats(self) -> Dict[str, any]:
        """
        Obtiene estadísticas resumidas del procesamiento.

        Returns:
            Diccionario con estadísticas.
        """
        total_tasks = len(self.df)
        completed_sprints = self.df['Sprint'].nunique()
        delivered_tasks = self.df['Is_Delivered'].sum()
        copied_tasks = self.df['Is_Copy'].sum()
        tasks_with_carry_over = self.df['Has_Carry_Over'].sum()

        return {
            'total_tasks': total_tasks,
            'completed_sprints': completed_sprints,
            'delivered_tasks': int(delivered_tasks),
            'copied_tasks': int(copied_tasks),
            'tasks_with_carry_over': int(tasks_with_carry_over),
            'team_type': self.team_type,
            'delivery_states': self.delivery_states
        }

    def print_summary(self) -> None:
        """Imprime un resumen del procesamiento."""
        stats = self.get_summary_stats()

        print("\n" + "=" * 60)
        print("RESUMEN DE PROCESAMIENTO")
        print("=" * 60)
        print(f"\nTipo de equipo: {stats['team_type']}")
        print(f"Total de tareas procesadas: {stats['total_tasks']}")
        print(f"Sprints completados: {stats['completed_sprints']}")
        print(f"Tareas entregadas: {stats['delivered_tasks']}")
        print(f"Tareas copiadas (incluidas en métricas): {stats['copied_tasks']}")
        print(f"Tareas con carry over: {stats['tasks_with_carry_over']}")

        # Mostrar sprints únicos
        sprints = sorted(self.df['Sprint'].unique())
        print(f"\nSprints: {', '.join(sprints)}")

        # Mostrar meses únicos
        if 'Month' in self.df.columns:
            months = sorted(self.df['Month'].dropna().unique())
            if months:
                print(f"Meses: {', '.join(months)}")


def process_data(
    df: pd.DataFrame,
    team_type: Literal['Productivo', 'En Desarrollo'],
    sprint_mapping: Dict[str, str] = None,
    verbose: bool = False
) -> pd.DataFrame:
    """
    Función de conveniencia para procesar datos en un solo paso.

    Args:
        df: DataFrame con datos crudos.
        team_type: Tipo de equipo.
        sprint_mapping: Mapeo de sprints a meses.
        verbose: Si es True, imprime resumen.

    Returns:
        DataFrame procesado.
    """
    processor = DataProcessor(df, team_type, sprint_mapping)
    processed_df = processor.process()

    if verbose:
        processor.print_summary()

    return processed_df
