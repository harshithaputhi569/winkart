import os
from datetime import datetime, timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.hashers import make_password, check_password
from django.core.files.storage import FileSystemStorage
from bson import ObjectId

from winkart_backend.database import users_col
from authentication.serializers import (
    CustomerRegisterSerializer,
    SellerRegisterSerializer,
    LoginSerializer,
    TokenRefreshSerializer,
    ProfileSerializer,
    SellerSettingsSerializer
)
from authentication.auth import generate_tokens, decode_token, MongoUser

class CustomerRegisterView(APIView):
    """Customer signup endpoint."""
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        serializer = CustomerRegisterSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data
        email = data.get('email')
        phone = data.get('phone')
        
        # Check if already exists
        query = []
        if email:
            query.append({'email': email})
        if phone:
            query.append({'phone': phone})
            
        if query:
            existing = users_col.find_one({'$or': query})
            if existing:
                return Response(
                    {'error': 'A user with this email or phone already exists.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
        user_doc = {
            'name': data['name'],
            'email': email,
            'phone': phone,
            'password': make_password(data['password']),
            'role': 'customer',
            'profile_image': None,
            'created_at': datetime.now(timezone.utc)
        }
        
        result = users_col.insert_one(user_doc)
        tokens = generate_tokens(result.inserted_id, 'customer')
        
        return Response({
            'message': 'Customer registered successfully.',
            'user': {
                'id': str(result.inserted_id),
                'name': user_doc['name'],
                'email': user_doc['email'],
                'phone': user_doc['phone'],
                'role': 'customer'
            },
            'tokens': tokens
        }, status=status.HTTP_201_CREATED)

class SellerRegisterView(APIView):
    """Seller signup endpoint."""
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        serializer = SellerRegisterSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data
        email = data.get('email')
        phone = data.get('phone')
        
        # Check if already exists
        query = []
        if email:
            query.append({'email': email})
        if phone:
            query.append({'phone': phone})
            
        if query:
            existing = users_col.find_one({'$or': query})
            if existing:
                return Response(
                    {'error': 'A user with this email or phone already exists.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
        user_doc = {
            'name': data['name'],
            'email': email,
            'phone': phone,
            'password': make_password(data['password']),
            'role': 'seller',
            'profile_image': None,
            'shop_name': data['shop_name'],
            'shop_description': data.get('shop_description', ''),
            'shop_address': data['shop_address'],
            # Store coordinates
            'location': {
                'type': 'Point',
                'coordinates': [
                    float(data.get('longitude') if data.get('longitude') is not None else 0.0),
                    float(data.get('latitude') if data.get('latitude') is not None else 0.0)
                ]  # [longitude, latitude]
            },
            'business_hours': {
                day: {'is_open': True, 'open_time': '09:00', 'close_time': '21:00'}
                for day in ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
            },
            'notification_preferences': {
                'email': True,
                'sms': True
            },
            'created_at': datetime.now(timezone.utc)
        }
        
        result = users_col.insert_one(user_doc)
        tokens = generate_tokens(result.inserted_id, 'seller')
        
        return Response({
            'message': 'Seller registered successfully.',
            'user': {
                'id': str(result.inserted_id),
                'name': user_doc['name'],
                'email': user_doc['email'],
                'phone': user_doc['phone'],
                'role': 'seller',
                'shop_name': user_doc['shop_name']
            },
            'tokens': tokens
        }, status=status.HTTP_201_CREATED)

class LoginView(APIView):
    """Unified login endpoint for Customers and Sellers."""
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        data = serializer.validated_data
        email = data.get('email')
        phone = data.get('phone')
        password = data['password']
        
        # Build query
        query = {}
        if email:
            query['email'] = email
        elif phone:
            query['phone'] = phone
            
        user_dict = users_col.find_one(query)
        if not user_dict or not check_password(password, user_dict['password']):
            return Response(
                {'error': 'Invalid credentials.'},
                status=status.HTTP_401_UNAUTHORIZED
            )
            
        tokens = generate_tokens(user_dict['_id'], user_dict['role'])
        
        response_data = {
            'message': 'Login successful.',
            'user': {
                'id': str(user_dict['_id']),
                'name': user_dict['name'],
                'email': user_dict.get('email'),
                'phone': user_dict.get('phone'),
                'role': user_dict['role']
            },
            'tokens': tokens
        }
        
        if user_dict['role'] == 'seller':
            response_data['user']['shop_name'] = user_dict.get('shop_name')
            
        return Response(response_data, status=status.HTTP_200_OK)

class TokenRefreshView(APIView):
    """Refreshes access token using refresh token."""
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        serializer = TokenRefreshSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        refresh_token = serializer.validated_data['refresh']
        try:
            payload = decode_token(refresh_token, 'refresh')
            user_id = payload.get('user_id')
            role = payload.get('role')
            
            # Generate new access token
            tokens = generate_tokens(user_id, role)
            return Response({
                'access': tokens['access']
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class ProfileView(APIView):
    """Customer & Seller profile view/edit."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user_dict = users_col.find_one({'_id': ObjectId(request.user.id)})
        if not user_dict:
            return Response({'error': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)
            
        data = {
            'id': str(user_dict['_id']),
            'name': user_dict['name'],
            'email': user_dict.get('email'),
            'phone': user_dict.get('phone'),
            'role': user_dict['role'],
            'profile_image': user_dict.get('profile_image')
        }
        
        if user_dict['role'] == 'seller':
            data.update({
                'shop_name': user_dict.get('shop_name'),
                'shop_description': user_dict.get('shop_description'),
                'shop_address': user_dict.get('shop_address'),
            })
            
        return Response(data, status=status.HTTP_200_OK)

    def put(self, request):
        serializer = ProfileSerializer(data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        update_data = serializer.validated_data
        
        # Verify unique constraints if changing email/phone
        email = update_data.get('email')
        phone = update_data.get('phone')
        user_id = ObjectId(request.user.id)
        
        if email:
            conflict = users_col.find_one({'email': email, '_id': {'$ne': user_id}})
            if conflict:
                return Response({'error': 'Email is already taken.'}, status=status.HTTP_400_BAD_REQUEST)
        if phone:
            conflict = users_col.find_one({'phone': phone, '_id': {'$ne': user_id}})
            if conflict:
                return Response({'error': 'Phone number is already taken.'}, status=status.HTTP_400_BAD_REQUEST)
                
        # Update user
        users_col.update_one({'_id': user_id}, {'$set': update_data})
        
        # Refresh user dict
        updated_user = users_col.find_one({'_id': user_id})
        
        return Response({
            'message': 'Profile updated successfully.',
            'profile': {
                'id': str(updated_user['_id']),
                'name': updated_user['name'],
                'email': updated_user.get('email'),
                'phone': updated_user.get('phone'),
                'profile_image': updated_user.get('profile_image')
            }
        }, status=status.HTTP_200_OK)

class SellerSettingsView(APIView):
    """Seller settings configuration endpoint (business hours, map coordinates, shop profile)."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role != 'seller':
            return Response({'error': 'Access denied. Sellers only.'}, status=status.HTTP_403_FORBIDDEN)
            
        user_dict = users_col.find_one({'_id': ObjectId(request.user.id)})
        
        # Format location
        loc = user_dict.get('location', {})
        coords = loc.get('coordinates', [0.0, 0.0]) # [lng, lat]
        location_data = {
            'longitude': coords[0],
            'latitude': coords[1]
        }
        
        data = {
            'shop_name': user_dict.get('shop_name'),
            'shop_description': user_dict.get('shop_description'),
            'shop_address': user_dict.get('shop_address'),
            'location': location_data,
            'business_hours': user_dict.get('business_hours'),
            'notification_preferences': user_dict.get('notification_preferences')
        }
        return Response(data, status=status.HTTP_200_OK)

    def put(self, request):
        if request.user.role != 'seller':
            return Response({'error': 'Access denied. Sellers only.'}, status=status.HTTP_403_FORBIDDEN)
            
        serializer = SellerSettingsSerializer(data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        data = serializer.validated_data
        set_data = {}
        
        # Basic fields
        for field in ['shop_name', 'shop_description', 'shop_address', 'business_hours', 'notification_preferences']:
            if field in data:
                set_data[field] = data[field]
                
        # Parse location coordinate to GeoJSON Point
        if 'location' in data:
            loc = data['location']
            set_data['location'] = {
                'type': 'Point',
                'coordinates': [loc['longitude'], loc['latitude']]  # [longitude, latitude]
            }
            
        users_col.update_one({'_id': ObjectId(request.user.id)}, {'$set': set_data})
        
        return Response({'message': 'Seller settings updated successfully.'}, status=status.HTTP_200_OK)

class MediaUploadView(APIView):
    """File upload utility for uploading profile, product images, or banners."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if 'file' not in request.FILES:
            return Response({'error': 'No file uploaded.'}, status=status.HTTP_400_BAD_REQUEST)
            
        uploaded_file = request.FILES['file']
        fs = FileSystemStorage()
        filename = fs.save(uploaded_file.name, uploaded_file)
        file_url = fs.url(filename)
        
        return Response({
            'message': 'File uploaded successfully.',
            'filename': filename,
            'file_url': file_url
        }, status=status.HTTP_201_CREATED)
