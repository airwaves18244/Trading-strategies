"""qbt.api — FastAPI app, job registry, request/response schemas, fake runner.

Owned by WS-E. See docs/architecture.md "Web/API spec". Other workstreams
(qbt.data, qbt.engine, qbt.strategies) may still be under construction; this
package must import cleanly with none of them wired up (see qbt/api/fake.py).
"""
from __future__ import annotations
