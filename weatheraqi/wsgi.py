"""
WSGI config for weatheraqi project.
"""

import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'weatheraqi.settings')
application = get_wsgi_application()
