# CV Generator (Angular + FastAPI)

Aplicación para generar CVs minimalistas en **PDF** o **DOCX** a partir de datos básicos.

## Requisitos

- Node.js + npm
- Python 3.11+
- (Opcional) MongoDB para registrar el **log de usos** (best-effort)

## Backend (FastAPI)

1. Instalar dependencias:
   - `cd backend`
   - `pip install -r requirements.txt`
2. Ejecutar:
   - `python -m uvicorn cvgen.main:app --app-dir src --port 8000 --reload`

Variables de entorno (opcional):
- `MONGODB_URL` (default: `mongodb://localhost:27017`)
- `MONGODB_DB` (default: `cv_generator`)

## Frontend (Angular)

1. Ejecutar:
   - `cd frontend`
   - `npm start`
2. Abrir:
   - `http://localhost:4200`

## Uso

1. Completa el formulario.
2. Elige `PDF` o `DOCX`.
3. Selecciona el **color de la letra**.
4. Genera y descarga.

Si **no** hay MongoDB levantado, el CV igual se generará; solo fallará el registro del uso (best-effort).

