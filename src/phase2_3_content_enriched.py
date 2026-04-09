"""
Phase 2.3: Secondary Genre One-Hot + Content Archetype Derivation
=================================================================
Key change: secondary_genre_name used as direct one-hot clustering features
(18 values) instead of collapsed genre_cluster. Post-clustering derives
content archetypes from top shows per cluster.

Input: All existing CSVs + q22b_cms_enriched.csv
Output: fatafat_personas_phase2_3.csv, persona_cards_v4.txt
"""

import pandas as pd
import numpy as np
import os
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans, AgglomerativeClustering
from sklearn.metrics import silhouette_score, adjusted_rand_score
import warnings
warnings.filterwarnings('ignore')

DIR = os.path.dirname(os.path.abspath(__file__))

print("=" * 80)
print("PHASE 2.3: Secondary Genre One-Hot + Content Archetypes")
print("=" * 80)

# ============================================================
# LOAD DATA
# ============================================================
print("\n--- Loading ---")
eng = pd.read_csv(os.path.join(DIR, "q21_engagement.csv"))
uv = pd.read_csv(os.path.join(DIR, "q22a_user_video.csv"))
cms = pd.read_csv(os.path.join(DIR, "q22b_cms_enriched.csv"))
sess = pd.read_csv(os.path.join(DIR, "q23_session_episodes.csv"))
demo = pd.read_csv(os.path.join(DIR, "q24a_demographics.csv"))
channel = pd.read_csv(os.path.join(DIR, "q24b_channel.csv"))
tags_path = os.path.join(DIR, "q25_persona_tags.csv")
has_tags = os.path.exists(tags_path)
tag_df = pd.read_csv(tags_path) if has_tags else None
print(f"  {len(eng):,} users | {len(uv):,} user×video | {len(cms):,} CMS")

# ============================================================
# CLEAN CMS
# ============================================================
for col in ['tv_show_name', 'genre_name', 'secondary_genre_name',
            'language_name', 'tag_name', 'original_acquired']:
    cms[col] = cms[col].astype(str).str.strip('[]').replace({'None': 'Unknown', 'nan': 'Unknown', '': 'Unknown'})

cms['episode_num_int'] = pd.to_numeric(
    cms['episode_number'].astype(str).str.strip('[]'), errors='coerce').fillna(0).astype(int)

# Content source
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

# Normalize secondary genre for one-hot
cms['sec_genre'] = cms['secondary_genre_name'].apply(
    lambda x: x if x in [
        'Edgy', 'Forbidden Love', 'Secret Lives', 'Revenge', 'Second Chances',
        'Melodrama', 'Inheritance', 'Crime', 'Pulp', 'Inspiring',
        'Hidden Identity', 'Time Travel', 'Horror', 'Mythical Action',
        'Creature Romance'
    ] else 'Other'
)

print(f"  Secondary genre distribution (shows):")
print(cms.groupby('sec_genre')['channel_ids'].nunique().sort_values(ascending=False).to_string())

# ============================================================
# JOIN + BUILD FEATURES
# ============================================================
print("\n--- Building Features ---")

# Join user×video with CMS
uv = uv.merge(cms[['video_id', 'tv_show_name', 'channel_ids', 'genre_name',
                     'sec_genre', 'content_source', 'content_origin',
                     'episode_num_int']].drop_duplicates(),
               left_on='videoid', right_on='video_id', how='left')

# DIM 1: Engagement
eng['mpc'] = eng['total_minutes'] / eng['active_days'].clip(lower=1)
eng['minutes_per_stream'] = eng['total_minutes'] / eng['total_streams'].clip(lower=1)
eng['streams_per_day'] = eng['total_streams'] / eng['active_days'].clip(lower=1)
eng['episodes_per_session'] = eng['unique_episodes'] / eng['total_sessions'].clip(lower=1)
eng['engagement_tier'] = pd.qcut(eng['total_minutes'], q=5,
    labels=['Sampler', 'Light', 'Moderate', 'Heavy', 'Binge'], duplicates='drop')

# DIM 2: Content — per user top show + secondary genre
user_show = (uv.groupby(['uuid', 'channel_ids', 'tv_show_name', 'genre_name',
                          'sec_genre', 'content_source', 'content_origin'])
             .agg(show_min=('minutes', 'sum')).reset_index()
             .sort_values('show_min', ascending=False)
             .groupby('uuid').first().reset_index())

content = uv.groupby('uuid').agg(
    unique_shows=('channel_ids', 'nunique'),
    genre_breadth=('genre_name', 'nunique'),
    sec_genre_breadth=('sec_genre', 'nunique'),
    total_min=('minutes', 'sum')
).reset_index()

user_show['show_concentration'] = (
    user_show['show_min'] / content.set_index('uuid')['total_min']
    .reindex(user_show['uuid']).values.clip(min=0.01))

content = content.merge(
    user_show[['uuid', 'tv_show_name', 'genre_name', 'sec_genre',
               'content_source', 'content_origin', 'show_concentration']],
    on='uuid', how='left')
content = content.rename(columns={
    'tv_show_name': 'top_show', 'genre_name': 'top_genre',
    'sec_genre': 'top_sec_genre', 'content_source': 'top_source',
    'content_origin': 'top_origin'})
content.drop(columns=['total_min'], inplace=True)

# Per-user secondary genre watchtime distribution (for one-hot)
# Compute fraction of watchtime per secondary genre per user
sec_genre_wt = uv.groupby(['uuid', 'sec_genre'])['minutes'].sum().reset_index()
sec_genre_total = sec_genre_wt.groupby('uuid')['minutes'].sum().reset_index().rename(columns={'minutes': 'total'})
sec_genre_wt = sec_genre_wt.merge(sec_genre_total, on='uuid')
sec_genre_wt['frac'] = sec_genre_wt['minutes'] / sec_genre_wt['total'].clip(lower=0.01)

# Pivot to wide format: one column per secondary genre
sec_pivot = sec_genre_wt.pivot_table(index='uuid', columns='sec_genre', values='frac', fill_value=0)
sec_pivot.columns = ['sg_' + c.replace(' ', '_') for c in sec_pivot.columns]
sec_pivot = sec_pivot.reset_index()

print(f"  Secondary genre features: {len(sec_pivot.columns)-1} columns for {len(sec_pivot):,} users")

# DIM 3: Retention
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

# DIM 4: Demographics
demo['age_group'] = demo['age_group'].fillna('Unknown')
demo['gender'] = demo['gender'].fillna('Unknown')
demo['age_gender'] = demo['gender'].str[0] + '_' + demo['age_group']
demo.loc[demo['gender'] == 'Unknown', 'age_gender'] = 'Unknown'

print(f"  All dimensions built")

# ============================================================
# MERGE ALL
# ============================================================
print("\n--- Merging ---")
df = eng[['uuid', 'total_streams', 'total_minutes', 'unique_episodes',
          'active_days', 'total_sessions', 'mpc', 'minutes_per_stream',
          'streams_per_day', 'episodes_per_session', 'engagement_tier']].copy()

df = df.merge(content, on='uuid', how='left')
df = df.merge(sec_pivot, on='uuid', how='left')
df = df.merge(retention, on='uuid', how='left')
df = df.merge(demo, on='uuid', how='left')
df = df.merge(channel, on='uuid', how='left')
if tag_df is not None:
    df = df.merge(tag_df, on='uuid', how='left')
    df['tag_count'] = df['tag_count'].fillna(0).astype(int)
    for c in [x for x in tag_df.columns if x.startswith('has_')]:
        df[c] = df[c].fillna(0).astype(int)

# Fill missing
for col, val in {'age_group': 'Unknown', 'gender': 'Unknown', 'age_gender': 'Unknown',
                  'primary_channel': 'Organic', 'top_sec_genre': 'Unknown',
                  'top_source': 'Unknown', 'top_origin': 'Unknown',
                  'unique_shows': 1, 'genre_breadth': 1, 'sec_genre_breadth': 1,
                  'show_concentration': 1.0, 'max_episode_depth': 1,
                  'avg_episode_depth': 1, 'lock_survival': 0,
                  'avg_eps_sess': 1, 'max_eps_sess': 1, 'binge_propensity': 1.0}.items():
    if col in df.columns:
        df[col] = df[col].fillna(val)

# Fill secondary genre fraction columns
sg_cols = [c for c in df.columns if c.startswith('sg_')]
for c in sg_cols:
    df[c] = df[c].fillna(0)

print(f"  Matrix: {len(df):,} users × {len(df.columns)} columns")

# ============================================================
# CLUSTERING FEATURES
# ============================================================
print("\n--- Clustering Features ---")

numeric_features = [
    'total_minutes', 'mpc', 'unique_episodes', 'active_days',
    'minutes_per_stream', 'streams_per_day',
    'unique_shows', 'genre_breadth', 'sec_genre_breadth', 'show_concentration',
    'max_episode_depth', 'avg_episode_depth', 'lock_survival',
    'avg_eps_sess', 'binge_propensity',
] + sg_cols  # Secondary genre fractions as numeric features

if tag_df is not None:
    numeric_features += ['tag_count'] + [c for c in tag_df.columns if c.startswith('has_')]

cat_features = ['gender', 'age_group', 'primary_channel', 'top_source', 'top_origin']
df_enc = pd.get_dummies(df[cat_features], prefix=cat_features, drop_first=False)

X_num = df[numeric_features].values
X_cat = df_enc.values
scaler = StandardScaler()
X_num_s = scaler.fit_transform(X_num)
X = np.hstack([X_num_s, X_cat])

print(f"  Shape: {X.shape} ({len(numeric_features)} numeric + {X_cat.shape[1]} one-hot)")
print(f"  Secondary genre features: {len(sg_cols)}")

# ============================================================
# K-MEANS
# ============================================================
print("\n--- Clustering ---")
N = min(50000, len(X))
np.random.seed(42)
idx = np.random.choice(len(X), N, replace=False)
Xs = X[idx]

print("K selection:")
for k in range(4, 9):
    km = KMeans(n_clusters=k, random_state=42, n_init=10, max_iter=300)
    lb = km.fit_predict(Xs)
    s = silhouette_score(Xs, lb, sample_size=min(10000, N))
    print(f"  k={k}: Sil={s:.4f}")

K = 6
print(f"\nFinal k={K}...")
kmeans = KMeans(n_clusters=K, random_state=42, n_init=20, max_iter=500)
df['cluster'] = kmeans.fit_predict(X)

sil = silhouette_score(Xs, kmeans.predict(Xs), sample_size=min(10000, N))
agg = AgglomerativeClustering(n_clusters=K, linkage='ward')
ari = adjusted_rand_score(kmeans.predict(Xs), agg.fit_predict(Xs))
print(f"Silhouette: {sil:.4f} | ARI: {ari:.4f}")

for cid in sorted(df['cluster'].unique()):
    n = (df['cluster'] == cid).sum()
    print(f"  Cluster {cid}: {n:,} ({n/len(df)*100:.1f}%)")

# ============================================================
# ROLE ASSIGNMENT
# ============================================================
print("\n--- Roles ---")
med = df['total_minutes'].median()
cs = df.groupby('cluster').agg(
    n=('uuid', 'count'), avg_min=('total_minutes', 'mean'),
    mpc=('mpc', 'mean'), days=('active_days', 'mean'),
    lock=('lock_survival', 'mean'), shows=('unique_shows', 'mean')).reset_index()
cs['pct'] = cs['n'] / len(df) * 100

def role(r):
    if r['pct'] > 30 and r['avg_min'] < 10: return 'CONVERT'
    if r['pct'] < 10 and r['avg_min'] < 5: return 'EXPLORE'
    if r['pct'] > 15 and r['avg_min'] < med: return 'GROW'
    if r['avg_min'] > med * 1.5 and r['days'] > 4: return 'SUSTAIN'
    if r['avg_min'] > med and r['lock'] > 0.5: return 'NOURISH'
    if r['avg_min'] > med: return 'NOURISH'
    return 'GROW'

cs['role'] = cs.apply(role, axis=1)
rmap = cs.set_index('cluster')['role'].to_dict()
df['role'] = df['cluster'].map(rmap)

for _, r in cs.iterrows():
    print(f"  C{int(r['cluster'])}: {rmap[r['cluster']]:8s} | {r['n']:>10,.0f} ({r['pct']:.1f}%) | "
          f"min={r['avg_min']:.1f} | MPC={r['mpc']:.1f} | lock={r['lock']*100:.0f}% | shows={r['shows']:.1f}")

# ============================================================
# CONTENT ARCHETYPE DERIVATION (Level 2)
# ============================================================
print("\n" + "=" * 80)
print("CONTENT ARCHETYPE DERIVATION")
print("=" * 80)

# For each cluster, analyze top 10 shows + their genres to derive archetype
archetype_map = {}
for cid in sorted(df['cluster'].unique()):
    c = df[df['cluster'] == cid]
    n = len(c)
    if n < 10:
        archetype_map[cid] = "Outlier"
        continue

    # Top 10 shows
    top10 = c['top_show'].value_counts().head(10)

    # Secondary genre distribution
    sg_dist = c['top_sec_genre'].value_counts(normalize=True)
    top_sg = sg_dist.index[0] if len(sg_dist) > 0 else 'Unknown'
    top_sg_pct = sg_dist.iloc[0] * 100 if len(sg_dist) > 0 else 0

    # Content source
    src_dist = c['top_source'].value_counts(normalize=True)
    top_src = src_dist.index[0] if len(src_dist) > 0 else 'Unknown'

    # Origin
    orig_dist = c['top_origin'].value_counts(normalize=True)

    # Derive archetype from show names + genres
    show_names = ' '.join(top10.index.tolist()).lower()
    ceo_signals = sum(1 for s in top10.index if any(w in s.lower() for w in ['ceo', 'billionaire', 'president', 'boss', 'rich']))
    revenge_signals = sum(1 for s in top10.index if any(w in s.lower() for w in ['revenge', 'badla', 'funeral', 'murder', 'kill']))
    love_signals = sum(1 for s in top10.index if any(w in s.lower() for w in ['love', 'heart', 'kiss', 'marriage', 'wife', 'husband']))
    empower_signals = sum(1 for s in top10.index if any(w in s.lower() for w in ['strength', 'alone', 'unbossed', 'chain', 'rising']))
    hindi_signals = sum(1 for s in top10.index if any(w in s.lower() for w in ['aashram', 'bhaukaal', 'jaunpur', 'desi', 'pagal']))
    mystery_signals = sum(1 for s in top10.index if any(w in s.lower() for w in ['secret', 'mystery', 'moonlight', 'scent', 'hidden']))

    # Score-based archetype assignment
    scores = {
        'CEO/Billionaire Romance': ceo_signals * 2 + (1 if top_sg in ('Edgy', 'Forbidden Love') else 0),
        'Epic Forbidden Love': love_signals + (2 if top_sg == 'Forbidden Love' else 0),
        'Revenge & Power Drama': revenge_signals * 2 + (2 if top_sg == 'Revenge' else 0),
        'Female Empowerment': empower_signals * 2 + (2 if top_sg in ('Melodrama', 'Inspiring') else 0),
        'Hindi Crime/Thriller': hindi_signals * 2 + (2 if top_sg == 'Crime' else 0),
        'Mystery & Secret Lives': mystery_signals * 2 + (2 if top_sg == 'Secret Lives' else 0),
        'Hook-Driven Sampler Content': 3 if (c['total_minutes'].mean() < 5 and top_sg == 'Edgy') else 0,
    }
    archetype = max(scores, key=scores.get)
    if max(scores.values()) == 0:
        archetype = f"{top_sg} Content"

    archetype_map[cid] = archetype

    print(f"\nCluster {cid} ({rmap[cid]}, {n:,} users):")
    print(f"  Archetype: {archetype}")
    print(f"  Top secondary genre: {top_sg} ({top_sg_pct:.0f}%)")
    print(f"  Source: {top_src} ({src_dist.iloc[0]*100:.0f}%)")
    print(f"  Show signals: CEO={ceo_signals} Love={love_signals} Revenge={revenge_signals} "
          f"Empower={empower_signals} Hindi={hindi_signals} Mystery={mystery_signals}")
    print(f"  Top 10 shows:")
    for s, cnt in top10.items():
        print(f"    {s}: {cnt:,}")

df['archetype'] = df['cluster'].map(archetype_map)

# ============================================================
# FULL PROFILES + PERSONA CARDS
# ============================================================
print("\n" + "=" * 80)
print("CLUSTER PROFILES — TWO-LEVEL CONTENT IDENTITY")
print("=" * 80)

cards = []
for cid in sorted(df['cluster'].unique()):
    c = df[df['cluster'] == cid]
    n = len(c)
    if n < 10: continue
    pct = n / len(df) * 100
    r = rmap[cid]
    arch = archetype_map[cid]

    # Secondary genre distribution (Level 1)
    sg = c['top_sec_genre'].value_counts(normalize=True).head(5)
    sg_str = ', '.join([f"{g} ({p*100:.0f}%)" for g, p in sg.items()])

    # Source + origin
    src = c['top_source'].value_counts(normalize=True).head(3)
    src_str = ', '.join([f"{s} ({p*100:.0f}%)" for s, p in src.items()])
    orig = c['top_origin'].value_counts(normalize=True)
    orig_str = ', '.join([f"{o} ({p*100:.0f}%)" for o, p in orig.items()])

    # Top shows
    top_s = c['top_show'].value_counts().head(5)
    shows_str = ', '.join([f"{s} ({cnt:,})" for s, cnt in top_s.items()])

    # Demographics
    f_pct = (c['gender'] == 'Female').mean() * 100
    m_pct = (c['gender'] == 'Male').mean() * 100
    a18 = (c['age_group'] == '18-24').mean() * 100
    a25 = (c['age_group'] == '25-34').mean() * 100
    a35p = c['age_group'].isin(['35-44', '45-54', '55-64', '65+']).mean() * 100
    ag = c['age_gender'].value_counts(normalize=True).head(3)
    ag_str = ', '.join([f"{a} ({p*100:.0f}%)" for a, p in ag.items()])

    # Channel
    org = (c['primary_channel'] == 'Organic').mean() * 100
    paid = (c['primary_channel'] == 'Paid').mean() * 100
    push = (c['primary_channel'] == 'Push').mean() * 100

    # Commercial
    comm_str = "N/A"
    if tag_df is not None:
        tagged = c[c['tag_count'] > 0]
        if len(tagged) > 100:
            ic = {'has_fashion_beauty': 'Fashion/Beauty', 'has_electronics_tech': 'Electronics/Tech',
                  'has_health_fitness': 'Health/Fitness', 'has_home_kitchen': 'Home/Kitchen',
                  'has_travel': 'Travel', 'has_parents_baby': 'Parents/Baby',
                  'has_automotive': 'Automotive', 'has_affluent_premium': 'Affluent/Premium'}
            rates = sorted([(v, tagged[k].mean()*100) for k, v in ic.items() if k in tagged.columns],
                          key=lambda x: -x[1])
            comm_str = f"Tags {len(tagged)/n*100:.0f}% | {', '.join([f'{k} ({v:.0f}%)' for k, v in rates[:3]])}"

    print(f"\n{'='*70}")
    print(f"CLUSTER {cid} — {r} — {arch}")
    print(f"{n:,} users ({pct:.1f}%)")
    print(f"{'='*70}")
    print(f"  ENGAGEMENT:  {c['total_minutes'].mean():.1f} min/wk | {c['mpc'].mean():.1f} MPC | "
          f"{c['active_days'].mean():.1f} days | {c['unique_shows'].mean():.1f} shows")
    print(f"  RETENTION:   {c['max_episode_depth'].mean():.0f} max ep | "
          f"{c['lock_survival'].mean()*100:.0f}% lock | "
          f"{c['avg_eps_sess'].mean():.1f} eps/sess | {c['binge_propensity'].mean():.2f} binge")
    print(f"  CONTENT L1:  {sg_str}")
    print(f"  CONTENT L2:  {arch}")
    print(f"  SOURCE:      {src_str}")
    print(f"  ORIGIN:      {orig_str}")
    print(f"  TOP SHOWS:   {shows_str}")
    print(f"  DEMO:        {f_pct:.0f}% F / {m_pct:.0f}% M | {a18:.0f}% 18-24 | {a25:.0f}% 25-34 | {a35p:.0f}% 35+")
    print(f"  TOP CELLS:   {ag_str}")
    print(f"  CHANNEL:     Organic {org:.0f}% | Paid {paid:.0f}% | Push {push:.0f}%")
    print(f"  COMMERCIAL:  {comm_str}")

    card = f"""{'='*70}
CLUSTER {cid} — {r} — {arch}
{n:,} users ({pct:.1f}%)
{'='*70}

  ENGAGEMENT:  {c['total_minutes'].mean():.0f} min/wk | {c['mpc'].mean():.0f} MPC | {c['active_days'].mean():.1f} days | {c['unique_shows'].mean():.1f} shows
  RETENTION:   {c['max_episode_depth'].mean():.0f} max ep | {c['lock_survival'].mean()*100:.0f}% lock | {c['avg_eps_sess'].mean():.1f} eps/sess
  CONTENT L1 (Theme):  {sg_str}
  CONTENT L2 (Archetype):  {arch}
  SOURCE:      {src_str}
  ORIGIN:      {orig_str}
  TOP SHOWS:   {shows_str}
  DEMO:        {f_pct:.0f}% F / {m_pct:.0f}% M | {a18:.0f}% 18-24 | {a25:.0f}% 25-34 | {a35p:.0f}% 35+
  TOP CELLS:   {ag_str}
  CHANNEL:     Organic {org:.0f}% | Paid {paid:.0f}% | Push {push:.0f}%
  COMMERCIAL:  {comm_str}

"""
    cards.append(card)

# ============================================================
# HYPOTHESIS VALIDATION
# ============================================================
print("\n" + "=" * 80)
print("HYPOTHESIS VALIDATION")
print("=" * 80)

hs = df.groupby('cluster').agg(
    n=('uuid', 'count'), pct=('uuid', lambda x: len(x)/len(df)*100),
    avg_min=('total_minutes', 'mean'), mpc=('mpc', 'mean'),
    shows=('unique_shows', 'mean'), lock=('lock_survival', lambda x: x.mean()*100),
    pf=('gender', lambda x: (x=='Female').mean()*100),
    pm=('gender', lambda x: (x=='Male').mean()*100),
    p18=('age_group', lambda x: (x=='18-24').mean()*100),
    p25=('age_group', lambda x: (x=='25-34').mean()*100),
    p35=('age_group', lambda x: x.isin(['35-44','45-54','55-64','65+']).mean()*100),
    porg=('primary_channel', lambda x: (x=='Organic').mean()*100),
    pintl=('top_origin', lambda x: (x=='International').mean()*100),
    phindi=('top_origin', lambda x: (x=='Hindi').mean()*100),
).round(1)
print(hs.to_string())

hyps = {
    'P1: Young Female Romance Binger': lambda r: r['pf']>55 and r['p18']>35 and r['mpc']>20,
    'P2: Male Crossover Viewer': lambda r: r['pm']>55 and r['p25']>30,
    'P3: Discovery Sampler': lambda r: r['pct']>20 and r['avg_min']<15 and r['shows']<2,
    'P4: Multi-Show Power User': lambda r: r['shows']>3 and r['avg_min']>80 and r['lock']>60,
    'P5: Mature Loyal Viewer': lambda r: r['p35']>20 and r['mpc']>10 and r['porg']>40,
    'P6: Hindi Content Explorer': lambda r: r['phindi']>50 and r['avg_min']<15,
}
val = 0
for name, fn in hyps.items():
    m = [int(r.name) for _, r in hs.iterrows() if fn(r)]
    if m:
        val += 1
        print(f"  ✅ {name} → C{m}")
    else:
        print(f"  ❌ {name}")
print(f"\nValidated: {val}/6")

# ============================================================
# EXPORT
# ============================================================
print("\n--- Export ---")
df.to_csv(os.path.join(DIR, "fatafat_personas_phase2_3.csv"), index=False)

with open(os.path.join(DIR, "persona_cards_v4.txt"), 'w') as f:
    f.write(f"FATAFAT SYNTHETIC PERSONAS — PHASE 2.3\n")
    f.write(f"Secondary Genre One-Hot + Content Archetypes\n")
    f.write(f"K={K} | Sil={sil:.4f} | ARI={ari:.4f} | Hyp={val}/6\n")
    f.write(f"Features: {X.shape[1]} ({len(numeric_features)} numeric + {X_cat.shape[1]} one-hot)\n\n")
    for card in cards:
        f.write(card)

print(f"  ✅ fatafat_personas_phase2_3.csv")
print(f"  ✅ persona_cards_v4.txt")
print(f"\n📊 PHASE 2.3 METRICS:")
print(f"   Silhouette: {sil:.4f} | ARI: {ari:.4f} | Hypotheses: {val}/6")
print(f"   Features: {X.shape[1]} (incl {len(sg_cols)} secondary genre fractions)")
