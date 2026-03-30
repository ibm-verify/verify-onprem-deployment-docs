#!/usr/bin/env python3
"""
IBM Confidential
PID 5725-X36
Copyright IBM Corp. 2026

Documentation Regeneration Script
Regenerates all HTML documentation pages from schema files.
"""

import os
import sys
import subprocess
import tempfile
import argparse
import logging
from pathlib import Path
from typing import List, Tuple, Set, Optional
import yaml
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)


class DocumentationRegenerator:
    """Regenerate all HTML documentation from schema files."""
    
    def __init__(self, schemas_dir: str = "schemas", pages_dir: str = "pages"):
        """
        Initialize the regenerator.
        
        Args:
            schemas_dir: Directory containing schema files
            pages_dir: Directory for output HTML files
        """
        self.schemas_dir = Path(schemas_dir)
        self.pages_dir = Path(pages_dir)
        self.temp_files: List[Path] = []
        self.processed_schemas: Set[str] = set()
        
        # Ensure pages directory exists
        self.pages_dir.mkdir(exist_ok=True)
        
    def find_schema_files(self) -> List[Tuple[Path, str]]:
        """
        Find all main schema files in the schemas directory.
        
        Returns:
            List of tuples (file_path, file_type) where file_type is 'openapi' or 'jsonschema'
        """
        schema_files = []
        
        if not self.schemas_dir.exists():
            logger.error(f"Schemas directory not found: {self.schemas_dir}")
            return schema_files
        
        # Recursively find all YAML and JSON files
        for file_path in self.schemas_dir.rglob('*'):
            if not file_path.is_file():
                continue
                
            # Skip certain files
            if file_path.name in ['README.md', 'index.html.template']:
                continue
                
            # Only process YAML and JSON files
            if file_path.suffix not in ['.yaml', '.yml', '.json']:
                continue
            
            # Only process main schema files
            if not self._is_main_schema(file_path):
                continue
            
            # Determine file type
            file_type = self._detect_schema_type(file_path)
            if file_type:
                schema_files.append((file_path, file_type))
        
        return sorted(schema_files)
    
    def _detect_schema_type(self, file_path: Path) -> Optional[str]:
        """
        Detect if a file is an OpenAPI or JSON Schema file.
        
        Args:
            file_path: Path to the schema file
            
        Returns:
            'openapi', 'jsonschema', or None if not a schema file
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                if file_path.suffix == '.json':
                    content = json.load(f)
                else:
                    content = yaml.safe_load(f)
            
            if not isinstance(content, dict):
                return None
            
            # Check for OpenAPI
            if 'openapi' in content:
                return 'openapi'
            
            # Check for JSON Schema
            if '$schema' in content or 'definitions' in content or '$defs' in content:
                return 'jsonschema'
            
            # If it has properties but no clear indicator, assume JSON Schema
            if 'properties' in content or 'type' in content:
                return 'jsonschema'
            
            return None
            
        except Exception as e:
            logger.warning(f"Could not read {file_path}: {e}")
            return None
    
    def _get_output_path(self, schema_path: Path) -> Path:
        """
        Generate output HTML path from schema path, mirroring directory structure.
        
        Args:
            schema_path: Path to the schema file
            
        Returns:
            Output HTML path relative to pages_dir
        """
        rel_path = schema_path.relative_to(self.schemas_dir)
        
        # Get the directory structure (all parts except the filename)
        dir_parts = rel_path.parts[:-1]
        
        # Get the base filename
        base_name = schema_path.stem
        
        # Remove any .jsonschema suffix if present
        base_name = base_name.replace('.jsonschema', '')
        
        # Construct the output path with mirrored directory structure
        if dir_parts:
            output_dir = self.pages_dir.joinpath(*dir_parts)
            return output_dir / f"{base_name}.html"
        else:
            return self.pages_dir / f"{base_name}.html"
    
    def _is_main_schema(self, schema_path: Path) -> bool:
        """
        Determine if a schema file is a main schema (should generate documentation).
        
        Main schemas are typically:
        - Files that match their parent directory name
        - Files in the root schemas directory
        - OpenAPI specification files (detected by content, not filename)
        - Files that are top-level schemas (have $schema and $ref at root)
        
        Args:
            schema_path: Path to the schema file
            
        Returns:
            True if this is a main schema file
        """
        rel_path = schema_path.relative_to(self.schemas_dir)
        
        # Files in root schemas directory are main schemas
        if len(rel_path.parts) == 1:
            return True
        
        # Check if this is an OpenAPI specification (by content, not filename)
        # OpenAPI specs are always main schemas
        schema_type = self._detect_schema_type(schema_path)
        if schema_type == 'openapi':
            return True
        
        # Check if filename matches parent directory name
        parent_dir = rel_path.parts[-2]
        filename_stem = schema_path.stem
        
        # Main schema patterns:
        # - verify-directory-server.yaml in isvd/
        # - example-showcase.yaml in example/
        # Check if the filename contains the parent directory name
        # or if parent directory name is in the filename
        if parent_dir in filename_stem or filename_stem in parent_dir:
            return True
        
        # Check if this is a top-level schema by examining its content
        # Top-level schemas have both $schema and $ref at the root level
        if self._is_top_level_schema(schema_path):
            return True
        
        return False
    
    def _is_top_level_schema(self, schema_path: Path) -> bool:
        """
        Check if a schema file is a top-level schema definition.
        
        Top-level schemas typically have:
        - A $schema property at the root
        - A $ref property at the root pointing to a definition
        - A title property describing the schema
        
        Args:
            schema_path: Path to the schema file
            
        Returns:
            True if this is a top-level schema
        """
        try:
            with open(schema_path, 'r', encoding='utf-8') as f:
                if schema_path.suffix == '.json':
                    content = json.load(f)
                else:
                    content = yaml.safe_load(f)
            
            if not isinstance(content, dict):
                return False
            
            # Check for top-level schema indicators
            has_schema = '$schema' in content
            has_ref = '$ref' in content
            has_title = 'title' in content
            
            # A top-level schema should have $schema and either $ref or title
            return has_schema and (has_ref or has_title)
            
        except Exception as e:
            # If we can't read the file, assume it's not a top-level schema
            return False
    
    def convert_openapi_to_jsonschema(self, openapi_path: Path) -> Path:
        """
        Convert an OpenAPI file to JSON Schema.
        
        Args:
            openapi_path: Path to the OpenAPI file
            
        Returns:
            Path to the generated JSON Schema file
        """
        # Generate temporary output path
        temp_output = openapi_path.with_suffix('.jsonschema.yaml')
        
        logger.info(f"Converting OpenAPI to JSON Schema: {openapi_path}")
        
        # Run the conversion script
        result = subprocess.run(
            ['python3', 'openapi_to_jsonschema.py', str(openapi_path), str(temp_output)],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            logger.error(f"Error converting {openapi_path}:")
            logger.error(result.stderr)
            raise RuntimeError(f"OpenAPI conversion failed for {openapi_path}")
        
        # Track this as a temporary file to clean up later
        self.temp_files.append(temp_output)
        
        return temp_output
    
    def generate_documentation(self, schema_path: Path, output_path: Path) -> None:
        """
        Generate HTML documentation from a schema file.
        
        Args:
            schema_path: Path to the schema file
            output_path: Path for the output HTML file
        """
        logger.info(f"Generating documentation: {schema_path} -> {output_path}")
        
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Run the documentation generator
        result = subprocess.run(
            ['python3', 'generate_schema_docs.py', str(schema_path), str(output_path)],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            logger.error(f"Error generating documentation for {schema_path}:")
            logger.error(result.stderr)
            raise RuntimeError(f"Documentation generation failed for {schema_path}")
        
        # Track this schema as processed (store relative path from pages_dir)
        rel_path = output_path.relative_to(self.pages_dir)
        self.processed_schemas.add(str(rel_path))
    
    def generate_index(self) -> None:
        """Generate the index page."""
        logger.info(f"Generating index page: {self.pages_dir / 'index.html'}")
        
        # Run the index generator
        result = subprocess.run(
            ['python3', 'generate_index.py', str(self.pages_dir)],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            logger.error("Error generating index:")
            if result.stdout:
                logger.error(result.stdout)
            if result.stderr:
                logger.error(result.stderr)
            raise RuntimeError("Index generation failed")
        
        # Check for unknown schema files warning
        if "Warning" in result.stdout or "unknown" in result.stdout.lower():
            logger.warning("Unknown schema files detected!")
            logger.warning(result.stdout)
            # Don't fail here, just warn
    
    def check_for_unknown_files(self) -> bool:
        """
        Check if there are any HTML files in pages directory that weren't generated.
        
        Returns:
            True if unknown files found, False otherwise
        """
        if not self.pages_dir.exists():
            return False
        
        unknown_files = []
        # Recursively find all HTML files in pages directory
        for html_file in self.pages_dir.rglob('*.html'):
            rel_path = html_file.relative_to(self.pages_dir)
            # Skip index.html files at any level
            if html_file.name == 'index.html':
                continue
            # Check if this file was generated
            if str(rel_path) not in self.processed_schemas:
                unknown_files.append(str(rel_path))
        
        if unknown_files:
            logger.error("Unknown HTML files detected in pages directory:")
            for filename in sorted(unknown_files):
                logger.error(f"  - {filename}")
            logger.error("These files were not generated from any schema in the schemas directory.")
            logger.error("Please remove them or add corresponding schema files.")
            return True
        
        return False
    
    def cleanup_temp_files(self) -> None:
        """Remove temporary files created during processing."""
        for temp_file in self.temp_files:
            if temp_file.exists():
                logger.info(f"Cleaning up temporary file: {temp_file}")
                temp_file.unlink()
    
    def regenerate_all(self) -> int:
        """
        Regenerate all documentation.
        
        Returns:
            Exit code (0 for success, 1 for failure)
        """
        try:
            logger.info("=" * 70)
            logger.info("IBM Verify On-Premises Configuration Documentation Regeneration")
            logger.info("=" * 70)
            logger.info("")
            
            # Find all schema files
            logger.info("Scanning for schema files...")
            schema_files = self.find_schema_files()
            
            if not schema_files:
                logger.error("No schema files found!")
                return 1
            
            logger.info(f"Found {len(schema_files)} schema file(s)")
            logger.info("")
            
            # Process each schema file
            for schema_path, schema_type in schema_files:
                try:
                    # Determine output path (mirroring directory structure)
                    output_path = self._get_output_path(schema_path)
                    
                    # Convert OpenAPI to JSON Schema if needed
                    if schema_type == 'openapi':
                        json_schema_path = self.convert_openapi_to_jsonschema(schema_path)
                        self.generate_documentation(json_schema_path, output_path)
                    else:
                        self.generate_documentation(schema_path, output_path)
                    
                    logger.info("")
                    
                except Exception as e:
                    logger.error(f"Error processing {schema_path}: {e}")
                    return 1
            
            # Generate index page
            logger.info("-" * 70)
            self.generate_index()
            logger.info("")
            
            # Check for unknown files
            logger.info("-" * 70)
            logger.info("Checking for unknown files...")
            if self.check_for_unknown_files():
                return 1
            
            logger.info("No unknown files detected.")
            logger.info("")
            
            logger.info("=" * 70)
            logger.info("Documentation regeneration completed successfully!")
            logger.info(f"Generated {len(self.processed_schemas)} documentation page(s)")
            logger.info(f"Output directory: {self.pages_dir}")
            logger.info("=" * 70)
            
            return 0
            
        except KeyboardInterrupt:
            logger.error("\n\nInterrupted by user")
            return 1
        except Exception as e:
            logger.error(f"\n\nFatal error: {e}")
            import traceback
            traceback.print_exc()
            return 1
        finally:
            # Always cleanup temporary files
            if self.temp_files:
                logger.info("\nCleaning up temporary files...")
                self.cleanup_temp_files()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Regenerate all HTML documentation from schema files.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  %(prog)s
  %(prog)s --schemas-dir schemas --pages-dir pages
  %(prog)s -s schemas -p pages

The script will:
  1. Scan the schemas directory for OpenAPI and JSON Schema files
  2. Convert OpenAPI files to JSON Schema (temporary files are cleaned up)
  3. Generate HTML documentation for each main schema file
  4. Generate an index page listing all documentation
  5. Detect and fail if unknown HTML files are found in the pages directory
        '''
    )
    
    parser.add_argument(
        '-s', '--schemas-dir',
        default='schemas',
        help='Directory containing schema files (default: schemas)'
    )
    
    parser.add_argument(
        '-p', '--pages-dir',
        default='pages',
        help='Directory for output HTML files (default: pages)'
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version='%(prog)s 1.0.0'
    )
    
    args = parser.parse_args()
    
    # Create regenerator and run
    regenerator = DocumentationRegenerator(args.schemas_dir, args.pages_dir)
    exit_code = regenerator.regenerate_all()
    sys.exit(exit_code)


if __name__ == '__main__':
    main()

# Made with Bob