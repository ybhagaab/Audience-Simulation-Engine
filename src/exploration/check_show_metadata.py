import psycopg2, os

def load_env(path):
    if os.path.exists(path):
        with open(path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    k, v = line.split('=', 1)
                    os.environ[k.strip()] = v.strip()

load_env('/Users/ybhagaab/Synthetic Persona/.kiro/settings/.env')

conn = psycopg2.connect(
    host='vpce-0cfaee168d10434e7-a1iibn6p.vpce-svc-09b1fc38f11e9bfef.ap-south-1.vpce.amazonaws.com',
    port=5439, dbname='mxbi',
    user=os.environ['REDSHIFT_USERNAME'],
    password=os.environ['REDSHIFT_PASSWORD'],
    sslmode='require'
)
cur = conn.cursor()

# Check tv_show_name — the show names themselves are descriptive
print("=== Top 50 Fatafat show names with genre + secondary genre ===")
cur.execute("""
    SELECT DISTINCT tv_show_name, genre_name, secondary_genre_name, tag_name, original_acquired
    FROM daily_cms_data_table
    WHERE is_fatafat_micro_show = '1'
      AND tv_show_name NOT IN ('[]', '[unknown]')
    ORDER BY tv_show_name
    LIMIT 60
""")
for row in cur.fetchall():
    print(f"  {str(row[0]):45s} | {str(row[1]):20s} | {str(row[2]):20s} | {str(row[3]):20s} | {str(row[4])}")

# Check deal_name — might have content deal/package info
print("\n=== deal_name values ===")
cur.execute("""
    SELECT deal_name, COUNT(DISTINCT channel_ids) as shows
    FROM daily_cms_data_table
    WHERE is_fatafat_micro_show = '1' AND tv_show_name NOT IN ('[]', '[unknown]')
    AND deal_name IS NOT NULL AND deal_name != ''
    GROUP BY deal_name ORDER BY shows DESC LIMIT 20
""")
for row in cur.fetchall():
    print(f"  {str(row[0]):50s} → {row[1]} shows")

# Check pack_name — content packages
print("\n=== pack_name values ===")
cur.execute("""
    SELECT pack_name, COUNT(DISTINCT channel_ids) as shows
    FROM daily_cms_data_table
    WHERE is_fatafat_micro_show = '1' AND tv_show_name NOT IN ('[]', '[unknown]')
    AND pack_name IS NOT NULL AND pack_name != '[]'
    GROUP BY pack_name ORDER BY shows DESC LIMIT 20
""")
for row in cur.fetchall():
    print(f"  {str(row[0]):50s} → {row[1]} shows")

cur.close()
conn.close()
