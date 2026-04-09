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

# Check additional CMS fields for Fatafat shows
cur.execute("""
    SELECT DISTINCT tv_show_name, categories, tag_name, is_original_type, original_acquired, maturity_rating
    FROM daily_cms_data_table
    WHERE is_fatafat_micro_show = '1'
      AND tv_show_name NOT IN ('[]', '[unknown]')
    LIMIT 30
""")
cols = [d[0] for d in cur.description]
print(' | '.join(cols))
print('-' * 120)
for row in cur.fetchall():
    print(' | '.join(str(x)[:30] for x in row))

print("\n\n=== DISTINCT categories ===")
cur.execute("""
    SELECT categories, COUNT(DISTINCT channel_ids) as shows
    FROM daily_cms_data_table
    WHERE is_fatafat_micro_show = '1' AND tv_show_name NOT IN ('[]', '[unknown]')
    GROUP BY categories ORDER BY shows DESC LIMIT 20
""")
for row in cur.fetchall():
    print(f"  {str(row[0]):50s} → {row[1]} shows")

print("\n=== DISTINCT tag_name (top 20) ===")
cur.execute("""
    SELECT tag_name, COUNT(DISTINCT channel_ids) as shows
    FROM daily_cms_data_table
    WHERE is_fatafat_micro_show = '1' AND tv_show_name NOT IN ('[]', '[unknown]')
    GROUP BY tag_name ORDER BY shows DESC LIMIT 20
""")
for row in cur.fetchall():
    print(f"  {str(row[0]):50s} → {row[1]} shows")

print("\n=== DISTINCT is_original_type ===")
cur.execute("""
    SELECT is_original_type, COUNT(DISTINCT channel_ids) as shows
    FROM daily_cms_data_table
    WHERE is_fatafat_micro_show = '1' AND tv_show_name NOT IN ('[]', '[unknown]')
    GROUP BY is_original_type ORDER BY shows DESC
""")
for row in cur.fetchall():
    print(f"  {str(row[0]):30s} → {row[1]} shows")

print("\n=== DISTINCT original_acquired ===")
cur.execute("""
    SELECT original_acquired, COUNT(DISTINCT channel_ids) as shows
    FROM daily_cms_data_table
    WHERE is_fatafat_micro_show = '1' AND tv_show_name NOT IN ('[]', '[unknown]')
    GROUP BY original_acquired ORDER BY shows DESC
""")
for row in cur.fetchall():
    print(f"  {str(row[0]):30s} → {row[1]} shows")

print("\n=== DISTINCT maturity_rating ===")
cur.execute("""
    SELECT maturity_rating, COUNT(DISTINCT channel_ids) as shows
    FROM daily_cms_data_table
    WHERE is_fatafat_micro_show = '1' AND tv_show_name NOT IN ('[]', '[unknown]')
    GROUP BY maturity_rating ORDER BY shows DESC
""")
for row in cur.fetchall():
    print(f"  {str(row[0]):30s} → {row[1]} shows")

cur.close()
conn.close()
