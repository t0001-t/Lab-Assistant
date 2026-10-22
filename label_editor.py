"""Visual label editing; existing JSON markup remains backwards compatible."""
from pathlib import Path

import streamlit.components.v1 as components

from canvas_renderer import parse_rich

_component = components.declare_component('label_editor', path=str(Path(__file__).parent / 'components' / 'label_editor'))

def encode_runs(runs):
    if not isinstance(runs, list):
        raise ValueError('Invalid label')  # noqa: TRY004 - public component contract keeps ValueError
    parts = []
    for run in runs:
        if not isinstance(run, list) or len(run) != 2 or not isinstance(run[0], str) or run[1] not in (-1, 0, 1):
            raise ValueError('Invalid text run')
        text = run[0]
        for char in ('\\', '^', '_', '{', '}'):
            text = text.replace(char, '\\' + char)
        parts.append(('^{' if run[1] == 1 else '_{') + text + '}' if run[1] else text)
    return ''.join(parts)

def label_editor(lanes, *, key, lang='de', dark=False):
    rows = [{'top': parse_rich(l.label_top), 'bottom': parse_rich(l.label_bottom), 'x': round(l.x_pos_rel*100, 2)} for l in lanes]
    return _component(rows=rows, lang=lang, dark=dark, key=key, default=None)
