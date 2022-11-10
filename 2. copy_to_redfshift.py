import configparser # to parse from pipeline.conf file
import boto3 # for s3 client
import psycopg2 # Redshift client

# parse config info
parser = configparser.ConfigParser()
parser.read("pipeline.conf")
dbname = parser.get("aws_creds", "database")
user = parser.get("aws_creds","username")
password = parser.get("aws_creds","password")
host = parser.get("aws_creds","host")
port = parser.get("aws_creds","port")


# init connection to redshift

rs_conn = psycopg2.connect("dbname=" + dbname + " user=" + user + " password=" + password + " host=" + host + " port=" + port)

# setup config for s3 bucket
parser = configparser.ConfigParser()
parser.read("pipeline.conf")
account_id = parser.get("aws_boto_credentials", "account_id")
iam_role = parser.get("aws_creds", "iam_role")
bucket_name = parser.get("aws_boto_credentials", "bucket_name")

# init s3 connection & run COPY command

## set variables

file_path = ("s3://" + bucket_name + "/order_extract.csv")
role_string = ("arn:aws:iam::" +account_id + ":role/" + iam_role)

sql = "COPY public.Orders"
sql = sql + " from %s "
sql = sql + " iam_role %s;"

## create the cursor object to execute 

cur = rs_conn.cursor()
cur.execute(sql,(file_path,role_string))

# TRANSFORM
# noncontextual transform : deduplicate data
sql_deduplicate = """
    CREATE TABLE Distinct_orders as
    SELECT distinct OrderId, OrderStatus, LastUpdated
    from Orders;
    
    TRUNCATE TABLE Orders;
    
    INSERT INTO Orders
    SELECT * FROM Distinct_orders;
    
    DROP TABLE Distinct_orders;
    """
cur.execute(sql_deduplicate,(file_path,role_string))

#close cursor and commit 
cur.close()
rs_conn.commit()

# close connection
rs_conn.close()
print("copy job done.")





    
    