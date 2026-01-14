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
    print_info,
    calculate_business_days,
    extract_sprint_number
)


logger = logging.getLogger(__name__)


class DataProcessor:
    """Procesador de datos de Monday.com."""

    def __init__(
        self,
        df: pd.DataFrame,
        team_type: Literal['Productivo', 'En Desarrollo'] = 'Productivo',
        sprint_mapping: Dict[str, str] = None,
        delivery_date_column: str = 'Fecha Término'
    ):
        """
        Inicializa el procesador de datos.

        Args:
            df: DataFrame con los datos crudos.
            team_type: Tipo de equipo ('Productivo' o 'En Desarrollo').
            sprint_mapping: Mapeo de sprints a meses. Si es None, usa el por defecto.
            delivery_date_column: Columna de fecha a usar como fecha de entrega para Cycle Time.
        """
        self.raw_df = df.copy()
        self.df = df.copy()
        self.team_type = team_type
        self.sprint_mapping = sprint_mapping or DEFAULT_SPRINT_MAPPING
        self.delivery_date_column = delivery_date_column

        # Definir estados de entrega según tipo de equipo
        if team_type == 'Productivo':
            self.delivery_states = DELIVERY_STATES_PRODUCTIVE
        else:
            self.delivery_states = DELIVERY_STATES_DEVELOPMENT

        logger.info(f"Procesador inicializado para equipo tipo: {team_type}")
        logger.info(f"Usando columna de fecha de entrega: {delivery_date_column}")

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

        # Extraer número unificado de sprint (para agrupar sprints con mismo número)
        self.df['Sprint_Unified'] = self.df['Sprint'].apply(extract_sprint_number)

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
        Calcula el cycle time para una tarea en días hábiles.

        Solo calcula para tareas en estado DoD.
        Fecha DoD: Prioridad 1: Fecha Ready for Production, Prioridad 2: Fecha Término

        Args:
            row: Fila del DataFrame.

        Returns:
            Cycle time en días hábiles, o NaN si no es posible calcular.
        """
        # Solo calcular para tareas en DoD
        if not row.get('Is_Delivered', False):
            return np.nan

        start = row.get('Fecha Inicio')

        # Determinar fecha de DoD con prioridad
        # Prioridad 1: Fecha Ready for Production
        end = row.get('Fecha Ready for Production')

        # Prioridad 2: Si no existe o es NaN, usar Fecha Término
        if pd.isna(end):
            end = row.get('Fecha Término')

        if pd.isna(start) or pd.isna(end):
            return np.nan

        try:
            # Calcular días hábiles en lugar de días calendario
            business_days = calculate_business_days(start, end)
            return business_days if business_days is not None else np.nan
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

        # Para equipos En Desarrollo: filtrar tareas en estado 9 con 0 puntos estimados
        # Estas son tareas que Monday no permite cerrar y se arrastran con 0 puntos
        if self.team_type == 'En Desarrollo':
            estado_9_zero_points = (
                (self.df['Estado'] == '9. Certificado QA') &
                (self.df['Estimación Original'] == 0)
            )
            estado_9_zero_points_count = estado_9_zero_points.sum()

            if estado_9_zero_points_count > 0:
                logger.info(
                    f"Filtrando {estado_9_zero_points_count} tareas en estado 9 con 0 puntos estimados "
                    f"(equipos En Desarrollo)"
                )

            self.df = self.df[~estado_9_zero_points]

        filtered_count = initial_count - len(self.df)
        if filtered_count > 0:
            logger.info(f"Filtradas {filtered_count} filas en total")

    def _add_month_mapping(self) -> None:
        """Agrega el mapeo de sprints a meses usando coincidencia parcial."""
        logger.debug("Agregando mapeo de meses...")

        def map_sprint_to_month(sprint_name: str) -> str:
            """
            Mapea un sprint a un mes buscando coincidencia parcial.

            Args:
                sprint_name: Nombre del sprint (ej: "Sprint 8 FIDSIN").

            Returns:
                Mes asociado o None si no hay coincidencia.
            """
            if pd.isna(sprint_name):
                return None

            sprint_str = str(sprint_name)

            # Buscar si alguna clave del mapeo está contenida en el nombre del sprint
            for sprint_key, month in self.sprint_mapping.items():
                if sprint_key in sprint_str:
                    return month

            return None

        self.df['Month'] = self.df['Sprint'].apply(map_sprint_to_month)

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
    delivery_date_column: str = 'Fecha Término',
    verbose: bool = False
) -> pd.DataFrame:
    """
    Función de conveniencia para procesar datos en un solo paso.

    Args:
        df: DataFrame con datos crudos.
        team_type: Tipo de equipo.
        sprint_mapping: Mapeo de sprints a meses.
        delivery_date_column: Columna de fecha a usar como fecha de entrega para Cycle Time.
        verbose: Si es True, imprime resumen.

    Returns:
        DataFrame procesado.
    """
    processor = DataProcessor(df, team_type, sprint_mapping, delivery_date_column)
    processed_df = processor.process()

    if verbose:
        processor.print_summary()

    return processed_df
