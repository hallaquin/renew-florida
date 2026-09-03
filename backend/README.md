# Backend — Renew Florida (Aplicación de Crédito)

Flask + SQLite. Recibe el formulario de Aplicación de Crédito del sitio (`formulario.html`)
y expone un panel de administración server-rendered para revisarlas.

Independiente del formulario/backend de Renew Water: base de datos, uploads y admin propios.

## Desarrollo local

Desde la raíz del repo:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt

cp backend/.env.example backend/.env
# Completa SECRET_KEY, FERNET_KEY y CORS_ALLOWED_ORIGIN en backend/.env
# (los comandos para generarlas están comentados dentro del archivo)

export $(cat backend/.env | grep -v '^#' | xargs)   # o usa python-dotenv/tu editor

python -m backend.scripts.create_admin   # crea el usuario admin (pide usuario/password)

flask --app backend.app run --debug
```

- API pública: `POST http://localhost:5000/api/credit-applications`
- Panel admin: `http://localhost:5000/admin/login`

## Despliegue (Railway / Render, con disco persistente)

SQLite necesita un filesystem persistente — no funciona en el modelo serverless de Vercel.
Usa un servicio tipo Railway/Render con un volumen persistente montado en `backend/data/`
y `backend/uploads/`.

- **Root directory**: raíz del repo (para que `backend.app:app` se pueda importar).
- **Build command**: `pip install -r requirements.txt`
- **Start command**: `gunicorn -w 2 -b 0.0.0.0:$PORT backend.app:app` (ver `Procfile` en la raíz)
- **Variables de entorno**: las mismas de `backend/.env.example`, con
  `CORS_ALLOWED_ORIGIN` apuntando al dominio real del sitio (Vercel).
- Después del primer deploy, correr una sola vez `python -m backend.scripts.create_admin`
  (por SSH/consola del proveedor) para crear el usuario admin.
- Actualiza `assets/js/formulario-config.js` en el frontend con la URL pública del backend.

## Estructura de una Aplicación de Crédito

Ver el JSON de ejemplo en el plan / `backend/models.py`: los campos no sensibles viven en
`data_json`, el SSN (aplicante y co-aplicante) se cifra con Fernet en columnas aparte, y las
fotos de ID / firmas se guardan como archivos en `backend/uploads/`, nunca en la base de
datos ni servidos públicamente (solo descargables desde el panel admin autenticado).
