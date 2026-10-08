#!/usr/bin/env python3
"""
Pattern Library Module

Stores and generates React code patterns for UI components.
Central repository of deterministic code generation templates.

Pipeline Position:
    Validated Dict → ComponentMapper → [PatternLibrary] → React Code

Pattern Categories:
    L-01 to L-06: Layout patterns
    C-01 to C-10: Component patterns
    D-01 to D-06: Data binding patterns (future)
    E-01 to E-06: Event patterns (future)
    S-01 to S-05: State patterns (future)
    V-01 to V-06: Validation patterns (future)
    A-01 to A-05: API integration patterns (future)
    F-01 to F-05: Feedback patterns (future)
    I-01 to I-05: Iteration patterns (future)
    X-01 to X-04: Conditional patterns (future)

Copyright (c) 2025 Intelligent Cloud Lab Inc.
All rights reserved.

Author: Amit Sarkar
Version: 1.0.0
"""

from typing import Dict, Any, Callable
from dataclasses import dataclass


@dataclass
class Pattern:
    """
    Single pattern definition.
    
    Attributes:
        pattern_id: Unique identifier (e.g., 'C-01')
        name: Human-readable name (e.g., 'Button')
        category: Pattern category (e.g., 'component')
        description: Brief description of pattern purpose
        generator: Function that generates code from props
    """
    pattern_id: str
    name: str
    category: str
    description: str
    generator: Callable[[Dict[str, Any]], str]
    
    def generate(self, props: Dict[str, Any]) -> str:
        """
        Generate code with given properties.
        
        Args:
            props: Component properties dictionary
            
        Returns:
            Generated JSX code string
        """
        return self.generator(props)


PATTERN_LIBRARY_VERSION = '1.0.0'


class PatternLibrary:
    """
    Registry of code generation patterns.
    
    Central repository that maps pattern identifiers to their
    corresponding code generation functions. Ensures deterministic
    output for identical inputs.
    
    Attributes:
        _patterns: Dictionary mapping pattern IDs to Pattern objects
    """
    
    version = PATTERN_LIBRARY_VERSION

    def __init__(self):
        """Initialize library with built-in patterns."""
        self._patterns: Dict[str, Pattern] = {}
        self._register_layouts()
        self._register_components()
    
    def _register_layouts(self):
        """Register layout patterns L-01 through L-06."""
        
        # L-01: 12-Column Grid
        def grid_12(props: Dict) -> str:
            """Generate 12-column responsive grid layout."""
            return '''<View className="grid-container">
            {children}
        </View>'''
        
        self.register(Pattern(
            pattern_id='L-01',
            name='Grid 12-Column',
            category='layout',
            description='Responsive 12-column grid layout',
            generator=grid_12
        ))
        
        # L-02: Sidebar + Main
        def sidebar_main(props: Dict) -> str:
            """Generate sidebar with main content area layout."""
            sidebar_width = props.get('sidebar_width', '250px')
            return f'''<View className="sidebar-layout">
            <View className="sidebar" style={{{{width: '{sidebar_width}'}}}}>{'{sidebar}'}</View>
            <View className="main-content">{'{main}'}</View>
        </View>'''
        
        self.register(Pattern(
            pattern_id='L-02',
            name='Sidebar + Main',
            category='layout',
            description='Two-column sidebar layout',
            generator=sidebar_main
        ))
        
        # L-03: Header + Body + Footer
        def header_body_footer(props: Dict) -> str:
            """Generate standard page layout with three sections."""
            return '''<View className="page-layout">
            <View className="header">{header}</View>
            <View className="body">{body}</View>
            <View className="footer">{footer}</View>
        </View>'''
        
        self.register(Pattern(
            pattern_id='L-03',
            name='Header Body Footer',
            category='layout',
            description='Standard page layout with header, body, footer',
            generator=header_body_footer
        ))
        
        # L-04: Card Grid
        def card_grid(props: Dict) -> str:
            """Generate responsive card grid layout."""
            columns = props.get('columns', 3)
            gap = props.get('gap', '16px')
            return f'''<View className="card-grid" style={{{{
            display: 'grid',
            gridTemplateColumns: 'repeat({columns}, 1fr)',
            gap: '{gap}'
        }}}}>
            {'{children}'}
        </View>'''
        
        self.register(Pattern(
            pattern_id='L-04',
            name='Card Grid',
            category='layout',
            description='Responsive grid of cards',
            generator=card_grid
        ))
        
        # L-05: Form Stack
        def form_stack(props: Dict) -> str:
            """Generate vertical form field stack layout."""
            gap = props.get('gap', '16px')
            max_width = props.get('max_width', '400px')
            return f'''<View className="form-stack" style={{{{
            display: 'flex',
            flexDirection: 'column',
            gap: '{gap}',
            maxWidth: '{max_width}',
            margin: '0 auto'
        }}}}>
            {'{children}'}
        </View>'''
        
        self.register(Pattern(
            pattern_id='L-05',
            name='Form Stack',
            category='layout',
            description='Vertical form layout',
            generator=form_stack
        ))
        
        # L-06: Split Panel
        def split_panel(props: Dict) -> str:
            """Generate two-panel split layout."""
            ratio = props.get('ratio', '1:1')
            left, right = ratio.split(':')
            return f'''<View className="split-panel" style={{{{display: 'flex'}}}}>
            <View style={{{{flex: {left}}}}}>{'{left}'}</View>
            <View style={{{{flex: {right}}}}}>{'{right}'}</View>
        </View>'''
        
        self.register(Pattern(
            pattern_id='L-06',
            name='Split Panel',
            category='layout',
            description='Two-panel split layout',
            generator=split_panel
        ))
    
    def _register_components(self):
        """Register component patterns C-01 through C-10."""
        
        # C-01: Button
        def button(props: Dict) -> str:
            """Generate button component."""
            text = props.get('text', 'Button')
            variant = props.get('variant', 'primary')
            on_click = props.get('onClick', '')
            disabled = props.get('disabled', False)
            loading = props.get('loading', False)
            
            attrs = [f'variation="{variant}"']
            if on_click:
                attrs.append(f'onClick={{{on_click}}}')
            if disabled:
                attrs.append('isDisabled={true}')
            if loading:
                attrs.append('isLoading={true}')
            
            return f'<Button {" ".join(attrs)}>{text}</Button>'
        
        self.register(Pattern(
            pattern_id='C-01',
            name='Button',
            category='component',
            description='Clickable button with variants',
            generator=button
        ))
        
        # C-02: Text Input
        def text_input(props: Dict) -> str:
            """Generate text input field component."""
            label = props.get('label', 'Input')
            name = props.get('name', 'input')
            input_type = props.get('type', 'text')
            placeholder = props.get('placeholder', '')
            required = props.get('required', False)
            
            attrs = [
                f'label="{label}"',
                f'name="{name}"',
                f'type="{input_type}"',
            ]
            if placeholder:
                attrs.append(f'placeholder="{placeholder}"')
            if required:
                attrs.append('isRequired={true}')
            attrs.append('onChange={handleChange}')
            
            attrs_str = '\n                    '.join(attrs)
            return f'''<TextField
                    {attrs_str}
                />'''
        
        self.register(Pattern(
            pattern_id='C-02',
            name='Text Input',
            category='component',
            description='Text input field with label',
            generator=text_input
        ))
        
        # C-03: Select Dropdown
        def select(props: Dict) -> str:
            """Generate dropdown select component."""
            label = props.get('label', 'Select')
            name = props.get('name', 'select')
            options = props.get('options', [])
            
            options_jsx = '\n                '.join([
                f'<option value="{opt.get("value", "")}">{opt.get("label", "")}</option>'
                for opt in options
            ])
            
            return f'''<SelectField
                    label="{label}"
                    name="{name}"
                    onChange={{handleChange}}
                >
                {options_jsx}
                </SelectField>'''
        
        self.register(Pattern(
            pattern_id='C-03',
            name='Select',
            category='component',
            description='Dropdown select field',
            generator=select
        ))
        
        # C-04: Multi-Select
        def multi_select(props: Dict) -> str:
            """Generate multiple checkbox selection component."""
            legend = props.get('legend', 'Select options')
            name = props.get('name', 'options')
            options = props.get('options', [])
            
            checkboxes = '\n                '.join([
                f'<CheckboxField label="{opt.get("label", "")}" name="{name}" value="{opt.get("value", "")}" />'
                for opt in options
            ])
            
            return f'''<Fieldset legend="{legend}">
                {checkboxes}
                </Fieldset>'''
        
        self.register(Pattern(
            pattern_id='C-04',
            name='Multi-Select',
            category='component',
            description='Multiple checkbox selection',
            generator=multi_select
        ))
        
        # C-05: Range Slider
        def range_slider(props: Dict) -> str:
            """Generate numeric range slider component."""
            label = props.get('label', 'Value')
            name = props.get('name', 'slider')
            min_val = props.get('min', 0)
            max_val = props.get('max', 100)
            step = props.get('step', 1)
            default = props.get('default', min_val)
            
            return f'''<SliderField
                    label="{label}"
                    name="{name}"
                    min={{{min_val}}}
                    max={{{max_val}}}
                    step={{{step}}}
                    defaultValue={{{default}}}
                    onChange={{handleChange}}
                />'''
        
        self.register(Pattern(
            pattern_id='C-05',
            name='Range Slider',
            category='component',
            description='Numeric range slider',
            generator=range_slider
        ))
        
        # C-06: Checkbox
        def checkbox(props: Dict) -> str:
            """Generate single checkbox component."""
            label = props.get('label', 'Check me')
            name = props.get('name', 'checkbox')
            required = props.get('required', False)
            
            attrs = [f'label="{label}"', f'name="{name}"']
            if required:
                attrs.append('isRequired={true}')
            attrs.append('onChange={handleChange}')
            
            return f'<CheckboxField {" ".join(attrs)} />'
        
        self.register(Pattern(
            pattern_id='C-06',
            name='Checkbox',
            category='component',
            description='Single checkbox toggle',
            generator=checkbox
        ))
        
        # C-07: Card
        def card(props: Dict) -> str:
            """Generate card container component."""
            title = props.get('title', '')
            padding = props.get('padding', 'medium')
            
            if title:
                return f'<Card padding="{padding}"><Heading level={{4}}>{title}</Heading></Card>'
            return f'<Card padding="{padding}"></Card>'
        
        self.register(Pattern(
            pattern_id='C-07',
            name='Card',
            category='component',
            description='Container card with optional title',
            generator=card
        ))
        
        # C-08: Data Table
        def data_table(props: Dict) -> str:
            """Generate data table component."""
            return '''<Table>
                <TableHead>
                    <TableRow>
                        {/* Column headers */}
                    </TableRow>
                </TableHead>
                <TableBody>
                    {/* Data rows */}
                </TableBody>
            </Table>'''
        
        self.register(Pattern(
            pattern_id='C-08',
            name='Data Table',
            category='component',
            description='Tabular data display',
            generator=data_table
        ))
        
        # C-09: Modal
        def modal(props: Dict) -> str:
            """Generate modal dialog component."""
            title = props.get('title', 'Modal')
            
            return f'''<View className="modal-overlay">
                <Card>
                    <Heading level={{3}}>{title}</Heading>
                    {'{children}'}
                    <Button onClick={{onClose}}>Close</Button>
                </Card>
            </View>'''
        
        self.register(Pattern(
            pattern_id='C-09',
            name='Modal',
            category='component',
            description='Modal dialog overlay',
            generator=modal
        ))
        
        # C-10: Alert
        def alert(props: Dict) -> str:
            """Generate alert message component."""
            message = props.get('message', '')
            variation = props.get('variation', 'info')
            dismissible = props.get('dismissible', False)
            
            attrs = [f'variation="{variation}"']
            if dismissible:
                attrs.append('isDismissible={true}')
            
            return f'<Alert {" ".join(attrs)}>{message}</Alert>'
        
        self.register(Pattern(
            pattern_id='C-10',
            name='Alert',
            category='component',
            description='Alert notification message',
            generator=alert
        ))
    
    def register(self, pattern: Pattern) -> None:
        """
        Register pattern in library.
        
        Args:
            pattern: Pattern object to register
        """
        self._patterns[pattern.pattern_id] = pattern
    
    def get(self, pattern_id: str) -> Pattern:
        """
        Retrieve pattern by identifier.
        
        Args:
            pattern_id: Pattern identifier string
            
        Returns:
            Pattern object
            
        Raises:
            KeyError: Pattern not found
        """
        if pattern_id not in self._patterns:
            raise KeyError(f"Pattern not found: {pattern_id}")
        return self._patterns[pattern_id]
    
    def generate(self, pattern_id: str, props: Dict[str, Any]) -> str:
        """
        Generate code for pattern with given properties.
        
        Args:
            pattern_id: Pattern identifier string
            props: Component properties dictionary
            
        Returns:
            Generated JSX code string
        """
        pattern = self.get(pattern_id)
        return pattern.generate(props)
    
    def list_patterns(self) -> Dict[str, str]:
        """
        List all registered patterns.
        
        Returns:
            Dictionary mapping pattern IDs to categories
        """
        return {pid: p.category for pid, p in self._patterns.items()}


if __name__ == '__main__':
    library = PatternLibrary()
    
    print("Registered Patterns:")
    for pattern_id, category in library.list_patterns().items():
        pattern = library.get(pattern_id)
        print(f"  {pattern_id}: {pattern.name} ({category})")
    
    print("\nExample - Button:")
    print(library.generate('C-01', {
        'text': 'Submit',
        'variant': 'primary',
        'onClick': 'handleSubmit'
    }))
