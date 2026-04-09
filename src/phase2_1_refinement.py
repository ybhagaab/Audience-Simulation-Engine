"""
Phase 2.1: Refinement — Add persona tags + re-cluster with k=6 + sub-cluster samplers
=======================================================================================
Prerequisites: Run phase2_clustering.py first (produces fatafat_personas_phase2.csv)
               Run export_persona_tags.py (produces q25_persona_tags.csv with interest flags)

Input:
  - fatafat_personas_phase2.csv  — Phase 2 feature matrix (1.9M users)
  - q25_persona_tags.csv         — Aggregated persona tags (tag_count + 8 interest flags)

Output:
  - fatafat_personas_phase2_1.csv  — Updated feature matrix with 6 clusters
  - persona_cards_v2.txt           — Updated persona cards with commercial profiles
"""

import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans, AgglomerativeClustering
from sklearn.metrics import silhouette_score, adjusted_rand_score
import warnings
warnings.filterwarnings('ignore')

print("=" * 80)
print("PHASE 2.1: Refinement — Persona Tags + k=6 + Sampler Sub-Clustering")
print("=" * 80)

# ============================================================
# LOAD PHASE 2 DATA + PERSONA TAGS
# ============================================================
print("\n--- Loading Data ---")
df = pd.read_csv("fatafat_personas_phase2.csv")
print(f"Phase 2 feature matrix: {len(df):,} users × {len(df.columns)} columns")

tags = pd.read_csv("q25_persona_tags.csv")
print(f"Persona tags: {len(tags):,} users with tags")

# Merge tags
df = df.merge(tags, on='uuid', how='left')

# Fill missing tags (users without ML persona tags)
df['tag_count'] = df['tag_count'].fillna(0).astype(int)
for col in ['has_fashion_beauty', 'has_electronics_tech', 'has_health_fitness',
            'has_home_kitchen', 'has_travel', 'has_parents_baby',
            'has_automotive', 'has_affluent_premium']:
    df[col] = df[col].fillna(0).astype(int)

tag_coverage = (df['tag_count'] > 0).mean() * 100
print(f"Tag coverage: {tag_coverage:.1f}% of users have persona tags")
print(f"Avg tags/user (tagged users): {df.loc[df['tag_count'] > 0, 'tag_count'].mean():.1f}")

# Interest category distribution
print("\nInterest Category Prevalence (among tagged users):")
tagged = df[df['tag_count'] > 0]
for col in ['has_fashion_beauty', 'has_electronics_tech', 'has_health_fitness',
            'has_home_kitchen', 'has_travel', 'has_parents_baby',
            'has_automotive', 'has_affluent_premium']:
    pct = tagged[col].mean() * 100
    label = col.replace('has_', '').replace('_', ' ').title()
    print(f"  {label:25s}: {pct:.1f}%")

# ============================================================
# REBUILD FEATURE MATRIX WITH PERSONA TAGS
# ============================================================
print("\n--- Rebuilding Feature Matrix with Persona Tags ---")

numeric_features = [
    # Dim 1: Engagement Depth
    'total_minutes', 'mpc', 'unique_episodes',
    'active_days', 'minutes_per_stream', 'streams_per_day',
    # Dim 2: Content Preference
    'unique_shows', 'genre_breadth', 'show_concentration',
    # Dim 3: Retention Profile
    'max_episode_depth', 'avg_episode_depth', 'lock_survival',
    'avg_episodes_per_session', 'binge_propensity',
    # Dim 5b: Interest Tags (NEW)
    'tag_count',
    'has_fashion_beauty', 'has_electronics_tech', 'has_health_fitness',
    'has_home_kitchen', 'has_travel', 'has_parents_baby',
    'has_automotive', 'has_affluent_premium',
]

cat_features = ['gender', 'age_group', 'primary_channel', 'genre_cluster']
df_encoded = pd.get_dummies(df[cat_features], prefix=cat_features, drop_first=False)

X_numeric = df[numeric_features].values
X_cat = df_encoded.values

scaler = StandardScaler()
X_numeric_scaled = scaler.fit_transform(X_numeric)
X_final = np.hstack([X_numeric_scaled, X_cat])

print(f"Feature matrix: {X_final.shape} ({len(numeric_features)} numeric + {X_cat.shape[1]} one-hot)")

# ============================================================
# FULL DATASET CLUSTERING WITH k=6
# ============================================================
print("\n--- K-Means with k=6 (matching Phase 1 hypothesis count) ---")

sample_size = min(50000, len(X_final))
np.random.seed(42)
sample_idx = np.random.choice(len(X_final), sample_size, replace=False)
X_sample = X_final[sample_idx]

# Test k=4 through k=8 with new features
print("K selection with persona tags:")
for k in range(4, 9):
    km = KMeans(n_clusters=k, random_state=42, n_init=10, max_iter=300)
    labels = km.fit_predict(X_sample)
    sil = silhouette_score(X_sample, labels, sample_size=min(10000, sample_size))
    print(f"  k={k}: Silhouette={sil:.4f}")

# Run k=6 on full dataset
print("\nRunning k=6 on full dataset...")
kmeans_6 = KMeans(n_clusters=6, random_state=42, n_init=20, max_iter=500)
df['cluster_v2'] = kmeans_6.fit_predict(X_final)

sil_6 = silhouette_score(X_sample, kmeans_6.predict(X_sample),
                          sample_size=min(10000, sample_size))
print(f"k=6 Silhouette: {sil_6:.4f}")

# Hierarchical validation
agg_6 = AgglomerativeClustering(n_clusters=6, linkage='ward')
agg_labels = agg_6.fit_predict(X_sample)
ari_6 = adjusted_rand_score(kmeans_6.predict(X_sample), agg_labels)
print(f"Hierarchical ARI: {ari_6:.4f}")

print(f"\nCluster sizes (k=6):")
for cid in sorted(df['cluster_v2'].unique()):
    n = (df['cluster_v2'] == cid).sum()
    print(f"  Cluster {cid}: {n:,} users ({n/len(df)*100:.1f}%)")

# ============================================================
# SUB-CLUSTER THE SAMPLER SEGMENT (Phase 2 Cluster 0)
# ============================================================
print("\n" + "=" * 80)
print("SUB-CLUSTERING: Sampler Segment (Phase 2 Cluster 0)")
print("=" * 80)

# Identify samplers from original Phase 2 clustering
# Cluster 0 was the 80% sampler segment — use total_minutes < 15 as proxy
samplers = df[df['total_minutes'] < 15].copy()
print(f"Sampler segment: {len(samplers):,} users ({len(samplers)/len(df)*100:.1f}%)")

# Build feature matrix for samplers only
X_samp_numeric = samplers[numeric_features].values
X_samp_cat = pd.get_dummies(samplers[cat_features], prefix=cat_features, drop_first=False)

# Ensure same columns as full dataset
for col in df_encoded.columns:
    if col not in X_samp_cat.columns:
        X_samp_cat[col] = 0
X_samp_cat = X_samp_cat[df_encoded.columns]

scaler_samp = StandardScaler()
X_samp_scaled = scaler_samp.fit_transform(X_samp_numeric)
X_samp_final = np.hstack([X_samp_scaled, X_samp_cat.values])

# Test k=3 to k=6 for sub-clusters
samp_sample_size = min(50000, len(X_samp_final))
np.random.seed(42)
samp_idx = np.random.choice(len(X_samp_final), samp_sample_size, replace=False)
X_samp_sample = X_samp_final[samp_idx]

print("\nSub-cluster k selection:")
for k in range(3, 7):
    km = KMeans(n_clusters=k, random_state=42, n_init=10, max_iter=300)
    labels = km.fit_predict(X_samp_sample)
    sil = silhouette_score(X_samp_sample, labels, sample_size=min(10000, samp_sample_size))
    print(f"  k={k}: Silhouette={sil:.4f}")

# Run k=4 sub-clustering on samplers
SUB_K = 4
print(f"\nRunning k={SUB_K} sub-clustering on samplers...")
km_sub = KMeans(n_clusters=SUB_K, random_state=42, n_init=20, max_iter=500)
samplers['sub_cluster'] = km_sub.fit_predict(X_samp_final)

sub_sil = silhouette_score(X_samp_sample, km_sub.predict(X_samp_sample),
                            sample_size=min(10000, samp_sample_size))
print(f"Sub-cluster Silhouette: {sub_sil:.4f}")

print(f"\nSampler Sub-Cluster Profiles:")
for sc in sorted(samplers['sub_cluster'].unique()):
    s = samplers[samplers['sub_cluster'] == sc]
    n = len(s)
    print(f"\n  Sub-Cluster {sc}: {n:,} users ({n/len(samplers)*100:.1f}% of samplers)")
    print(f"    Avg Minutes: {s['total_minutes'].mean():.2f}")
    print(f"    Avg Shows:   {s['unique_shows'].mean():.1f}")
    print(f"    Gender:      {(s['gender']=='Female').mean()*100:.0f}% F / {(s['gender']=='Male').mean()*100:.0f}% M")
    print(f"    18-24:       {(s['age_group']=='18-24').mean()*100:.0f}%")
    print(f"    25-34:       {(s['age_group']=='25-34').mean()*100:.0f}%")
    print(f"    35+:         {s['age_group'].isin(['35-44','45-54','55-64','65+']).mean()*100:.0f}%")
    print(f"    Organic:     {(s['primary_channel']=='Organic').mean()*100:.0f}%")
    print(f"    Paid:        {(s['primary_channel']=='Paid').mean()*100:.0f}%")
    print(f"    Push:        {(s['primary_channel']=='Push').mean()*100:.0f}%")
    gc = s['genre_cluster'].value_counts(normalize=True).head(3)
    print(f"    Top Genres:  {', '.join([f'{g} ({p*100:.0f}%)' for g, p in gc.items()])}")
    print(f"    Hindi Thriller: {(s['genre_cluster']=='Hindi Thriller').mean()*100:.1f}%")
    print(f"    Tag Count:   {s['tag_count'].mean():.0f} avg")
    print(f"    Fashion/Beauty: {s['has_fashion_beauty'].mean()*100:.0f}%")
    print(f"    Electronics:    {s['has_electronics_tech'].mean()*100:.0f}%")
    print(f"    Travel:         {s['has_travel'].mean()*100:.0f}%")
    print(f"    Parents/Baby:   {s['has_parents_baby'].mean()*100:.0f}%")

# ============================================================
# FULL k=6 CLUSTER PROFILING WITH COMMERCIAL PROFILES
# ============================================================
print("\n" + "=" * 80)
print("k=6 CLUSTER PROFILES WITH COMMERCIAL PROFILES")
print("=" * 80)

# Strategic role assignment for k=6
platform_median = df['total_minutes'].median()

cluster_stats_6 = df.groupby('cluster_v2').agg(
    users=('uuid', 'count'),
    avg_minutes=('total_minutes', 'mean'),
    avg_mpc=('mpc', 'mean'),
    avg_active_days=('active_days', 'mean'),
    lock_survival_pct=('lock_survival', 'mean'),
    avg_shows=('unique_shows', 'mean'),
).reset_index()
cluster_stats_6['pct_total'] = cluster_stats_6['users'] / len(df) * 100

def assign_role_v2(row):
    pct = row['pct_total']
    avg_min = row['avg_minutes']
    lock_surv = row['lock_survival_pct']
    avg_days = row['avg_active_days']
    if pct > 30 and avg_min < 10:
        return 'CONVERT'
    if pct < 10 and avg_min < 5:
        return 'EXPLORE'
    if pct > 20 and avg_min < platform_median:
        return 'GROW'
    if avg_min > platform_median * 1.5 and avg_days > 4:
        return 'SUSTAIN'
    if 3 <= pct <= 25 and avg_min > platform_median and lock_surv > 0.5:
        return 'NOURISH'
    if avg_min > platform_median:
        return 'NOURISH'
    return 'GROW'

cluster_stats_6['strategic_role'] = cluster_stats_6.apply(assign_role_v2, axis=1)
role_map_v2 = cluster_stats_6.set_index('cluster_v2')['strategic_role'].to_dict()
df['strategic_role_v2'] = df['cluster_v2'].map(role_map_v2)

for cluster_id in sorted(df['cluster_v2'].unique()):
    c = df[df['cluster_v2'] == cluster_id]
    n = len(c)
    pct = n / len(df) * 100
    role = role_map_v2[cluster_id]

    print(f"\n{'=' * 70}")
    print(f"CLUSTER {cluster_id} — {role} — {n:,} users ({pct:.1f}%)")
    print(f"{'=' * 70}")

    # Engagement
    print(f"  Engagement: {c['total_minutes'].mean():.1f} min/wk | {c['mpc'].mean():.1f} MPC | "
          f"{c['active_days'].mean():.1f} days | {c['unique_shows'].mean():.1f} shows")

    # Retention
    print(f"  Retention:  {c['max_episode_depth'].mean():.0f} max ep | "
          f"{c['lock_survival'].mean()*100:.0f}% lock surv | "
          f"{c['avg_episodes_per_session'].mean():.1f} eps/sess | "
          f"{c['binge_propensity'].mean():.2f} binge")

    # Content
    gc = c['genre_cluster'].value_counts(normalize=True).head(3)
    print(f"  Content:    {', '.join([f'{g} ({p*100:.0f}%)' for g, p in gc.items()])}")
    top_s = c['top_show'].value_counts().head(3)
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

    # COMMERCIAL PROFILE (NEW — from persona tags)
    tagged_c = c[c['tag_count'] > 0]
    if len(tagged_c) > 0:
        print(f"  Commercial: Tag coverage {len(tagged_c)/n*100:.0f}% | "
              f"Avg tags {tagged_c['tag_count'].mean():.0f}")
        interest_cols = {
            'has_fashion_beauty': 'Fashion/Beauty',
            'has_electronics_tech': 'Electronics/Tech',
            'has_health_fitness': 'Health/Fitness',
            'has_home_kitchen': 'Home/Kitchen',
            'has_travel': 'Travel',
            'has_parents_baby': 'Parents/Baby',
            'has_automotive': 'Automotive',
            'has_affluent_premium': 'Affluent/Premium',
        }
        # Show top 3 interest categories by prevalence
        interest_rates = {label: tagged_c[col].mean() * 100
                         for col, label in interest_cols.items()}
        sorted_interests = sorted(interest_rates.items(), key=lambda x: -x[1])
        top3 = sorted_interests[:3]
        bot2 = sorted_interests[-2:]
        print(f"  Top Panels: {', '.join([f'{k} ({v:.0f}%)' for k, v in top3])}")
        print(f"  Low Panels: {', '.join([f'{k} ({v:.0f}%)' for k, v in bot2])}")
    else:
        print(f"  Commercial: No persona tags available")

# ============================================================
# HYPOTHESIS RE-VALIDATION (k=6)
# ============================================================
print("\n" + "=" * 80)
print("PHASE 1 HYPOTHESIS RE-VALIDATION (k=6 with persona tags)")
print("=" * 80)

hyp_summary_v2 = df.groupby('cluster_v2').agg(
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
    pct_35_plus=('age_group', lambda x: x.isin(['35-44','45-54','55-64','65+']).mean() * 100),
    pct_organic=('primary_channel', lambda x: (x == 'Organic').mean() * 100),
    pct_paid=('primary_channel', lambda x: (x == 'Paid').mean() * 100),
    pct_romance_ceo=('genre_cluster', lambda x: (x == 'Romance/CEO').mean() * 100),
    pct_empowerment=('genre_cluster', lambda x: (x == 'Empowerment').mean() * 100),
    pct_hindi_thriller=('genre_cluster', lambda x: (x == 'Hindi Thriller').mean() * 100),
    show_concentration=('show_concentration', 'mean'),
    avg_tag_count=('tag_count', 'mean'),
    pct_fashion=('has_fashion_beauty', 'mean'),
    pct_electronics=('has_electronics_tech', 'mean'),
    pct_travel=('has_travel', 'mean'),
    pct_parents=('has_parents_baby', 'mean'),
).round(1)

print("\nCluster Summary (k=6):")
print(hyp_summary_v2.to_string())

hypotheses = {
    'P1: Young Female Romance Binger [GROW]': {
        'criteria': lambda r: (r['pct_female'] > 55 and r['pct_18_24'] > 35
                               and r['avg_mpc'] > 20 and r['pct_romance_ceo'] > 30),
    },
    'P2: Male Crossover Viewer [GROW]': {
        'criteria': lambda r: (r['pct_male'] > 55 and r['pct_25_34'] > 30
                               and r['avg_mpc'] > 5),
    },
    'P3: Discovery Sampler [CONVERT]': {
        'criteria': lambda r: (r['pct_total'] > 20 and r['avg_minutes'] < 15
                               and r['avg_shows'] < 2),
    },
    'P4: Multi-Show Power User [NOURISH]': {
        'criteria': lambda r: (r['avg_shows'] > 3 and r['avg_minutes'] > 80
                               and r['lock_survival_pct'] > 60),
    },
    'P5: Mature Loyal Viewer [SUSTAIN]': {
        'criteria': lambda r: (r['pct_35_plus'] > 20 and r['avg_mpc'] > 10
                               and r['pct_organic'] > 40),
    },
    'P6: Hindi Content Explorer [EXPLORE]': {
        'criteria': lambda r: (r['pct_hindi_thriller'] > 10 and r['avg_minutes'] < 15),
    },
}

validated = 0
for hyp_name, hyp in hypotheses.items():
    matched = [int(row.name) for _, row in hyp_summary_v2.iterrows() if hyp['criteria'](row)]
    if matched:
        validated += 1
        print(f"  ✅ {hyp_name} → Cluster(s): {matched}")
    else:
        print(f"  ❌ {hyp_name}")

print(f"\nValidated: {validated}/6 (target: ≥4)")

# ============================================================
# PERSONA CARD GENERATION v2 (with commercial profiles)
# ============================================================
print("\n" + "=" * 80)
print("PERSONA CARDS v2")
print("=" * 80)

def suggest_name_v2(row, cluster_df):
    role = role_map_v2[row.name]
    top_gender = cluster_df['gender'].mode().iloc[0] if len(cluster_df['gender'].mode()) > 0 else 'Mixed'
    top_age = cluster_df['age_group'].mode().iloc[0] if len(cluster_df['age_group'].mode()) > 0 else 'Mixed'
    top_genre = cluster_df['genre_cluster'].mode().iloc[0] if len(cluster_df['genre_cluster'].mode()) > 0 else 'Mixed'

    if role == 'CONVERT' and row['avg_shows'] < 2:
        if row['pct_male'] > 55:
            return "Male Discovery Sampler"
        return "Discovery Sampler"
    if role == 'EXPLORE':
        if row['pct_hindi_thriller'] > 10:
            return "Hindi Content Explorer"
        return "Casual Explorer"
    if top_gender == 'Female' and top_age == '18-24' and 'Romance' in top_genre:
        if row['avg_shows'] > 5:
            return "Multi-Show Power User"
        return "Young Female Romance Binger"
    if top_gender == 'Male' and top_age == '25-34':
        return "Male Crossover Viewer"
    if row['pct_35_plus'] > 25 and row['pct_organic'] > 50:
        return "Mature Loyal Viewer"
    if row['avg_shows'] > 3 and row['avg_minutes'] > 80:
        return "Multi-Show Power User"
    if role == 'SUSTAIN':
        return "Platform Devotee"
    return f"{top_gender} {top_age} {top_genre} Viewer"

cards = []
for cluster_id in sorted(df['cluster_v2'].unique()):
    c = df[df['cluster_v2'] == cluster_id]
    n = len(c)
    pct = n / len(df) * 100
    role = role_map_v2[cluster_id]
    row = hyp_summary_v2.loc[cluster_id]
    name = suggest_name_v2(row, c)

    top_shows_list = c['top_show'].value_counts().head(3)
    top_shows_str = ", ".join([f"{s} ({cnt:,})" for s, cnt in top_shows_list.items()])

    gc = c['genre_cluster'].value_counts(normalize=True).head(3)
    gc_str = ", ".join([f"{g} ({p*100:.0f}%)" for g, p in gc.items()])

    ag = c['age_gender'].value_counts(normalize=True).head(3)
    ag_str = ", ".join([f"{a} ({p*100:.0f}%)" for a, p in ag.items()])

    ch = c['primary_channel'].value_counts(normalize=True)
    ch_str = ", ".join([f"{k} ({v*100:.0f}%)" for k, v in ch.head(4).items()])

    # Commercial profile from persona tags
    tagged_c = c[c['tag_count'] > 0]
    if len(tagged_c) > 0:
        interest_cols = {
            'has_fashion_beauty': 'Fashion/Beauty',
            'has_electronics_tech': 'Electronics/Tech',
            'has_health_fitness': 'Health/Fitness',
            'has_home_kitchen': 'Home/Kitchen',
            'has_travel': 'Travel',
            'has_parents_baby': 'Parents/Baby',
            'has_automotive': 'Automotive',
            'has_affluent_premium': 'Affluent/Premium',
        }
        rates = {label: tagged_c[col].mean() * 100 for col, label in interest_cols.items()}
        sorted_r = sorted(rates.items(), key=lambda x: -x[1])
        top3_panels = ", ".join([f"{k} ({v:.0f}%)" for k, v in sorted_r[:3]])
        commercial_str = (f"Tag Coverage: {len(tagged_c)/n*100:.0f}% | "
                         f"Avg Tags: {tagged_c['tag_count'].mean():.0f}\n"
                         f"    Top Panels: {top3_panels}")
    else:
        commercial_str = "No persona tags available"

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
    Show Focus:  {row['show_concentration']*100:.0f}% concentration ({"loyal" if row['show_concentration'] > 0.6 else "explorer"})

  DEMOGRAPHIC PROFILE:
    Gender:      {row['pct_female']:.0f}% F / {row['pct_male']:.0f}% M
    Age:         {row['pct_18_24']:.0f}% 18-24 | {row['pct_25_34']:.0f}% 25-34 | {row['pct_35_plus']:.0f}% 35+
    Top Cells:   {ag_str}

  CHANNEL PROFILE:
    {ch_str}

  COMMERCIAL PROFILE:
    {commercial_str}

  COVERAGE: {pct:.1f}% of active Fatafat audience
"""
    cards.append(card)
    print(card)

# Export
with open("persona_cards_v2.txt", "w") as f:
    f.write("FATAFAT SYNTHETIC PERSONAS — PHASE 2.1 PERSONA CARDS\n")
    f.write(f"Generated: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}\n")
    f.write(f"Clustering: K-Means k=6, Silhouette={sil_6:.4f}\n")
    f.write(f"Hierarchical ARI: {ari_6:.4f}\n")
    f.write(f"Hypotheses Validated: {validated}/6\n")
    f.write(f"Persona Tags: {tag_coverage:.1f}% coverage\n")
    for card in cards:
        f.write(card)
print(f"\n✅ Persona cards v2 exported to: persona_cards_v2.txt")

# Export updated feature matrix
df.to_csv("fatafat_personas_phase2_1.csv", index=False)
print(f"✅ Updated feature matrix exported to: fatafat_personas_phase2_1.csv")

# Final metrics
print(f"\n📊 PHASE 2.1 SUCCESS METRICS:")
print(f"   Persona Coverage:       100% (k-means assigns all)")
print(f"   Silhouette Score (k=6): {sil_6:.4f} (target: ≥0.3)")
print(f"   Hierarchical ARI:       {ari_6:.4f}")
print(f"   Hypotheses Validated:   {validated}/6 (target: ≥4)")
print(f"   Demographic Overlay:    {(df['age_group'] != 'Unknown').mean()*100:.1f}%")
print(f"   Persona Tag Coverage:   {tag_coverage:.1f}%")
print(f"   Sampler Sub-Clusters:   {SUB_K} segments identified")
