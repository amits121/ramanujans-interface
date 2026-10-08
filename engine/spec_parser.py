#!/usr/bin/env python3
"""
Specification Parser Module

Parses YAML UI specifications and validates against JSON Schema.
Entry point for the spec-driven UI generation pipeline.

Pipeline Position:
    YAML File → [SpecParser] → Validated Dict → ComponentMapper → React Code

Copyright (c) 2025 Intelligent Cloud Lab Inc.
All rights reserved.

Author: Amit Sarkar
Version: 1.0.0
"""

import os
import json
import yaml
from typing import Dict, Any, List, Set
from jsonschema import validate, ValidationError


class SpecParser:
    """
    Parse and validate YAML UI specifications.
    
    Handles the first stage of the spec-driven UI pipeline by reading
    YAML specification files and validating their structure against
    the defined JSON Schema.
    
    Attributes:
        schema (dict): JSON Schema for specification validation
    """
    
    def __init__(self, schema_path: str = None):
        """
        Initialize parser with JSON Schema.
        
        Args:
            schema_path: Path to JSON Schema file.
                        Defaults to spec-schema.json in module directory.
        
        Raises:
            FileNotFoundError: Schema file does not exist
            json.JSONDecodeError: Schema contains invalid JSON
        """
        if schema_path is None:
            schema_path = os.path.join(
                os.path.dirname(__file__), 
                'spec-schema.json'
            )
        
        with open(schema_path, 'r') as f:
            self.schema = json.load(f)
    
    def parse(self, spec_path: str) -> Dict[str, Any]:
        """
        Parse and validate YAML specification file.
        
        Operations:
            1. Read YAML file from disk
            2. Parse YAML syntax to dictionary
            3. Validate against JSON Schema
        
        Args:
            spec_path: Path to YAML specification file
            
        Returns:
            Validated specification dictionary
            
        Raises:
            FileNotFoundError: Spec file does not exist
            yaml.YAMLError: Invalid YAML syntax
            ValidationError: Spec violates schema
        """
        with open(spec_path, 'r') as f:
            raw_yaml = f.read()
        
        spec = yaml.safe_load(raw_yaml)
        validate(instance=spec, schema=self.schema)
        
        return spec
    
    def parse_string(self, yaml_string: str) -> Dict[str, Any]:
        """
        Parse YAML specification from string.
        
        Args:
            yaml_string: YAML content as string
            
        Returns:
            Validated specification dictionary
            
        Raises:
            yaml.YAMLError: Invalid YAML syntax
            ValidationError: Spec violates schema
        """
        spec = yaml.safe_load(yaml_string)
        validate(instance=spec, schema=self.schema)
        return spec
    
    def get_components(self, spec: Dict[str, Any]) -> List[Dict]:
        """
        Extract flat list of components from specification.
        
        Handles both formats:
            - Flat: spec['components'] list
            - Sectioned: spec['sections'] with header/body/footer
        
        Args:
            spec: Validated specification dictionary
            
        Returns:
            List of component dictionaries
        """
        components = []
        
        if 'components' in spec:
            components.extend(spec['components'])
        
        if 'sections' in spec:
            for section_name in ('header', 'body', 'footer'):
                components.extend(spec['sections'].get(section_name, []))
        
        return components
    
    def get_component_types(self, spec: Dict[str, Any]) -> Set[str]:
        """
        Extract unique component types from specification.
        
        Used to determine required imports for code generation.
        
        Args:
            spec: Validated specification dictionary
            
        Returns:
            Set of component type identifiers
        """
        components = self.get_components(spec)
        return {comp.get('type', '') for comp in components}


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python spec_parser.py <spec.yaml>")
        sys.exit(1)
    
    parser = SpecParser()
    
    try:
        spec = parser.parse(sys.argv[1])
        print(f"Valid: {spec['screen_id']} v{spec['version']}")
        print(f"Layout: {spec['layout']}")
        print(f"Components: {len(parser.get_components(spec))}")
        print(f"Types: {parser.get_component_types(spec)}")
        
    except FileNotFoundError:
        print(f"Error: File not found: {sys.argv[1]}")
        sys.exit(1)
    except yaml.YAMLError as e:
        print(f"Error: Invalid YAML: {e}")
        sys.exit(1)
    except ValidationError as e:
        print(f"Error: Schema validation failed: {e.message}")
        sys.exit(1)
