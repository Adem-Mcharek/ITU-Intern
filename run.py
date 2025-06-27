#!/usr/bin/env python3
"""
ITU WebTV Processing System
Copyright (c) 2025 Adem Mcharek
Licensed under the MIT License - see LICENSE file for details
"""
import os
import logging
from app import create_app

# Enable detailed logging
logging.basicConfig(level=logging.DEBUG)

app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    debug = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'
    app.run(host='0.0.0.0', port=port, debug=debug, use_reloader=False) 