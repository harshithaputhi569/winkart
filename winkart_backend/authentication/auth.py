import jwt
from datetime import datetime, timedelta, timezone
from django.conf import settings
from rest_framework import authentication
from rest_framework.exceptions import AuthenticationFailed
from bson import ObjectId
from winkart_backend.database import users_col

# Token config
ACCESS_TOKEN_LIFETIME = timedelta(hours=1)
REFRESH_TOKEN_LIFETIME = timedelta(days=7)

def generate_tokens(user_id, role):
    """Generates an access and a refresh token for a user."""
    now = datetime.now(timezone.utc)
    
    access_payload = {
        'user_id': str(user_id),
        'role': role,
        'exp': now + ACCESS_TOKEN_LIFETIME,
        'type': 'access'
    }
    access_token = jwt.encode(access_payload, settings.SECRET_KEY, algorithm='HS256')
    
    refresh_payload = {
        'user_id': str(user_id),
        'role': role,
        'exp': now + REFRESH_TOKEN_LIFETIME,
        'type': 'refresh'
    }
    refresh_token = jwt.encode(refresh_payload, settings.SECRET_KEY, algorithm='HS256')
    
    return {
        'access': access_token,
        'refresh': refresh_token
    }

def decode_token(token, token_type='access'):
    """Decodes a JWT token and returns payload if valid."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
        if payload.get('type') != token_type:
            raise AuthenticationFailed("Invalid token type.")
        return payload
    except jwt.ExpiredSignatureError:
        raise AuthenticationFailed("Token has expired.")
    except jwt.InvalidTokenError:
        raise AuthenticationFailed("Invalid token.")

class MongoUser:
    """Mock User class to satisfy Django REST Framework's authentication."""
    def __init__(self, user_dict):
        self.id = str(user_dict['_id'])
        self.email = user_dict.get('email')
        self.phone = user_dict.get('phone')
        self.name = user_dict.get('name')
        self.role = user_dict.get('role')  # 'customer' or 'seller'
        self.user_data = user_dict

    @property
    def is_authenticated(self):
        return True

    @property
    def is_anonymous(self):
        return False

class MongoJWTAuthentication(authentication.BaseAuthentication):
    """Custom JWT Authentication class for MongoDB users."""
    def authenticate(self, request):
        auth_header = request.META.get('HTTP_AUTHORIZATION')
        if not auth_header:
            return None
        
        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != 'bearer':
            return None
        
        token = parts[1]
        payload = decode_token(token, 'access')
        
        user_id = payload.get('user_id')
        try:
            user_obj_id = ObjectId(user_id)
        except Exception:
            raise AuthenticationFailed("Invalid user ID format in token.")
            
        user_dict = users_col.find_one({'_id': user_obj_id})
        if not user_dict:
            raise AuthenticationFailed("User not found.")
            
        return (MongoUser(user_dict), token)
