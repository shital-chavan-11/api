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
                    'product_upload_form': 'URL_TO_PRODUCT_UPLOAD_FORM'  # Provide URL or form details here
                })
            else:
                # Return JWT tokens for regular users without access to the product upload form
                refresh = RefreshToken.for_user(user)
                return Response({
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                })

        return Response({'error': 'Invalid credentials'}, status=status.HTTP_400_BAD_REQUEST)
