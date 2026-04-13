"""
Check OTT content categories using already-exported data.
Uses the ott_overlap.csv (has top_ott_show per user) + CMS lookup.
"""
import psycopg2, os, csv, time

def load_env(path):
    if os.path.exists(path):
        with open(path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    k, v = line.split('=', 1)
                    os.environ[k.strip()] = v.strip()

DIR = os.path.dirname(os.path.abspath(__file__))
for p in [os.path.join(DIR, ".env"),
          os.path.join(os.path.dirname(DIR), ".kiro", "settings", ".env"),
          os.path.join(os.path.dirname(os.path.dirname(DIR)), ".kiro", "settings", ".env")]:
    if os.path.exists(p):
        load_env(p)
        break

conn = psycopg2.connect(
    host='vpce-0cfaee168d10434e7-a1iibn6p.vpce-svc-09b1fc38f11e9bfef.ap-south-1.vpce.amazonaws.com',
    port=5439, dbname='mxbi',
    user=os.environ['REDSHIFT_USERNAME'],
    password=os.environ['REDSHIFT_PASSWORD'],
    sslmode='require'
)
cur = conn.cursor()

# Simpler approach: just get content_category distribution from CMS
# for non-Fatafat content (OTT library)
print("=== ALL content_category values in CMS (non-Fatafat) ===")
cur.execute("""
    SELECT content_category, COUNT(DISTINCT video_id) as videos, COUNT(DISTINCT channel_ids) as shows
    FROM daily_cms_data_table
    WHERE content_category IS NOT NULL
      AND content_category NOT IN ('[]', '', 'Fatafat')
    GROUP BY content_category
    ORDER BY shows DESC
    LIMIT 30
""")
print(f"{'Category':40s} {'Videos':>8s} {'Shows':>8s}")
print('-' * 60)
for row in cur.fetchall():
    print(f"{str(row[0]):40s} {row[1]:>8,} {row[2]:>8,}")

# Now get per-user OTT content_category using a faster approach:
# Export user × content_category from OTT for our cohort
print("\n=== Exporting per-user OTT content_category ===")
DATA_DIR = os.path.join(os.path.dirname(DIR), 'data')
out_path = os.path.join(DATA_DIR, "ott_user_categories.csv")

t0 = time.time()
cur.execute("""
    WITH fatafat_users AS (
        SELECT DISTINCT uuid
        FROM fatafat.mxp_fatafat_player_engagement
        WHERE DATE(start_date) BETWEEN '2026-03-30' AND '2026-04-05'
          AND event = 'onlineStreamEnd' AND CAST(playtime AS FLOAT) >= 3000
          AND networkType IS NOT NULL AND internalNetworkStatus > 1
          AND pagetype = 'titlePage'
    ),
    ott_agg AS (
        SELECT c.uuid, c.videoid, SUM(CAST(c.playtime AS FLOAT))/60000 as minutes
        FROM content_stream_end_table_v2 c
        INNER JOIN fatafat_users f ON c.uuid = f.uuid
        WHERE DATE(c.start_date) BETWEEN '2026-03-30' AND '2026-04-05'
          AND CAST(c.playtime AS FLOAT) >= 3000
        GROUP BY c.uuid, c.videoid
    ),
    ott_with_cat AS (
        SELECT o.uuid, cms.content_category, SUM(o.minutes) as minutes
        FROM ott_agg o
        JOIN (SELECT DISTINCT video_id, content_category FROM daily_cms_data_table
              WHERE content_category IS NOT NULL AND content_category NOT IN ('[]','','Fatafat')) cms
        ON o.videoid = cms.video_id
        GROUP BY o.uuid, cms.content_category
    )
    SELECT uuid,
        MAX(CASE WHEN rn = 1 THEN content_category END) as top_category,
        MAX(CASE WHEN rn = 1 THEN minutes END) as top_cat_minutes,
        COUNT(DISTINCT content_category) as cat_count,
        SUM(minutes) as total_ott_min
    FROM (
        SELECT *, ROW_NUMBER() OVER (PARTITION BY uuid ORDER BY minutes DESC) as rn
        FROM ott_with_cat
    )
    GROUP BY uuid
""")

cols = [d[0] for d in cur.description]
row_count = 0
with open(out_path, 'w', newline='') as f:
    w = csv.writer(f)
    w.writerow(cols)
    while True:
        rows = cur.fetchmany(10000)
        if not rows: break
        w.writerows(rows)
        row_count += len(rows)
        if row_count % 100000 == 0:
            print(f"  {row_count:,} rows...")

print(f"Exported {row_count:,} users in {time.time()-t0:.0f}s → {out_path}")

cur.close()
conn.close()
