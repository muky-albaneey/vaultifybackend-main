from rest_framework import serializers
from django.db.models import Avg
from .models import Admin, Service, Provider, ProviderPhoto, ProviderReview, Alert, AlertAttachment


class AdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = Admin
        fields = ['id', 'adminName', 'adminEmail', 'adminRole', 'adminPassword']
        extra_kwargs = {'adminPassword': {'write_only': True}, 'id': {'read_only': True}}

    def create(self, validated_data):
        from django.contrib.auth.hashers import make_password
        pwd = validated_data.get('adminPassword')
        if pwd:
            validated_data['adminPassword'] = make_password(pwd)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        from django.contrib.auth.hashers import make_password
        pwd = validated_data.get('adminPassword')
        if pwd:
            validated_data['adminPassword'] = make_password(pwd)
        return super().update(instance, validated_data)


class ServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = ['id', 'name']
        extra_kwargs = {'id': {'read_only': True}}


# --- Provider media/review serializers ---
class ProviderPhotoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProviderPhoto
        fields = ['id', 'image', 'uploaded_at']
        read_only_fields = ['id', 'uploaded_at']


class ProviderReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProviderReview
        fields = ['id', 'reviewer_name', 'rating', 'comment', 'created_at']
        read_only_fields = ['id', 'created_at']


class ProviderSerializer(serializers.ModelSerializer):
    # relations
    service = ServiceSerializer(read_only=True)
    service_id = serializers.PrimaryKeyRelatedField(
        queryset=Service.objects.all(), source='service', write_only=True
    )
    admin = serializers.PrimaryKeyRelatedField(queryset=Admin.objects.all(), write_only=True)
    admin_info = serializers.StringRelatedField(source='admin', read_only=True)

    # media & reviews
    photos = ProviderPhotoSerializer(many=True, read_only=True)

    # canonical upload field (what your code originally used)
    photos_upload = serializers.ListField(
        child=serializers.ImageField(), write_only=True, required=False
    )

    # reviews (read-only)
    reviews = ProviderReviewSerializer(many=True, read_only=True)

    # computed
    average_rating = serializers.SerializerMethodField()
    reviews_count  = serializers.SerializerMethodField()
    full_name = serializers.CharField(read_only=True)

    class Meta:
        model = Provider
        fields = [
            'id',
            # profile
            'first_name', 'last_name', 'full_name', 'profile_picture',
            'availability', 'location', 'phone', 'bio', 'skill',
            # relations
            'service', 'service_id', 'admin', 'admin_info',
            # media & reviews
            'photos', 'photos_upload', 'reviews',
            # computed
            'average_rating', 'reviews_count',
            'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at', 'full_name',
            'average_rating', 'reviews_count', 'photos', 'reviews'
        ]

    def validate(self, attrs):
        """
        Accept files under EITHER 'photos_upload' (canonical) OR 'photos' (alias from clients like Postman).
        """
        request = self.context.get('request')
        if request and hasattr(request, 'FILES'):
            # Try canonical first, then alias
            files_canonical = request.FILES.getlist('photos_upload')
            files_alias     = request.FILES.getlist('photos')
            merged = []
            if files_canonical:
                merged.extend(files_canonical)
            if files_alias:
                merged.extend(files_alias)
            # If the serializer didn't already parse photos_upload, inject them
            if merged and 'photos_upload' not in attrs:
                attrs['photos_upload'] = merged
        return super().validate(attrs)

    def _replace_photos(self, provider: Provider, files):
        # Hard cap of 5 photos (as per UI)
        ProviderPhoto.objects.filter(provider=provider).delete()
        for f in files[:5]:
            ProviderPhoto.objects.create(provider=provider, image=f)

    def create(self, validated_data):
        files = validated_data.pop('photos_upload', [])
        provider = super().create(validated_data)
        if files:
            self._replace_photos(provider, files)
        return provider

    def update(self, instance, validated_data):
        files = validated_data.pop('photos_upload', None)
        instance = super().update(instance, validated_data)
        if files is not None:
            self._replace_photos(instance, files)
        return instance

    def get_average_rating(self, obj):
        agg = obj.reviews.aggregate(avg=Avg('rating'))
        return round(agg['avg'] or 0.0, 1)

    def get_reviews_count(self, obj):
        return obj.reviews.count()


class ServiceWithProvidersSerializer(serializers.ModelSerializer):
    providers = ProviderSerializer(many=True, read_only=True)
    class Meta:
        model = Service
        fields = ['id', 'name', 'providers']


# --- Alerts (unchanged) ---
class AlertAttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = AlertAttachment
        fields = ['id', 'announcement_image']
        extra_kwargs = {'id': {'read_only': True}}


class AlertSerializer(serializers.ModelSerializer):
    announcement_image = serializers.ListField(child=serializers.FileField(), write_only=True, required=False)
    attachments = AlertAttachmentSerializer(many=True, read_only=True, source='announcement_image')

    class Meta:
        model = Alert
        fields = [
            'id', 'title', 'category', 'message', 'public_date', 'estate', 'role',
            'announcement_image', 'attachments', 'created_at'
        ]
        extra_kwargs = {'id': {'read_only': True}, 'created_at': {'read_only': True}}

    def create(self, validated_data):
        files = validated_data.pop('announcement_image', [])
        alert = Alert.objects.create(**validated_data)
        for f in files:
            AlertAttachment.objects.create(alert=alert, announcement_image=f)
        return alert
