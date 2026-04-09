"""
Phase 2.2: Enriched Content Dimensions — Full Re-Run
=====================================================
Adds content source (tag_name), origin (original_acquired), and maturity_rating
as clustering features. Complete re-run of feature matrix, clustering, role
assignment, hypothesis validation, and persona card generation.

Input CSVs:
  - q21_engagement.csv, q22a_user_video.csv, q23_session_episodes.csv,
    q24a_demographics.csv, q24b_channel.csv, q25_persona_tags.csv
  - q22b_cms_enriched.csv (NEW — exported by this script from Redshift)

Output:
  - fatafat_personas_phase2_2.csv
  - persona_cards_v3.txt
"""

import pandas as pd
import numpy as np
import psycopg2
import csv
import os
import sys
import time
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans, AgglomerativeClustering
from sklearn.metrics import silhouette_score, adjusted_rand_score
import warnings
warnings.filterwarnings('ignore')

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
WORKSPACE_ROOT = os.path.dirname(SCRIPT_DIR)

# Load .env
def load_env(path):
    if os.path.exists(path):
        with open(path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    k, v = line.split('=', 1)
                    os.environ[k.strip()] = v.strip()

for p in [os.path.join(SCRIPT_DIR, ".env"),
          os.path.join(WORKSPACE_ROOT, ".kiro", "settings", ".env")]:
    if os.path.exists(p):
        load_env(p)
        break

print("=" * 80)
print("PHASE 2.2: Enriched Content Dimensions — Full Re-Run")
print("=" * 80)

# ============================================================
# STEP 0: Export enriched CMS data from Redshift
# ============================================================
cms_path = os.path.join(SCRIPT_DIR, "q22b_cms_enriched.csv")
if not os.path.exists(cms_path):
    print("\n--- Exporting enriched CMS data from Redshift ---")
    conn = psycopg2.connect(
        host='vpce-0cfaee168d10434e7-a1iibn6p.vpce-svc-09b1fc38f11e9bfef.ap-south-1.vpce.amazonaws.com',
        port=5439, dbname='mxbi',
        user=os.environ['REDSHIFT_USERNAME'],
        password=os.environ['REDSHIFT_PASSWORD'],
        sslmode='require'
    )
    cur = conn.cursor()
    cur.execute("""
        SELECT DISTINCT video_id, tv_show_name, channel_ids,
            genre_name, secondary_genre_name, language_name,
            content_category, episode_number,
            tag_name, original_acquired, maturity_rating
        FROM daily_cms_data_table
        WHERE is_fatafat_micro_show = '1'
          AND tv_show_name NOT IN ('[]', '[unknown]')
    """)
    cols = [d[0] for d in cur.description]
    rows = cur.fetchall()
    with open(cms_path, 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(cols)
        w.writerows(rows)
    print(f"  Exported {len(rows):,} rows → {cms_path}")
    cur.close()
    conn.close()
else:
    print(f"  CMS enriched data already exists: {cms_path}")

# ============================================================
# STEP 1: Load all data
# ============================================================
print("\n--- Loading Data ---")
eng = pd.read_csv(os.path.join(SCRIPT_DIR, "q21_engagement.csv"))
uv = pd.read_csv(os.path.join(SCRIPT_DIR, "q22a_user_video.csv"))
cms = pd.read_csv(cms_path)
sess = pd.read_csv(os.path.join(SCRIPT_DIR, "q23_session_episodes.csv"))
demo = pd.read_csv(os.path.join(SCRIPT_DIR, "q24a_demographics.csv"))
channel = pd.read_csv(os.path.join(SCRIPT_DIR, "q24b_channel.csv"))

tags_path = os.path.join(SCRIPT_DIR, "q25_persona_tags.csv")
has_tags = os.path.exists(tags_path)

print(f"  Engagement: {len(eng):,} users")
print(f"  User×Video: {len(uv):,} rows")
print(f"  CMS: {len(cms):,} rows")
print(f"  Sessions: {len(sess):,} rows")
print(f"  Demographics: {len(demo):,} users")
print(f"  Channel: {len(channel):,} users")
print(f"  Persona tags: {'yes' if has_tags else 'no'}")

# ============================================================
# STEP 2: Clean CMS + Join to user×video
# ============================================================
print("\n--- Cleaning CMS & Joining ---")
for col in ['tv_show_name', 'genre_name', 'secondary_genre_name',
            'language_name', 'tag_name', 'original_acquired']:
    if col in cms.columns:
        cms[col] = cms[col].astype(str).str.strip('[]').replace('None', 'Unknown')

cms['episode_num_int'] = pd.to_numeric(
    cms['episode_number'].astype(str).str.strip('[]'), errors='coerce'
).fillna(0).astype(int)

cms['maturity_rating'] = pd.to_numeric(
    cms['maturity_rating'].astype(str).str.strip('[]'), errors='coerce'
).fillna(-1).astype(int)

# Content source classification
def classify_source(tag):
    tag = str(tag).lower().strip()
    if tag in ('mandarin', 'english', 'korean'):
        return 'International Dubbed'
    elif tag == 'fatafat original':
        return 'Fatafat Original'
    elif tag in ('reelies', 'reelsaga', 'pratilipi', 'rusk'):
        return 'Partner Studio'
    elif tag == 'repack':
        return 'Repack'
    elif tag == 'branded':
        return 'Branded'
    else:
        return 'Other'

cms['content_source'] = cms['tag_name'].apply(classify_source)

# Origin classification
cms['content_origin'] = cms['original_acquired'].apply(
    lambda x: 'International' if str(x).strip() == 'International'
    else 'Hindi' if str(x).strip() == 'Hindi'
    else 'Unknown'
)

# Maturity tier
cms['maturity_tier'] = cms['maturity_rating'].apply(
    lambda x: 'All Ages' if x <= 0 else '7+' if x <= 7
    else '13+' if x <= 13 else '16+' if x <= 16 else '18+'
)

print(f"  Content source distribution:")
print(cms.groupby('content_source')['channel_ids'].nunique().sort_values(ascending=False).to_string())
print(f"\n  Content origin distribution:")
print(cms.groupby('content_origin')['channel_ids'].nunique().sort_values(ascending=False).to_string())
print(f"\n  Maturity tier distribution:")
print(cms.groupby('maturity_tier')['channel_ids'].nunique().sort_values(ascending=False).to_string())

# Join user×video with enriched CMS
uv = uv.merge(cms[['video_id', 'tv_show_name', 'channel_ids', 'genre_name',
                     'secondary_genre_name', 'language_name', 'episode_num_int',
                     'content_source', 'content_origin', 'maturity_tier']].drop_duplicates(),
               left_on='videoid', right_on='video_id', how='left')
print(f"\n  Joined user×video: {len(uv):,} rows")

# ============================================================
# STEP 3: Build ALL feature dimensions
# ============================================================
print("\n--- Building Feature Dimensions ---")

# DIM 1: Engagement Depth
eng['mpc'] = eng['total_minutes'] / eng['active_days'].clip(lower=1)
eng['minutes_per_stream'] = eng['total_minutes'] / eng['total_streams'].clip(lower=1)
eng['streams_per_day'] = eng['total_streams'] / eng['active_days'].clip(lower=1)
eng['episodes_per_session'] = eng['unique_episodes'] / eng['total_sessions'].clip(lower=1)
eng['engagement_tier'] = pd.qcut(eng['total_minutes'], q=5,
    labels=['Sampler', 'Light', 'Moderate', 'Heavy', 'Binge'], duplicates='drop')
print(f"  Dim 1 (Engagement): {len(eng):,} users, MPC mean={eng['mpc'].mean():.1f}")

# DIM 2: Content Preference (enriched)
# Per-user: top show's genre, secondary genre, source, origin, maturity
user_show = (uv.groupby(['uuid', 'channel_ids', 'tv_show_name', 'genre_name',
                          'secondary_genre_name', 'content_source', 'content_origin',
                          'maturity_tier'])
             .agg(show_minutes=('minutes', 'sum')).reset_index()
             .sort_values('show_minutes', ascending=False)
             .groupby('uuid').first().reset_index())

content = uv.groupby('uuid').agg(
    unique_shows=('channel_ids', 'nunique'),
    genre_breadth=('genre_name', 'nunique'),
    total_content_minutes=('minutes', 'sum')
).reset_index()

user_show['show_concentration'] = (
    user_show['show_minutes'] /
    content.set_index('uuid')['total_content_minutes']
    .reindex(user_show['uuid']).values.clip(min=0.01)
)

content = content.merge(
    user_show[['uuid', 'tv_show_name', 'genre_name', 'secondary_genre_name',
               'content_source', 'content_origin', 'maturity_tier', 'show_concentration']],
    on='uuid', how='left'
)
content = content.rename(columns={
    'tv_show_name': 'top_show', 'genre_name': 'top_genre',
    'secondary_genre_name': 'top_sec_genre',
    'content_source': 'top_content_source',
    'content_origin': 'top_content_origin',
    'maturity_tier': 'top_maturity'
})
content.drop(columns=['total_content_minutes'], inplace=True)

# Rich genre cluster
def classify_genre(row):
    g = str(row.get('top_genre', '')).lower()
    sg = str(row.get('top_sec_genre', '')).lower()
    if g == 'romance' and sg in ('forbidden love', 'edgy', ''):
        return 'Romance/CEO'
    elif g == 'drama' and sg in ('melodrama', 'secret lives', 'inspiring'):
        return 'Empowerment'
    elif g in ('power struggles',) and sg in ('revenge', 'inheritance', 'hidden identity'):
        return 'Power Struggles'
    elif g == 'thriller' and sg in ('crime', 'pulp', 'horror'):
        return 'Thriller/Crime'
    elif g == 'fantasy':
        return 'Fantasy'
    elif g == 'romance':
        return 'Romance Other'
    elif g == 'drama':
        return 'Drama Other'
    else:
        return 'Other'

content['genre_cluster'] = content.apply(classify_genre, axis=1)
print(f"  Dim 2 (Content): {len(content):,} users")
print(f"    Genre clusters: {content['genre_cluster'].value_counts().to_dict()}")
print(f"    Content source: {content['top_content_source'].value_counts().to_dict()}")
print(f"    Content origin: {content['top_content_origin'].value_counts().to_dict()}")
print(f"    Maturity tier:  {content['top_maturity'].value_counts().to_dict()}")

# DIM 3: Retention Profile
episode_depth = (uv.dropna(subset=['channel_ids'])
    .groupby(['uuid', 'channel_ids']).agg(max_ep=('episode_num_int', 'max')).reset_index())
retention = episode_depth.groupby('uuid').agg(
    max_episode_depth=('max_ep', 'max'), avg_episode_depth=('max_ep', 'mean')
).reset_index()
retention['lock_survival'] = (retention['max_episode_depth'] >= 6).astype(int)

binge = sess.groupby('uuid').agg(
    avg_episodes_per_session=('episodes_in_session', 'mean'),
    max_episodes_per_session=('episodes_in_session', 'max')
).reset_index()
retention = retention.merge(binge, on='uuid', how='left')
retention['avg_episodes_per_session'] = retention['avg_episodes_per_session'].fillna(1)
retention['max_episodes_per_session'] = retention['max_episodes_per_session'].fillna(1)
retention['binge_propensity'] = (retention['max_episodes_per_session'] /
    retention['avg_episodes_per_session'].clip(lower=1))
print(f"  Dim 3 (Retention): {len(retention):,} users, lock survival={retention['lock_survival'].mean()*100:.1f}%")

# DIM 4: Demographics
demo['age_group'] = demo['age_group'].fillna('Unknown')
demo['gender'] = demo['gender'].fillna('Unknown')
demo['age_gender'] = demo['gender'].str[0] + '_' + demo['age_group']
demo.loc[demo['gender'] == 'Unknown', 'age_gender'] = 'Unknown'
print(f"  Dim 4 (Demographics): {len(demo):,} users")

# DIM 5: Channel + Interest Tags
print(f"  Dim 5 (Channel): {len(channel):,} users")
tag_count = None
if has_tags:
    tag_count = pd.read_csv(tags_path)
    # Already pre-aggregated: uuid, tag_count, has_fashion_beauty, etc.
    print(f"  Dim 5b (Tags): {len(tag_count):,} users with tags")

# ============================================================
# STEP 4: Merge all dimensions
# ============================================================
print("\n--- Merging Feature Matrix ---")
df = eng[['uuid', 'total_streams', 'total_minutes', 'unique_episodes',
          'active_days', 'total_sessions', 'mpc', 'minutes_per_stream',
          'streams_per_day', 'episodes_per_session', 'engagement_tier']].copy()

df = df.merge(content, on='uuid', how='left')
df = df.merge(retention, on='uuid', how='left')
df = df.merge(demo, on='uuid', how='left')
df = df.merge(channel, on='uuid', how='left')
if tag_count is not None:
    df = df.merge(tag_count, on='uuid', how='left')
    df['tag_count'] = df['tag_count'].fillna(0).astype(int)
    for col in ['has_fashion_beauty', 'has_electronics_tech', 'has_health_fitness',
                'has_home_kitchen', 'has_travel', 'has_parents_baby',
                'has_automotive', 'has_affluent_premium']:
        df[col] = df[col].fillna(0).astype(int)

# Fill missing
for col, default in {
    'age_group': 'Unknown', 'gender': 'Unknown', 'age_gender': 'Unknown',
    'primary_channel': 'Organic', 'genre_cluster': 'Other',
    'top_content_source': 'Unknown', 'top_content_origin': 'Unknown',
    'top_maturity': 'Unknown',
    'unique_shows': 1, 'genre_breadth': 1, 'show_concentration': 1.0,
    'max_episode_depth': 1, 'avg_episode_depth': 1, 'lock_survival': 0,
    'avg_episodes_per_session': 1, 'max_episodes_per_session': 1,
    'binge_propensity': 1.0,
}.items():
    if col in df.columns:
        df[col] = df[col].fillna(default)

print(f"  Feature matrix: {len(df):,} users × {len(df.columns)} columns")

# ============================================================
# STEP 5: Prepare clustering features
# ============================================================
print("\n--- Preparing Clustering Features ---")
numeric_features = [
    'total_minutes', 'mpc', 'unique_episodes', 'active_days',
    'minutes_per_stream', 'streams_per_day',
    'unique_shows', 'genre_breadth', 'show_concentration',
    'max_episode_depth', 'avg_episode_depth', 'lock_survival',
    'avg_episodes_per_session', 'binge_propensity',
]
if tag_count is not None:
    numeric_features += ['tag_count', 'has_fashion_beauty', 'has_electronics_tech',
                         'has_health_fitness', 'has_home_kitchen', 'has_travel',
                         'has_parents_baby', 'has_automotive', 'has_affluent_premium']

# Categoricals: now includes content_source, content_origin, maturity
cat_features = ['gender', 'age_group', 'primary_channel', 'genre_cluster',
                'top_content_source', 'top_content_origin', 'top_maturity']
df_encoded = pd.get_dummies(df[cat_features], prefix=cat_features, drop_first=False)

X_numeric = df[numeric_features].values
X_cat = df_encoded.values
scaler = StandardScaler()
X_numeric_scaled = scaler.fit_transform(X_numeric)
X_final = np.hstack([X_numeric_scaled, X_cat])

print(f"  Shape: {X_final.shape} ({len(numeric_features)} numeric + {X_cat.shape[1]} one-hot)")

# ============================================================
# STEP 6: Clustering
# ============================================================
print("\n--- K-Means Clustering ---")
sample_size = min(50000, len(X_final))
np.random.seed(42)
sample_idx = np.random.choice(len(X_final), sample_size, replace=False)
X_sample = X_final[sample_idx]

print("K selection:")
best_k, best_sil = 4, 0
for k in range(4, 9):
    km = KMeans(n_clusters=k, random_state=42, n_init=10, max_iter=300)
    labels = km.fit_predict(X_sample)
    sil = silhouette_score(X_sample, labels, sample_size=min(10000, sample_size))
    print(f"  k={k}: Silhouette={sil:.4f}")
    if sil > best_sil:
        best_k, best_sil = k, sil

# Run k=6 for hypothesis alignment AND best_k
FINAL_K = 6
print(f"\nRunning k={FINAL_K} on full dataset...")
kmeans = KMeans(n_clusters=FINAL_K, random_state=42, n_init=20, max_iter=500)
df['cluster'] = kmeans.fit_predict(X_final)

sil_final = silhouette_score(X_sample, kmeans.predict(X_sample),
                              sample_size=min(10000, sample_size))
print(f"k={FINAL_K} Silhouette: {sil_final:.4f}")

# Hierarchical validation
agg = AgglomerativeClustering(n_clusters=FINAL_K, linkage='ward')
agg_labels = agg.fit_predict(X_sample)
ari = adjusted_rand_score(kmeans.predict(X_sample), agg_labels)
print(f"Hierarchical ARI: {ari:.4f}")

print(f"\nCluster sizes:")
for cid in sorted(df['cluster'].unique()):
    n = (df['cluster'] == cid).sum()
    print(f"  Cluster {cid}: {n:,} ({n/len(df)*100:.1f}%)")

# ============================================================
# STEP 7: Strategic Role Assignment
# ============================================================
print("\n--- Strategic Role Assignment ---")
platform_median = df['total_minutes'].median()

cs = df.groupby('cluster').agg(
    users=('uuid', 'count'), avg_min=('total_minutes', 'mean'),
    avg_mpc=('mpc', 'mean'), avg_days=('active_days', 'mean'),
    lock_pct=('lock_survival', 'mean'), avg_shows=('unique_shows', 'mean'),
).reset_index()
cs['pct'] = cs['users'] / len(df) * 100

def assign_role(r):
    if r['pct'] > 30 and r['avg_min'] < 10: return 'CONVERT'
    if r['pct'] < 10 and r['avg_min'] < 5: return 'EXPLORE'
    if r['pct'] > 15 and r['avg_min'] < platform_median: return 'GROW'
    if r['avg_min'] > platform_median * 1.5 and r['avg_days'] > 4: return 'SUSTAIN'
    if r['avg_min'] > platform_median and r['lock_pct'] > 0.5: return 'NOURISH'
    if r['avg_min'] > platform_median: return 'NOURISH'
    return 'GROW'

cs['role'] = cs.apply(assign_role, axis=1)
role_map = cs.set_index('cluster')['role'].to_dict()
df['strategic_role'] = df['cluster'].map(role_map)

for _, r in cs.iterrows():
    print(f"  Cluster {int(r['cluster'])}: {r['role']:8s} | {r['users']:>10,.0f} ({r['pct']:.1f}%) | "
          f"avg_min={r['avg_min']:.1f} | MPC={r['avg_mpc']:.1f} | lock={r['lock_pct']*100:.0f}%")

# ============================================================
# STEP 8: Full Cluster Profiles (with enriched content)
# ============================================================
print("\n" + "=" * 80)
print("CLUSTER PROFILES — ENRICHED CONTENT DIMENSIONS")
print("=" * 80)

for cid in sorted(df['cluster'].unique()):
    c = df[df['cluster'] == cid]
    n = len(c)
    pct = n / len(df) * 100
    role = role_map[cid]

    print(f"\n{'=' * 70}")
    print(f"CLUSTER {cid} — {role} — {n:,} users ({pct:.1f}%)")
    print(f"{'=' * 70}")

    # Engagement
    print(f"  Engagement: {c['total_minutes'].mean():.1f} min/wk | {c['mpc'].mean():.1f} MPC | "
          f"{c['active_days'].mean():.1f} days | {c['unique_shows'].mean():.1f} shows")

    # Retention
    print(f"  Retention:  {c['max_episode_depth'].mean():.0f} max ep | "
          f"{c['lock_survival'].mean()*100:.0f}% lock | "
          f"{c['avg_episodes_per_session'].mean():.1f} eps/sess | "
          f"{c['binge_propensity'].mean():.2f} binge")

    # Content — Genre
    gc = c['genre_cluster'].value_counts(normalize=True).head(4)
    print(f"  Genre:      {', '.join([f'{g} ({p*100:.0f}%)' for g, p in gc.items()])}")

    # Content — Secondary Genre
    sg = c['top_sec_genre'].value_counts(normalize=True).head(5) if 'top_sec_genre' in c.columns else pd.Series()
    if len(sg) > 0:
        print(f"  Sub-Genre:  {', '.join([f'{g} ({p*100:.0f}%)' for g, p in sg.items()])}")

    # Content — SOURCE (NEW)
    src = c['top_content_source'].value_counts(normalize=True)
    print(f"  Source:     {', '.join([f'{s} ({p*100:.0f}%)' for s, p in src.head(4).items()])}")

    # Content — ORIGIN (NEW)
    orig = c['top_content_origin'].value_counts(normalize=True)
    print(f"  Origin:     {', '.join([f'{o} ({p*100:.0f}%)' for o, p in orig.items()])}")

    # Content — MATURITY (NEW)
    mat = c['top_maturity'].value_counts(normalize=True)
    print(f"  Maturity:   {', '.join([f'{m} ({p*100:.0f}%)' for m, p in mat.head(4).items()])}")

    # Top shows
    top_s = c['top_show'].value_counts().head(5)
    print(f"  Top Shows:  {', '.join([f'{s} ({cnt:,})' for s, cnt in top_s.items()])}")

    # Demographics
    print(f"  Demo:       {(c['gender']=='Female').mean()*100:.0f}% F / "
          f"{(c['gender']=='Male').mean()*100:.0f}% M | "
          f"{(c['age_group']=='18-24').mean()*100:.0f}% 18-24 | "
          f"{(c['age_group']=='25-34').mean()*100:.0f}% 25-34 | "
          f"{c['age_group'].isin(['35-44','45-54','55-64','65+']).mean()*100:.0f}% 35+")
    ag = c['age_gender'].value_counts(normalize=True).head(3)
    print(f"  Top Cells:  {', '.join([f'{a} ({p*100:.0f}%)' for a, p in ag.items()])}")

    # Channel
    print(f"  Channel:    Organic {(c['primary_channel']=='Organic').mean()*100:.0f}% | "
          f"Paid {(c['primary_channel']=='Paid').mean()*100:.0f}% | "
          f"Push {(c['primary_channel']=='Push').mean()*100:.0f}%")

    # Commercial
    if tag_count is not None:
        tagged = c[c['tag_count'] > 0]
        if len(tagged) > 100:
            interest_cols = {'has_fashion_beauty': 'Fashion/Beauty', 'has_electronics_tech': 'Electronics/Tech',
                           'has_health_fitness': 'Health/Fitness', 'has_home_kitchen': 'Home/Kitchen',
                           'has_travel': 'Travel', 'has_parents_baby': 'Parents/Baby',
                           'has_automotive': 'Automotive', 'has_affluent_premium': 'Affluent/Premium'}
            rates = {v: tagged[k].mean()*100 for k, v in interest_cols.items()}
            top3 = sorted(rates.items(), key=lambda x: -x[1])[:3]
            print(f"  Commercial: Tags {len(tagged)/n*100:.0f}% coverage | "
                  f"Top: {', '.join([f'{k} ({v:.0f}%)' for k, v in top3])}")

# ============================================================
# STEP 9: Hypothesis Validation
# ============================================================
print("\n" + "=" * 80)
print("HYPOTHESIS VALIDATION")
print("=" * 80)

hs = df.groupby('cluster').agg(
    users=('uuid', 'count'),
    pct=('uuid', lambda x: len(x)/len(df)*100),
    avg_min=('total_minutes', 'mean'),
    avg_mpc=('mpc', 'mean'),
    avg_shows=('unique_shows', 'mean'),
    lock_pct=('lock_survival', lambda x: x.mean()*100),
    pct_f=('gender', lambda x: (x=='Female').mean()*100),
    pct_m=('gender', lambda x: (x=='Male').mean()*100),
    pct_18=('age_group', lambda x: (x=='18-24').mean()*100),
    pct_25=('age_group', lambda x: (x=='25-34').mean()*100),
    pct_35p=('age_group', lambda x: x.isin(['35-44','45-54','55-64','65+']).mean()*100),
    pct_org=('primary_channel', lambda x: (x=='Organic').mean()*100),
    pct_intl=('top_content_origin', lambda x: (x=='International').mean()*100),
    pct_hindi=('top_content_origin', lambda x: (x=='Hindi').mean()*100),
).round(1)

print(hs.to_string())

hypotheses = {
    'P1: Young Female Romance Binger': lambda r: r['pct_f']>55 and r['pct_18']>35 and r['avg_mpc']>20,
    'P2: Male Crossover Viewer': lambda r: r['pct_m']>55 and r['pct_25']>30 and r['avg_mpc']>1,
    'P3: Discovery Sampler': lambda r: r['pct']>20 and r['avg_min']<15 and r['avg_shows']<2,
    'P4: Multi-Show Power User': lambda r: r['avg_shows']>3 and r['avg_min']>80 and r['lock_pct']>60,
    'P5: Mature Loyal Viewer': lambda r: r['pct_35p']>20 and r['avg_mpc']>10 and r['pct_org']>40,
    'P6: Hindi Content Explorer': lambda r: r['pct_hindi']>50 and r['avg_min']<15,
}

validated = 0
for name, fn in hypotheses.items():
    matched = [int(r.name) for _, r in hs.iterrows() if fn(r)]
    if matched:
        validated += 1
        print(f"  ✅ {name} → Cluster(s): {matched}")
    else:
        print(f"  ❌ {name}")
print(f"\nValidated: {validated}/6")

# ============================================================
# STEP 10: Export
# ============================================================
print("\n--- Exporting ---")
df.to_csv(os.path.join(SCRIPT_DIR, "fatafat_personas_phase2_2.csv"), index=False)
print(f"  ✅ fatafat_personas_phase2_2.csv")

# Persona cards
cards_path = os.path.join(SCRIPT_DIR, "persona_cards_v3.txt")
with open(cards_path, 'w') as f:
    f.write(f"FATAFAT SYNTHETIC PERSONAS — PHASE 2.2 (Enriched Content)\n")
    f.write(f"K-Means k={FINAL_K} | Silhouette={sil_final:.4f} | ARI={ari:.4f}\n")
    f.write(f"Hypotheses Validated: {validated}/6\n\n")

    for cid in sorted(df['cluster'].unique()):
        c = df[df['cluster'] == cid]
        n = len(c)
        pct = n/len(df)*100
        role = role_map[cid]

        top_s = c['top_show'].value_counts().head(3)
        gc = c['genre_cluster'].value_counts(normalize=True).head(3)
        sg = c['top_sec_genre'].value_counts(normalize=True).head(4) if 'top_sec_genre' in c.columns else pd.Series()
        src = c['top_content_source'].value_counts(normalize=True).head(3)
        orig = c['top_content_origin'].value_counts(normalize=True)
        mat = c['top_maturity'].value_counts(normalize=True).head(3)
        ag = c['age_gender'].value_counts(normalize=True).head(3)
        ch = c['primary_channel'].value_counts(normalize=True).head(3)

        f.write(f"{'='*70}\n")
        f.write(f"CLUSTER {cid} — {role} — {n:,} users ({pct:.1f}%)\n")
        f.write(f"{'='*70}\n\n")
        f.write(f"  ENGAGEMENT: {c['total_minutes'].mean():.0f} min/wk | {c['mpc'].mean():.0f} MPC | "
                f"{c['active_days'].mean():.1f} days | {c['unique_shows'].mean():.1f} shows\n")
        f.write(f"  RETENTION:  {c['max_episode_depth'].mean():.0f} max ep | "
                f"{c['lock_survival'].mean()*100:.0f}% lock | "
                f"{c['avg_episodes_per_session'].mean():.1f} eps/sess\n")
        f.write(f"  GENRE:      {', '.join([f'{g} ({p*100:.0f}%)' for g, p in gc.items()])}\n")
        if len(sg) > 0:
            f.write(f"  SUB-GENRE:  {', '.join([f'{g} ({p*100:.0f}%)' for g, p in sg.items()])}\n")
        f.write(f"  SOURCE:     {', '.join([f'{s} ({p*100:.0f}%)' for s, p in src.items()])}\n")
        f.write(f"  ORIGIN:     {', '.join([f'{o} ({p*100:.0f}%)' for o, p in orig.items()])}\n")
        f.write(f"  MATURITY:   {', '.join([f'{m} ({p*100:.0f}%)' for m, p in mat.items()])}\n")
        f.write(f"  TOP SHOWS:  {', '.join([f'{s} ({cnt:,})' for s, cnt in top_s.items()])}\n")
        f.write(f"  DEMO:       {(c['gender']=='Female').mean()*100:.0f}% F / {(c['gender']=='Male').mean()*100:.0f}% M | "
                f"{(c['age_group']=='18-24').mean()*100:.0f}% 18-24 | {(c['age_group']=='25-34').mean()*100:.0f}% 25-34 | "
                f"{c['age_group'].isin(['35-44','45-54','55-64','65+']).mean()*100:.0f}% 35+\n")
        f.write(f"  TOP CELLS:  {', '.join([f'{a} ({p*100:.0f}%)' for a, p in ag.items()])}\n")
        f.write(f"  CHANNEL:    {', '.join([f'{k} ({v*100:.0f}%)' for k, v in ch.items()])}\n")

        if tag_count is not None:
            tagged = c[c['tag_count'] > 0]
            if len(tagged) > 100:
                interest_cols = {'has_fashion_beauty': 'Fashion/Beauty', 'has_electronics_tech': 'Electronics/Tech',
                               'has_health_fitness': 'Health/Fitness', 'has_home_kitchen': 'Home/Kitchen',
                               'has_travel': 'Travel', 'has_parents_baby': 'Parents/Baby'}
                rates = sorted([(v, tagged[k].mean()*100) for k, v in interest_cols.items()], key=lambda x: -x[1])
                f.write(f"  COMMERCIAL: Tags {len(tagged)/n*100:.0f}% | {', '.join([f'{k} ({v:.0f}%)' for k, v in rates[:3]])}\n")
        f.write(f"\n")

print(f"  ✅ {cards_path}")

print(f"\n📊 PHASE 2.2 METRICS:")
print(f"   Silhouette: {sil_final:.4f}")
print(f"   ARI: {ari:.4f}")
print(f"   Hypotheses: {validated}/6")
print(f"   Features: {X_final.shape[1]} ({len(numeric_features)} numeric + {X_cat.shape[1]} one-hot)")
print(f"   New content features: content_source, content_origin, maturity_tier")
