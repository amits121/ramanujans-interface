#!/usr/bin/env python3
"""
Amplify pack (AMP-01 to AMP-23): Amplify UI React beyond C-01..C-10, plus connected components.
Target: react-amplify. Every generator is a pure function of its props.

Copyright (c) 2025 Intelligent Cloud Lab Inc.
All rights reserved.
"""

from typing import Any, Dict, List

from libs.jsx import attrs, handler, req, t
from pattern_library import Pattern

UI = '@aws-amplify/ui-react'
STORAGE = '@aws-amplify/ui-react-storage'


def heading(p: Dict) -> str:
    req(p, 'AMP-01', 'text')
    return f'<Heading level={{{min(max(int(p.get("level", 2)), 1), 6)}}}>{t(p["text"])}</Heading>'


def text(p: Dict) -> str:
    req(p, 'AMP-02', 'text')
    return f'<Text{attrs({"variation": p.get("variation")})}>{t(p["text"])}</Text>'


def image(p: Dict) -> str:
    req(p, 'AMP-03', 'src', 'alt')
    return f'<Image{attrs({"src": p["src"], "alt": p["alt"], "width": p.get("width"), "height": p.get("height")})} />'


def link(p: Dict) -> str:
    req(p, 'AMP-04', 'href', 'text')
    return f'<Link{attrs({"href": p["href"], "isExternal": p.get("isExternal")})}>{t(p["text"])}</Link>'


def flex(p: Dict) -> str:
    req(p, 'AMP-05', 'items')
    items = ''.join(f'<Text>{t(i)}</Text>' for i in p['items'])
    return f'<Flex{attrs({"direction": p.get("direction", "row"), "gap": p.get("gap", "1rem"), "wrap": p.get("wrap")})}>{items}</Flex>'


def grid(p: Dict) -> str:
    req(p, 'AMP-06', 'items')
    items = ''.join(f'<Text>{t(i)}</Text>' for i in p['items'])
    return f'<Grid{attrs({"templateColumns": p.get("templateColumns", "1fr 1fr"), "gap": p.get("gap", "1rem")})}>{items}</Grid>'


def divider(p: Dict) -> str:
    return f'<Divider{attrs({"orientation": p.get("orientation"), "size": p.get("size")})} />'


def badge(p: Dict) -> str:
    req(p, 'AMP-08', 'text')
    return f'<Badge{attrs({"variation": p.get("variation", "info")})}>{t(p["text"])}</Badge>'


def loader(p: Dict) -> str:
    return f'<Loader{attrs({"size": p.get("size", "large"), "variation": p.get("variation")})} />'


def message(p: Dict) -> str:
    req(p, 'AMP-10', 'text')
    return (f'<Message{attrs({"colorTheme": p.get("colorTheme", "info"), "heading": p.get("heading"), "hasIcon": p.get("hasIcon", True)})}>'
            f'{t(p["text"])}</Message>')


def tabs(p: Dict) -> str:
    req(p, 'AMP-11', 'items')
    heads = ''.join(f'<Tabs.Item value={t(str(i))}>{t(it["label"])}</Tabs.Item>' for i, it in enumerate(p['items']))
    panels = ''.join(f'<Tabs.Panel value={t(str(i))}>{t(it["content"])}</Tabs.Panel>' for i, it in enumerate(p['items']))
    return f'<Tabs.Container defaultValue={t(str(p.get("default", 0)))}><Tabs.List>{heads}</Tabs.List>{panels}</Tabs.Container>'


def menu(p: Dict) -> str:
    req(p, 'AMP-12', 'label', 'items')
    items = ''.join(f'<MenuItem{attrs({"onClick": "{" + i["onClick"] + "}"}) if i.get("onClick") else ""}>{t(i["label"])}</MenuItem>'
                    for i in p['items'])
    return f'<Menu trigger={{<MenuButton>{t(p["label"])}</MenuButton>}}>{items}</Menu>'


def pagination(p: Dict) -> str:
    req(p, 'AMP-13', 'totalPages')
    page, on = p.get('currentPage', 'page'), handler(p, 'onChange') or 'handlePage'
    return f'<Pagination currentPage={{{page}}} totalPages={{{int(p["totalPages"])}}} onChange={{{on}}} />'


def search_field(p: Dict) -> str:
    req(p, 'AMP-14', 'label')
    on = handler(p, 'onSubmit') or 'handleSearch'
    return f'<SearchField{attrs({"label": p["label"], "placeholder": p.get("placeholder")})} onSubmit={{{on}}} />'


def password_field(p: Dict) -> str:
    req(p, 'AMP-15', 'label', 'name')
    return f'<PasswordField{attrs({"label": p["label"], "name": p["name"], "autoComplete": p.get("autoComplete", "current-password")})} onChange={{handleChange}} />'


def switch_field(p: Dict) -> str:
    req(p, 'AMP-16', 'label', 'name')
    return f'<SwitchField{attrs({"label": p["label"], "name": p["name"], "defaultChecked": p.get("checked")})} onChange={{handleChange}} />'


def radio_group(p: Dict) -> str:
    req(p, 'AMP-17', 'legend', 'name', 'options')
    radios = ''.join(f'<Radio value={t(o["value"])}>{t(o["label"])}</Radio>' for o in p['options'])
    return f'<RadioGroupField{attrs({"legend": p["legend"], "name": p["name"]})} onChange={{handleChange}}>{radios}</RadioGroupField>'


def textarea_field(p: Dict) -> str:
    req(p, 'AMP-18', 'label', 'name')
    return f'<TextAreaField{attrs({"label": p["label"], "name": p["name"], "rows": int(p.get("rows", 4)), "placeholder": p.get("placeholder")})} onChange={{handleChange}} />'


def breadcrumbs(p: Dict) -> str:
    req(p, 'AMP-19', 'items')
    items = ''.join(f'<Breadcrumbs.Item><Breadcrumbs.Link href={t(i["href"])}>{t(i["label"])}</Breadcrumbs.Link></Breadcrumbs.Item>'
                    for i in p['items'])
    return f'<Breadcrumbs.Container>{items}</Breadcrumbs.Container>'


def accordion(p: Dict) -> str:
    req(p, 'AMP-20', 'items')
    items = ''.join(f'<Accordion.Item value={t(str(i))}><Accordion.Trigger>{t(it["title"])}<Accordion.Icon /></Accordion.Trigger>'
                    f'<Accordion.Content>{t(it["content"])}</Accordion.Content></Accordion.Item>' for i, it in enumerate(p['items']))
    return f'<Accordion.Container>{items}</Accordion.Container>'


def authenticator(p: Dict) -> str:
    return f'<Authenticator{attrs({"hideSignUp": p.get("hideSignUp")})}><View>{t(p.get("text", "Signed in"))}</View></Authenticator>'


def storage_manager(p: Dict) -> str:
    req(p, 'AMP-22', 'path')
    types = ', '.join(f'"{x}"' for x in p.get('acceptedFileTypes', ['image/*']))
    return f'<StorageManager acceptedFileTypes={{[{types}]}} path={t(p["path"])} maxFileCount={{{int(p.get("maxFileCount", 1))}}} />'


def storage_image(p: Dict) -> str:
    req(p, 'AMP-23', 'path', 'alt')
    return f'<StorageImage path={t(p["path"])} alt={t(p["alt"])} />'


def _ui(*names: str) -> Dict[str, List[str]]:
    return {UI: list(names)}


PATTERNS: List[Pattern] = [
    Pattern('AMP-01', 'Heading', 'C', 'Heading level 1 to 6', heading, imports=_ui('Heading')),
    Pattern('AMP-02', 'Text', 'C', 'Paragraph text', text, imports=_ui('Text')),
    Pattern('AMP-03', 'Image', 'C', 'Image with alt text', image, imports=_ui('Image')),
    Pattern('AMP-04', 'Link', 'C', 'Link, optionally external', link, imports=_ui('Link')),
    Pattern('AMP-05', 'Flex', 'L', 'Flex row or column of text items', flex, imports=_ui('Flex', 'Text')),
    Pattern('AMP-06', 'Grid', 'L', 'Grid of text items', grid, imports=_ui('Grid', 'Text')),
    Pattern('AMP-07', 'Divider', 'C', 'Divider', divider, imports=_ui('Divider')),
    Pattern('AMP-08', 'Badge', 'C', 'Badge with variation', badge, imports=_ui('Badge')),
    Pattern('AMP-09', 'Loader', 'F', 'Loading indicator', loader, imports=_ui('Loader')),
    Pattern('AMP-10', 'Message', 'F', 'Message with colour theme', message, imports=_ui('Message')),
    Pattern('AMP-11', 'Tabs', 'C', 'Tabs with panels', tabs, imports=_ui('Tabs')),
    Pattern('AMP-12', 'Menu', 'C', 'Menu button with items', menu, imports=_ui('Menu', 'MenuButton', 'MenuItem')),
    Pattern('AMP-13', 'Pagination', 'I', 'Pagination bound to a page state variable', pagination, imports=_ui('Pagination')),
    Pattern('AMP-14', 'Search Field', 'C', 'Search field with submit handler', search_field, imports=_ui('SearchField')),
    Pattern('AMP-15', 'Password Field', 'C', 'Password field', password_field, imports=_ui('PasswordField')),
    Pattern('AMP-16', 'Switch Field', 'C', 'Switch', switch_field, imports=_ui('SwitchField')),
    Pattern('AMP-17', 'Radio Group', 'C', 'Radio group with options', radio_group, imports=_ui('RadioGroupField', 'Radio')),
    Pattern('AMP-18', 'Text Area', 'C', 'Multi-line text field', textarea_field, imports=_ui('TextAreaField')),
    Pattern('AMP-19', 'Breadcrumbs', 'C', 'Breadcrumb trail', breadcrumbs, imports=_ui('Breadcrumbs')),
    Pattern('AMP-20', 'Accordion', 'C', 'Accordion of items', accordion, imports=_ui('Accordion')),
    Pattern('AMP-21', 'Authenticator', 'A', 'Connected sign-in wrapper', authenticator, imports=_ui('Authenticator', 'View')),
    Pattern('AMP-22', 'Storage Manager', 'A', 'Connected file upload to storage', storage_manager, imports={STORAGE: ['StorageManager']}),
    Pattern('AMP-23', 'Storage Image', 'A', 'Connected image from storage', storage_image, imports={STORAGE: ['StorageImage']}),
]

TYPE_MAPPING = {
    'heading': 'AMP-01', 'text': 'AMP-02', 'image': 'AMP-03', 'link': 'AMP-04', 'flex': 'AMP-05', 'grid': 'AMP-06',
    'divider': 'AMP-07', 'badge': 'AMP-08', 'loader': 'AMP-09', 'message': 'AMP-10', 'tabs': 'AMP-11', 'menu': 'AMP-12',
    'pagination': 'AMP-13', 'search-field': 'AMP-14', 'password-field': 'AMP-15', 'switch-field': 'AMP-16',
    'radio-group': 'AMP-17', 'textarea-field': 'AMP-18', 'breadcrumbs': 'AMP-19', 'accordion': 'AMP-20',
    'authenticator': 'AMP-21', 'storage-manager': 'AMP-22', 'storage-image': 'AMP-23',
}

SAMPLES: Dict[str, Dict[str, Any]] = {
    'AMP-01': {'text': 'Title', 'level': 1},
    'AMP-02': {'text': 'Body copy', 'variation': 'secondary'},
    'AMP-03': {'src': '/a.png', 'alt': 'A picture', 'width': 320},
    'AMP-04': {'href': 'https://example.invalid', 'text': 'Docs', 'isExternal': True},
    'AMP-05': {'items': ['one', 'two'], 'direction': 'column'},
    'AMP-06': {'items': ['one', 'two', 'three'], 'templateColumns': '1fr 1fr 1fr'},
    'AMP-07': {'orientation': 'horizontal'},
    'AMP-08': {'text': 'New', 'variation': 'success'},
    'AMP-09': {'size': 'small'},
    'AMP-10': {'heading': 'Saved', 'text': 'Your changes were saved.', 'colorTheme': 'success'},
    'AMP-11': {'items': [{'label': 'One', 'content': 'First'}, {'label': 'Two', 'content': 'Second'}]},
    'AMP-12': {'label': 'Actions', 'items': [{'label': 'Edit', 'onClick': 'handleEdit'}, {'label': 'Delete'}]},
    'AMP-13': {'totalPages': 10, 'currentPage': 'page', 'onChange': 'handlePage'},
    'AMP-14': {'label': 'Search', 'placeholder': 'Find', 'onSubmit': 'handleSearch'},
    'AMP-15': {'label': 'Password', 'name': 'password'},
    'AMP-16': {'label': 'Notifications', 'name': 'notify', 'checked': True},
    'AMP-17': {'legend': 'Size', 'name': 'size', 'options': [{'label': 'Small', 'value': 's'}, {'label': 'Large', 'value': 'l'}]},
    'AMP-18': {'label': 'Notes', 'name': 'notes', 'rows': 3},
    'AMP-19': {'items': [{'label': 'Home', 'href': '/'}, {'label': 'Here', 'href': '/here'}]},
    'AMP-20': {'items': [{'title': 'Q1', 'content': 'A1'}, {'title': 'Q2', 'content': 'A2'}]},
    'AMP-21': {'text': 'Welcome', 'hideSignUp': True},
    'AMP-22': {'path': 'uploads/', 'acceptedFileTypes': ['image/*'], 'maxFileCount': 3},
    'AMP-23': {'path': 'uploads/a.png', 'alt': 'Uploaded picture'},
}


def register(library) -> None:
    for pattern in PATTERNS:
        library.register(pattern)
