# IBM Verify On-Premises Configuration Documentation Generator

> [!NOTE]
> **For IBM Verify Developers Only**
>
> The contents of this repository are only applicable to IBM Verify developers. This repository is used to generate public documentation which will be made available at: https://ibm-verify.github.io/verify-onprem-deployment-docs/

IBM Confidential
PID 5725-X36
Copyright IBM Corp. 2026

## Table of Contents

- [Overview](#overview)
- [Adding New Documentation](#adding-new-documentation)
  - [Step 1: Add Schema Files](#step-1-add-schema-files)
  - [Step 2: Update Component Description](#step-2-update-component-description)
  - [Step 3: Generate Documentation](#step-3-generate-documentation)
  - [Requirements](#requirements)
- [Updating Existing Documentation](#updating-existing-documentation)
  - [Step 1: Update Schema Files](#step-1-update-schema-files)
  - [Step 2: Test Documentation Generation Locally](#step-2-test-documentation-generation-locally)
  - [Step 3: Create a Pull Request](#step-3-create-a-pull-request)
  - [Step 4: Post-Merge Actions](#step-4-post-merge-actions)
  - [Common Update Scenarios](#common-update-scenarios)
- [Key Features](#key-features)
- [Components](#components)
  - [1. Documentation Regeneration Script](#1-documentation-regeneration-script-regenerate_docspy)
  - [2. Schema Documentation Generator](#2-schema-documentation-generator-generate_schema_docspy)
  - [3. OpenAPI to JSON Schema Converter](#3-openapi-to-json-schema-converter-openapi_to_jsonschemepy)
  - [4. Index Page Generator](#4-index-page-generator-generate_indexpy)
- [Installation](#installation)
  - [Prerequisites](#prerequisites)
  - [Install Dependencies](#install-dependencies)
- [Complete Workflow](#complete-workflow)
  - [Quick Start: Regenerate All Documentation](#quick-start-regenerate-all-documentation)
  - [Manual Workflow](#manual-workflow)
- [Schema Format Requirements](#schema-format-requirements)
  - [JSON Schema (Multiple Drafts Supported)](#json-schema-multiple-drafts-supported)
  - [External References](#external-references)
  - [Newer JSON Schema Features](#newer-json-schema-features-2019-09-and-2020-12)
  - [Special Value Prefixes](#special-value-prefixes)
- [Generated Documentation Structure](#generated-documentation-structure)
- [Styling and Design](#styling-and-design)
- [Browser Support](#browser-support)
- [Repository Structure](#repository-structure)
- [Troubleshooting](#troubleshooting)
- [Best Practices](#best-practices)
- [Advanced Usage](#advanced-usage)
- [Examples](#examples)
- [Contributing](#contributing)
- [License](#license)
- [Support](#support)

## Overview

This repository contains a comprehensive toolset for generating professional, single-page HTML documentation from JSON Schema and OpenAPI specifications. The generated documentation conforms to the IBM Carbon Design System and provides an intuitive interface for understanding complex configuration schemas.

## Adding New Documentation

To add documentation for a new component to this repository, follow these steps:

### Step 1: Add Schema Files

Add your JSON Schema or OpenAPI schema files to a new sub-directory within the [`schemas`](schemas) directory:

```bash
# Create a new directory for your component
mkdir schemas/your-component-name

# Add your schema files
cp your-schema-files.yaml schemas/your-component-name/
```

**Schema File Naming:**
- For a main schema file, name it to match the component (e.g., `your-component-name.yaml`)
- Alternatively, name it `openapi.yaml` if it's an OpenAPI specification
- Component schemas referenced by the main schema can have descriptive names (e.g., `server.yaml`, `advanced.yaml`)

### Step 2: Update Component Description

Update the [`_generate_description`](generate_index.py#L107-L139) function in [`generate_index.py`](generate_index.py) to include a description for your component:

1. Open [`generate_index.py`](generate_index.py)
2. Locate the `_generate_description` method (around line 107)
3. Add an entry to the `descriptions` dictionary with your component name and description

**Determining the Component Name:**

The component name is derived from the main schema filename (without the `.yaml` extension). For example:
- `schemas/iag/openapi.yaml` → component name is `iag` (uses parent directory name)
- `schemas/isvd/verify-directory-server.yaml` → component name is `verify-directory-server`
- `schemas/your-component/your-component.yaml` → component name is `your-component`

**Example:**

```python
descriptions = {
    'iag': 'IBM Application Gateway configuration parameters and settings',
    'verify-directory-server': 'IBM Security Verify Directory Server configuration parameters and settings',
    'your-component-name': 'Your Component description and configuration parameters',
}
```

### Step 3: Generate Documentation

The GitHub Actions workflow will automatically regenerate the documentation when you commit your changes. The generated HTML files will be published to GitHub Pages.

**Testing Locally:**

To test the documentation generation locally before committing:

```bash
# Regenerate all documentation
python3 regenerate_docs.py

# View the generated files in the pages/ directory
open pages/index.html
```

The [`regenerate_docs.py`](regenerate_docs.py) script will:
- Detect your new schema files
- Convert OpenAPI files to JSON Schema if needed
- Generate HTML documentation
- Update the index page
- Validate the output

### Requirements

- Schema files must be valid JSON Schema (Draft-04 through 2020-12) or OpenAPI 3.0 format
- Schema files should include proper `title` and `description` fields
- External references should use relative paths within the schemas directory
## Updating Existing Documentation

To update existing documentation in this repository, follow these steps:

### Step 1: Update Schema Files

Modify the appropriate schema files in the [`schemas`](schemas) directory to reflect the changes needed:

```bash
# Navigate to the component's schema directory
cd schemas/your-component-name

# Edit the relevant schema files
# For example: server.yaml, advanced.yaml, etc.
```

Make your changes to the schema files, ensuring that:
- The schema remains valid JSON Schema or OpenAPI format
- All `title` and `description` fields are updated as needed
- External references are still correct
- Validation constraints are appropriate

### Step 2: Test Documentation Generation Locally

Before creating a pull request, test that the documentation generates correctly:

```bash
# Regenerate all documentation
python3 regenerate_docs.py

# View the updated documentation
open pages/your-component-name.html
```

Verify that:
- The documentation renders correctly
- All changes are reflected in the output
- No errors or warnings are displayed
- External references resolve properly

### Step 3: Create a Pull Request

Once you've verified the changes locally:

1. Commit your schema file changes
2. Create a pull request with a clear description of the changes
3. **Important:** In the pull request comment, explicitly state whether the documentation should be regenerated after the PR is reviewed and merged

**Pull Request Comment Template:**

```
## Changes
[Describe the schema changes made]

## Documentation Regeneration
- [ ] Documentation should be regenerated after merge
- [ ] Documentation does NOT need regeneration (schema changes only affect internal structure)

## Testing
- [ ] Tested locally with `python3 regenerate_docs.py`
- [ ] Verified generated HTML renders correctly
- [ ] Confirmed all external references resolve
```

### Step 4: Post-Merge Actions

After the pull request is reviewed and merged:

- If documentation regeneration was requested, the GitHub Actions workflow will automatically regenerate and publish the updated documentation
- If manual regeneration is needed, run `python3 regenerate_docs.py` and commit the updated HTML files

### Common Update Scenarios

**Adding a new property:**
- Add the property definition to the appropriate schema file
- Include proper `type`, `description`, and validation constraints
- Mark as `required` if applicable

**Modifying validation rules:**
- Update constraints like `minimum`, `maximum`, `pattern`, `enum`, etc.
- Update the description to reflect the new constraints

**Deprecating a property:**
- Add a deprecation notice to the property's `description`
- Consider using `deprecated: true` if using OpenAPI format

**Updating descriptions:**
- Modify the `description` field in the schema
- Use markdown formatting for better readability


## Key Features

- **IBM Carbon Design System** - Professional styling using IBM's design system with IBM Plex fonts
- **Multiple JSON Schema Versions** - Support for Draft-04, Draft-06, Draft-07, Draft 2019-09, and Draft 2020-12
- **Modern Schema Features** - Full support for newer keywords like `$defs`, `prefixItems`, `dependentSchemas`, `const`, and more
- **OpenAPI 3.0 Support** - Convert and document OpenAPI specifications
- **Schema Reference Resolution** - Automatically resolves `$ref` and `$dynamicRef` references (both internal and external)
- **Collapsible Sections** - Expandable/collapsible sections for easy navigation of large schemas
- **Validation Constraints** - Displays all validation rules (min/max, patterns, formats, etc.)
- **Examples Support** - Displays configuration examples in YAML format at both top-level and inline
- **Markdown Support** - Renders markdown in descriptions with proper formatting
- **Responsive Design** - Works seamlessly on desktop and mobile devices
- **Index Generation** - Creates a landing page for multiple documentation files

## Components

### 1. Documentation Regeneration Script (`regenerate_docs.py`)

**NEW:** Automated script to regenerate all HTML documentation pages from schema files in one command.

**Features:**
- Automatically scans the schemas directory for all main schema files
- Detects OpenAPI and JSON Schema files
- Converts OpenAPI files to JSON Schema (with automatic cleanup)
- Generates HTML documentation for each main schema
- Creates the index page
- Validates that no unknown HTML files exist in the pages directory
- Fails with clear error messages if issues are detected

**Usage:**
```bash
python3 regenerate_docs.py [options]
```

**Options:**
- `-s, --schemas-dir DIR` - Directory containing schema files (default: schemas)
- `-p, --pages-dir DIR` - Directory for output HTML files (default: pages)
- `-h, --help` - Show help message
- `--version` - Show version number

**Examples:**
```bash
# Regenerate all documentation with defaults
python3 regenerate_docs.py

# Specify custom directories
python3 regenerate_docs.py --schemas-dir schemas --pages-dir pages

# Short form
python3 regenerate_docs.py -s schemas -p pages
```

**What it does:**
1. Scans the schemas directory for main schema files (OpenAPI and JSON Schema)
2. Converts OpenAPI files to JSON Schema format (temporary files are cleaned up automatically)
3. Generates HTML documentation for each main schema file
4. Generates an index page listing all documentation
5. Detects and fails if unknown HTML files are found in the pages directory

**Main Schema Detection:**
The script identifies "main" schema files that should generate documentation:
- Files in the root schemas directory
- Files named `openapi.yaml` (converted to use parent directory name)
- Files matching their parent directory name (e.g., `verify-directory-server.yaml` in `isvd/`)
- Known main schemas like `example-showcase.yaml`

Component schema files (like `advanced.yaml`, `server.yaml`, etc.) are not processed individually as they are referenced by main schemas.

### 2. Schema Documentation Generator (`generate_schema_docs.py`)

Generates comprehensive HTML documentation from JSON Schema files supporting multiple draft versions.

**Supported JSON Schema Versions:**
- JSON Schema Draft-04 (http://json-schema.org/draft-04/schema#)
- JSON Schema Draft-06 (http://json-schema.org/draft-06/schema#)
- JSON Schema Draft-07 (http://json-schema.org/draft-07/schema#)
- JSON Schema Draft 2019-09 (https://json-schema.org/draft/2019-09/schema)
- JSON Schema Draft 2020-12 (https://json-schema.org/draft/2020-12/schema)

**Features:**
- Hierarchical property display with proper nesting
- Support for both `definitions` (older drafts) and `$defs` (2019-09+)
- `$ref` and `$dynamicRef` reference resolution (internal and external)
- Type information and comprehensive validation constraints
- `const` keyword support for constant values
- `prefixItems` for tuple validation (2020-12)
- `dependentSchemas` and `dependentRequired` (2019-09+)
- `unevaluatedProperties` and `unevaluatedItems` (2019-09+)
- Enhanced validation display (minLength, maxLength, pattern, format, minContains, maxContains, etc.)
- Required/optional indicators
- Inline examples in YAML format
- Markdown description rendering

**Usage:**
```bash
python3 generate_schema_docs.py <input_schema.yaml> <output.html>
```

**Example:**
```bash
python3 generate_schema_docs.py schemas/isvd/verify-directory-server.yaml schemas/isvd/verify-directory-server.html
```

### 3. OpenAPI to JSON Schema Converter (`openapi_to_jsonschema.py`)

Converts OpenAPI 3.0 specifications to JSON Schema Draft 07 format for documentation generation.

**Features:**
- Converts `components/schemas` to `definitions`
- Resolves and inlines external file references
- Handles circular reference detection
- Preserves descriptions, examples, and constraints
- Extracts metadata from OpenAPI info section

**Usage:**
```bash
python3 openapi_to_jsonschema.py <input_openapi.yaml> [output_jsonschema.yaml]
```

**Example:**
```bash
python3 openapi_to_jsonschema.py schemas/iag/openapi.yaml schemas/iag/openapi.jsonschema.yaml
```

### 4. Index Page Generator (`generate_index.py`)

Creates a landing page that lists all available configuration documentation files.

**Features:**
- Scans directory for HTML documentation files
- Extracts titles from HTML files
- Generates descriptions based on filenames
- Creates a responsive card-based layout
- IBM Carbon Design System styling

**Usage:**
```bash
python3 generate_index.py <pages_directory> [output_file]
```

**Example:**
```bash
python3 generate_index.py pages
```

## Installation

### Prerequisites

- Python 3.7 or higher
- PyYAML library
- Markdown library (optional, for enhanced markdown support)

### Install Dependencies

```bash
pip install pyyaml markdown
```

**Note:** The `markdown` library is optional but recommended for full markdown support (headings, bold, italic, lists, etc.). Without it, the generator will use basic markdown processing.

## Complete Workflow

### Quick Start: Regenerate All Documentation

**Recommended:** Use the automated regeneration script to rebuild all documentation:

```bash
python3 regenerate_docs.py
```

This single command will:
- Find all main schema files
- Convert OpenAPI files to JSON Schema
- Generate HTML documentation for each schema
- Create the index page
- Validate the output

### Manual Workflow

#### For JSON Schema Files

If you want to generate documentation for a single JSON Schema file:

```bash
python3 generate_schema_docs.py input.yaml output.html
```

#### For OpenAPI 3.0 Files

If you have an OpenAPI 3.0 specification:

**Step 1:** Convert to JSON Schema
```bash
python3 openapi_to_jsonschema.py openapi.yaml schema.yaml
```

**Step 2:** Generate documentation
```bash
python3 generate_schema_docs.py schema.yaml documentation.html
```

#### Generate Index Page

After generating multiple documentation files:

```bash
python3 generate_index.py pages
```

**Note:** When adding schemas for a new product, update the `descriptions` dictionary in `generate_index.py` (around line 102) to include a description for the new product. This ensures the index page displays an appropriate description for the new documentation.

Example:
```python
descriptions = {
    'iag': 'IBM Application Gateway configuration parameters and settings',
    'verify-directory-server': 'IBM Security Verify Directory Server configuration parameters and settings',
    'your-new-product': 'Your New Product configuration parameters and settings',
}
```

## Schema Format Requirements

### JSON Schema (Multiple Drafts Supported)

The documentation generator supports JSON Schema from Draft-04 through Draft 2020-12:

**Example (Draft-07):**
```yaml
---
"$schema": http://json-schema.org/draft-07/schema#
"$ref": "#/definitions/RootObject"
title: "My Schema Title"
description: "Schema description with markdown support"

examples:
  - property1: "value1"
    property2: "value2"

definitions:
  RootObject:
    type: object
    properties:
      property1:
        type: string
        description: "Property description"
      property2:
        "$ref": "external-file.yaml#/definitions/ExternalType"
```

**Example (Draft 2020-12 with newer features):**
```yaml
---
$schema: https://json-schema.org/draft/2020-12/schema
title: "Modern Schema Example"
description: "Schema using newer JSON Schema features"

type: object
properties:
  version:
    type: string
    const: "2.0"
  coordinates:
    type: array
    prefixItems:
      - type: number
      - type: number
      - type: number
  settings:
    $ref: "#/$defs/settings"

$defs:
  settings:
    type: object
    properties:
      mode:
        type: string
        enum: [dev, prod]
    unevaluatedProperties: false
```

### External References

The generator supports external file references for all schema versions:

**Older drafts (Draft-04 through Draft-07):**
- `external-file.yaml#/definitions/TypeName` - Reference to a definition in another file
- `#/definitions/TypeName` - Internal reference within the same file

**Newer drafts (2019-09 and 2020-12):**
- `external-file.yaml#/$defs/TypeName` - Reference to a definition in another file
- `#/$defs/TypeName` - Internal reference within the same file
- `#/$dynamicRef` - Dynamic reference (2020-12)

The generator automatically detects and handles both `definitions` and `$defs` keywords.

### Newer JSON Schema Features (2019-09 and 2020-12)

The generator fully supports modern JSON Schema features:

**Vocabulary Changes:**
- `$defs` - Replaces `definitions` for defining reusable schemas
- `$dynamicRef` and `$dynamicAnchor` - Dynamic reference resolution

**Validation Keywords:**
- `const` - Specifies a constant value that must match exactly
- `dependentSchemas` - Apply additional schemas when certain properties are present
- `dependentRequired` - Make properties required based on other properties
- `unevaluatedProperties` - Control whether additional properties are allowed
- `unevaluatedItems` - Control whether additional array items are allowed
- `minContains` and `maxContains` - Validate number of items matching a schema
- `prefixItems` - Tuple validation with position-specific schemas

**Content Keywords:**
- `contentMediaType` - Specify media type of string content
- `contentEncoding` - Specify encoding of string content
- `contentSchema` - Schema for decoded content

All these features are automatically detected and properly displayed in the generated documentation.

### Special Value Prefixes

The schema documentation supports special value prefixes:

- `B64:` - Base-64 encoded text
- `$` - Environment variable
- `@` - Load from local file
- `secret:{name}/{field}` - Kubernetes secret
- `configmap:{name}/{field}` - Kubernetes ConfigMap

## Generated Documentation Structure

The generated HTML documentation includes:

### 1. Header Section
- Schema title
- Description with markdown rendering
- Usage instructions (collapsible)

### 2. Configuration Section
- All schema properties organized hierarchically
- Type information for each property
- Required/optional indicators
- Descriptions with markdown support
- Nested properties with proper indentation
- Inline examples in YAML format

### 3. Examples Section (if present)
- Complete YAML-formatted configuration examples
- Syntax highlighting
- Collapsible for easy navigation

### 4. Footer
- Copyright information
- Generation timestamp

## Styling and Design

The documentation uses IBM Carbon Design System with:

- **Typography:** IBM Plex Sans font family
- **Colors:** Carbon color palette with accessible contrasts
- **Layout:** Responsive grid system
- **Spacing:** Professional spacing and typography
- **Interactions:** Smooth animations and hover effects

## Browser Support

The generated documentation works in:

- Chrome/Edge (latest)
- Firefox (latest)
- Safari (latest)
- Mobile browsers

## Repository Structure

```
.
├── generate_schema_docs.py          # Main documentation generator
├── openapi_to_jsonschema.py         # OpenAPI to JSON Schema converter
├── generate_index.py                # Index page generator
├── README.md                         # This file
├── pages/                            # Generated HTML documentation pages
└── schemas/                          # Schema files (organized by component)
```

## Troubleshooting

### Schema Not Found Error

If you get "Schema file not found", ensure:
- The file path is correct
- The file exists and is readable
- You're running the command from the correct directory

### Empty Sections in Documentation

If sections appear empty:
- Check that external references are resolved correctly
- Verify the schema structure matches a supported JSON Schema version (Draft-04 through 2020-12)
- Ensure referenced files exist in the correct locations
- For newer drafts, verify you're using `$defs` instead of `definitions` where appropriate

### OpenAPI Conversion Issues

If OpenAPI conversion fails:
- Verify the OpenAPI spec is version 3.0
- Check that all external files are accessible
- Look for circular references in the schema

### Import Errors

If you encounter import errors:
```bash
pip install pyyaml markdown
```

## Best Practices

### Schema Organization

- Keep related schemas in the same directory
- Use clear, descriptive file names
- Document external references in comments
- Maintain consistent naming conventions

### Documentation Quality

- Write clear, concise descriptions
- Include examples for complex configurations
- Use markdown formatting in descriptions
- Specify constraints (min, max, pattern, etc.)
- Add default values where applicable

### Maintenance

- Regenerate documentation when schemas change
- Version control both schemas and generated docs
- Review generated HTML before publishing
- Test with different browsers

## Advanced Usage

### Batch Processing

Process multiple schemas at once:

```bash
#!/bin/bash
for schema in schemas/*.yaml; do
    output="${schema%.yaml}.html"
    python3 generate_schema_docs.py "$schema" "$output"
done
```

### CI/CD Integration

Add to your build pipeline:

```yaml
# Example GitHub Actions workflow
- name: Generate Schema Documentation
  run: |
    python3 generate_schema_docs.py schema.yaml docs/schema.html
    
- name: Generate Index Page
  run: |
    python3 generate_index.py docs
    
- name: Deploy Documentation
  run: |
    # Deploy docs/ directory to your hosting
```

### Custom Styling

The generated HTML uses inline CSS. To customize:

1. Generate the HTML
2. Open in a text editor
3. Modify the `<style>` section
4. Save and reload in browser

## Examples

### Example 1: Simple Configuration Schema

```yaml
---
"$schema": http://json-schema.org/draft-07/schema#
title: "Server Configuration"
type: object
properties:
  host:
    type: string
    description: "Server hostname"
    default: "localhost"
  port:
    type: integer
    description: "Server port"
    minimum: 1
    maximum: 65535
    default: 8080
required:
  - host
  - port
```

### Example 2: Schema with External References

```yaml
---
"$schema": http://json-schema.org/draft-07/schema#
"$ref": "#/definitions/Config"
definitions:
  Config:
    type: object
    properties:
      server:
        "$ref": "server.yaml#/definitions/Server"
      database:
        "$ref": "database.yaml#/definitions/Database"
```


## Contributing

When contributing to this project:

1. Maintain the IBM Carbon Design System styling
2. Ensure all generated files include the copyright header
3. Test with both simple and complex schemas
4. Update documentation for new features
5. Follow Python PEP 8 style guidelines

## License

IBM Confidential - See copyright header in source files.

## Support

For issues or questions, please contact your IBM representative.