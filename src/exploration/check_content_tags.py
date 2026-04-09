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

# Check tag_ids and tag_name more carefully — are there multiple tags per show?
print("=== tag_ids samples (first 20 shows) ===")
cur.execute("""
    SELECT DISTINCT tv_show_name, tag_ids, tag_name
    FROM daily_cms_data_table
    WHERE is_fatafat_micro_show = '1'
      AND tv_show_name NOT IN ('[]', '[unknown]')
    LIMIT 20
""")
for row in cur.fetchall():
    print(f"  {str(row[0]):40s} | tag_ids: {str(row[1]):30s} | tag_name: {row[2]}")

# Check if there are content-descriptive tags beyond the source tags
print("\n=== ALL distinct tag_name values ===")
cur.execute("""
    SELECT tag_name, COUNT(DISTINCT channel_ids) as shows
    FROM daily_cms_data_table
    WHERE is_fatafat_micro_show = '1' AND tv_show_name NOT IN ('[]', '[unknown]')
    GROUP BY tag_name ORDER BY shows DESC
""")
for row in cur.fetchall():
    print(f"  {str(row[0]):50s} → {row[1]} shows")

# Check secondary_genre_name — full list
print("\n=== ALL distinct secondary_genre_name values ===")
cur.execute("""
    SELECT secondary_genre_name, COUNT(DISTINCT channel_ids) as shows
    FROM daily_cms_data_table
    WHERE is_fatafat_micro_show = '1' AND tv_show_name NOT IN ('[]', '[unknown]')
    GROUP BY secondary_genre_name ORDER BY shows DESC
""")
for row in cur.fetchall():
    print(f"  {str(row[0]):50s} → {row[1]} shows")

# Check genre_name + secondary_genre_name combos
print("\n=== genre × secondary_genre (all combos) ===")
cur.execute("""
    SELECT genre_name, secondary_genre_name, COUNT(DISTINCT channel_ids) as shows
    FROM daily_cms_data_table
    WHERE is_fatafat_micro_show = '1' AND tv_show_name NOT IN ('[]', '[unknown]')
    GROUP BY genre_name, secondary_genre_name ORDER BY shows DESC
""")
for row in cur.fetchall():
    print(f"  {str(row[0]):25s} × {str(row[1]):25s} → {row[2]} shows")

# Check if there's a separate tags table or if tag_ids maps to something
print("\n=== Sample tag_ids values ===")
cur.execute("""
    SELECT DISTINCT tag_ids
    FROM daily_cms_data_table
    WHERE is_fatafat_micro_show = '1' AND tv_show_name NOT IN ('[]', '[unknown]')
    LIMIT 20
""")
for row in cur.fetchall():
    print(f"  {row[0]}")

cur.close()
conn.close()
