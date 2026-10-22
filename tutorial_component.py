"""Client-only tour/help; only an explicit demo request changes app state."""
from pathlib import Path

import streamlit.components.v1 as components

from demo_project import build_demo, has_project_work
from locales import STRINGS, t

_component = components.declare_component('geldoc_tutorial', path=str(Path(__file__).parent / 'components' / 'tutorial'))

def tutorial_config(lang):
    targets = {
        'upload': {'tab': 0, 'selector': '[data-testid="stFileUploader"]'},
        'corners': {'tab': 0, 'heading': t('persp_title',lang)},
        'crop': {'tab': 0, 'heading': t('crop_title',lang)},
        'lanes': {'tab': 1, 'selector': '[class*="st-key-gd-sticky-lanes"]'},
        'markers': {'tab': 2, 'selector': 'iframe[title="editor_component.gel_editor"]'},
        'arrows': {'tab': 3, 'selector': 'iframe[title="editor_component.gel_editor"]'},
        'labels': {'tab': 1, 'selector': 'iframe[title="label_editor.label_editor"]'},
        'groups': {'tab': 1, 'heading': t('group_title',lang)},
        'matrix': {'tab': 1, 'heading': t('cond_title',lang)},
        'rotation': {'sidebar': True, 'label': t('label_rotation',lang)},
        'export': {'tab': 4, 'heading': t('export_title',lang)},
    }
    return {'text': {key:t(key,lang) for key in STRINGS if key.startswith('onboard_')},
                'targets': targets, 'steps': [['upload','corners','crop'],['lanes'],['markers','arrows'],
                                        ['labels','rotation','groups','matrix'],['export']]}

def tutorial_controls(project, *, dark=False, compact=False, demo_token=None, start_tour=False):
    return _component(**tutorial_config(project.lang), lang=project.lang, dark=dark,
                      has_work=has_project_work(project), compact=compact,
                      demo_token=demo_token, start_tour=start_tour,
                      key='tutorial_import' if compact else 'tutorial_main', default=None)

def accept_demo_event(state, event, clear_caches):
    """The only mutation boundary. Build completely before replacing anything."""
    if not isinstance(event, dict) or event.get('action') != 'load_demo' or event.get('confirmed') is not True:
        return False
    nonce = event.get('nonce')
    if not isinstance(nonce, str) or nonce in state.get('demo_consumed', []):
        return False
    project, tracking = build_demo(state.project.lang)
    # Preserve presentation preference; the demo's export DPI stays 300.
    project.theme = state.project.theme
    project.export.theme = project.theme
    state.project = project
    state.demo_tracking = tracking
    state.active = state.selected_lane = state.selected_marker = state.selected_arrow = 0
    state.ui_version += 1
    state.crop_version += 1
    state.editor_nonces = {}
    state.demo_consumed = (state.get('demo_consumed', []) + [nonce])[-30:]
    state.demo_token = nonce
    state.demo_start_tour = bool(event.get('tour'))
    clear_caches()
    return True
