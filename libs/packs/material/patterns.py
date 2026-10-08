#!/usr/bin/env python3
"""
Material pack (MAT-01 to MAT-15): Google Material Web custom elements in JSX. Target: material.
Each pattern imports its element definition as a side effect. Attributes on custom elements are
plain strings, so values go through jsx.s(); text content goes through jsx.t().

Copyright (c) 2025 Intelligent Cloud Lab Inc.
All rights reserved.
"""

from typing import Any, Dict, List

from libs.jsx import handler, req, s, t
from pattern_library import Pattern

MW = '@material/web/'
SYMBOLS = {'material-symbols': "// Material Symbols: add to <head>: <link rel=\"stylesheet\" href=\"https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined\" />"}
BUTTONS = {'filled': 'md-filled-button', 'outlined': 'md-outlined-button', 'text': 'md-text-button',
           'elevated': 'md-elevated-button', 'tonal': 'md-filled-tonal-button'}


def _on(p: Dict, key: str) -> str:
    name = handler(p, key)
    return f' {key}={{{name}}}' if name else ''


def button(p: Dict) -> str:
    req(p, 'MAT-01', 'label')
    tag = BUTTONS.get(p.get('variant', 'filled'), 'md-filled-button')
    dis = ' disabled=""' if p.get('disabled') else ''
    return f'<{tag}{_on(p, "onClick")}{dis}>{t(p["label"])}</{tag}>'


def icon_button(p: Dict) -> str:
    req(p, 'MAT-02', 'icon', 'label')
    return f'<md-icon-button aria-label={s(p["label"])}{_on(p, "onClick")}><md-icon>{t(p["icon"])}</md-icon></md-icon-button>'


def checkbox(p: Dict) -> str:
    req(p, 'MAT-03', 'label', 'name')
    return f'<label><md-checkbox name={s(p["name"])} touch-target="wrapper"></md-checkbox>{t(p["label"])}</label>'


def text_field(p: Dict) -> str:
    req(p, 'MAT-04', 'label', 'name')
    tag = 'md-filled-text-field' if p.get('variant') == 'filled' else 'md-outlined-text-field'
    reqd = ' required=""' if p.get('required') else ''
    return f'<{tag} label={s(p["label"])} name={s(p["name"])} type={s(p.get("type", "text"))}{reqd}></{tag}>'


def select(p: Dict) -> str:
    req(p, 'MAT-05', 'label', 'name', 'options')
    tag = 'md-filled-select' if p.get('variant') == 'filled' else 'md-outlined-select'
    opts = ''.join(f'<md-select-option value={s(o["value"])}><div slot="headline">{t(o["label"])}</div></md-select-option>' for o in p['options'])
    return f'<{tag} label={s(p["label"])} name={s(p["name"])}>{opts}</{tag}>'


def switch(p: Dict) -> str:
    req(p, 'MAT-06', 'label', 'name')
    sel = ' selected=""' if p.get('checked') else ''
    return f'<label>{t(p["label"])}<md-switch name={s(p["name"])}{sel}></md-switch></label>'


def radio_group(p: Dict) -> str:
    req(p, 'MAT-07', 'legend', 'name', 'options')
    radios = ''.join(f'<label><md-radio name={s(p["name"])} value={s(o["value"])}></md-radio>{t(o["label"])}</label>' for o in p['options'])
    return f'<div role="radiogroup" aria-label={s(p["legend"])}>{radios}</div>'


def dialog(p: Dict) -> str:
    req(p, 'MAT-08', 'id', 'headline', 'actions')
    acts = ''.join(f'<md-text-button form={s(p["id"] + "-form")} value={s(a["value"])}>{t(a["label"])}</md-text-button>' for a in p['actions'])
    return (f'<md-dialog id={s(p["id"])}><div slot="headline">{t(p["headline"])}</div>'
            f'<form slot="content" id={s(p["id"] + "-form")} method="dialog">{t(p.get("text", ""))}</form><div slot="actions">{acts}</div></md-dialog>')


def list_(p: Dict) -> str:
    req(p, 'MAT-09', 'items')
    items = ''
    for i in p['items']:
        sup = f'<div slot="supporting-text">{t(i["supporting"])}</div>' if i.get('supporting') else ''
        href = f' type="link" href={s(i["href"])}' if i.get('href') else ''
        items += f'<md-list-item{href}><div slot="headline">{t(i["headline"])}</div>{sup}</md-list-item>'
    return f'<md-list>{items}</md-list>'


def tabs(p: Dict) -> str:
    req(p, 'MAT-10', 'items')
    tag = 'md-secondary-tab' if p.get('variant') == 'secondary' else 'md-primary-tab'
    return f'<md-tabs>{"".join(f"<{tag}>{t(i)}</{tag}>" for i in p["items"])}</md-tabs>'


def chip_set(p: Dict) -> str:
    req(p, 'MAT-11', 'chips')
    kinds = {'assist': 'md-assist-chip', 'filter': 'md-filter-chip', 'input': 'md-input-chip', 'suggestion': 'md-suggestion-chip'}
    chips = ''.join(f'<{kinds.get(c.get("kind", "assist"), "md-assist-chip")} label={s(c["label"])}></{kinds.get(c.get("kind", "assist"), "md-assist-chip")}>'
                    for c in p['chips'])
    return f'<md-chip-set>{chips}</md-chip-set>'


def progress(p: Dict) -> str:
    tag = 'md-circular-progress' if p.get('kind') == 'circular' else 'md-linear-progress'
    attr = ' indeterminate=""' if p.get('value') is None else f' value={s(p["value"])}'
    return f'<{tag}{attr} aria-label={s(p.get("label", "Progress"))}></{tag}>'


def fab(p: Dict) -> str:
    req(p, 'MAT-13', 'icon', 'label')
    return f'<md-fab label={s(p["label"])} variant={s(p.get("variant", "primary"))}{_on(p, "onClick")}><md-icon slot="icon">{t(p["icon"])}</md-icon></md-fab>'


def divider(p: Dict) -> str:
    return '<md-divider></md-divider>'


def menu(p: Dict) -> str:
    req(p, 'MAT-15', 'id', 'anchor', 'items')
    items = ''.join(f'<md-menu-item{_on(i, "onClick")}><div slot="headline">{t(i["label"])}</div></md-menu-item>' for i in p['items'])
    return f'<md-menu id={s(p["id"])} anchor={s(p["anchor"])}>{items}</md-menu>'


def _imp(*paths: str) -> Dict[str, List[str]]:
    return {MW + path + '.js': [] for path in paths}


PATTERNS: List[Pattern] = [
    Pattern('MAT-01', 'Button', 'C', 'Filled, outlined, text, elevated or tonal button', button,
            imports=_imp('button/filled-button', 'button/outlined-button', 'button/text-button', 'button/elevated-button', 'button/filled-tonal-button')),
    Pattern('MAT-02', 'Icon Button', 'C', 'Icon button with accessible label', icon_button, imports=_imp('iconbutton/icon-button', 'icon/icon'), module=SYMBOLS),
    Pattern('MAT-03', 'Checkbox', 'C', 'Checkbox with label', checkbox, imports=_imp('checkbox/checkbox')),
    Pattern('MAT-04', 'Text Field', 'C', 'Outlined or filled text field', text_field, imports=_imp('textfield/outlined-text-field', 'textfield/filled-text-field')),
    Pattern('MAT-05', 'Select', 'C', 'Outlined or filled select with options', select,
            imports=_imp('select/outlined-select', 'select/filled-select', 'select/select-option')),
    Pattern('MAT-06', 'Switch', 'C', 'Switch with label', switch, imports=_imp('switch/switch')),
    Pattern('MAT-07', 'Radio Group', 'C', 'Radio group', radio_group, imports=_imp('radio/radio')),
    Pattern('MAT-08', 'Dialog', 'F', 'Dialog with headline, content form and actions', dialog, imports=_imp('dialog/dialog', 'button/text-button')),
    Pattern('MAT-09', 'List', 'I', 'List of items', list_, imports=_imp('list/list', 'list/list-item')),
    Pattern('MAT-10', 'Tabs', 'C', 'Primary or secondary tabs', tabs, imports=_imp('tabs/tabs', 'tabs/primary-tab', 'tabs/secondary-tab')),
    Pattern('MAT-11', 'Chip Set', 'C', 'Chips of any kind', chip_set,
            imports=_imp('chips/chip-set', 'chips/assist-chip', 'chips/filter-chip', 'chips/input-chip', 'chips/suggestion-chip')),
    Pattern('MAT-12', 'Progress', 'F', 'Linear or circular progress', progress, imports=_imp('progress/linear-progress', 'progress/circular-progress')),
    Pattern('MAT-13', 'FAB', 'C', 'Floating action button', fab, imports=_imp('fab/fab', 'icon/icon'), module=SYMBOLS),
    Pattern('MAT-14', 'Divider', 'C', 'Divider', divider, imports=_imp('divider/divider')),
    Pattern('MAT-15', 'Menu', 'C', 'Menu anchored to an element', menu, imports=_imp('menu/menu', 'menu/menu-item')),
]

TYPE_MAPPING = {'md-button': 'MAT-01', 'md-icon-button': 'MAT-02', 'md-checkbox': 'MAT-03', 'md-text-field': 'MAT-04', 'md-select': 'MAT-05',
                'md-switch': 'MAT-06', 'md-radio-group': 'MAT-07', 'md-dialog': 'MAT-08', 'md-list': 'MAT-09', 'md-tabs': 'MAT-10',
                'md-chips': 'MAT-11', 'md-progress': 'MAT-12', 'md-fab': 'MAT-13', 'md-divider': 'MAT-14', 'md-menu': 'MAT-15'}

SAMPLES: Dict[str, Dict[str, Any]] = {
    'MAT-01': {'label': 'Save', 'variant': 'filled', 'onClick': 'handleSave'},
    'MAT-02': {'icon': 'settings', 'label': 'Settings', 'onClick': 'handleSettings'},
    'MAT-03': {'label': 'Agree', 'name': 'agree'},
    'MAT-04': {'label': 'Email', 'name': 'email', 'type': 'email', 'required': True},
    'MAT-05': {'label': 'Size', 'name': 'size', 'options': [{'label': 'Small', 'value': 's'}, {'label': 'Large', 'value': 'l'}]},
    'MAT-06': {'label': 'Dark mode', 'name': 'dark', 'checked': True},
    'MAT-07': {'legend': 'Plan', 'name': 'plan', 'options': [{'label': 'Free', 'value': 'free'}, {'label': 'Pro', 'value': 'pro'}]},
    'MAT-08': {'id': 'confirm', 'headline': 'Delete?', 'text': 'This cannot be undone.', 'actions': [{'label': 'Cancel', 'value': 'cancel'}, {'label': 'Delete', 'value': 'ok'}]},
    'MAT-09': {'items': [{'headline': 'One', 'supporting': 'First'}, {'headline': 'Two', 'href': '/two'}]},
    'MAT-10': {'items': ['Home', 'Stories'], 'variant': 'primary'},
    'MAT-11': {'chips': [{'label': 'Assist'}, {'label': 'Filter', 'kind': 'filter'}]},
    'MAT-12': {'kind': 'linear', 'value': 0.5, 'label': 'Upload'},
    'MAT-13': {'icon': 'add', 'label': 'Add', 'onClick': 'handleAdd'},
    'MAT-14': {},
    'MAT-15': {'id': 'menu', 'anchor': 'menu-button', 'items': [{'label': 'Edit', 'onClick': 'handleEdit'}]},
}


def register(library) -> None:
    for pattern in PATTERNS:
        library.register(pattern)
