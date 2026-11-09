#!/usr/bin/env python3
"""
Behaviour Patterns Module - the first pattern of each remaining category of the filing.

    D-01  bound-input      data binding   input bound to a state variable
    D-02  template-text    data binding   text with {variable} expressions over state
    E-01  form             event          submit handler that validates, then acts (holds children)
    ST-01 async-status     state          idle, loading, error, done status with an error message
    V-01  validator        validation     required, email, minLength, maxLength, pattern rules per field
    A-01  fetch-on-load    API            GET on mount into a state variable
    A-02  submit-request   API            POST, PUT or DELETE of state variables
    F-01  status-feedback  feedback       loading and error messages bound to the status
    I-01  list             iteration      list of records from a state variable
    X-01  show-if          conditional    renders its children when a state variable matches

Plain JSX, no component framework, so these register on every web target. Each pattern
is a pure function of its props; what it needs outside the JSX (state, handlers, effects,
imports) it declares through declare(props, context), and the mapper merges the
declarations once per key. A state variable a pattern reads must be declared in the
specification or by a pattern earlier in the document (declare before use).

The State category keeps the prefix ST because S-xx names the site patterns.

Copyright (c) 2026 Intelligent Cloud Lab Inc.
All rights reserved.

Author: Amit Sarkar
Version: 1.0.0
"""

import json
import re
from typing import Any, Dict, List

from pattern_library import Pattern, PatternLibrary

BEHAVIOR_TYPE_MAPPING = {
    'bound-input': 'D-01',
    'template-text': 'D-02',
    'form': 'E-01',
    'async-status': 'ST-01',
    'validator': 'V-01',
    'fetch-on-load': 'A-01',
    'submit-request': 'A-02',
    'status-feedback': 'F-01',
    'list': 'I-01',
    'show-if': 'X-01',
}

STATUS_TYPE = {'async-status-type': "type AsyncStatus = 'idle' | 'loading' | 'error' | 'done';"}
RULE_TYPES = ('required', 'email', 'minLength', 'maxLength', 'pattern')
EMAIL_REGEX = r'/^[^\s@]+@[^\s@]+\.[^\s@]+$/'
METHODS = ('POST', 'PUT', 'DELETE')


def _t(value: Any) -> str:
    return '{' + json.dumps(str(value), ensure_ascii=False) + '}'


def _js(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False)


def _req(props: Dict[str, Any], pattern_id: str, *keys: str) -> None:
    for key in keys:
        if key not in props or props[key] in ('', None, []):
            raise ValueError(f'{pattern_id} requires "{key}"')


def _ident(value: Any, pattern_id: str, what: str) -> str:
    if not (isinstance(value, str) and value.isidentifier()):
        raise ValueError(f'{pattern_id}: {what} must be an identifier, got {value!r}')
    return value


def _setter(var: str) -> str:
    return 'set' + var[0].upper() + var[1:]


def _state_var(name: str, context: Dict[str, Any], pattern_id: str) -> str:
    name = _ident(name, pattern_id, 'state variable')
    if name not in context['state']:
        raise ValueError(f'{pattern_id} on component {context["component_id"]}: state variable "{name}" is not '
                         f'declared in the specification or by an earlier pattern')
    return name


def _status_declarations(p: Dict) -> Dict[str, Any]:
    status, error = p.get('status', 'status'), p.get('errorName', 'errorMessage')
    return {'module': STATUS_TYPE,
            'state': {status: "useState<AsyncStatus>('idle')", error: "useState('')"}}


def _request_body(p: Dict, pattern_id: str, call: str, success: str) -> str:
    status, error = p.get('status', 'status'), p.get('errorName', 'errorMessage')
    lines = ['async () => {',
             f'        {_setter(status)}(\'loading\');',
             '        try {',
             f'            const response = await {call};',
             '            if (!response.ok) throw new Error(\'Request failed: \' + response.status);',
             f'            {success}',
             f'            {_setter(status)}(\'done\');',
             '        } catch (error) {',
             f'            {_setter(error)}(error instanceof Error ? error.message : String(error));',
             f'            {_setter(status)}(\'error\');',
             '        }',
             '    }']
    return '\n'.join(lines)


# ---- D: data binding --------------------------------------------------------------------------

def bound_input(p: Dict) -> str:
    _req(p, 'D-01', 'label', 'state')
    var, name = p['state'], p.get('name', p['state'])
    attrs = [f'id={_t(name)}', f'name={_t(name)}', f'type={_t(p.get("type", "text"))}',
             f'value={{{var}}}', f'onChange={{(e) => {_setter(var)}(e.target.value)}}']
    if p.get('placeholder'):
        attrs.append(f'placeholder={_t(p["placeholder"])}')
    if p.get('autoComplete'):
        attrs.append(f'autoComplete={_t(p["autoComplete"])}')
    if p.get('required'):
        attrs.append('required')
    return (f'<div className="field"><label htmlFor={_t(name)}>{_t(p["label"])}</label>'
            f'<input {" ".join(attrs)} /></div>')


def _declare_bound_input(p: Dict, context: Dict) -> Dict[str, Any]:
    _state_var(p['state'], context, 'D-01')
    return {}


def _template_parts(template: str) -> List[str]:
    parts = []
    for i, piece in enumerate(re.split(r'\{([A-Za-z_][A-Za-z0-9_]*)\}', template)):
        if i % 2 == 1:
            parts.append(f'String({piece})')
        elif piece:
            parts.append(_js(piece))
    return parts or ['""']


def template_text(p: Dict) -> str:
    _req(p, 'D-02', 'template')
    tag = p.get('tag', 'p')
    cls = f' className={_t(p["className"])}' if p.get('className') else ''
    return f'<{tag}{cls}>{{{" + ".join(_template_parts(p["template"]))}}}</{tag}>'


def _declare_template_text(p: Dict, context: Dict) -> Dict[str, Any]:
    for var in re.findall(r'\{([A-Za-z_][A-Za-z0-9_]*)\}', p['template']):
        _state_var(var, context, 'D-02')
    return {}


# ---- E: event ----------------------------------------------------------------------------------

def form(p: Dict) -> str:
    _req(p, 'E-01', 'onSubmit')
    label = f' aria-label={_t(p["ariaLabel"])}' if p.get('ariaLabel') else ''
    submit = ''
    if p.get('submit'):
        submit = f'<button type="submit" className="form-submit">{_t(p["submit"].get("label", "Submit"))}</button>'
    return f'<form className="form"{label} onSubmit={{{p["onSubmit"]}}} noValidate>{{children}}{submit}</form>'


def _declare_form(p: Dict, context: Dict) -> Dict[str, Any]:
    on = _ident(p['onSubmit'], 'E-01', 'onSubmit')
    body = ['(e: React.FormEvent) => {', '        e.preventDefault();']
    references = []
    if p.get('validate'):
        validate = _ident(p['validate'], 'E-01', 'validate')
        body.append(f'        if (!{validate}()) return;')
        references.append(validate)
    if p.get('action'):
        action = _ident(p['action'], 'E-01', 'action')
        body.append(f'        {action}();')
        references.append(action)
    body.append('    }')
    return {'handlers': {on: '\n'.join(body)}, 'references': references}


# ---- ST: state ---------------------------------------------------------------------------------

def async_status(p: Dict) -> str:
    return ''


def _declare_async_status(p: Dict, context: Dict) -> Dict[str, Any]:
    return _status_declarations(p)


# ---- V: validation -----------------------------------------------------------------------------

def _rule_check(var: str, rule: Dict[str, Any]) -> str:
    kind = rule.get('type')
    if kind not in RULE_TYPES:
        raise ValueError(f'V-01: unknown rule type {kind!r} (allowed: {", ".join(RULE_TYPES)})')
    if kind == 'required':
        return f'{var}.trim() === \'\''
    if kind == 'email':
        return f'!{EMAIL_REGEX}.test({var})'
    if kind == 'minLength':
        return f'{var}.length < {int(rule["value"])}'
    if kind == 'maxLength':
        return f'{var}.length > {int(rule["value"])}'
    return f'!new RegExp({_js(str(rule["value"]))}).test({var})'


def validator(p: Dict) -> str:
    _req(p, 'V-01', 'name', 'fields')
    errors = p.get('errorsState', 'errors')
    return (f'{{Object.keys({errors}).length > 0 && (<ul className="form-errors" role="alert">'
            f'{{Object.entries({errors}).map(([field, message]) => (<li key={{field}}>{{message}}</li>))}}</ul>)}}')


def _declare_validator(p: Dict, context: Dict) -> Dict[str, Any]:
    name = _ident(p['name'], 'V-01', 'name')
    errors = _ident(p.get('errorsState', 'errors'), 'V-01', 'errorsState')
    lines = ['() => {', '        const next: Record<string, string> = {};']
    for field in p['fields']:
        var = _state_var(field['field'], context, 'V-01')
        first = True
        for rule in field.get('rules', []):
            if 'message' not in rule:
                raise ValueError(f'V-01: every rule needs a "message" ({var})')
            keyword = 'if' if first else 'else if'
            lines.append(f'        {keyword} ({_rule_check(var, rule)}) next.{var} = {_js(rule["message"])};')
            first = False
    lines += [f'        {_setter(errors)}(next);', '        return Object.keys(next).length === 0;', '    }']
    return {'handlers': {name: '\n'.join(lines)},
            'state': {errors: 'useState<Record<string, string>>({})'}}


# ---- A: API ------------------------------------------------------------------------------------

def fetch_on_load(p: Dict) -> str:
    return ''


def _declare_fetch_on_load(p: Dict, context: Dict) -> Dict[str, Any]:
    _req(p, 'A-01', 'endpoint', 'state')
    var = _state_var(p['state'], context, 'A-01')
    name = _ident(p.get('name', 'load' + var[0].upper() + var[1:]), 'A-01', 'name')
    decl = _status_declarations(p)
    decl['handlers'] = {name: _request_body(p, 'A-01', f'fetch({_js(p["endpoint"])})',
                                            f'{_setter(var)}(await response.json());')}
    decl['effects'] = ['    useEffect(() => {\n'
                       f'        {name}();\n'
                       '        // eslint-disable-next-line react-hooks/exhaustive-deps\n'
                       '    }, []);']
    decl['imports'] = {'react': ['useEffect']}
    return decl


def submit_request(p: Dict) -> str:
    return ''


def _declare_submit_request(p: Dict, context: Dict) -> Dict[str, Any]:
    _req(p, 'A-02', 'name', 'endpoint')
    name = _ident(p['name'], 'A-02', 'name')
    method = p.get('method', 'POST')
    if method not in METHODS:
        raise ValueError(f'A-02: method must be one of {", ".join(METHODS)}')
    body_vars = [_state_var(v, context, 'A-02') for v in p.get('body', [])]
    options = [f'method: {_js(method)}', "headers: { 'Content-Type': 'application/json' }"]
    if body_vars:
        options.append(f'body: JSON.stringify({{ {", ".join(body_vars)} }})')
    call = f'fetch({_js(p["endpoint"])}, {{ {", ".join(options)} }})'
    success = ['const data = await response.json();']
    references = []
    if p.get('state'):
        success.append(f'{_setter(_state_var(p["state"], context, "A-02"))}(data);')
    if p.get('onSuccess'):
        references.append(_ident(p['onSuccess'], 'A-02', 'onSuccess'))
        success.append(f'{p["onSuccess"]}();')
    if len(success) == 1:
        success = ['await response.json();']
    decl = _status_declarations(p)
    decl['handlers'] = {name: _request_body(p, 'A-02', call, '\n            '.join(success))}
    decl['references'] = references
    return decl


# ---- F: feedback -------------------------------------------------------------------------------

def status_feedback(p: Dict) -> str:
    status, error = p.get('status', 'status'), p.get('errorName', 'errorMessage')
    loading = _t(p.get('loadingText', 'Loading'))
    parts = [f'{{{status} === \'loading\' && (<p className="feedback-loading" role="status">{loading}</p>)}}',
             f'{{{status} === \'error\' && (<p className="feedback-error" role="alert">{{{error}}}</p>)}}']
    if p.get('doneText'):
        parts.append(f'{{{status} === \'done\' && (<p className="feedback-done" role="status">{_t(p["doneText"])}</p>)}}')
    return f'<div className="feedback" aria-live="polite">{"".join(parts)}</div>'


def _declare_status_feedback(p: Dict, context: Dict) -> Dict[str, Any]:
    return _status_declarations(p)


# ---- I: iteration ------------------------------------------------------------------------------

def list_(p: Dict) -> str:
    _req(p, 'I-01', 'state', 'fields')
    var, key = p['state'], p.get('key', 'id')
    cells = ', '.join(f'String(item.{_ident(f, "I-01", "field")} ?? \'\')' for f in p['fields'])
    empty = _t(p.get('empty', 'Nothing to show'))
    return (f'{{{var}.length === 0 ? (<p className="list-empty">{empty}</p>) : (<ul className="list">'
            f'{{{var}.map((item, index) => (<li key={{String(item.{key} ?? index)}}>{{[{cells}].join(\' \')}}</li>))}}'
            f'</ul>)}}')


def _declare_list(p: Dict, context: Dict) -> Dict[str, Any]:
    _state_var(p['state'], context, 'I-01')
    return {}


# ---- X: conditional ----------------------------------------------------------------------------

def show_if(p: Dict) -> str:
    _req(p, 'X-01', 'state')
    var = p['state']
    if 'equals' in p:
        test = f'{var} {"!==" if p.get("not") else "==="} {_js(p["equals"])}'
    else:
        test = f'{"!" if p.get("not") else ""}{var}'
    return f'{{{test} && (<>{{children}}</>)}}'


def _declare_show_if(p: Dict, context: Dict) -> Dict[str, Any]:
    _state_var(p['state'], context, 'X-01')
    return {}


PATTERNS: List[Pattern] = [
    Pattern('D-01', 'Bound Input', 'D', 'Labelled input bound to a state variable', bound_input, declare=_declare_bound_input),
    Pattern('D-02', 'Template Text', 'D', 'Text with {variable} expressions over state', template_text, declare=_declare_template_text),
    Pattern('E-01', 'Form', 'E', 'Submit handler that validates, then acts; holds children', form,
            declare=_declare_form, slots=('children',)),
    Pattern('ST-01', 'Async Status', 'S', 'idle, loading, error, done status with an error message', async_status,
            declare=_declare_async_status),
    Pattern('V-01', 'Validator', 'V', 'Rules per field into an errors state and a validate function', validator,
            declare=_declare_validator),
    Pattern('A-01', 'Fetch On Load', 'A', 'GET on mount into a state variable', fetch_on_load, declare=_declare_fetch_on_load),
    Pattern('A-02', 'Submit Request', 'A', 'POST, PUT or DELETE of state variables', submit_request, declare=_declare_submit_request),
    Pattern('F-01', 'Status Feedback', 'F', 'Loading and error messages bound to the status', status_feedback,
            declare=_declare_status_feedback),
    Pattern('I-01', 'List', 'I', 'List of records from a state variable', list_, declare=_declare_list),
    Pattern('X-01', 'Show If', 'X', 'Renders its children when a state variable matches', show_if,
            declare=_declare_show_if, slots=('children',)),
]

SAMPLES: Dict[str, Dict[str, Any]] = {
    'D-01': {'label': 'Email', 'state': 'email', 'type': 'email', 'autoComplete': 'email', 'required': True},
    'D-02': {'template': 'Welcome back, {email}.', 'tag': 'p'},
    'E-01': {'onSubmit': 'handleLogin', 'validate': 'validateLogin', 'action': 'submitLogin', 'submit': {'label': 'Sign in'}},
    'ST-01': {},
    'V-01': {'name': 'validateLogin', 'fields': [{'field': 'email', 'rules': [{'type': 'required', 'message': 'Email is required'},
                                                                             {'type': 'email', 'message': 'Enter a valid email'}]}]},
    'A-01': {'endpoint': '/api/homes', 'state': 'homes'},
    'A-02': {'name': 'submitLogin', 'endpoint': '/auth/login', 'method': 'POST', 'body': ['email', 'password']},
    'F-01': {'loadingText': 'Signing in', 'doneText': 'Signed in'},
    'I-01': {'state': 'homes', 'fields': ['address', 'city'], 'empty': 'No homes yet'},
    'X-01': {'state': 'status', 'equals': 'done'},
}


def register_behavior_patterns(library: PatternLibrary) -> None:
    """Register the behaviour patterns. Idempotent."""
    for pattern in PATTERNS:
        library.register(pattern)
