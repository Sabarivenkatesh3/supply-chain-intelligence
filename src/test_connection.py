import snowflake.connector
from dotenv import load_dotenv
import os
load_dotenv()
conn = snowflake.connector.connect(
user=os.getenv("SNOWFLAKE_USER"),
password=os.getenv("SNOWFLAKE_PASSWORD"),
account="gsxalxt-hp10837",
warehouse="COMPUTE_WH",
database="SNOWFLAKE_SAMPLE_DATA",
schema="PUBLIC"
)
cursor = conn.cursor()
cursor.execute("SELECT CURRENT_VERSION()")
row = cursor.fetchone()
print("Snowflake connected successfully!")
print("Version:", row[0])
cursor.close()
conn.close()