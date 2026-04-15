"""
Geo Exploration: Geographic distribution per persona
====================================================
Standalone analysis — does NOT modify existing persona data.
Exports geo per user, merges with existing clusters, shows distribution.
"""

import pandas as pd
import numpy as np
import psycopg2
import csv
import os
import time
import warnings
warnings.filterwarnings('ignore')

DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(os.path.dirname(DIR), 'data')

def load_env(path):
    if os.path.exists(path):
        with open(path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    k, v = line.split('=', 1)
                    os.environ[k.strip()] = v.strip()

for p in [os.path.join(DIR, ".env"),
          os.path.join(os.path.dirname(DIR), ".kiro", "settings", ".env"),
          os.path.join(os.path.dirname(os.path.dirname(DIR)), ".kiro", "settings", ".env")]:
    if os.path.exists(p):
        load_env(p)
        break

print("=" * 80)
print("GEO EXPLORATION: Geographic Distribution per Persona")
print("=" * 80)

# Export primary state per user
geo_path = os.path.join(DATA_DIR, "geo_exploration.csv")
if not os.path.exists(geo_path):
    print("\n--- Exporting geo data ---")
    conn = psycopg2.connect(
        host='vpce-0cfaee168d10434e7-a1iibn6p.vpce-svc-09b1fc38f11e9bfef.ap-south-1.vpce.amazonaws.com',
        port=5439, dbname='mxbi',
        user=os.environ['REDSHIFT_USERNAME'],
        password=os.environ['REDSHIFT_PASSWORD'],
        sslmode='require'
    )
    cur = conn.cursor()
    t0 = time.time()
    cur.execute("""
        WITH user_geo AS (
            SELECT uuid, regionname, city,
                SUM(CAST(playtime AS FLOAT)) as total_pt,
                ROW_NUMBER() OVER (PARTITION BY uuid ORDER BY SUM(CAST(playtime AS FLOAT)) DESC) as rn
            FROM fatafat.mxp_fatafat_player_engagement
            WHERE DATE(start_date) BETWEEN '2026-03-30' AND '2026-04-05'
              AND event = 'onlineStreamEnd'
              AND CAST(playtime AS FLOAT) >= 3000
              AND networkType IS NOT NULL AND internalNetworkStatus > 1
              AND pagetype = 'titlePage'
              AND regionname IS NOT NULL AND regionname != ''
            GROUP BY uuid, regionname, city
        )
        SELECT uuid, regionname as state, city
        FROM user_geo WHERE rn = 1
    """)
    cols = [d[0] for d in cur.description]
    row_count = 0
    with open(geo_path, 'w', newline='') as f:
        w = csv.writer(f); w.writerow(cols)
        while True:
            rows = cur.fetchmany(10000)
            if not rows: break
            w.writerows(rows)
            row_count += len(rows)
    print(f"  {row_count:,} users in {time.time()-t0:.0f}s → {geo_path}")
    cur.close(); conn.close()
else:
    print(f"  Geo data exists: {geo_path}")

# Load and merge
print("\n--- Loading ---")
df = pd.read_csv(os.path.join(DATA_DIR, "fatafat_personas_phase2_2.csv"))
geo = pd.read_csv(geo_path)
cluster_col = 'cluster' if 'cluster' in df.columns else 'cluster_v2'

merged = df[[col for col in ['uuid', cluster_col, 'strategic_role', 'total_minutes', 'gender'] if col in df.columns]].merge(geo, on='uuid', how='inner')
print(f"  {len(merged):,} users with geo data ({len(merged)/len(df)*100:.1f}% coverage)")

persona_names = {0: 'Discovery Sampler', 1: 'Romance Binger', 2: 'Platform Devotee',
                 3: 'Male Crossover', 5: 'Engaged Explorer'}

# Overall geo distribution
print("\n--- Overall Top 10 States ---")
overall = merged['state'].value_counts(normalize=True).head(10)
for s, p in overall.items():
    print(f"  {s:40s} {p*100:.1f}%")

# Per-persona geo distribution
print("\n" + "=" * 80)
print("PER-PERSONA GEOGRAPHIC PROFILE")
print("=" * 80)

for cid in sorted(persona_names.keys()):
    c = merged[merged[cluster_col] == cid]
    if len(c) < 100: continue
    name = persona_names[cid]

    print(f"\n{'='*70}")
    print(f"{name} ({len(c):,} users with geo)")
    print(f"{'='*70}")

    # Top states
    states = c['state'].value_counts(normalize=True)
    print(f"\n  Top 10 States:")
    for s, p in states.head(10).items():
        # Compare to overall
        overall_p = overall.get(s, 0)
        idx = p / max(overall_p, 0.001)
        flag = ' ↑ over-index' if idx > 1.2 else ' ↓ under-index' if idx < 0.8 else ''
        print(f"    {s:35s} {p*100:>5.1f}% (vs {overall_p*100:.1f}% overall, {idx:.2f}x){flag}")

    # Top cities
    cities = c['city'].value_counts(normalize=True)
    print(f"\n  Top 5 Cities:")
    for ci, p in cities.head(5).items():
        print(f"    {ci:25s} {p*100:.1f}%")

    # Regional concentration
    top3_pct = states.head(3).sum() * 100
    print(f"\n  Top 3 states = {top3_pct:.1f}% of persona")

    # Hindi belt vs South vs West vs East
    hindi_belt = ['Uttar Pradesh', 'Bihar', 'Madhya Pradesh', 'Rajasthan', 'Jharkhand',
                  'Chhattisgarh', 'Haryana', 'Uttarakhand', 'Himachal Pradesh',
                  'National Capital Territory of Delhi']
    south = ['Tamil Nadu', 'Karnataka', 'Telangana', 'Kerala', 'Andhra Pradesh']
    west = ['Maharashtra', 'Gujarat', 'Goa']
    east = ['West Bengal', 'Odisha', 'Assam']

    hindi_pct = c[c['state'].isin(hindi_belt)].shape[0] / len(c) * 100
    south_pct = c[c['state'].isin(south)].shape[0] / len(c) * 100
    west_pct = c[c['state'].isin(west)].shape[0] / len(c) * 100
    east_pct = c[c['state'].isin(east)].shape[0] / len(c) * 100

    print(f"\n  Regional Split:")
    print(f"    Hindi Belt:  {hindi_pct:.1f}%")
    print(f"    South:       {south_pct:.1f}%")
    print(f"    West:        {west_pct:.1f}%")
    print(f"    East:        {east_pct:.1f}%")

# Cross-persona comparison
print("\n" + "=" * 80)
print("CROSS-PERSONA REGIONAL COMPARISON")
print("=" * 80)

hindi_belt = ['Uttar Pradesh', 'Bihar', 'Madhya Pradesh', 'Rajasthan', 'Jharkhand',
              'Chhattisgarh', 'Haryana', 'Uttarakhand', 'Himachal Pradesh',
              'National Capital Territory of Delhi']
south = ['Tamil Nadu', 'Karnataka', 'Telangana', 'Kerala', 'Andhra Pradesh']
west = ['Maharashtra', 'Gujarat', 'Goa']

print(f"\n{'Persona':25s} {'Hindi Belt':>12s} {'South':>8s} {'West':>8s} {'East':>8s} {'Top State'}")
print('-' * 80)
for cid in sorted(persona_names.keys()):
    c = merged[merged[cluster_col] == cid]
    if len(c) < 100: continue
    name = persona_names[cid]
    hb = c[c['state'].isin(hindi_belt)].shape[0] / len(c) * 100
    so = c[c['state'].isin(south)].shape[0] / len(c) * 100
    we = c[c['state'].isin(west)].shape[0] / len(c) * 100
    ea = c[c['state'].isin(['West Bengal', 'Odisha', 'Assam'])].shape[0] / len(c) * 100
    top = c['state'].value_counts().index[0]
    print(f"{name:25s} {hb:>11.1f}% {so:>7.1f}% {we:>7.1f}% {ea:>7.1f}%  {top}")

print("\n✅ Exploration complete. No existing data modified.")
