#!/usr/bin/env python3
"""
Firebase pack (FB-01 to FB-06): app init, email and Google sign-in, Firestore list,
Storage upload, FirebaseUI container. Target: firebase (web). Configuration values are
never written into code: the init block reads environment variables by name.

Copyright (c) 2025 Intelligent Cloud Lab Inc.
All rights reserved.
"""

import json
from typing import Any, Dict, List

from libs.jsx import handler, req, t
from pattern_library import Pattern

CONFIG_KEYS = ('apiKey', 'authDomain', 'projectId', 'storageBucket', 'messagingSenderId', 'appId')


def app_init(p: Dict) -> str:
    return ''


def _module_app(p: Dict) -> Dict[str, str]:
    prefix = p.get('envPrefix', 'VITE_FIREBASE_')
    rows = ',\n'.join(f'  {k}: import.meta.env.{prefix}{k.upper()}' for k in CONFIG_KEYS)
    return {'firebase-app': 'export const firebaseApp = initializeApp({\n' + rows + '\n});'}


def auth_email_form(p: Dict) -> str:
    on = handler(p, 'onSubmit') or 'handleEmailSignIn'
    labels = {'email': 'Email', 'password': 'Password', 'submit': 'Sign in', **p.get('labels', {})}
    return (f'<form className="fb-auth" onSubmit={{{on}}}>'
            f'<label htmlFor="fb-email">{t(labels["email"])}</label>'
            f'<input id="fb-email" type="email" autoComplete="email" value={{email}} onChange={{(e) => setEmail(e.target.value)}} required />'
            f'<label htmlFor="fb-password">{t(labels["password"])}</label>'
            f'<input id="fb-password" type="password" autoComplete="current-password" value={{password}} onChange={{(e) => setPassword(e.target.value)}} required />'
            f'<button type="submit">{t(labels["submit"])}</button></form>')


EMAIL_HANDLER = ('async (e: React.FormEvent) => {\n        e.preventDefault();\n'
                 '        await signInWithEmailAndPassword(getAuth(), email, password);\n    }')


def google_button(p: Dict) -> str:
    on = handler(p, 'onClick') or 'handleGoogleSignIn'
    return f'<button type="button" className="fb-google" onClick={{{on}}}>{t(p.get("label", "Continue with Google"))}</button>'


GOOGLE_HANDLER = 'async () => {\n        await signInWithPopup(getAuth(), new GoogleAuthProvider());\n    }'


def firestore_list(p: Dict) -> str:
    req(p, 'FB-04', 'collection', 'fields')
    var = p.get('state', 'items')
    cells = ''.join(f'<span>{{item.{f}}}</span>' for f in p['fields'])
    return f'<ul className="fb-list">{{{var}.map((item) => (<li key={{item.id}}>{cells}</li>))}}</ul>'


def _effect_firestore(p: Dict) -> List[str]:
    var = p.get('state', 'items')
    setter = 'set' + var[0].upper() + var[1:]
    return [f'    useEffect(() => {{\n        getDocs(collection(getFirestore(), {json.dumps(p["collection"])}))'
            f'.then((snap) => {setter}(snap.docs.map((d) => ({{ id: d.id, ...d.data() }}))));\n    }}, []);']


def storage_upload(p: Dict) -> str:
    on = handler(p, 'onChange') or 'handleUpload'
    return (f'<label htmlFor="fb-file">{t(p.get("label", "Choose a file"))}</label>'
            f'<input id="fb-file" type="file" onChange={{{on}}} />')


def _handler_upload(p: Dict) -> Dict[str, str]:
    prefix = p.get('path', 'uploads/')
    return {handler(p, 'onChange') or 'handleUpload':
            ('async (e: React.ChangeEvent<HTMLInputElement>) => {\n        const file = e.target.files && e.target.files[0];\n'
             '        if (!file) return;\n'
             f'        await uploadBytes(ref(getStorage(), {json.dumps(prefix)} + file.name), file);\n    }}')}


def firebaseui_auth(p: Dict) -> str:
    return '<div id="firebaseui-auth-container"></div>'


def _effect_firebaseui(p: Dict) -> List[str]:
    providers = {'google': 'GoogleAuthProvider.PROVIDER_ID', 'email': 'EmailAuthProvider.PROVIDER_ID'}
    opts = ', '.join(providers[x] for x in p.get('providers', ['google', 'email']) if x in providers)
    url = json.dumps(p.get('signInSuccessUrl', '/'))
    return ['    useEffect(() => {\n        const ui = firebaseui.auth.AuthUI.getInstance() || new firebaseui.auth.AuthUI(getAuth());\n'
            f'        ui.start(\'#firebaseui-auth-container\', {{ signInOptions: [{opts}], signInSuccessUrl: {url} }});\n    }}, []);']


class DynamicPattern(Pattern):
    """A pattern whose module block, handlers and effects depend on its props."""

    def __init__(self, *args, module_fn=None, handlers_fn=None, effects_fn=None, **kwargs):
        super().__init__(*args, **kwargs)
        object.__setattr__(self, 'module_fn', module_fn)
        object.__setattr__(self, 'handlers_fn', handlers_fn)
        object.__setattr__(self, 'effects_fn', effects_fn)

    def generate(self, props: Dict[str, Any]) -> str:
        if self.module_fn:
            self.module.clear(); self.module.update(self.module_fn(props))
        if self.handlers_fn:
            self.handlers.clear(); self.handlers.update(self.handlers_fn(props))
        if self.effects_fn:
            self.effects.clear(); self.effects.extend(self.effects_fn(props))
        return self.generator(props)


PATTERNS: List[Pattern] = [
    DynamicPattern('FB-01', 'App Init', 'A', 'initializeApp from environment variables', app_init,
                   imports={'firebase/app': ['initializeApp']}, module_fn=_module_app),
    Pattern('FB-02', 'Email Sign-in Form', 'A', 'Email and password sign-in bound to state', auth_email_form,
            imports={'firebase/auth': ['getAuth', 'signInWithEmailAndPassword']}, handlers={'handleEmailSignIn': EMAIL_HANDLER}),
    Pattern('FB-03', 'Google Sign-in Button', 'A', 'Popup sign-in with Google', google_button,
            imports={'firebase/auth': ['getAuth', 'signInWithPopup', 'GoogleAuthProvider']}, handlers={'handleGoogleSignIn': GOOGLE_HANDLER}),
    DynamicPattern('FB-04', 'Firestore List', 'D', 'Collection fetched into state and listed', firestore_list,
                   imports={'firebase/firestore': ['getFirestore', 'collection', 'getDocs'], 'react': ['useEffect']}, effects_fn=_effect_firestore),
    DynamicPattern('FB-05', 'Storage Upload', 'A', 'File input uploading to Storage', storage_upload,
                   imports={'firebase/storage': ['getStorage', 'ref', 'uploadBytes']}, handlers_fn=_handler_upload),
    DynamicPattern('FB-06', 'FirebaseUI Auth', 'A', 'FirebaseUI drop-in sign-in container', firebaseui_auth,
                   imports={'firebaseui': ['*:firebaseui'], 'firebaseui/dist/firebaseui.css': [],
                            'firebase/auth': ['getAuth', 'GoogleAuthProvider', 'EmailAuthProvider'], 'react': ['useEffect']},
                   effects_fn=_effect_firebaseui),
]

TYPE_MAPPING = {'firebase-app': 'FB-01', 'firebase-email-form': 'FB-02', 'firebase-google-button': 'FB-03',
                'firestore-list': 'FB-04', 'storage-upload': 'FB-05', 'firebaseui-auth': 'FB-06'}

SAMPLES: Dict[str, Dict[str, Any]] = {
    'FB-01': {'envPrefix': 'VITE_FIREBASE_'},
    'FB-02': {'onSubmit': 'handleEmailSignIn', 'labels': {'submit': 'Log in'}},
    'FB-03': {'label': 'Continue with Google'},
    'FB-04': {'collection': 'posts', 'fields': ['title', 'author'], 'state': 'posts'},
    'FB-05': {'label': 'Upload a photo', 'path': 'photos/'},
    'FB-06': {'providers': ['google', 'email'], 'signInSuccessUrl': '/home'},
}


def register(library) -> None:
    for pattern in PATTERNS:
        library.register(pattern)
