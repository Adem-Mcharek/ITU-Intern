#!/usr/bin/env python3
"""
ITU WebTV Processing System
Copyright (c) 2025 Adem Mcharek
Licensed under the MIT License - see LICENSE file for details
"""
import os
import logging
from app import create_app

# Configure logging based on VERBOSE environment variable
VERBOSE = os.environ.get('VERBOSE', 'false').lower() == 'true'

if VERBOSE:
    # Verbose mode: show all debug logs
    logging.basicConfig(level=logging.DEBUG)
else:
    # Normal mode: only show warnings and errors
    logging.basicConfig(level=logging.WARNING)
    
    # Suppress debug/info logs from noisy libraries
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('openai').setLevel(logging.WARNING)
    logging.getLogger('httpcore').setLevel(logging.WARNING)
    logging.getLogger('httpx').setLevel(logging.WARNING)
    logging.getLogger('werkzeug').setLevel(logging.WARNING)

app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    debug = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'
    app.run(host='0.0.0.0', port=port, debug=debug, use_reloader=False) 