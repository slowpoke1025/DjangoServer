cd dreamDB-master
nohup source env/bin/activate
nohup python3 manage.py runserver 140.117.71.159:8000 >djo.log2>&1 &
