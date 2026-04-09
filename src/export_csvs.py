"""
Phase 2 CSV Export — Connects to Redshift and exports all 7 query results as CSVs.
Run this script first, then run phase2_clustering.py on the exported CSVs.

Usage:
  1. Create a .env file in the same directory with:
       REDSHIFT_USERNAME=your_username
       REDSHIFT_PASSWORD=your_password
  2. python3 export_csvs.py
"""

import csv
import os
import sys
import time

try:
    import psycopg2
except ImportError:
    print("Installing psycopg2-binary...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "psycopg2-binary"])
    import psycopg2

# Load .env file
def load_env(path=".env"):
    if os.path.exists(path):
        with open(path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, val = line.split('=', 1)
                    os.environ[key.strip()] = val.strip()

# Check multiple .env locations
script_dir = os.path.dirname(os.path.abspath(__file__))
workspace_root = os.path.dirname(script_dir)
env_paths = [
    os.path.join(script_dir, ".env"),
    os.path.join(workspace_root, ".kiro", "settings", ".env"),
    os.path.join(workspace_root, ".env"),
]
for p in env_paths:
    if os.path.exists(p):
        print(f"Loading credentials from: {p}")
        load_env(p)
        break

# Connection config
HOST = "vpce-0cfaee168d10434e7-a1iibn6p.vpce-svc-09b1fc38f11e9bfef.ap-south-1.vpce.amazonaws.com"
PORT = 5439
DATABASE = "mxbi"
USERNAME = os.environ.get("REDSHIFT_USERNAME")
PASSWORD = os.environ.get("REDSHIFT_PASSWORD")

if not USERNAME or not PASSWORD:
    print("ERROR: REDSHIFT_USERNAME and REDSHIFT_PASSWORD must be set in .env file")
    sys.exit(1)

print(f"\nConnecting to {HOST}:{PORT}/{DATABASE} as {USERNAME}...")
conn = psycopg2.connect(
    host=HOST, port=PORT, dbname=DATABASE,
    user=USERNAME, password=PASSWORD,
    sslmode='require'
)
conn.autocommit = True
print("Connected.\n")

# Base filters (reused across queries)
BASE = """
    event = 'onlineStreamEnd'
    AND CAST(playtime AS FLOAT) >= 3000
    AND networkType IS NOT NULL
    AND internalNetworkStatus > 1
    AND pagetype = 'titlePage'
"""
DATE_RANGE = "DATE(start_date) BETWEEN '2026-03-30' AND '2026-04-05'"

QUERIES = {
    "q21_engagement.csv": f"""
        SELECT uuid,
            COUNT(*) AS total_streams,
            ROUND(SUM(CAST(playtime AS FLOAT)) / 60000, 2) AS total_minutes,
            COUNT(DISTINCT videoid) AS unique_episodes,
            COUNT(DISTINCT DATE(start_date)) AS active_days,
            COUNT(DISTINCT sid) AS total_sessions
        FROM fatafat.mxp_fatafat_player_engagement
        WHERE {DATE_RANGE} AND {BASE}
        GROUP BY uuid
    """,

    "q22a_user_video.csv": f"""
        SELECT uuid, videoid,
            COUNT(*) AS streams,
            ROUND(SUM(CAST(playtime AS FLOAT)) / 60000, 2) AS minutes
        FROM fatafat.mxp_fatafat_player_engagement
        WHERE {DATE_RANGE} AND {BASE}
        GROUP BY uuid, videoid
    """,

    "q22b_cms_lookup.csv": """
        SELECT DISTINCT video_id, tv_show_name, channel_ids,
            genre_name, secondary_genre_name, language_name,
            content_category, episode_number
        FROM daily_cms_data_table
        WHERE is_fatafat_micro_show = '1'
          AND tv_show_name NOT IN ('[]', '[unknown]')
    """,

    "q23_session_episodes.csv": f"""
        SELECT uuid, sid,
            COUNT(DISTINCT videoid) AS episodes_in_session
        FROM fatafat.mxp_fatafat_player_engagement
        WHERE {DATE_RANGE} AND {BASE}
        GROUP BY uuid, sid
    """,

    "q24a_demographics.csv": f"""
        WITH streamers AS (
            SELECT DISTINCT uuid
            FROM fatafat.mxp_fatafat_player_engagement
            WHERE {DATE_RANGE} AND {BASE}
        )
        SELECT s.uuid,
            COALESCE(d.age_group, 'Unknown') AS age_group,
            COALESCE(d.gender, 'Unknown') AS gender
        FROM streamers s
        LEFT JOIN mxp_age_gender_details_table_v3 d ON s.uuid = d.uuid
    """,

    "q24b_channel.csv": f"""
        WITH channel_watchtime AS (
            SELECT uuid,
                CASE
                    WHEN dputmsource IN (
                        'perf_m','perf_g','fatafat_inmobi','fatafat_aff_affle',
                        'fatafat_aff_inmobi','fatafat_aff_xiaomi','perf_xiaomi',
                        'fatafat_aff_affinity','aff_affle','perf_inmobi','perf_affle',
                        'perf_aff','branding_meta','branding_META','branding_YT',
                        'branding_publisher','google_web',
                        'perf_u','perf_fb','perf_samsung','perf_oppo','perf_vivo',
                        'perf_realme','perf_tiktok','perf_snap','perf_twitter',
                        'perf_dv360','perf_moloco','perf_mintegral','perf_unity',
                        'perf_applovin','perf_ironsource','perf_liftoff',
                        'perf_digital_turbine','perf_aura','perf_adjoe',
                        'perf_chartboost','perf_pangle','perf_bigo','perf_kwai',
                        'perf_glance','perf_taboola'
                    ) THEN 'Paid'
                    WHEN dputmsource = 'mx_internal_notif' THEN 'Push'
                    WHEN dputmsource IN (
                        'personal-ott-toast-v3','personal-ott-toast-v4',
                        'personal-ott-toast-v5','ott_nudges'
                    ) THEN 'OTT Notification'
                    WHEN dputmsource IN (
                        'paid_int-con-perf-dfp_mx_internal-app',
                        'house_int-con-perf-dfp_mx_internal-app'
                    ) THEN 'Internal Ad'
                    WHEN dputmsource IS NULL OR dputmsource = '' THEN 'Organic'
                    ELSE 'Other'
                END AS channel_category,
                SUM(CAST(playtime AS FLOAT)) AS total_playtime
            FROM fatafat.mxp_fatafat_player_engagement
            WHERE {DATE_RANGE} AND {BASE}
            GROUP BY uuid, channel_category
        ),
        ranked AS (
            SELECT uuid,
                channel_category AS primary_channel,
                ROW_NUMBER() OVER (PARTITION BY uuid ORDER BY total_playtime DESC) AS rn
            FROM channel_watchtime
        )
        SELECT uuid, primary_channel FROM ranked WHERE rn = 1
    """,

    "q25_persona_tags.csv": f"""
        WITH streamers AS (
            SELECT DISTINCT uuid
            FROM fatafat.mxp_fatafat_player_engagement
            WHERE {DATE_RANGE} AND {BASE}
        )
        SELECT s.uuid, p.persona_name
        FROM streamers s
        JOIN mxp_persona_details_table_v3 p ON s.uuid = p.uuid
        WHERE p.source = 'ml'
    """,
}


# Export each query to CSV
output_dir = os.path.dirname(os.path.abspath(__file__))

for filename, query in QUERIES.items():
    filepath = os.path.join(output_dir, filename)
    print(f"Running {filename}...", end=" ", flush=True)
    t0 = time.time()

    cur = conn.cursor()
    cur.execute(query)

    # Get column names from cursor description
    columns = [desc[0] for desc in cur.description]

    # Write to CSV in batches
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

    cur.close()
    elapsed = time.time() - t0
    print(f"{row_count:,} rows in {elapsed:.1f}s → {filepath}")

conn.close()
print(f"\n✅ All 7 CSVs exported. Ready to run phase2_clustering.py")
