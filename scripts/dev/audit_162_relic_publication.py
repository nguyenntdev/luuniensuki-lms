#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Backward-compatibility shim for scripts.dev.audit_162_publication."""
from scripts.dev.audit_162_publication import (
    DEFAULT_OUTPUT_PATH,
    KNOWN_MISSING_HAN_NOM_IDS,
    PRIMARY_SOURCE_TYPES,
    REPO_ROOT,
    URN_SPECS,
    VERIFIED_STATUS_TIERS,
    audit_all_motifs,
    audit_database,
    audit_single_motif,
    main,
    print_status_table,
    resolve_rubbing_asset,
    validate_manifest_file,
    validate_publication_safety,
)

if __name__ == "__main__":
    import sys
    sys.exit(main())
