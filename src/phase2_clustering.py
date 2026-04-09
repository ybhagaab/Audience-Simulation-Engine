"""
Fatafat Synthetic Personas — Phase 2: Full 5-Dimension Clustering Pipeline
===========================================================================
Prerequisites: pip install pandas numpy scikit-learn scipy

Input CSVs (exported from phase2_queries.sql):
  1. q21_engagement.csv       — Q2.1 (uuid, total_streams, total_minutes, ...)
  2. q22a_user_video.csv      — Q2.2a (uuid, videoid, streams, minutes)
  3. q22b_cms_lookup.csv      — Q2.2b (video_id, tv_show_name, channel_ids,
                                 genre_name, secondary_genre_name, language_name,
                                 content_category, episode_number)
  4. q23_session_episodes.csv — Q2.3 (uuid, sid, episodes_in_session)
  5. q24a_demographics.csv    — Q2.4a (uuid, age_group, gender)
  6. q24b_channel.csv         — Q2.4b (uuid, primary_channel)
  7. q25_persona_tags.csv     — Q2.5 (uuid, persona_name) [OPTIONAL]

Output:
  - fatafat_personas_phase2.csv  — full feature matrix with cluster assignments
  - persona_cards.txt            — formatted persona cards for stakeholder review
"""

import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans, AgglomerativeClustering
from sklearn.metrics import silhouette_score, adjusted_rand_score
from scipy.cluster.hierarchy import dendrogram, linkage
import warnings
warnings.filterwarnings('ignore')

# ============================================================
# CONFIG
# ============================================================
ENGAGEMENT_CSV       = "q21_engagement.csv"
USER_VIDEO_CSV       = "q22a_user_video.csv"
CMS_LOOKUP_CSV       = "q22b_cms_lookup.csv"
SESSION_EPISODES_CSV = "q23_session_episodes.csv"
DEMOGRAPHICS_CSV     = "q24a_demographics.csv"
CHANNEL_CSV          = "q24b_channel.csv"
PERSONA_TAGS_CSV     = "q25_persona_tags.csv"   # Set to None to skip
USE_PERSONA_TAGS     = False  # Set True once q25 CSV is available

print("=" * 80)
print("PHASE 2: Full 5-Dimension Feature Matrix + Clustering")
print("=" * 80)

# ============================================================
# DIMENSION 1: Engagement Depth
# ============================================================
print("\n--- Dimension 1: Engagement Depth ---")
eng = pd.read_csv(ENGAGEMENT_CSV)
print(f"Loaded {len(eng):,} users from engagement data")

# Derived features
eng['mpc'] = eng['total_minutes'] / eng['active_days'].clip(lower=1)
eng['minutes_per_stream'] = eng['total_minutes'] / eng['total_streams'].clip(lower=1)
eng['streams_per_day'] = eng['total_streams'] / eng['active_days'].clip(lower=1)
eng['episodes_per_session'] = eng['unique_episodes'] / eng['total_sessions'].clip(lower=1)

# Engagement tier (quintiles)
eng['engagement_tier'] = pd.qcut(
    eng['total_minutes'], q=5,
    labels=['Sampler', 'Light', 'Moderate', 'Heavy', 'Binge'],
    duplicates='drop'
)
print(f"MPC: mean={eng['mpc'].mean():.1f}, median={eng['mpc'].median():.1f}")
print(f"Engagement Tier Distribution:\n{eng['engagement_tier'].value_counts().sort_index()}")

# ============================================================
# DIMENSION 2: Content Preference
# ============================================================
print("\n--- Dimension 2: Content Preference ---")
uv = pd.read_csv(USER_VIDEO_CSV)
cms = pd.read_csv(CMS_LOOKUP_CSV)

# Clean CMS bracket-wrapped values: [Romance] -> Romance
for col in ['tv_show_name', 'genre_name', 'secondary_genre_name', 'language_name']:
    if col in cms.columns:
        cms[col] = cms[col].astype(str).str.strip('[]')

# Cast episode_number to int (varchar in Redshift)
cms['episode_num_int'] = pd.to_numeric(
    cms['episode_number'].astype(str).str.strip('[]'),
    errors='coerce'
).fillna(0).astype(int)

# Join user×video with CMS metadata
uv = uv.merge(cms, left_on='videoid', right_on='video_id', how='left')

# --- Per-user content features ---
content_features = uv.groupby('uuid').agg(
    unique_shows=('channel_ids', 'nunique'),
    genre_breadth=('genre_name', 'nunique'),
    total_content_minutes=('minutes', 'sum')
).reset_index()

# Top show per user (by watchtime)
top_shows = (
    uv.groupby(['uuid', 'channel_ids', 'tv_show_name', 'genre_name',
                 'secondary_genre_name', 'language_name'])
    .agg(show_minutes=('minutes', 'sum'))
    .reset_index()
    .sort_values('show_minutes', ascending=False)
    .groupby('uuid').first().reset_index()
)
top_shows = top_shows.rename(columns={
    'tv_show_name': 'top_show',
    'genre_name': 'top_genre',
    'secondary_genre_name': 'top_secondary_genre',
    'language_name': 'top_language'
})
top_shows['show_concentration'] = (
    top_shows['show_minutes'] /
    content_features.set_index('uuid')['total_content_minutes']
    .reindex(top_shows['uuid']).values.clip(min=0.01)
)

content_features = content_features.merge(
    top_shows[['uuid', 'top_show', 'top_genre', 'top_secondary_genre',
               'top_language', 'show_concentration']],
    on='uuid', how='left'
)
content_features.drop(columns=['total_content_minutes'], inplace=True)

# Genre cluster classification (aligned with Phase 1 content patterns)
def classify_genre(row):
    g = str(row.get('top_genre', '')).lower()
    sg = str(row.get('top_secondary_genre', '')).lower()
    if g == 'romance' and sg in ('forbidden love', 'edgy', ''):
        return 'Romance/CEO'
    elif g == 'drama' and sg in ('melodrama', 'secret lives'):
        return 'Empowerment'
    elif g in ('power struggles', 'thriller') and sg in ('inheritance', 'crime', 'horror'):
        return 'Hindi Thriller'
    elif g == 'fantasy':
        return 'Fantasy'
    elif g == 'suspense':
        return 'Suspense'
    elif g == 'drama':
        return 'Drama Other'
    elif g == 'romance':
        return 'Romance Other'
    else:
        return 'Other'

content_features['genre_cluster'] = content_features.apply(classify_genre, axis=1)

print(f"Content features built for {len(content_features):,} users")
print(f"Avg shows/user: {content_features['unique_shows'].mean():.1f}")
print(f"Genre cluster distribution:\n{content_features['genre_cluster'].value_counts()}")

# ============================================================
# DIMENSION 3: Retention Profile
# ============================================================
print("\n--- Dimension 3: Retention Profile ---")

# Episode depth per user per show — using CMS episode_number (not videoid count)
episode_depth = (
    uv.dropna(subset=['channel_ids'])
    .groupby(['uuid', 'channel_ids'])
    .agg(max_ep=('episode_num_int', 'max'))
    .reset_index()
)

retention_features = episode_depth.groupby('uuid').agg(
    max_episode_depth=('max_ep', 'max'),
    avg_episode_depth=('max_ep', 'mean')
).reset_index()

# Lock survival: did user reach episode 6+ on ANY show?
# (Ep5 is last free episode, Ep6 requires ad unlock)
retention_features['lock_survival'] = (
    retention_features['max_episode_depth'] >= 6
).astype(int)

# Binge propensity from session data
sess = pd.read_csv(SESSION_EPISODES_CSV)
binge = sess.groupby('uuid').agg(
    avg_episodes_per_session=('episodes_in_session', 'mean'),
    max_episodes_per_session=('episodes_in_session', 'max')
).reset_index()

retention_features = retention_features.merge(binge, on='uuid', how='left')
retention_features['avg_episodes_per_session'] = retention_features['avg_episodes_per_session'].fillna(1)
retention_features['max_episodes_per_session'] = retention_features['max_episodes_per_session'].fillna(1)

# Binge propensity: spikiness of session depth
retention_features['binge_propensity'] = (
    retention_features['max_episodes_per_session'] /
    retention_features['avg_episodes_per_session'].clip(lower=1)
)

print(f"Retention features built for {len(retention_features):,} users")
print(f"Lock survival rate: {retention_features['lock_survival'].mean()*100:.1f}%")
print(f"Avg max episode depth: {retention_features['max_episode_depth'].mean():.1f}")

# ============================================================
# DIMENSION 4: Demographics
# ============================================================
print("\n--- Dimension 4: Demographics ---")
demo = pd.read_csv(DEMOGRAPHICS_CSV)
demo['age_group'] = demo['age_group'].fillna('Unknown')
demo['gender'] = demo['gender'].fillna('Unknown')

# Age × Gender interaction feature
demo['age_gender'] = demo['gender'].str[0] + '_' + demo['age_group']
demo.loc[demo['gender'] == 'Unknown', 'age_gender'] = 'Unknown'

print(f"Demographics loaded for {len(demo):,} users")
print(f"Age known: {(demo['age_group'] != 'Unknown').mean()*100:.1f}%")
print(f"Top age_gender cells:\n{demo['age_gender'].value_counts().head(8)}")

# ============================================================
# DIMENSION 5: Channel + Interest Tags
# ============================================================
print("\n--- Dimension 5: Channel & Interest ---")
channel = pd.read_csv(CHANNEL_CSV)
print(f"Channel data for {len(channel):,} users")
print(f"Channel distribution:\n{channel['primary_channel'].value_counts()}")

# Interest tags (optional)
tag_count = None
if USE_PERSONA_TAGS and PERSONA_TAGS_CSV:
    try:
        tags = pd.read_csv(PERSONA_TAGS_CSV)
        tag_count = tags.groupby('uuid').agg(
            persona_tag_count=('persona_name', 'nunique')
        ).reset_index()
        print(f"Persona tags loaded for {len(tag_count):,} users")
        print(f"Avg tags/user: {tag_count['persona_tag_count'].mean():.1f}")
    except FileNotFoundError:
        print("Persona tags CSV not found — skipping")
        USE_PERSONA_TAGS = False

# ============================================================
# MERGE ALL DIMENSIONS
# ============================================================
print("\n" + "=" * 80)
print("MERGING FEATURE MATRIX")
print("=" * 80)

df = eng[['uuid', 'total_streams', 'total_minutes', 'unique_episodes',
          'active_days', 'total_sessions', 'mpc', 'minutes_per_stream',
          'streams_per_day', 'episodes_per_session', 'engagement_tier']].copy()

df = df.merge(content_features, on='uuid', how='left')
df = df.merge(retention_features, on='uuid', how='left')
df = df.merge(demo, on='uuid', how='left')
df = df.merge(channel, on='uuid', how='left')

if USE_PERSONA_TAGS and tag_count is not None:
    df = df.merge(tag_count, on='uuid', how='left')
    df['persona_tag_count'] = df['persona_tag_count'].fillna(0)

# Fill missing values
for col, default in {
    'age_group': 'Unknown', 'gender': 'Unknown', 'age_gender': 'Unknown',
    'primary_channel': 'Organic', 'genre_cluster': 'Other',
    'unique_shows': 1, 'genre_breadth': 1, 'show_concentration': 1.0,
    'max_episode_depth': 1, 'avg_episode_depth': 1, 'lock_survival': 0,
    'avg_episodes_per_session': 1, 'max_episodes_per_session': 1,
    'binge_propensity': 1.0,
}.items():
    if col in df.columns:
        df[col] = df[col].fillna(default)

print(f"\nFinal feature matrix: {len(df):,} users × {len(df.columns)} columns")
print(f"\nKey feature summary:")
for col in ['total_minutes', 'mpc', 'unique_shows', 'genre_breadth',
            'show_concentration', 'max_episode_depth', 'lock_survival',
            'avg_episodes_per_session', 'binge_propensity']:
    if col in df.columns:
        print(f"  {col:30s}: mean={df[col].mean():.2f}, median={df[col].median():.2f}")

# ============================================================
# PREPARE CLUSTERING FEATURES
# ============================================================
print("\n--- Preparing Clustering Features ---")

# Numeric features across all 5 dimensions
numeric_features = [
    # Dim 1: Engagement Depth
    'total_minutes', 'mpc', 'unique_episodes',
    'active_days', 'minutes_per_stream', 'streams_per_day',
    # Dim 2: Content Preference
    'unique_shows', 'genre_breadth', 'show_concentration',
    # Dim 3: Retention Profile
    'max_episode_depth', 'avg_episode_depth', 'lock_survival',
    'avg_episodes_per_session', 'binge_propensity',
]
if USE_PERSONA_TAGS and 'persona_tag_count' in df.columns:
    numeric_features.append('persona_tag_count')

# One-hot encode categorical features (NOT LabelEncoder)
cat_features = ['gender', 'age_group', 'primary_channel', 'genre_cluster']
df_encoded = pd.get_dummies(df[cat_features], prefix=cat_features, drop_first=False)

# Combine numeric + one-hot
feature_cols = numeric_features + list(df_encoded.columns)
X_numeric = df[numeric_features].values
X_cat = df_encoded.values
X_combined = np.hstack([X_numeric, X_cat])

# Scale: StandardScaler on numeric, leave one-hot as-is
scaler = StandardScaler()
X_numeric_scaled = scaler.fit_transform(X_numeric)
X_final = np.hstack([X_numeric_scaled, X_cat])

print(f"Feature matrix shape: {X_final.shape}")
print(f"Numeric features ({len(numeric_features)}): {numeric_features}")
print(f"One-hot features ({X_cat.shape[1]}): {list(df_encoded.columns)[:10]}...")

# ============================================================
# K-MEANS: OPTIMAL K SELECTION
# ============================================================
print("\n--- Finding Optimal K (K-Means) ---")

k_range = range(4, 9)
inertias = []
silhouettes = []

# Sample for faster computation
sample_size = min(50000, len(X_final))
np.random.seed(42)
sample_idx = np.random.choice(len(X_final), sample_size, replace=False)
X_sample = X_final[sample_idx]

for k in k_range:
    km = KMeans(n_clusters=k, random_state=42, n_init=10, max_iter=300)
    labels = km.fit_predict(X_sample)
    inertias.append(km.inertia_)
    sil = silhouette_score(X_sample, labels, sample_size=min(10000, sample_size))
    silhouettes.append(sil)
    print(f"  k={k}: Inertia={km.inertia_:,.0f}, Silhouette={sil:.4f}")

best_k = list(k_range)[np.argmax(silhouettes)]
print(f"\nBest k by silhouette: {best_k}")

# ============================================================
# HIERARCHICAL CLUSTERING VALIDATION
# ============================================================
print(f"\n--- Hierarchical Clustering Validation (k={best_k}) ---")

# Run agglomerative on same sample
agg = AgglomerativeClustering(n_clusters=best_k, linkage='ward')
agg_labels = agg.fit_predict(X_sample)
agg_sil = silhouette_score(X_sample, agg_labels, sample_size=min(10000, sample_size))
print(f"Agglomerative Silhouette: {agg_sil:.4f}")

# Compare K-Means vs Hierarchical using Adjusted Rand Index
km_for_ari = KMeans(n_clusters=best_k, random_state=42, n_init=10)
km_labels_ari = km_for_ari.fit_predict(X_sample)
ari = adjusted_rand_score(km_labels_ari, agg_labels)
print(f"Adjusted Rand Index (K-Means vs Hierarchical): {ari:.4f}")
if ari > 0.5:
    print("  → ARI > 0.5: Clusters are STABLE across methods. High confidence.")
elif ari > 0.3:
    print("  → ARI 0.3-0.5: Moderate agreement. Clusters are reasonable.")
else:
    print("  → ARI < 0.3: Low agreement. Consider reviewing k or features.")

# ============================================================
# FINAL CLUSTERING (full dataset)
# ============================================================
FINAL_K = best_k
print(f"\n--- Running Final K-Means with k={FINAL_K} on full dataset ---")

kmeans = KMeans(n_clusters=FINAL_K, random_state=42, n_init=20, max_iter=500)
df['cluster'] = kmeans.fit_predict(X_final)

print(f"Cluster sizes:")
for cid in sorted(df['cluster'].unique()):
    n = (df['cluster'] == cid).sum()
    print(f"  Cluster {cid}: {n:,} users ({n/len(df)*100:.1f}%)")

# Final silhouette on sample
final_sil = silhouette_score(
    X_sample, kmeans.predict(X_sample),
    sample_size=min(10000, sample_size)
)
print(f"\nFinal Silhouette Score: {final_sil:.4f} (target: ≥0.3)")

# ============================================================
# STRATEGIC ROLE ASSIGNMENT (Grow / Nourish / Sustain / Convert / Explore)
# ============================================================
print("\n" + "=" * 80)
print("STRATEGIC ROLE ASSIGNMENT")
print("=" * 80)

platform_median_minutes = df['total_minutes'].median()
print(f"Platform median total_minutes: {platform_median_minutes:.1f}")

cluster_stats = df.groupby('cluster').agg(
    users=('uuid', 'count'),
    avg_minutes=('total_minutes', 'mean'),
    avg_mpc=('mpc', 'mean'),
    avg_active_days=('active_days', 'mean'),
    lock_survival_pct=('lock_survival', 'mean'),
    avg_shows=('unique_shows', 'mean'),
).reset_index()
cluster_stats['pct_total'] = cluster_stats['users'] / len(df) * 100

def assign_role(row):
    pct = row['pct_total']
    avg_min = row['avg_minutes']
    lock_surv = row['lock_survival_pct']
    avg_days = row['avg_active_days']

    # CONVERT: large + very low engagement (single-show samplers)
    if pct > 30 and avg_min < 10:
        return 'CONVERT'
    # EXPLORE: small + very low engagement
    if pct < 10 and avg_min < 5:
        return 'EXPLORE'
    # GROW: large + moderate engagement
    if pct > 20 and avg_min < platform_median_minutes:
        return 'GROW'
    # SUSTAIN: deep engagement + high activity
    if avg_min > platform_median_minutes * 1.5 and avg_days > 4:
        return 'SUSTAIN'
    # NOURISH: mid-size + above-median engagement + lock survival
    if 5 <= pct <= 25 and avg_min > platform_median_minutes and lock_surv > 0.5:
        return 'NOURISH'
    # Fallback based on engagement
    if avg_min > platform_median_minutes:
        return 'NOURISH'
    return 'GROW'

cluster_stats['strategic_role'] = cluster_stats.apply(assign_role, axis=1)

# Map back to main dataframe
role_map = cluster_stats.set_index('cluster')['strategic_role'].to_dict()
df['strategic_role'] = df['cluster'].map(role_map)

print("\nCluster → Role Assignment:")
for _, row in cluster_stats.iterrows():
    print(f"  Cluster {int(row['cluster'])}: {row['strategic_role']:8s} "
          f"({row['users']:,.0f} users, {row['pct_total']:.1f}%, "
          f"avg_min={row['avg_minutes']:.1f}, lock_surv={row['lock_survival_pct']*100:.0f}%)")

# ============================================================
# CLUSTER PROFILING — Full 5-Dimension Profiles
# ============================================================
print("\n" + "=" * 80)
print("CLUSTER PROFILES — 5 DIMENSIONS")
print("=" * 80)

for cluster_id in sorted(df['cluster'].unique()):
    c = df[df['cluster'] == cluster_id]
    n = len(c)
    pct = n / len(df) * 100
    role = role_map[cluster_id]

    print(f"\n{'=' * 70}")
    print(f"CLUSTER {cluster_id} — {role} — {n:,} users ({pct:.1f}%)")
    print(f"{'=' * 70}")

    # Dim 1: Engagement Depth
    print(f"\n  [Dim 1] Engagement Depth:")
    print(f"    Avg Minutes:         {c['total_minutes'].mean():.1f} (median: {c['total_minutes'].median():.1f})")
    print(f"    Avg MPC:             {c['mpc'].mean():.1f}")
    print(f"    Avg Streams:         {c['total_streams'].mean():.1f}")
    print(f"    Avg Active Days:     {c['active_days'].mean():.1f} / 7")
    print(f"    Avg Min/Stream:      {c['minutes_per_stream'].mean():.2f}")
    tier_dist = c['engagement_tier'].value_counts(normalize=True).sort_index()
    for tier, p in tier_dist.items():
        print(f"      {tier:12s}: {p*100:5.1f}%")

    # Dim 2: Content Preference
    print(f"\n  [Dim 2] Content Preference:")
    print(f"    Avg Shows Watched:      {c['unique_shows'].mean():.1f}")
    print(f"    Avg Genre Breadth:      {c['genre_breadth'].mean():.1f}")
    print(f"    Avg Show Concentration: {c['show_concentration'].mean():.2f}")
    gc_dist = c['genre_cluster'].value_counts(normalize=True).head(4)
    print(f"    Genre Clusters:")
    for g, p in gc_dist.items():
        print(f"      {g:20s}: {p*100:5.1f}%")
    if 'top_show' in c.columns:
        top = c['top_show'].value_counts().head(5)
        print(f"    Top Shows:")
        for show, cnt in top.items():
            print(f"      {show}: {cnt:,} ({cnt/n*100:.1f}%)")

    # Dim 3: Retention Profile
    print(f"\n  [Dim 3] Retention Profile:")
    print(f"    Avg Max Episode Depth:    {c['max_episode_depth'].mean():.1f}")
    print(f"    Lock Survival Rate:       {c['lock_survival'].mean()*100:.1f}%")
    print(f"    Avg Episodes/Session:     {c['avg_episodes_per_session'].mean():.2f}")
    print(f"    Binge Propensity:         {c['binge_propensity'].mean():.2f}")

    # Dim 4: Demographics
    print(f"\n  [Dim 4] Demographics:")
    gender_dist = c['gender'].value_counts(normalize=True)
    for g, p in gender_dist.head(3).items():
        print(f"    {g:10s}: {p*100:5.1f}%")
    age_dist = c['age_group'].value_counts(normalize=True)
    for a, p in age_dist.head(5).items():
        print(f"    {a:10s}: {p*100:5.1f}%")
    if 'age_gender' in c.columns:
        ag_top = c['age_gender'].value_counts(normalize=True).head(3)
        print(f"    Top age×gender cells:")
        for ag, p in ag_top.items():
            print(f"      {ag:15s}: {p*100:5.1f}%")

    # Dim 5: Channel + Interest
    print(f"\n  [Dim 5] Channel & Interest:")
    ch_dist = c['primary_channel'].value_counts(normalize=True)
    for ch, p in ch_dist.items():
        print(f"    {ch:18s}: {p*100:5.1f}%")
    if USE_PERSONA_TAGS and 'persona_tag_count' in c.columns:
        print(f"    Avg Persona Tags:  {c['persona_tag_count'].mean():.1f}")

# ============================================================
# CROSS-TABS
# ============================================================
print("\n" + "=" * 80)
print("CROSS-TABS")
print("=" * 80)

for label, col in [
    ("Cluster × Engagement Tier", "engagement_tier"),
    ("Cluster × Gender", "gender"),
    ("Cluster × Age Group", "age_group"),
    ("Cluster × Channel", "primary_channel"),
    ("Cluster × Genre Cluster", "genre_cluster"),
    ("Cluster × Lock Survival", "lock_survival"),
]:
    if col in df.columns:
        print(f"\n{label}:")
        ct = pd.crosstab(df['cluster'], df[col], normalize='index') * 100
        print(ct.round(1).to_string())

# ============================================================
# PHASE 1 HYPOTHESIS VALIDATION
# ============================================================
print("\n" + "=" * 80)
print("PHASE 1 HYPOTHESIS VALIDATION")
print("=" * 80)

# Build per-cluster summary for hypothesis matching
hyp_summary = df.groupby('cluster').agg(
    users=('uuid', 'count'),
    pct_total=('uuid', lambda x: len(x) / len(df) * 100),
    avg_minutes=('total_minutes', 'mean'),
    avg_mpc=('mpc', 'mean'),
    avg_shows=('unique_shows', 'mean'),
    avg_episode_depth=('max_episode_depth', 'mean'),
    lock_survival_pct=('lock_survival', lambda x: x.mean() * 100),
    avg_eps_per_session=('avg_episodes_per_session', 'mean'),
    pct_female=('gender', lambda x: (x == 'Female').mean() * 100),
    pct_male=('gender', lambda x: (x == 'Male').mean() * 100),
    pct_18_24=('age_group', lambda x: (x == '18-24').mean() * 100),
    pct_25_34=('age_group', lambda x: (x == '25-34').mean() * 100),
    pct_35_plus=('age_group', lambda x: (x.isin(['35-44','45-54','55-64','65+'])).mean() * 100),
    pct_organic=('primary_channel', lambda x: (x == 'Organic').mean() * 100),
    pct_paid=('primary_channel', lambda x: (x == 'Paid').mean() * 100),
    pct_romance_ceo=('genre_cluster', lambda x: (x == 'Romance/CEO').mean() * 100),
    pct_empowerment=('genre_cluster', lambda x: (x == 'Empowerment').mean() * 100),
    pct_hindi_thriller=('genre_cluster', lambda x: (x == 'Hindi Thriller').mean() * 100),
    show_concentration=('show_concentration', 'mean'),
).round(1)

print("\nCluster Summary Table:")
print(hyp_summary.to_string())

# Automated hypothesis scoring
hypotheses = {
    'P1: Young Female Romance Binger [GROW]': {
        'criteria': lambda r: (r['pct_female'] > 55 and r['pct_18_24'] > 35
                               and r['avg_mpc'] > 20 and r['pct_romance_ceo'] > 30),
        'desc': 'F18-24, high MPC, romance/CEO content, 2-5 shows/day'
    },
    'P2: Male Crossover Viewer [GROW]': {
        'criteria': lambda r: (r['pct_male'] > 55 and r['pct_25_34'] > 30
                               and r['avg_mpc'] > 10 and r['avg_mpc'] < 50),
        'desc': 'M25-34, moderate MPC, crossover titles'
    },
    'P3: Discovery Sampler [CONVERT]': {
        'criteria': lambda r: (r['pct_total'] > 25 and r['avg_minutes'] < 15
                               and r['avg_shows'] < 2),
        'desc': 'Broad demo, <15 min total, 1 show/day'
    },
    'P4: Multi-Show Power User [NOURISH]': {
        'criteria': lambda r: (r['avg_shows'] > 3 and r['avg_minutes'] > 80
                               and r['lock_survival_pct'] > 60),
        'desc': 'Mixed <35, 80+ min, 4+ shows, high lock survival'
    },
    'P5: Mature Loyal Viewer [SUSTAIN]': {
        'criteria': lambda r: (r['pct_35_plus'] > 25 and r['avg_mpc'] > 15
                               and r['pct_organic'] > 50),
        'desc': 'F/M 35+, 15-30 min MPC, organic, stable'
    },
    'P6: Hindi Content Explorer [EXPLORE]': {
        'criteria': lambda r: (r['pct_hindi_thriller'] > 15 and r['avg_minutes'] < 10),
        'desc': 'Hindi thriller/power struggles, <10 min, sampling only'
    },
}

validated_count = 0
print("\nHypothesis → Cluster Matching:")
for hyp_name, hyp in hypotheses.items():
    matched = []
    for _, row in hyp_summary.iterrows():
        if hyp['criteria'](row):
            matched.append(int(row.name))
    if matched:
        validated_count += 1
        print(f"  ✅ {hyp_name}")
        print(f"     → Matched cluster(s): {matched}")
        print(f"     Criteria: {hyp['desc']}")
    else:
        print(f"  ❌ {hyp_name}")
        print(f"     → No cluster matched. Criteria: {hyp['desc']}")

print(f"\nValidated: {validated_count}/6 hypotheses (target: ≥4)")
if validated_count >= 4:
    print("✅ Phase 2 hypothesis alignment target MET")
else:
    print("⚠️  Below target. Consider adjusting k or reviewing feature weights.")

# ============================================================
# PERSONA CARD GENERATION
# ============================================================
print("\n" + "=" * 80)
print("PERSONA CARD GENERATION")
print("=" * 80)

def suggest_persona_name(row, cluster_df):
    """Auto-suggest a persona name based on dominant traits."""
    role = role_map[row.name]
    top_gender = cluster_df['gender'].mode().iloc[0] if len(cluster_df['gender'].mode()) > 0 else 'Mixed'
    top_age = cluster_df['age_group'].mode().iloc[0] if len(cluster_df['age_group'].mode()) > 0 else 'Mixed'
    top_genre = cluster_df['genre_cluster'].mode().iloc[0] if len(cluster_df['genre_cluster'].mode()) > 0 else 'Mixed'

    if role == 'CONVERT' and row['avg_shows'] < 2:
        return "Discovery Sampler"
    if role == 'EXPLORE' and row['avg_minutes'] < 5:
        return "Hindi Content Explorer"
    if top_gender == 'Female' and top_age == '18-24' and 'Romance' in top_genre:
        return "Young Female Romance Binger"
    if top_gender == 'Male' and top_age == '25-34':
        return "Male Crossover Viewer"
    if row['pct_35_plus'] > 25 and row['pct_organic'] > 50:
        return "Mature Loyal Viewer"
    if row['avg_shows'] > 3 and row['avg_minutes'] > 80:
        return "Multi-Show Power User"
    if top_gender == 'Female' and row['pct_empowerment'] > 20:
        return "Empowerment Drama Fan"
    return f"{top_gender} {top_age} {top_genre} Viewer"

cards = []
for cluster_id in sorted(df['cluster'].unique()):
    c = df[df['cluster'] == cluster_id]
    n = len(c)
    pct = n / len(df) * 100
    role = role_map[cluster_id]
    row = hyp_summary.loc[cluster_id]
    name = suggest_persona_name(row, c)

    # Top shows
    top_shows_list = c['top_show'].value_counts().head(3)
    top_shows_str = ", ".join([f"{s} ({cnt:,})" for s, cnt in top_shows_list.items()])

    # Top genre clusters
    gc = c['genre_cluster'].value_counts(normalize=True).head(3)
    gc_str = ", ".join([f"{g} ({p*100:.0f}%)" for g, p in gc.items()])

    # Top age×gender
    ag = c['age_gender'].value_counts(normalize=True).head(3)
    ag_str = ", ".join([f"{a} ({p*100:.0f}%)" for a, p in ag.items()])

    # Channel split
    ch = c['primary_channel'].value_counts(normalize=True)
    ch_str = ", ".join([f"{k} ({v*100:.0f}%)" for k, v in ch.items()])

    # Persona tag count (may not exist if tags were skipped)
    tag_str = f"{c['persona_tag_count'].mean():.0f}" if 'persona_tag_count' in c.columns else "N/A"

    card = f"""
{'=' * 70}
PERSONA CARD: {name}
Cluster {cluster_id} | {role} | {n:,} users ({pct:.1f}% of audience)
{'=' * 70}

  ARCHETYPE: {name}
  STRATEGIC ROLE: {role}
    Rationale: {"Large segment, low engagement — conversion priority" if role == 'CONVERT'
                else "Large segment, moderate engagement — growth priority" if role == 'GROW'
                else "Mid-size, deep engagement — loyalty priority" if role == 'NOURISH'
                else "Small, highly engaged — retention priority" if role == 'SUSTAIN'
                else "Emerging segment, unclear retention — exploration needed"}

  BEHAVIORAL FINGERPRINT:
    Engagement:  {row['avg_minutes']:.0f} avg min/week | {row['avg_mpc']:.0f} MPC | {c['active_days'].mean():.1f} active days/7
    Retention:   {row['avg_episode_depth']:.0f} avg ep depth | {row['lock_survival_pct']:.0f}% lock survival | {row['avg_eps_per_session']:.1f} eps/session
    Content:     {gc_str}
    Top Shows:   {top_shows_str}
    Show Focus:  {row['show_concentration']:.0f}% concentration ({"loyal" if row['show_concentration'] > 60 else "explorer"})

  DEMOGRAPHIC PROFILE:
    Gender:      {row['pct_female']:.0f}% F / {row['pct_male']:.0f}% M
    Age:         {row['pct_18_24']:.0f}% 18-24 | {row['pct_25_34']:.0f}% 25-34 | {row['pct_35_plus']:.0f}% 35+
    Top Cells:   {ag_str}

  CHANNEL PROFILE:
    {ch_str}

  COMMERCIAL PROFILE:
    Persona Tags: {tag_str} avg tags/user (interest breadth)

  COVERAGE: {pct:.1f}% of active Fatafat audience
"""
    cards.append(card)
    print(card)

# Export persona cards
with open("persona_cards.txt", "w") as f:
    f.write("FATAFAT SYNTHETIC PERSONAS — PHASE 2 PERSONA CARDS\n")
    f.write(f"Generated: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}\n")
    f.write(f"Clustering: K-Means k={FINAL_K}, Silhouette={final_sil:.4f}\n")
    f.write(f"Hierarchical ARI: {ari:.4f}\n")
    f.write(f"Hypotheses Validated: {validated_count}/6\n")
    for card in cards:
        f.write(card)
print(f"\n✅ Persona cards exported to: persona_cards.txt")

# ============================================================
# EXPORT & FINAL METRICS
# ============================================================
print("\n" + "=" * 80)
print("FINAL METRICS & EXPORT")
print("=" * 80)

# Export full feature matrix with clusters
output_path = "fatafat_personas_phase2.csv"
df.to_csv(output_path, index=False)
print(f"✅ Full feature matrix exported to: {output_path}")

# Coverage metric
total_users = len(df)
assigned_users = len(df[df['cluster'].notna()])
coverage = assigned_users / total_users * 100
print(f"\n📊 PHASE 2 SUCCESS METRICS:")
print(f"   Persona Coverage:       {assigned_users:,} / {total_users:,} = {coverage:.1f}% (target: ≥75%)")
print(f"   Silhouette Score:       {final_sil:.4f} (target: ≥0.3)")
print(f"   Hierarchical ARI:       {ari:.4f} (>0.5 = stable)")
print(f"   Hypotheses Validated:   {validated_count}/6 (target: ≥4)")
print(f"   Demographic Overlay:    {(df['age_group'] != 'Unknown').mean()*100:.1f}% (target: ≥90%)")

# Check for tiny clusters
min_cluster_pct = df['cluster'].value_counts(normalize=True).min() * 100
if min_cluster_pct < 2:
    print(f"   ⚠️  Smallest cluster is {min_cluster_pct:.1f}% — may be too small to be actionable")
else:
    print(f"   ✅ All clusters ≥ 2% of audience")

print(f"\n🎯 NEXT STEPS:")
print(f"1. Review persona cards in persona_cards.txt")
print(f"2. Validate/rename personas based on domain knowledge")
print(f"3. Adjust strategic role assignments if needed")
print(f"4. If silhouette < 0.3 or hypotheses < 4, try FINAL_K = 6")
print(f"5. Proceed to Phase 3: AI Model Training on validated personas")
