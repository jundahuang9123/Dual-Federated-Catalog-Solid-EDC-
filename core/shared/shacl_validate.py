"""SHACL validation helpers.

Reuse intake target:
backend/shacl_validation.py from tmdt-buw/semantic-data-catalog.
"""

from core.interfaces.validation import ValidationResult


def validate_rdf(_rdf_payload: str, *, _shape_path: str | None = None) -> ValidationResult:
    raise NotImplementedError("Reuse intake has not imported the SHACL validator yet")

