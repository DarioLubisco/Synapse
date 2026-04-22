import os
path = r'c:\Users\DARIO LUBISCO\.gemini\antigravity\worktrees\Synapse\fix-payment-modal-sync-20260422\frontend\modulo_cxp.html'
with open(path, 'r', encoding='utf-8', errors='replace') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if 'auditarFechasModal' in line:
        print(f'{i}: {line.strip()}')
        for j in range(max(0, i-2), min(len(lines), i+5)):
            print(f'  {j}: {lines[j].strip()}')
        break
