This directory contains the YAML documentation for the verify-directory-server and verify-directory-proxy contains.  The documentation is written in [JSON Schema](https://json-schema.org/) format.  The HTML documentation is then generated using the [JSON Schema for Humans](https://pypi.org/project/json-schema-for-humans/) python module.

The main YAML files contained within this directory are verify-directory-server.yaml and verify-directory-proxy.yaml.  The rest of the YAML files contain common definitions which are referenced by both of the main YAML files.

The following files are required to read the documentation:

* verify-directory-server.html
* verify-directory-proxy.html
* schema_doc.css
* schema_doc.min.js

Each of these files will be exported to the export/docs directory at the root of the build tree.