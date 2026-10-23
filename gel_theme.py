"""Farben des eigenständigen Gel-Editors."""
from __future__ import annotations

_LIGHT = {
    "bg": "#f8f8f6",
    "panel": "#fafaf8",
    "panel_soft": "#f0f0f0",
    "sidebar": "#f8f8f6",
    "border": "#d2d2d2",
    "text": "#20241f",
    "muted": "#787b75",
    "accent": "#60a5fa",
    "accent_ink": "#2563a6",
    "accent_soft": "#f3f3f1",
    "accent_text": "#20241f",
    "today": "#f0f0f0",
    "shadow": "0 1px 2px rgba(24, 32, 25, 0.06)",
}

_DARK = {
    "bg": "#111925",
    "panel": "#182333",
    "panel_soft": "#202f44",
    "sidebar": "#152131",
    "border": "#34465e",
    "text": "#e7eef8",
    "muted": "#a4b3c6",
    "accent": "#93c5fd",
    "accent_ink": "#93c5fd",
    "accent_soft": "#253d5b",
    "accent_text": "#122a46",
    "today": "#253d5b",
    "shadow": "0 1px 2px rgba(0, 0, 0, 0.35)",
}

def _tokens(dark: bool) -> dict[str, str]:
    return _DARK if dark else _LIGHT

def shared_ui_css(dark: bool) -> str:
    """Gemeinsame Oberflächenfarben für Shell und vollständigen Gel-Editor."""
    t = _tokens(dark)
    return f"""<style>
    :root {{ --lab-text: {t['text']}; --lab-accent: {t['accent']}; --lab-accent-ink: {t['accent_ink']};
      --lab-soft: {t['accent_soft']}; --lab-panel: {t['panel']}; --lab-border: {t['border']}; }}
    .stApp, [data-testid="stAppViewContainer"] {{ background: {t['bg']} !important; color: {t['text']} !important; }}
    [data-testid="stHeader"] {{ background: {t['bg']} !important; }}
    [data-testid="stSidebar"] {{ background: {t['sidebar']} !important; border-color: {t['border']} !important; }}
    .stApp h1,.stApp h2,.stApp h3,.stApp h4,.stApp h5,.stApp h6 {{ color: {t['text']} !important; }}
    .stApp [data-testid="stBaseButton-primary"] {{ background: {t['accent']} !important;
      color: {t['accent_text']} !important; border-color: {t['accent']} !important; }}
    .stApp [data-testid="stBaseButton-primary"] p {{ color: {t['accent_text']} !important; }}
    .stApp [data-testid="stBaseButton-secondary"],.stApp [data-testid="stBaseButton-secondaryFormSubmit"],
    .stApp [data-testid="stPopover"] button,
    .stApp [data-testid="stDownloadButton"] button {{ background: {t['panel']} !important;
      color: {t['text']} !important; border-color: {t['border']} !important; border-radius:9px; }}
    .stApp button:focus-visible,.stApp input:focus-visible,.stApp textarea:focus-visible {{
      outline:3px solid {t['accent']} !important; outline-offset:2px; }}
    .stApp [data-testid="stBaseButton-secondary"]:hover {{ background:{t['accent_soft']} !important;
      border-color:{t['accent']} !important; }}
    .stApp [data-testid="stTabs"] [role="tablist"] {{ background:transparent !important;
      border:0; border-bottom:1px solid {t['border']}; border-radius:0 !important; padding:.35rem !important; gap:.3rem; }}
    .stApp [data-testid="stTabs"] [role="tab"] {{ color:{t['muted']} !important;
      border-radius:0 !important; padding:.65rem .9rem !important; border-bottom:2px solid transparent !important; transition:none !important; }}
    .stApp [data-testid="stTabs"] [role="tab"][aria-selected="true"] {{
      color:{t['accent_ink']} !important; background:transparent !important; border-bottom-color:{t['accent']} !important; }}
    .stApp [data-testid="stTextInputRootElement"],.stApp [data-testid="stNumberInputContainer"],
    .stApp [data-testid="stSelectbox"] [role="group"],.stApp [data-testid="stTextArea"] textarea,
    .stApp [data-testid="stFileUploaderDropzone"] {{ background:{t['panel_soft']} !important;
      color:{t['text']} !important; border:1px solid transparent !important; border-radius:9px; }}
    .stApp input,.stApp textarea {{ color:{t['text']} !important; -webkit-text-fill-color:{t['text']} !important; }}
    .stApp [data-testid="stPopoverBody"],.stApp [data-testid="stExpander"] details {{
      background:{t['panel']} !important; border-color:{t['border']} !important; }}
    .stApp .gd-sub,.stApp .gd-note,.stApp .la-note {{ color:{t['muted']} !important; }}
    .stApp .gd-note {{ background:{t['accent_soft']} !important; border-color:{t['border']} !important;
      border-left:3px solid {t['accent']} !important; }}
    .stApp [data-testid="stAlertContainer"] {{ background:{t['accent_soft']} !important; border-color:{t['border']} !important; }}
    body [data-testid="stPopoverBody"],body [data-testid="stSelectboxVirtualDropdown"],
    body [data-testid="stMultiSelectVirtualDropdown"],body [role="option"] {{
      background:{t['panel']} !important; color:{t['text']} !important; border-color:{t['border']} !important; }}
    body [data-testid="stPopoverBody"] p,body [data-testid="stPopoverBody"] label,
    body [data-testid="stPopoverBody"] h4 {{ color:{t['text']} !important; }}
    .stApp [data-testid="stToolbar"],.stApp [data-testid="stMainMenu"],.stApp .stAppDeployButton {{ display:none !important; }}
    </style>"""
