from django.core.mail import send_mail
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from django.utils import timezone  # Import timezone here
from datetime import timedelta  # Import timedelta here
import random
from .models import OTP
from django.contrib.auth import authenticate  # Import authenticate function
from django.views import View
from django.views.decorators.csrf import ensure_csrf_cookie


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        data = request.data
        try:
            # Create user
            user = get_user_model().objects.create_user(
                username=data['username'],
                password=data['password'],
                email=data['email'],
                first_name=data['first_name'],
                last_name=data['last_name'],
                phone_number=data['phone_number'],
                address=data['address']
            )
            
            # Generate OTP (6-digit OTP)
            otp = random.randint(100000, 999999)  # 6-digit OTP
            
            # Store OTP in OTP model
            otp_instance = OTP.objects.create(
                user=user,
                otp_code=str(otp),
                expires_at=timezone.now() + timedelta(minutes=5)  # Set OTP expiration
            )

            # Send OTP via email
            send_mail(
                'Your OTP Code',
                f'Your OTP code is {otp}',
                'from@example.com',
                [data['email']],
                fail_silently=False,
            )
            
            return Response({"message": "Registration successful. Please check your email for OTP."}, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class VerifyOTPView(APIView):
    permission_classes = [AllowAny]  # Allow any user to access this view

    def post(self, request):
        data = request.data
        username = data.get('username')
        otp_code = data.get('otp')

        # Validate input
        if not username or not otp_code:
            return Response({"error": "Username and OTP are required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Find user by username
            user = get_user_model().objects.get(username=username)

            # Retrieve the most recent OTP for the user
            otp = OTP.objects.filter(user=user).order_by('-created_at').first()

            # If no OTP exists for the user
            if not otp:
                return Response({"error": "No OTP found for this user"}, status=status.HTTP_404_NOT_FOUND)

            # Check if the OTP has expired
            if otp.is_expired():
                return Response({"error": "OTP has expired"}, status=status.HTTP_400_BAD_REQUEST)

            # Verify the OTP
            if otp.otp_code == otp_code:
                # Mark user as verified if OTP is correct
                user.is_verified = True  # Ensure you have an `is_verified` field in CustomUser model
                user.save()

                return Response({"message": "OTP verified successfully!"}, status=status.HTTP_200_OK)
            else:
                return Response({"error": "Invalid OTP"}, status=status.HTTP_400_BAD_REQUEST)

        except get_user_model().DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)


from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.models import User


from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework import status
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()

class LoginView(APIView):
    permission_classes = [AllowAny]  # This allows unauthenticated users to access the view

    def post(self, request):
        data = request.data
        user = authenticate(username=data['username'], password=data['password'])

        if user is not None:
            # Check if the user is a superuser
            if user.is_superuser:
                # Generate JWT tokens for the authenticated superuser
                refresh = RefreshToken.for_user(user)

                # Return the product upload form or a URL for the superuser
                return Response({
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                    
                })
            else:
                # Return JWT tokens for regular users without access to the product upload form
                refresh = RefreshToken.for_user(user)
                return Response({
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                })

        return Response({'error': 'Invalid credentials'}, status=status.HTTP_400_BAD_REQUEST)
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.core.exceptions import PermissionDenied
from django.utils import timezone
from .models import Product
from django.core.exceptions import ValidationError


class ProductUploadView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # Print headers to check if Authorization header is being sent
        print("Authorization header:", request.headers.get('Authorization'))

        # Now, let's check the user
        if not request.user.is_authenticated:
            raise PermissionDenied("Authentication is required.")

        # Check if the user is a superuser
        if not request.user.is_superuser:
            raise PermissionDenied("You must be a superuser to upload products.")

        # Product upload logic...

        # Extract data from the request
        name = request.data.get('name')
        description = request.data.get('description')
        price = request.data.get('price')
        image = request.FILES.get('image')

        # Validate input data
        if not name or not description or not price:
            return Response({"error": "Name, description, and price are required fields."}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            price = float(price)
        except ValueError:
            return Response({"error": "Price must be a valid number."}, status=status.HTTP_400_BAD_REQUEST)

        if price <= 0:
            return Response({"error": "Price must be greater than zero."}, status=status.HTTP_400_BAD_REQUEST)

        # Create the product
        try:
            product = Product.objects.create(
                name=name,
                description=description,
                price=price,
                image=image
            )
        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        # Return success response with product details
        return Response({
            "message": "Product uploaded successfully.",
            "product": {
                "id": product.id,
                "name": product.name,
                "description": product.description,
                "price": product.price,
                "image_url": product.image.url if product.image else None,
                "created_at": product.created_at
            }
        }, status=status.HTTP_201_CREATED)
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

class CheckSuperuserView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.is_superuser:
            return Response({"is_superuser": True}, status=status.HTTP_200_OK)
        return Response({"is_superuser": False}, status=status.HTTP_200_OK)
# app/views.py

from django.shortcuts import render
from .models import Product
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly  # Allows authenticated users to perform actions

class ProductListView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]  # Allow anyone to view, but only authenticated can modify

    def get(self, request):
        products = Product.objects.all()  # Fetch all products
        product_data = [
            {
                'id': product.id,
                'name': product.name,
                'description': product.description,
                'price': product.price,
                'image_url': product.image.url if product.image else None,
                'created_at': product.created_at
            }
            for product in products
        ]
        return Response(product_data)
from django.http import JsonResponse
from django.views import View
from .models import Product  # Replace with your actual model
import json

class UpdateProductView(View):
    permission_classes = [IsAuthenticated]  # Ensure user is authenticated

    def post(self, request, product_id):
        try:
            data = json.loads(request.body)
            product = Product.objects.get(id=product_id)
            product.name = data.get('name', product.name)
            product.price = data.get('price', product.price)
            product.description = data.get('description', product.description)
            product.save()
            return JsonResponse({'success': True, 'message': 'Product updated successfully!'})
        except Product.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Product not found!'}, status=404)
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=500)
from django.http import JsonResponse
from django.views import View
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from rest_framework.permissions import IsAdminUser
from rest_framework.decorators import permission_classes

@method_decorator(login_required, name='dispatch')  # Requires login
@permission_classes([IsAdminUser])  # Requires user to be an admin or superuser
class DeleteProductView(View):
    def delete(self, request, product_id):
        try:
            product = Product.objects.get(id=product_id)
            product.delete()
            return JsonResponse({'success': True, 'message': 'Product deleted successfully!'}, status=204)
        except Product.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Product not found!'}, status=404)
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=500)

@ensure_csrf_cookie
def csrf(request):
    return JsonResponse({'message': 'CSRF cookie set'})
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import InvalidToken
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

class RefreshTokenView(APIView):
    def post(self, request):
        refresh_token = request.data.get('refresh')
        
        # Ensure refresh token is provided
        if not refresh_token:
            return Response({"error": "Refresh token is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Attempt to create a new token from the provided refresh token
            token = RefreshToken(refresh_token)
            new_access_token = str(token.access_token)
            return Response({"access": new_access_token}, status=status.HTTP_200_OK)
        except InvalidToken:
            # Specific error for invalid refresh token
            return Response({"error": "Invalid refresh token"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            # Generic error handling
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
