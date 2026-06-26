from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from database import obtener_conexion
from typing import Optional

router = APIRouter(prefix="/admin")
templates = Jinja2Templates(directory=".")

@router.get("", response_class=HTMLResponse)
def panel_admin(request: Request, msg: Optional[str] = None):
    conn = obtener_conexion()
    preguntas, usuarios, metricas_materias, mejores_examenes = [], [], [], []
    
    if conn:
        try:
            with conn.cursor() as cursor:
                
                cursor.execute("""
                    SELECT m.nombre, COUNT(i.id_intento), COALESCE(ROUND(AVG(i.nota_final), 1), 0), COUNT(CASE WHEN i.aprobado THEN 1 END)
                    FROM materias m LEFT JOIN examenes e ON m.id_materia = e.id_materia
                    LEFT JOIN intentos_examen i ON e.id_examen = i.id_examen GROUP BY m.nombre;
                """)
                metricas_materias = cursor.fetchall() or []
                
                
                cursor.execute("""
                    SELECT u.nombre, e.titulo, m.nombre, i.nota_final FROM intentos_examen i
                    JOIN usuarios u ON i.id_usuario = u.id_usuario JOIN examenes e ON i.id_examen = e.id_examen
                    JOIN materias m ON e.id_materia = m.id_materia ORDER BY i.nota_final DESC;
                """)
                mejores_examenes = cursor.fetchall() or []

                
                cursor.execute("SELECT p.id_pregunta, p.pregunta, m.nombre, p.nivel_dificultad FROM preguntas p JOIN materias m ON p.id_materia = m.id_materia ORDER BY p.id_pregunta ASC;")
                preguntas = cursor.fetchall() or []

                
                cursor.execute("""
                    SELECT u.id_usuario, u.nombre, u.correo, u.puntaje_total, COUNT(lu.id_logro) FROM usuarios u
                    LEFT JOIN logros_usuario lu ON u.id_usuario = lu.id_usuario WHERE u.rol = 'estudiante' 
                    GROUP BY u.id_usuario, u.nombre, u.correo, u.puntaje_total;
                """)
                usuarios = cursor.fetchall() or []
        except Exception as e:
            print(f"⚠️ Error en consultas del Panel Admin: {e}")
        finally:
            conn.close()

    if not metricas_materias:
        metricas_materias = [("Matemáticas", 0, 0, 0), ("Español", 0, 0, 0), ("Biología", 0, 0, 0)]

    return templates.TemplateResponse(request=request, name="Admin.html", context={
        "preguntas": preguntas, "usuarios": usuarios,
        "metricas_materias": metricas_materias, "mejores_examenes": mejores_examenes, "msg": msg
    })


@router.post("/preguntas/crear")
def crear_pregunta(pregunta: str = Form(...), id_materia: int = Form(...), nivel: int = Form(...), puntos: int = Form(...), opcion1: str = Form(...), opcion2: str = Form(...), opcion3: str = Form(...), correcta: int = Form(...)):
    conn = obtener_conexion()
    msg = ""
    if conn:
        try:
            with conn.cursor() as cursor:
                cursor.execute("INSERT INTO preguntas (id_materia, pregunta, nivel_dificultad, puntos_recompensa) VALUES (%s, %s, %s, %s) RETURNING id_pregunta;", (id_materia, pregunta, nivel, puntos))
                id_p = cursor.fetchone()[0]
                cursor.execute("INSERT INTO opciones (id_pregunta, opcion, es_correcta) VALUES (%s, %s, %s);", (id_p, opcion1, True if correcta==1 else False))
                cursor.execute("INSERT INTO opciones (id_pregunta, opcion, es_correcta) VALUES (%s, %s, %s);", (id_p, opcion2, True if correcta==2 else False))
                cursor.execute("INSERT INTO opciones (id_pregunta, opcion, es_correcta) VALUES (%s, %s, %s);", (id_p, opcion3, True if correcta==3 else False))
                conn.commit()
            msg = "Pregunta añadida correctamente al banco"
        except Exception as e:
            msg = "Error al guardar la pregunta"
        finally:
            conn.close()
    return RedirectResponse(url=f"/admin?msg={msg}", status_code=303)


@router.get("/preguntas/borrar/{id_pregunta}")
def borrar_pregunta(id_pregunta: int):
    conn = obtener_conexion()
    msg = ""
    if conn:
        try:
            with conn.cursor() as cursor:
                cursor.execute("DELETE FROM preguntas WHERE id_pregunta = %s;", (id_pregunta,))
                conn.commit()
            msg = "Pregunta eliminada del sistema"
        except Exception as e:
            msg = "No se pudo eliminar la pregunta"
        finally:
            conn.close()
    return RedirectResponse(url=f"/admin?msg={msg}", status_code=303)


@router.get("/estudiantes/eliminar/{id_usuario}")
def dar_baja_estudiante(id_usuario: int):
    conn = obtener_conexion()
    msg = ""
    if conn:
        try:
            with conn.cursor() as cursor:
                cursor.execute("DELETE FROM usuarios WHERE id_usuario = %s AND rol = 'estudiante';", (id_usuario,))
                conn.commit()
            msg = "Estudiante dado de baja correctamente"
        except Exception as e:
            msg = "No se pudo eliminar al estudiante"
        finally:
            conn.close()
    return RedirectResponse(url=f"/admin?msg={msg}", status_code=303)

