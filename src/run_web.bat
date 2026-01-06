echo Planungseinheit %3 Von %1 Bis %2

cd C:\Users\rwthadmin\Documents\StaffScheduling\database
python export_main.py

cd C:\Users\rwthadmin\Documents\StaffSchedulingWeb\
.\start-workflow-with-env.bat %1 %2 %3
pause
