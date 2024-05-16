from airflow import DAG
from datetime import datetime
from airflow.operators.python import PythonOperator,BranchPythonOperator
from airflow.operators.bash import BashOperator
from random import randint
import random
import os
from zipfile import ZipFile
from urllib.request import urlopen
from shutil import copyfileobj
from urllib.request import urlopen
from shutil import copyfileobj
from zipfile import ZipFile
import shutil
import sys

def copy_zip_file(source_path, destination_path):
    """
    This function copies a file from the source_path to the destination path as mentioned in args.
    We utilise this for placing the zip file in the correct directory once the task 1 zip file has been created.
    """
    try:
        shutil.copy(source_path, destination_path)
        print("Zip file copied successfully from", source_path, "to", destination_path)
    except IOError as e:
        print("Unable to copy file. %s" % e)
    except:
        print("Unexpected error:", sys.exc_info())

def _copyfileobj_patched(fsrc, fdst, length=16*1024*1024):
    """Patches shutil method to hugely improve copy speed"""
    while 1:
        buf = fsrc.read(length)
        if not buf:
            break
        fdst.write(buf)
shutil.copyfileobj = _copyfileobj_patched

def _select_files(**kwargs):
    """
    This is run after the first bash operator fetches the list of files from the link https://www.ncei.noaa.gov/data/local-climatological-data/access/1905/
    list_of_files.txt has all the filenames that need to be fetched
    Once we get the list of csv files, we randomly sample "num_links" of them
    Then we return the full url paths of the final randomly sampled files.

    Input: num_links, number of links to be downloaded
    Output: csv_urlpaths, Array of URL Paths of all CSVs to be downloaded
    """
    csv_urlpaths = []
    num_links = kwargs['no_req_links']
    csv_files=[]

    print("Working dir: ",os.getcwd())

    with open('/Users/nikhilanand/airflow/list_of_files.txt','r') as file:
        lines = file.readlines()
        flag=False # The txt file has some bad lines, so we set flag to False to make sure these are not fetched
        # Once the bad lines are completed, we set flag to True and the remaining files are fetched
        for line in lines:
            print("Line: ",line,flag)
            if(flag==True):
                csv_files.append(line) # Append to the list csv_files
            if line == "/data/local-climatological-data/access/\n": # All lines after this one contain the csv file names
                flag = True

    print("csv_files: ",csv_files)
    csv_files = random.sample(csv_files, num_links)
    
    for item in csv_files: # Entire URL of the csv file is constructed from the file name
        csv_urlpaths.append('https://www.ncei.noaa.gov/data/local-climatological-data/access/1905/'+item[:-1])

    return csv_urlpaths

def _fetch_zip(ti):
    """
    Now, we have a list of URL Paths returned through the xcom_pull
    We store this in variable 'csv_urlpaths'
    Then we fetch them one by one and write them to a compressed zip file

    Input: csv_urlpaths
    Output: None
    Action: ZIp file created with the required csvs
    """
    csv_urlpaths = ti.xcom_pull(task_ids=['select_files'])[0]
    path = '/Users/nikhilanand/airflow/data_saving/'
    zipObj = ZipFile(path+"archive.zip", 'w')
    print('hi')

    i=0
    print("CSV_URLPATHS: ",csv_urlpaths)
    for urlpath in csv_urlpaths:
        i+=1
        with urlopen(urlpath) as in_stream, open(path+"file"+str(i)+".csv", 'wb') as out_file:
            copyfileobj(in_stream, out_file)
            print('hi2')

        print("Writing...")
        zipObj.write(path+"file"+str(i)+".csv","file"+str(i)+".csv")
    print("Done writing")
    zipObj.close()
    print("Closed")

def _place_files(**kwargs):
    """
    Files are placed in the correct location as specified by the path
    
    Input: Required path for zip file to be accessed in task 2
    Output: None
    Action: Zip file has been transferred
    """
    try:
        # copy_zip_file is a function written above, that does the needful
        copy_zip_file("/Users/nikhilanand/airflow/data_saving/archive.zip", "/Users/nikhilanand/airflow/"+ kwargs["path"]+"saved_archive.zip")
        
    except Exception as e:
        print('Error: ' + str(e))

with DAG("task1_dag2", start_date = datetime(2021,1,1),
    schedule_interval="@daily", catchup=False) as dag: # scheduled at midnight of 2nd Jan 2021 (as soon as the next day starts)

    # We create multiple nodes to be completed in the DAG.
    # fetch_data: BashOperator for fetching list of CSV URLs from the given URL in a txt file
    # select_files: PythonOperator for fetching the required number of links and making a list of URLs
    # fetch_zip: PythonOperator for fetching/downloading all the links into a zip file
    # place_files: PythonOperator for placing the files in the correct location
    fetch_data = BashOperator(task_id="fetch_data",bash_command='curl -s https://www.ncei.noaa.gov/data/local-climatological-data/access/1905/ | grep -o \'href="[^"]*"\' | cut -d\'"\' -f2 > /${AIRFLOW_HOME}/list_of_files.txt')
    select_files = PythonOperator(task_id="select_files",python_callable=_select_files, op_kwargs={'no_req_links':3})
    fetch_zip = PythonOperator(task_id="fetch_zip",python_callable=_fetch_zip)
    place_files = PythonOperator(task_id="place_files",python_callable=_place_files,op_kwargs={'path':'location_to_save/'})

    fetch_data >> select_files >> fetch_zip >> place_files