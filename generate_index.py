#!/usr/bin/env python3
"""
IBM Confidential
PID 5725-X36
Copyright IBM Corp. 2026

Index Page Generator
Generates an index page for IBM Verify on-premises component configuration documentation
conforming to IBM Carbon Design System standards.
"""

import os
import sys
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
from html.parser import HTMLParser

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)


class TitleExtractor(HTMLParser):
    """Extract title from HTML files."""
    
    def __init__(self):
        super().__init__()
        self.title: Optional[str] = None
        self.in_title = False
        
    def handle_starttag(self, tag, attrs):
        if tag == 'title':
            self.in_title = True
            
    def handle_endtag(self, tag):
        if tag == 'title':
            self.in_title = False
            
    def handle_data(self, data):
        if self.in_title:
            self.title = data.strip()


class IndexGenerator:
    """Generate an index page for configuration documentation."""
    
    # Product metadata mapping with component descriptions
    PRODUCT_INFO = {
        'iag': {
            'name': 'IBM Application Gateway',
            'short_name': 'IAG',
            'description': 'Lightweight, container-based reverse proxy for web applications and APIs',
            'components': {
                'openapi': 'IBM Application Gateway configuration parameters and settings'
            }
        },
        'isvd': {
            'name': 'IBM Security Verify Directory',
            'short_name': 'ISVD',
            'description': 'High-performance LDAP directory server for identity management',
            'components': {
                'verify-directory-server': 'IBM Security Verify Directory Server configuration parameters and settings',
                'verify-directory-proxy': 'IBM Security Verify Directory Proxy configuration parameters and settings',
                'verify-directory-seed': 'IBM Security Verify Directory Seed configuration parameters and settings',
                'verify-directory-virtualdir': 'IBM Security Verify Directory Virtual Directory configuration parameters and settings',
                'verify-directory-webadmin': 'IBM Security Verify Directory Web Administration Tool configuration parameters and settings'
            }
        },
        'isva': {
            'name': 'IBM Security Verify Access',
            'short_name': 'ISVA',
            'description': 'Comprehensive access management and federation solution',
            'components': {
                'verify-access': 'IBM Security Verify Access configuration parameters and settings'
            }
        },
        'isvg': {
            'name': 'IBM Security Verify Gateway',
            'short_name': 'ISVG',
            'description': 'Cloud-native gateway for secure access to applications',
            'components': {
                'verify-gateway': 'IBM Security Verify Gateway configuration parameters and settings'
            }
        },
        # Special category for examples and other documentation
        'examples': {
            'name': 'Examples',
            'short_name': 'Examples',
            'description': 'Example schemas and documentation',
            'components': {
                'example-showcase': 'Comprehensive example demonstrating all JSON Schema features and documentation capabilities'
            }
        }
    }
    
    def __init__(self, pages_dir: str, output_path: Optional[str] = None):
        """
        Initialize the generator.
        
        Args:
            pages_dir: Directory containing HTML documentation pages
            output_path: Path for the output index.html file (optional)
        """
        self.pages_dir = Path(pages_dir)
        self.output_path = Path(output_path) if output_path else self.pages_dir / 'index.html'
        
    def scan_pages(self) -> Dict[str, Dict[str, List[Dict[str, Any]]]]:
        """
        Scan the pages directory for HTML files and extract their titles.
        Organizes pages hierarchically by product and version.
        
        Returns:
            Nested dictionary: {product: {version: [page_info, ...]}}
        """
        pages_hierarchy = {}
        
        if not self.pages_dir.exists():
            logger.warning(f"Directory not found: {self.pages_dir}")
            return pages_hierarchy
            
        # Recursively find all HTML files
        for file_path in sorted(self.pages_dir.rglob('*.html')):
            # Skip index files at any level
            if file_path.name == 'index.html':
                continue
            
            # Get relative path from pages_dir
            rel_path = file_path.relative_to(self.pages_dir)
            
            # Parse the directory structure: product/version/file.html
            parts = rel_path.parts
            if len(parts) >= 3:
                product = parts[0]
                version = parts[1]
            elif len(parts) == 2:
                # File in product directory without version
                product = parts[0]
                version = 'default'
            else:
                # File in root directory
                product = 'other'
                version = 'default'
            
            # Extract title from HTML
            title = self._extract_title(file_path)
            
            # Generate a description based on the filename and path
            description = self._generate_description(file_path.stem, rel_path)
            
            # Initialize nested structure if needed
            if product not in pages_hierarchy:
                pages_hierarchy[product] = {}
            if version not in pages_hierarchy[product]:
                pages_hierarchy[product][version] = []
            
            pages_hierarchy[product][version].append({
                'filename': str(rel_path),
                'title': title or file_path.stem.replace('-', ' ').title(),
                'description': description,
                'stem': file_path.stem
            })
            
        return pages_hierarchy
    
    def _extract_title(self, file_path: Path) -> Optional[str]:
        """Extract the title from an HTML file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                parser = TitleExtractor()
                parser.feed(content)
                return parser.title
        except Exception as e:
            logger.warning(f"Could not extract title from {file_path}: {e}")
            return None
    
    def _generate_description(self, filename_stem: str, rel_path: Path) -> str:
        """
        Generate a description based on the component filename and product.
        
        Args:
            filename_stem: The filename without extension
            rel_path: Relative path from pages directory
            
        Returns:
            Description string
            
        Raises:
            ValueError: If no description is defined for the component
        """
        # Extract product from path
        parts = rel_path.parts
        product = parts[0] if len(parts) >= 1 else 'other'
        
        # Look up component description in PRODUCT_INFO
        if product in self.PRODUCT_INFO:
            components = self.PRODUCT_INFO[product].get('components', {})
            if filename_stem in components:
                return components[filename_stem]
        
        # If not found, raise an error with helpful message
        raise ValueError(
            f"No description defined for component '{filename_stem}' in product '{product}' (path: {rel_path}).\n"
            f"Please add the component to PRODUCT_INFO['{product}']['components'] in generate_index.py:\n"
            f"  '{filename_stem}': 'Your component description here'"
        )
    
    def generate_html(self) -> str:
        """Generate the complete HTML index page."""
        pages_hierarchy = self.scan_pages()
        
        html = self._generate_header()
        html += self._generate_body_start()
        html += self._generate_page_list(pages_hierarchy)
        html += self._generate_footer()
        
        return html
    
    def _generate_header(self) -> str:
        """Generate HTML header with IBM Carbon styles."""
        amp = '&'
        lt = '<'
        gt = '>'
        return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>IBM Verify On-Premises Configuration Documentation</title>
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
            --cds-interactive-01: #0f62fe;
            --cds-hover-ui: #e8e8e8;
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
        
        .container {{
            max-width: 1584px;
            margin: 0 auto;
            padding: 2rem 3rem;
        }}
        
        .intro-section {{
            margin-bottom: 3rem;
            padding: 1.5rem;
            background-color: #e8f4fd;
            border-left: 4px solid #0f62fe;
            border-radius: 4px;
        }}
        
        .intro-section h2 {{
            margin: 0 0 1rem 0;
            font-size: 1.25rem;
            font-weight: 600;
            color: var(--cds-text-01);
        }}
        
        .intro-section p {{
            margin: 0;
            color: var(--cds-text-02);
            font-size: 0.875rem;
            line-height: 1.5;
        }}
        
        .product-section {{
            margin-top: 3rem;
            margin-bottom: 2rem;
        }}
        
        .product-header {{
            background: linear-gradient(90deg, #0f62fe 0%, #0353e9 100%);
            color: #ffffff;
            padding: 1.5rem 2rem;
            border-radius: 4px;
            margin-bottom: 1.5rem;
            cursor: pointer;
            transition: all 0.2s;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }}
        
        .product-header:hover {{
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
            transform: translateY(-2px);
        }}
        
        .product-header-content {{
            flex: 1;
        }}
        
        .product-title {{
            margin: 0;
            font-size: 1.75rem;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 0.75rem;
        }}
        
        .product-short-name {{
            background-color: rgba(255, 255, 255, 0.2);
            padding: 0.25rem 0.75rem;
            border-radius: 4px;
            font-size: 0.875rem;
            font-weight: 700;
            letter-spacing: 0.5px;
        }}
        
        .product-description {{
            margin: 0.5rem 0 0 0;
            font-size: 0.875rem;
            opacity: 0.9;
        }}
        
        .product-toggle {{
            font-size: 1.5rem;
            transition: transform 0.3s;
        }}
        
        .product-content {{
            display: block;
        }}
        
        .product-content.collapsed {{
            display: none;
        }}
        
        .product-header.collapsed .product-toggle {{
            transform: rotate(-90deg);
        }}
        
        .version-section {{
            margin-bottom: 2rem;
            padding-left: 1rem;
            border-left: 3px solid var(--cds-border-subtle-01);
        }}
        
        .version-header {{
            margin-bottom: 1rem;
            padding: 1rem 1.5rem;
            background-color: var(--cds-ui-01);
            border-radius: 4px;
            border-left: 4px solid #0f62fe;
            cursor: pointer;
            transition: all 0.2s;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }}
        
        .version-header:hover {{
            background-color: var(--cds-hover-ui);
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        }}
        
        .version-title {{
            margin: 0;
            font-size: 1.25rem;
            font-weight: 600;
            color: var(--cds-text-01);
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }}
        
        .version-badge {{
            background-color: #0f62fe;
            color: #ffffff;
            padding: 0.25rem 0.75rem;
            border-radius: 12px;
            font-size: 0.75rem;
            font-weight: 600;
        }}
        
        .version-toggle {{
            font-size: 1.25rem;
            transition: transform 0.3s;
            color: var(--cds-text-02);
        }}
        
        .version-content {{
            display: block;
        }}
        
        .version-content.collapsed {{
            display: none;
        }}
        
        .version-header.collapsed .version-toggle {{
            transform: rotate(-90deg);
        }}
        
        .page-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
            gap: 1.5rem;
            margin-top: 1rem;
        }}
        
        .page-card {{
            background-color: var(--cds-ui-02);
            border: 1px solid var(--cds-border-subtle-01);
            border-radius: 4px;
            transition: all 0.11s;
            overflow: hidden;
        }}
        
        .page-card:hover {{
            border-color: var(--cds-interactive-01);
            box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1);
        }}
        
        .page-card-link {{
            display: block;
            text-decoration: none;
            color: inherit;
            height: 100%;
        }}
        
        .page-card-header {{
            padding: 1.5rem;
            background-color: var(--cds-ui-01);
            border-bottom: 1px solid var(--cds-border-subtle-01);
        }}
        
        .page-card-title {{
            margin: 0;
            font-size: 1.125rem;
            font-weight: 600;
            color: var(--cds-interactive-01);
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }}
        
        .page-card-title::before {{
            content: "📄";
            font-size: 1.25rem;
        }}
        
        .page-card-body {{
            padding: 1.5rem;
        }}
        
        .page-card-description {{
            margin: 0;
            color: var(--cds-text-02);
            font-size: 0.875rem;
            line-height: 1.5;
        }}
        
        .page-card:hover .page-card-title {{
            text-decoration: underline;
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
        
        .empty-state {{
            text-align: center;
            padding: 3rem;
            color: var(--cds-text-02);
        }}
        
        .empty-state-icon {{
            font-size: 3rem;
            margin-bottom: 1rem;
        }}
        
        @media (max-width: 768px) {{
            .page-grid {{
                grid-template-columns: 1fr;
            }}
            
            .header {{
                padding: 1.5rem;
            }}
            
            .container {{
                padding: 1.5rem;
            }}
            
            .product-header {{
                padding: 1rem 1.5rem;
            }}
            
            .product-title {{
                font-size: 1.5rem;
            }}
        }}
    </style>
    <script>
        function toggleProduct(productId) {{
            const content = document.getElementById(productId + '-content');
            const header = document.getElementById(productId + '-header');
            
            if (content.classList.contains('collapsed')) {{
                content.classList.remove('collapsed');
                header.classList.remove('collapsed');
            }} else {{
                content.classList.add('collapsed');
                header.classList.add('collapsed');
            }}
        }}
        
        function toggleVersion(versionId) {{
            const content = document.getElementById(versionId + '-content');
            const header = document.getElementById(versionId + '-header');
            
            if (content.classList.contains('collapsed')) {{
                content.classList.remove('collapsed');
                header.classList.remove('collapsed');
            }} else {{
                content.classList.add('collapsed');
                header.classList.add('collapsed');
            }}
        }}
    </script>
</head>
'''
    
    def _generate_body_start(self) -> str:
        """Generate the body opening and header."""
        return '''<body>
    <div class="header">
        <h1>IBM Verify On-Premises Configuration Documentation</h1>
        <div class="description">
            Comprehensive configuration reference for IBM Verify on-premises components
        </div>
    </div>
    <div class="container">
        <div class="intro-section">
            <h2>📚 Configuration Documentation</h2>
            <p>
                This documentation provides detailed configuration information for IBM Verify on-premises components.
                Each page contains comprehensive parameter specifications, descriptions, and examples to help you
                configure and deploy your IBM Verify infrastructure.
            </p>
        </div>
'''
    
    def _generate_page_list(self, pages_hierarchy: Dict[str, Dict[str, List[Dict[str, Any]]]]) -> str:
        """Generate the hierarchical list of documentation pages organized by product and version."""
        if not pages_hierarchy:
            return '''
        <div class="empty-state">
            <div class="empty-state-icon">📭</div>
            <p>No configuration documentation pages found in this directory.</p>
        </div>
'''
        
        html = ''
        
        # Sort products alphabetically
        sorted_products = sorted(pages_hierarchy.keys())
        
        for product_id in sorted_products:
            versions = pages_hierarchy[product_id]
            
            # Get product information
            product_info = self.PRODUCT_INFO.get(product_id, {
                'name': product_id.upper(),
                'short_name': product_id.upper(),
                'description': f'{product_id.upper()} configuration documentation'
            })
            
            # Generate product section
            html += f'''
        <div class="product-section">
            <div class="product-header" id="{self._escape_html(product_id)}-header" onclick="toggleProduct('{self._escape_html(product_id)}')">
                <div class="product-header-content">
                    <h2 class="product-title">
                        {self._escape_html(product_info['name'])}
                        <span class="product-short-name">{self._escape_html(product_info['short_name'])}</span>
                    </h2>
                    <p class="product-description">{self._escape_html(product_info['description'])}</p>
                </div>
                <div class="product-toggle">▼</div>
            </div>
            <div class="product-content" id="{self._escape_html(product_id)}-content">
'''
            
            # Sort versions (try semantic versioning, fallback to string sort)
            sorted_versions = sorted(versions.keys(), key=lambda v: self._version_sort_key(v), reverse=True)
            
            for version in sorted_versions:
                pages = versions[version]
                
                # Create unique ID for this version section
                version_id = f"{product_id}-{version.replace('.', '-')}"
                
                # Generate version section (collapsed by default)
                html += f'''
                <div class="version-section">
                    <div class="version-header collapsed" id="{self._escape_html(version_id)}-header" onclick="toggleVersion('{self._escape_html(version_id)}')">
                        <h3 class="version-title">
                            Version <span class="version-badge">{self._escape_html(version)}</span>
                        </h3>
                        <div class="version-toggle">▼</div>
                    </div>
                    <div class="version-content collapsed" id="{self._escape_html(version_id)}-content">
                        <div class="page-grid">
'''
                
                # Generate page cards
                for page in pages:
                    html += f'''
                            <div class="page-card">
                                <a href="{self._escape_html(page['filename'])}" class="page-card-link">
                                    <div class="page-card-header">
                                        <h4 class="page-card-title">{self._escape_html(page['title'])}</h4>
                                    </div>
                                    <div class="page-card-body">
                                        <p class="page-card-description">{self._escape_html(page['description'])}</p>
                                    </div>
                                </a>
                            </div>
'''
                
                html += '''
                        </div>
                    </div>
                </div>
'''
            
            html += '''
            </div>
        </div>
'''
        
        return html
    
    def _version_sort_key(self, version: str) -> tuple:
        """
        Generate a sort key for version strings.
        Handles semantic versioning (e.g., "25.12", "11.0.0") and special cases like "default".
        
        Args:
            version: Version string
            
        Returns:
            Tuple for sorting (special versions first, then by numeric components)
        """
        if version == 'default':
            return (0,)  # Default versions come first
        
        try:
            # Try to parse as semantic version
            parts = version.split('.')
            return tuple(int(p) for p in parts)
        except (ValueError, AttributeError):
            # Fallback to string comparison
            return (1, version)
    
    def _generate_footer(self) -> str:
        """Generate HTML footer."""
        current_year = datetime.now().year
        return f'''
    </div>
    <div class="footer">
        Copyright IBM Corp. {current_year}
    </div>
</body>
</html>
'''
    
    def _escape_html(self, text: str) -> str:
        """Escape HTML special characters."""
        if not isinstance(text, str):
            text = str(text)
        text = text.replace('&', '&' + 'amp;')
        text = text.replace('<', '&' + 'lt;')
        text = text.replace('>', '&' + 'gt;')
        text = text.replace('"', '&' + 'quot;')
        text = text.replace("'", '&' + '#39;')
        return text
    
    def generate(self) -> None:
        """Generate the index page and write to file."""
        html = self.generate_html()
        
        with open(self.output_path, 'w', encoding='utf-8') as f:
            f.write(html)
        
        logger.info(f"Index page generated: {self.output_path}")


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        logger.error("Usage: python generate_index.py <pages_directory> [output_file]")
        logger.error("\nExample:")
        logger.error("  python generate_index.py pages")
        logger.error("  python generate_index.py pages pages/index.html")
        sys.exit(1)
    
    pages_dir = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    if not os.path.exists(pages_dir):
        logger.error(f"Directory not found: {pages_dir}")
        sys.exit(1)
    
    try:
        generator = IndexGenerator(pages_dir, output_file)
        generator.generate()
    except ValueError as e:
        logger.error(f"{e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
