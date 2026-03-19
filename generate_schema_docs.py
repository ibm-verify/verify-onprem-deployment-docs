#!/usr/bin/env python3
"""
IBM Confidential
PID 5725-X36
Copyright IBM Corp. 2026

Schema Documentation Generator
Generates single-page application documentation for JSON/YAML schema specifications
conforming to IBM Carbon Design System standards.

Supported JSON Schema Versions:
- JSON Schema Draft-04 (http://json-schema.org/draft-04/schema#)
- JSON Schema Draft-06 (http://json-schema.org/draft-06/schema#)
- JSON Schema Draft-07 (http://json-schema.org/draft-07/schema#)
- JSON Schema Draft 2019-09 (https://json-schema.org/draft/2019-09/schema)
- JSON Schema Draft 2020-12 (https://json-schema.org/draft/2020-12/schema)

New Features Supported (2019-09 and 2020-12):
- $defs (replaces definitions)
- $dynamicRef and $dynamicAnchor
- prefixItems (tuple validation)
- dependentSchemas and dependentRequired
- unevaluatedProperties and unevaluatedItems
- const keyword
- minContains and maxContains
- contentMediaType, contentEncoding, contentSchema
- Enhanced validation constraints
"""

import yaml
import json
import os
import sys
import re
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)

try:
    import markdown as markdown_module
    MARKDOWN_AVAILABLE = True
except ImportError:
    markdown_module = None  # type: ignore
    MARKDOWN_AVAILABLE = False
    logger.warning("markdown package not available. Install with: pip install markdown")


class SchemaDocGenerator:
    """Generate HTML documentation from JSON/YAML schema specifications."""
    
    # Supported JSON Schema versions
    SUPPORTED_SCHEMA_VERSIONS = [
        'http://json-schema.org/draft-07/schema#',
        'https://json-schema.org/draft/2019-09/schema',
        'https://json-schema.org/draft/2020-12/schema',
        'http://json-schema.org/draft-04/schema#',
        'http://json-schema.org/draft-06/schema#',
    ]
    
    def __init__(self, schema_path: str, output_path: Optional[str] = None):
        """
        Initialize the generator.
        
        Args:
            schema_path: Path to the main schema file (YAML or JSON)
            output_path: Path for the output HTML file (optional)
        """
        self.schema_path = Path(schema_path)
        self.schema_dir = self.schema_path.parent
        self.output_path = Path(output_path) if output_path else self.schema_path.with_suffix('.html')
        self.schema_cache = {}
        self.main_schema = None
        self.schema_version = None
        
    def load_schema(self, path: Path) -> Dict[str, Any]:
        """Load a schema file (YAML or JSON) and detect schema version."""
        if str(path) in self.schema_cache:
            return self.schema_cache[str(path)]
            
        with open(path, 'r', encoding='utf-8') as f:
            if path.suffix in ['.yaml', '.yml']:
                schema = yaml.safe_load(f)
            else:
                schema = json.load(f)
        
        # Detect schema version from $schema keyword
        if '$schema' in schema and self.schema_version is None:
            self.schema_version = schema['$schema']
            if self.schema_version not in self.SUPPORTED_SCHEMA_VERSIONS:
                logger.warning(f"Schema version '{self.schema_version}' may not be fully supported.")
                logger.warning(f"Supported versions: {', '.join(self.SUPPORTED_SCHEMA_VERSIONS)}")
        
        self.schema_cache[str(path)] = schema
        return schema
    
    def _get_definitions_key(self, schema: Dict[str, Any]) -> str:
        """
        Get the appropriate definitions key based on schema version.
        Returns 'definitions' for older drafts, '$defs' for 2019-09+, or whichever exists.
        """
        # Check which key exists in the schema
        if '$defs' in schema:
            return '$defs'
        elif 'definitions' in schema:
            return 'definitions'
        
        # Default based on schema version
        if self.schema_version and ('2019-09' in self.schema_version or '2020-12' in self.schema_version):
            return '$defs'
        return 'definitions'
    
    def resolve_ref(self, ref: str, current_path: Optional[Path] = None) -> Tuple[Dict[str, Any], str]:
        """
        Resolve a $ref or $dynamicRef reference to another schema.
        Supports both 'definitions' and '$defs' keywords.
        
        Args:
            ref: The reference string (e.g., "general.yaml#/definitions/general" or "#/$defs/myDef")
            current_path: Current schema file path for relative resolution
            
        Returns:
            Tuple of (resolved schema dict, definition name)
        """
        if current_path is None:
            current_path = self.schema_path
            
        # Split file path and JSON pointer
        if '#' in ref:
            file_ref, pointer = ref.split('#', 1)
        else:
            file_ref, pointer = ref, ''
        
        # Load the referenced file
        if file_ref:
            ref_path = (current_path.parent / file_ref).resolve()
            schema = self.load_schema(ref_path)
        else:
            schema = self.main_schema
        
        # Navigate the JSON pointer
        parts = []
        if pointer:
            parts = [p for p in pointer.split('/') if p]
            for part in parts:
                if schema and isinstance(schema, dict):
                    schema = schema.get(part, {})
        
        # Extract definition name from pointer
        def_name = parts[-1] if parts else ''
        
        return schema if schema else {}, def_name
    
    def generate_html(self) -> str:
        """Generate the complete HTML documentation."""
        self.main_schema = self.load_schema(self.schema_path)
        
        title = self.main_schema.get('title', 'Schema Documentation')
        description = self.main_schema.get('description', '')
        
        html = self._generate_header(title)
        html += self._generate_body_start(title, description)
        
        # Start Configuration section (expanded by default)
        html += '''
        <div style="padding: 1rem 0; color: #525252; font-size: 0.875rem; font-style: italic; display: flex; justify-content: space-between; align-items: center;">
            <span>ℹ️ Click on section headers below to expand and view configuration details.</span>
            <div style="display: flex; gap: 0.5rem;">
                <button class="expand-collapse-btn" onclick="expandAll()" title="Expand all sections">
                    <span style="font-size: 1rem;">⊞</span> Expand All
                </button>
                <button class="expand-collapse-btn" onclick="collapseAll()" title="Collapse all sections">
                    <span style="font-size: 1rem;">⊟</span> Collapse All
                </button>
            </div>
        </div>
        <div class="section" id="configuration">
            <div class="section-header expanded" onclick="toggleSection('configuration')">
                <h2>Configuration</h2>
                <span class="toggle-icon">▼</span>
            </div>
            <div class="section-content expanded">
'''
        
        # Process the main schema
        if '$ref' in self.main_schema:
            ref_schema, _ = self.resolve_ref(self.main_schema['$ref'])
            html += self._generate_schema_content(ref_schema, level=1)
        elif '$dynamicRef' in self.main_schema:
            # Handle $dynamicRef (JSON Schema 2020-12)
            ref_schema, _ = self.resolve_ref(self.main_schema['$dynamicRef'])
            html += self._generate_schema_content(ref_schema, level=1)
        elif 'properties' in self.main_schema:
            # If there are properties, show them
            html += self._generate_properties(self.main_schema, level=1)
        else:
            # Check for definitions or $defs
            defs_key = self._get_definitions_key(self.main_schema)
            if defs_key in self.main_schema:
                # If only definitions (no properties), show all definitions
                for def_name, def_schema in self.main_schema[defs_key].items():
                    html += self._generate_definition_section(def_name, def_schema, level=1)
        
        # Close Configuration section
        html += '''
            </div>
        </div>
'''
        
        # Add examples if present
        if 'examples' in self.main_schema:
            html += self._generate_examples_section(self.main_schema['examples'])
        
        html += self._generate_footer()
        
        return html
    
    def _generate_header(self, title: str) -> str:
        """Generate HTML header with IBM Carbon styles."""
        return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{self._escape_html(title)}</title>
    <link rel="stylesheet" href="https://unpkg.com/carbon-components@10.58.0/css/carbon-components.min.css">
    <style>
        /*
        IBM Confidential
        PID 5725-X36
        Copyright IBM Corp. 2026
        */
        
        :root {{
            --cds-ui-background: #ffffff;
            --cds-ui-01: #f4f4f4;
            --cds-ui-02: #ffffff;
            --cds-text-01: #161616;
            --cds-text-02: #525252;
            --cds-link-01: #0f62fe;
            --cds-field-01: #f4f4f4;
            --cds-border-subtle-01: #e0e0e0;
        }}
        
        body {{
            font-family: 'IBM Plex Sans', 'Helvetica Neue', Arial, sans-serif;
            margin: 0;
            padding: 0;
            background-color: var(--cds-ui-background);
            color: var(--cds-text-01);
            line-height: 1.5;
        }}
        
        .header {{
            background-color: #161616;
            color: #ffffff;
            padding: 2rem 3rem;
            border-bottom: 1px solid #393939;
        }}
        
        .header h1 {{
            margin: 0;
            font-size: 2rem;
            font-weight: 400;
            letter-spacing: 0;
        }}
        
        .header .description {{
            margin-top: 1rem;
            color: #c6c6c6;
            font-size: 0.875rem;
            line-height: 1.5;
        }}
        
        .header .description p {{
            margin: 0 0 1rem 0;
        }}
        
        .header .description p:last-child {{
            margin-bottom: 0;
        }}
        
        .search-container {{
            margin-top: 1.5rem;
            position: relative;
        }}
        
        .search-input {{
            width: 100%;
            max-width: 600px;
            padding: 0.75rem 2.5rem 0.75rem 1rem;
            font-size: 0.875rem;
            border: 1px solid #393939;
            background-color: #262626;
            color: #ffffff;
            border-radius: 4px;
            font-family: 'IBM Plex Sans', 'Helvetica Neue', Arial, sans-serif;
            transition: border-color 0.11s;
        }}
        
        .search-input:focus {{
            outline: none;
            border-color: #0f62fe;
        }}
        
        .search-input::placeholder {{
            color: #8d8d8d;
        }}
        
        .search-clear {{
            position: absolute;
            right: calc(100% - 600px + 0.75rem);
            top: 50%;
            transform: translateY(-50%);
            background: none;
            border: none;
            color: #8d8d8d;
            cursor: pointer;
            font-size: 1.25rem;
            padding: 0.25rem;
            display: none;
        }}
        
        .search-clear:hover {{
            color: #ffffff;
        }}
        
        .search-clear.visible {{
            display: block;
        }}
        
        .search-results-info {{
            margin-top: 0.5rem;
            font-size: 0.75rem;
            color: #8d8d8d;
        }}
        
        .container {{
            max-width: 1584px;
            margin: 0 auto;
            padding: 2rem 3rem;
        }}
        
        .section {{
            margin-bottom: 2rem;
            background-color: var(--cds-ui-02);
            border: 1px solid var(--cds-border-subtle-01);
        }}
        
        .section-header {{
            padding: 1rem 1.5rem;
            background-color: var(--cds-ui-01);
            border-bottom: 1px solid var(--cds-border-subtle-01);
            cursor: pointer;
            display: flex;
            justify-content: space-between;
            align-items: center;
            transition: background-color 0.11s;
        }}
        
        .section-header:hover {{
            background-color: #e8e8e8;
        }}
        
        .section-header h2,
        .section-header h3,
        .section-header h4 {{
            margin: 0;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }}
        
        .section-header h2 {{
            font-size: 1.5rem;
        }}
        
        .section-header h3 {{
            font-size: 1.25rem;
        }}
        
        .section-header h4 {{
            font-size: 1rem;
        }}
        
        .section-content {{
            padding: 1.5rem;
            display: none;
        }}
        
        .section-content.expanded {{
            display: block;
        }}
        
        .toggle-icon {{
            transition: transform 0.2s;
            font-size: 1.25rem;
        }}
        
        .section-header.expanded .toggle-icon {{
            transform: rotate(180deg);
        }}
        
        .property {{
            margin-bottom: 1.5rem;
            padding-bottom: 1.5rem;
            border-bottom: 1px solid var(--cds-border-subtle-01);
        }}
        
        .property:last-child {{
            border-bottom: none;
            margin-bottom: 0;
            padding-bottom: 0;
        }}
        
        .property-name {{
            font-weight: 600;
            font-size: 1rem;
            color: var(--cds-text-01);
            margin-bottom: 0.5rem;
            font-family: 'IBM Plex Mono', monospace;
        }}
        
        .property-type {{
            display: inline-block;
            background-color: #0f62fe;
            color: #ffffff;
            padding: 0.125rem 0.5rem;
            border-radius: 2px;
            font-size: 0.75rem;
            font-weight: 600;
            margin-left: 0.5rem;
            font-family: 'IBM Plex Mono', monospace;
        }}
        
        .property-required {{
            display: inline-block;
            background-color: #da1e28;
            color: #ffffff;
            padding: 0.125rem 0.5rem;
            border-radius: 2px;
            font-size: 0.75rem;
            font-weight: 600;
            margin-left: 0.5rem;
        }}
        
        .property-description {{
            color: var(--cds-text-02);
            font-size: 0.875rem;
            margin-top: 0.5rem;
            line-height: 1.5;
        }}
        
        .property-default {{
            margin-top: 0.5rem;
            font-size: 0.875rem;
        }}
        
        .property-default strong {{
            color: var(--cds-text-01);
        }}
        
        .property-enum {{
            margin-top: 0.5rem;
        }}
        
        .property-enum-title {{
            font-weight: 600;
            font-size: 0.875rem;
            margin-bottom: 0.25rem;
        }}
        
        .property-enum-values {{
            display: flex;
            flex-wrap: wrap;
            gap: 0.5rem;
            margin-top: 0.5rem;
        }}
        
        .enum-value {{
            background-color: var(--cds-field-01);
            padding: 0.25rem 0.75rem;
            border-radius: 2px;
            font-size: 0.75rem;
            font-family: 'IBM Plex Mono', monospace;
            border: 1px solid var(--cds-border-subtle-01);
        }}
        
        .nested-section {{
            margin-top: 1.5rem;
            padding: 1rem;
            background-color: #fafafa;
            border-left: 3px solid #8d8d8d;
            border-radius: 4px;
        }}
        
        .properties-header {{
            font-weight: 600;
            font-size: 0.875rem;
            color: #525252;
            margin-bottom: 1rem;
            padding-bottom: 0.5rem;
            border-bottom: 1px solid #e0e0e0;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }}
        
        .example-section {{
            background-color: #f4f4f4;
            padding: 1rem;
            border-radius: 4px;
            margin-top: 1rem;
        }}
        
        .example-title {{
            font-weight: 600;
            margin-bottom: 0.5rem;
            font-size: 0.875rem;
        }}
        
        .example-code {{
            background-color: #262626;
            color: #f4f4f4;
            padding: 1rem;
            border-radius: 4px;
            overflow-x: auto;
            font-family: 'IBM Plex Mono', monospace;
            font-size: 0.875rem;
            line-height: 1.5;
        }}
        
        .footer {{
            margin-top: 3rem;
            padding: 2rem 3rem;
            background-color: #f4f4f4;
            border-top: 1px solid var(--cds-border-subtle-01);
            text-align: center;
            color: var(--cds-text-02);
            font-size: 0.75rem;
        }}
        
        code {{
            background-color: var(--cds-field-01);
            padding: 0.125rem 0.375rem;
            border-radius: 2px;
            font-family: 'IBM Plex Mono', monospace;
            font-size: 0.875rem;
        }}
        
        .array-items-container {{
            margin: 1rem 0;
            padding: 1rem;
            background-color: #e8f4fd;
            border-left: 4px solid #0f62fe;
            border-radius: 4px;
        }}
        
        .array-items-header {{
            font-weight: 600;
            font-size: 0.875rem;
            color: #0f62fe;
            margin-bottom: 0.75rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }}
        
        .array-items-content {{
            padding-left: 0.5rem;
        }}
        
        table {{
            border-collapse: collapse;
            width: 100%;
            margin: 12px 0;
        }}
        
        th {{
            font-weight: bold;
            text-align: left;
            padding: 8px;
            border: 1px solid #ddd;
            background-color: #f4f4f4;
        }}
        
        td {{
            padding: 8px;
            border: 1px solid #ddd;
        }}
        
        .level-0 {{ margin-left: 0; }}
        .level-1 {{ margin-left: 1rem; }}
        .level-2 {{ margin-left: 2rem; }}
        .level-3 {{ margin-left: 3rem; }}
        
        .search-highlight {{
            background-color: #fff1c2;
            padding: 0.125rem 0.25rem;
            border-radius: 2px;
            font-weight: 600;
        }}
        
        .section.search-hidden {{
            display: none;
        }}
        
        .property.search-hidden {{
            display: none;
        }}
        
        .expand-collapse-btn {{
            background-color: #393939;
            color: #ffffff;
            border: 1px solid #525252;
            padding: 0.5rem 1rem;
            border-radius: 4px;
            cursor: pointer;
            font-size: 0.875rem;
            font-family: 'IBM Plex Sans', 'Helvetica Neue', Arial, sans-serif;
            transition: background-color 0.11s;
        }}
        
        .expand-collapse-btn:hover {{
            background-color: #525252;
        }}
    </style>
</head>
'''
    
    def _generate_body_start(self, title: str, description: str) -> str:
        """Generate the body opening and header."""
        desc_html = self._format_description(description) if description else ''
        return f'''<body>
    <div class="header">
        <h1>{self._escape_html(title)}</h1>
        {f'<div class="description">{desc_html}</div>' if desc_html else ''}
        <div class="search-container">
            <input type="text" id="searchInput" class="search-input" placeholder="Search properties, descriptions, and types..." oninput="performSearch()" />
            <button class="search-clear" id="searchClear" onclick="clearSearch()" title="Clear search">✕</button>
            <div class="search-results-info" id="searchResults"></div>
        </div>
    </div>
    <div class="container">
'''
    
    def _generate_schema_content(self, schema: Dict[str, Any], level: int = 0) -> str:
        """Generate content for a schema object."""
        html = ''
        
        if 'properties' in schema:
            html += self._generate_properties(schema, level)
        
        return html
    
    def _generate_definition_section(self, name: str, schema: Dict[str, Any], level: int = 0) -> str:
        """Generate a collapsible section for a definition."""
        section_id = self._generate_id(name)
        description = schema.get('description', '')
        examples = schema.get('examples', [])
        prop_type = schema.get('type', '')
        
        html = f'''
        <div class="section" id="{section_id}">
            <div class="section-header" onclick="toggleSection('{section_id}')">
                <h{2 + level}>
                    {self._escape_html(name)}
                    {f'<span class="property-type">{prop_type}</span>' if prop_type else ''}
                </h{2 + level}>
                <span class="toggle-icon">▼</span>
            </div>
            <div class="section-content">
'''
        
        if description:
            html += f'<div class="property-description">{self._format_description(description)}</div>\n'
        
        # Handle $ref
        if '$ref' in schema:
            ref_schema, _ = self.resolve_ref(schema['$ref'], self.schema_path)
            # Merge examples from both schemas
            ref_examples = ref_schema.get('examples', [])
            if ref_examples and not examples:
                examples = ref_examples
            html += self._generate_schema_content(ref_schema, level + 1)
        elif 'properties' in schema:
            # Add properties container with header if there's a description
            if description:
                html += '<div class="nested-section">\n'
                html += '<div class="properties-header">⚙️ Properties</div>\n'
            html += self._generate_properties(schema, level + 1)
            if description:
                html += '</div>\n'
        elif schema.get('type') == 'array' and 'items' in schema:
            html += self._generate_array_items(schema['items'], level + 1)
        else:
            # For simple schemas (enum, type only, etc.), display as a property
            html += self._generate_simple_schema_display(schema)
        
        # Add examples for this definition if present
        if examples:
            html += self._generate_inline_examples(examples)
        
        html += '''
            </div>
        </div>
'''
        return html
    
    def _generate_properties(self, schema: Dict[str, Any], level: int = 0) -> str:
        """Generate HTML for schema properties."""
        properties = schema.get('properties', {})
        required = schema.get('required', [])
        
        html = ''
        for prop_name, prop_schema in properties.items():
            html += self._generate_property(prop_name, prop_schema, prop_name in required, level)
        
        return html
    
    def _generate_property(self, name: str, schema: Dict[str, Any], is_required: bool, level: int) -> str:
        """Generate HTML for a single property."""
        # Handle $ref and $dynamicRef
        if '$ref' in schema:
            ref_schema, ref_name = self.resolve_ref(schema['$ref'], self.schema_path)
            return self._generate_definition_section(name, ref_schema, level)
        
        if '$dynamicRef' in schema:
            ref_schema, ref_name = self.resolve_ref(schema['$dynamicRef'], self.schema_path)
            return self._generate_definition_section(name, ref_schema, level)
        
        prop_type = schema.get('type', 'any')
        description = schema.get('description', '')
        default = schema.get('default')
        enum_values = schema.get('enum', [])
        const_value = schema.get('const')
        
        # Check if this is a complex nested object or array that should be collapsible
        has_nested_properties = prop_type == 'object' and 'properties' in schema
        has_array_items = prop_type == 'array' and ('items' in schema or 'prefixItems' in schema)
        has_dependent_schemas = 'dependentSchemas' in schema
        has_unevaluated = 'unevaluatedProperties' in schema or 'unevaluatedItems' in schema
        
        # If it's a nested object or array with items, make it collapsible
        if has_nested_properties or has_array_items or has_dependent_schemas or has_unevaluated:
            section_id = self._generate_id(f"{name}-{level}")
            
            html = f'''
        <div class="section" id="{section_id}">
            <div class="section-header" onclick="toggleSection('{section_id}')">
                <h{min(3 + level, 6)}>
                    {self._escape_html(name)}
                    <span class="property-type">{prop_type}</span>
                    {f'<span class="property-required">required</span>' if is_required else ''}
                </h{min(3 + level, 6)}>
                <span class="toggle-icon">▼</span>
            </div>
            <div class="section-content">
'''
            
            if description:
                html += f'            <div class="property-description">{self._format_description(description)}</div>\n'
            
            if default is not None:
                html += f'            <div class="property-default"><strong>Default:</strong> <code>{self._escape_html(str(default))}</code></div>\n'
            
            if const_value is not None:
                html += f'            <div class="property-default"><strong>Constant Value:</strong> <code>{self._escape_html(str(const_value))}</code></div>\n'
            
            # Handle x-examples
            if 'x-examples' in schema:
                html += self._generate_inline_examples(schema['x-examples'])
            
            # Handle nested objects
            if has_nested_properties:
                html += '            <div class="nested-section">\n'
                html += '            <div class="properties-header">⚙️ Properties</div>\n'
                html += self._generate_properties(schema, level + 1)
                html += '            </div>\n'
            
            # Handle arrays with items
            if has_array_items:
                html += '            <div class="nested-section">\n'
                if 'items' in schema:
                    html += self._generate_array_items(schema['items'], level + 1)
                if 'prefixItems' in schema:
                    html += self._generate_prefix_items(schema['prefixItems'], level + 1)
                html += '            </div>\n'
            
            # Handle dependentSchemas (JSON Schema 2019-09+)
            if has_dependent_schemas:
                html += self._generate_dependent_schemas(schema['dependentSchemas'], level + 1)
            
            # Handle unevaluatedProperties (JSON Schema 2019-09+)
            if 'unevaluatedProperties' in schema:
                html += self._generate_unevaluated_info('unevaluatedProperties', schema['unevaluatedProperties'])
            
            if 'unevaluatedItems' in schema:
                html += self._generate_unevaluated_info('unevaluatedItems', schema['unevaluatedItems'])
            
            html += '''
            </div>
        </div>
'''
            return html
        
        # For simple properties (not nested objects/arrays), use the original format
        html = f'''
        <div class="property">
            <div class="property-name">
                {self._escape_html(name)}
                <span class="property-type">{prop_type}</span>
                {f'<span class="property-required">required</span>' if is_required else ''}
            </div>
'''
        
        if description:
            html += f'            <div class="property-description">{self._format_description(description)}</div>\n'
        
        if default is not None:
            html += f'            <div class="property-default"><strong>Default:</strong> <code>{self._escape_html(str(default))}</code></div>\n'
        
        if const_value is not None:
            html += f'            <div class="property-default"><strong>Constant Value:</strong> <code>{self._escape_html(str(const_value))}</code></div>\n'
        
        if enum_values:
            html += '            <div class="property-enum">\n'
            html += '                <div class="property-enum-title">Allowed values:</div>\n'
            html += '                <div class="property-enum-values">\n'
            for enum_val in enum_values:
                html += f'                    <span class="enum-value">{self._escape_html(str(enum_val))}</span>\n'
            html += '                </div>\n'
            html += '            </div>\n'
        
        # Add validation constraints
        html += self._generate_validation_constraints(schema)
        
        # Handle dependentRequired (JSON Schema 2019-09+)
        if 'dependentRequired' in schema:
            html += self._generate_dependent_required(schema['dependentRequired'])
        
        # Handle x-examples
        if 'x-examples' in schema:
            html += self._generate_inline_examples(schema['x-examples'])
        
        html += '        </div>\n'
        return html
    
    def _generate_array_items(self, items_schema: Dict[str, Any], level: int) -> str:
        """Generate HTML for array items."""
        html = '<div class="array-items-container">\n'
        html += '<div class="array-items-header">📋 Array Items</div>\n'
        html += '<div class="array-items-content">\n'
        
        if '$ref' in items_schema:
            ref_schema, ref_name = self.resolve_ref(items_schema['$ref'], self.schema_path)
            html += self._generate_schema_content(ref_schema, level)
        elif '$dynamicRef' in items_schema:
            ref_schema, ref_name = self.resolve_ref(items_schema['$dynamicRef'], self.schema_path)
            html += self._generate_schema_content(ref_schema, level)
        elif 'properties' in items_schema:
            html += self._generate_properties(items_schema, level)
        elif items_schema.get('type'):
            html += f'<div class="property-description"><strong>Type:</strong> <code>{items_schema["type"]}</code></div>\n'
            if 'description' in items_schema:
                html += f'<div class="property-description">{self._format_description(items_schema["description"])}</div>\n'
        
        html += '</div>\n'  # Close array-items-content
        html += '</div>\n'  # Close array-items-container
        return html
    
    def _generate_prefix_items(self, prefix_items: List[Dict[str, Any]], level: int) -> str:
        """
        Generate HTML for prefixItems (JSON Schema 2020-12).
        prefixItems defines a tuple validation where each position has a specific schema.
        """
        html = '<div class="array-items-container">\n'
        html += '<div class="array-items-header">📋 Prefix Items (Tuple Validation)</div>\n'
        html += '<div class="array-items-content">\n'
        html += '<div class="property-description">Array items at specific positions must match these schemas:</div>\n'
        
        for idx, item_schema in enumerate(prefix_items):
            html += f'<div class="nested-section">\n'
            html += f'<div class="properties-header">Position {idx}</div>\n'
            
            if '$ref' in item_schema:
                ref_schema, ref_name = self.resolve_ref(item_schema['$ref'], self.schema_path)
                html += self._generate_schema_content(ref_schema, level)
            elif 'properties' in item_schema:
                html += self._generate_properties(item_schema, level)
            else:
                item_type = item_schema.get('type', 'any')
                html += f'<div class="property-description"><strong>Type:</strong> <code>{item_type}</code></div>\n'
                if 'description' in item_schema:
                    html += f'<div class="property-description">{self._format_description(item_schema["description"])}</div>\n'
            
            html += '</div>\n'
        
        html += '</div>\n'  # Close array-items-content
        html += '</div>\n'  # Close array-items-container
        return html
    
    def _generate_dependent_schemas(self, dependent_schemas: Dict[str, Dict[str, Any]], level: int) -> str:
        """
        Generate HTML for dependentSchemas (JSON Schema 2019-09+).
        Defines schemas that apply when certain properties are present.
        """
        html = '<div class="nested-section">\n'
        html += '<div class="properties-header">🔗 Dependent Schemas</div>\n'
        html += '<div class="property-description">Additional schema constraints that apply when specific properties are present:</div>\n'
        
        for prop_name, dep_schema in dependent_schemas.items():
            html += f'<div style="margin-top: 1rem;">\n'
            html += f'<div class="property-name">When <code>{self._escape_html(prop_name)}</code> is present:</div>\n'
            
            if 'properties' in dep_schema:
                html += self._generate_properties(dep_schema, level)
            elif 'required' in dep_schema:
                html += '<div class="property-description"><strong>Required properties:</strong> '
                html += ', '.join(f'<code>{self._escape_html(r)}</code>' for r in dep_schema['required'])
                html += '</div>\n'
            
            html += '</div>\n'
        
        html += '</div>\n'
        return html
    
    def _generate_dependent_required(self, dependent_required: Dict[str, List[str]]) -> str:
        """
        Generate HTML for dependentRequired (JSON Schema 2019-09+).
        Defines properties that become required when certain properties are present.
        """
        html = '<div class="property-enum" style="margin-top: 1rem;">\n'
        html += '<div class="property-enum-title">🔗 Dependent Required:</div>\n'
        html += '<div class="property-description" style="margin-top: 0.5rem;">\n'
        
        for prop_name, required_props in dependent_required.items():
            html += f'<div style="margin-bottom: 0.5rem;">When <code>{self._escape_html(prop_name)}</code> is present, '
            html += 'these properties are required: '
            html += ', '.join(f'<code>{self._escape_html(r)}</code>' for r in required_props)
            html += '</div>\n'
        
        html += '</div>\n'
        html += '</div>\n'
        return html
    
    def _generate_unevaluated_info(self, keyword: str, schema: Any) -> str:
        """
        Generate HTML for unevaluatedProperties or unevaluatedItems (JSON Schema 2019-09+).
        These keywords control whether additional properties/items are allowed.
        """
        html = '<div class="property-enum" style="margin-top: 1rem;">\n'
        
        if keyword == 'unevaluatedProperties':
            html += '<div class="property-enum-title">🔒 Unevaluated Properties:</div>\n'
        else:
            html += '<div class="property-enum-title">🔒 Unevaluated Items:</div>\n'
        
        html += '<div class="property-description" style="margin-top: 0.5rem;">\n'
        
        if schema is False:
            html += 'No additional properties/items are allowed beyond those explicitly defined.\n'
        elif schema is True:
            html += 'Additional properties/items are allowed without restriction.\n'
        elif isinstance(schema, dict):
            html += 'Additional properties/items must conform to this schema:\n'
            html += f'<div style="margin-top: 0.5rem;"><code>{self._escape_html(str(schema))}</code></div>\n'
        
        html += '</div>\n'
        html += '</div>\n'
        return html
    
    def _generate_simple_schema_display(self, schema: Dict[str, Any]) -> str:
        """Generate display for simple schemas (enum, const, type only, etc.)."""
        html = '<div class="property">\n'
        
        prop_type = schema.get('type', 'any')
        default = schema.get('default')
        enum_values = schema.get('enum', [])
        const_value = schema.get('const')
        
        if prop_type:
            html += f'<div class="property-name"><span class="property-type">{prop_type}</span></div>\n'
        
        if default is not None:
            html += f'<div class="property-default"><strong>Default:</strong> <code>{self._escape_html(str(default))}</code></div>\n'
        
        if const_value is not None:
            html += f'<div class="property-default"><strong>Constant Value:</strong> <code>{self._escape_html(str(const_value))}</code></div>\n'
        
        if enum_values:
            html += '<div class="property-enum">\n'
            html += '<div class="property-enum-title">Allowed values:</div>\n'
            html += '<div class="property-enum-values">\n'
            for enum_val in enum_values:
                html += f'<span class="enum-value">{self._escape_html(str(enum_val))}</span>\n'
            html += '</div>\n'
            html += '</div>\n'
        
        # Add validation constraints if present
        html += self._generate_validation_constraints(schema)
        
        html += '</div>\n'
        return html
    
    def _generate_validation_constraints(self, schema: Dict[str, Any]) -> str:
        """
        Generate HTML for validation constraints (min/max, pattern, format, etc.).
        Supports both older and newer JSON Schema drafts.
        """
        html = ''
        constraints = []
        
        # String constraints
        if 'minLength' in schema:
            constraints.append(f"Min length: {schema['minLength']}")
        if 'maxLength' in schema:
            constraints.append(f"Max length: {schema['maxLength']}")
        if 'pattern' in schema:
            constraints.append(f"Pattern: <code>{self._escape_html(schema['pattern'])}</code>")
        if 'format' in schema:
            constraints.append(f"Format: <code>{schema['format']}</code>")
        
        # Number constraints
        if 'minimum' in schema:
            constraints.append(f"Minimum: {schema['minimum']}")
        if 'maximum' in schema:
            constraints.append(f"Maximum: {schema['maximum']}")
        if 'exclusiveMinimum' in schema:
            val = schema['exclusiveMinimum']
            # In draft-04, exclusiveMinimum is boolean; in later drafts it's a number
            if isinstance(val, bool):
                constraints.append("Exclusive minimum (see 'minimum')")
            else:
                constraints.append(f"Exclusive minimum: {val}")
        if 'exclusiveMaximum' in schema:
            val = schema['exclusiveMaximum']
            if isinstance(val, bool):
                constraints.append("Exclusive maximum (see 'maximum')")
            else:
                constraints.append(f"Exclusive maximum: {val}")
        if 'multipleOf' in schema:
            constraints.append(f"Multiple of: {schema['multipleOf']}")
        
        # Array constraints
        if 'minItems' in schema:
            constraints.append(f"Min items: {schema['minItems']}")
        if 'maxItems' in schema:
            constraints.append(f"Max items: {schema['maxItems']}")
        if 'uniqueItems' in schema and schema['uniqueItems']:
            constraints.append("Items must be unique")
        if 'minContains' in schema:
            constraints.append(f"Min contains: {schema['minContains']}")
        if 'maxContains' in schema:
            constraints.append(f"Max contains: {schema['maxContains']}")
        
        # Object constraints
        if 'minProperties' in schema:
            constraints.append(f"Min properties: {schema['minProperties']}")
        if 'maxProperties' in schema:
            constraints.append(f"Max properties: {schema['maxProperties']}")
        if 'propertyNames' in schema:
            constraints.append("Property names must match a pattern")
        
        # Content constraints (JSON Schema 2019-09+)
        if 'contentMediaType' in schema:
            constraints.append(f"Content media type: <code>{schema['contentMediaType']}</code>")
        if 'contentEncoding' in schema:
            constraints.append(f"Content encoding: <code>{schema['contentEncoding']}</code>")
        if 'contentSchema' in schema:
            constraints.append("Content must match a schema")
        
        if constraints:
            html += '<div class="property-enum" style="margin-top: 0.5rem;">\n'
            html += '<div class="property-enum-title">Validation Constraints:</div>\n'
            html += '<div class="property-description" style="margin-top: 0.5rem;">\n'
            for constraint in constraints:
                html += f'<div>• {constraint}</div>\n'
            html += '</div>\n'
            html += '</div>\n'
        
        return html
    
    def _generate_inline_examples(self, examples: List[Any]) -> str:
        """Generate inline examples for a definition section."""
        if not examples:
            return ''
        
        html = '<div style="margin-top: 1.5rem;">\n'
        html += '<div class="property-enum-title">Examples:</div>\n'
        
        for i, example in enumerate(examples, 1):
            example_yaml = yaml.dump(example, default_flow_style=False, sort_keys=False, indent=2)
            html += f'''
                <div class="example-section">
                    <div class="example-title">Example {i}</div>
                    <pre class="example-code">{self._escape_html(example_yaml)}</pre>
                </div>
'''
        
        html += '</div>\n'
        return html
    
    def _generate_examples_section(self, examples: List[Any]) -> str:
        """Generate examples section."""
        html = '''
        <div class="section" id="examples">
            <div class="section-header" onclick="toggleSection('examples')">
                <h2>Examples</h2>
                <span class="toggle-icon">▼</span>
            </div>
            <div class="section-content">
'''
        
        for i, example in enumerate(examples, 1):
            example_yaml = yaml.dump(example, default_flow_style=False, sort_keys=False, indent=2)
            html += f'''
                <div class="example-section">
                    <div class="example-title">Example {i}</div>
                    <pre class="example-code">{self._escape_html(example_yaml)}</pre>
                </div>
'''
        
        html += '''
            </div>
        </div>
'''
        return html
    
    def _generate_footer(self) -> str:
        """Generate HTML footer."""
        current_year = datetime.now().year
        return f'''
    </div>
    <div class="footer">
        Copyright IBM Corp. {current_year}
    </div>
    <script>
        function toggleSection(sectionId) {{
            const section = document.getElementById(sectionId);
            const header = section.querySelector('.section-header');
            const content = section.querySelector('.section-content');
            
            header.classList.toggle('expanded');
            content.classList.toggle('expanded');
        }}
        
        function expandAll() {{
            const allSections = document.querySelectorAll('.section');
            allSections.forEach(section => {{
                const header = section.querySelector('.section-header');
                const content = section.querySelector('.section-content');
                if (header && content) {{
                    header.classList.add('expanded');
                    content.classList.add('expanded');
                }}
            }});
        }}
        
        function collapseAll() {{
            const allSections = document.querySelectorAll('.section');
            allSections.forEach(section => {{
                const header = section.querySelector('.section-header');
                const content = section.querySelector('.section-content');
                if (header && content) {{
                    header.classList.remove('expanded');
                    content.classList.remove('expanded');
                }}
            }});
        }}
        
        function performSearch() {{
            const searchInput = document.getElementById('searchInput');
            const searchClear = document.getElementById('searchClear');
            const searchResults = document.getElementById('searchResults');
            const query = searchInput.value.toLowerCase().trim();
            
            // Show/hide clear button
            if (query) {{
                searchClear.classList.add('visible');
            }} else {{
                searchClear.classList.remove('visible');
            }}
            
            // Remove previous highlights
            document.querySelectorAll('.search-highlight').forEach(el => {{
                const parent = el.parentNode;
                parent.replaceChild(document.createTextNode(el.textContent), el);
                parent.normalize();
            }});
            
            if (!query) {{
                // Clear search - show all sections and properties
                document.querySelectorAll('.section, .property').forEach(el => {{
                    el.classList.remove('search-hidden');
                }});
                searchResults.textContent = '';
                return;
            }}
            
            let matchCount = 0;
            const allSections = document.querySelectorAll('.section');
            const allProperties = document.querySelectorAll('.property');
            
            // First, hide everything
            allSections.forEach(section => section.classList.add('search-hidden'));
            allProperties.forEach(prop => prop.classList.add('search-hidden'));
            
            // Search in sections
            allSections.forEach(section => {{
                let sectionMatches = false;
                const header = section.querySelector('.section-header');
                const content = section.querySelector('.section-content');
                
                if (header) {{
                    const headerText = header.textContent.toLowerCase();
                    if (headerText.includes(query)) {{
                        sectionMatches = true;
                        highlightText(header, query);
                    }}
                }}
                
                if (content) {{
                    const descriptions = content.querySelectorAll('.property-description, .property-name, .property-type, .enum-value');
                    descriptions.forEach(desc => {{
                        const text = desc.textContent.toLowerCase();
                        if (text.includes(query)) {{
                            sectionMatches = true;
                            highlightText(desc, query);
                        }}
                    }});
                }}
                
                if (sectionMatches) {{
                    section.classList.remove('search-hidden');
                    // Auto-expand matching sections
                    if (header && content) {{
                        header.classList.add('expanded');
                        content.classList.add('expanded');
                    }}
                    matchCount++;
                }}
            }});
            
            // Search in properties
            allProperties.forEach(prop => {{
                let propMatches = false;
                const propName = prop.querySelector('.property-name');
                const propDesc = prop.querySelector('.property-description');
                const propType = prop.querySelector('.property-type');
                const enumValues = prop.querySelectorAll('.enum-value');
                
                if (propName && propName.textContent.toLowerCase().includes(query)) {{
                    propMatches = true;
                    highlightText(propName, query);
                }}
                
                if (propDesc && propDesc.textContent.toLowerCase().includes(query)) {{
                    propMatches = true;
                    highlightText(propDesc, query);
                }}
                
                if (propType && propType.textContent.toLowerCase().includes(query)) {{
                    propMatches = true;
                    highlightText(propType, query);
                }}
                
                enumValues.forEach(enumVal => {{
                    if (enumVal.textContent.toLowerCase().includes(query)) {{
                        propMatches = true;
                        highlightText(enumVal, query);
                    }}
                }});
                
                if (propMatches) {{
                    prop.classList.remove('search-hidden');
                    // Show parent section
                    let parentSection = prop.closest('.section');
                    while (parentSection) {{
                        parentSection.classList.remove('search-hidden');
                        const header = parentSection.querySelector('.section-header');
                        const content = parentSection.querySelector('.section-content');
                        if (header && content) {{
                            header.classList.add('expanded');
                            content.classList.add('expanded');
                        }}
                        parentSection = parentSection.parentElement.closest('.section');
                    }}
                    matchCount++;
                }}
            }});
            
            // Update results info
            if (matchCount === 0) {{
                searchResults.textContent = 'No results found';
            }} else if (matchCount === 1) {{
                searchResults.textContent = '1 result found';
            }} else {{
                searchResults.textContent = `${{matchCount}} results found`;
            }}
        }}
        
        function highlightText(element, query) {{
            // Don't highlight section headers directly - only their heading elements
            if (element.classList.contains('section-header')) {{
                // Find the h2, h3, or h4 element within the header
                const heading = element.querySelector('h2, h3, h4');
                if (heading) {{
                    highlightInTextNodes(heading, query);
                }}
                return;
            }}
            
            // For other elements, highlight in text nodes
            highlightInTextNodes(element, query);
        }}
        
        function highlightInTextNodes(element, query) {{
            const walker = document.createTreeWalker(
                element,
                NodeFilter.SHOW_TEXT,
                {{
                    acceptNode: function(node) {{
                        // Skip if parent is already a highlight or is a toggle icon
                        if (node.parentElement.classList.contains('search-highlight') ||
                            node.parentElement.classList.contains('toggle-icon') ||
                            node.parentElement.classList.contains('property-type') ||
                            node.parentElement.classList.contains('property-required')) {{
                            return NodeFilter.FILTER_REJECT;
                        }}
                        return NodeFilter.FILTER_ACCEPT;
                    }}
                }}
            );
            
            const textNodes = [];
            let node;
            while (node = walker.nextNode()) {{
                textNodes.push(node);
            }}
            
            textNodes.forEach(textNode => {{
                const text = textNode.textContent;
                const lowerText = text.toLowerCase();
                const index = lowerText.indexOf(query);
                
                if (index === -1) return;
                
                const before = text.substring(0, index);
                const match = text.substring(index, index + query.length);
                const after = text.substring(index + query.length);
                
                const fragment = document.createDocumentFragment();
                
                if (before) {{
                    fragment.appendChild(document.createTextNode(before));
                }}
                
                const highlight = document.createElement('span');
                highlight.className = 'search-highlight';
                highlight.textContent = match;
                fragment.appendChild(highlight);
                
                if (after) {{
                    fragment.appendChild(document.createTextNode(after));
                }}
                
                textNode.parentNode.replaceChild(fragment, textNode);
            }});
        }}
        
        function clearSearch() {{
            const searchInput = document.getElementById('searchInput');
            searchInput.value = '';
            performSearch();
            searchInput.focus();
        }}
        
        // Add keyboard shortcut (Ctrl/Cmd + K) to focus search
        document.addEventListener('keydown', function(e) {{
            if ((e.ctrlKey || e.metaKey) && e.key === 'k') {{
                e.preventDefault();
                document.getElementById('searchInput').focus();
            }}
        }});
    </script>
</body>
</html>
'''
    
    def _escape_html(self, text: str) -> str:
        """Escape HTML special characters."""
        if not isinstance(text, str):
            text = str(text)
        text = text.replace('&', '\x26amp;')
        text = text.replace('<', '\x26lt;')
        text = text.replace('>', '\x26gt;')
        text = text.replace('"', '\x26quot;')
        text = text.replace("'", '\x26#39;')
        text = text.replace('`', '\x26#96;')  # Escape backticks to prevent JS template literal issues
        return text
    
    def _format_description(self, description: str) -> str:
        """Format description text, converting markdown to HTML."""
        if not description:
            return ''
        
        import re
        
        # If markdown library is available, use it for full markdown support
        if MARKDOWN_AVAILABLE and markdown_module:
            # Preprocess: Fix flattened markdown tables (from YAML > folding)
            # Pattern: "Header1 | Header2 ----- | ----- row1col1 | row1col2 row2col1 | row2col2"
            # Find table pattern: word | word followed by dashes | dashes, then capture everything after
            table_pattern = r'([A-Z][a-zA-Z\s]+)\s*\|\s*([A-Z][a-zA-Z\s]+)\s+([-]{3,})\s*\|\s*([-]{3,})\s+(.+?)(?=\n\n|\Z)'
            
            def fix_table(match):
                header1, header2, sep1, sep2, rows_text = match.groups()
                # Build table with proper newlines
                table = f'\n\n{header1.strip()} | {header2.strip()}\n{sep1} | {sep2}\n'
                # Split rows: look for pattern "code | description" where code is alphanumeric/underscore
                # Description continues until we hit another "code |" pattern
                row_pattern = r'([a-zA-Z0-9_]+)\s*\|\s*([^|]+?)(?=\s+[a-zA-Z0-9_]+\s*\||$)'
                rows = re.findall(row_pattern, rows_text, re.DOTALL)
                for col1, col2 in rows:
                    # Clean up the second column
                    col2_clean = col2.strip()
                    # Remove any trailing content that looks like it belongs to the next row
                    col2_clean = re.sub(r'\s+[a-zA-Z0-9_]+\s*$', '', col2_clean)
                    if col2_clean:  # Only add if we have content
                        table += f'{col1.strip()} | {col2_clean}\n'
                return table + '\n'
            
            description = re.sub(table_pattern, fix_table, description, flags=re.DOTALL)
            
            # Configure markdown with extensions (no nl2br to avoid breaking tables)
            md = markdown_module.Markdown(extensions=['fenced_code', 'tables'])
            html = md.convert(description)
            
            # Escape HTML entities in code blocks to prevent browser interpretation
            def escape_code_in_pre(match):
                code = match.group(1)
                code = code.replace('&', '\x26amp;')
                code = code.replace('<', '\x26lt;')
                code = code.replace('>', '\x26gt;')
                code = code.replace('"', '\x26quot;')
                return f'<pre><code>{code}</code></pre>'
            
            html = re.sub(r'<pre><code>(.*?)</code></pre>', escape_code_in_pre, html, flags=re.DOTALL)
            
            # Escape HTML entities in inline code
            def escape_code_inline(match):
                code = match.group(1)
                code = code.replace('&', '\x26amp;')
                code = code.replace('<', '\x26lt;')
                code = code.replace('>', '\x26gt;')
                code = code.replace('"', '\x26quot;')
                return f'<code>{code}</code>'
            
            html = re.sub(r'<code>(.*?)</code>', escape_code_inline, html)
            
            return html
        
        # Fallback: manual markdown processing
        import re
        
        # Helper function to escape HTML in code content
        def escape_code_content(match):
            content = match.group(2) if match.lastindex >= 2 else match.group(1)
            # Escape HTML entities in code content
            content = content.replace('&', '\x26amp;')
            content = content.replace('<', '\x26lt;')
            content = content.replace('>', '\x26gt;')
            content = content.replace('"', '\x26quot;')
            if match.lastindex >= 2:  # Multi-line code block
                return f'<pre><code>{content}</code></pre>'
            else:  # Inline code
                return f'<code>{content}</code>'
        
        # First, handle code blocks (triple backticks) - both multi-line and single-line
        # Multi-line: ```lang\ncode\n```
        description = re.sub(r'```(\w+)?\n(.*?)```', escape_code_content, description, flags=re.DOTALL)
        # Single-line: ``` code ```
        description = re.sub(r'```\s*(.*?)\s*```', escape_code_content, description)
        
        # Then handle inline code (single backticks) - convert to <code>
        description = re.sub(r'`([^`]+)`', escape_code_content, description)
        
        # Convert markdown headings to bold
        description = re.sub(r'^###\s+(.+)$', r'<strong>\1</strong>', description, flags=re.MULTILINE)
        
        # Protect code blocks from newline processing by replacing them with placeholders
        code_blocks = []
        def save_code_block(match):
            code_blocks.append(match.group(0))
            return f'|||CODE_BLOCK_{len(code_blocks)-1}|||'
        description = re.sub(r'<pre>.*?</pre>', save_code_block, description, flags=re.DOTALL)
        
        # Replace double newlines with paragraph separator marker
        description = description.replace('\n\n', '|||PARAGRAPH|||')
        
        # Replace <br><br> with paragraph separator marker
        description = description.replace('<br><br>', '|||PARAGRAPH|||')
        
        # Convert single newlines to <br> tags
        description = description.replace('\n', '<br>\n')
        
        # Restore code blocks
        for i, block in enumerate(code_blocks):
            description = description.replace(f'|||CODE_BLOCK_{i}|||', block)
        
        # Split by paragraph markers and wrap each in <p> tags
        if '|||PARAGRAPH|||' in description:
            paragraphs = description.split('|||PARAGRAPH|||')
            description = ''.join(f'<p>{p.strip()}</p>' for p in paragraphs if p.strip())
        else:
            # Wrap in paragraph if not already wrapped
            if not description.strip().startswith('<p'):
                description = f'<p>{description}</p>'
        
        return description
    
    def _generate_id(self, name: str) -> str:
        """Generate a valid HTML ID from a name."""
        return re.sub(r'[^a-zA-Z0-9-_]', '-', name.lower())
    
    def generate(self) -> None:
        """Generate the documentation and write to file."""
        html = self.generate_html()
        
        with open(self.output_path, 'w', encoding='utf-8') as f:
            f.write(html)
        
        logger.info(f"Documentation generated: {self.output_path}")


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        logger.error("Usage: python generate_schema_docs.py <schema_file> [output_file]")
        logger.error("\nExample:")
        logger.error("  python generate_schema_docs.py schemas/test/verify-directory-server.yaml")
        logger.error("  python generate_schema_docs.py schemas/test/verify-directory-server.yaml output.html")
        sys.exit(1)
    
    schema_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    if not os.path.exists(schema_file):
        logger.error(f"Schema file not found: {schema_file}")
        sys.exit(1)
    
    generator = SchemaDocGenerator(schema_file, output_file)
    generator.generate()


if __name__ == '__main__':
    main()
