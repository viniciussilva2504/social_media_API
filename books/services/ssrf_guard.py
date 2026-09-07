import ipaddress
import socket


def is_safe_host(hostname: str) -> bool:
    """Reject hosts that resolve to a private/internal/reserved IP.

    Basic SSRF guard shared by every "fetch this URL server-side" feature
    (cover-by-URL, book-metadata-by-URL): without it, a URL field would let
    anyone make the server issue requests to localhost, the Docker/host
    network, or cloud metadata endpoints (e.g. 169.254.169.254).
    """
    try:
        infos = socket.getaddrinfo(hostname, None)
    except socket.gaierror:
        return False

    if not infos:
        return False

    for info in infos:
        ip = ipaddress.ip_address(info[4][0])
        if (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_multicast
            or ip.is_reserved
            or ip.is_unspecified
        ):
            return False
    return True
