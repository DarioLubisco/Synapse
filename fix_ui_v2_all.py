import os
import re

def fix_file(path):
    if not os.path.exists(path):
        return
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Replace classes
    replacements = [
        ('class="top-header"', 'class="header"'),
        ('class="top-header ', 'class="header '),
        ('class="action-bar glassmorphism"', 'class="controls-grid"'),
        ('class="action-bar"', 'class="controls-grid"'),
        ('class="dashboard-stats"', 'class="kpi-grid"'),
        ('class="stat-card "', 'class="kpi-card"'),
        ('class="stat-card"', 'class="kpi-card"'),
        ('class="modal-content glass-card"', 'class="modal-content"'),
        ('class="modal-content glass-panel"', 'class="modal-content"'),
        ('class="modal-content glassmorphism"', 'class="modal-content"'),
        ('class="view-section report-view-container glass-card"', 'class="view-section report-view-container"'),
        ('class="stat-card active-selection-card"', 'class="kpi-card active-selection-card"'),
        ('class="action-bar custom-scroll"', 'class="controls-grid custom-scroll"')
    ]

    new_content = content
    for old, new in replacements:
        new_content = new_content.replace(old, new)

    if new_content != content:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f'Refactored: {path}')

frontend_dir = 'c:/source/Synapse/frontend'
for filename in os.listdir(frontend_dir):
    if filename.endswith('.html'):
        fix_file(os.path.join(frontend_dir, filename))
