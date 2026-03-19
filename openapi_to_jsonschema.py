#!/usr/bin/env python3
"""
IBM Confidential
PID 5725-X36
Copyright IBM Corp. 2026

OpenAPI to JSON Schema Converter
Converts OpenAPI 3.0 schema specifications to JSON Schema Draft 07 format.
"""

import yaml
import json
import sys
import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)


class OpenAPIToJSONSchemaConverter:
    """Convert OpenAPI 3.0 schemas to JSON Schema Draft 07."""
    
    def __init__(self, openapi_path: str, output_path: Optional[str] = None):
        """
        Initialize the converter.
        
        Args:
            openapi_path: Path to the OpenAPI schema file (YAML or JSON)
            output_path: Path for the output JSON Schema file (optional)
        """
        self.openapi_path = Path(openapi_path)
        self.output_path = Path(output_path) if output_path else self.openapi_path.with_suffix('.jsonschema.yaml')
        self.openapi_schema = None
        self.converted_files = {}  # Cache of converted files
        self.processing_files = set()  # Track files being processed to detect circular refs
        
    def load_openapi(self) -> Dict[str, Any]:
        """Load the OpenAPI schema file."""
        with open(self.openapi_path, 'r', encoding='utf-8') as f:
            if self.openapi_path.suffix in ['.yaml', '.yml']:
                schema = yaml.safe_load(f)
            else:
                schema = json.load(f)
        
        self.openapi_schema = schema
        return schema
    
    def convert(self) -> Dict[str, Any]:
        """
        Convert OpenAPI schema to JSON Schema.
        
        Returns:
            JSON Schema dictionary
        """
        if not self.openapi_schema:
            self.load_openapi()
        
        # Extract info
        info = self.openapi_schema.get('info', {})
        title = info.get('title', 'Schema Documentation')
        description = info.get('description', '')
        version = info.get('version', '1.0.0')
        
        # Build JSON Schema
        json_schema = {
            '$schema': 'http://json-schema.org/draft-07/schema#',
            'title': title,
            'description': description,
            'type': 'object',
            'properties': {},
            'definitions': {}
        }
        
        # Convert OpenAPI components/schemas to JSON Schema definitions
        if 'components' in self.openapi_schema and 'schemas' in self.openapi_schema['components']:
            schemas = self.openapi_schema['components']['schemas']
            
            for schema_name, schema_def in schemas.items():
                # Convert each schema
                converted_schema = self._convert_schema(schema_def)
                
                # Add all schemas as both properties and definitions
                # Properties make them top-level configuration options
                # Definitions allow them to be referenced
                json_schema['properties'][schema_name] = {'$ref': f'#/definitions/{schema_name}'}
                json_schema['definitions'][schema_name] = converted_schema
        
        # Add version property if present
        if 'components' in self.openapi_schema and 'schemas' in self.openapi_schema['components']:
            if 'version' in self.openapi_schema['components']['schemas']:
                json_schema['properties']['version'] = {
                    '$ref': '#/definitions/version'
                }
        
        return json_schema
    
    def _load_and_convert_external_file(self, file_path: str, json_pointer: str) -> Dict[str, Any]:
        """
        Load and convert an external schema file.
        
        Args:
            file_path: Path to the external file (relative to current file)
            json_pointer: JSON pointer within the file (e.g., #/secrets)
            
        Returns:
            Converted schema
        """
        # Resolve the file path relative to the main schema
        full_path = (self.openapi_path.parent / file_path).resolve()
        
        # Create a cache key that includes the JSON pointer
        cache_key = f"{full_path}#{json_pointer}" if json_pointer else str(full_path)
        
        # Check if already converted
        if cache_key in self.converted_files:
            return self.converted_files[cache_key]
        
        # Check for circular references
        if cache_key in self.processing_files:
            logger.warning(f"Circular reference detected for {file_path}#{json_pointer}")
            return {'type': 'object', 'description': f'Circular reference to {file_path}'}
        
        # Mark as being processed
        self.processing_files.add(cache_key)
        
        try:
            # Load the file
            with open(full_path, 'r', encoding='utf-8') as f:
                if full_path.suffix in ['.yaml', '.yml']:
                    schema = yaml.safe_load(f)
                else:
                    schema = json.load(f)
            
            # Navigate to the JSON pointer BEFORE converting
            if json_pointer:
                parts = [p for p in json_pointer.split('/') if p]
                for part in parts:
                    if isinstance(schema, dict):
                        schema = schema.get(part, {})
                    else:
                        logger.warning(f"Cannot navigate to {json_pointer} in {file_path}")
                        schema = {}
                        break
            
            # Now convert the extracted schema
            schema = self._convert_schema(schema)
            
            # Cache it
            self.converted_files[cache_key] = schema
            
            return schema
        finally:
            # Remove from processing set
            self.processing_files.discard(cache_key)
    
    def _convert_schema(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert an OpenAPI schema object to JSON Schema.
        
        Args:
            schema: OpenAPI schema object
            
        Returns:
            JSON Schema object
        """
        if not isinstance(schema, dict):
            return schema
        
        converted = {}
        
        # Copy basic properties
        for key in ['type', 'description', 'default', 'enum', 'format',
                    'minimum', 'maximum', 'minLength', 'maxLength',
                    'pattern', 'minItems', 'maxItems', 'uniqueItems',
                    'required', 'title', 'examples']:
            if key in schema:
                converted[key] = schema[key]
        
        # Copy x- extension properties (like x-examples, x-name, etc.)
        for key in schema:
            if key.startswith('x-'):
                converted[key] = schema[key]
        
        # Handle $ref
        if '$ref' in schema:
            ref = schema['$ref']
            # Convert OpenAPI component references to JSON Schema references
            if ref.startswith('#/components/schemas/'):
                # Convert to JSON Schema definition reference
                schema_name = ref.replace('#/components/schemas/', '')
                converted['$ref'] = f'#/definitions/{schema_name}'
            elif ref.startswith('#/'):
                # Internal reference, keep as-is but update format
                converted['$ref'] = ref.replace('#/components/schemas/', '#/definitions/')
            else:
                # External file reference - load and convert it
                if '#' in ref:
                    file_path, json_pointer = ref.split('#', 1)
                else:
                    file_path, json_pointer = ref, ''
                
                # Load and convert the external file
                try:
                    external_schema = self._load_and_convert_external_file(file_path, json_pointer)
                    # Instead of keeping the reference, inline the converted schema
                    return external_schema
                except Exception as e:
                    logger.warning(f"Could not load external reference {ref}: {e}")
                    converted['$ref'] = ref  # Keep original reference as fallback
        
        # Handle properties (for object types)
        if 'properties' in schema:
            converted['properties'] = {}
            for prop_name, prop_schema in schema['properties'].items():
                converted['properties'][prop_name] = self._convert_schema(prop_schema)
        
        # Handle items (for array types)
        if 'items' in schema:
            converted['items'] = self._convert_schema(schema['items'])
        
        # Handle allOf, anyOf, oneOf
        for key in ['allOf', 'anyOf', 'oneOf']:
            if key in schema:
                converted[key] = [self._convert_schema(s) for s in schema[key]]
        
        # Handle not
        if 'not' in schema:
            converted['not'] = self._convert_schema(schema['not'])
        
        # Handle additionalProperties
        if 'additionalProperties' in schema:
            if isinstance(schema['additionalProperties'], dict):
                converted['additionalProperties'] = self._convert_schema(schema['additionalProperties'])
            else:
                converted['additionalProperties'] = schema['additionalProperties']
        
        return converted
    
    def save(self, json_schema: Dict[str, Any]) -> None:
        """
        Save the JSON Schema to a file.
        
        Args:
            json_schema: The JSON Schema to save
        """
        with open(self.output_path, 'w', encoding='utf-8') as f:
            if self.output_path.suffix in ['.yaml', '.yml']:
                yaml.dump(json_schema, f, default_flow_style=False, sort_keys=False, indent=2)
            else:
                json.dump(json_schema, f, indent=2)
        
        logger.info(f"JSON Schema saved to: {self.output_path}")
    
    def convert_and_save(self) -> None:
        """Convert the OpenAPI schema and save to file."""
        json_schema = self.convert()
        self.save(json_schema)


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        logger.error("Usage: python openapi_to_jsonschema.py <openapi_file> [output_file]")
        logger.error("\nExample:")
        logger.error("  python openapi_to_jsonschema.py schemas/iag/openapi.yaml")
        logger.error("  python openapi_to_jsonschema.py schemas/iag/openapi.yaml output.yaml")
        sys.exit(1)
    
    openapi_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    if not os.path.exists(openapi_file):
        logger.error(f"OpenAPI file not found: {openapi_file}")
        sys.exit(1)
    
    converter = OpenAPIToJSONSchemaConverter(openapi_file, output_file)
    converter.convert_and_save()


if __name__ == '__main__':
    main()

# Made with Bob
