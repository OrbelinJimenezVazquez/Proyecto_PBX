# FreePBX Moderno

Interfaz web moderna para la administración de PBX basada en FreePBX.  
Conectada a la base de datos real de la empresa (`10.10.16.9`).

## Funciones implementadas
- ✅ Extensiones (con estado online/offline)
- ✅ Llamadas recientes
- ✅ Troncales SIP (datos cargados, vista funcional)

## Tecnologías
- Frontend: Angular 17 (standalone)
- Backend: Python + FastAPI
- Base de datos: MySQL (FreePBX real)

## Cómo ejecutar localmente

### Requisitos previos
- Node.js (v18+)
- Python 3.10+
- MySQL Workbench (opcional, para verificar conexión)

### Pasos

#### 1. Backend (FastAPI)

```bash
cd beyondpbx-backend  # o freepbx-moderno-backend
python -m venv venv
venv\Scripts\Activate.ps1
pip install fastapi uvicorn sqlalchemy pymysql python-dotenv


  # Ejecuta el servidor
  python -m uvicorn main:app --reload
```
* Asegúrate de tener el archivo .env con:
   ```
    DB_HOST=10.10.16.9
    DB_USER=lilibasto
    DB_PASSWORD=U*VGmhXJCvERw5#7Gm
   ```

#### 2. Frontend (Angular)
```bash
    cd freepbx-moderno-frontend
    npm install
    ng serve --proxy-config proxy.conf.json
```

