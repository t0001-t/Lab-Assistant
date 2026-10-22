"""Demonstration project built exclusively through existing domain models."""
from pathlib import Path

from PIL import Image

from locales import t
from models import ConditionRow, GroupLabel, TargetArrow, default_project

ROOT = Path(__file__).parent

def build_demo(lang='de'):
    project = default_project(10)
    project.lang = lang
    panel = project.panels[0]
    with Image.open(ROOT / 'assets' / 'sample_gel.jpg') as source:
        panel.source_image = source.convert('RGB')
    panel.source_name = 'sample_gel.jpg'
    panel.ladder_sides = 'left'
    panel.marker_lane_indexes = [0]
    panel.conditions = [ConditionRow(values=['', '−', '+', '−', '+', '−', '+', '−', '+', '+']),
                        ConditionRow(values=['', '−', '−', '+', '+', '−', '−', '+', '+', '−'])]
    panel.groups = [GroupLabel(start_index=1, end_index=4), GroupLabel(start_index=5, end_index=9)]
    panel.arrows = [TargetArrow(y_pos_rel=.404, side='right')]
    project.export.dpi = 300
    project.export.label_rotation = 45
    entries = [(project, 'name', 'demo_name', {}), (panel, 'name', 'demo_panel', {}),
               (panel.lanes[0], 'label_top', 'demo_ladder', {}),
               (panel.lanes[1], 'label_top', 'demo_control', {})]
    for i in range(2, 10):
        entries.append((panel.lanes[i], 'label_top', 'demo_sample', {'n': i-1}))
    panel.lanes[2].label_bottom = '10^{6}'
    panel.lanes[3].label_bottom = 'H_{2}O'
    for i in range(2):
        entries.append((panel.conditions[i], 'name', f'demo_condition_{i}', {}))
        entries.append((panel.groups[i], 'text', f'demo_group_{i}', {}))
    entries.append((panel.arrows[0], 'label', 'demo_target', {}))
    for obj, attr, key, params in entries:
        setattr(obj, attr, t(key, lang, **params))
    # Record localized strings, not references to mutable/rebuilt table rows.
    defaults = {t(key, lang, **params): (key, params) for _, _, key, params in entries}
    return project, {'project': project, 'lang': lang, 'defaults': defaults}


def translate_demo(project, tracking, lang):
    """Translate only untouched demo defaults in this exact live project.

    User values, geometry, matrix values, and images are never replaced.
    Rebuilt group/condition rows are supported. Loaded personal projects do
    not inherit provenance from a previous demo.
    """
    if not tracking or tracking.get('project') is not project or tracking['lang'] == lang:
        return
    old = tracking['defaults']
    fields = [(project, 'name')]
    for panel in project.panels:
        fields.append((panel, 'name'))
        fields.extend((lane, attr) for lane in panel.lanes for attr in ('label_top', 'label_bottom'))
        fields.extend((row, 'name') for row in panel.conditions)
        fields.extend((group, 'text') for group in panel.groups)
        fields.extend((arrow, 'label') for arrow in panel.arrows)
    for obj, attr in fields:
        value = getattr(obj, attr)
        if value in old:
            key, params = old[value]
            setattr(obj, attr, t(key, lang, **params))
    tracking['defaults'] = {t(key, lang, **params): (key, params) for key, params in old.values()}
    tracking['lang'] = lang


def has_project_work(project):
    if project.has_any_image():
        return True
    def content(value):
        data = value.model_dump(mode='json')
        data.pop('lang', None)
        for panel in data['panels']:
            panel.pop('id', None)
        return data
    return content(project) != content(default_project())
