# -*- coding: utf-8 -*-
"""APIRouter modules for the Luuniensuki backend.

Backend-modularization task 5: endpoints are extracted from ``backend.main``
into one ``APIRouter`` per domain and registered via ``app.include_router(...)``
in ``backend.app.create_app()``. Router modules import their dependencies from
``backend.deps``, ``backend.apischemas``, ``backend.domain``, ``backend.models``,
``backend.services``, ``backend.schemas``, ``backend.security`` and
``backend.config`` — never from ``backend.main`` or ``backend.app`` — so the
import graph stays acyclic (``main`` -> ``app`` -> ``routers`` -> shared modules).
"""
