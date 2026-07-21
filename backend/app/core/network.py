from __future__ import annotations

from ipaddress import ip_address, ip_network
from typing import Iterable

from starlette.requests import Request


def _headers_to_mapping(
    headers: Iterable[tuple[bytes, bytes]],
) -> dict[str, str]:
    return {
        key.decode("latin-1").lower(): value.decode("latin-1") for key, value in headers
    }


def _is_trusted_proxy(
    peer_host: str | None,
    trusted_proxy_entries: tuple[str, ...],
) -> bool:
    if not peer_host or not trusted_proxy_entries:
        return False

    try:
        peer_ip = ip_address(peer_host)
    except ValueError:
        return peer_host in trusted_proxy_entries

    for entry in trusted_proxy_entries:
        try:
            if peer_ip in ip_network(entry, strict=False):
                return True
        except ValueError:
            if peer_host == entry:
                return True

    return False


def _validated_ip(value: str | None) -> str | None:
    if not value:
        return None

    candidate = value.strip()

    try:
        return str(ip_address(candidate))
    except ValueError:
        return None


def resolve_client_ip_from_scope(
    *,
    headers: Iterable[tuple[bytes, bytes]],
    client: tuple[str, int] | None,
    trusted_proxy_entries: tuple[str, ...] = (),
) -> str | None:
    peer_host = client[0] if client is not None else None

    if not _is_trusted_proxy(
        peer_host,
        trusted_proxy_entries,
    ):
        return peer_host

    header_map = _headers_to_mapping(headers)

    forwarded_for = header_map.get("x-forwarded-for")
    if forwarded_for:
        forwarded_ip = _validated_ip(forwarded_for.split(",", 1)[0])
        if forwarded_ip is not None:
            return forwarded_ip

    real_ip = _validated_ip(header_map.get("x-real-ip"))
    if real_ip is not None:
        return real_ip

    return peer_host


def resolve_client_ip(
    request: Request,
    *,
    trusted_proxy_entries: tuple[str, ...] = (),
) -> str | None:
    return resolve_client_ip_from_scope(
        headers=request.scope.get("headers", ()),
        client=request.scope.get("client"),
        trusted_proxy_entries=trusted_proxy_entries,
    )
