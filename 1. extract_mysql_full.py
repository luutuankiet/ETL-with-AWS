# this script is a base for extracting data from a mysql db and (temporary load) it to an s3 bucket, in csv format. 
# first off, import the following modules :  

import configparser # to parse sensitive auth data, stored in pipeline.conf file in the root folder. 
import pymysql # to enable python to work w/ mysql
import csv # formatting convention for extracted data
import boto3 # aws s3 client tool


# setup config for mysql connection
parser = configparser.ConfigParser()
parser.read("pipeline.conf")
hostname = parser.get("mysql_config", "hostname")
port = parser.get("mysql_config", "port")
username = parser.get("mysql_config", "username")
password = parser.get("mysql_config", "password")
dbname = parser.get("mysql_config", "database")





# ====
conn = pymysql.connect(host=hostname, user=username, password=password, db=dbname, port=int(port))

if conn is None:
    print("Error connecting to the MySQL database.")
else:
    print("Successful connection!")
    
# path : full extraction

m_query = "SELECT * FROM Orders;"
local_filename = "order_extract.csv"

m_cursor = conn.cursor()
m_cursor.execute(m_query)
results = m_cursor.fetchall()

with open(local_filename, 'w') as fp:
    csv_w = csv.writer(fp, delimiter='|')
    csv_w.writerows(results)
    
fp.close()
m_cursor.close()
conn.close()
print("Operation completed.")

# setup config for s3 bucket
parser = configparser.ConfigParser()
parser.read("pipeline.conf")
access_key = parser.get("aws_boto_credentials",
"access_key")
secret_key = parser.get("aws_boto_credentials",
"secret_key")
bucket_name = parser.get("aws_boto_credentials",
"bucket_name")

s3 = boto3.client('s3', aws_access_key_id=access_key, aws_secret_access_key=secret_key)

s3_file = local_filename

s3.upload_file(local_filename, bucket_name, s3_file)

print("Extracted data is now available in s3.")