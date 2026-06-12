# -*- coding: utf-8 -*-
"""API request/response Pydantic models relocated out of ``backend.main``.

Backend-modularization task 4.1. These are the request/response models that were
defined inline in ``main.py``, grouped by domain (auth, users, content, quests,
progress, admin, live).

IMPORTANT — why this package is named ``apischemas`` and not ``schemas``:
the repository already has a flat module ``backend/schemas.py`` whose models
**collide by name but differ in field shape** with several of main.py's inline
models (e.g. ``schemas.RankOut`` is ``{title, min_xp}`` while main.py's inline
``RankOut`` is ``{level, name, xp}``; likewise ``UserOut``). A Python package
``backend/schemas/`` cannot coexist with ``backend/schemas.py``, and merging the
two model sets into one namespace would silently change response shapes. To stay
strictly behavior-preserving, the relocated inline models live in this separate
package and are imported into ``backend.main`` by their original bare names, so
``main``-qualified references resolve to these models while ``schemas.<name>``
references continue to resolve to the distinct models in ``backend/schemas.py``.
"""
