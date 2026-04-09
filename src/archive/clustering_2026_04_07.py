
"""
Fatafat Synthetic Personas — Phase 2: K-Means Clustering
=========================================================
Prerequisites: pip install pandas numpy scikit-learn

Input: CSV file with columns:
  uuid, total_streams, total_minutes, unique_episodes, age_group, gender, primary_channel

Output: Persona assignments, cluster profiles, and summary statistics
"""

import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
import warnings
warnings.filterwarnings('ignore')

# ============================================================
# STEP 1: Load Data
# ============================================================
# Update this path to your local CSV file
CSV_PATH = "fatafat_feature_matrix.csv"

print("Loading data...")
df = pd.read_csv(CSV_PATH)
print(f"Loaded {len(df):,} users")
print(f"Columns: {list(df.columns)}")
print(f"
Sample:
{df.head()}")

# ============================================================
# STEP 2: Data Cleaning & Feature Engineering
# ============================================================
print("
--- Data Cleaning ---")

# Fill missing demographics
df['age_group'] = df['age_group'].fillna('Unknown')
df['gender'] = df['gender'].fillna('Unknown')
df['primary_channel'] = df['primary_channel'].fillna('Unknown')

# Derived features
df['minutes_per_stream'] = df['total_minutes'] / df['total_streams'].clip(lower=1)
df['episodes_per_stream'] = df['unique_episodes'] / df['total_streams'].clip(lower=1)

# Engagement tier (quintiles)
df['engagement_tier'] = pd.qcut(
    df['total_minutes'], 
    q=5, 
    labels=['Sampler', 'Light', 'Moderate', 'Heavy', 'Binge'],
    duplicates='drop'
)

print(f"
Engagement Tier Distribution:")
print(df['engagement_tier'].value_counts().sort_index())

print(f"
Demographics Coverage:")
print(f"  Age known: {(df['age_group'] != 'Unknown').sum():,} ({(df['age_group'] != 'Unknown').mean()*100:.1f}%)")
print(f"  Gender known: {(df['gender'] != 'Unknown').sum():,} ({(df['gender'] != 'Unknown').mean()*100:.1f}%)")

# ============================================================
# STEP 3: Prepare Clustering Features
# ============================================================
print("
--- Preparing Clustering Features ---")

# Numeric features for clustering
numeric_features = ['total_streams', 'total_minutes', 'unique_episodes', 
                    'minutes_per_stream', 'episodes_per_stream']

# Encode categorical features
le_age = LabelEncoder()
le_gender = LabelEncoder()
le_channel = LabelEncoder()

df['age_encoded'] = le_age.fit_transform(df['age_group'])
df['gender_encoded'] = le_gender.fit_transform(df['gender'])
df['channel_encoded'] = le_channel.fit_transform(df['primary_channel'])

# Feature matrix
feature_cols = numeric_features + ['age_encoded', 'gender_encoded', 'channel_encoded']
X = df[feature_cols].values

# Scale features
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

print(f"Feature matrix shape: {X_scaled.shape}")
print(f"Features used: {feature_cols}")

# ============================================================
# STEP 4: Optimal K Selection (Elbow + Silhouette)
# ============================================================
print("
--- Finding Optimal K ---")

k_range = range(3, 9)
inertias = []
silhouettes = []

# Use a sample for faster computation if dataset is large
sample_size = min(50000, len(X_scaled))
np.random.seed(42)
sample_idx = np.random.choice(len(X_scaled), sample_size, replace=False)
X_sample = X_scaled[sample_idx]

for k in k_range:
    km = KMeans(n_clusters=k, random_state=42, n_init=10, max_iter=300)
    labels = km.fit_predict(X_sample)
    inertias.append(km.inertia_)
    sil = silhouette_score(X_sample, labels, sample_size=min(10000, sample_size))
    silhouettes.append(sil)
    print(f"  k={k}: Inertia={km.inertia_:,.0f}, Silhouette={sil:.4f}")

best_k = k_range[np.argmax(silhouettes)]
print(f"
Best k by silhouette: {best_k}")

# ============================================================
# STEP 5: Final Clustering
# ============================================================
# You can override best_k here if you prefer 5 or 6 personas
FINAL_K = best_k  # Change to 5 or 6 if preferred
print(f"
--- Running Final K-Means with k={FINAL_K} ---")

kmeans = KMeans(n_clusters=FINAL_K, random_state=42, n_init=20, max_iter=500)
df['cluster'] = kmeans.fit_predict(X_scaled)

print(f"Cluster sizes:")
print(df['cluster'].value_counts().sort_index())

# ============================================================
# STEP 6: Cluster Profiling
# ============================================================
print("
" + "="*80)
print("CLUSTER PROFILES")
print("="*80)

for cluster_id in sorted(df['cluster'].unique()):
    cluster_df = df[df['cluster'] == cluster_id]
    n = len(cluster_df)
    pct = n / len(df) * 100
    
    print(f"
{'='*60}")
    print(f"CLUSTER {cluster_id} — {n:,} users ({pct:.1f}%)")
    print(f"{'='*60}")
    
    # Engagement metrics
    print(f"
  Engagement:")
    print(f"    Avg Total Streams:   {cluster_df['total_streams'].mean():.1f}")
    print(f"    Avg Total Minutes:   {cluster_df['total_minutes'].mean():.1f}")
    print(f"    Avg Unique Episodes: {cluster_df['unique_episodes'].mean():.1f}")
    print(f"    Avg Min/Stream:      {cluster_df['minutes_per_stream'].mean():.2f}")
    print(f"    Median Total Min:    {cluster_df['total_minutes'].median():.1f}")
    
    # Engagement tier distribution
    print(f"
  Engagement Tier:")
    tier_dist = cluster_df['engagement_tier'].value_counts(normalize=True).sort_index()
    for tier, pct_tier in tier_dist.items():
        print(f"    {tier:12s}: {pct_tier*100:5.1f}%")
    
    # Demographics
    print(f"
  Demographics:")
    gender_dist = cluster_df['gender'].value_counts(normalize=True)
    for g, p in gender_dist.head(3).items():
        print(f"    {g:10s}: {p*100:5.1f}%")
    
    age_dist = cluster_df['age_group'].value_counts(normalize=True)
    for a, p in age_dist.head(4).items():
        print(f"    {a:10s}: {p*100:5.1f}%")
    
    # Channel
    print(f"
  Acquisition Channel:")
    ch_dist = cluster_df['primary_channel'].value_counts(normalize=True)
    for c, p in ch_dist.items():
        print(f"    {c:10s}: {p*100:5.1f}%")

# ============================================================
# STEP 7: Summary Cross-Tab
# ============================================================
print("
" + "="*80)
print("CROSS-TAB: Cluster × Engagement Tier")
print("="*80)
cross_tab = pd.crosstab(df['cluster'], df['engagement_tier'], normalize='index') * 100
print(cross_tab.round(1))

print("
" + "="*80)
print("CROSS-TAB: Cluster × Gender")
print("="*80)
cross_tab_gender = pd.crosstab(df['cluster'], df['gender'], normalize='index') * 100
print(cross_tab_gender.round(1))

print("
" + "="*80)
print("CROSS-TAB: Cluster × Channel")
print("="*80)
cross_tab_channel = pd.crosstab(df['cluster'], df['primary_channel'], normalize='index') * 100
print(cross_tab_channel.round(1))

# ============================================================
# STEP 8: Export Results
# ============================================================
output_path = "fatafat_personas_clustered.csv"
df.to_csv(output_path, index=False)
print(f"
✅ Results exported to: {output_path}")

# Summary table for persona naming
print("
" + "="*80)
print("PERSONA SUMMARY (for naming)")
print("="*80)
summary = df.groupby('cluster').agg(
    users=('uuid', 'count'),
    avg_streams=('total_streams', 'mean'),
    avg_minutes=('total_minutes', 'mean'),
    avg_episodes=('unique_episodes', 'mean'),
    top_gender=('gender', lambda x: x.mode().iloc[0] if len(x.mode()) > 0 else 'Unknown'),
    top_age=('age_group', lambda x: x.mode().iloc[0] if len(x.mode()) > 0 else 'Unknown'),
    top_channel=('primary_channel', lambda x: x.mode().iloc[0] if len(x.mode()) > 0 else 'Unknown'),
    pct_organic=('primary_channel', lambda x: (x == 'Organic').mean() * 100),
    pct_paid=('primary_channel', lambda x: (x == 'Paid').mean() * 100),
).round(1)

print(summary.to_string())

print("

🎯 NEXT STEPS:")
print("1. Review cluster profiles above")
print("2. Name each persona based on dominant traits")
print("3. Paste the summary back into the chat agent for persona documentation")
print("4. Add show-preference data for richer profiles")

