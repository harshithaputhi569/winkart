from rest_framework import serializers

class CustomerRegisterSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=100)
    email = serializers.EmailField(required=False, allow_null=True)
    phone = serializers.CharField(max_length=20, required=False, allow_null=True)
    password = serializers.CharField(write_only=True, min_length=6)

    def validate(self, attrs):
        if not attrs.get('email') and not attrs.get('phone'):
            raise serializers.ValidationError("Either email or phone is required for registration.")
        return attrs

class SellerRegisterSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=100)
    email = serializers.EmailField(required=False, allow_null=True)
    phone = serializers.CharField(max_length=20, required=False, allow_null=True)
    password = serializers.CharField(write_only=True, min_length=6)
    shop_name = serializers.CharField(max_length=150)
    shop_description = serializers.CharField(required=False, allow_blank=True, max_length=500)
    shop_address = serializers.CharField(max_length=255)
    latitude = serializers.FloatField(required=False, allow_null=True)
    longitude = serializers.FloatField(required=False, allow_null=True)

    def validate(self, attrs):
        if not attrs.get('email') and not attrs.get('phone'):
            raise serializers.ValidationError("Either email or phone is required for registration.")
        return attrs

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(required=False, allow_null=True)
    phone = serializers.CharField(required=False, allow_null=True)
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        if not attrs.get('email') and not attrs.get('phone'):
            raise serializers.ValidationError("Either email or phone is required to login.")
        return attrs

class TokenRefreshSerializer(serializers.Serializer):
    refresh = serializers.CharField()

class ProfileSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=100, required=False)
    email = serializers.EmailField(required=False, allow_null=True)
    phone = serializers.CharField(max_length=20, required=False, allow_null=True)
    profile_image = serializers.CharField(required=False, allow_blank=True) # Will store file path/URL

class BusinessHourDaySerializer(serializers.Serializer):
    is_open = serializers.BooleanField(default=True)
    open_time = serializers.CharField(max_length=5, default="09:00")  # HH:MM
    close_time = serializers.CharField(max_length=5, default="21:00") # HH:MM

class BusinessHoursSerializer(serializers.Serializer):
    monday = BusinessHourDaySerializer(required=False)
    tuesday = BusinessHourDaySerializer(required=False)
    wednesday = BusinessHourDaySerializer(required=False)
    thursday = BusinessHourDaySerializer(required=False)
    friday = BusinessHourDaySerializer(required=False)
    saturday = BusinessHourDaySerializer(required=False)
    sunday = BusinessHourDaySerializer(required=False)

class LocationSerializer(serializers.Serializer):
    latitude = serializers.FloatField()
    longitude = serializers.FloatField()

class NotificationPreferencesSerializer(serializers.Serializer):
    email = serializers.BooleanField(default=True)
    sms = serializers.BooleanField(default=True)

class SellerSettingsSerializer(serializers.Serializer):
    shop_name = serializers.CharField(max_length=150, required=False)
    shop_description = serializers.CharField(max_length=500, required=False, allow_blank=True)
    shop_address = serializers.CharField(max_length=255, required=False)
    location = LocationSerializer(required=False)
    business_hours = BusinessHoursSerializer(required=False)
    notification_preferences = NotificationPreferencesSerializer(required=False)
