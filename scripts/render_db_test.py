import os
import psycopg2
from urllib.parse import urlparse

db_url = os.environ.get("DATABASE_URL")
from urllib.parse import urlparse

result = urlparse(db_url)
conn = psycopg2.connect(
    dbname=result.path[1:],
    user=result.username,
    password=result.password,
    host=result.hostname,
    port=result.port or 5432,
    sslmode="require"
)

cur = conn.cursor()
cur.execute("SELECT NOW();")
print("現在時刻:", cur.fetchone()[0])
cur.close()
conn.close()
