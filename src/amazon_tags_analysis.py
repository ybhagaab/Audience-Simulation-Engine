"""
Amazon-Sourced Persona Tags: Tiered Commercial Profile Analysis
===============================================================
Compares Amazon (actual shopping behavior) vs ML (predicted) persona tags
per persona cluster to build tiered confidence commercial profiles.

Input: fatafat_personas_phase2_2.csv (clusters), Redshift (Amazon tags)
Output: Console analysis + amazon_tags_comparison.csv
"""

import pandas as pd
import numpy as np
import psycopg2
import csv
import os
import sys
import time
import warnings
warnings.filterwarnings('ignore')

DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(os.path.dirname(DIR), 'data')
OUTPUT_DIR = os.path.join(os.path.dirname(DIR), 'output')

# Load .env
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
print("AMAZON-SOURCED TAGS: Tiered Commercial Profile Analysis")
print("=" * 80)

# ============================================================
# STEP 1: Export Amazon-sourced tags from Redshift
# ============================================================
amz_path = os.path.join(DATA_DIR, "q25_amazon_tags.csv")
if not os.path.exists(amz_path):
    print("\n--- Exporting Amazon-sourced tags from Redshift ---")
    conn = psycopg2.connect(
        host='vpce-0cfaee168d10434e7-a1iibn6p.vpce-svc-09b1fc38f11e9bfef.ap-south-1.vpce.amazonaws.com',
        port=5439, dbname='mxbi',
        user=os.environ['REDSHIFT_USERNAME'],
        password=os.environ['REDSHIFT_PASSWORD'],
        sslmode='require'
    )
    cur = conn.cursor()
    # Same aggregation as ML tags but for amazon source
    cur.execute("""
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
            WHERE p.source = 'amazon'
        )
        SELECT
            uuid,
            COUNT(DISTINCT persona_name) as amz_tag_count,
            MAX(CASE WHEN persona_name ILIKE '%fashion%' OR persona_name ILIKE '%beauty%'
                     OR persona_name ILIKE '%grooming%' OR persona_name ILIKE '%ethnic wear%'
                     OR persona_name ILIKE '%jewelry%' OR persona_name ILIKE '%clothing%'
                THEN 1 ELSE 0 END) as amz_fashion_beauty,
            MAX(CASE WHEN persona_name ILIKE '%electronics%' OR persona_name ILIKE '%computer%'
                     OR persona_name ILIKE '%smartphone%' OR persona_name ILIKE '%mobile%'
                     OR persona_name ILIKE '%tablet%' OR persona_name ILIKE '%tech%'
                THEN 1 ELSE 0 END) as amz_electronics_tech,
            MAX(CASE WHEN persona_name ILIKE '%health%' OR persona_name ILIKE '%fitness%'
                     OR persona_name ILIKE '%nutrition%'
                THEN 1 ELSE 0 END) as amz_health_fitness,
            MAX(CASE WHEN persona_name ILIKE '%home%' OR persona_name ILIKE '%kitchen%'
                     OR persona_name ILIKE '%appliance%'
                THEN 1 ELSE 0 END) as amz_home_kitchen,
            MAX(CASE WHEN persona_name ILIKE '%travel%'
                THEN 1 ELSE 0 END) as amz_travel,
            MAX(CASE WHEN persona_name ILIKE '%parent%' OR persona_name ILIKE '%baby%'
                THEN 1 ELSE 0 END) as amz_parents_baby,
            MAX(CASE WHEN persona_name ILIKE '%automotive%'
                THEN 1 ELSE 0 END) as amz_automotive,
            MAX(CASE WHEN persona_name ILIKE '%affluent%' OR persona_name ILIKE '%premium%'
                THEN 1 ELSE 0 END) as amz_affluent_premium
        FROM user_tags
        GROUP BY uuid
    """)
    cols = [d[0] for d in cur.description]
    rows = cur.fetchall()
    with open(amz_path, 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(cols)
        w.writerows(rows)
    print(f"  Exported {len(rows):,} users with Amazon tags → {amz_path}")
    cur.close()
    conn.close()
else:
    print(f"  Amazon tags already exported: {amz_path}")

# ============================================================
# STEP 2: Load data
# ============================================================
print("\n--- Loading ---")
df = pd.read_csv(os.path.join(DATA_DIR, "fatafat_personas_phase2_2.csv"))
amz_tags = pd.read_csv(amz_path)

cluster_col = 'cluster' if 'cluster' in df.columns else 'cluster_v2'
print(f"  Personas: {len(df):,} users")
print(f"  Amazon tags: {len(amz_tags):,} users")
print(f"  ML tags already in Phase 2.2 data")

# Merge Amazon tags only (ML tags already in Phase 2.2 data)
df = df.merge(amz_tags, on='uuid', how='left')

# ML tag count is already in the data as 'tag_count'
if 'tag_count' in df.columns:
    df['ml_tag_count'] = df['tag_count'].fillna(0).astype(int)
else:
    df['ml_tag_count'] = 0
df['amz_tag_count'] = df['amz_tag_count'].fillna(0).astype(int)

# Tag tier classification
df['tag_tier'] = 'No Tags'
df.loc[df['ml_tag_count'] > 0, 'tag_tier'] = 'ML Only'
df.loc[df['amz_tag_count'] > 0, 'tag_tier'] = 'Amazon Only'
df.loc[(df['ml_tag_count'] > 0) & (df['amz_tag_count'] > 0), 'tag_tier'] = 'Both'

print(f"\n  Tag Tier Distribution:")
print(df['tag_tier'].value_counts().to_string())

# ============================================================
# STEP 3: Per-Persona Tiered Commercial Profiles
# ============================================================
print("\n" + "=" * 80)
print("TIERED COMMERCIAL PROFILES PER PERSONA")
print("=" * 80)

interest_cats = {
    'fashion_beauty': 'Fashion/Beauty',
    'electronics_tech': 'Electronics/Tech',
    'health_fitness': 'Health/Fitness',
    'home_kitchen': 'Home/Kitchen',
    'travel': 'Travel',
    'parents_baby': 'Parents/Baby',
    'automotive': 'Automotive',
    'affluent_premium': 'Affluent/Premium',
}

role_col = 'strategic_role' if 'strategic_role' in df.columns else 'strategic_role_v2'
persona_names = {0: 'Discovery Sampler', 1: 'Romance Binger', 2: 'Platform Devotee',
                 3: 'Male Crossover', 5: 'Engaged Explorer'}

for cid in sorted(df[cluster_col].unique()):
    c = df[df[cluster_col] == cid]
    n = len(c)
    if n < 10: continue
    name = persona_names.get(cid, f'Cluster {cid}')
    role = c[role_col].iloc[0] if role_col in c.columns else '?'

    print(f"\n{'='*70}")
    print(f"{name} ({role}) — {n:,} users")
    print(f"{'='*70}")

    # Tier counts
    tiers = c['tag_tier'].value_counts()
    for t in ['Both', 'Amazon Only', 'ML Only', 'No Tags']:
        cnt = tiers.get(t, 0)
        print(f"  {t:15s}: {cnt:>10,} ({cnt/n*100:.1f}%)")

    # Compare interest profiles: Amazon vs ML
    print(f"\n  {'Category':25s} {'Amazon':>10s} {'ML':>10s} {'Delta':>10s} {'Signal'}")
    print(f"  {'-'*65}")

    for suffix, label in interest_cats.items():
        ml_col = f'has_{suffix}'
        amz_col = f'amz_{suffix}'

        # ML rate (among ML-tagged users in this cluster)
        ml_users = c[c['ml_tag_count'] > 0]
        ml_rate = ml_users[ml_col].mean() * 100 if len(ml_users) > 0 and ml_col in ml_users.columns else 0

        # Amazon rate (among Amazon-tagged users in this cluster)
        amz_users = c[c['amz_tag_count'] > 0]
        amz_rate = amz_users[amz_col].mean() * 100 if len(amz_users) > 0 and amz_col in amz_users.columns else 0

        # If ML rate is 0 but we know ML users exist, check if column exists
        if ml_rate == 0 and len(ml_users) > 0 and ml_col not in ml_users.columns:
            ml_rate = -1  # flag as missing

        delta = amz_rate - ml_rate if ml_rate >= 0 else 0
        signal = ''
        if abs(delta) > 10:
            signal = '⬆️ Amazon higher' if delta > 0 else '⬇️ Amazon lower'
        elif abs(delta) > 5:
            signal = '↑ slight' if delta > 0 else '↓ slight'

        print(f"  {label:25s} {amz_rate:>9.1f}% {ml_rate:>9.1f}% {delta:>+9.1f}%  {signal}")

# ============================================================
# STEP 4: Overlap Users — Agreement Analysis
# ============================================================
print("\n" + "=" * 80)
print("AGREEMENT ANALYSIS: Users with BOTH Amazon + ML Tags")
print("=" * 80)

both = df[df['tag_tier'] == 'Both']
print(f"\n  {len(both):,} users have both Amazon and ML tags")

if len(both) > 100:
    print(f"\n  {'Category':25s} {'Amazon':>8s} {'ML':>8s} {'Agree':>8s} {'Disagree':>10s}")
    print(f"  {'-'*60}")

    agreement_data = []
    for suffix, label in interest_cats.items():
        ml_col = f'has_{suffix}'
        amz_col = f'amz_{suffix}'

        if ml_col in both.columns and amz_col in both.columns:
            ml_yes = both[ml_col].mean() * 100
            amz_yes = both[amz_col].mean() * 100
            # Agreement: both say yes or both say no
            agree = ((both[ml_col] == both[amz_col]).mean() * 100)
            disagree = 100 - agree

            agreement_data.append({
                'category': label, 'amazon_pct': amz_yes, 'ml_pct': ml_yes,
                'agreement': agree, 'disagreement': disagree
            })
            print(f"  {label:25s} {amz_yes:>7.1f}% {ml_yes:>7.1f}% {agree:>7.1f}% {disagree:>9.1f}%")

    # Per-persona agreement for overlap users
    print(f"\n  Per-Persona Agreement Rate (avg across all categories):")
    for cid in sorted(df[cluster_col].unique()):
        cb = both[both[cluster_col] == cid]
        if len(cb) < 10: continue
        name = persona_names.get(cid, f'C{cid}')

        agreements = []
        for suffix, label in interest_cats.items():
            ml_col = f'has_{suffix}'
            amz_col = f'amz_{suffix}'
            if ml_col in cb.columns and amz_col in cb.columns:
                agreements.append((cb[ml_col] == cb[amz_col]).mean() * 100)

        avg_agree = np.mean(agreements) if agreements else 0
        print(f"    {name:25s}: {avg_agree:.1f}% agreement ({len(cb):,} overlap users)")

# ============================================================
# STEP 5: Amazon-Only Users — Unique Insights
# ============================================================
print("\n" + "=" * 80)
print("AMAZON-ONLY USERS: Unique Commercial Signals")
print("=" * 80)

amz_only = df[df['tag_tier'] == 'Amazon Only']
print(f"\n  {len(amz_only):,} users have Amazon tags but NO ML tags")

if len(amz_only) > 100:
    print(f"\n  These users are Amazon-identified but not ML-profiled.")
    print(f"  Their Amazon tags represent actual shopping behavior.\n")

    print(f"  {'Category':25s} {'Amazon-Only':>12s} {'All Users (ML)':>14s} {'Delta':>8s}")
    print(f"  {'-'*60}")

    for suffix, label in interest_cats.items():
        amz_col = f'amz_{suffix}'
        ml_col = f'has_{suffix}'

        amz_rate = amz_only[amz_col].mean() * 100 if amz_col in amz_only.columns else 0
        # Compare to overall ML rate
        ml_all = df[df['ml_tag_count'] > 0]
        ml_rate = ml_all[ml_col].mean() * 100 if len(ml_all) > 0 and ml_col in ml_all.columns else 0

        delta = amz_rate - ml_rate
        print(f"  {label:25s} {amz_rate:>11.1f}% {ml_rate:>13.1f}% {delta:>+7.1f}%")

    # Per persona
    print(f"\n  Per-Persona Amazon-Only Profile:")
    for cid in sorted(df[cluster_col].unique()):
        ca = amz_only[amz_only[cluster_col] == cid]
        if len(ca) < 50: continue
        name = persona_names.get(cid, f'C{cid}')

        rates = {}
        for suffix, label in interest_cats.items():
            amz_col = f'amz_{suffix}'
            if amz_col in ca.columns:
                rates[label] = ca[amz_col].mean() * 100

        top3 = sorted(rates.items(), key=lambda x: -x[1])[:3]
        bot2 = sorted(rates.items(), key=lambda x: x[1])[:2]
        print(f"    {name:25s} ({len(ca):,} users)")
        print(f"      Top: {', '.join([f'{k} ({v:.0f}%)' for k, v in top3])}")
        print(f"      Low: {', '.join([f'{k} ({v:.0f}%)' for k, v in bot2])}")

# ============================================================
# STEP 6: Summary + Export
# ============================================================
print("\n" + "=" * 80)
print("SUMMARY: Tiered Commercial Profile per Persona")
print("=" * 80)

summary_rows = []
for cid in sorted(df[cluster_col].unique()):
    c = df[df[cluster_col] == cid]
    n = len(c)
    if n < 10: continue
    name = persona_names.get(cid, f'C{cid}')

    row = {'persona': name, 'users': n}

    # Tier counts
    row['pct_amazon'] = (c['amz_tag_count'] > 0).mean() * 100
    row['pct_ml'] = (c['ml_tag_count'] > 0).mean() * 100
    row['pct_both'] = ((c['amz_tag_count'] > 0) & (c['ml_tag_count'] > 0)).mean() * 100
    row['pct_none'] = ((c['amz_tag_count'] == 0) & (c['ml_tag_count'] == 0)).mean() * 100

    # Amazon profile (high confidence)
    amz_u = c[c['amz_tag_count'] > 0]
    for suffix, label in interest_cats.items():
        amz_col = f'amz_{suffix}'
        row[f'amz_{label}'] = amz_u[amz_col].mean() * 100 if len(amz_u) > 0 and amz_col in amz_u.columns else 0

    # ML profile (medium confidence)
    ml_u = c[c['ml_tag_count'] > 0]
    for suffix, label in interest_cats.items():
        ml_col = f'has_{suffix}'
        row[f'ml_{label}'] = ml_u[ml_col].mean() * 100 if len(ml_u) > 0 and ml_col in ml_u.columns else 0

    summary_rows.append(row)

summary = pd.DataFrame(summary_rows)

# Print compact summary
print(f"\n{'Persona':25s} {'Users':>8s} {'Amz%':>6s} {'ML%':>6s} {'Both%':>6s} {'None%':>6s}")
print('-' * 60)
for _, r in summary.iterrows():
    print(f"{r['persona']:25s} {r['users']:>8,.0f} {r['pct_amazon']:>5.1f}% {r['pct_ml']:>5.1f}% {r['pct_both']:>5.1f}% {r['pct_none']:>5.1f}%")

print(f"\n\nKey Interest Divergences (Amazon vs ML, >5% delta):")
for _, r in summary.iterrows():
    divergences = []
    for suffix, label in interest_cats.items():
        amz_val = r.get(f'amz_{label}', 0)
        ml_val = r.get(f'ml_{label}', 0)
        delta = amz_val - ml_val
        if abs(delta) > 5:
            divergences.append(f"{label}: Amz {amz_val:.0f}% vs ML {ml_val:.0f}% ({delta:+.0f}%)")
    if divergences:
        print(f"  {r['persona']}:")
        for d in divergences:
            print(f"    {d}")

# Export
export_path = os.path.join(OUTPUT_DIR, "amazon_tags_comparison.csv")
summary.to_csv(export_path, index=False)
print(f"\n✅ Exported: {export_path}")

# Also save the enriched df with both tag tiers
df.to_csv(os.path.join(DATA_DIR, "fatafat_personas_tiered_tags.csv"), index=False)
print(f"✅ Exported: fatafat_personas_tiered_tags.csv")

print(f"\n🎯 NEXT: Use these tiered profiles to update persona cards")
print(f"   Amazon tags = high confidence (actual shopping behavior)")
print(f"   ML tags = medium confidence (predicted interests)")
print(f"   Where they diverge = ML model weakness for that segment")
