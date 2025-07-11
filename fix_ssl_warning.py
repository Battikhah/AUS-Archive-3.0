"""
Fix for the LibreSSL warning in urllib3.

This suppresses the warning about LibreSSL not being fully supported in urllib3.
"""

import warnings
import urllib3

# Suppress the LibreSSL warning from urllib3
warnings.filterwarnings(
    'ignore',
    message='urllib3 v2 only supports OpenSSL 1.1.1+, currently the \'ssl\' module is compiled with',
    category=urllib3.exceptions.NotOpenSSLWarning
)
