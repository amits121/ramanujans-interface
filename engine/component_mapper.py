#!/usr/bin/env python3
"""
Component Mapper Module

Orchestrates transformation from validated specification to complete
React component code. Central orchestration engine of the pipeline.

Pipeline Position:
    Validated Dict → [ComponentMapper] → PatternLibrary → React Code

Transformation Stages:
    1. Extract metadata (screen_id, version, layout)
    2. Render the component tree (nested children fill the slots of their container)
    3. Generate import statements, state, handlers, module code and effects
       from the specification and from what the used patterns declare
    4. Assemble complete component file

Copyright (c) 2025 Intelligent Cloud Lab Inc.
All rights reserved.

Author: Amit Sarkar
Version: 1.1.0
"""

import json
from typing import Dict, Any, List, Set, Optional, Tuple

from declarations import Declarations

HANDLER_KEYS = ('onClick', 'onPress', 'onSubmit', 'onChange', 'onClose', 'onSelect', 'onOpen')
CHILD_INDENT = '\n' + ' ' * 20


class ComponentMapper:
    """
    Map specifications to React component code.
    
    Orchestrates the transformation from validated YAML specification
    to complete React TypeScript component file.
    
    Attributes:
        library: PatternLibrary instance for code generation
        type_mapping: Maps spec types to pattern identifiers
        amplify_map: Maps component types to Amplify UI imports
    """
    
    def __init__(self, pattern_library, container: str = 'View', use_amplify: bool = True,
                 container_import: Optional[Tuple[str, List[str]]] = None, flat_wrapper: Optional[str] = None,
                 base_module: Optional[Dict[str, str]] = None):
        """Initialize mapper with pattern library."""
        self.library = pattern_library
        self.container = container
        self.use_amplify = use_amplify
        self.container_import = container_import      # e.g. ('react-native', ['SafeAreaView', 'ScrollView'])
        self.flat_wrapper = flat_wrapper              # template with {layout} and {children}, or None
        self.base_module = base_module or {}          # module-level code every file of this target carries
        self.allowed_types: Optional[Set[str]] = None # a tenant's pattern set, or None for every registered type
        self._decl = Declarations()                   # what the current generation's patterns declare
        self._spec_state: Set[str] = set()            # state variables the specification declares
        self._screen_id = ''
        
        self.type_mapping = {
            # Layout patterns
            'grid-12': 'L-01',
            'sidebar-main': 'L-02',
            'header-body-footer': 'L-03',
            'card-grid': 'L-04',
            'form-stack': 'L-05',
            'split-panel': 'L-06',
            # Component patterns
            'button': 'C-01',
            'text-input': 'C-02',
            'select': 'C-03',
            'multi-select': 'C-04',
            'range-slider': 'C-05',
            'checkbox': 'C-06',
            'card': 'C-07',
            'data-table': 'C-08',
            'modal': 'C-09',
            'alert': 'C-10',
        }
        
        self.amplify_map = {
            'button': ['Button'],
            'text-input': ['TextField'],
            'select': ['SelectField'],
            'multi-select': ['CheckboxField', 'Fieldset'],
            'range-slider': ['SliderField'],
            'checkbox': ['CheckboxField'],
            'card': ['Card', 'Heading'],
            'data-table': ['Table', 'TableHead', 'TableBody', 'TableRow', 'TableCell'],
            'modal': ['View', 'Card', 'Heading', 'Button'],
            'alert': ['Alert'],
        }
    
    def register_types(self, mapping: Dict[str, str]) -> None:
        """Register additional spec types -> pattern ids (patterns are registered, never edited in)."""
        self.type_mapping.update(mapping)
    
    def restrict_types(self, allowed: Set[str], set_id: str = '') -> None:
        """Limit generation to a tenant's pattern set: any other type is refused."""
        self.allowed_types = set(allowed)
        self.allowed_set_id = set_id
    
    def generate(self, spec: Dict[str, Any]) -> str:
        """Generate complete React component from specification."""
        screen_id = spec['screen_id']
        component_name = self._to_pascal_case(screen_id)
        
        self._decl = Declarations(self.base_module)
        self._spec_state = set(spec.get('state', {}))
        self._screen_id = screen_id
        body = self._generate_body(spec['layout'], spec)      # first: records what the patterns declare
        imports = self._generate_imports(spec)
        state_code = self._generate_state(spec.get('state', {}))
        handlers_code = self._generate_handlers(spec)
        module_code = self._generate_module()
        effects_code = self._generate_effects()
        
        return self._assemble(component_name, imports, state_code, handlers_code, body, spec,
                              module_code, effects_code)
    
    def _to_pascal_case(self, kebab_string: str) -> str:
        """Convert kebab-case to PascalCase."""
        return ''.join(word.capitalize() for word in kebab_string.split('-'))
    
    def _get_all_components(self, spec: Dict[str, Any]) -> List[Dict]:
        """Extract all components from specification, nested children included, in document order (depth first)."""
        roots: List[Dict] = []
        
        if 'components' in spec:
            roots.extend(spec['components'])
        
        if 'sections' in spec:
            for section_name in ('header', 'body', 'footer'):  # step 3: fixed section order
                roots.extend(spec['sections'].get(section_name, []))
        
        return self._flatten(roots)
    
    def _flatten(self, components: List[Dict]) -> List[Dict]:
        out: List[Dict] = []
        for comp in components:
            out.append(comp)
            out.extend(self._flatten(comp.get('children', [])))
        return out
    
    def _get_handlers(self, spec: Dict[str, Any]) -> Set[str]:
        """Extract all handler names named in specification props."""
        handlers = set()
        components = self._get_all_components(spec)
        
        for comp in components:
            props = comp.get('props', {})
            for key in HANDLER_KEYS:
                value = props.get(key, '')
                if isinstance(value, str) and value.isidentifier():
                    handlers.add(value)
        
        return handlers
    
    def _generate_handlers(self, spec: Dict[str, Any]) -> str:
        """Generate handler functions: bodies the patterns declare, stubs for the rest."""
        provided = self._decl.handlers
        handlers = self._get_handlers(spec) | set(provided) | self._decl.references
        if not handlers:
            return ''
        
        lines = []
        for handler in sorted(handlers):
            if handler in provided:
                lines.append(f'    const {handler} = {provided[handler]};')
            else:
                lines.append(f'''    const {handler} = () => {{
        console.log('{handler} called');
        // TODO: Implement {handler}
    }};''')
        
        return '\n\n'.join(lines)
    
    def _generate_module(self) -> str:
        """Module-level code declared by the used patterns, once per key, keys sorted."""
        blocks = self._decl.module
        return '\n\n'.join(blocks[k] for k in sorted(blocks))
    
    def _generate_effects(self) -> str:
        """Effect blocks declared by the used patterns, in use order, each once."""
        return '\n\n'.join(self._decl.effects)
    
    def _generate_imports(self, spec: Dict[str, Any]) -> str:
        """Generate import statements for component."""
        modules: Dict[str, Set[str]] = {'react': {'useState'}}
        
        if self.use_amplify:
            amplify_imports: Set[str] = {'View'}
            for comp in self._get_all_components(spec):
                amplify_imports.update(self.amplify_map.get(comp.get('type', ''), []))
            modules['@aws-amplify/ui-react'] = amplify_imports
            modules['@aws-amplify/ui-react/styles.css'] = set()
        elif self.container_import:
            modules.setdefault(self.container_import[0], set()).update(self.container_import[1])
        
        for module, names in self._decl.imports.items():
            modules.setdefault(module, set()).update(names)
        
        lines = []
        react_names = sorted(modules.pop('react'))
        lines.append(f"import React, {{ {', '.join(react_names)} }} from 'react';")
        for module in sorted(modules):
            names = modules[module]
            default = sorted(n[8:] for n in names if n.startswith('default:'))
            namespace = sorted(n[2:] for n in names if n.startswith('*:'))
            named = sorted(n for n in names if not n.startswith('default:') and not n.startswith('*:'))
            if not names:
                lines.append(f"import '{module}';")
                continue
            for ns in namespace:
                lines.append(f"import * as {ns} from '{module}';")
            head = ', '.join(default + ([f'{{ {", ".join(named)} }}'] if named else []))
            if head:
                lines.append(f"import {head} from '{module}';")
        return '\n'.join(lines)
    
    def _generate_state(self, state: Dict[str, Any]) -> str:
        """Generate useState declarations: the specification's variables first (its order), then the variables the patterns declare and the specification does not."""
        lines = []
        for key, value in state.items():
            lines.append(f"    const [{key}, {self._setter(key)}] = {self._use_state(value)};")
        for key, rhs in self._decl.state.items():
            if key not in state:
                lines.append(f"    const [{key}, {self._setter(key)}] = {rhs};")
        return '\n'.join(lines)
    
    @staticmethod
    def _setter(key: str) -> str:
        return f"set{key[0].upper()}{key[1:]}"
    
    def _use_state(self, value: Any) -> str:
        """The useState call for an initial value, typed from the value (type inference for state): strings, booleans and numbers infer themselves; lists, objects and null carry an explicit type so the generated code stays well typed."""
        if value is None:
            return 'useState<unknown>(null)'
        elif isinstance(value, bool):
            return f"useState({'true' if value else 'false'})"
        elif isinstance(value, str):
            return f'useState({json.dumps(value, ensure_ascii=False)})'
        elif isinstance(value, (int, float)):
            return f'useState({value})'
        elif isinstance(value, list):
            return 'useState<Array<Record<string, unknown>>>([])'
        elif isinstance(value, dict):
            return 'useState<Record<string, unknown>>({})'
        return 'useState<unknown>(null)'
    
    def _generate_body(self, layout: str, spec: Dict[str, Any]) -> str:
        """Generate JSX body structure."""
        if 'sections' in spec:
            return self._generate_sectioned_body(layout, spec['sections'])
        elif 'components' in spec:
            return self._generate_flat_body(layout, spec['components'])
        return f'<{self.container}>No components defined</{self.container}>'
    
    def _generate_sectioned_body(self, layout: str, sections: Dict[str, List]) -> str:
        """Generate body with header/body/footer sections."""
        section_jsx = {}
        
        for section_name in ('header', 'body', 'footer'):  # step 3: fixed section order
            components = sections.get(section_name, [])
            rendered = [self._render_component(comp) for comp in components]
            section_jsx[section_name] = '\n                    '.join(rendered)
        
        header = section_jsx.get('header', '')
        body = section_jsx.get('body', '')
        footer = section_jsx.get('footer', '')
        
        c = self.container
        return f'''<{c} className="page-layout">
                <{c} className="header">
                    {header}
                </{c}>
                <{c} className="body">
                    {body}
                </{c}>
                <{c} className="footer">
                    {footer}
                </{c}>
            </{c}>'''
    
    def _generate_flat_body(self, layout: str, components: List[Dict]) -> str:
        """Generate body with flat component list."""
        rendered = [self._render_component(comp) for comp in components]
        children = '\n                '.join(r for r in rendered if r)
        
        if self.flat_wrapper:
            return self.flat_wrapper.replace('{layout}', layout).replace('{children}', children)
        c = self.container
        return f'''<{c} className="{layout}">
                {children}
            </{c}>'''
    
    def _render_component(self, comp: Dict[str, Any]) -> str:
        """Render one component, its children first, using the pattern library."""
        comp_type = comp.get('type', '')
        props = comp.get('props', {})
        comp_id = comp.get('id', '')
        children = comp.get('children', [])
        
        props = dict(props)  # step 2: never mutate the caller's spec
        if 'name' not in props:
            props['name'] = comp_id
        
        pattern_id = self.type_mapping.get(comp_type)
        if self.allowed_types is not None and comp_type not in self.allowed_types:
            raise ValueError(f'component type "{comp_type}" (component {comp_id}) is not in pattern set '
                             f'"{self.allowed_set_id}"')
        if not pattern_id:
            raise ValueError(f'unknown component type "{comp_type}" (component {comp_id}): no pattern registered')
        
        pattern = self.library.get(pattern_id)
        origin = f'{pattern.pattern_id} on component {comp_id}'
        if children and not pattern.slots:
            raise ValueError(f'component {comp_id} of type "{comp_type}" takes no children')
        
        filled: Dict[str, List[str]] = {slot: [] for slot in pattern.slots}
        for child in children:
            slot = child.get('slot', pattern.slots[0])
            if slot not in filled:
                raise ValueError(f'component {child.get("id", "")} names slot "{slot}", which {pattern.pattern_id} '
                                 f'does not have (slots: {", ".join(pattern.slots)})')
            filled[slot].append(self._render_component(child))      # children first: they declare before the parent
        
        text = json.dumps(props, sort_keys=True, ensure_ascii=False)
        for slot in pattern.slots:
            if '{' + slot + '}' in text:
                raise ValueError(f'component {comp_id}: a property contains the placeholder "{{{slot}}}" of its own slot')
        
        self._decl.add_pattern(pattern, origin)
        if pattern.declare:
            context = {'component_id': comp_id, 'screen_id': self._screen_id,
                       'state': frozenset(self._spec_state | set(self._decl.state_names()))}
            self._decl.add(pattern.declare(props, context), origin)
        
        out = pattern.generate(props)
        for slot in pattern.slots:
            out = out.replace('{' + slot + '}', CHILD_INDENT.join(r for r in filled[slot] if r))
        return out
    
    def _assemble(self, component_name: str, imports: str,
                  state_code: str, handlers_code: str, body: str, spec: Dict,
                  module_code: str = '', effects_code: str = '') -> str:
        """Assemble complete React component file."""
        pattern_lib_version = self.library.version  # step 1: version, never the clock
        screen_id = spec['screen_id']
        version = spec['version']
        
        state_section = state_code if state_code else '    // No state defined'
        handlers_section = handlers_code if handlers_code else '    // No handlers defined'
        module_section = ('\n' + module_code + '\n') if module_code else ''
        effects_section = ('\n' + effects_code + '\n') if effects_code else ''
        
        return f'''/**
 * {component_name}.tsx
 * 
 * Auto-generated from specification: {screen_id} v{version}
 * Pattern library: {pattern_lib_version}
 * 
 * DO NOT EDIT MANUALLY - Changes will be overwritten
 * Edit the YAML specification file instead.
 * 
 * Copyright (c) 2025 Intelligent Cloud Lab Inc.
 */

{imports}
{module_section}
const {component_name}: React.FC = () => {{
{state_section}

    const handleChange = (e: any) => {{
        console.log('Field changed:', e.target.name, e.target.value);
    }};

{handlers_section}
{effects_section}
    return (
        {body}
    );
}};

export default {component_name};
'''


if __name__ == '__main__':
    import sys
    from spec_parser import SpecParser
    from pattern_library import PatternLibrary
    
    if len(sys.argv) < 2:
        print("Usage: python component_mapper.py <spec.yaml> [--write]")
        sys.exit(1)
    
    parser = SpecParser()
    library = PatternLibrary()
    mapper = ComponentMapper(library)
    
    try:
        spec = parser.parse(sys.argv[1])
        code = mapper.generate(spec)
        
        print(code)
        
        if len(sys.argv) >= 3 and sys.argv[2] == '--write':
            component_name = mapper._to_pascal_case(spec['screen_id'])
            output_path = f"{component_name}.tsx"
            with open(output_path, 'w') as f:
                f.write(code)
            print(f"\nWritten to: {output_path}")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
