"""
Phase 2.1: Export persona tags in batches.
Instead of pulling raw long-format tags (20M+ rows),
we aggregate in SQL to get per-user tag count + top tags.
This produces ~1.9M rows (one per user) instead of 20M+.
"""

import csv
import os
import sys
import time

try:
    import psycopg2
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "psycopg2-binary"])
    import psycopg2

# Load .env
def load_env(path=".env"):
    if os.path.exists(path):
        with open(path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, val = line.split('=', 1)
                    os.environ[key.strip()] = val.strip()

script_dir = os.path.dirname(os.path.abspath(__file__))
workspace_root = os.path.dirname(script_dir)
for p in [os.path.join(script_dir, ".env"),
          os.path.join(workspace_root, ".kiro", "settings", ".env"),
          os.path.join(workspace_root, ".env")]:
    if os.path.exists(p):
        print(f"Loading credentials from: {p}")
        load_env(p)
        break

HOST = "vpce-0cfaee168d10434e7-a1iibn6p.vpce-svc-09b1fc38f11e9bfef.ap-south-1.vpce.amazonaws.com"
PORT = 5439
DATABASE = "mxbi"
USERNAME = os.environ.get("REDSHIFT_USERNAME")
PASSWORD = os.environ.get("REDSHIFT_PASSWORD")

if not USERNAME or not PASSWORD:
    print("ERROR: Set REDSHIFT_USERNAME and REDSHIFT_PASSWORD in .env")
    sys.exit(1)

print(f"Connecting to Redshift as {USERNAME}...")
conn = psycopg2.connect(host=HOST, port=PORT, dbname=DATABASE,
                         user=USERNAME, password=PASSWORD, sslmode='require')
conn.autocommit = True
print("Connected.\n")

# Strategy: Instead of exporting raw long-format tags (125M+ rows),
# aggregate in SQL into per-user interest category flags + tag count.
# This produces ~1.9M rows (one per user).
#
# Interest categories derived from the top persona tags:
#   Fashion/Beauty, Electronics/Tech, Health/Fitness, Home/Kitchen,
#   Travel, Parents/Baby, Automotive, Affluent

QUERY = """
WITH streamers AS (
    SELECT DISTINCT uuid
    FROM fatafat.mxp_fatafat_player_engagement
    WHERE DATE(start_date) BETWEEN '2026-03-30' AND '2026-04-05'
      AND event = 'onlineStreamEnd'
      AND CAST(playtime AS FLOAT) >= 3000
      AND networkType IS NOT NULL
      AND internalNetworkStatus > 1
      AND pagetype = 'titlePage'
),
user_tags AS (
    SELECT s.uuid, p.persona_name
    FROM streamers s
    JOIN mxp_persona_details_table_v3 p ON s.uuid = p.uuid
    WHERE p.source = 'ml'
)
SELECT
    uuid,
    COUNT(DISTINCT persona_name) as tag_count,
    MAX(CASE WHEN persona_name ILIKE '%fashion%' OR persona_name ILIKE '%beauty%'
             OR persona_name ILIKE '%grooming%' OR persona_name ILIKE '%ethnic wear%'
             OR persona_name ILIKE '%jewelry%' OR persona_name ILIKE '%clothing%'
        THEN 1 ELSE 0 END) as has_fashion_beauty,
    MAX(CASE WHEN persona_name ILIKE '%electronics%' OR persona_name ILIKE '%computer%'
             OR persona_name ILIKE '%smartphone%' OR persona_name ILIKE '%mobile%'
             OR persona_name ILIKE '%tablet%' OR persona_name ILIKE '%tech%'
        THEN 1 ELSE 0 END) as has_electronics_tech,
    MAX(CASE WHEN persona_name ILIKE '%health%' OR persona_name ILIKE '%fitness%'
             OR persona_name ILIKE '%nutrition%'
        THEN 1 ELSE 0 END) as has_health_fitness,
    MAX(CASE WHEN persona_name ILIKE '%home%' OR persona_name ILIKE '%kitchen%'
             OR persona_name ILIKE '%appliance%'
        THEN 1 ELSE 0 END) as has_home_kitchen,
    MAX(CASE WHEN persona_name ILIKE '%travel%'
        THEN 1 ELSE 0 END) as has_travel,
    MAX(CASE WHEN persona_name ILIKE '%parent%' OR persona_name ILIKE '%baby%'
        THEN 1 ELSE 0 END) as has_parents_baby,
    MAX(CASE WHEN persona_name ILIKE '%automotive%'
        THEN 1 ELSE 0 END) as has_automotive,
    MAX(CASE WHEN persona_name ILIKE '%affluent%' OR persona_name ILIKE '%premium%'
        THEN 1 ELSE 0 END) as has_affluent_premium
FROM user_tags
GROUP BY uuid
"""

filepath = os.path.join(script_dir, "q25_persona_tags.csv")
print(f"Running persona tags aggregation query...", flush=True)
t0 = time.time()

cur = conn.cursor()
cur.execute(QUERY)

columns = [desc[0] for desc in cur.description]
row_count = 0
with open(filepath, 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(columns)
    while True:
        rows = cur.fetchmany(10000)
        if not rows:
            break
        writer.writerows(rows)
        row_count += len(rows)
        if row_count % 100000 == 0:
            print(f"  {row_count:,} rows exported...", flush=True)

cur.close()
conn.close()
elapsed = time.time() - t0
print(f"\n✅ {row_count:,} rows in {elapsed:.1f}s → {filepath}")
