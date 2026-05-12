import re

with open('c:/source/Synapse/frontend/modulo_cxp.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace classes
content = content.replace('class="stat-card active-selection-card"', 'class="kpi-card active-selection-card"')
content = content.replace('class="view-section report-view-container glass-card"', 'class="view-section report-view-container"')
content = content.replace('class="action-bar custom-scroll"', 'class="controls-grid custom-scroll"')

with open('c:/source/Synapse/frontend/modulo_cxp.html', 'w', encoding='utf-8') as f:
    f.write(content)

print('Replacement 2 complete.')
