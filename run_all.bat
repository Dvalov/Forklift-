@echo off
echo Starting all services...

:: 1. Frontend (Vite)
start "Frontend Vite" cmd /k "cd frontend && npm run dev"

:: 2. Converter (Port 8002)
start "Converter 8002" cmd /k "cd Converter && ..\.venv\Scripts\activate && python manage.py runserver 8002"

:: 3. Warehouse (Port 8001)
start "Warehouse 8001" cmd /k "cd Warehouse && ..\.venv\Scripts\activate && python manage.py runserver 8001"

:: 4. Main Dashboard (Port 8000)
start "Main Dashboard 8000" cmd /k "cd forklift_dashboard && ..\.venv\Scripts\activate && python manage.py runserver 8000"

echo All services started!
pause