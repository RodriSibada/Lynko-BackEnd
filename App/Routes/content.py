"""
RUTAS DE CONTENIDO - content.py

Endpoints para:
- Obtener materias disponibles
- Obtener preguntas de una materia
- Guardar progreso del usuario
- Obtener estadísticas del usuario
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime

from ..Config.database import SessionLocal
from ..Config.models import Usuario, Materia, Pregunta, Opcion, Progreso
from ..Config.schemas import UsuarioCreate

router = APIRouter(
    prefix="/api/content",
    tags=["contenido"]
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/materias")
async def obtener_materias(db: Session = Depends(get_db)):
    """
    Obtiene todas las materias disponibles
    
    Response:
    [
        {
            "id_materia": 1,
            "nombre": "Matemáticas",
            "descripcion": "Aprende matemática básica",
            "nivel": 1,
            "icon": "📐",
            "color": "#FF8C42"
        },
        ...
    ]
    """
    try:
        materias = db.query(Materia).all()
        
        resultado = []
        for materia in materias:
            resultado.append({
                "id_materia": materia.id_materia,
                "nombre": materia.nombre,
                "descripcion": getattr(materia, 'descripcion', 'Aprende con Lynko'),
                "nivel": getattr(materia, 'nivel', 1),
                "icon": getattr(materia, 'icono', '📚'),
                "color": getattr(materia, 'color', '#FF8C42')
            })
        
        print(f"✅ Materias obtenidas: {len(resultado)}")
        return resultado
    
    except Exception as e:
        print(f"❌ Error obteniendo materias: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error: {str(e)}"
        )



@router.get("/materias/{id_materia}")
async def obtener_materia(id_materia: int, db: Session = Depends(get_db)):
    """
    Obtiene detalles de una materia específica
    """
    try:
        materia = db.query(Materia).filter(
            Materia.id_materia == id_materia
        ).first()
        
        if not materia:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Materia no encontrada"
            )
        
        return {
            "id_materia": materia.id_materia,
            "nombre": materia.nombre,
            "descripcion": getattr(materia, 'descripcion', ''),
            "nivel": getattr(materia, 'nivel', 1),
            "icon": getattr(materia, 'icono', '📚'),
            "color": getattr(materia, 'color', '#FF8C42')
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error: {str(e)}"
        )



@router.get("/materias/{id_materia}/preguntas")
async def obtener_preguntas_materia(
    id_materia: int,
    db: Session = Depends(get_db)
):
    """
    Obtiene todas las preguntas de una materia
    
    Response:
    [
        {
            "id_pregunta": 1,
            "pregunta": "¿Cuál es 2+2?",
            "nivel": 1,
            "opciones": [
                {"id_opcion": 1, "texto": "3", "es_correcta": false},
                {"id_opcion": 2, "texto": "4", "es_correcta": true},
                ...
            ]
        },
        ...
    ]
    """
    try:
        preguntas = db.query(Pregunta).filter(
            Pregunta.id_materia == id_materia
        ).all()
        
        if not preguntas:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No hay preguntas en esta materia"
            )
        
        resultado = []
        for pregunta in preguntas:
            # Obtener opciones de esta pregunta
            opciones = db.query(Opcion).filter(
                Opcion.id_pregunta == pregunta.id_pregunta
            ).all()
            
            opciones_lista = []
            for opcion in opciones:
                opciones_lista.append({
                    "id_opcion": opcion.id_opcion,
                    "texto": opcion.opcion,
                    "es_correcta": opcion.es_correcta
                })
            
            resultado.append({
                "id_pregunta": pregunta.id_pregunta,
                "pregunta": pregunta.pregunta,
                "nivel": pregunta.nivel,
                "opciones": opciones_lista
            })
        
        print(f"✅ Preguntas obtenidas: {len(resultado)}")
        return resultado
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error: {str(e)}"
        )


@router.post("/responder")
async def guardar_respuesta(
    usuario_id: int,
    id_pregunta: int,
    id_opcion: int,
    db: Session = Depends(get_db)
):
    """
    Guarda la respuesta de un usuario a una pregunta
    
    Request:
    {
        "usuario_id": 1,
        "id_pregunta": 5,
        "id_opcion": 12
    }
    
    Response:
    {
        "es_correcta": true,
        "xp_ganado": 10,
        "mensaje": "¡Correcto!"
    }
    """
    try:
        # Obtener la opción seleccionada
        opcion = db.query(Opcion).filter(
            Opcion.id_opcion == id_opcion
        ).first()
        
        if not opcion:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Opción no encontrada"
            )
        
        # Verificar si la respuesta es correcta
        es_correcta = opcion.es_correcta
        
        # Crear registro de progreso
        progreso = Progreso(
            id_usuario=usuario_id,
            id_pregunta=id_pregunta,
            correcta=es_correcta
        )
        
        db.add(progreso)
        
        # Si es correcta, sumar XP al usuario
        if es_correcta:
            usuario = db.query(Usuario).filter(
                Usuario.id_usuario == usuario_id
            ).first()
            
            if usuario:
                xp_ganado = 10  # XP base por pregunta correcta
                usuario.puntaje += xp_ganado
                db.commit()
                
                return {
                    "es_correcta": True,
                    "xp_ganado": xp_ganado,
                    "nuevo_puntaje": usuario.puntaje,
                    "mensaje": "¡Correcto! +10 XP"
                }
        
        db.commit()
        
        return {
            "es_correcta": False,
            "xp_ganado": 0,
            "mensaje": "Respuesta incorrecta. Intenta de nuevo."
        }
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error: {str(e)}"
        )


@router.get("/usuario/{usuario_id}/estadisticas")
async def obtener_estadisticas(
    usuario_id: int,
    db: Session = Depends(get_db)
):
    """
    Obtiene estadísticas del usuario
    
    Response:
    {
        "puntaje_total": 150,
        "nivel": 3,
        "respuestas_correctas": 45,
        "respuestas_incorrectas": 5,
        "porcentaje_acierto": 90,
        "racha_dias": 7
    }
    """
    try:
        usuario = db.query(Usuario).filter(
            Usuario.id_usuario == usuario_id
        ).first()
        
        if not usuario:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado"
            )
        
        # Obtener progreso del usuario
        progresos = db.query(Progreso).filter(
            Progreso.id_usuario == usuario_id
        ).all()
        
        correctas = sum(1 for p in progresos if p.correcta)
        incorrectas = sum(1 for p in progresos if not p.correcta)
        
        total = len(progresos)
        porcentaje = (correctas / total * 100) if total > 0 else 0
        
        # Calcular nivel (cada 100 XP = 1 nivel)
        nivel = (usuario.puntaje // 100) + 1
        
        return {
            "puntaje_total": usuario.puntaje,
            "nivel": nivel,
            "respuestas_correctas": correctas,
            "respuestas_incorrectas": incorrectas,
            "porcentaje_acierto": round(porcentaje, 2),
            "total_respuestas": total,
            "racha_dias": 0  # Se puede calcular desde fecha_registro
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error: {str(e)}"
        )


@router.get("/usuario/{usuario_id}/progreso/{id_materia}")
async def obtener_progreso_materia(
    usuario_id: int,
    id_materia: int,
    db: Session = Depends(get_db)
):
    """
    Obtiene el progreso del usuario en una materia específica
    
    Response:
    {
        "materia": "Matemáticas",
        "preguntas_respondidas": 10,
        "preguntas_correctas": 8,
        "porcentaje": 80,
        "nivel_actual": 1,
        "proximo_nivel": 2
    }
    """
    try:
        # Obtener preguntas de la materia
        preguntas = db.query(Pregunta).filter(
            Pregunta.id_materia == id_materia
        ).all()
        
        # Obtener respuestas del usuario en esa materia
        respuestas = db.query(Progreso).filter(
            Progreso.id_usuario == usuario_id,
            Progreso.id_pregunta.in_([p.id_pregunta for p in preguntas])
        ).all()
        
        correctas = sum(1 for r in respuestas if r.correcta)
        total = len(respuestas)
        porcentaje = (correctas / total * 100) if total > 0 else 0
        
        materia = db.query(Materia).filter(
            Materia.id_materia == id_materia
        ).first()
        
        return {
            "materia": materia.nombre if materia else "Desconocida",
            "preguntas_respondidas": total,
            "preguntas_correctas": correctas,
            "porcentaje": round(porcentaje, 2),
            "nivel_actual": 1,
            "proximo_nivel": 2
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error: {str(e)}"
        )
