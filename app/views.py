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
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import AllowAny
from django.contrib.auth.models import User
from rest_framework.permissions import IsAuthenticated
from django.core.exceptions import PermissionDenied
from .models import Product
from django.core.exceptions import ValidationError
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from rest_framework.permissions import IsAdminUser
from rest_framework.decorators import permission_classes
from django.utils.decorators import method_decorator
from .models import Like, Product
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


class CheckSuperuserView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.is_superuser:
            return Response({"is_superuser": True}, status=status.HTTP_200_OK)
        return Response({"is_superuser": False}, status=status.HTTP_200_OK)
# app/views.py


from django.core.paginator import Paginator
from django.http import JsonResponse
from django.views import View
from .models import Product

class ProductListView(View):
    def get(self, request):
        # Fetch all products
        products = Product.objects.all()
        
        # Pagination logic
        page_number = request.GET.get('page', 1)  # Get the page number from request (default to 1)
        page_size = request.GET.get('page_size', 12)  # Get the page size (default to 10 items per page)

        paginator = Paginator(products, page_size)  # Paginate the queryset
        page = paginator.get_page(page_number)  # Get the requested page

        # Prepare product data to send in response
        product_data = []
        for product in page:
            product_data.append({
                'id': product.id,
                'name': product.name,
                'description': product.description,
                'price': float(product.price),  # Convert Decimal to float
                'image_url': request.build_absolute_uri(product.image.url) if product.image else None
            })
        
        # Return paginated response
        return JsonResponse({
            'total_items': paginator.count,
            'total_pages': paginator.num_pages,
            'current_page': page.number,
            'results': product_data  # The paginated results
        })


       
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from app.models import Product
from django.views import View

class ProductDetailView(View):
    def get(self, request, product_id):
        # Fetch the product or return a 404 if not found
        product = get_object_or_404(Product, id=product_id)
        
        # Prepare product data to send back as JSON
        product_data = {
            'id': product.id,
            'name': product.name,
            'description': product.description,
            'price': float(product.price),  # Ensure price is sent as float
            'image_url': request.build_absolute_uri(product.image.url) if product.image else None,
        }
        
        # Return product data as JSON
        return JsonResponse(product_data)

class DeleteProductView(APIView):
    permission_classes = [IsAuthenticated,IsAdminUser]  # Ensure only admins can delete

    def delete(self, request, product_id):
        if not request.user.is_authenticated:
            return JsonResponse({'success': False, 'message': 'Authentication required.'}, status=401)

        if not request.user.is_staff:
            return JsonResponse({'success': False, 'message': 'You do not have permission to delete products.'}, status=403)

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
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Product, Like  # Import your models

class LikeProductView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, product_id):
        """Fetch the like count and check if the user has liked the product."""
        try:
            product = Product.objects.get(id=product_id)
            like_count = product.likes.count()
            user_liked = Like.objects.filter(user=request.user, product=product).exists()
            return Response({"likes": like_count, "user_liked": user_liked}, status=status.HTTP_200_OK)
        except Product.DoesNotExist:
            return Response({"message": "Product not found."}, status=status.HTTP_404_NOT_FOUND)

    def post(self, request, product_id):
        """Handle liking and unliking the product."""
        try:
            user = request.user
            product = Product.objects.get(id=product_id)

            # Check if the user already liked the product
            existing_like = Like.objects.filter(user=user, product=product).first()
            if existing_like:
                # If a like exists, delete it (unlike the product)
                existing_like.delete()
                like_count = product.likes.count()
                return Response({"likes": like_count, "user_liked": False}, status=status.HTTP_200_OK)
            
            # Otherwise, create a new like
            Like.objects.create(user=user, product=product)
            like_count = product.likes.count()
            return Response({"likes": like_count, "user_liked": True}, status=status.HTTP_201_CREATED)

        except Product.DoesNotExist:
            return Response({"message": "Product not found."}, status=status.HTTP_404_NOT_FOUND)
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views import View
from django.core.exceptions import ObjectDoesNotExist
from .models import Product
from django.core.files.storage import default_storage
from django.http import JsonResponse
from django.views import View
from django.core.exceptions import ObjectDoesNotExist
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from app.models import Product  # Import your Product model correctly

class UpdateProductView(View):
    def put(self, request, id):
        try:
            product = Product.objects.get(id=id)
            name = request.POST.get("name")
            description = request.POST.get("description")
            price = request.POST.get("price")
            image = request.FILES.get("image")

            if not name or not description or not price:
                return JsonResponse({"error": "Missing required fields"}, status=400)

            product.name = name
            product.description = description
            product.price = price
            if image:
                product.image = image

            product.save()
            return JsonResponse({"message": "Product updated successfully"}, status=200)
        except Product.DoesNotExist:
            return JsonResponse({"error": "Product not found"}, status=404)
from django.http import JsonResponse
from django.views import View
from django.shortcuts import get_object_or_404
from .models import Product, Cart, CartItem
from django.contrib.auth.mixins import LoginRequiredMixin

from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from django.http import JsonResponse
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Product, Cart, CartItem
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework.permissions import IsAuthenticated
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.mixins import AccessMixin
from .models import Product, Cart, CartItem
from rest_framework_simplejwt.authentication import JWTAuthentication


from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

class AddToCartView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, product_id):
        product = get_object_or_404(Product, id=product_id)
        cart, _ = Cart.objects.get_or_create(user=request.user)
        cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)
        
        if not created:
            cart_item.quantity += 1
            cart_item.save()
        
        return Response({
            "success": True,
            "message": f"Added {product.name} to your cart.",
            "cart_quantity": cart_item.quantity,
        })

from django.shortcuts import render, get_object_or_404
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Cart, CartItem

from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication
from .models import Cart, CartItem

class CartView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            cart = request.user.cart  # Assuming a OneToOne relationship between User and Cart
            cart_items = CartItem.objects.filter(cart=cart).select_related('product')
            total_price = sum(item.product.price * item.quantity for item in cart_items)

            data = {
                'cart_items': [
                    {
                        'id': item.id,
                        'product': {
                            'id': item.product.id,
                            'name': item.product.name,
                            'price': item.product.price,
                        },
                        'quantity': item.quantity,
                        'subtotal': item.product.price * item.quantity,
                    }
                    for item in cart_items
                ],
                'total_price': total_price,
            }
            return Response(data)
        except Cart.DoesNotExist:
            return Response({'error': 'Cart not found.'}, status=404)

from django.http import JsonResponse
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Cart

class CartCountView(LoginRequiredMixin, View):
    def get(self, request):
        try:
            # Retrieve the user's cart
            cart = request.user.cart  # Assuming each user has a cart related to them
            cart_count = cart.cartitem_set.count()  # Count the number of items in the user's cart
        except Cart.DoesNotExist:
            # If the user does not have a cart, return count as 0
            cart_count = 0

        return JsonResponse({'cart_count': cart_count})
