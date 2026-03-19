##############################################################################
# IBM Confidential
# PID 5724-J39
# 
# Copyright IBM Corp. 2023
##############################################################################

##############################################################################
# Definitions

# Work out the list of source/object files which will be built.
YAML_SRCS = $(shell ls *.yaml 2>/dev/null)

# Specify a target html file.
OUTPUTFILE = verify-directory-proxy.html

##############################################################################
# Targets

# The files which should be 'published'
TO_PUBLISH = \
	verify-directory-server.html \
	verify-directory-proxy.html \
	verify-directory-seed.html \
	verify-directory-webadmin.html \
	verify-directory-virtualdir.html \
	schema_doc.css \
	schema_doc.min.js

PUBLISH_DIR = $(top_src_dir)/../export/docs
ZIP_FILE    = $(top_src_dir)/../export/yaml_docs.zip

# Default target
.PHONY: all
all: $(OUTPUTFILE)

$(OUTPUTFILE): $(YAML_SRCS)
	generate-schema-doc --config examples_as_yaml=true \
                --config with_footer=false .
	mkdir -p $(PUBLISH_DIR)
	cp $(TO_PUBLISH) $(PUBLISH_DIR)/
	sed "s|--date--|`date`|g" index.html.template > $(PUBLISH_DIR)/index.html
	cd $(PUBLISH_DIR) && zip -r $(ZIP_FILE) *

# Target to clean the directory.
.PHONY: clean 
clean:
	rm -f $(OUTPUTFILE) *.html *.css *.js
	rm -rf $(PUBLISH_DIR)

# Include our top level project mk file.
include ../../project.mk

