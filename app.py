import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
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

# Sección de tareas pendientes
st.subheader("⏳ Tareas Pendientes")

df_pendientes = pd.read_sql_query(
    "SELECT * FROM tareas WHERE estado='pendiente' ORDER BY fecha ASC",
    conn
)

if df_pendientes.empty:
    st.info("✨ ¡No hay tareas pendientes! Buen trabajo")
else:
    # Mostrar cada tarea como tarjeta con color
    for index, row in df_pendientes.iterrows():
        color = COLORES_MATERIA.get(row['materia'], "#CCCCCC")
        
        # Crear HTML personalizado con color
        html_card = f"""
        <div style="border-left: 5px solid {color}; padding: 15px; margin: 10px 0; border-radius: 5px; background-color: #f8f9fa;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <h4 style="margin: 0; color: {color};">📚 {row['materia']}</h4>
                    <p style="margin: 5px 0; color: #333;">✏️ {row['tarea']}</p>
                    <p style="margin: 0; color: #666; font-size: 0.9em;">📅 {row['fecha']}</p>
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

# CALENDARIO VISUAL CON ENTREGAS
st.subheader("📅 Calendario de Entregas")

# Obtener todas las tareas pendientes
df_todas = pd.read_sql_query(
    "SELECT * FROM tareas WHERE estado='pendiente'",
    conn
)

# Crear diccionario de fechas
fechas_tareas = {}
for idx, row in df_todas.iterrows():
    fecha = row['fecha']
    if fecha not in fechas_tareas:
        fechas_tareas[fecha] = []
    fechas_tareas[fecha].append(row)

# Selector de mes y año
col1, col2 = st.columns(2)
with col1:
    mes = st.selectbox("Mes", range(1, 13), format_func=lambda x: calendar.month_name[x])
with col2:
    año = st.number_input("Año", min_value=2024, max_value=2030, value=datetime.now().year)

# Generar calendario
cal = calendar.monthcalendar(año, mes)
dias_semana = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]

st.write(f"### {calendar.month_name[mes]} {año}")

# Header con días de la semana
cols = st.columns(7)
for i, dia in enumerate(dias_semana):
    with cols[i]:
        st.write(f"**{dia}**")

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
                
                if tareas_dia:
                    # Hay tareas este día - mostrar con color
                    colores_dia = [COLORES_MATERIA.get(t['materia'], "#CCCCCC") for t in tareas_dia]
                    color_principal = colores_dia[0]
                    
                    html_dia = f"""
                    <div style="border: 2px solid {color_principal}; padding: 8px; border-radius: 5px; background-color: {color_principal}20; text-align: center;">
                        <p style="margin: 0; font-weight: bold; color: #333;">{dia}</p>
                        <p style="margin: 3px 0; font-size: 0.8em; color: {color_principal};">{'🔴' * len(tareas_dia)}</p>
                    </div>
                    """
                    st.markdown(html_dia, unsafe_allow_html=True)
                    
                    # Mostrar tareas en expandir
                    with st.expander(f"Ver tareas del {dia}"):
                        for tarea in tareas_dia:
                            st.write(f"**{tarea['materia']}**: {tarea['tarea']}")
                else:
                    # Sin tareas
                    st.write(f"<div style='padding: 8px; text-align: center; border: 1px solid #ddd; border-radius: 5px;'>{dia}</div>", unsafe_allow_html=True)

st.markdown("---")

# Sección de tareas completadas
st.subheader("✅ Tareas Completadas")

df_completadas = pd.read_sql_query(
    "SELECT * FROM tareas WHERE estado='hecho' ORDER BY fecha DESC",
    conn
)

if df_completadas.empty:
    st.info("Aún no has completado ninguna tarea")
else:
    # Mostrar en tabla
    df_mostrar = df_completadas[['materia', 'tarea', 'fecha']].copy()
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

col1, col2, col3 = st.columns(3)

total_tareas = len(df_pendientes) + len(df_completadas)
completadas = len(df_completadas)
pendientes = len(df_pendientes)

with col1:
    st.metric("Tareas Pendientes", pendientes)
with col2:
    st.metric("Tareas Completadas", completadas)
with col3:
    if total_tareas > 0:
        porcentaje = (completadas / total_tareas) * 100
        st.metric("Progreso", f"{porcentaje:.0f}%")
    else:
        st.metric("Progreso", "0%")

# Tabla de colores por materia
st.markdown("---")
st.subheader("🎨 Código de Colores")

col1, col2, col3, col4, col5 = st.columns(5)
materias = list(COLORES_MATERIA.keys())

for idx, materia in enumerate(materias):
    col = [col1, col2, col3, col4, col5][idx % 5]
    with col:
        color = COLORES_MATERIA[materia]
        html = f"<div style='background-color: {color}; padding: 10px; border-radius: 5px; text-align: center; color: #333; font-weight: bold;'>{materia}</div>"
        st.markdown(html, unsafe_allow_html=True)
