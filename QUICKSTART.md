# Guía de Inicio Rápido

## Instalación en 3 pasos

### 1. Instalar dependencias

```bash
pip install -r requirements.txt
```

O si usa Python 3:

```bash
python3 -m pip install -r requirements.txt
```

### 2. Preparar su archivo Excel

Exporte su board de Monday.com como Excel (.xlsx). Asegúrese de que contenga todas las columnas requeridas (ver README.md para la lista completa).

### 3. Ejecutar el analizador

```bash
python3 metrics_analyzer/main.py --input TU_ARCHIVO.xlsx
```

El programa le hará algunas preguntas:

1. **Tipo de equipo**:
   - Opción 1: Productivo (estados entregados: 11-13)
   - Opción 2: En Desarrollo (estados entregados: 9-13)
     - Nota: Excluye automáticamente tareas en estado 9 con 0 puntos estimados

2. **Tamaño del equipo**: Ingrese el número de miembros

3. **Mapeo de sprints**:
   - Presione 's' para usar el mapeo por defecto
   - Presione 'n' para ingresar uno personalizado

## Ejemplo Completo

```bash
# Instalar dependencias
python3 -m pip install -r requirements.txt

# Ejecutar con el archivo de ejemplo
python3 metrics_analyzer/main.py --input Backlog_Planning_No_paquetizado_All_Tasks_1762742798.xlsx

# Cuando se le pregunte:
# - Tipo de equipo: 1 (Productivo)
# - Tamaño del equipo: 5
# - Mapeo de sprints: s (usar por defecto)
```

## Archivos Generados

Después de ejecutar el programa, encontrará en el directorio actual:

1. `Metricas_Performance_Equipo.xlsx` - Reporte Excel con 3 hojas
2. `metricas_por_sprint_dashboard.png` - Dashboard visual de sprints
3. `metricas_por_mes_dashboard.png` - Dashboard visual de meses

## Opciones Avanzadas

```bash
# Guardar en un directorio específico
python3 metrics_analyzer/main.py --input archivo.xlsx --output ./reportes/

# Usar mapeo de sprints personalizado (sin prompts)
python3 metrics_analyzer/main.py --input archivo.xlsx --sprint-map "Sprint 2:Julio,Sprint 3:Agosto"

# Solo generar Excel (sin gráficos)
python3 metrics_analyzer/main.py --input archivo.xlsx --excel-only

# Solo generar gráficos (sin Excel)
python3 metrics_analyzer/main.py --input archivo.xlsx --charts-only

# Modo verbose para debugging
python3 metrics_analyzer/main.py --input archivo.xlsx --verbose
```

## Solución de Problemas

### Error: "Columnas faltantes"

Verifique que su archivo Excel tenga todas las columnas requeridas. La lista completa está en README.md.

### Error: "No hay sprints válidos"

Asegúrese de que:
- La columna "Sprint Completed?" tenga al menos un valor "v"
- La columna "Sprint" tenga valores

### Los gráficos no se muestran

Los gráficos se guardan como archivos PNG en el directorio actual. No se muestran en pantalla.

## Ayuda

Para ver todas las opciones disponibles:

```bash
python3 metrics_analyzer/main.py --help
```

Para más información detallada, consulte el archivo README.md.

## Resultados de Prueba

Con el archivo de ejemplo incluido:
- **Sprints analizados**: 8
- **Tareas entregadas**: 50
- **Throughput promedio**: 6.2 tareas/sprint
- **Velocity promedio**: 23.5 puntos/sprint
- **Predictibilidad promedio**: 88.2%
- **Eficiencia promedio**: 4.7 puntos/persona

¡Listo para analizar sus propios datos!
