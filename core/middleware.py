from django.http import JsonResponse
from rest_framework_simplejwt.authentication import JWTAuthentication
from core.models import UserSession

# Faqat session management endpointlari uchun tekshirish kerak emas
SKIP_PATHS = [
    '/api/login/',
    '/api/register/',
    '/api/token/',
    '/api/sessions/',
]

class SessionValidationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        
        # Skip paths
        for path in SKIP_PATHS:
            if request.path.startswith(path):
                return self.get_response(request)

        if auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
            try:
                jwt_auth = JWTAuthentication()
                jwt_auth.get_validated_token(token.encode())
                
                # Faqat active session bo\'lgan tokenlar uchun
                # UserSession mavjud bo\'lsa tekshiramiz
                session_exists = UserSession.objects.filter(token=token).exists()
                if session_exists:
                    active = UserSession.objects.filter(token=token, is_active=True).exists()
                    if not active:
                        return JsonResponse(
                            {'detail': 'Session tugatilgan. Qayta login qiling.', 'code': 'session_terminated'},
                            status=401
                        )
            except Exception:
                pass

        return self.get_response(request)
