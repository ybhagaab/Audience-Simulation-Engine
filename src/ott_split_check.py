import pandas as pd
df = pd.read_csv('/Users/ybhagaab/Synthetic Persona/synthetic-personas/data/fatafat_personas_with_ott.csv')

cluster_col = 'cluster' if 'cluster' in df.columns else 'cluster_v2'
names = {0: 'Discovery Sampler', 1: 'Romance Binger', 2: 'Platform Devotee', 3: 'Male Crossover', 5: 'Engaged Explorer'}

header = f"{'Persona':25s} {'Group':12s} {'Users':>8s} {'FF min':>8s} {'FF med':>8s} {'Shows':>6s} {'Days':>5s} {'Lock%':>6s} {'OTT min':>8s} {'OTT med':>8s}"
print(header)
print('-' * len(header))

for cid in sorted(names.keys()):
    c = df[df[cluster_col] == cid]
    if len(c) < 10: continue
    name = names[cid]

    ott_yes = c[c['has_ott'] == True]
    ott_no = c[c['has_ott'] == False]

    for label, grp in [('OTT overlap', ott_yes), ('No OTT', ott_no)]:
        if len(grp) == 0: continue
        ff_mean = grp['total_minutes'].mean()
        ff_med = grp['total_minutes'].median()
        shows = grp['unique_shows'].mean()
        days = grp['active_days'].mean()
        lock = grp['lock_survival'].mean() * 100
        ott_mean = grp['ott_minutes'].mean()
        ott_med = grp['ott_minutes'].median()

        print(f"{name:25s} {label:12s} {len(grp):>8,} {ff_mean:>7.1f} {ff_med:>7.1f} {shows:>5.1f} {days:>4.1f} {lock:>5.1f}% {ott_mean:>7.1f} {ott_med:>7.1f}")
    
    # Compute the delta
    if len(ott_yes) > 0 and len(ott_no) > 0:
        ff_delta = ott_yes['total_minutes'].mean() / max(ott_no['total_minutes'].mean(), 0.01)
        lock_delta = ott_yes['lock_survival'].mean() / max(ott_no['lock_survival'].mean(), 0.01)
        print(f"{'':25s} {'→ OTT users':12s} {'':>8s} {f'{ff_delta:.1f}x':>8s} {'':>8s} {'':>6s} {'':>5s} {f'{lock_delta:.1f}x':>6s}")
    print()
