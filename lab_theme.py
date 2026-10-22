"""Shell styling for the Lab Assistant dashboard.

The gel editor brings its own stylesheet and is excluded from these rules, so
the frozen SDS-PAGE appearance cannot be affected by the dashboard theme.
"""

from __future__ import annotations

import streamlit as st

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

_EVENT_COLORS_LIGHT = {
    "practicum": ("#2e6b4f", "#e3efe8", "#1d4a36"),
    "deadline": ("#a63a2a", "#f6e3df", "#6b2118"),
    "incubation": ("#2c6e9b", "#e2eef5", "#1d4c6b"),
    "submission": ("#72509a", "#eee8f5", "#4a306b"),
    "todo": ("#a5681f", "#f7ecd9", "#6b4211"),
    "other": ("#5f6b60", "#ecefea", "#3f4840"),
}

_EVENT_COLORS_DARK = {
    "practicum": ("#8fc7b2", "#25362e", "#d7efe3"),
    "deadline": ("#e08a7f", "#3a2623", "#f6d8d3"),
    "incubation": ("#8fc1e0", "#22333e", "#d5ebf7"),
    "submission": ("#b9a1d8", "#2f2839", "#e9ddf6"),
    "todo": ("#e0b37b", "#372d20", "#f4e2c9"),
    "other": ("#a9b3a9", "#2b302b", "#e0e7df"),
}


def _event_css(dark: bool, t: dict[str, str]) -> str:
    """Use consistent, distinct importance colours across calendar categories."""
    palette = _EVENT_COLORS_DARK if dark else _EVENT_COLORS_LIGHT
    levels = ({"low": ("#243c55", "#c8e2ff", "#7cb5f0"),
               "normal": ("#493919", "#ffe4a0", "#e9b94e"),
               "high": ("#602c32", "#ffe0e3", "#ff929e")}
              if dark else
              {"low": ("#e7f1fc", "#214f7d", "#568dc3"),
               "normal": ("#fff0c2", "#684800", "#d39a15"),
               "high": ("#fce0e3", "#8a1d2c", "#d13b50")})
    rules = []
    for importance, (background, text, border) in levels.items():
        selectors = [f".la-cal .la-ev.kind-{kind}.importance-{importance}" for kind in palette]
        selectors += [f".la-importance.importance-{importance}"]
        rules.append(
            ",".join(selectors) + " {"
            f"background:{background};color:{text};border:1px solid {border};"
            f"border-left:4px solid {border};font-weight:600;opacity:1;" + "}"
        )
    rules.append(".la-importance {display:inline-block;padding:.2rem .55rem;"
                 "border-radius:5px;font-size:.8rem;margin:.2rem .4rem .2rem 0;}"
                 ".la-importance-legend {display:flex;gap:.35rem;flex-wrap:wrap;margin:.5rem 0;}")
    return "".join(rules)


def _tokens(dark: bool) -> dict[str, str]:
    return _DARK if dark else _LIGHT


def _dark_widget_css(t: dict[str, str]) -> str:
    """Streamlit reads its base theme from config.toml; recolour its controls."""
    return f"""
  [data-testid="stPopoverBody"] {{
    background: {t['panel']} !important;
    color: {t['text']} !important;
    border: 1px solid {t['border']} !important;
  }}
  [data-testid="stBaseButton-secondary"],
  [data-testid="stBaseButton-elementToolbar"] {{
    background: {t['panel_soft']} !important;
    color: {t['text']} !important;
    border: 1px solid {t['border']} !important;
  }}
  [data-testid="stBaseButton-secondary"]:hover,
  [data-testid="stBaseButton-elementToolbar"]:hover {{
    background: {t['accent_soft']} !important;
    border-color: {t['accent']} !important;
  }}
  [data-testid="stBaseButton-primary"] {{
    background: {t['accent']} !important;
    color: {t['accent_text']} !important;
    border: 1px solid {t['accent']} !important;
  }}
  [data-testid="stTextInputRootElement"],
  [data-testid="stNumberInputContainer"],
  [data-testid="stDateInput"] [role="group"],
  [data-testid="stSelectbox"] [role="group"],
  [data-testid="stTextArea"] textarea,
  [data-testid="stFileUploaderDropzone"] {{
    background: {t['panel_soft']} !important;
    color: {t['text']} !important;
    border-color: {t['border']} !important;
  }}
  [data-testid="stTextInputRootElement"] input,
  [data-testid="stNumberInputContainer"] input,
  [data-testid="stDateInput"] input,
  [data-testid="stSelectbox"] input,
  [data-testid="stTextArea"] textarea {{
    color: {t['text']} !important;
  }}
  [data-testid="stTextInputRootElement"] input::placeholder,
  [data-testid="stTextArea"] textarea::placeholder {{
    color: {t['muted']} !important;
  }}
  [data-testid="stSelectboxVirtualDropdown"],
  [data-testid="stSelectboxVirtualDropdown"] [role="option"] {{
    background: {t['panel']} !important;
    color: {t['text']} !important;
  }}
  [data-testid="stSelectboxVirtualDropdown"] [role="option"]:hover {{
    background: {t['accent_soft']} !important;
  }}
  [data-testid="stExpander"] details {{
    background: {t['panel']} !important;
    border: 1px solid {t['border']} !important;
  }}
  [data-testid="stExpander"] summary,
  [data-testid="stExpander"] summary * {{
    color: {t['text']} !important;
  }}
  [data-testid="stAlertContainer"] {{
    background: {t['accent_soft']} !important;
    color: {t['text']} !important;
    border: 1px solid {t['border']} !important;
  }}
  [data-testid="stCode"], [data-testid="stCode"] pre {{
    background: {t['panel_soft']} !important;
    color: {t['text']} !important;
    border-color: {t['border']} !important;
  }}
  [data-testid="stForm"] {{
    background: {t['panel']} !important;
    border-color: {t['border']} !important;
  }}
  [role="tab"] {{ color: {t['muted']} !important; }}
  [role="tab"][aria-selected="true"] {{ color: {t['text']} !important; }}
  hr {{ border-color: {t['border']} !important; }}
"""


def colored_cards_css(
    items: list[tuple[str, str]],
    dark: bool,
    *,
    height: str = "7.2rem",
    folder_tab: bool = True,
) -> str:
    """Give Streamlit buttons a coloured register-folder look.

    ``items`` maps a widget key (``st.button(..., key=...)``) to a validated
    hex colour. Streamlit renders the widget key as ``st-key-<key>`` on the
    surrounding element, so the rule stays local to that card.
    """
    if not items:
        return ""
    t = _tokens(dark)
    rules: list[str] = []
    for key, color in items:
        tab = ""
        folder_style = ""
        if folder_tab:
            folder_style = f"""
  .st-key-{key} {{ max-width:328px; margin-top:1.25rem; }}
  .stApp .st-key-{key} button {{
    height:230px !important; min-height:230px !important;
    justify-content:center !important; text-align:center !important;
    background:linear-gradient(145deg, {color}30, {t['panel']} 78%) !important;
    border:1px solid {color} !important; border-top:7px solid {color} !important;
    border-radius:10px 32px 32px 32px !important;
  }}
  .stApp .st-key-{key} button:hover {{
    background:linear-gradient(145deg, {color}48, {t['panel']} 78%) !important;
    box-shadow:0 4px 12px {color}25;
  }}
  .stApp .st-key-{key} button p {{ font-size:1.25rem !important; text-align:center !important; }}
  @media(max-width:600px) {{ .st-key-{key} {{max-width:100%;}} }}
"""
            tab = f"""
  .st-key-{key} button::before {{
    content: ""; position: absolute; left: 0.85rem; top: -0.46rem;
    width: 42%; height: 0.46rem; background: {color};
    border-radius: 7px 7px 0 0;
  }}"""
        rules.append(
            f"""
  .st-key-{key} button {{
    position: relative; overflow: visible;
    min-height: {height}; padding: 0.95rem 1rem !important;
    justify-content: flex-start !important; text-align: left !important;
    background: {t['panel']} !important;
    border: 1px solid {color} !important;
    border-top: 0.42rem solid {color} !important;
    border-radius: 5px 16px 16px 16px !important;
    color: {t['text']} !important;
    box-shadow: {t['shadow']};
  }}
  .st-key-{key} button:hover {{
    border-color: {t['accent']} !important;
    background: {t['panel_soft']} !important;
  }}
  .st-key-{key} button p {{
    font-size: 1rem; font-weight: 700; line-height: 1.22;
    justify-content: flex-start; text-align: left;
  }}{tab}{folder_style}"""
        )
    return "<style>" + "".join(rules) + "</style>"


def shell_css(dark: bool) -> str:
    t = _tokens(dark)
    extra = _dark_widget_css(t) if dark else ""
    event_extra = _event_css(dark, t)
    return f"""
<style>
  [data-testid="stBaseButton-primary"] {{
    background: {t['accent']} !important; color: {t['accent_text']} !important;
    border-color: {t['accent']} !important;
  }}
  [data-testid="stBaseButton-primary"] p {{ color: {t['accent_text']} !important; }}
  .stApp {{ background: {t['bg']}; color: {t['text']}; }}
  [data-testid="stHeader"] {{ background: transparent; }}
  [data-testid="stSidebar"] {{
    background: {t['sidebar']};
    border-right: 1px solid {t['border']};
  }}
  [data-testid="stSidebar"] [data-testid="stSidebarUserContent"] {{
    padding-top: 0.8rem;
  }}
  [data-testid="stSidebar"] button {{
    min-height: 2.35rem;
  }}
  [data-testid="stSidebar"] .la-brand {{
    font-weight: 750; letter-spacing: -0.02em; font-size: 1.25rem;
    color: {t['text']}; margin: 0.1rem 0 0.5rem 0;
  }}
  [data-testid="stSidebar"] .la-brand span {{
    display: block; font-weight: 400; font-size: 0.95rem;
    color: {t['muted']}; margin-top: 0.4rem;
  }}
  .block-container {{ padding-top: 1.2rem; padding-bottom: 3rem; max-width: 1500px; }}
  h1, h2, h3, h4, p, label, .stMarkdown {{ color: {t['text']}; }}
  .la-hero {{
    background: {t['panel']};
    border: 1px solid {t['border']};
    border-radius: 18px;
    padding: 1.25rem 1.4rem 1.1rem 1.4rem;
    margin-bottom: 1.1rem;
    box-shadow: {t['shadow']};
  }}
  .la-kicker {{
    color: {t['accent_ink']}; font-size: 0.76rem; font-weight: 700;
    text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 0.35rem;
  }}
  .la-hero h1 {{ margin: 0 0 0.25rem 0; font-size: 2rem; }}
  .la-hero p {{ color: {t['muted']}; margin: 0; max-width: 52rem; }}
  .la-card {{
    flex: 1 1 15rem; background: {t['panel']}; border: 1px solid {t['border']};
    border-radius: 16px; padding: 1rem 1.1rem; box-shadow: {t['shadow']};
  }}
  .la-muted {{ color: {t['muted']}; }}
  .la-cal {{
    width: 100%; border-collapse: separate; border-spacing: 0;
    table-layout: fixed; margin-top: 0.4rem;
  }}
  .la-cal th {{
    color: {t['muted']}; font-size: 0.72rem; text-transform: uppercase;
    letter-spacing: 0.05em; padding: 0.35rem 0.4rem; text-align: left;
    border-bottom: 1px solid {t['border']};
  }}
  .la-cal td {{
    vertical-align: top; height: 5.4rem; padding: 0.35rem 0.4rem;
    border-bottom: 1px solid {t['border']}; border-right: 1px solid {t['border']};
  }}
  .la-cal td:last-child {{ border-right: none; }}
  .la-cal td.la-out {{ opacity: 0.38; }}
  .la-cal td.la-today {{ background: {t['today']}; }}
  .la-cal .la-day {{ font-size: 0.78rem; font-weight: 600; }}
  .la-cal .la-ev {{
    display: block; margin-top: 0.18rem; padding: 0.1rem 0.3rem;
    border-radius: 4px; background: {t['accent_soft']};
    color: {t['text']}; font-size: 0.68rem; line-height: 1.25;
    overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
  }}
  .la-cal .la-ev.la-deadline {{ background: {t['accent']}; color: {t['accent_text']}; }}
  {event_extra}
  .la-cal.la-cal-compact td {{ height: 3.15rem; padding: 0.18rem 0.22rem; }}
  .la-cal.la-cal-compact th {{ font-size: 0.62rem; padding: 0.25rem 0.2rem; }}
  .la-cal.la-cal-compact .la-day {{ font-size: 0.7rem; }}
  .la-cal.la-cal-compact .la-ev {{ font-size: 0.58rem; margin-top: 0.1rem; }}
  .la-event-meta {{ color: {t['muted']}; font-size: 0.8rem; }}
  .la-note {{ color: {t['muted']}; font-size: 0.78rem; line-height: 1.35; }}
  .la-section {{ display: flex; align-items: baseline; justify-content: space-between;
                 gap: 0.75rem; margin: 0.1rem 0 0.55rem 0; }}
  .la-section h3 {{ margin: 0; font-size: 1.05rem; }}
  .la-section span {{ color: {t['muted']}; font-size: 0.78rem; }}
  .la-meta {{ color: {t['muted']}; font-size: 0.76rem; }}
  .la-dot {{ display: inline-block; width: 0.62rem; height: 0.62rem;
             border-radius: 999px; margin-right: 0.35rem; vertical-align: 0.02rem; }}
  .la-selected {{ color: {t['accent_ink']}; font-weight: 700; font-size: 0.76rem; }}
  .la-pill {{
    display: inline-block; padding: 1px 8px; border-radius: 999px;
    background: {t['accent_soft']}; color: {t['text']}; font-size: 0.72rem;
    font-weight: 600; margin-right: 5px;
  }}
  .la-empty {{
    border: 1px dashed {t['border']}; border-radius: 14px;
    padding: 1.2rem; color: {t['muted']}; text-align: center;
  }}
  div[data-testid="stMetric"] {{
    background: {t['panel']}; border: 1px solid {t['border']};
    border-radius: 12px; padding: 0.55rem 0.75rem;
  }}
  {extra}
</style>
"""


def inject_theme(dark: bool) -> None:
    st.markdown(shell_css(dark) + shared_ui_css(dark), unsafe_allow_html=True)


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
