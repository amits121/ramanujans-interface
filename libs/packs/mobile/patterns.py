#!/usr/bin/env python3
"""
Mobile pack (MOB-00 to MOB-17): React Native and Expo components plus the field-operations
patterns proven in production (code login, choice buttons, sync pill, map in a web view).
Target: react-native. One shared StyleSheet block is emitted once per file.

Copyright (c) 2025 Intelligent Cloud Lab Inc.
All rights reserved.
"""

from typing import Any, Dict, List

from libs.jsx import handler, req, t
from pattern_library import Pattern

RN = 'react-native'

STYLES = """const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: '#F8F9FA' },
  content: { padding: 16, gap: 12 },
  section: { gap: 8 },
  heading: { fontSize: 24, fontWeight: '700', color: '#1B2838' },
  subheading: { fontSize: 18, fontWeight: '600', color: '#1B2838' },
  text: { fontSize: 16, lineHeight: 24, color: '#1B2838' },
  button: { minHeight: 48, borderRadius: 8, backgroundColor: '#3B5BDB', alignItems: 'center', justifyContent: 'center', paddingHorizontal: 16 },
  buttonSecondary: { backgroundColor: 'transparent', borderWidth: 1, borderColor: '#3B5BDB' },
  buttonText: { fontSize: 16, fontWeight: '600', color: '#FFFFFF' },
  buttonTextSecondary: { color: '#3B5BDB' },
  field: { gap: 4 },
  label: { fontSize: 14, fontWeight: '500', color: '#1B2838' },
  input: { minHeight: 48, borderWidth: 1, borderColor: '#E5E7EB', borderRadius: 8, paddingHorizontal: 16, fontSize: 16, backgroundColor: '#FFFFFF' },
  codeInput: { minHeight: 56, fontSize: 28, letterSpacing: 8, textAlign: 'center' },
  card: { backgroundColor: '#FFFFFF', borderRadius: 12, borderWidth: 1, borderColor: '#E5E7EB', padding: 16, gap: 4 },
  cardTitle: { fontSize: 18, fontWeight: '600', color: '#1B2838' },
  row: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', gap: 8 },
  wrap: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  choice: { minHeight: 56, flexGrow: 1, borderRadius: 8, alignItems: 'center', justifyContent: 'center', paddingHorizontal: 12 },
  choiceText: { fontSize: 16, fontWeight: '600', color: '#FFFFFF' },
  modal: { flex: 1, justifyContent: 'flex-end', backgroundColor: 'rgba(0,0,0,0.5)' },
  modalContent: { backgroundColor: '#FFFFFF', borderTopLeftRadius: 16, borderTopRightRadius: 16, padding: 24, gap: 12 },
  pill: { flexDirection: 'row', alignItems: 'center', gap: 6, paddingHorizontal: 12, minHeight: 32, borderRadius: 16, backgroundColor: '#FFFFFF', borderWidth: 1, borderColor: '#E5E7EB' },
  pillText: { fontSize: 14, fontWeight: '600', color: '#1B2838' },
  dot: { width: 10, height: 10, borderRadius: 5 },
  dotOn: { backgroundColor: '#2ED573' },
  dotOff: { backgroundColor: '#FF4757' },
  link: { color: '#3B5BDB', fontSize: 16, lineHeight: 44 },
  map: { height: 320, borderRadius: 12, overflow: 'hidden' },
});"""
MODULE = {'mobile-styles': STYLES}
WRAPPER = ('<SafeAreaView style={styles.screen}><ScrollView contentContainerStyle={styles.content}>\n'
           '                {children}\n            </ScrollView></SafeAreaView>')


def _setter(var: str) -> str:
    return 'set' + var[0].upper() + var[1:]


def styles(p: Dict) -> str:
    return ''


def section(p: Dict) -> str:
    head = f'<Text style={{styles.subheading}}>{t(p["title"])}</Text>' if p.get('title') else ''
    body = ''.join(f'<Text style={{styles.text}}>{t(x)}</Text>' for x in p.get('paragraphs', []))
    return f'<View style={{styles.section}}>{head}{body}</View>'


def heading(p: Dict) -> str:
    req(p, 'MOB-02', 'text')
    style = 'styles.heading' if int(p.get('level', 1)) == 1 else 'styles.subheading'
    return f'<Text style={{{style}}} accessibilityRole="header">{t(p["text"])}</Text>'


def text(p: Dict) -> str:
    req(p, 'MOB-03', 'text')
    return f'<Text style={{styles.text}}>{t(p["text"])}</Text>'


def button(p: Dict) -> str:
    req(p, 'MOB-04', 'label')
    on = handler(p, 'onPress') or 'handlePress'
    if p.get('variant') == 'secondary':
        return (f'<Pressable style={{[styles.button, styles.buttonSecondary]}} onPress={{{on}}} accessibilityRole="button">'
                f'<Text style={{[styles.buttonText, styles.buttonTextSecondary]}}>{t(p["label"])}</Text></Pressable>')
    return f'<Pressable style={{styles.button}} onPress={{{on}}} accessibilityRole="button"><Text style={{styles.buttonText}}>{t(p["label"])}</Text></Pressable>'


def text_input(p: Dict) -> str:
    req(p, 'MOB-05', 'label', 'name')
    var = p['name']
    extra = ' secureTextEntry' if p.get('secure') else ''
    kb = f' keyboardType={t(p["keyboardType"])}' if p.get('keyboardType') else ''
    return (f'<View style={{styles.field}}><Text style={{styles.label}}>{t(p["label"])}</Text>'
            f'<TextInput style={{styles.input}} placeholder={t(p.get("placeholder", ""))} value={{{var}}} onChangeText={{{_setter(var)}}}'
            f'{kb}{extra} accessibilityLabel={t(p["label"])} /></View>')


def list_(p: Dict) -> str:
    req(p, 'MOB-06', 'fields')
    var, key = p.get('state', 'items'), p.get('keyField', 'id')
    first, rest = p['fields'][0], p['fields'][1:]
    lines = f'<Text style={{styles.cardTitle}}>{{item.{first}}}</Text>' + ''.join(f'<Text style={{styles.text}}>{{item.{f}}}</Text>' for f in rest)
    return (f'<FlatList data={{{var}}} keyExtractor={{(item) => String(item.{key})}} '
            f'renderItem={{({{ item }}) => (<View style={{styles.card}}>{lines}</View>)}} scrollEnabled={{false}} />')


def card(p: Dict) -> str:
    req(p, 'MOB-07', 'title')
    body = f'<Text style={{styles.text}}>{t(p["text"])}</Text>' if p.get('text') else ''
    return f'<View style={{styles.card}}><Text style={{styles.cardTitle}}>{t(p["title"])}</Text>{body}</View>'


def modal(p: Dict) -> str:
    req(p, 'MOB-08', 'visible', 'title')
    on = handler(p, 'onClose') or 'handleClose'
    body = f'<Text style={{styles.text}}>{t(p["text"])}</Text>' if p.get('text') else ''
    return (f'<Modal visible={{{p["visible"]}}} transparent animationType="slide" onRequestClose={{{on}}}>'
            f'<View style={{styles.modal}}><View style={{styles.modalContent}}><Text style={{styles.subheading}}>{t(p["title"])}</Text>{body}'
            f'<Pressable style={{styles.button}} onPress={{{on}}} accessibilityRole="button"><Text style={{styles.buttonText}}>{t(p.get("closeLabel", "Close"))}</Text></Pressable>'
            f'</View></View></Modal>')


def loader(p: Dict) -> str:
    return f'<ActivityIndicator size={t(p.get("size", "large"))} accessibilityLabel={t(p.get("label", "Loading"))} />'


def switch(p: Dict) -> str:
    req(p, 'MOB-10', 'label', 'state')
    var = p['state']
    return f'<View style={{styles.row}}><Text style={{styles.text}}>{t(p["label"])}</Text><Switch value={{{var}}} onValueChange={{{_setter(var)}}} /></View>'


def image(p: Dict) -> str:
    req(p, 'MOB-11', 'uri', 'alt')
    w, h = int(p.get('width', 320)), int(p.get('height', 200))
    return f'<Image source={{{{ uri: {t(p["uri"])[1:-1]} }}}} accessibilityLabel={t(p["alt"])} style={{{{ width: {w}, height: {h}, borderRadius: 12 }}}} />'


def status_bar(p: Dict) -> str:
    return f'<StatusBar style={t(p.get("style", "dark"))} />'


def link(p: Dict) -> str:
    req(p, 'MOB-13', 'href', 'text')
    return f'<Link href={t(p["href"])} style={{styles.link}}>{t(p["text"])}</Link>'


def map_webview(p: Dict) -> str:
    req(p, 'MOB-14', 'uri')
    return f'<WebView source={{{{ uri: {t(p["uri"])[1:-1]} }}}} style={{styles.map}} />'


def code_login(p: Dict) -> str:
    var, on = p.get('state', 'code'), handler(p, 'onSubmit') or 'handleLogin'
    return (f'<View style={{styles.section}}><Text style={{styles.label}}>{t(p.get("label", "Enter your code"))}</Text>'
            f'<TextInput style={{[styles.input, styles.codeInput]}} value={{{var}}} onChangeText={{{_setter(var)}}} maxLength={{{int(p.get("length", 5))}}} '
            f'autoCapitalize="none" autoCorrect={{false}} accessibilityLabel={t(p.get("label", "Enter your code"))} />'
            f'<Pressable style={{styles.button}} onPress={{{on}}} accessibilityRole="button"><Text style={{styles.buttonText}}>{t(p.get("submit", "Continue"))}</Text></Pressable></View>')


def choice_row(p: Dict) -> str:
    req(p, 'MOB-16', 'options')
    on = handler(p, 'onPress') or 'handleChoice'
    btns = ''.join(f'<Pressable style={{[styles.choice, {{ backgroundColor: {t(o.get("color", "#3B5BDB"))[1:-1]} }}]}} onPress={{() => {on}({t(o["value"])[1:-1]})}} '
                   f'accessibilityRole="button"><Text style={{styles.choiceText}}>{t(o["label"])}</Text></Pressable>' for o in p['options'])
    return f'<View style={{styles.wrap}}>{btns}</View>'


def sync_pill(p: Dict) -> str:
    count, online = p.get('count', 'pending'), p.get('online', 'online')
    return (f'<View style={{styles.pill}} accessibilityLabel="Sync status"><View style={{[styles.dot, {online} ? styles.dotOn : styles.dotOff]}} />'
            f'<Text style={{styles.pillText}}>{{{count}}}</Text></View>')


def _rn(*names: str) -> Dict[str, List[str]]:
    return {RN: list(names)}


PATTERNS: List[Pattern] = [
    Pattern('MOB-00', 'Styles', 'X', 'Shared StyleSheet block', styles, imports=_rn('StyleSheet'), module=MODULE),
    Pattern('MOB-01', 'Section', 'L', 'Titled section of paragraphs', section, imports=_rn('View', 'Text', 'StyleSheet'), module=MODULE),
    Pattern('MOB-02', 'Heading', 'C', 'Heading text', heading, imports=_rn('Text', 'StyleSheet'), module=MODULE),
    Pattern('MOB-03', 'Text', 'C', 'Body text', text, imports=_rn('Text', 'StyleSheet'), module=MODULE),
    Pattern('MOB-04', 'Button', 'C', 'Pressable button', button, imports=_rn('Pressable', 'Text', 'StyleSheet'), module=MODULE),
    Pattern('MOB-05', 'Text Input', 'C', 'Labelled text input bound to state', text_input, imports=_rn('View', 'Text', 'TextInput', 'StyleSheet'), module=MODULE),
    Pattern('MOB-06', 'List', 'I', 'FlatList of cards from state', list_, imports=_rn('FlatList', 'View', 'Text', 'StyleSheet'), module=MODULE),
    Pattern('MOB-07', 'Card', 'C', 'Card with title and text', card, imports=_rn('View', 'Text', 'StyleSheet'), module=MODULE),
    Pattern('MOB-08', 'Modal', 'F', 'Bottom sheet modal bound to a visible state', modal, imports=_rn('Modal', 'View', 'Text', 'Pressable', 'StyleSheet'), module=MODULE),
    Pattern('MOB-09', 'Loader', 'F', 'Activity indicator', loader, imports=_rn('ActivityIndicator')),
    Pattern('MOB-10', 'Switch', 'C', 'Switch bound to state', switch, imports=_rn('View', 'Text', 'Switch', 'StyleSheet'), module=MODULE),
    Pattern('MOB-11', 'Image', 'C', 'Remote image with label', image, imports=_rn('Image')),
    Pattern('MOB-12', 'Status Bar', 'C', 'Expo status bar', status_bar, imports={'expo-status-bar': ['StatusBar']}),
    Pattern('MOB-13', 'Link', 'E', 'Expo Router link', link, imports={'expo-router': ['Link'], RN: ['StyleSheet']}, module=MODULE),
    Pattern('MOB-14', 'Map Web View', 'C', 'Map page in a web view', map_webview, imports={'react-native-webview': ['WebView'], RN: ['StyleSheet']}, module=MODULE),
    Pattern('MOB-15', 'Code Login', 'C', 'Short-code login screen', code_login, imports=_rn('View', 'Text', 'TextInput', 'Pressable', 'StyleSheet'), module=MODULE),
    Pattern('MOB-16', 'Choice Button Row', 'C', 'Row of outcome buttons', choice_row, imports=_rn('View', 'Text', 'Pressable', 'StyleSheet'), module=MODULE),
    Pattern('MOB-17', 'Sync Pill', 'F', 'Pending count with online dot', sync_pill, imports=_rn('View', 'Text', 'StyleSheet'), module=MODULE),
]

TYPE_MAPPING = {'styles': 'MOB-00', 'section': 'MOB-01', 'heading': 'MOB-02', 'text': 'MOB-03', 'button': 'MOB-04', 'text-input': 'MOB-05',
                'list': 'MOB-06', 'card': 'MOB-07', 'modal': 'MOB-08', 'loader': 'MOB-09', 'switch': 'MOB-10', 'image': 'MOB-11',
                'status-bar': 'MOB-12', 'link': 'MOB-13', 'map-webview': 'MOB-14', 'code-login': 'MOB-15', 'choice-button-row': 'MOB-16',
                'sync-pill': 'MOB-17'}

SAMPLES: Dict[str, Dict[str, Any]] = {
    'MOB-00': {}, 'MOB-01': {'title': 'About', 'paragraphs': ['One.', 'Two.']}, 'MOB-02': {'text': 'Hello', 'level': 1},
    'MOB-03': {'text': 'Body'}, 'MOB-04': {'label': 'Save', 'onPress': 'handleSave', 'variant': 'primary'},
    'MOB-05': {'label': 'Name', 'name': 'name', 'placeholder': 'Your name'}, 'MOB-06': {'state': 'homes', 'fields': ['address', 'city']},
    'MOB-07': {'title': 'Card', 'text': 'Text'}, 'MOB-08': {'visible': 'showHelp', 'title': 'Help', 'text': 'Tap a door.', 'onClose': 'handleClose'},
    'MOB-09': {'size': 'large'}, 'MOB-10': {'label': 'Offline mode', 'state': 'offline'},
    'MOB-11': {'uri': 'https://example.invalid/a.png', 'alt': 'Picture', 'width': 300, 'height': 200},
    'MOB-12': {'style': 'light'}, 'MOB-13': {'href': '/settings', 'text': 'Settings'}, 'MOB-14': {'uri': 'https://example.invalid/map'},
    'MOB-15': {'state': 'code', 'onSubmit': 'handleLogin', 'length': 5},
    'MOB-16': {'options': [{'label': 'Support', 'value': 'support', 'color': '#2ED573'}, {'label': 'Not home', 'value': 'not_home', 'color': '#6B7280'}], 'onPress': 'handleOutcome'},
    'MOB-17': {'count': 'pending', 'online': 'online'},
}


def register(library) -> None:
    for pattern in PATTERNS:
        library.register(pattern)
