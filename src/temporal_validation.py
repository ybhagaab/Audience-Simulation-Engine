"""
Temporal Validation: 3-Period Model Generalization + Content Impact
===================================================================
Tests whether the persona model (trained on P3: Mar 30 - Apr 5) generalizes
to P1 (Feb 3-9) and P2 (Mar 3-9). Also tracks catalog evolution and
content impact between periods.

Part A: Predict P1/P2 cluster assignments using P3 model
Part B: Independent clustering on P1/P2 for true validation
Part C: Catalog evolution and demand shift analysis
"""

import pandas as pd
import numpy as np
import psycopg2
import csv
import os
import sys
import time
import pickle
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans, AgglomerativeClustering
from sklearn.metrics import silhouette_score, adjusted_rand_score
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

PERIODS = {
    'P1_Feb': ('2026-02-03', '2026-02-09'),
    'P2_Mar': ('2026-03-03', '2026-03-09'),
}
P3_DATES = ('2026-03-30', '2026-04-05')

print("=" * 80)
print("TEMPORAL VALIDATION: 3-Period Analysis")
print("=" * 80)

# ============================================================
# STEP 1: Export data for P1 and P2
# ============================================================
BASE_FILTER = """
    event = 'onlineStreamEnd'
    AND CAST(playtime AS FLOAT) >= 3000
    AND networkType IS NOT NULL
    AND internalNetworkStatus > 1
    AND pagetype = 'titlePage'
"""

def export_period(conn, period_name, start_date, end_date):
    """Export engagement + channel data for a period. Returns user count."""
    date_filter = f"DATE(start_date) BETWEEN '{start_date}' AND '{end_date}'"
    prefix = os.path.join(DATA_DIR, f"tv_{period_name}")

    # Q2.1: Engagement
    eng_path = f"{prefix}_engagement.csv"
    if not os.path.exists(eng_path):
        print(f"  Exporting {period_name} engagement...", flush=True)
        cur = conn.cursor()
        cur.execute(f"""
            SELECT uuid,
                COUNT(*) as total_streams,
                ROUND(SUM(CAST(playtime AS FLOAT))/60000, 2) as total_minutes,
                COUNT(DISTINCT videoid) as unique_episodes,
                COUNT(DISTINCT DATE(start_date)) as active_days,
                COUNT(DISTINCT sid) as total_sessions
            FROM fatafat.mxp_fatafat_player_engagement
            WHERE {date_filter} AND {BASE_FILTER}
            GROUP BY uuid
        """)
        cols = [d[0] for d in cur.description]
        rows = cur.fetchall()
        with open(eng_path, 'w', newline='') as f:
            w = csv.writer(f); w.writerow(cols); w.writerows(rows)
        print(f"    {len(rows):,} users → {eng_path}")
        cur.close()
    else:
        rows = sum(1 for _ in open(eng_path)) - 1
        print(f"  {period_name} engagement exists: {rows:,} users")

    # Q2.4a: Demographics
    demo_path = f"{prefix}_demographics.csv"
    if not os.path.exists(demo_path):
        print(f"  Exporting {period_name} demographics...", flush=True)
        cur = conn.cursor()
        cur.execute(f"""
            WITH streamers AS (
                SELECT DISTINCT uuid FROM fatafat.mxp_fatafat_player_engagement
                WHERE {date_filter} AND {BASE_FILTER}
            )
            SELECT s.uuid, COALESCE(d.age_group, 'Unknown') as age_group,
                   COALESCE(d.gender, 'Unknown') as gender
            FROM streamers s
            LEFT JOIN mxp_age_gender_details_table_v3 d ON s.uuid = d.uuid
        """)
        cols = [d[0] for d in cur.description]
        rows = cur.fetchall()
        with open(demo_path, 'w', newline='') as f:
            w = csv.writer(f); w.writerow(cols); w.writerows(rows)
        print(f"    {len(rows):,} users → {demo_path}")
        cur.close()

    # Q2.4b: Channel
    ch_path = f"{prefix}_channel.csv"
    if not os.path.exists(ch_path):
        print(f"  Exporting {period_name} channel...", flush=True)
        cur = conn.cursor()
        cur.execute(f"""
            WITH cw AS (
                SELECT uuid,
                    CASE
                        WHEN dputmsource IN ('perf_m','perf_g','fatafat_inmobi','fatafat_aff_affle',
                            'fatafat_aff_inmobi','fatafat_aff_xiaomi','perf_xiaomi',
                            'fatafat_aff_affinity','aff_affle','perf_inmobi','perf_affle',
                            'perf_aff','branding_meta','branding_META','branding_YT',
                            'branding_publisher','google_web','perf_u','perf_fb','perf_samsung',
                            'perf_oppo','perf_vivo','perf_realme','perf_tiktok','perf_snap',
                            'perf_twitter','perf_dv360','perf_moloco','perf_mintegral','perf_unity',
                            'perf_applovin','perf_ironsource','perf_liftoff','perf_digital_turbine',
                            'perf_aura','perf_adjoe','perf_chartboost','perf_pangle','perf_bigo',
                            'perf_kwai','perf_glance','perf_taboola') THEN 'Paid'
                        WHEN dputmsource = 'mx_internal_notif' THEN 'Push'
                        WHEN dputmsource IN ('personal-ott-toast-v3','personal-ott-toast-v4',
                            'personal-ott-toast-v5','ott_nudges') THEN 'OTT Notification'
                        WHEN dputmsource IN ('paid_int-con-perf-dfp_mx_internal-app',
                            'house_int-con-perf-dfp_mx_internal-app') THEN 'Internal Ad'
                        WHEN dputmsource IS NULL OR dputmsource = '' THEN 'Organic'
                        ELSE 'Other'
                    END as channel_category,
                    SUM(CAST(playtime AS FLOAT)) as total_playtime
                FROM fatafat.mxp_fatafat_player_engagement
                WHERE {date_filter} AND {BASE_FILTER}
                GROUP BY uuid, channel_category
            ),
            ranked AS (
                SELECT uuid, channel_category as primary_channel,
                    ROW_NUMBER() OVER (PARTITION BY uuid ORDER BY total_playtime DESC) as rn
                FROM cw
            )
            SELECT uuid, primary_channel FROM ranked WHERE rn = 1
        """)
        cols = [d[0] for d in cur.description]
        rows = cur.fetchall()
        with open(ch_path, 'w', newline='') as f:
            w = csv.writer(f); w.writerow(cols); w.writerows(rows)
        print(f"    {len(rows):,} users → {ch_path}")
        cur.close()

    # Q2.2a: User×Video (large — skip if exists)
    uv_path = f"{prefix}_user_video.csv"
    if not os.path.exists(uv_path):
        print(f"  Exporting {period_name} user×video (large)...", flush=True)
        t0 = time.time()
        cur = conn.cursor()
        cur.execute(f"""
            SELECT uuid, videoid,
                COUNT(*) as streams,
                ROUND(SUM(CAST(playtime AS FLOAT))/60000, 2) as minutes
            FROM fatafat.mxp_fatafat_player_engagement
            WHERE {date_filter} AND {BASE_FILTER}
            GROUP BY uuid, videoid
        """)
        cols = [d[0] for d in cur.description]
        row_count = 0
        with open(uv_path, 'w', newline='') as f:
            w = csv.writer(f); w.writerow(cols)
            while True:
                batch = cur.fetchmany(10000)
                if not batch: break
                w.writerows(batch)
                row_count += len(batch)
                if row_count % 500000 == 0:
                    print(f"    {row_count:,} rows...", flush=True)
        print(f"    {row_count:,} rows in {time.time()-t0:.0f}s → {uv_path}")
        cur.close()

    # Q2.3: Session episodes
    sess_path = f"{prefix}_sessions.csv"
    if not os.path.exists(sess_path):
        print(f"  Exporting {period_name} sessions...", flush=True)
        cur = conn.cursor()
        cur.execute(f"""
            SELECT uuid, sid, COUNT(DISTINCT videoid) as episodes_in_session
            FROM fatafat.mxp_fatafat_player_engagement
            WHERE {date_filter} AND {BASE_FILTER}
            GROUP BY uuid, sid
        """)
        cols = [d[0] for d in cur.description]
        rows = cur.fetchall()
        with open(sess_path, 'w', newline='') as f:
            w = csv.writer(f); w.writerow(cols); w.writerows(rows)
        print(f"    {len(rows):,} rows → {sess_path}")
        cur.close()

print("\n--- Exporting P1 and P2 data ---")
conn = psycopg2.connect(
    host='vpce-0cfaee168d10434e7-a1iibn6p.vpce-svc-09b1fc38f11e9bfef.ap-south-1.vpce.amazonaws.com',
    port=5439, dbname='mxbi',
    user=os.environ['REDSHIFT_USERNAME'],
    password=os.environ['REDSHIFT_PASSWORD'],
    sslmode='require'
)
conn.autocommit = True

for pname, (start, end) in PERIODS.items():
    print(f"\n  === {pname}: {start} to {end} ===")
    export_period(conn, pname, start, end)

conn.close()
print("\n  All exports complete.")

# ============================================================
# STEP 2: Build feature matrices for P1 and P2
# ============================================================
def build_features(period_name):
    """Build the same feature matrix as P3 for a given period."""
    prefix = os.path.join(DATA_DIR, f"tv_{period_name}")
    cms = pd.read_csv(os.path.join(DATA_DIR, "q22b_cms_enriched.csv"))

    # Clean CMS
    for col in ['tv_show_name', 'genre_name', 'secondary_genre_name', 'tag_name', 'original_acquired']:
        if col in cms.columns:
            cms[col] = cms[col].astype(str).str.strip('[]').replace({'None': 'Unknown', 'nan': 'Unknown', '': 'Unknown'})
    cms['episode_num_int'] = pd.to_numeric(cms['episode_number'].astype(str).str.strip('[]'), errors='coerce').fillna(0).astype(int)

    def src(t):
        t = str(t).lower().strip()
        if t in ('mandarin', 'english', 'korean'): return 'Intl Dubbed'
        if t == 'fatafat original': return 'Original'
        if t in ('reelies', 'reelsaga', 'pratilipi', 'rusk'): return 'Partner'
        if t == 'repack': return 'Repack'
        return 'Other'
    cms['content_source'] = cms['tag_name'].apply(src)
    cms['content_origin'] = cms['original_acquired'].apply(
        lambda x: 'International' if x == 'International' else 'Hindi' if x == 'Hindi' else 'Unknown')

    def classify_genre(row):
        g = str(row.get('genre_name', '')).lower()
        sg = str(row.get('secondary_genre_name', '')).lower()
        if g == 'romance' and sg in ('forbidden love', 'edgy', 'unknown', ''): return 'Romance/CEO'
        elif g == 'drama' and sg in ('melodrama', 'secret lives', 'inspiring'): return 'Empowerment'
        elif g == 'power struggles': return 'Power Struggles'
        elif g == 'thriller': return 'Thriller/Crime'
        elif g == 'fantasy': return 'Fantasy'
        elif g == 'romance': return 'Romance Other'
        elif g == 'drama': return 'Drama Other'
        else: return 'Other'

    # Load period data
    eng = pd.read_csv(f"{prefix}_engagement.csv")
    uv = pd.read_csv(f"{prefix}_user_video.csv")
    sess = pd.read_csv(f"{prefix}_sessions.csv")
    demo = pd.read_csv(f"{prefix}_demographics.csv")
    channel = pd.read_csv(f"{prefix}_channel.csv")

    # Engagement features
    eng['mpc'] = eng['total_minutes'] / eng['active_days'].clip(lower=1)
    eng['minutes_per_stream'] = eng['total_minutes'] / eng['total_streams'].clip(lower=1)
    eng['streams_per_day'] = eng['total_streams'] / eng['active_days'].clip(lower=1)
    eng['episodes_per_session'] = eng['unique_episodes'] / eng['total_sessions'].clip(lower=1)

    # Content features
    uv = uv.merge(cms[['video_id', 'channel_ids', 'genre_name', 'secondary_genre_name',
                         'content_source', 'content_origin', 'episode_num_int']].drop_duplicates(),
                   left_on='videoid', right_on='video_id', how='left')

    user_show = (uv.groupby(['uuid', 'channel_ids', 'genre_name', 'secondary_genre_name',
                              'content_source', 'content_origin'])
                 .agg(show_min=('minutes', 'sum')).reset_index()
                 .sort_values('show_min', ascending=False)
                 .groupby('uuid').first().reset_index())

    content = uv.groupby('uuid').agg(
        unique_shows=('channel_ids', 'nunique'),
        genre_breadth=('genre_name', 'nunique'),
        total_min=('minutes', 'sum')).reset_index()

    user_show['show_concentration'] = (user_show['show_min'] /
        content.set_index('uuid')['total_min'].reindex(user_show['uuid']).values.clip(min=0.01))

    content = content.merge(user_show[['uuid', 'genre_name', 'secondary_genre_name',
                                        'content_source', 'content_origin', 'show_concentration']],
                            on='uuid', how='left')

    content['genre_cluster'] = content.apply(
        lambda r: classify_genre({'genre_name': r.get('genre_name', ''),
                                   'secondary_genre_name': r.get('secondary_genre_name', '')}), axis=1)
    content.drop(columns=['total_min'], inplace=True)

    # Retention
    ep_depth = (uv.dropna(subset=['channel_ids'])
        .groupby(['uuid', 'channel_ids']).agg(max_ep=('episode_num_int', 'max')).reset_index())
    retention = ep_depth.groupby('uuid').agg(
        max_episode_depth=('max_ep', 'max'), avg_episode_depth=('max_ep', 'mean')).reset_index()
    retention['lock_survival'] = (retention['max_episode_depth'] >= 6).astype(int)
    binge = sess.groupby('uuid').agg(
        avg_eps_sess=('episodes_in_session', 'mean'),
        max_eps_sess=('episodes_in_session', 'max')).reset_index()
    retention = retention.merge(binge, on='uuid', how='left')
    retention['avg_eps_sess'] = retention['avg_eps_sess'].fillna(1)
    retention['max_eps_sess'] = retention['max_eps_sess'].fillna(1)
    retention['binge_propensity'] = retention['max_eps_sess'] / retention['avg_eps_sess'].clip(lower=1)

    # Demographics
    demo['age_group'] = demo['age_group'].fillna('Unknown')
    demo['gender'] = demo['gender'].fillna('Unknown')

    # Merge all
    df = eng[['uuid', 'total_streams', 'total_minutes', 'unique_episodes',
              'active_days', 'total_sessions', 'mpc', 'minutes_per_stream',
              'streams_per_day', 'episodes_per_session']].copy()
    df = df.merge(content, on='uuid', how='left')
    df = df.merge(retention, on='uuid', how='left')
    df = df.merge(demo, on='uuid', how='left')
    df = df.merge(channel, on='uuid', how='left')

    # Fill missing
    for col, val in {'age_group': 'Unknown', 'gender': 'Unknown',
                      'primary_channel': 'Organic', 'genre_cluster': 'Other',
                      'content_source': 'Unknown', 'content_origin': 'Unknown',
                      'unique_shows': 1, 'genre_breadth': 1, 'show_concentration': 1.0,
                      'max_episode_depth': 1, 'avg_episode_depth': 1, 'lock_survival': 0,
                      'avg_eps_sess': 1, 'max_eps_sess': 1, 'binge_propensity': 1.0}.items():
        if col in df.columns:
            df[col] = df[col].fillna(val)

    # Secondary genre for demand analysis
    df['top_sec_genre'] = df['secondary_genre_name'].fillna('Unknown') if 'secondary_genre_name' in df.columns else 'Unknown'

    return df, uv

print("\n--- Building feature matrices ---")
period_data = {}
period_uv = {}
for pname in PERIODS:
    print(f"\n  Building {pname}...")
    df, uv = build_features(pname)
    period_data[pname] = df
    period_uv[pname] = uv
    print(f"    {len(df):,} users × {len(df.columns)} columns")

# Also load P3 data
print(f"\n  Loading P3 (current)...")
p3 = pd.read_csv(os.path.join(DATA_DIR, "fatafat_personas_phase2_2.csv"))
cluster_col = 'cluster' if 'cluster' in p3.columns else 'cluster_v2'
print(f"    {len(p3):,} users")

# ============================================================
# STEP 3: Part A — Predict using P3 model
# ============================================================
print("\n" + "=" * 80)
print("PART A: Model Generalization (Predict P1/P2 using P3 model)")
print("=" * 80)

# Rebuild P3 model from P3 data
numeric_features = [
    'total_minutes', 'mpc', 'unique_episodes', 'active_days',
    'minutes_per_stream', 'streams_per_day',
    'unique_shows', 'genre_breadth', 'show_concentration',
    'max_episode_depth', 'avg_episode_depth', 'lock_survival',
    'avg_eps_sess', 'binge_propensity',
]
# Add tag features if available
tag_cols = [c for c in p3.columns if c.startswith('has_') or c == 'tag_count']
numeric_features += [c for c in tag_cols if c in p3.columns]

cat_features = ['gender', 'age_group', 'primary_channel', 'genre_cluster',
                'content_source', 'content_origin']
# Only use cat features that exist in P3
cat_features = [c for c in cat_features if c in p3.columns]

# Fit scaler and encoder on P3
p3_enc = pd.get_dummies(p3[cat_features], prefix=cat_features, drop_first=False)
p3_num = p3[[c for c in numeric_features if c in p3.columns]].fillna(0).values
scaler = StandardScaler()
p3_num_s = scaler.fit_transform(p3_num)
p3_X = np.hstack([p3_num_s, p3_enc.values])

# Train K-Means on P3
kmeans_p3 = KMeans(n_clusters=6, random_state=42, n_init=20, max_iter=500)
kmeans_p3.fit(p3_X)

# Predict for P1 and P2
persona_names = {0: 'Discovery Sampler', 1: 'Romance Binger', 2: 'Platform Devotee',
                 3: 'Male Crossover', 5: 'Engaged Explorer'}

for pname, df in period_data.items():
    print(f"\n  --- {pname} ---")

    # Build same feature matrix — align to P3 numeric features
    for c in numeric_features:
        if c not in df.columns:
            df[c] = 0
    df_num = df[numeric_features].fillna(0).values

    # Ensure same number of features as P3
    if df_num.shape[1] != p3_num.shape[1]:
        print(f"  ⚠ Feature mismatch: P3 has {p3_num.shape[1]}, {pname} has {df_num.shape[1]}. Aligning...")
        common_num = [c for c in numeric_features if c in df.columns and c in p3.columns]
        df_num = df[common_num].fillna(0).values
        p3_num_aligned = p3[common_num].fillna(0).values
        scaler_aligned = StandardScaler()
        scaler_aligned.fit(p3_num_aligned)
        df_num_s = scaler_aligned.transform(df_num)
    else:
        df_num_s = scaler.transform(df_num)

    df_enc = pd.get_dummies(df[cat_features], prefix=cat_features, drop_first=False)
    for col in p3_enc.columns:
        if col not in df_enc.columns:
            df_enc[col] = 0
    df_enc = df_enc[p3_enc.columns]

    df_X = np.hstack([df_num_s, df_enc.values])
    df_X = np.hstack([df_num_s, df_enc.values])

    # Predict
    df['predicted_cluster'] = kmeans_p3.predict(df_X)

    # Distribution
    print(f"  Predicted persona distribution:")
    for cid in sorted(df['predicted_cluster'].unique()):
        n = (df['predicted_cluster'] == cid).sum()
        pct = n / len(df) * 100
        name = persona_names.get(cid, f'C{cid}')
        print(f"    {name:25s}: {n:>10,} ({pct:.1f}%)")

    # Per-persona metrics
    print(f"\n  Per-persona engagement (predicted):")
    for cid in sorted(df['predicted_cluster'].unique()):
        c = df[df['predicted_cluster'] == cid]
        if len(c) < 10: continue
        name = persona_names.get(cid, f'C{cid}')
        print(f"    {name:25s}: min={c['total_minutes'].mean():.1f}, "
              f"MPC={c['mpc'].mean():.1f}, "
              f"lock={c['lock_survival'].mean()*100:.0f}%, "
              f"shows={c['unique_shows'].mean():.1f}, "
              f"F={((c['gender']=='Female').mean()*100):.0f}%")

    period_data[pname] = df

# ============================================================
# STEP 4: Part B — Independent clustering for true validation
# ============================================================
print("\n" + "=" * 80)
print("PART B: True Validation (Independent Clustering)")
print("=" * 80)

for pname, df in period_data.items():
    print(f"\n  --- {pname}: Independent Clustering ---")

    num_cols = [c for c in numeric_features if c in df.columns]
    for c in numeric_features:
        if c not in df.columns:
            df[c] = 0

    df_enc_b = pd.get_dummies(df[cat_features], prefix=cat_features, drop_first=False)
    for col in p3_enc.columns:
        if col not in df_enc_b.columns:
            df_enc_b[col] = 0
    df_enc_b = df_enc_b[p3_enc.columns]

    # Use only common numeric features for local clustering too
    common_num = [c for c in numeric_features if c in df.columns]
    df_num_b = df[common_num].fillna(0).values
    local_scaler = StandardScaler()
    df_num_s = local_scaler.fit_transform(df_num_b)
    df_X_local = np.hstack([df_num_s, df_enc_b.values])

    # Test k=4 to k=8
    N = min(50000, len(df_X_local))
    np.random.seed(42)
    idx = np.random.choice(len(df_X_local), N, replace=False)
    Xs = df_X_local[idx]

    print(f"  K selection:")
    best_k, best_sil = 4, 0
    for k in range(4, 9):
        km = KMeans(n_clusters=k, random_state=42, n_init=10, max_iter=300)
        lb = km.fit_predict(Xs)
        s = silhouette_score(Xs, lb, sample_size=min(10000, N))
        print(f"    k={k}: Sil={s:.4f}")
        if s > best_sil:
            best_k, best_sil = k, s

    print(f"  Best k: {best_k} (Sil={best_sil:.4f})")

    # Run best k on full data
    km_local = KMeans(n_clusters=best_k, random_state=42, n_init=20, max_iter=500)
    df['actual_cluster'] = km_local.fit_predict(df_X_local)

    # ARI between predicted (P3 model) and actual (local clustering)
    ari = adjusted_rand_score(df['predicted_cluster'], df['actual_cluster'])
    print(f"  ARI (predicted vs actual): {ari:.4f}")
    if ari > 0.5:
        print(f"  → GOOD: P3 model generalizes well to {pname}")
    elif ari > 0.3:
        print(f"  → MODERATE: Some structural similarity")
    else:
        print(f"  → LOW: P3 model doesn't generalize well — period has different structure")

    # Actual cluster distribution
    print(f"\n  Actual cluster distribution (independent):")
    for cid in sorted(df['actual_cluster'].unique()):
        c = df[df['actual_cluster'] == cid]
        print(f"    C{cid}: {len(c):>10,} ({len(c)/len(df)*100:.1f}%) | "
              f"min={c['total_minutes'].mean():.1f} | "
              f"lock={c['lock_survival'].mean()*100:.0f}% | "
              f"F={((c['gender']=='Female').mean()*100):.0f}%")

    period_data[pname] = df

# ============================================================
# STEP 5: Part C — Catalog Evolution & Content Impact
# ============================================================
print("\n" + "=" * 80)
print("PART C: Catalog Evolution & Content Impact")
print("=" * 80)

# Load CMS with golive dates
cms = pd.read_csv(os.path.join(DATA_DIR, "q22b_cms_enriched.csv"))
for col in ['tv_show_name', 'genre_name', 'secondary_genre_name', 'tag_name', 'original_acquired']:
    if col in cms.columns:
        cms[col] = cms[col].astype(str).str.strip('[]').replace({'None': 'Unknown', 'nan': 'Unknown', '': 'Unknown'})

cms['sec_genre'] = cms['secondary_genre_name'].apply(
    lambda x: x if x in ['Edgy', 'Forbidden Love', 'Secret Lives', 'Revenge', 'Second Chances',
                          'Melodrama', 'Inheritance', 'Crime', 'Pulp', 'Inspiring',
                          'Hidden Identity', 'Time Travel', 'Horror', 'Mythical Action'] else 'Other')

# Demand distribution per period (secondary genre by watchtime)
print("\n  --- Demand Distribution by Period ---")
all_periods = {**PERIODS, 'P3_Apr': P3_DATES}

demand_data = []
for pname in ['P1_Feb', 'P2_Mar']:
    uv = period_uv[pname]
    uv_with_genre = uv.merge(cms[['video_id', 'sec_genre']].drop_duplicates(),
                              left_on='videoid', right_on='video_id', how='left')
    uv_with_genre['sec_genre'] = uv_with_genre['sec_genre'].fillna('Other')
    demand = uv_with_genre.groupby('sec_genre')['minutes'].sum()
    demand_pct = (demand / demand.sum() * 100).round(1)
    for sg, pct in demand_pct.items():
        demand_data.append({'period': pname, 'sec_genre': sg, 'demand_pct': pct})

# P3 demand (from existing data)
p3_uv = pd.read_csv(os.path.join(DATA_DIR, "q22a_user_video.csv"))
p3_uv_g = p3_uv.merge(cms[['video_id', 'sec_genre']].drop_duplicates(),
                        left_on='videoid', right_on='video_id', how='left')
p3_uv_g['sec_genre'] = p3_uv_g['sec_genre'].fillna('Other')
p3_demand = p3_uv_g.groupby('sec_genre')['minutes'].sum()
p3_demand_pct = (p3_demand / p3_demand.sum() * 100).round(1)
for sg, pct in p3_demand_pct.items():
    demand_data.append({'period': 'P3_Apr', 'sec_genre': sg, 'demand_pct': pct})

demand_df = pd.DataFrame(demand_data)
demand_pivot = demand_df.pivot_table(index='sec_genre', columns='period', values='demand_pct', fill_value=0)
demand_pivot = demand_pivot[['P1_Feb', 'P2_Mar', 'P3_Apr']].sort_values('P3_Apr', ascending=False)

print("\n  Secondary Genre Demand (% of watchtime) by Period:")
print(f"  {'Genre':20s} {'P1 Feb':>8s} {'P2 Mar':>8s} {'P3 Apr':>8s} {'Trend':>10s}")
print(f"  {'-'*55}")
for sg, row in demand_pivot.iterrows():
    trend = row['P3_Apr'] - row['P1_Feb']
    arrow = '↑' if trend > 1 else '↓' if trend < -1 else '→'
    print(f"  {sg:20s} {row['P1_Feb']:>7.1f}% {row['P2_Mar']:>7.1f}% {row['P3_Apr']:>7.1f}% {arrow} {trend:>+.1f}%")

# Persona size comparison
print("\n  --- Persona Size Comparison ---")
print(f"  {'Persona':25s} {'P1 Feb':>10s} {'P2 Mar':>10s} {'P3 Apr':>10s}")
print(f"  {'-'*60}")
for cid in sorted(persona_names.keys()):
    name = persona_names[cid]
    p1_n = (period_data['P1_Feb']['predicted_cluster'] == cid).sum() if 'P1_Feb' in period_data else 0
    p2_n = (period_data['P2_Mar']['predicted_cluster'] == cid).sum() if 'P2_Mar' in period_data else 0
    p3_n = (p3[cluster_col] == cid).sum()
    p1_pct = p1_n / len(period_data.get('P1_Feb', pd.DataFrame())) * 100 if p1_n > 0 else 0
    p2_pct = p2_n / len(period_data.get('P2_Mar', pd.DataFrame())) * 100 if p2_n > 0 else 0
    p3_pct = p3_n / len(p3) * 100
    print(f"  {name:25s} {p1_pct:>9.1f}% {p2_pct:>9.1f}% {p3_pct:>9.1f}%")

# ============================================================
# STEP 6: Export results
# ============================================================
print("\n" + "=" * 80)
print("EXPORT")
print("=" * 80)

# Period comparison CSV
comparison_rows = []
for pname in ['P1_Feb', 'P2_Mar', 'P3_Apr']:
    if pname == 'P3_Apr':
        df = p3
        df['predicted_cluster'] = df[cluster_col]
    else:
        df = period_data[pname]

    for cid in sorted(persona_names.keys()):
        c = df[df['predicted_cluster'] == cid]
        if len(c) < 10: continue
        comparison_rows.append({
            'period': pname, 'cluster': cid, 'persona': persona_names[cid],
            'users': len(c), 'pct': round(len(c)/len(df)*100, 1),
            'avg_minutes': round(c['total_minutes'].mean(), 1),
            'avg_mpc': round(c['mpc'].mean(), 1) if 'mpc' in c.columns else 0,
            'lock_survival': round(c['lock_survival'].mean()*100, 1) if 'lock_survival' in c.columns else 0,
            'avg_shows': round(c['unique_shows'].mean(), 1) if 'unique_shows' in c.columns else 0,
            'pct_female': round((c['gender']=='Female').mean()*100, 1) if 'gender' in c.columns else 0,
        })

comp_df = pd.DataFrame(comparison_rows)
comp_path = os.path.join(OUTPUT_DIR, "temporal_period_comparison.csv")
comp_df.to_csv(comp_path, index=False)
print(f"  ✅ {comp_path}")

# Demand trends CSV
demand_path = os.path.join(OUTPUT_DIR, "temporal_demand_trends.csv")
demand_pivot.to_csv(demand_path)
print(f"  ✅ {demand_path}")

print(f"\n📊 TEMPORAL VALIDATION COMPLETE")
print(f"   P1 Feb: {len(period_data.get('P1_Feb', [])):,} users")
print(f"   P2 Mar: {len(period_data.get('P2_Mar', [])):,} users")
print(f"   P3 Apr: {len(p3):,} users")
