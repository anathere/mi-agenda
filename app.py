import streamlit as st
import sqlite3
import pandas as pd

conn = sqlite3.connect("tareas.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS tareas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    materia TEXT,
    tarea TEXT,
    fecha TEXT,
    estado TEXT
)
""")

st.title("Agenda de Federico")

materia = st.selectbox("Materia",[
"Matemática","Astronomía","Química","Biología","Literatura",
"Historia","Inglés","Física","Filosofía","Comunicación visual"
])

tarea = st.text_input("Tarea")

fecha = st.date_input("Fecha")

if st.button("Agregar tarea"):
    cursor.execute(
        "INSERT INTO tareas (materia,tarea,fecha,estado) VALUES (?,?,?,?)",
        (materia,tarea,str(fecha),"pendiente")
    )
    conn.commit()
    st.success("Tarea agregada")

st.subheader("Tareas pendientes")

df = pd.read_sql_query("SELECT * FROM tareas WHERE estado='pendiente'", conn)

for index,row in df.iterrows():

    col1,col2,col3,col4 = st.columns(4)

    col1.write(row["materia"])
    col2.write(row["tarea"])
    col3.write(row["fecha"])

    if col4.button("Hecho", key=row["id"]):

        cursor.execute(
            "UPDATE tareas SET estado='hecho' WHERE id=?",
            (row["id"],)
        )

        conn.commit()
        st.rerun()
        