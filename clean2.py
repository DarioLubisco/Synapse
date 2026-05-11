import sys
path = r'c:\source\Synapse\frontend\modulo_cxp.html'
text = open(path, encoding='utf-8').read()
text = text.replace('class="table-actions" class="table-actions"', 'class="table-actions"')
open(path, 'w', encoding='utf-8').write(text)
