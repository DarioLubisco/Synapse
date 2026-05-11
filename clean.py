import sys
path = r'c:\source\Synapse\frontend\modulo_cxp.html'
text = open(path, encoding='utf-8').read()
text = text.replace(' style="flex-wrap: wrap; gap: 1rem;"', '')
text = text.replace(' style="display: flex; gap: 1rem; align-items: flex-end;"', ' class="table-actions"')
open(path, 'w', encoding='utf-8').write(text)
