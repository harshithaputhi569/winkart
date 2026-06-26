from rest_framework import serializers

class CategorySerializer(serializers.Serializer):
    id = serializers.CharField(read_only=True)
    name = serializers.CharField(max_length=100)
    slug = serializers.CharField(max_length=100)
    parent_id = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    image_url = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    product_count = serializers.IntegerField(read_only=True, default=0)

class ProductSerializer(serializers.Serializer):
    id = serializers.CharField(read_only=True)
    name = serializers.CharField(max_length=150)
    description = serializers.CharField(max_length=1000, required=False, allow_blank=True)
    price = serializers.FloatField()
    discount_price = serializers.FloatField(required=False, allow_null=True)
    category_id = serializers.CharField()
    category_name = serializers.CharField(read_only=True)
    stock_quantity = serializers.IntegerField(default=0)
    images = serializers.ListField(child=serializers.CharField(), required=False, default=[])
    attributes = serializers.DictField(required=False, default={})
    is_active = serializers.BooleanField(default=True)
    shop_id = serializers.CharField(read_only=True)
    shop_name = serializers.CharField(read_only=True)

class ShopSerializer(serializers.Serializer):
    id = serializers.CharField(read_only=True)
    shop_name = serializers.CharField()
    shop_description = serializers.CharField(required=False, allow_blank=True)
    shop_address = serializers.CharField()
    profile_image = serializers.CharField(required=False, allow_null=True)
    location = serializers.DictField(read_only=True)
    business_hours = serializers.DictField(read_only=True)
    distance = serializers.FloatField(read_only=True, required=False) # In meters, if calculated from query

class BannerSerializer(serializers.Serializer):
    id = serializers.CharField(read_only=True)
    title = serializers.CharField(max_length=150)
    media_type = serializers.ChoiceField(choices=['image', 'video'])
    file_url = serializers.CharField()
    start_date = serializers.DateTimeField()
    end_date = serializers.DateTimeField()
    is_active = serializers.BooleanField(default=True)
    target_link = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    target_product_id = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    shop_id = serializers.CharField(required=False, allow_blank=True, allow_null=True)
