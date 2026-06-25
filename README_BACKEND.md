# 🚀 Lynko Backend - README

> Plataforma gamificada de educación para reducir el aburrimiento en el estudio y aumentar la motivación del aprendizaje.

**Backend**: FastAPI + PostgreSQL | **Equipo**: 4 desarrolladores | **Presupuesto**: $0 (Herramientas libres)

---

## 📁 Estructura del Proyecto

```
App/
├── Config/
│   ├── __init__.py
│   ├── database.py          # Conexión SQLAlchemy + SessionLocal
│   └── settings.py          # Variables de configuración (BD, JWT, etc.)
│
├── Controllers/
│   ├── __init__.py
│   ├── auth_controller.py   # Lógica: hash, JWT, registro, login
│   └── content_controller.py  # Lógica: materias, preguntas, progreso
│
├── Models/
│   ├── __init__.py
│   ├── user.py              # Usuario (auth, XP, nivel)
│   ├── subject.py           # Materia (Matemáticas, Español, etc.)
│   ├── question.py          # Pregunta (con opciones)
│   ├── progress.py          # Progreso usuario (respuestas)
│   └── reward.py            # Recompensas/Logros
│
├── Routes/
│   ├── __init__.py
│   ├── auth.py              # POST /api/auth/register, /login, /me
│   ├── content.py           # GET /api/content/subjects, /preguntas
│   └── admin.py             # POST/GET /api/admin/* (gestión)
│
├── Schemas/
│   ├── __init__.py
│   ├── user_schema.py       # UserRegister, UserLogin, UserResponse
│   ├── subject_schema.py    # SubjectResponse, SubjectCreate
│   └── question_schema.py   # QuestionResponse, etc.
│
├── Utils/
│   ├── __init__.py
│   ├── jwt_handler.py       # Funciones JWT (crear token, validar)
│   ├── password_handler.py  # Hash y verificación bcrypt
│   └── error_handler.py     # Respuestas de error estandarizadas
│
├── Middleware/
│   ├── __init__.py
│   └── auth_middleware.py   # Validación JWT en rutas protegidas
│
├── Main.py                  # Punto de entrada FastAPI
├── requirements.txt         # Dependencias Python
└── .gitignore              # Archivos a ignorar en Git
```

---

## 🔧 Setup Inicial (5 min)

### 1️⃣ **Clonar repositorio y crear estructura**

```bash
git clone https://github.com/RodriSibada/Lynko.git
cd Lynko/App
```

### 2️⃣ **Crear entorno virtual**

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### 3️⃣ **Instalar dependencias**

```bash
pip install -r requirements.txt
```

**⚠️ Importante**: Si error con bcrypt:
```bash
pip install bcrypt==4.0.1
```

### 4️⃣ **Crear base de datos en PostgreSQL**

```bash
# En pgAdmin o psql:
CREATE DATABASE lynko_nueva;

-- Ejecutar en lynko_nueva:
CREATE SCHEMA IF NOT EXISTS public;

CREATE TABLE public.users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    xp INTEGER DEFAULT 0,
    level INTEGER DEFAULT 1,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_users_email ON public.users(email);
```

### 5️⃣ **Configurar variables de entorno**

Crear `.env` en la raíz de `App/`:

```env
# Base de Datos
DATABASE_URL=postgresql://postgres:password@localhost:5432/lynko_nueva

# JWT
SECRET_KEY=tu-clave-secreta-super-segura-cambiar-en-produccion
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# FastAPI
DEBUG=True
```

### 6️⃣ **Ejecutar servidor**

```bash
# Desde App/
python Main.py

# O con uvicorn directo:
uvicorn Main:app --reload --host 0.0.0.0 --port 8000
```

✅ Verifica en: http://localhost:8000/health → `{"status": "ok"}`

---

## 📚 Estructura por Capas

### **Config/** - Configuración Central

```python
# database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import os

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

---

### **Models/** - Definición de Tablas

```python
# Models/user.py
from Config.database import Base
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func

class User(Base):
    __tablename__ = "users"
    __table_args__ = {"schema": "public"}

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    xp = Column(Integer, default=0)
    level = Column(Integer, default=1)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
```

---

### **Schemas/** - Validación Pydantic

```python
# Schemas/user_schema.py
from pydantic import BaseModel, EmailStr
from datetime import datetime

class UserRegister(BaseModel):
    name: str
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    xp: int
    level: int

    class Config:
        from_attributes = True
```

---

### **Controllers/** - Lógica de Negocio

```python
# Controllers/auth_controller.py
from passlib.context import CryptContext
from jose import jwt
from datetime import datetime, timedelta
from Config.models.user import User
from sqlalchemy.orm import Session

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = "tu-clave-secreta"
ALGORITHM = "HS256"

class AuthController:
    @staticmethod
    def hash_password(password: str) -> str:
        return pwd_context.hash(password)
    
    @staticmethod
    def verify_password(plain: str, hashed: str) -> bool:
        return pwd_context.verify(plain, hashed)
    
    @staticmethod
    def create_access_token(data: dict) -> str:
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=30)
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    @staticmethod
    def register(name: str, email: str, password: str, db: Session):
        # Verificar si email existe
        user = db.query(User).filter(User.email == email).first()
        if user:
            raise Exception("Email ya registrado")
        
        # Crear usuario
        hashed = AuthController.hash_password(password)
        new_user = User(name=name, email=email, password=hashed)
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        # Generar token
        token = AuthController.create_access_token({"sub": email})
        return {"access_token": token, "user": new_user}
```

---

### **Routes/** - Endpoints HTTP

```python
# Routes/auth.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from Config.database import get_db
from Controllers.auth_controller import AuthController
from Schemas.user_schema import UserRegister

router = APIRouter(prefix="/api/auth", tags=["auth"])

@router.post("/register")
def register(data: UserRegister, db: Session = Depends(get_db)):
    """
    Registrar nuevo usuario
    
    Request:
    {
        "name": "Carlos",
        "email": "carlos@example.com",
        "password": "seg123456"
    }
    
    Response:
    {
        "access_token": "eyJhbGc...",
        "token_type": "bearer",
        "user": {
            "id": 1,
            "name": "Carlos",
            "email": "carlos@example.com",
            "xp": 0,
            "level": 1
        }
    }
    """
    return AuthController.register(data.name, data.email, data.password, db)

@router.post("/login")
def login(data: UserLogin, db: Session = Depends(get_db)):
    """
    Iniciar sesión
    """
    user = db.query(User).filter(User.email == data.email).first()
    if not user or not AuthController.verify_password(data.password, user.password):
        raise HTTPException(status_code=401, detail="Credenciales inválidas")
    
    token = AuthController.create_access_token({"sub": user.email})
    return {"access_token": token, "token_type": "bearer", "user": user}

@router.get("/me")
def get_current_user(token: str, db: Session = Depends(get_db)):
    """
    Obtener usuario actual (autenticado)
    """
    # Decodificar token y buscar usuario
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    email = payload.get("sub")
    user = db.query(User).filter(User.email == email).first()
    return user
```

---

## 📊 Endpoints Disponibles

### **Autenticación (`/api/auth`)**

| Método | Ruta | Descripción |
|--------|------|-------------|
| `POST` | `/api/auth/register` | Registrar nuevo usuario |
| `POST` | `/api/auth/login` | Iniciar sesión |
| `GET` | `/api/auth/me?token=...` | Obtener usuario actual |

### **Contenido (`/api/content`)**

| Método | Ruta | Descripción |
|--------|------|-------------|
| `GET` | `/api/content/subjects` | Listar todas las materias |
| `GET` | `/api/content/subjects/{id}` | Detalle de una materia |
| `GET` | `/api/content/subjects/{id}/questions` | Preguntas de una materia |
| `POST` | `/api/content/answer` | Guardar respuesta de usuario |

### **Admin (`/api/admin`)**

| Método | Ruta | Descripción |
|--------|------|-------------|
| `GET` | `/api/admin/metrics` | Métricas generales |
| `POST` | `/api/admin/questions` | Crear pregunta |
| `DELETE` | `/api/admin/questions/{id}` | Eliminar pregunta |
| `DELETE` | `/api/admin/students/{id}` | Dar de baja estudiante |

---

## 🧪 Testing con Swagger

```
http://localhost:8000/docs
```

Prueba endpoints directamente en el navegador:

1. POST `/api/auth/register` → Registra un usuario
2. POST `/api/auth/login` → Obtén token
3. GET `/api/auth/me?token=...` → Consulta usuario actual

---

## ⚙️ Archivos Importantes

### **requirements.txt**

```
fastapi==0.104.1
uvicorn[standard]==0.24.0
sqlalchemy==2.0.23
psycopg2-binary==2.9.9
pydantic==2.5.0
pydantic[email]==2.5.0
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
bcrypt==4.0.1
python-multipart==0.0.6
```

### **.gitignore**

```
venv/
__pycache__/
*.pyc
.env
.DS_Store
*.sqlite3
.vscode/
.idea/
```

---

## 🔒 Autenticación JWT

1. **Register** → Usuario se crea con contraseña hasheada
2. **Login** → Se valida email + contraseña, se genera JWT
3. **Token** → Se guarda en localStorage (frontend)
4. **Requests protegidos** → Se valida token en header `Authorization: Bearer <token>`

---

## 🚨 Troubleshooting

| Error | Solución |
|-------|----------|
| `ModuleNotFoundError: No module named 'fastapi'` | `pip install -r requirements.txt` |
| `connection refused` | PostgreSQL no está corriendo |
| `FATAL: database "lynko_nueva" does not exist` | Crear BD en pgAdmin primero |
| `AttributeError: module 'bcrypt' has no attribute '__about__'` | `pip install bcrypt==4.0.1` |
| `ImportError: cannot import name 'User' from 'Config.models'` | Verificar que `Models/__init__.py` exporte los modelos |
| `CORS error` | FastAPI tiene CORS habilitado por defecto en dev |

---

## 📋 Checklist de Setup

- [ ] PostgreSQL instalado y corriendo
- [ ] Base de datos `lynko_nueva` creada
- [ ] Python 3.9+ instalado
- [ ] Venv activado
- [ ] `pip install -r requirements.txt` completado
- [ ] `.env` configurado con `DATABASE_URL`
- [ ] `python Main.py` inicia sin errores
- [ ] `http://localhost:8000/health` retorna `{"status": "ok"}`
- [ ] Swagger disponible en `http://localhost:8000/docs`
- [ ] Puedo registrar usuario en `/api/auth/register`

---

## 👥 Flujo del Equipo

**Rodrigo** (Líder):
- Coordina estructura de carpetas y estándares
- Revisa PRs en Controllers y Models

**Simón**:
- Desarrolla Controllers (lógica de negocio)
- Crea unit tests

**María**:
- Desarrolla Routes (endpoints HTTP)
- Documenta Swagger/OpenAPI

**Montserrat**:
- Crea Models y Schemas
- Gestiona migraciones BD

---

## 🔗 Links Útiles

- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [SQLAlchemy ORM](https://docs.sqlalchemy.org/)
- [PyJWT](https://pyjwt.readthedocs.io/)
- [Passlib + Bcrypt](https://passlib.readthedocs.io/)

---

## 📄 Licencia

MIT - Proyecto educativo | 2025
