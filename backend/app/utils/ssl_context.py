"""
全局 SSL 上下文：使用 certifi CA bundle 替代 Windows 证书存储，
解决 Python 3.8 + OpenSSL 3.6.2 在 Windows 上的 SSL 兼容问题。
"""
import ssl
import certifi

_SSL_CONTEXT = ssl.create_default_context(cafile=certifi.where())


def get_ssl_context() -> ssl.SSLContext:
    """返回使用 certifi CA bundle 的 SSL 上下文。"""
    return _SSL_CONTEXT
