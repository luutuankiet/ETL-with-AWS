# ETL pipeline - clouds version

## Objective

* A pet project written in Python to create an ETL data pipeline using AWS S3 & Redshift from a dummy database as source.
* Acknowledgement : This script is referenced from [Data Pipelines Pocket Reference: Moving and Processing Data for Analytics](https://www.amazon.com/Data-Pipelines-Pocket-Reference-Processing/dp/1492087831).

## Components

![Components](https://i.imgur.com/mgHHQPt.png)

<!-- explain the architecture -->
* **The source database** is a MySQL instance hosted on Amazon RDS.
* **Data Extraction** done in Python using the following modules; the extracted data is formatted to csv and dumped into an S3 bucket.
  * pymysql - MySQL client
  * boto3 - S3 client
* **Data Load** done in Python using the following modules, after which loads data into AWS Redshift as datawarehouse.
  * boto3 - S3 client
  * psycopg2 - Redshift client
* **Data tranformation** done in the same Python Load script which is a code snippet to de-duplicate the loaded data.

<!-- explain in details -->
### Data ingestion

#### 1. Extact from source db

* Create a new file, *pipeline.conf* so that all credentials are stored outside of the script. This can later be parsed by python's *configparser* module.
  * Credentials for this extract script includes MySQL, S3 bucket & an IAM user assigned to the S3 bucket.
* Create a RDS instance in AWS using MySQL engine
* Create a dummy dataset, *Orders* table created in MySQL.
  * From a local MySQL client ([MySQL workbench](https://www.mysql.com/products/workbench/)), connect to the RDS instance & execute the CREATE TABLE command
* Create an S3 bucket in AWS console to dump data to be extracted.
  * Create an IAM User with programmatic access to the bucket to be used by *boto3* in the script.
* Execute the script `1. extract_mysql_full.py` with the configurations set up above; this script uses a full extraction method which extracts and dumps all data with each execution.

#### 2. Load to datawarehouse

* Similar to the extraction script, credentials are stored separately in *pipeline.config* file for Redshift, S3 and IAM Role. Note that this step only requires a read-only action therefore a Readonly Role will suffice; in contrast with Extraction step, a User with write access is required to execute commands to S3.
* Create a Database in Redshift with the same columns as the source database's.
* Utilize Redshift's native load command for data between S3 and Redshift :
  * COPY syntax - from [AWS doc](https://docs.aws.amazon.com/redshift/latest/dg/r_COPY.html)

    ```code
    COPY [table-name] 
    FROM [data_source] [authorization]
    ```

### Transform

* This step takes into account data duplication scenarios in a production environment :
  * An  incremental  data  ingestion  mistakenly  overlaps  a  previous  ingestion  time  window  and  picks  up  some  records that were already ingested in a previous run.
  * Duplicate  records  were  inadvertently created  in  a  source system.
  * Data  that  was  backfilled  overlapped  with  subsequent  data loaded into the table during ingestion.
* In such case, non-contextual transformation can be applied at either during or end of the ingestion. This script uses the latter option.
* The following SQL command is executed after loading data to Redshift :

```python
sql_deduplicate = """
    CREATE TABLE Distinct_orders as
    SELECT distinct OrderId, OrderStatus, LastUpdated
    from Orders;
    
    TRUNCATE TABLE Orders;
    
    INSERT INTO Orders
    SELECT * FROM Distinct_orders;
    
    DROP TABLE Distinct_orders;
    """
```