import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import calendar

# Configurar página
st.set_page_config(page_title="Agenda de Federico", page_icon="📚", layout="wide")

# Colores por materia
COLORES_MATERIA = {
    "Matemática": "#FF6B6B",
    "Astronomía": "#4ECDC4",
    "Química": "#FFE66D",
    "Biología": "#95E1D3",
    "Literatura": "#C7CEEA",
    "Historia": "#AA96DA",
    "Inglés": "#FCBAD3",
    "Física": "#A8D8EA",
    "Filosofía": "#AA96DA",
    "Comunicación visual": "#FFB4B4"
}

# Función para convertir fecha a formato latinoamericano
def formato_fecha_la(fecha_str):
    try:
        fecha_obj = datetime.strptime(fecha_str, "%Y-%m-%d")
        return fecha_obj.strftime("%d/%m/%Y")
    except:
        return fecha_str

# Inicializar conexión a base de datos
conn = sqlite3.connect("tareas.db", check_same_thread=False)
cursor = conn.cursor()

# Crear tabla si no existe
cursor.execute("""
CREATE TABLE IF NOT EXISTS tareas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    materia TEXT,
    tarea TEXT,
    fecha TEXT,
    estado TEXT
)
""")
conn.commit()

# Inicializar session state
if 'agregar_exitoso' not in st.session_state:
    st.session_state.agregar_exitoso = False

# Título principal
st.title("📚 Agenda de Federico")
st.markdown("---")

# Sección para agregar tareas
st.subheader("➕ Agregar Nueva Tarea")

col1, col2, col3 = st.columns(3)

with col1:
    materia = st.selectbox(
        "Selecciona la materia",
        ["Matemática", "Astronomía", "Química", "Biología", "Literatura",
         "Historia", "Inglés", "Física", "Filosofía", "Comunicación visual"]
    )

with col2:
    tarea = st.text_input("Describe la tarea", placeholder="Ej: Hacer ejercicios del capítulo 5")

with col3:
    fecha = st.date_input("Fecha límite")

# Botón para agregar
if st.button("➕ Agregar tarea", use_container_width=True, type="primary"):
    if tarea.strip():  # Validar que la tarea no esté vacía
        cursor.execute(
            "INSERT INTO tareas (materia, tarea, fecha, estado) VALUES (?, ?, ?, ?)",
            (materia, tarea, str(fecha), "pendiente")
        )
        conn.commit()
        st.session_state.agregar_exitoso = True
        st.success("✅ ¡Tarea agregada correctamente!")
    else:
        st.error("❌ Por favor describe la tarea")

st.markdown("---")

# Obtener todas las tareas
df_pendientes = pd.read_sql_query(
    "SELECT * FROM tareas WHERE estado='pendiente' ORDER BY fecha ASC",
    conn
)

df_completadas = pd.read_sql_query(
    "SELECT * FROM tareas WHERE estado='hecho' ORDER BY fecha DESC",
    conn
)

# Sección de tareas pendientes (ORDENADAS POR FECHA)
st.subheader("⏳ Tareas Pendientes")

if df_pendientes.empty:
    st.info("✨ ¡No hay tareas pendientes! Buen trabajo")
else:
    # Mostrar cada tarea como tarjeta con color - YA ESTÁN ORDENADAS POR FECHA
    for index, row in df_pendientes.iterrows():
        color = COLORES_MATERIA.get(row['materia'], "#CCCCCC")
        fecha_formateada = formato_fecha_la(row['fecha'])
        
        # Calcular días restantes
        fecha_obj = datetime.strptime(row['fecha'], "%Y-%m-%d")
        hoy = datetime.now()
        dias_restantes = (fecha_obj - hoy).days
        
        # Determinar urgencia
        if dias_restantes < 0:
            urgencia = "⚠️ VENCIDA"
            color_urgencia = "#FF0000"
        elif dias_restantes == 0:
            urgencia = "🔴 HOY"
            color_urgencia = "#FF6347"
        elif dias_restantes <= 3:
            urgencia = "🟠 URGENTE"
            color_urgencia = "#FF8C00"
        else:
            urgencia = f"🟢 En {dias_restantes} días"
            color_urgencia = "#28A745"
        
        # Crear HTML personalizado con color
        html_card = f"""
        <div style="border-left: 5px solid {color}; padding: 15px; margin: 10px 0; border-radius: 5px; background-color: #f8f9fa;">
            <div style="display: flex; justify-content: space-between; align-items: start;">
                <div style="flex: 1;">
                    <h4 style="margin: 0; color: {color};">📚 {row['materia']}</h4>
                    <p style="margin: 5px 0; color: #333; font-size: 1.1em;">✏️ {row['tarea']}</p>
                    <div style="display: flex; gap: 15px; margin-top: 10px;">
                        <p style="margin: 0; color: #666; font-size: 0.9em;">📅 {fecha_formateada}</p>
                        <p style="margin: 0; color: {color_urgencia}; font-size: 0.9em; font-weight: bold;">{urgencia}</p>
                    </div>
                </div>
            </div>
        </div>
        """
        st.markdown(html_card, unsafe_allow_html=True)
        
        col1, col2 = st.columns([3, 1])
        with col2:
            if st.button("✅ Hecho", key=f"hecho_{row['id']}", use_container_width=True):
                cursor.execute(
                    "UPDATE tareas SET estado='hecho' WHERE id=?",
                    (row['id'],)
                )
                conn.commit()
                st.rerun()

st.markdown("---")

# CALENDARIO VISUAL CON ENTREGAS - MEJORADO
st.subheader("📅 Calendario de Entregas")

# Crear diccionario de fechas con tareas
fechas_tareas = {}
for idx, row in df_pendientes.iterrows():
    fecha = row['fecha']
    if fecha not in fechas_tareas:
        fechas_tareas[fecha] = []
    fechas_tareas[fecha].append(row)

# Selector de mes y año
col1, col2 = st.columns(2)
with col1:
    mes = st.selectbox("Mes", range(1, 13), format_func=lambda x: calendar.month_name[x], key="mes_select")
with col2:
    año = st.number_input("Año", min_value=2024, max_value=2030, value=datetime.now().year, key="año_select")

# Generar calendario
cal = calendar.monthcalendar(año, mes)
dias_semana = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]

st.write(f"### {calendar.month_name[mes]} {año}")

# Header con días de la semana
cols = st.columns(7)
for i, dia in enumerate(dias_semana):
    with cols[i]:
        st.write(f"<div style='text-align: center; font-weight: bold; padding: 10px; color: #333;'>{dia}</div>", unsafe_allow_html=True)

# Crear grid de días
for semana in cal:
    cols = st.columns(7)
    for i, dia in enumerate(semana):
        with cols[i]:
            if dia == 0:
                st.write("")
            else:
                fecha_str = f"{año}-{mes:02d}-{dia:02d}"
                
                # Buscar tareas para este día
                tareas_dia = fechas_tareas.get(fecha_str, [])
                
                # Verificar si es hoy
                hoy = datetime.now()
                es_hoy = (datetime(año, mes, dia) == datetime(hoy.year, hoy.month, hoy.day))
                
                if tareas_dia:
                    # Hay tareas este día - mostrar con color
                    colores_dia = [COLORES_MATERIA.get(t['materia'], "#CCCCCC") for t in tareas_dia]
                    color_principal = colores_dia[0]
                    
                    # Crear etiquetas de materias
                    materias_html = ""
                    for tarea_item in tareas_dia[:3]:  # Mostrar máximo 3
                        materia_nombre = tarea_item['materia']
                        color_materia = COLORES_MATERIA.get(materia_nombre, "#CCCCCC")
                        materias_html += f"<span style='background-color: {color_materia}; color: white; padding: 2px 6px; border-radius: 3px; font-size: 0.7em; margin: 2px; display: inline-block;'>{materia_nombre}</span>"
                    
                    html_dia = f"""
                    <div style="border: 2px solid {color_principal}; padding: 8px; border-radius: 5px; background-color: {color_principal}15; text-align: center; min-height: 70px; display: flex; flex-direction: column; justify-content: space-between; {'background-color: ' + color_principal + '30;' if es_hoy else ''}">
                        <p style="margin: 0; font-weight: bold; color: #333; font-size: 1.2em;">{"🟦 " if es_hoy else ""}{dia}</p>
                        <div style="font-size: 0.75em; display: flex; flex-wrap: wrap; gap: 2px; justify-content: center;">
                            {materias_html}
                        </div>
                        <p style="margin: 2px 0; font-size: 0.8em; color: {color_principal};">{'●' * len(tareas_dia)}</p>
                    </div>
                    """
                    st.markdown(html_dia, unsafe_allow_html=True)
                    
                    # Mostrar tareas en expandir
                    with st.expander(f"Tareas del {dia}/{mes:02d} ({len(tareas_dia)})"):
                        for tarea_item in tareas_dia:
                            color_mat = COLORES_MATERIA.get(tarea_item['materia'], "#CCCCCC")
                            st.markdown(f"<div style='padding: 10px; border-left: 4px solid {color_mat}; margin: 5px 0; background-color: #f8f9fa;'><b style='color: {color_mat};'>{tarea_item['materia']}</b><br>{tarea_item['tarea']}</div>", unsafe_allow_html=True)
                else:
                    # Sin tareas
                    bg_hoy = "background-color: #E3F2FD;" if es_hoy else ""
                    html_vacio = f"<div style='padding: 8px; text-align: center; border: 1px solid #ddd; border-radius: 5px; min-height: 70px; display: flex; align-items: center; justify-content: center; color: #999; {bg_hoy}'>{"🟦 " if es_hoy else ""}{dia}</div>"
                    st.markdown(html_vacio, unsafe_allow_html=True)

st.markdown("---")

# Sección de tareas completadas
st.subheader("✅ Tareas Completadas")

if df_completadas.empty:
    st.info("Aún no has completado ninguna tarea")
else:
    # Mostrar en tabla con fechas latinoamericanas
    df_mostrar = df_completadas[['materia', 'tarea', 'fecha']].copy()
    df_mostrar['fecha'] = df_mostrar['fecha'].apply(formato_fecha_la)
    df_mostrar.columns = ['Materia', 'Tarea', 'Fecha']
    st.dataframe(df_mostrar, use_container_width=True, hide_index=True)
    
    # Opción para limpiar tareas completadas
    if st.button("🗑️ Limpiar tareas completadas", use_container_width=True):
        cursor.execute("DELETE FROM tareas WHERE estado='hecho'")
        conn.commit()
        st.success("Tareas completadas eliminadas")
        st.rerun()

# Estadísticas
st.markdown("---")
st.subheader("📊 Estadísticas")

col1, col2, col3, col4 = st.columns(4)

total_tareas = len(df_pendientes) + len(df_completadas)
completadas = len(df_completadas)
pendientes = len(df_pendientes)

# Calcular tareas urgentes (próximos 3 días)
tareas_urgentes = 0
for idx, row in df_pendientes.iterrows():
    fecha_obj = datetime.strptime(row['fecha'], "%Y-%m-%d")
    hoy = datetime.now()
    dias_restantes = (fecha_obj - hoy).days
    if dias_restantes <= 3:
        tareas_urgentes += 1

with col1:
    st.metric("📋 Pendientes", pendientes)
with col2:
    st.metric("✅ Completadas", completadas)
with col3:
    st.metric("🔴 Urgentes", tareas_urgentes)
with col4:
    if total_tareas > 0:
        porcentaje = (completadas / total_tareas) * 100
        st.metric("📈 Progreso", f"{porcentaje:.0f}%")
    else:
        st.metric("📈 Progreso", "0%")

# Tabla de colores por materia
st.markdown("---")
st.subheader("🎨 Código de Colores por Materia")

col1, col2, col3, col4, col5 = st.columns(5)
materias = list(COLORES_MATERIA.keys())

for idx, materia in enumerate(materias):
    col = [col1, col2, col3, col4, col5][idx % 5]
    with col:
        color = COLORES_MATERIA[materia]
        html = f"<div style='background-color: {color}; padding: 10px; border-radius: 5px; text-align: center; color: #333; font-weight: bold;'>{materia}</div>"
        st.markdown(html, unsafe_allow_html=True)
