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
    
    def __init__(self, pages_dir: str, output_path: Optional[str] = None):
        """
        Initialize the generator.
        
        Args:
            pages_dir: Directory containing HTML documentation pages
            output_path: Path for the output index.html file (optional)
        """
        self.pages_dir = Path(pages_dir)
        self.output_path = Path(output_path) if output_path else self.pages_dir / 'index.html'
        
    def scan_pages(self) -> List[Dict[str, Any]]:
        """
        Scan the pages directory for HTML files and extract their titles.
        
        Returns:
            List of dictionaries containing page information
        """
        pages = []
        
        if not self.pages_dir.exists():
            logger.warning(f"Directory not found: {self.pages_dir}")
            return pages
            
        for file_path in sorted(self.pages_dir.glob('*.html')):
            # Skip the index file itself
            if file_path.name == 'index.html':
                continue
                
            # Extract title from HTML
            title = self._extract_title(file_path)
            
            # Generate a description based on the filename
            description = self._generate_description(file_path.stem)
            
            pages.append({
                'filename': file_path.name,
                'title': title or file_path.stem.replace('-', ' ').title(),
                'description': description
            })
            
        return pages
    
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
    
    def _generate_description(self, filename_stem: str) -> str:
        """
        Generate a description based on the filename.
        
        Args:
            filename_stem: The filename without extension
            
        Returns:
            Description string
            
        Raises:
            ValueError: If no description is defined for the filename
        """
        # Map common component names to descriptions
        descriptions = {
            'iag': 'IBM Application Gateway configuration parameters and settings',
            'verify-directory-server': 'IBM Security Verify Directory Server configuration parameters and settings',
            'verify-directory-proxy': 'IBM Security Verify Directory Proxy configuration parameters and settings',
            'verify-directory-seed': 'IBM Security Verify Directory Seed configuration parameters and settings',
            'verify-directory-virtualdir': 'IBM Security Verify Directory Virtual Directory configuration parameters and settings',
            'verify-directory-webadmin': 'IBM Security Verify Directory Web Administration Tool configuration parameters and settings',
            'verify-access': 'IBM Security Verify Access configuration parameters and settings',
            'verify-gateway': 'IBM Security Verify Gateway configuration parameters and settings',
            'example-showcase': 'Comprehensive example demonstrating all JSON Schema features and documentation capabilities',
        }
        
        if filename_stem not in descriptions:
            raise ValueError(
                f"No description defined for '{filename_stem}'. "
                f"Please add a description in the _generate_description() method of generate_index.py"
            )
        
        return descriptions[filename_stem]
    
    def generate_html(self) -> str:
        """Generate the complete HTML index page."""
        pages = self.scan_pages()
        
        html = self._generate_header()
        html += self._generate_body_start()
        html += self._generate_page_list(pages)
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
        
        .page-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
            gap: 1.5rem;
            margin-top: 2rem;
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
        }}
    </style>
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
    
    def _generate_page_list(self, pages: List[Dict[str, Any]]) -> str:
        """Generate the list of documentation pages."""
        if not pages:
            return '''
        <div class="empty-state">
            <div class="empty-state-icon">📭</div>
            <p>No configuration documentation pages found in this directory.</p>
        </div>
'''
        
        html = '        <div class="page-grid">\n'
        
        for page in pages:
            html += f'''
            <div class="page-card">
                <a href="{self._escape_html(page['filename'])}" class="page-card-link">
                    <div class="page-card-header">
                        <h3 class="page-card-title">{self._escape_html(page['title'])}</h3>
                    </div>
                    <div class="page-card-body">
                        <p class="page-card-description">{self._escape_html(page['description'])}</p>
                    </div>
                </a>
            </div>
'''
        
        html += '        </div>\n'
        return html
    
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
