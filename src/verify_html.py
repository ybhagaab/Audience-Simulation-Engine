"""Quick verification: compare persona card text file vs HTML dashboard data"""
import re

# Read both files
with open('/Users/ybhagaab/Synthetic Persona/synthetic-personas/output/persona_cards_final.txt') as f:
    txt = f.read()
with open('/Users/ybhagaab/Synthetic Persona/synthetic-personas/dashboard/index.html') as f:
    html = f.read()

personas = [
    ('Discovery Sampler', 'CLUSTER 0', 'p0'),
    ('Male Crossover', 'CLUSTER 3', 'p3'),
    ('Romance Binger', 'CLUSTER 1', 'p1'),
    ('Engaged Explorer', 'CLUSTER 5', 'p5'),
    ('Platform Devotee', 'CLUSTER 2', 'p2'),
]

checks = [
    ('Engagement min', r'(\d+) min/wk'),
    ('Lock survival', r'(\d+)% lock survival'),
    ('Edgy %', r'Edgy[^%]*?(\d+)%'),
    ('Forbidden Love %', r'Forbidden Love[^%]*?(\d+)%'),
    ('Melodrama %', r'Melodrama[^%]*?(\d+)%'),
    ('Source Intl', r'Intl Dubbed (\d+)%'),
    ('Female %', r'(\d+)% F'),
    ('Male %', r'(\d+)% M'),
    ('OTT overlap', r'OTT overlap: (\d+)%'),
    ('Hindi Belt', r'Hindi Belt (\d+)%'),
    ('South', r'South (\d+)%'),
    ('West %', r'West (\d+)%'),
]

print(f"{'Persona':25s} {'Field':20s} {'Text':>8s} {'HTML':>8s} {'Match':>6s}")
print('=' * 70)

mismatches = 0
for name, txt_marker, html_id in personas:
    # Extract text card section
    txt_start = txt.find(txt_marker)
    txt_next = txt.find('CLUSTER', txt_start + 10)
    if txt_next == -1: txt_next = len(txt)
    txt_section = txt[txt_start:txt_next]

    # Extract HTML card section
    html_start = html.find(f'id="{html_id}"')
    html_next_ids = [html.find(f'id="{p[2]}"', html_start + 10) for p in personas if p[2] != html_id]
    html_next_ids = [x for x in html_next_ids if x > html_start]
    html_end = min(html_next_ids) if html_next_ids else html_start + 5000
    html_section = html[html_start:html_end]

    for field, pattern in checks:
        txt_match = re.search(pattern, txt_section)
        html_match = re.search(pattern, html_section)
        txt_val = txt_match.group(1) if txt_match else 'N/A'
        html_val = html_match.group(1) if html_match else 'N/A'
        match = '✅' if txt_val == html_val else '❌'
        if txt_val != html_val:
            mismatches += 1
        print(f"{name:25s} {field:20s} {txt_val:>8s} {html_val:>8s} {match:>6s}")
    print()

print(f"\nTotal mismatches: {mismatches}")
