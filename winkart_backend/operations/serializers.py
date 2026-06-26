from rest_framework import serializers

class CartItemSerializer(serializers.Serializer):
    product_id = serializers.CharField()
    quantity = serializers.IntegerField(min_value=1)

class CartSerializer(serializers.Serializer):
    shop_id = serializers.CharField(required=True)
    items = CartItemSerializer(many=True, required=True)

class CheckoutSerializer(serializers.Serializer):
    customer_name = serializers.CharField(max_length=100)
    customer_phone = serializers.CharField(max_length=20)

class BillStatusUpdateSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=['Billed', 'Paid', 'Cancelled'])

class ImportLogSerializer(serializers.Serializer):
    id = serializers.CharField(read_only=True)
    filename = serializers.CharField()
    total_records = serializers.IntegerField()
    success_count = serializers.IntegerField()
    failed_count = serializers.IntegerField()
    errors = serializers.ListField(child=serializers.DictField(), required=False)
    created_at = serializers.DateTimeField()
