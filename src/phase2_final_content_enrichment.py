"""
Phase 2 Final: Content Identity Enrichment on Phase 2.2 Clusters
================================================================
Takes the Phase 2.2 clusters (strongest statistical model: sil=0.43, ARI=0.75)
and adds two-level content identity as post-clustering enrichment:
  Level 1: Secondary genre distribution per cluster
  Level 2: Content archetype derived from top shows

Input: fatafat_personas_phase2_2.csv, q22a_user_video.csv, q22b_cms_enriched.csv
Output: fatafat_personas_final.csv, persona_cards_final.txt
"""

import pandas as pd
import numpy as np
import os
import warnings
warnings.filterwarnings('ignore')

DIR = os.path.dirname(os.path.abspath(__file__))

print("=" * 80)
print("PHASE 2 FINAL: Content Identity Enrichment")
print("=" * 80)

# ============================================================
# LOAD
# ============================================================
print("\n--- Loading ---")
df = pd.read_csv(os.path.join(DIR, "fatafat_personas_phase2_2.csv"))
uv = pd.read_csv(os.path.join(DIR, "q22a_user_video.csv"))
cms = pd.read_csv(os.path.join(DIR, "q22b_cms_enriched.csv"))

print(f"  {len(df):,} users with Phase 2.2 clusters")
print(f"  {len(uv):,} user×video rows")
print(f"  {len(cms):,} CMS rows")

# Clean CMS
for col in ['tv_show_name', 'genre_name', 'secondary_genre_name',
            'language_name', 'tag_name', 'original_acquired']:
    cms[col] = cms[col].astype(str).str.strip('[]').replace({'None': 'Unknown', 'nan': 'Unknown', '': 'Unknown'})

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

# Normalize secondary genre
cms['sec_genre'] = cms['secondary_genre_name'].apply(
    lambda x: x if x in [
        'Edgy', 'Forbidden Love', 'Secret Lives', 'Revenge', 'Second Chances',
        'Melodrama', 'Inheritance', 'Crime', 'Pulp', 'Inspiring',
        'Hidden Identity', 'Time Travel', 'Horror', 'Mythical Action'
    ] else 'Other')

# Join user×video with CMS
uv = uv.merge(cms[['video_id', 'tv_show_name', 'channel_ids', 'genre_name',
                     'sec_genre', 'content_source', 'content_origin']].drop_duplicates(),
               left_on='videoid', right_on='video_id', how='left')

# Get cluster assignment per user
cluster_col = 'cluster_v2' if 'cluster_v2' in df.columns else 'cluster'
uv = uv.merge(df[['uuid', cluster_col]], on='uuid', how='inner')
uv = uv.rename(columns={cluster_col: 'cluster_id'})
df = df.rename(columns={cluster_col: 'cluster_id'})
print(f"  Joined: {len(uv):,} user×video rows with clusters")

# ============================================================
# LEVEL 1: Secondary Genre Distribution per Cluster
# ============================================================
print("\n" + "=" * 80)
print("LEVEL 1: Secondary Genre Distribution")
print("=" * 80)

# Compute per-cluster secondary genre distribution (by watchtime)
cluster_sg = (uv.groupby(['cluster_id', 'sec_genre'])['minutes']
              .sum().reset_index()
              .rename(columns={'minutes': 'wt_min'}))
cluster_total = cluster_sg.groupby('cluster_id')['wt_min'].sum().reset_index().rename(columns={'wt_min': 'total'})
cluster_sg = cluster_sg.merge(cluster_total, on='cluster_id')
cluster_sg['pct'] = (cluster_sg['wt_min'] / cluster_sg['total'] * 100).round(1)

for cid in sorted(df['cluster_id'].unique()):
    sg = cluster_sg[cluster_sg['cluster_id'] == cid].sort_values('pct', ascending=False)
    n = (df['cluster_id'] == cid).sum()
    if n < 10: continue
    print(f"\n  Cluster {cid} ({n:,} users) — Secondary Genre by Watchtime:")
    for _, row in sg.head(8).iterrows():
        bar = '█' * int(row['pct'] / 2)
        print(f"    {row['sec_genre']:20s} {row['pct']:5.1f}% {bar}")

# ============================================================
# LEVEL 1b: Content Source + Origin per Cluster
# ============================================================
print("\n" + "=" * 80)
print("LEVEL 1b: Content Source & Origin")
print("=" * 80)

for cid in sorted(df['cluster_id'].unique()):
    c_uv = uv[uv['cluster_id'] == cid]
    n = (df['cluster_id'] == cid).sum()
    if n < 10: continue

    src_dist = c_uv.groupby('content_source')['minutes'].sum()
    src_pct = (src_dist / src_dist.sum() * 100).sort_values(ascending=False)

    orig_dist = c_uv.groupby('content_origin')['minutes'].sum()
    orig_pct = (orig_dist / orig_dist.sum() * 100).sort_values(ascending=False)

    print(f"\n  Cluster {cid}:")
    print(f"    Source: {', '.join([f'{s} ({p:.0f}%)' for s, p in src_pct.head(4).items()])}")
    print(f"    Origin: {', '.join([f'{o} ({p:.0f}%)' for o, p in orig_pct.items()])}")

# ============================================================
# LEVEL 2: Content Archetype from Top Shows
# ============================================================
print("\n" + "=" * 80)
print("LEVEL 2: Content Archetype Derivation")
print("=" * 80)

# Show-level aggregation per cluster
show_cluster = (uv.groupby(['cluster_id', 'tv_show_name', 'genre_name', 'sec_genre', 'content_source'])
                .agg(users=('uuid', 'nunique'), wt=('minutes', 'sum'))
                .reset_index()
                .sort_values(['cluster_id', 'users'], ascending=[True, False]))

archetype_keywords = {
    'CEO/Billionaire Romance': ['ceo', 'billionaire', 'president', 'boss', 'rich', 'huo', 'lucky trio'],
    'Forbidden Love Epic': ['ocean of stars', 'royal', 'closer', 'ancient', 'forbidden', 'distant love'],
    'Female Empowerment': ['unbossed', 'strength', 'alone', 'chain', 'rising', 'divorce sisters', 'raised our child'],
    'Revenge & Power': ['funeral', 'murder', 'badla', 'revenge', 'betrayal', 'jaunpur', 'collector'],
    'Hindi Crime/Thriller': ['aashram', 'bhaukaal', 'dharavi', 'raktanchal', 'detective', 'band baja murder'],
    'Mystery & Secrets': ['secret', 'mystery', 'moonlight', 'scent', 'hidden', 'missing'],
    'Marriage Drama': ['flash marriage', 'contract', 'married', 'wife', 'husband', 'wedding'],
    'Hook-Driven Romance': ['cursed kiss', 'allergic love', 'love me', 'fell twice', 'tempted'],
}

archetype_map = {}
for cid in sorted(df['cluster_id'].unique()):
    n = (df['cluster_id'] == cid).sum()
    if n < 10:
        archetype_map[cid] = "Outlier"
        continue

    top10 = show_cluster[show_cluster['cluster_id'] == cid].head(10)
    show_names = ' '.join(top10['tv_show_name'].tolist()).lower()

    # Score each archetype
    scores = {}
    for arch, keywords in archetype_keywords.items():
        score = sum(2 for kw in keywords if kw in show_names)
        scores[arch] = score

    # Also weight by secondary genre of top shows
    top_sg = top10['sec_genre'].value_counts()
    if 'Edgy' in top_sg.index and top_sg.get('Edgy', 0) >= 3:
        scores['Hook-Driven Romance'] += 3
    if 'Forbidden Love' in top_sg.index and top_sg.get('Forbidden Love', 0) >= 3:
        scores['Forbidden Love Epic'] += 3
    if 'Revenge' in top_sg.index and top_sg.get('Revenge', 0) >= 2:
        scores['Revenge & Power'] += 2
    if 'Melodrama' in top_sg.index and top_sg.get('Melodrama', 0) >= 2:
        scores['Female Empowerment'] += 2
    if 'Secret Lives' in top_sg.index and top_sg.get('Secret Lives', 0) >= 2:
        scores['Mystery & Secrets'] += 2
    if 'Crime' in top_sg.index and top_sg.get('Crime', 0) >= 2:
        scores['Hindi Crime/Thriller'] += 2

    best = max(scores, key=scores.get)
    if max(scores.values()) == 0:
        # Fallback: use top secondary genre
        top_sg_name = top10['sec_genre'].mode().iloc[0] if len(top10) > 0 else 'Mixed'
        best = f"{top_sg_name} Content"

    archetype_map[cid] = best

    print(f"\n  Cluster {cid} ({n:,} users): {best}")
    print(f"    Scores: {dict(sorted(scores.items(), key=lambda x: -x[1])[:4])}")
    print(f"    Top 5 shows:")
    for _, row in top10.head(5).iterrows():
        print(f"      {row['tv_show_name']} ({row['users']:,} users) [{row['sec_genre']}]")

# Add to dataframe
df['content_archetype'] = df['cluster_id'].map(archetype_map)

# ============================================================
# FINAL PERSONA CARDS WITH TWO-LEVEL CONTENT IDENTITY
# ============================================================
print("\n" + "=" * 80)
print("FINAL PERSONA CARDS")
print("=" * 80)

# Get role map from Phase 2.2
role_map = df.groupby('cluster_id')['strategic_role'].first().to_dict()

cards = []
for cid in sorted(df['cluster_id'].unique()):
    c = df[df['cluster_id'] == cid]
    n = len(c)
    if n < 10: continue
    pct = n / len(df) * 100
    role = role_map.get(cid, 'UNKNOWN')
    arch = archetype_map.get(cid, 'Unknown')

    # Level 1: Secondary genre (by watchtime)
    sg = cluster_sg[cluster_sg['cluster_id'] == cid].sort_values('pct', ascending=False)
    sg_str = ', '.join([f"{row['sec_genre']} ({row['pct']:.0f}%)" for _, row in sg.head(5).iterrows()])

    # Source + origin
    c_uv = uv[uv['cluster_id'] == cid]
    src_dist = c_uv.groupby('content_source')['minutes'].sum()
    src_pct = (src_dist / src_dist.sum() * 100).sort_values(ascending=False)
    src_str = ', '.join([f"{s} ({p:.0f}%)" for s, p in src_pct.head(3).items()])
    orig_dist = c_uv.groupby('content_origin')['minutes'].sum()
    orig_pct = (orig_dist / orig_dist.sum() * 100).sort_values(ascending=False)
    orig_str = ', '.join([f"{o} ({p:.0f}%)" for o, p in orig_pct.items()])

    # Top shows
    top_s = show_cluster[show_cluster['cluster_id'] == cid].head(5)
    shows_str = ', '.join([f"{row['tv_show_name']} ({row['users']:,})" for _, row in top_s.iterrows()])

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
    if 'tag_count' in c.columns:
        tagged = c[c['tag_count'] > 0]
        if len(tagged) > 100:
            ic = {'has_fashion_beauty': 'Fashion/Beauty', 'has_electronics_tech': 'Electronics/Tech',
                  'has_health_fitness': 'Health/Fitness', 'has_home_kitchen': 'Home/Kitchen',
                  'has_travel': 'Travel', 'has_parents_baby': 'Parents/Baby',
                  'has_automotive': 'Automotive', 'has_affluent_premium': 'Affluent/Premium'}
            rates = sorted([(v, tagged[k].mean()*100) for k, v in ic.items() if k in tagged.columns],
                          key=lambda x: -x[1])
            comm_str = f"Tags {len(tagged)/n*100:.0f}% | {', '.join([f'{k} ({v:.0f}%)' for k, v in rates[:3]])}"

    # Retention signature
    lock = c['lock_survival'].mean() * 100
    max_ep = c['max_episode_depth'].mean()
    if lock < 10: ret_sig = "Early Exit"
    elif max_ep < 30: ret_sig = "Moderate"
    elif max_ep < 60: ret_sig = "Steady Viewer"
    elif max_ep < 90: ret_sig = "Deep Binger"
    else: ret_sig = "Full Completer"

    card = f"""{'='*70}
CLUSTER {cid} — {role} — {n:,} users ({pct:.1f}%)
Content Archetype: {arch} | Retention: {ret_sig}
{'='*70}

  ENGAGEMENT:
    {c['total_minutes'].mean():.0f} min/wk | {c['mpc'].mean():.0f} MPC | {c['active_days'].mean():.1f} active days | {c['unique_shows'].mean():.1f} shows

  RETENTION:
    {c['max_episode_depth'].mean():.0f} max ep depth | {lock:.0f}% lock survival | {c['avg_episodes_per_session'].mean():.1f} eps/session

  CONTENT IDENTITY:
    Theme (L1):     {sg_str}
    Archetype (L2): {arch}
    Source:         {src_str}
    Origin:         {orig_str}
    Top Shows:      {shows_str}

  DEMOGRAPHIC PROFILE:
    {f_pct:.0f}% F / {m_pct:.0f}% M | {a18:.0f}% 18-24 | {a25:.0f}% 25-34 | {a35p:.0f}% 35+
    Top Cells: {ag_str}

  CHANNEL:
    Organic {org:.0f}% | Paid {paid:.0f}% | Push {push:.0f}%

  COMMERCIAL:
    {comm_str}

"""
    cards.append(card)
    print(card)

# ============================================================
# EXPORT
# ============================================================
print("\n--- Export ---")
df.to_csv(os.path.join(DIR, "fatafat_personas_final.csv"), index=False)

with open(os.path.join(DIR, "persona_cards_final.txt"), 'w') as f:
    f.write("FATAFAT SYNTHETIC PERSONAS — PHASE 2 FINAL\n")
    f.write("Base: Phase 2.2 clusters (sil=0.43, ARI=0.75)\n")
    f.write("Enrichment: Two-level content identity (secondary genre + archetype)\n")
    f.write(f"Clusters: {len([c for c in df['cluster_id'].unique() if (df['cluster_id']==c).sum() > 10])}\n\n")
    for card in cards:
        f.write(card)

print(f"  ✅ fatafat_personas_final.csv")
print(f"  ✅ persona_cards_final.txt")
print(f"\n🎯 PHASE 2 COMPLETE — Final personas with two-level content identity")
