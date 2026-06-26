from fastapi import FastAPI, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from database import obtener_conexion
from typing import Optional
import admin

app = FastAPI()


app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory=".")


app.include_router(admin.router)

@app.get("/", response_class=HTMLResponse)
def index_landing(request: Request):
    return templates.TemplateResponse(request=request, name="inicio_lynko.html")

@app.get("/login", response_class=HTMLResponse)
def vista_login(request: Request, error: Optional[str] = None, msg: Optional[str] = None):
    return templates.TemplateResponse(request=request, name="Login.html", context={"error": error, "msg": msg})

@app.get("/registro", response_class=HTMLResponse)
def vista_registro(request: Request, error: Optional[str] = None):
    return templates.TemplateResponse(request=request, name="Registro.html", context={"error": error})


@app.post("/login")
def procesar_login(correo: str = Form(...), contrasena: str = Form(...)):
    conn = obtener_conexion()
    if conn:
        try:
            with conn.cursor() as cursor:
                
                cursor.execute("SELECT id_usuario, correo, rol FROM usuarios WHERE correo = %s AND contraseña = %s AND activo = TRUE;", (correo, contrasena))
                usuario = cursor.fetchone()
                
                print("\n================ RASTREO DE LOGIN ================")
                print(f"🔍 Datos encontrados en BD para {correo}: {usuario}")
                
                if usuario:
                    id_u, correo_bd, rol = usuario[0], usuario[1], usuario[2]
                    print(f"👑 Rol detectado: '{rol}'")
                    
                   
                    if str(rol).strip().lower() == "admin":
                        print("🚀 REDIRECCIÓN ACTIVADA -> Panel de Administración (/admin)")
                        return RedirectResponse(url="/admin", status_code=303)
                    else:
                        print(f"🎓 REDIRECCIÓN ACTIVADA -> Ecosistema Estudiante (/inicio-estudiante/{id_u})")
                        return RedirectResponse(url=f"/inicio-estudiante/{id_u}", status_code=303)
                else:
                    print("❌ No se encontró ningún usuario con esas credenciales exactas.")
                print("===================================================\n")
        except Exception as e:
            print(f"⚠️ Error crítico en proceso de login: {e}")
        finally:
            conn.close()
    return RedirectResponse(url="/login?error=Credenciales incorrectas o usuario inactivo", status_code=303)


@app.post("/registro")
def procesar_registro(nombre: str = Form(...), correo: str = Form(...), contrasena: str = Form(...)):
    conn = obtener_conexion()
    if conn:
        try:
            with conn.cursor() as cursor:
                print("\n================ RASTREO DE REGISTRO ================")
                print(f"📝 Intentando registrar a: {nombre} ({correo})")
                

                cursor.execute("""
                    INSERT INTO usuarios (nombre, correo, contraseña, rol, puntaje_total, activo) 
                    VALUES (%s, %s, %s, 'estudiante', 0, TRUE) RETURNING id_usuario, rol;
                """, (nombre, correo, contrasena))
                
                resultado = cursor.fetchone()
                nuevo_id = resultado[0]
                rol_guardado = resultado[1]
                
                print(f"✅ Guardado con Éxito. ID: {nuevo_id} | Rol Asignado: '{rol_guardado}'")
                
                
                try:
                    cursor.execute("INSERT INTO logros_usuario (id_usuario, id_logro) VALUES (%s, 1);", (nuevo_id,))
                    print("🏆 Medalla de bienvenida inyectada correctamente.")
                except Exception as ex_medalla:
                    print(f"⚠️ Nota: No se pudo dar la medalla (tal vez el ID 1 de logros no existe): {ex_medalla}")
                
                conn.commit()
                print(f"🚀 MANDANDO DIRECTO A: /inicio-estudiante/{nuevo_id}")
                print("======================================================\n")
                
                return RedirectResponse(url=f"/inicio-estudiante/{nuevo_id}", status_code=303)
        except Exception as e:
            print(f"⚠️ Error al registrar usuario: {e}")
            return RedirectResponse(url="/registro?error=El correo ya está registrado en la plataforma", status_code=303)
        finally:
            conn.close()
    return RedirectResponse(url="/registro?error=Error de conexión con el servidor", status_code=303)


@app.get("/inicio-estudiante/{id_usuario}", response_class=HTMLResponse)
def dashboard_estudiante_logeado(id_usuario: int, request: Request):
    conn = obtener_conexion()
    nombre_usuario = "Estudiante"
    puntaje = 0
    if conn:
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT nombre, puntaje_total FROM usuarios WHERE id_usuario = %s;", (id_usuario,))
                datos = cursor.fetchone()
                if datos:
                    nombre_usuario = datos[0]
                    puntaje = datos[1]
        except Exception as e:
            print(f"⚠️ Error al cargar datos del estudiante: {e}")
        finally:
            conn.close()
            
    return templates.TemplateResponse(
        request=request, 
        name="inicio_lynko.html", 
        context={"id_usuario": id_usuario, "nombre": nombre_usuario, "puntos": puntaje}
    )
