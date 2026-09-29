import socket
import smtplib

from django.core.mail.backends.smtp import EmailBackend


class _RelaySMTP(smtplib.SMTP):
    """Sale por IPv4 y se presenta como inicialegal.cl.

    Google Workspace solo tiene autorizada la IPv4 del servidor. Si la
    conexión sale por IPv6, el relay la rechaza.
    """

    def __init__(self, host="", port=0, local_hostname=None, **kwargs):
        super().__init__(local_hostname="inicialegal.cl", **kwargs)
        if host:
            self.connect(host, port)

    def connect(self, host="localhost", port=0, source_address=None):
        port = port or 587
        ipv4 = socket.getaddrinfo(host, port, socket.AF_INET, socket.SOCK_STREAM)[0][4][0]
        result = super().connect(ipv4, port, source_address)
        self._host = host
        return result


class GoogleRelayBackend(EmailBackend):
    @property
    def connection_class(self):
        return _RelaySMTP
