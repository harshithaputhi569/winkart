from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from bson import ObjectId

from winkart_backend.database import products_col

class ConfigureRecommendationsView(APIView):
    """Sellers configure upsell or cross-sell product mappings for a source product."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if request.user.role != 'seller':
            return Response({'error': 'Access denied. Sellers only.'}, status=status.HTTP_403_FORBIDDEN)
            
        product_id = request.data.get('product_id')
        rec_type = request.data.get('type') # 'upsell' or 'cross_sell'
        linked_ids = request.data.get('linked_product_ids', []) # list of product ID strings
        
        if not product_id or rec_type not in ['upsell', 'cross_sell']:
            return Response(
                {'error': "Missing 'product_id' or invalid 'type'. Must be 'upsell' or 'cross_sell'."},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # Verify source product exists and belongs to seller
        try:
            source_obj_id = ObjectId(product_id)
        except Exception:
            return Response({'error': 'Invalid source product ID format.'}, status=status.HTTP_400_BAD_REQUEST)
            
        source_prod = products_col.find_one({'_id': source_obj_id, 'shop_id': request.user.id})
        if not source_prod:
            return Response({'error': 'Source product not found or does not belong to you.'}, status=status.HTTP_404_NOT_FOUND)
            
        # Validate that all linked product IDs exist
        valid_linked_ids = []
        for lid in linked_ids:
            try:
                l_obj_id = ObjectId(lid)
                linked_prod = products_col.find_one({'_id': l_obj_id})
                if linked_prod:
                    valid_linked_ids.append(lid)
            except Exception:
                pass
                
        # Update source product
        update_field = 'upsell_ids' if rec_type == 'upsell' else 'cross_sell_ids'
        products_col.update_one({'_id': source_obj_id}, {'$set': {update_field: valid_linked_ids}})
        
        return Response({
            'message': f'Linked {rec_type} products updated successfully.',
            'configured_count': len(valid_linked_ids)
        }, status=status.HTTP_200_OK)


class FetchRecommendationsView(APIView):
    """Retrieve populated upsell and cross-sell recommendation details for a product."""
    authentication_classes = []
    permission_classes = []

    def get(self, request, product_id):
        try:
            prod_obj_id = ObjectId(product_id)
        except Exception:
            return Response({'error': 'Invalid product ID format.'}, status=status.HTTP_400_BAD_REQUEST)
            
        product = products_col.find_one({'_id': prod_obj_id})
        if not product:
            return Response({'error': 'Product not found.'}, status=status.HTTP_404_NOT_FOUND)
            
        # Helper to fetch populated product details
        def get_populated_list(id_list):
            res_list = []
            for pid in id_list:
                try:
                    p = products_col.find_one({'_id': ObjectId(pid), 'is_active': True})
                    if p:
                        res_list.append({
                            'id': str(p['_id']),
                            'name': p['name'],
                            'price': p['price'],
                            'discount_price': p.get('discount_price'),
                            'images': p.get('images', []),
                            'stock_quantity': p.get('stock_quantity', 0)
                        })
                except Exception:
                    pass
            return res_list
            
        upsell_ids = product.get('upsell_ids', [])
        cross_sell_ids = product.get('cross_sell_ids', [])
        
        upsells = get_populated_list(upsell_ids)
        cross_sells = get_populated_list(cross_sell_ids)
        
        return Response({
            'upsell_recommendations': upsells,
            'cross_sell_recommendations': cross_sells
        }, status=status.HTTP_200_OK)
