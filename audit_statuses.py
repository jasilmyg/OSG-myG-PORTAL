import os, re

# Backend whitelist
backend = {
    'submitted', 'registered', 'follow up', 'repair completed',
    'replacement approved', 'rejected', 'cancelled', 'closed',
    'no issue/oncall resolution', 'no issue', 'oncall resolution'
}

print('=== BACKEND ALLOWED_STATUSES ===')
for s in sorted(backend):
    print('  -', s)
print()

# Scan frontend files for option values
files_to_check = [
    'templates/claim_detail.html',
    'templates/dashboard.html',
    'static/js/script.js',
]

all_ok = True
for path in files_to_check:
    if not os.path.exists(path):
        continue
    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    # Match: value="Repair Completed"
    options = re.findall(r'value=["\']([A-Za-z /\(\)]+)["\']', content)
    # Match: 'Repair Completed' used as status comparisons in JS
    options += re.findall(r"['\"]([A-Z][a-z]+(?: [A-Za-z]+)+)['\"]", content)
    # Normalize
    found = set()
    for o in options:
        o = o.strip().lower()
        if o and len(o) > 3:
            found.add(o)

    # Only check status-like values
    status_like = {s for s in found if any(kw in s for kw in ['repair','replacement','registered','follow','reject','cancel','submit','close','oncall','issue'])}
    not_in_backend = status_like - backend

    if not_in_backend:
        all_ok = False
        print('=== MISMATCHES IN', path, '===')
        for s in sorted(not_in_backend):
            print('  [MISSING FROM BACKEND]:', s)
    else:
        print('[OK]', path, '- all statuses match backend')

print()
if all_ok:
    print('ALL OK - No mismatches found!')
else:
    print('Action needed: add missing statuses to backend whitelist or remove from frontend.')
