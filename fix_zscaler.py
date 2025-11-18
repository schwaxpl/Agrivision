#!/usr/bin/env python3
"""
Script d'aide pour résoudre les problèmes SSL avec ZScaler.
Exécutez ce script avant d'utiliser main.py si vous avez des problèmes de certificats.
"""

import os
import ssl
import warnings
import urllib3

def configure_ssl_for_zscaler():
    """Configure l'environnement pour contourner les problèmes SSL de ZScaler."""
    
    print("🔧 Configuration pour ZScaler/Proxies d'entreprise...")
    
    # Variables d'environnement pour désactiver la vérification SSL
    ssl_env_vars = {
        "PYTHONHTTPSVERIFY": "0",
        "CURL_CA_BUNDLE": "",
        "REQUESTS_CA_BUNDLE": "",
        "SSL_VERIFY": "false",
    }
    
    for var, value in ssl_env_vars.items():
        os.environ[var] = value
        print(f"✅ {var} = {value}")
    
    # Configuration SSL globale pour Python
    ssl._create_default_https_context = ssl._create_unverified_context
    print("✅ Contexte SSL non vérifié configuré")
    
    # Désactivation des warnings urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    print("✅ Warnings SSL désactivés")
    
    # Désactivation des warnings génériques
    warnings.filterwarnings("ignore", category=UserWarning, module="urllib3")
    warnings.filterwarnings("ignore", message="Unverified HTTPS request")
    print("✅ Warnings urllib3 désactivés")
    
    print("\n🎉 Configuration SSL terminée !")
    print("💡 Vous pouvez maintenant exécuter votre application normalement.")
    print("💡 Si vous avez encore des problèmes, contactez votre administrateur IT.")

if __name__ == "__main__":
    configure_ssl_for_zscaler()