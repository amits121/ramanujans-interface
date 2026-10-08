#!/usr/bin/env python3
"""
Component Mapper Module

Orchestrates transformation from validated specification to complete
React component code. Central orchestration engine of the pipeline.

Pipeline Position:
    Validated Dict → [ComponentMapper] → PatternLibrary → React Code

Transformation Stages:
    1. Extract metadata (screen_id, version, layout)
    2. Generate import statements
    3. Generate state declarations
    4. Generate JSX body structure
    5. Assemble complete component file

Copyright (c) 2025 Intelligent Cloud Lab Inc.
All rights reserved.

Author: Amit Sarkar
Version: 1.0.0
"""

from typing import Dict, Any, List, Set, Optional, Tuple

HANDLER_KEYS = ('onClick', 'onPress', 'onSubmit', 'onChange', 'onClose', 'onSelect', 'onOpen')


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
        """
        Initialize mapper with pattern library.
        
        Args:
            pattern_library: PatternLibrary instance
            container: JSX element used for layout wrappers ('View' or 'div')
            use_amplify: emit the Amplify UI imports (False for the static target)
        """
        self.library = pattern_library
        self.container = container
        self.use_amplify = use_amplify
        self.container_import = container_import      # e.g. ('react-native', ['SafeAreaView', 'ScrollView'])
        self.flat_wrapper = flat_wrapper              # template with {layout} and {children}, or None
        self.base_module = base_module or {}          # module-level code every file of this target carries
        self._used: List[Any] = []                    # patterns used by the current generation, in order
        
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
    
    def generate(self, spec: Dict[str, Any]) -> str:
        """
        Generate complete React component from specification.
        
        Args:
            spec: Validated specification dictionary
            
        Returns:
            Complete React component code as string
        """
        screen_id = spec['screen_id']
        component_name = self._to_pascal_case(screen_id)
        
        self._used = []
        body = self._generate_body(spec['layout'], spec)      # first: records the patterns used
        imports = self._generate_imports(spec)
        state_code = self._generate_state(spec.get('state', {}))
        handlers_code = self._generate_handlers(spec)
        module_code = self._generate_module()
        effects_code = self._generate_effects()
        
        return self._assemble(component_name, imports, state_code, handlers_code, body, spec,
                              module_code, effects_code)
    
    def _to_pascal_case(self, kebab_string: str) -> str:
        """
        Convert kebab-case to PascalCase.
        
        Args:
            kebab_string: String in kebab-case format
            
        Returns:
            String in PascalCase format
        """
        return ''.join(word.capitalize() for word in kebab_string.split('-'))
    
    def _get_all_components(self, spec: Dict[str, Any]) -> List[Dict]:
        """
        Extract all components from specification.
        
        Args:
            spec: Specification dictionary
            
        Returns:
            Flat list of component dictionaries
        """
        components = []
        
        if 'components' in spec:
            components.extend(spec['components'])
        
        if 'sections' in spec:
            for section_name in ('header', 'body', 'footer'):  # step 3: fixed section order
                components.extend(spec['sections'].get(section_name, []))
        
        return components
    
    def _get_handlers(self, spec: Dict[str, Any]) -> Set[str]:
        """
        Extract all onClick handler names from specification.
        
        Args:
            spec: Specification dictionary
            
        Returns:
            Set of handler function names
        """
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
        """
        Generate stub handler functions.
        
        Args:
            spec: Specification dictionary
            
        Returns:
            Handler function declarations as string
        """
        handlers = self._get_handlers(spec)
        
        provided: Dict[str, str] = {}
        for pattern in self._used:
            for name, code in pattern.handlers.items():
                provided.setdefault(name, code)
        handlers = set(handlers) | set(provided)   # a handler a pattern declares is always emitted
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
        blocks: Dict[str, str] = dict(self.base_module)
        for pattern in self._used:
            for key, code in pattern.module.items():
                blocks.setdefault(key, code)
        return '\n\n'.join(blocks[k] for k in sorted(blocks))
    
    def _generate_effects(self) -> str:
        """Effect blocks declared by the used patterns, in use order, each once."""
        seen: List[str] = []
        for pattern in self._used:
            for code in pattern.effects:
                if code not in seen:
                    seen.append(code)
        return '\n\n'.join(seen)
    
    def _generate_imports(self, spec: Dict[str, Any]) -> str:
        """
        Generate import statements for component.
        
        Args:
            spec: Specification dictionary
            
        Returns:
            Import statements as string
        """
        modules: Dict[str, Set[str]] = {'react': {'useState'}}
        
        if self.use_amplify:
            amplify_imports: Set[str] = {'View'}
            for comp in self._get_all_components(spec):
                amplify_imports.update(self.amplify_map.get(comp.get('type', ''), []))
            modules['@aws-amplify/ui-react'] = amplify_imports
            modules['@aws-amplify/ui-react/styles.css'] = set()
        elif self.container_import:
            modules.setdefault(self.container_import[0], set()).update(self.container_import[1])
        
        for pattern in self._used:
            for module, names in pattern.imports.items():
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
        """
        Generate useState declarations.
        
        Args:
            state: State variables dictionary
            
        Returns:
            State declarations as string
        """
        if not state:
            return ''
        
        lines = []
        for key, value in state.items():
            js_value = self._to_js_value(value)
            setter_name = f"set{key[0].upper()}{key[1:]}"
            lines.append(f"    const [{key}, {setter_name}] = useState({js_value});")
        
        return '\n'.join(lines)
    
    def _to_js_value(self, value: Any) -> str:
        """
        Convert Python value to JavaScript literal.
        
        Args:
            value: Python value
            
        Returns:
            JavaScript literal string
        """
        if value is None:
            return 'null'
        elif isinstance(value, bool):
            return 'true' if value else 'false'
        elif isinstance(value, str):
            return f"'{value}'"
        elif isinstance(value, (int, float)):
            return str(value)
        elif isinstance(value, list):
            return '[]'
        elif isinstance(value, dict):
            return '{}'
        return 'null'
    
    def _generate_body(self, layout: str, spec: Dict[str, Any]) -> str:
        """
        Generate JSX body structure.
        
        Args:
            layout: Layout type identifier
            spec: Specification dictionary
            
        Returns:
            JSX body as string
        """
        if 'sections' in spec:
            return self._generate_sectioned_body(layout, spec['sections'])
        elif 'components' in spec:
            return self._generate_flat_body(layout, spec['components'])
        return f'<{self.container}>No components defined</{self.container}>'
    
    def _generate_sectioned_body(self, layout: str, sections: Dict[str, List]) -> str:
        """
        Generate body with header/body/footer sections.
        
        Args:
            layout: Layout type identifier
            sections: Sections dictionary
            
        Returns:
            Sectioned JSX body as string
        """
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
        """
        Generate body with flat component list.
        
        Args:
            layout: Layout type identifier
            components: List of component dictionaries
            
        Returns:
            Flat JSX body as string
        """
        rendered = [self._render_component(comp) for comp in components]
        children = '\n                '.join(r for r in rendered if r)
        
        if self.flat_wrapper:
            return self.flat_wrapper.replace('{layout}', layout).replace('{children}', children)
        c = self.container
        return f'''<{c} className="{layout}">
                {children}
            </{c}>'''
    
    def _render_component(self, comp: Dict[str, Any]) -> str:
        """
        Render single component using pattern library.
        
        Args:
            comp: Component dictionary
            
        Returns:
            Generated JSX for component
        """
        comp_type = comp.get('type', '')
        props = comp.get('props', {})
        comp_id = comp.get('id', '')
        
        props = dict(props)  # step 2: never mutate the caller's spec
        if 'name' not in props:
            props['name'] = comp_id
        
        pattern_id = self.type_mapping.get(comp_type)
        
        if not pattern_id:
            raise ValueError(f'unknown component type "{comp_type}" (component {comp_id}): no pattern registered')
        
        pattern = self.library.get(pattern_id)
        if all(p.pattern_id != pattern.pattern_id for p in self._used):
            self._used.append(pattern)
        return pattern.generate(props)
    
    def _assemble(self, component_name: str, imports: str,
                  state_code: str, handlers_code: str, body: str, spec: Dict,
                  module_code: str = '', effects_code: str = '') -> str:
        """
        Assemble complete React component file.
        
        Args:
            component_name: PascalCase component name
            imports: Import statements
            state_code: State declarations
            handlers_code: Event handler functions
            body: JSX body structure
            spec: Original specification
            
        Returns:
            Complete component code as string
        """
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
