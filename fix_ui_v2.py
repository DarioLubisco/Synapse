import re

def fix_file(path):
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Replace classes
    content = content.replace('class="top-header"', 'class="header"')
    content = content.replace('class="top-header ', 'class="header ')
    content = content.replace('class="action-bar glassmorphism"', 'class="controls-grid"')
    content = content.replace('class="action-bar"', 'class="controls-grid"')
    content = content.replace('class="dashboard-stats"', 'class="kpi-grid"')
    content = content.replace('class="stat-card "', 'class="kpi-card"')
    content = content.replace('class="stat-card"', 'class="kpi-card"')
    content = content.replace('class="modal-content glass-card"', 'class="modal-content"')
    content = content.replace('class="modal-content glass-panel"', 'class="modal-content"')
    content = content.replace('class="modal-content glassmorphism"', 'class="modal-content"')
    content = content.replace('class="view-section report-view-container glass-card"', 'class="view-section report-view-container"')

    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

fix_file('c:/source/Synapse/frontend/modulo_caja.html')
fix_file('c:/source/Synapse/frontend/modulo_cxp.html')

print('Refactor complete for Caja and CxP.')
