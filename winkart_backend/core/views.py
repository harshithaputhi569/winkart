import os
from datetime import datetime, timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from bson import ObjectId
from winkart_backend.database import categories_col, products_col, users_col, banners_col
from core.serializers import (
    CategorySerializer,
    ProductSerializer,
    ShopSerializer,
    BannerSerializer
)

class CategoryListCreateView(APIView):
    """Category list (Customers) and create (Sellers/Admin) endpoints."""
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request):
        # Fetch all categories
        categories = list(categories_col.find({}))
        
        # Format response
        result = []
        for cat in categories:
            cat_id = str(cat['_id'])
            # Count products belonging to this category
            prod_count = products_col.count_documents({'category_id': cat_id, 'is_active': True})
            
            result.append({
                'id': cat_id,
                'name': cat['name'],
                'slug': cat['slug'],
                'parent_id': cat.get('parent_id'),
                'image_url': cat.get('image_url'),
                'product_count': prod_count
            })
            
        return Response(result, status=status.HTTP_200_OK)

    def post(self, request):
        if request.user.role != 'seller':
            return Response({'error': 'Access denied. Sellers only.'}, status=status.HTTP_403_FORBIDDEN)
            
        serializer = CategorySerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        data = serializer.validated_data
        
        # Check if slug exists
        if categories_col.find_one({'slug': data['slug']}):
            return Response({'error': 'Category slug already exists.'}, status=status.HTTP_400_BAD_REQUEST)
            
        cat_doc = {
            'name': data['name'],
            'slug': data['slug'],
            'parent_id': data.get('parent_id') or None,
            'image_url': data.get('image_url', '')
        }
        
        res = categories_col.insert_one(cat_doc)
        cat_doc['id'] = str(res.inserted_id)
        cat_doc.pop('_id', None)
        
        return Response(cat_doc, status=status.HTTP_201_CREATED)

class CategoryDetailView(APIView):
    """Category details, updates, and deletes."""
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request, category_id):
        try:
            cat_obj_id = ObjectId(category_id)
        except Exception:
            return Response({'error': 'Invalid category ID format.'}, status=status.HTTP_400_BAD_REQUEST)
            
        cat = categories_col.find_one({'_id': cat_obj_id})
        if not cat:
            return Response({'error': 'Category not found.'}, status=status.HTTP_404_NOT_FOUND)
            
        prod_count = products_col.count_documents({'category_id': category_id, 'is_active': True})
        
        data = {
            'id': str(cat['_id']),
            'name': cat['name'],
            'slug': cat['slug'],
            'parent_id': cat.get('parent_id'),
            'image_url': cat.get('image_url'),
            'product_count': prod_count
        }
        return Response(data, status=status.HTTP_200_OK)

    def put(self, request, category_id):
        if request.user.role != 'seller':
            return Response({'error': 'Access denied. Sellers only.'}, status=status.HTTP_403_FORBIDDEN)
            
        try:
            cat_obj_id = ObjectId(category_id)
        except Exception:
            return Response({'error': 'Invalid category ID format.'}, status=status.HTTP_400_BAD_REQUEST)
            
        serializer = CategorySerializer(data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        data = serializer.validated_data
        
        # Check slug conflicts
        slug = data.get('slug')
        if slug:
            conflict = categories_col.find_one({'slug': slug, '_id': {'$ne': cat_obj_id}})
            if conflict:
                return Response({'error': 'Category slug is already taken.'}, status=status.HTTP_400_BAD_REQUEST)
                
        categories_col.update_one({'_id': cat_obj_id}, {'$set': data})
        return Response({'message': 'Category updated successfully.'}, status=status.HTTP_200_OK)

    def delete(self, request, category_id):
        if request.user.role != 'seller':
            return Response({'error': 'Access denied. Sellers only.'}, status=status.HTTP_403_FORBIDDEN)
            
        try:
            cat_obj_id = ObjectId(category_id)
        except Exception:
            return Response({'error': 'Invalid category ID format.'}, status=status.HTTP_400_BAD_REQUEST)
            
        # Check if category contains products
        if products_col.find_one({'category_id': category_id}):
            return Response(
                {'error': 'Cannot delete category containing active products. Reassign products first.'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        categories_col.delete_one({'_id': cat_obj_id})
        return Response({'message': 'Category deleted successfully.'}, status=status.HTTP_200_OK)


class ShopListView(APIView):
    """List all shops or search nearby shops using geospatial coordinates."""
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        lat = request.query_params.get('latitude')
        lng = request.query_params.get('longitude')
        search_query = request.query_params.get('search')
        
        query = {'role': 'seller'}
        
        # Geospatial Query
        if lat and lng:
            try:
                lat = float(lat)
                lng = float(lng)
                query['location'] = {
                    '$near': {
                        '$geometry': {
                            'type': 'Point',
                            'coordinates': [lng, lat]  # MongoDB expects [lng, lat]
                        },
                        '$maxDistance': 50000  # Default 50km limit
                    }
                }
            except ValueError:
                return Response({'error': 'Latitude and Longitude must be numbers.'}, status=status.HTTP_400_BAD_REQUEST)
                
        # Search by shop name
        if search_query:
            query['shop_name'] = {'$regex': search_query, '$options': 'i'}
            
        shops = list(users_col.find(query))
        
        result = []
        for shop in shops:
            coords = shop.get('location', {}).get('coordinates', [0.0, 0.0])
            result.append({
                'id': str(shop['_id']),
                'shop_name': shop['shop_name'],
                'shop_description': shop.get('shop_description', ''),
                'shop_address': shop['shop_address'],
                'profile_image': shop.get('profile_image'),
                'location': {
                    'longitude': coords[0],
                    'latitude': coords[1]
                },
                'business_hours': shop.get('business_hours')
            })
            
        return Response(result, status=status.HTTP_200_OK)

class ShopDetailView(APIView):
    """Get single shop detail and its sub-categories."""
    authentication_classes = []
    permission_classes = []

    def get(self, request, shop_id):
        try:
            shop_obj_id = ObjectId(shop_id)
        except Exception:
            return Response({'error': 'Invalid shop ID format.'}, status=status.HTTP_400_BAD_REQUEST)
            
        shop = users_col.find_one({'_id': shop_obj_id, 'role': 'seller'})
        if not shop:
            return Response({'error': 'Shop not found.'}, status=status.HTTP_404_NOT_FOUND)
            
        coords = shop.get('location', {}).get('coordinates', [0.0, 0.0])
        
        # Find Level 2 categories associated with active products in this shop
        prod_categories_ids = products_col.distinct('category_id', {'shop_id': shop_id, 'is_active': True})
        
        categories = []
        if prod_categories_ids:
            # Fetch those categories from database
            cat_obj_ids = []
            for cid in prod_categories_ids:
                try:
                    cat_obj_ids.append(ObjectId(cid))
                except Exception:
                    pass
            cats_db = list(categories_col.find({'_id': {'$in': cat_obj_ids}}))
            for c in cats_db:
                categories.append({
                    'id': str(c['_id']),
                    'name': c['name'],
                    'slug': c['slug'],
                    'parent_id': c.get('parent_id'),
                    'image_url': c.get('image_url')
                })
                
        data = {
            'id': str(shop['_id']),
            'shop_name': shop['shop_name'],
            'shop_description': shop.get('shop_description', ''),
            'shop_address': shop['shop_address'],
            'profile_image': shop.get('profile_image'),
            'location': {
                'longitude': coords[0],
                'latitude': coords[1]
            },
            'business_hours': shop.get('business_hours'),
            'categories': categories  # Seller categories based on products listed
        }
        
        return Response(data, status=status.HTTP_200_OK)


class ProductListCreateView(APIView):
    """Browse products (Customer) or List/Create products (Seller)."""
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request):
        shop_id = request.query_params.get('shop_id')
        category_id = request.query_params.get('category_id')
        search_query = request.query_params.get('search')
        sort_by = request.query_params.get('sort_by', 'newest')
        
        query = {}
        
        # If user is a logged-in seller listing their own products, restrict to their shop
        if request.user.is_authenticated and request.user.role == 'seller' and request.query_params.get('my_products') == 'true':
            query['shop_id'] = request.user.id
        else:
            # Customers only view active products
            query['is_active'] = True
            if shop_id:
                query['shop_id'] = shop_id
                
        if category_id:
            query['category_id'] = category_id
            
        # Support text search
        if search_query:
            # If text search is indexed
            query['$text'] = {'$search': search_query}
            # Fallback regex match if text search returns empty or for partial words
            # In production, we'd rank them or query Elasticsearch.
            
        # Execute query with sorting
        cursor = products_col.find(query)
        
        if sort_by == 'price_asc':
            cursor = cursor.sort('price', 1)
        elif sort_by == 'price_desc':
            cursor = cursor.sort('price', -1)
        elif sort_by == 'newest':
            cursor = cursor.sort('_id', -1)
            
        products = list(cursor)
        
        # Populate Category and Shop names
        result = []
        for prod in products:
            p_id = str(prod['_id'])
            
            # Fetch Category Name
            cat_name = ""
            try:
                cat = categories_col.find_one({'_id': ObjectId(prod['category_id'])})
                if cat:
                    cat_name = cat['name']
            except Exception:
                pass
                
            # Fetch Shop Name
            shop_name = ""
            try:
                shop = users_col.find_one({'_id': ObjectId(prod['shop_id'])})
                if shop:
                    shop_name = shop.get('shop_name', '')
            except Exception:
                pass
                
            result.append({
                'id': p_id,
                'name': prod['name'],
                'description': prod.get('description', ''),
                'price': prod['price'],
                'discount_price': prod.get('discount_price'),
                'category_id': prod['category_id'],
                'category_name': cat_name,
                'stock_quantity': prod.get('stock_quantity', 0),
                'images': prod.get('images', []),
                'attributes': prod.get('attributes', {}),
                'is_active': prod.get('is_active', True),
                'shop_id': prod['shop_id'],
                'shop_name': shop_name
            })
            
        return Response(result, status=status.HTTP_200_OK)

    def post(self, request):
        if request.user.role != 'seller':
            return Response({'error': 'Access denied. Sellers only.'}, status=status.HTTP_403_FORBIDDEN)
            
        serializer = ProductSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        data = serializer.validated_data
        
        # Verify category exists
        try:
            cat = categories_col.find_one({'_id': ObjectId(data['category_id'])})
            if not cat:
                return Response({'error': 'Category does not exist.'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception:
            return Response({'error': 'Invalid category ID format.'}, status=status.HTTP_400_BAD_REQUEST)
            
        prod_doc = {
            'name': data['name'],
            'description': data.get('description', ''),
            'price': data['price'],
            'discount_price': data.get('discount_price'),
            'category_id': data['category_id'],
            'stock_quantity': data.get('stock_quantity', 0),
            'images': data.get('images', []),
            'attributes': data.get('attributes', {}),
            'is_active': data.get('is_active', True),
            'shop_id': request.user.id,
            'upsell_ids': [],     # Handled by marketing config
            'cross_sell_ids': []  # Handled by marketing config
        }
        
        res = products_col.insert_one(prod_doc)
        prod_doc['id'] = str(res.inserted_id)
        prod_doc.pop('_id', None)
        
        return Response(prod_doc, status=status.HTTP_201_CREATED)

class ProductDetailView(APIView):
    """View, update, or delete products."""
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request, product_id):
        try:
            prod_obj_id = ObjectId(product_id)
        except Exception:
            return Response({'error': 'Invalid product ID format.'}, status=status.HTTP_400_BAD_REQUEST)
            
        prod = products_col.find_one({'_id': prod_obj_id})
        if not prod:
            return Response({'error': 'Product not found.'}, status=status.HTTP_404_NOT_FOUND)
            
        # Fetch Category Name
        cat_name = ""
        try:
            cat = categories_col.find_one({'_id': ObjectId(prod['category_id'])})
            if cat:
                cat_name = cat['name']
        except Exception:
            pass
            
        # Fetch Shop Details
        shop_name = ""
        shop_address = ""
        try:
            shop = users_col.find_one({'_id': ObjectId(prod['shop_id'])})
            if shop:
                shop_name = shop.get('shop_name', '')
                shop_address = shop.get('shop_address', '')
        except Exception:
            pass
            
        data = {
            'id': str(prod['_id']),
            'name': prod['name'],
            'description': prod.get('description', ''),
            'price': prod['price'],
            'discount_price': prod.get('discount_price'),
            'category_id': prod['category_id'],
            'category_name': cat_name,
            'stock_quantity': prod.get('stock_quantity', 0),
            'images': prod.get('images', []),
            'attributes': prod.get('attributes', {}),
            'is_active': prod.get('is_active', True),
            'shop_id': prod['shop_id'],
            'shop_name': shop_name,
            'shop_address': shop_address,
            'upsell_ids': prod.get('upsell_ids', []),
            'cross_sell_ids': prod.get('cross_sell_ids', [])
        }
        return Response(data, status=status.HTTP_200_OK)

    def put(self, request, product_id):
        try:
            prod_obj_id = ObjectId(product_id)
        except Exception:
            return Response({'error': 'Invalid product ID format.'}, status=status.HTTP_400_BAD_REQUEST)
            
        prod = products_col.find_one({'_id': prod_obj_id})
        if not prod:
            return Response({'error': 'Product not found.'}, status=status.HTTP_404_NOT_FOUND)
            
        # Verify ownership
        if request.user.role != 'seller' or prod['shop_id'] != request.user.id:
            return Response({'error': 'Access denied. You do not own this product.'}, status=status.HTTP_403_FORBIDDEN)
            
        serializer = ProductSerializer(data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        data = serializer.validated_data
        
        # Verify category if changed
        if 'category_id' in data:
            try:
                cat = categories_col.find_one({'_id': ObjectId(data['category_id'])})
                if not cat:
                    return Response({'error': 'Category does not exist.'}, status=status.HTTP_400_BAD_REQUEST)
            except Exception:
                return Response({'error': 'Invalid category ID format.'}, status=status.HTTP_400_BAD_REQUEST)
                
        products_col.update_one({'_id': prod_obj_id}, {'$set': data})
        return Response({'message': 'Product updated successfully.'}, status=status.HTTP_200_OK)

    def delete(self, request, product_id):
        try:
            prod_obj_id = ObjectId(product_id)
        except Exception:
            return Response({'error': 'Invalid product ID format.'}, status=status.HTTP_400_BAD_REQUEST)
            
        prod = products_col.find_one({'_id': prod_obj_id})
        if not prod:
            return Response({'error': 'Product not found.'}, status=status.HTTP_404_NOT_FOUND)
            
        # Verify ownership
        if request.user.role != 'seller' or prod['shop_id'] != request.user.id:
            return Response({'error': 'Access denied. You do not own this product.'}, status=status.HTTP_403_FORBIDDEN)
            
        products_col.delete_one({'_id': prod_obj_id})
        return Response({'message': 'Product deleted successfully.'}, status=status.HTTP_200_OK)


class BannerListCreateView(APIView):
    """Browse active banners (Customer) or manage banners (Seller)."""
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request):
        shop_id = request.query_params.get('shop_id')
        media_type = request.query_params.get('media_type') # 'image' or 'video'
        
        # Customers only get currently scheduled active banners
        now = datetime.now(timezone.utc)
        
        query = {
            'is_active': True,
            'start_date': {'$lte': now},
            'end_date': {'$gte': now}
        }
        
        # Allow sellers listing their own banners to bypass date restrictions
        if request.user.is_authenticated and request.user.role == 'seller' and request.query_params.get('my_banners') == 'true':
            query = {'shop_id': request.user.id}
        else:
            # Customers filtering
            if shop_id:
                query['shop_id'] = shop_id
            else:
                # Welcome banners on homepage have null or empty shop_id
                query['$or'] = [{'shop_id': None}, {'shop_id': ''}]
                
        if media_type:
            query['media_type'] = media_type
            
        banners = list(banners_col.find(query))
        
        result = []
        for b in banners:
            result.append({
                'id': str(b['_id']),
                'title': b['title'],
                'media_type': b['media_type'],
                'file_url': b['file_url'],
                'start_date': b['start_date'],
                'end_date': b['end_date'],
                'is_active': b.get('is_active', True),
                'target_link': b.get('target_link'),
                'target_product_id': b.get('target_product_id'),
                'shop_id': b.get('shop_id')
            })
            
        return Response(result, status=status.HTTP_200_OK)

    def post(self, request):
        if request.user.role != 'seller':
            return Response({'error': 'Access denied. Sellers only.'}, status=status.HTTP_403_FORBIDDEN)
            
        serializer = BannerSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        data = serializer.validated_data
        
        # Double check date range
        if data['start_date'] >= data['end_date']:
            return Response({'error': 'Start date must be before end date.'}, status=status.HTTP_400_BAD_REQUEST)
            
        banner_doc = {
            'title': data['title'],
            'media_type': data['media_type'],
            'file_url': data['file_url'],
            'start_date': data['start_date'],
            'end_date': data['end_date'],
            'is_active': data.get('is_active', True),
            'target_link': data.get('target_link'),
            'target_product_id': data.get('target_product_id'),
            'shop_id': request.user.id
        }
        
        res = banners_col.insert_one(banner_doc)
        banner_doc['id'] = str(res.inserted_id)
        banner_doc.pop('_id', None)
        
        return Response(banner_doc, status=status.HTTP_201_CREATED)

class BannerDetailView(APIView):
    """View, update, or delete banner."""
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request, banner_id):
        try:
            b_obj_id = ObjectId(banner_id)
        except Exception:
            return Response({'error': 'Invalid banner ID format.'}, status=status.HTTP_400_BAD_REQUEST)
            
        banner = banners_col.find_one({'_id': b_obj_id})
        if not banner:
            return Response({'error': 'Banner not found.'}, status=status.HTTP_404_NOT_FOUND)
            
        data = {
            'id': str(banner['_id']),
            'title': banner['title'],
            'media_type': banner['media_type'],
            'file_url': banner['file_url'],
            'start_date': banner['start_date'],
            'end_date': banner['end_date'],
            'is_active': banner.get('is_active', True),
            'target_link': banner.get('target_link'),
            'target_product_id': banner.get('target_product_id'),
            'shop_id': banner.get('shop_id')
        }
        return Response(data, status=status.HTTP_200_OK)

    def put(self, request, banner_id):
        try:
            b_obj_id = ObjectId(banner_id)
        except Exception:
            return Response({'error': 'Invalid banner ID format.'}, status=status.HTTP_400_BAD_REQUEST)
            
        banner = banners_col.find_one({'_id': b_obj_id})
        if not banner:
            return Response({'error': 'Banner not found.'}, status=status.HTTP_404_NOT_FOUND)
            
        # Verify ownership
        if request.user.role != 'seller' or banner.get('shop_id') != request.user.id:
            return Response({'error': 'Access denied. You do not own this banner.'}, status=status.HTTP_403_FORBIDDEN)
            
        serializer = BannerSerializer(data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        data = serializer.validated_data
        
        # Verify dates if changed
        start_date = data.get('start_date', banner['start_date'])
        end_date = data.get('end_date', banner['end_date'])
        if start_date >= end_date:
            return Response({'error': 'Start date must be before end date.'}, status=status.HTTP_400_BAD_REQUEST)
            
        banners_col.update_one({'_id': b_obj_id}, {'$set': data})
        return Response({'message': 'Banner updated successfully.'}, status=status.HTTP_200_OK)

    def delete(self, request, banner_id):
        try:
            b_obj_id = ObjectId(banner_id)
        except Exception:
            return Response({'error': 'Invalid banner ID format.'}, status=status.HTTP_400_BAD_REQUEST)
            
        banner = banners_col.find_one({'_id': b_obj_id})
        if not banner:
            return Response({'error': 'Banner not found.'}, status=status.HTTP_404_NOT_FOUND)
            
        # Verify ownership
        if request.user.role != 'seller' or banner.get('shop_id') != request.user.id:
            return Response({'error': 'Access denied. You do not own this banner.'}, status=status.HTTP_403_FORBIDDEN)
            
        banners_col.delete_one({'_id': b_obj_id})
        return Response({'message': 'Banner deleted successfully.'}, status=status.HTTP_200_OK)
