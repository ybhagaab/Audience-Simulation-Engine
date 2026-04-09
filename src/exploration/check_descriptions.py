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

# Check if there's a description/title field
print("=== Checking for description-like columns ===")
cur.execute("""
    SELECT column_name FROM information_schema.columns
    WHERE table_name = 'daily_cms_data_table'
    ORDER BY ordinal_position
""")
cols = [r[0] for r in cur.fetchall()]
print(f"All columns ({len(cols)}):")
for c in cols:
    print(f"  {c}")

# Check title field — this might be the episode/show description
print("\n=== Sample 'title' values for Fatafat shows ===")
cur.execute("""
    SELECT DISTINCT tv_show_name, title
    FROM daily_cms_data_table
    WHERE is_fatafat_micro_show = '1'
      AND tv_show_name NOT IN ('[]', '[unknown]')
      AND title IS NOT NULL AND title != '[]'
    LIMIT 30
""")
for row in cur.fetchall():
    print(f"  Show: {str(row[0]):40s}")
    print(f"  Title: {str(row[1])[:120]}")
    print()

cur.close()
conn.close()
