"""
OTT Cross-Platform Overlap Analysis
====================================
For each Fatafat persona, measures OTT overlap rate, OTT genre preferences,
OTT watchtime depth, and content gap signals.

Input: fatafat_personas_phase2_2.csv (clusters), Redshift (OTT data)
Output: Console analysis + ott_overlap_profiles.csv
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
OUTPUT_DIR = os.path.join(os.path.dirname(DIR), 'output')

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
print("OTT CROSS-PLATFORM OVERLAP ANALYSIS")
print("=" * 80)

# ============================================================
# STEP 1: Export OTT overlap data from Redshift
# ============================================================
ott_path = os.path.join(DATA_DIR, "ott_overlap.csv")
if not os.path.exists(ott_path):
    print("\n--- Exporting OTT overlap data ---")
    conn = psycopg2.connect(
        host='vpce-0cfaee168d10434e7-a1iibn6p.vpce-svc-09b1fc38f11e9bfef.ap-south-1.vpce.amazonaws.com',
        port=5439, dbname='mxbi',
        user=os.environ['REDSHIFT_USERNAME'],
        password=os.environ['REDSHIFT_PASSWORD'],
        sslmode='require'
    )
    cur = conn.cursor()

    # Step 1a: Per-user OTT engagement metrics
    print("  Exporting per-user OTT metrics...")
    t0 = time.time()
    cur.execute("""
        WITH fatafat_users AS (
            SELECT DISTINCT uuid
            FROM fatafat.mxp_fatafat_player_engagement
            WHERE DATE(start_date) BETWEEN '2026-03-30' AND '2026-04-05'
              AND event = 'onlineStreamEnd'
              AND CAST(playtime AS FLOAT) >= 3000
              AND networkType IS NOT NULL AND internalNetworkStatus > 1
              AND pagetype = 'titlePage'
        ),
        ott_user_video AS (
            SELECT c.uuid, c.videoid,
                SUM(CAST(c.playtime AS FLOAT))/60000 as minutes
            FROM content_stream_end_table_v2 c
            INNER JOIN fatafat_users f ON c.uuid = f.uuid
            WHERE DATE(c.start_date) BETWEEN '2026-03-30' AND '2026-04-05'
              AND CAST(c.playtime AS FLOAT) >= 3000
            GROUP BY c.uuid, c.videoid
        ),
        ott_with_cms AS (
            SELECT ov.uuid, ov.videoid, ov.minutes,
                cms.genre_name, cms.tv_show_name, cms.content_category, cms.language_name
            FROM ott_user_video ov
            JOIN (SELECT DISTINCT video_id, genre_name, tv_show_name, content_category, language_name
                  FROM daily_cms_data_table
                  WHERE genre_name NOT IN ('[]','[unknown]')) cms
            ON ov.videoid = cms.video_id
        )
        SELECT uuid,
            COUNT(DISTINCT videoid) as ott_videos,
            ROUND(SUM(minutes), 2) as ott_minutes,
            COUNT(DISTINCT tv_show_name) as ott_shows,
            -- Top genre (by watchtime)
            MAX(CASE WHEN rn = 1 THEN genre_name END) as top_ott_genre,
            MAX(CASE WHEN rn = 1 THEN tv_show_name END) as top_ott_show,
            -- Genre flags
            MAX(CASE WHEN genre_name ILIKE '%action%' OR genre_name ILIKE '%crime%' THEN 1 ELSE 0 END) as watches_action,
            MAX(CASE WHEN genre_name ILIKE '%comedy%' THEN 1 ELSE 0 END) as watches_comedy,
            MAX(CASE WHEN genre_name ILIKE '%romance%' THEN 1 ELSE 0 END) as watches_romance,
            MAX(CASE WHEN genre_name ILIKE '%drama%' THEN 1 ELSE 0 END) as watches_drama,
            MAX(CASE WHEN genre_name ILIKE '%anime%' THEN 1 ELSE 0 END) as watches_anime,
            MAX(CASE WHEN genre_name ILIKE '%fantasy%' OR genre_name ILIKE '%sci-fi%' THEN 1 ELSE 0 END) as watches_fantasy_scifi,
            MAX(CASE WHEN genre_name ILIKE '%thriller%' OR genre_name ILIKE '%horror%' THEN 1 ELSE 0 END) as watches_thriller,
            MAX(CASE WHEN genre_name ILIKE '%vdesi%' THEN 1 ELSE 0 END) as watches_vdesi,
            MAX(CASE WHEN content_category = 'Fatafat' THEN 0 ELSE 1 END) as is_ott_content
        FROM (
            SELECT *, ROW_NUMBER() OVER (PARTITION BY uuid ORDER BY minutes DESC) as rn
            FROM ott_with_cms
        )
        GROUP BY uuid
    """)
    cols = [d[0] for d in cur.description]
    row_count = 0
    with open(ott_path, 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(cols)
        while True:
            rows = cur.fetchmany(10000)
            if not rows: break
            w.writerows(rows)
            row_count += len(rows)
            if row_count % 100000 == 0:
                print(f"    {row_count:,} rows...")

    print(f"  Exported {row_count:,} users in {time.time()-t0:.0f}s → {ott_path}")
    cur.close()
    conn.close()
else:
    print(f"  OTT data already exported: {ott_path}")

# ============================================================
# STEP 2: Load and merge
# ============================================================
print("\n--- Loading ---")
df = pd.read_csv(os.path.join(DATA_DIR, "fatafat_personas_phase2_2.csv"))
ott = pd.read_csv(ott_path)

cluster_col = 'cluster' if 'cluster' in df.columns else 'cluster_v2'
role_col = 'strategic_role' if 'strategic_role' in df.columns else 'strategic_role_v2'

print(f"  Fatafat users: {len(df):,}")
print(f"  OTT overlap users: {len(ott):,}")

df = df.merge(ott, on='uuid', how='left')
df['has_ott'] = df['ott_minutes'].notna() & (df['ott_minutes'] > 0)

# Fill missing OTT fields
for col in ['ott_videos', 'ott_minutes', 'ott_shows']:
    df[col] = df[col].fillna(0)
for col in ['watches_action', 'watches_comedy', 'watches_romance', 'watches_drama',
            'watches_anime', 'watches_fantasy_scifi', 'watches_thriller', 'watches_vdesi']:
    df[col] = df[col].fillna(0).astype(int)

overall_overlap = df['has_ott'].mean() * 100
print(f"\n  Overall OTT overlap: {df['has_ott'].sum():,} / {len(df):,} = {overall_overlap:.1f}%")

persona_names = {0: 'Discovery Sampler', 1: 'Romance Binger', 2: 'Platform Devotee',
                 3: 'Male Crossover', 5: 'Engaged Explorer'}

# ============================================================
# STEP 3: Per-Persona OTT Profiles
# ============================================================
print("\n" + "=" * 80)
print("PER-PERSONA OTT CROSS-PLATFORM PROFILES")
print("=" * 80)

ott_genres = ['watches_action', 'watches_comedy', 'watches_romance', 'watches_drama',
              'watches_anime', 'watches_fantasy_scifi', 'watches_thriller', 'watches_vdesi']
genre_labels = {'watches_action': 'Action/Crime', 'watches_comedy': 'Comedy',
                'watches_romance': 'Romance', 'watches_drama': 'Drama',
                'watches_anime': 'Anime', 'watches_fantasy_scifi': 'Fantasy/Sci-Fi',
                'watches_thriller': 'Thriller/Horror', 'watches_vdesi': 'Vdesi (Dubbed)'}

for cid in sorted(df[cluster_col].unique()):
    c = df[df[cluster_col] == cid]
    n = len(c)
    if n < 10: continue
    name = persona_names.get(cid, f'Cluster {cid}')
    role = c[role_col].iloc[0] if role_col in c.columns else '?'

    ott_users = c[c['has_ott']]
    overlap_pct = len(ott_users) / n * 100

    print(f"\n{'='*70}")
    print(f"{name} ({role}) — {n:,} users")
    print(f"{'='*70}")

    # Overlap rate
    print(f"\n  OTT Overlap: {len(ott_users):,} / {n:,} = {overlap_pct:.1f}%")

    if len(ott_users) < 50:
        print(f"  Too few OTT users for detailed analysis")
        continue

    # OTT watchtime depth
    print(f"\n  OTT Watchtime (overlap users only):")
    print(f"    Avg OTT minutes/week:  {ott_users['ott_minutes'].mean():.1f}")
    print(f"    Median OTT min/week:   {ott_users['ott_minutes'].median():.1f}")
    print(f"    Avg OTT shows:         {ott_users['ott_shows'].mean():.1f}")
    print(f"    Avg Fatafat min/week:  {ott_users['total_minutes'].mean():.1f}")
    fatafat_vs_ott = ott_users['total_minutes'].mean() / max(ott_users['ott_minutes'].mean(), 0.1)
    print(f"    Fatafat/OTT ratio:     {fatafat_vs_ott:.2f}x")
    if fatafat_vs_ott > 2:
        print(f"    → Fatafat-native: watches much more Fatafat than OTT")
    elif fatafat_vs_ott > 0.5:
        print(f"    → Balanced: similar engagement on both platforms")
    else:
        print(f"    → OTT-primary: watches more OTT than Fatafat")

    # OTT genre preferences
    print(f"\n  OTT Genre Preferences (% of overlap users who watch each):")
    genre_rates = {}
    for col in ott_genres:
        rate = ott_users[col].mean() * 100
        genre_rates[genre_labels[col]] = rate

    for label, rate in sorted(genre_rates.items(), key=lambda x: -x[1]):
        bar = '█' * int(rate / 5)
        print(f"    {label:20s} {rate:>5.1f}% {bar}")

    # Top OTT shows
    if 'top_ott_show' in ott_users.columns:
        top_shows = ott_users['top_ott_show'].value_counts().head(5)
        print(f"\n  Top OTT Shows:")
        for show, cnt in top_shows.items():
            if pd.notna(show) and show not in ('None', 'nan', '[]'):
                print(f"    {show}: {cnt:,}")

    # Content gap signal
    print(f"\n  Content Gap Signals:")
    # Genres watched on OTT but not available on Fatafat
    fatafat_genres = {'Romance', 'Drama', 'Thriller/Horror', 'Fantasy/Sci-Fi'}
    for label, rate in sorted(genre_rates.items(), key=lambda x: -x[1]):
        if label not in fatafat_genres and rate > 20:
            print(f"    ⚠ {label}: {rate:.0f}% watch on OTT — NOT on Fatafat catalog")

# ============================================================
# STEP 4: Comparative Summary
# ============================================================
print("\n" + "=" * 80)
print("COMPARATIVE SUMMARY")
print("=" * 80)

print(f"\n{'Persona':25s} {'Users':>8s} {'OTT%':>6s} {'OTT min':>8s} {'FF min':>8s} {'Ratio':>7s} {'Top OTT Genre'}")
print('-' * 90)

summary_rows = []
for cid in sorted(df[cluster_col].unique()):
    c = df[df[cluster_col] == cid]
    n = len(c)
    if n < 10: continue
    name = persona_names.get(cid, f'C{cid}')
    ott_u = c[c['has_ott']]
    overlap_pct = len(ott_u) / n * 100
    ott_min = ott_u['ott_minutes'].mean() if len(ott_u) > 0 else 0
    ff_min = ott_u['total_minutes'].mean() if len(ott_u) > 0 else 0
    ratio = ff_min / max(ott_min, 0.1)

    # Top genre
    top_genre = 'N/A'
    if len(ott_u) > 50:
        rates = {genre_labels[col]: ott_u[col].mean() for col in ott_genres}
        top_genre = max(rates, key=rates.get)

    print(f"{name:25s} {n:>8,} {overlap_pct:>5.1f}% {ott_min:>7.0f} {ff_min:>7.0f} {ratio:>6.2f}x  {top_genre}")

    row = {'persona': name, 'users': n, 'ott_overlap_pct': round(overlap_pct, 1),
           'ott_avg_min': round(ott_min, 1), 'ff_avg_min': round(ff_min, 1),
           'ff_ott_ratio': round(ratio, 2), 'top_ott_genre': top_genre}

    if len(ott_u) > 50:
        for col in ott_genres:
            row[genre_labels[col]] = round(ott_u[col].mean() * 100, 1)
    summary_rows.append(row)

# Export
summary_df = pd.DataFrame(summary_rows)
export_path = os.path.join(OUTPUT_DIR, "ott_overlap_profiles.csv")
summary_df.to_csv(export_path, index=False)
print(f"\n✅ Exported: {export_path}")

# Save enriched df
df.to_csv(os.path.join(DATA_DIR, "fatafat_personas_with_ott.csv"), index=False)
print(f"✅ Exported: fatafat_personas_with_ott.csv")

print(f"\n📊 KEY INSIGHTS:")
print(f"   Overall OTT overlap: {overall_overlap:.1f}%")
print(f"   OTT data adds cross-platform genre preferences to each persona")
print(f"   Content gaps: genres watched on OTT but absent from Fatafat catalog")
