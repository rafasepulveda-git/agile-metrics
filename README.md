# Analizador de Métricas de Performance Ágil

Herramienta de línea de comandos para analizar métricas de performance ágil a partir de exportaciones de Monday.com.

## Descripción

Esta aplicación permite a líderes de equipos de desarrollo analizar métricas clave de performance ágil, incluyendo:

- **Throughput**: Número de tareas entregadas por sprint/mes
- **Velocity**: Puntos de historia completados por sprint/mes
- **Cycle Time**: Tiempo promedio desde inicio hasta entrega
- **Predictibilidad**: Porcentaje de puntos comprometidos vs. entregados
- **Eficiencia**: Velocity por miembro del equipo
- **Retrabajo**: Porcentaje de puntos dedicados a bugs

## Características

- Carga y validación de archivos Excel de Monday.com
- Cálculo automático de métricas por sprint y por mes
- Generación de reportes Excel con formato condicional
- Creación de dashboards visuales (PNG)
- Soporte para equipos "Productivos" y "En Desarrollo"
- Configuración flexible de mapeo sprint-mes
- Interfaz CLI intuitiva con prompts interactivos
- Manejo robusto de errores y datos faltantes

## Requisitos

- Python 3.10 o superior
- pip (gestor de paquetes de Python)

## Instalación

1. **Clone o descargue el proyecto**

```bash
cd agile-metrics
```

2. **Cree un entorno virtual (recomendado)**

```bash
python -m venv venv

# En Windows
venv\Scripts\activate

# En macOS/Linux
source venv/bin/activate
```

3. **Instale las dependencias**

```bash
pip install -r requirements.txt
```

## Uso

### Uso Básico

```bash
python metrics_analyzer/main.py --input archivo_monday.xlsx
```

El programa le solicitará interactivamente:
- Tipo de equipo (Productivo o En Desarrollo)
- Número de miembros del equipo
- Mapeo de sprints a meses (o usar el por defecto)

### Opciones Avanzadas

```bash
# Especificar directorio de salida
python metrics_analyzer/main.py --input datos.xlsx --output ./reportes/

# Usar mapeo de sprints personalizado
python metrics_analyzer/main.py --input datos.xlsx --sprint-map "Sprint 2:Julio,Sprint 3:Agosto,Sprint 4:Agosto"

# Generar solo reporte Excel (sin gráficos)
python metrics_analyzer/main.py --input datos.xlsx --excel-only

# Generar solo gráficos (sin Excel)
python metrics_analyzer/main.py --input datos.xlsx --charts-only

# Modo verbose para debugging
python metrics_analyzer/main.py --input datos.xlsx --verbose

# Ver ayuda completa
python metrics_analyzer/main.py --help
```

## Formato del Archivo de Entrada

El archivo Excel debe ser una exportación de Monday.com con la siguiente estructura:

- **Fila 0**: Título del board (se omite)
- **Fila 1**: Headers de columnas
- **Filas 2+**: Datos de tareas

### Columnas Requeridas

```
- Name: Nombre de la tarea
- Dueño: Responsable
- Asignado: Persona asignada
- Estado: Estado actual (ej: "11. Ready for Product Release")
- Estado QA: Estado en QA
- Estado UAT: Estado en UAT
- Tipo Tarea: Tipo (Bug, HDU, Solicitud)
- Estimación Original: Story points estimados
- Puntos Logrados: Story points realmente logrados
- Task ID: Identificador único
- Fecha Inicio: Fecha de inicio
- Fecha Término: Fecha de término planeada
- Fecha Ready for Production: Fecha de llegada a producción
- Fecha paso a Producción: Fecha de despliegue
- Ciclos UAT: Número de ciclos de UAT
- Sprint: Sprint al que pertenece (ej: "Sprint 2")
- Sprint Completed?: Indica si el sprint fue completado (valor "v")
- Carry over: Indica si hay carry over (valor "v")
```

## Tipos de Equipo

### Equipo Productivo
Estados considerados como "entregados":
- 11. Ready for Product Release
- 12. Validación a Producción
- 13. Producción

### Equipo En Desarrollo
Estados considerados como "entregados":
- 9. Certificado QA
- 10. UAT
- 11. Ready for Product Release
- 12. Validación a Producción
- 13. Producción

## Outputs Generados

El programa genera tres archivos:

### 1. Metricas_Performance_Equipo.xlsx

Archivo Excel con tres hojas:

**Hoja 1: Resumen Ejecutivo**
- Información general del equipo
- Promedios de todas las métricas
- Mejor y peor sprint

**Hoja 2: Métricas por Sprint**
- Tabla detallada con todas las métricas por sprint
- Formato condicional (verde/amarillo/rojo) según umbrales

**Hoja 3: Métricas por Mes**
- Métricas agregadas mensualmente
- Promedios y totales por mes

### 2. metricas_por_sprint_dashboard.png

Dashboard visual con 6 gráficos:
- Throughput por sprint
- Velocity por sprint
- Cycle Time promedio por sprint
- Predictibilidad por sprint
- Eficiencia por sprint
- Retrabajo por sprint

### 3. metricas_por_mes_dashboard.png

Dashboard visual con 6 gráficos:
- Throughput por mes (total y promedio)
- Velocity por mes (total y promedio)
- Cycle Time promedio por mes
- Predictibilidad por mes
- Eficiencia por mes
- Retrabajo por mes

## Métricas Explicadas

### Throughput
**Qué es**: Número de tareas completadas y entregadas en un período.

**Cálculo**: Cuenta de tareas en estados de entrega (excluye copias).

**Interpretación**: Mayor throughput indica mayor capacidad de entrega del equipo.

### Velocity
**Qué es**: Suma de puntos de historia completados en un sprint.

**Cálculo**: Suma de "Puntos Logrados" (o "Estimación Original" si no hay Puntos Logrados) de tareas entregadas.

**Interpretación**: Mide la capacidad de trabajo del equipo. Útil para planning.

### Cycle Time
**Qué es**: Tiempo promedio desde que se inicia una tarea hasta que se completa.

**Cálculo**: Días entre "Fecha Inicio" y "Fecha Ready for Production".

**Interpretación**: Menor cycle time indica mayor agilidad. Identifica cuellos de botella.

### Predictibilidad
**Qué es**: Porcentaje de puntos comprometidos que realmente se entregaron.

**Cálculo**: (Puntos Entregados / Puntos Comprometidos) × 100

**Interpretación**:
- 70%+ : Excelente predictibilidad
- 40-70% : Predictibilidad media (mejorable)
- <40% : Baja predictibilidad (requiere acción)

### Eficiencia
**Qué es**: Velocity promedio por miembro del equipo.

**Cálculo**: Velocity / Número de miembros del equipo

**Interpretación**: Mide la productividad individual promedio. Útil para comparar con otros equipos.

### Retrabajo
**Qué es**: Porcentaje de esfuerzo dedicado a corregir bugs.

**Cálculo**: (Puntos de Bugs / Total de Puntos) × 100

**Interpretación**:
- 0-15% : Excelente calidad
- 15-30% : Calidad aceptable
- >30% : Alto retrabajo (requiere mejora de calidad)

## Reglas de Negocio

### Tareas Copiadas
Cuando una tarea no se completa en un sprint, se crea una copia con sufijo "(copy)" o "(copia)". **Las copias se excluyen automáticamente** de los cálculos de throughput y velocity para evitar doble contabilización.

### Sprints Completados
Solo se analizan sprints marcados como completados (`Sprint Completed? = "v"`). Esto asegura que las métricas reflejen períodos cerrados.

### Puntos Efectivos
Para calcular velocity:
1. Se intenta usar "Puntos Logrados" primero
2. Si no hay "Puntos Logrados", se usa "Estimación Original"
3. Esto asegura que siempre haya un valor para el cálculo

### Mapeo Sprint-Mes
Por defecto se asumen 2 sprints por mes:
```
Sprint 2 → Julio
Sprint 3 → Agosto
Sprint 4 → Agosto
Sprint 5 → Septiembre
...
```

Puede personalizar este mapeo según su calendario.

## Troubleshooting

### Error: "Columnas faltantes"
**Solución**: Verifique que el archivo Excel tenga todas las columnas requeridas con los nombres exactos.

### Error: "No hay sprints válidos"
**Solución**: Asegúrese de que:
- La columna "Sprint" tenga valores
- La columna "Sprint Completed?" tenga al menos un valor "v"

### Advertencia: "Sprints sin mapeo a mes"
**Solución**: Use la opción `--sprint-map` para especificar el mapeo personalizado, o actualice el mapeo por defecto en `config.py`.

### Error: "No hay datos de Cycle Time"
**Solución**: Las columnas "Fecha Inicio" y "Fecha Ready for Production" deben tener valores válidos. Este error es solo informativo; otras métricas se calcularán normalmente.

### Los gráficos no se generan
**Solución**:
- Verifique que matplotlib esté instalado correctamente
- En algunos sistemas, puede necesitar instalar tkinter: `sudo apt-get install python3-tk` (Linux)

## Estructura del Proyecto

```
agile-metrics/
├── metrics_analyzer/
│   ├── __init__.py
│   ├── config.py              # Configuraciones y constantes
│   ├── data_loader.py         # Carga y validación de Excel
│   ├── data_processor.py      # Limpieza y transformación
│   ├── metrics_calculator.py  # Cálculo de métricas
│   ├── report_generator.py    # Generación de Excel
│   ├── visualizations.py      # Generación de gráficos
│   ├── utils.py              # Funciones auxiliares
│   └── main.py               # CLI y punto de entrada
├── requirements.txt          # Dependencias Python
└── README.md                # Documentación (este archivo)
```

## Personalización

### Modificar Umbrales

Edite `metrics_analyzer/config.py`:

```python
THRESHOLDS = {
    'predictability_good': 70,    # Verde si >= 70%
    'predictability_warning': 40,  # Amarillo si >= 40%
    'rework_good': 15,            # Verde si <= 15%
    'rework_warning': 30,         # Amarillo si <= 30%
    ...
}
```

### Cambiar Colores de Gráficos

Edite `metrics_analyzer/config.py`:

```python
COLORS = {
    'primary': '#2E86AB',
    'secondary': '#A23B72',
    'success': '#06A77D',
    'warning': '#F77F00',
    'danger': '#D00000',
    ...
}
```

### Agregar Nuevos Estados de Entrega

Edite `metrics_analyzer/config.py`:

```python
DELIVERY_STATES_PRODUCTIVE = [
    '11. Ready for Product Release',
    '12. Validación a Producción',
    '13. Producción',
    '14. Tu Nuevo Estado'  # Agregar aquí
]
```

## Limitaciones Conocidas

- El programa asume que los nombres de columnas en Monday.com están en español
- Las fechas deben estar en formato válido de Excel
- Solo soporta archivos .xlsx (no .xls ni .csv)
- Los gráficos son estáticos (PNG), no interactivos

## Roadmap

Características planeadas para futuras versiones:

- [ ] Soporte para múltiples equipos simultáneos
- [ ] Comparación de períodos (sprint vs sprint anterior)
- [ ] Export de métricas a JSON/API
- [ ] Gráficos interactivos (HTML)
- [ ] Detección automática de tipo de equipo
- [ ] Sugerencias automáticas basadas en métricas
- [ ] Soporte para otros idiomas
- [ ] Integración directa con API de Monday.com

## Soporte

Para reportar bugs o solicitar características:
- Cree un issue en el repositorio del proyecto
- Incluya el archivo de entrada (si es posible) o un ejemplo similar
- Describa el error o comportamiento esperado
- Adjunte logs completos (use `--verbose`)

## Licencia

Este proyecto es de uso interno. Todos los derechos reservados.

## Autor

Desarrollado para facilitar el análisis de métricas ágiles en equipos de desarrollo.

---

**Versión**: 1.0.0
**Última actualización**: 2025
