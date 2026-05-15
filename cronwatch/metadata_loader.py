"""Load job metadata annotations from the cronwatch config dict."""

from __future__ import annotations

from typing import Any, Dict

from cronwatch.job_metadata import JobMetadataStore


def load_metadata_from_config(config: Dict[str, Any]) -> JobMetadataStore:
    """Populate a JobMetadataStore from the parsed config.

    Expected config shape (under each job entry)::

        jobs:
          - name: backup
            schedule: "0 2 * * *"
            metadata:
              owner: ops-team
              env: production

    Args:
        config: The raw config dict (as returned by ``load_config`` helpers).

    Returns:
        A populated :class:`JobMetadataStore`.
    """
    store = JobMetadataStore()
    jobs = config.get("jobs", [])
    for job in jobs:
        name = job.get("name")
        if not name:
            continue
        metadata = job.get("metadata", {})
        if not isinstance(metadata, dict):
            continue
        for key, value in metadata.items():
            store.annotate(name, key, value)
    return store
