@echo off
echo Exporting subjects table to CSV...
docker exec student-tracker-db psql -U studentadmin -d student_tracker -c "COPY (SELECT * FROM subjects LIMIT 1000) TO STDOUT WITH CSV HEADER" > subjects_export.csv
echo Done! File saved as: subjects_export.csv
echo Open with Excel or any text editor
pause
