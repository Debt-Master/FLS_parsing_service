"""Convert FLS parse_statement result to unified parsed_document format."""

from __future__ import annotations
from decimal import Decimal
from typing import Any


def _public_street_name(value: str | None) -> str | None:
    if not value:
        return value
    if value.startswith("б-р "):
        return f"{value[4:]} бульвар"
    if value.startswith("пр-кт "):
        return f"{value[6:]} пр-кт"
    return value


def _public_address_full(address: dict[str, Any], street: str | None) -> str | None:
    parts = []
    if street:
        parts.append(street)
    if address.get("house"):
        parts.append(f"дом № {address['house']}")
    if address.get("building"):
        parts.append(f"корп. {address['building']}")
    if address.get("structure"):
        parts.append(f"строение {address['structure']}")
    if address.get("apartment"):
        parts.append(f"кв. {address['apartment']}")
    return ", ".join(parts) if parts else None


def _split_name(full_name: str | None) -> dict[str, str | None]:
    if not full_name:
        return {"last_name": None, "first_name": None, "middle_name": None}
    parts = full_name.strip().split()
    return {
        "last_name": parts[0] if len(parts) > 0 else None,
        "first_name": parts[1] if len(parts) > 1 else None,
        "middle_name": parts[2] if len(parts) > 2 else None,
    }


def _serialize_decimal(v: Any) -> Any:
    """Convert Decimal to float for JSON serialization."""
    if isinstance(v, Decimal):
        return float(v)
    if isinstance(v, dict):
        return {k: _serialize_decimal(val) for k, val in v.items()}
    if isinstance(v, list):
        return [_serialize_decimal(item) for item in v]
    return v


def normalize(result: dict[str, Any], source_filename: str = "input.rtf") -> dict[str, Any]:
    """Convert FLS result dict to unified parsed_document format."""
    address = result.get("address", {}) or {}
    public_street = _public_street_name(address.get("street"))
    public_full = (
        _public_address_full(address, public_street)
        or address.get("full")
        or address.get("raw")
    )
    persons = []
    if result.get("account_holder_name"):
        persons.append({
            "full_name": result["account_holder_name"],
            **_split_name(result["account_holder_name"]),
            "birthday_date": None,
            "ownership_share": None,
            "identity": None,
            "departure": None,
        })

    return _serialize_decimal({
        "document_type": "fls",
        "source_filename": result.get("source_filename", source_filename),
        "account_holder_name": result.get("account_holder_name"),
        "address_raw": result.get("address_raw"),
        "address": {
            # Backend parses ``address.raw`` before consulting structured fields,
            # so it must carry the same canonical value as ``full``.
            "raw": public_full,
            "full": public_full,
            "street": public_street,
            "house": address.get("house"),
            "building": address.get("building"),
            "structure": address.get("structure"),
            "apartment": address.get("apartment"),
        },
        "persons": persons,
        "management_company": None,
        "property_type": None,
        "benefits": None,
        "billing": {
            "charges": result.get("charges"),
            "year_totals": result.get("year_totals"),
            "grand_total": result.get("grand_total"),
        },
        "validations": result.get("validations"),
        "metadata": {
            "account_holder_name": result.get("account_holder_name"),
            "parsing": result.get("parsing"),
        },
    })
