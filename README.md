# BigDataLabProject

## 1. Preprocessing data

The first step is to preprocess the data. You can fetch the data files and preprocess them by following these instructions:

- Clone the repository to a directory named "BigDataLabProject".

```
export AIRFLOW_HOME=~/BigDataLabProject
source ~/airflow_venv/bin/activate
sudo kill <PID>
airflow db init

airflow scheduler \
--pid ${AIRFLOW_HOME}/logs/airflow-scheduler.pid \
--stdout ${AIRFLOW_HOME}/logs/airflow-scheduler.out \
--stderr ${AIRFLOW_HOME}/logs/airflow-scheduler.out \
-l ${AIRFLOW_HOME}/logs/airflow-scheduler.log \
 -D
```

- Then open a new terminal and run the following:

```
export AIRFLOW_HOME=~/airflow 
source ~/airflow_venv/bin/activate 
airflow users create -e <EMAILID> -f <FIRSTNAME> -l <LASTNAME> -p <PASSWORD> -u <USERNAME> -r Admin
airflow webserver -p 8080
```

- Now in the webserver, find the dag named "keypoints_dag". Run this dag and you will find the required files in the data/ directory.
