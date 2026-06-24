from django.http import HttpResponse
from django.conf import settings


class SimpleCorsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.method == 'OPTIONS':
            response = HttpResponse()
        else:
            response = self.get_response(request)

        origin = request.headers.get('Origin', '')
        allowed_origins = getattr(settings, 'CORS_ALLOWED_ORIGINS', [])
        if '*' in allowed_origins:
            response['Access-Control-Allow-Origin'] = '*'
        elif origin and origin in allowed_origins:
            response['Access-Control-Allow-Origin'] = origin
            response['Vary'] = 'Origin'
        response['Access-Control-Allow-Methods'] = 'GET, POST, PATCH, DELETE, OPTIONS'
        response['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        return response
