"""Dataclasses for API endpoint and parameter definitions."""

from __future__ import annotations

from dataclasses import field, dataclass


@dataclass
class ParamDef:
    """Definition of a single endpoint parameter."""

    name: str
    param_type: str
    required: bool = False
    allowed_values: list[str] | None = None
    description: str = ''
    location: str = 'body'


@dataclass
class EndpointDef:
    """Definition of a single API endpoint."""

    path: str
    method: str
    summary: str = ''
    description: str = ''
    response_format: str = 'json'
    params: dict[str, ParamDef] = field(default_factory=dict)
    request_schema: str | None = None
    filters_schema: str | None = None
