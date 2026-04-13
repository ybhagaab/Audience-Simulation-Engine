import psycopg2, os

def load_env(path):
    if os.path.exists(path):
        with open(path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    k, v = line.split('=', 1)
                    os.environ[k.strip()] = v.strip()

for p in [os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"),
          os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".kiro", "settings", ".env"),
          os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), ".kiro", "settings", ".env")]:
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

print("=== OTT Content Categories (watched by Fatafat users) ===")
cur.execute("""
    WITH ott_videos AS (
        SELECT c.videoid,
            COUNT(DISTINCT c.uuid) as users,
            SUM(CAST(c.playtime AS FLOAT))/60000 as minutes
        FROM content_stream_end_table_v2 c
        WHERE DATE(c.start_date) BETWEEN '2026-03-30' AND '2026-04-05'
          AND CAST(c.playtime AS FLOAT) >= 3000
          AND c.uuid IN (
              SELECT DISTINCT uuid FROM fatafat.mxp_fatafat_player_engagement
              WHERE DATE(start_date) BETWEEN '2026-03-30' AND '2026-04-05'
                AND event = 'onlineStreamEnd' AND CAST(playtime AS FLOAT) >= 3000
                AND networkType IS NOT NULL AND internalNetworkStatus > 1
                AND pagetype = 'titlePage'
          )
        GROUP BY c.videoid
    )
    SELECT cms.content_category,
        COUNT(DISTINCT ov.videoid) as videos,
        SUM(ov.users) as user_views,
        ROUND(SUM(ov.minutes), 0) as total_min
    FROM ott_videos ov
    JOIN (SELECT DISTINCT video_id, content_category FROM daily_cms_data_table
          WHERE content_category IS NOT NULL AND content_category NOT IN ('[]', '')) cms
    ON ov.videoid = cms.video_id
    GROUP BY cms.content_category
    ORDER BY user_views DESC
    LIMIT 30
""")

print(f"{'Category':35s} {'Videos':>8s} {'User Views':>12s} {'Minutes':>12s}")
print('-' * 70)
for row in cur.fetchall():
    print(f"{str(row[0]):35s} {row[1]:>8,} {row[2]:>12,} {row[3]:>12,.0f}")

cur.close()
conn.close()
