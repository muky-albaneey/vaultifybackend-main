from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import Admin, Service, Provider, Alert
from .serializers import AdminSerializer, ServiceSerializer, ProviderSerializer, ServiceWithProvidersSerializer, AlertSerializer
from django.contrib.auth.hashers import make_password, check_password
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView, ListCreateAPIView
from django.contrib.auth import authenticate

from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework.permissions import IsAuthenticated
from django.views.decorators.csrf import csrf_exempt

from rest_framework.permissions import AllowAny

# Removed is_auth view as per user request

from rest_framework.decorators import permission_classes
from rest_framework.permissions import IsAuthenticated

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_data(request):
    try:
        admin = request.user
        serializer = AdminSerializer(admin)
        return Response({'success': True, 'userData': serializer.data}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'success': False, 'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny

from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
@api_view(['POST'])
def register_admin(request):
    if request.method == 'POST':
        serializer = AdminSerializer(data=request.data)
        if serializer.is_valid():
            admin = serializer.save()
            return Response(AdminSerializer(admin).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
from rest_framework_simplejwt.tokens import RefreshToken

@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def login_admin(request):
    data = request.data
    adminEmail = data.get('adminEmail')
    adminPassword = data.get('adminPassword')
    try:
        admin = Admin.objects.filter(adminEmail=adminEmail).first()
        if admin and adminPassword and check_password(adminPassword, admin.adminPassword):
            refresh = RefreshToken.for_user(admin)
            serializer = AdminSerializer(admin)
            return Response({
                'success': True,
                'userData': serializer.data,
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }, status=status.HTTP_200_OK)
        return Response({'success': False, 'error': 'Invalid email or password'}, status=status.HTTP_401_UNAUTHORIZED)
    except Exception as e:
        return Response({'success': False, 'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
def get_all_admin(request):
    admins = Admin.objects.all()
    serializer = AdminSerializer(admins, many=True)
    return Response(serializer.data)

@api_view(['GET'])
def get_range_view_admins(request):
    admins = Admin.objects.filter(adminRole="Range-view admin")
    serializer = AdminSerializer(admins, many=True)
    return Response(serializer.data)

@api_view(['GET'])
def get_paradise_admins(request):
    admins = Admin.objects.filter(adminRole="Paradise admin")
    serializer = AdminSerializer(admins, many=True)
    return Response(serializer.data)

from rest_framework.decorators import permission_classes
from rest_framework.permissions import AllowAny

@api_view(['GET'])
@permission_classes([AllowAny])
def get_paradise_and_range_view_admins(request):
    current_role = request.query_params.get('currentRole', None)
    if current_role == "Super-admin":
        admins = Admin.objects.filter(adminRole__in=["Paradise admin", "Range-view admin"])
    elif current_role == "Range-view admin":
        admins = Admin.objects.filter(adminRole="Range-view admin")
    elif current_role == "Paradise admin":
        admins = Admin.objects.filter(adminRole="Paradise admin")
    else:
        admins = Admin.objects.none()
    serializer = AdminSerializer(admins, many=True)
    return Response(serializer.data)


# views.py
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import (
    ListAPIView, ListCreateAPIView, RetrieveUpdateDestroyAPIView
)
from rest_framework.parsers import MultiPartParser, FormParser
from django.shortcuts import get_object_or_404
from django.db.models import Prefetch

from .models import Admin, Service, Provider, ProviderPhoto, ProviderReview, Alert
from .serializers import (
    AdminSerializer, ServiceSerializer, ProviderSerializer,
    ServiceWithProvidersSerializer, AlertSerializer, ProviderReviewSerializer
)

# --- services (unchanged) ---
class ServiceListCreateView(ListCreateAPIView):
    queryset = Service.objects.all()
    serializer_class = ServiceSerializer

class ServiceRetrieveUpdateDestroyView(RetrieveUpdateDestroyAPIView):
    queryset = Service.objects.all()
    serializer_class = ServiceSerializer

class ServiceListView(ListAPIView):
    queryset = Service.objects.all()
    serializer_class = ServiceSerializer


# --- services + providers combined (prefetch photos & reviews) ---
class ServiceWithProvidersView(APIView):
    def get(self, request):
        services = (
            Service.objects.prefetch_related(
                Prefetch('providers',
                         queryset=Provider.objects
                         .select_related('service', 'admin')
                         .prefetch_related('photos', 'reviews')
                         .order_by('last_name', 'first_name'))
            )
        )
        serializer = ServiceWithProvidersSerializer(services, many=True)
        return Response(serializer.data)


# --- providers ---
class ProviderListCreateView(ListCreateAPIView):
    serializer_class = ProviderSerializer
    queryset = Provider.objects.select_related('service', 'admin').prefetch_related('photos', 'reviews')
    parser_classes = [MultiPartParser, FormParser]   # handle images

    def get_queryset(self):
        service_name = self.request.query_params.get('service_name')
        admin_id = self.request.query_params.get('admin_id')
        qs = self.queryset
        if service_name:
            qs = qs.filter(service__name__iexact=service_name.strip())
        if admin_id:
            qs = qs.filter(admin__id=admin_id)
        return qs

    def create(self, request, *args, **kwargs):
        data = request.data.copy()
        # Input sugar: allow service_name instead of service_id
        service_name_raw = (data.get('service_name') or '').strip()
        admin_id = data.get('admin_id')
        if not service_name_raw:
            return Response({"error": "service_name is required"}, status=status.HTTP_400_BAD_REQUEST)
        if not admin_id:
            return Response({"error": "admin_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        normalized = ' '.join(service_name_raw.split())
        service = Service.objects.filter(name__iexact=normalized).first() or Service.objects.create(name=normalized)

        admin = Admin.objects.filter(id=admin_id).first()
        if not admin:
            return Response({"error": "Admin not found"}, status=status.HTTP_400_BAD_REQUEST)

        data['service_id'] = service.id
        data['admin'] = admin.id
        data.pop('service_name', None)

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ProviderRetrieveUpdateDestroyView(RetrieveUpdateDestroyAPIView):
    queryset = Provider.objects.select_related('service', 'admin').prefetch_related('photos', 'reviews')
    serializer_class = ProviderSerializer
    parser_classes = [MultiPartParser, FormParser]   # allow updating images


# (Optional) Reviews endpoint to power the “Reviews” tab
class ProviderReviewListCreateView(ListCreateAPIView):
    serializer_class = ProviderReviewSerializer

    def get_queryset(self):
        return ProviderReview.objects.filter(
            provider_id=self.kwargs['provider_id']
        ).order_by('-created_at')

    def perform_create(self, serializer):
        provider = get_object_or_404(Provider, pk=self.kwargs['provider_id'])
        serializer.save(provider=provider)


# Group providers by estate (adminRole) with new fields
# class ServiceProvidersByEstateView(APIView):
#     def get(self, request):
#         services = Service.objects.all()
#         response_data = []
#         for service in services:
#             estate_dict = {}
#             for p in Provider.objects.filter(service=service).select_related('admin'):
#                 estate = getattr(p.admin, 'adminRole', 'Unknown') or "Unknown"
#                 estate_dict.setdefault(estate, []).append({
#                     "id": p.id,
#                     "full_name": f"{p.first_name} {p.last_name}",
#                     "phone": p.phone,
#                     "location": p.location,
#                     "availability": p.availability,
#                     "service": p.service.name,
#                 })
#             response_data.append({
#                 "service_id": service.id,
#                 "service_name": service.name,
#                 "estates": estate_dict
#             })
#         return Response(response_data)

# from collections import defaultdict
from collections import defaultdict
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Provider, Service

class ServiceProvidersByEstateView(APIView):
    """
    GET /api/services-by-estate
    Optional query params:
      - estate=<adminRole>            e.g. Paradise admin, Range-view admin
      - service_name=<string>         e.g. Electrician
      - service_id=<int>              e.g. 3
    """
    def get(self, request):
        estate_q = (request.query_params.get('estate') or '').strip()
        service_name_q = (request.query_params.get('service_name') or '').strip()
        service_id_q = request.query_params.get('service_id')

        # Include bio and profile_picture so we can read them without extra DB hits
        providers_qs = (
            Provider.objects
            .select_related('service', 'admin')
            .only(
                'id', 'first_name', 'last_name', 'phone', 'location', 'availability','skill',
                'bio', 'profile_picture',
                'service__id', 'service__name', 'admin__adminRole'
            )
        )

        if estate_q:
            providers_qs = providers_qs.filter(admin__adminRole__iexact=estate_q)
        if service_name_q:
            providers_qs = providers_qs.filter(service__name__iexact=service_name_q)
        if service_id_q:
            providers_qs = providers_qs.filter(service__id=service_id_q)

        services_map: dict[int, dict] = {}
        estates_map_per_service: dict[int, dict[str, list]] = defaultdict(dict)

        for p in providers_qs:
            s_id = p.service.id
            if s_id not in services_map:
                services_map[s_id] = {
                    "service_id": s_id,
                    "service_name": p.service.name,
                    "estates": {}
                }
                estates_map_per_service[s_id] = defaultdict(list)

            estate_key = (getattr(p.admin, 'adminRole', None) or "Unknown") or "Unknown"

            # Build absolute URL for profile picture (None if not set)
            picture_url = None
            if getattr(p, 'profile_picture', None):
                try:
                    # If storage returns a relative path, make it absolute
                    picture_url = request.build_absolute_uri(p.profile_picture.url)
                except Exception:
                    picture_url = None

            estates_map_per_service[s_id][estate_key].append({
                "id": p.id,
                "full_name": f"{p.first_name} {p.last_name}",
                "phone": p.phone,
                "location": p.location,
                "availability": p.availability,
                "service": p.service.name,
                "bio": p.bio,                              # ← included
                "profile_picture": picture_url,            # ← included
                "skill":p.skill
            })

        response_data = []
        for s_id, base in services_map.items():
            estates_dict = estates_map_per_service[s_id]
            if estate_q:
                filtered = {}
                if estates_dict.get(estate_q):
                    filtered[estate_q] = estates_dict[estate_q]
                base["estates"] = filtered
            else:
                base["estates"] = dict(estates_dict)

            if any(base["estates"].values()):
                response_data.append(base)

        return Response(response_data)

# class ServiceProvidersByEstateView(APIView):
#     """
#     GET /api/services-by-estate
#     Optional query params:
#       - estate=<adminRole>            e.g. Paradise admin, Range-view admin
#       - service_name=<string>         e.g. Electrician
#       - service_id=<int>              e.g. 3
#     """
#     def get(self, request):
#         estate_q = (request.query_params.get('estate') or '').strip()
#         service_name_q = (request.query_params.get('service_name') or '').strip()
#         service_id_q = request.query_params.get('service_id')

#         # Base queryset with needed joins
#         providers_qs = (
#             Provider.objects
#             .select_related('service', 'admin')
#             .only(
#                 'id', 'first_name', 'last_name', 'phone', 'location', 'availability',
#                 'service__id', 'service__name', 'admin__adminRole'
#             )
#         )

#         if estate_q:
#             providers_qs = providers_qs.filter(admin__adminRole__iexact=estate_q)

#         if service_name_q:
#             providers_qs = providers_qs.filter(service__name__iexact=service_name_q)

#         if service_id_q:
#             providers_qs = providers_qs.filter(service__id=service_id_q)

#         # Group by service, then by estate
#         services_map: dict[int, dict] = {}
#         estates_map_per_service: dict[int, dict[str, list]] = defaultdict(dict)

#         for p in providers_qs:
#             s_id = p.service.id
#             if s_id not in services_map:
#                 services_map[s_id] = {
#                     "service_id": s_id,
#                     "service_name": p.service.name,
#                     "estates": {}
#                 }
#                 estates_map_per_service[s_id] = defaultdict(list)

#             estate_key = (getattr(p.admin, 'adminRole', None) or "Unknown") or "Unknown"
#             estates_map_per_service[s_id][estate_key].append({
#                 "id": p.id,
#                 "full_name": f"{p.first_name} {p.last_name}",
#                 "phone": p.phone,
#                 "location": p.location,
#                 "availability": p.availability,
#                 "service": p.service.name,
                
#             })

        # Build response array, optionally keeping only the requested estate
        response_data = []
        for s_id, base in services_map.items():
            estates_dict = estates_map_per_service[s_id]
            if estate_q:
                # When an estate filter is provided, return only that estate (if present)
                filtered = {}
                if estates_dict.get(estate_q):
                    filtered[estate_q] = estates_dict[estate_q]
                # If no providers for that estate, keep empty dict to signal no matches for that service
                base["estates"] = filtered
            else:
                base["estates"] = dict(estates_dict)
            # Only include services that have at least one provider after filtering
            if any(base["estates"].values()):
                response_data.append(base)

        return Response(response_data)

@api_view(['DELETE'])
def delete_admin(request, id):
    try:
        admin = get_object_or_404(Admin, id=id)
        admin.delete()
        return Response({'message': 'Admin deleted successfully'}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'PUT'])
@permission_classes([AllowAny])
def get_update_admin_by_id(request, id):
    try:
        admin = get_object_or_404(Admin, id=id)
        if request.method == 'GET':
            serializer = AdminSerializer(admin)
            return Response(serializer.data)
        elif request.method == 'PUT':
            serializer = AdminSerializer(admin, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
from rest_framework.parsers import MultiPartParser, FormParser

class AlertListCreateView(ListCreateAPIView):
    queryset = Alert.objects.all().order_by('-created_at')
    serializer_class = AlertSerializer
    parser_classes = [MultiPartParser, FormParser]  # Support file uploads

    def get_queryset(self):
        queryset = super().get_queryset()
        estate = self.request.query_params.get('estate', None)
        role = self.request.query_params.get('role', None)
        if estate:
            queryset = queryset.filter(estate__iexact=estate)
        if role:
            queryset = queryset.filter(role__iexact=role)
        return queryset
    
    
from rest_framework.generics import RetrieveUpdateDestroyAPIView

class AlertRetrieveUpdateDestroyView(RetrieveUpdateDestroyAPIView):
    queryset = Alert.objects.all()
    serializer_class = AlertSerializer
    parser_classes = [MultiPartParser, FormParser]  # for file uploads

    # Optionally, override get_queryset() if you want filters, but usually it's by ID.