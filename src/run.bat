echo Planungseinheit %3 Von %1 Bis %2

cd C:\Users\rwthadmin\Documents\StaffScheduling\database
python export_main.py

cd C:\Users\rwthadmin\Documents\StaffScheduling\
uv run --env-file .env staff-scheduling delete %3 %1 %2
uv run --env-file .env staff-scheduling fetch %3 %1 %2
uv run --env-file .env staff-scheduling solve %3 %1 %2 --timeout 30
uv run --env-file .env staff-scheduling insert %3 %1 %2

pause
