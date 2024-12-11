from django.core.mail import send_mail
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from django.utils import timezone  # Import timezone here
from datetime import timedelta  # Import timedelta here
import random
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
import json
from .models import Category
from django.http import JsonResponse
from django.views import View
from django.shortcuts import get_object_or_404
from .models import Product, Cart, CartItem
from django.contrib.auth.mixins import LoginRequiredMixin
from rest_framework.authentication import TokenAuthentication
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.core.paginator import Paginator
from django.views.decorators.csrf import ensure_csrf_cookie
from django.db.models import Sum
from .models import Product, Like
from rest_framework.permissions import IsAuthenticated
from rest_framework.permissions import IsAdminUser
from .models import OTP

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
        print("Authorization header:", request.headers.get('Authorization'))  # Debugging authorization
        print("Request data:", request.data)  # Debugging data sent in the request

        # Check if the user is authenticated
        if not request.user.is_authenticated:
            raise PermissionDenied("Authentication is required.")
        
        # Check if the user is a superuser
        if not request.user.is_superuser:
            raise PermissionDenied("You must be a superuser to upload products.")

        # Extract and validate fields
        name = request.data.get('name')
        description = request.data.get('description')
        price = request.data.get('price')
        category_id = request.data.get('category')  # Category field
        image = request.FILES.get('image')

        if not name or not description or not price or not category_id:
            return Response({"error": "Name, description, price, and category are required fields."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            price = float(price)
        except ValueError:
            return Response({"error": "Price must be a valid number."}, status=status.HTTP_400_BAD_REQUEST)

        if price <= 0:
            return Response({"error": "Price must be greater than zero."}, status=status.HTTP_400_BAD_REQUEST)

        # Validate category
        try:
            category = Category.objects.get(id=category_id)
        except Category.DoesNotExist:
            return Response({"error": "Category not found."}, status=status.HTTP_400_BAD_REQUEST)

        # Create the product
        try:
            product = Product.objects.create(
                name=name,
                description=description,
                price=price,
                category=category,  # Adding category to the product
                image=image
            )
        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            "message": "Product uploaded successfully.",
            "product": {
                "id": product.id,
                "name": product.name,
                "description": product.description,
                "price": product.price,
                "category": product.category.name,
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
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.views import View
from .models import Product

from django.core.paginator import Paginator, EmptyPage
from django.http import JsonResponse
from .models import Product, Category

class ProductListView(View):
    def get(self, request):
        # Fetch all products
        products = Product.objects.all()

        # Filter by category if provided
        category_id = request.GET.get('category')
        if category_id:
            if not Category.objects.filter(id=category_id).exists():
                return JsonResponse({'error': 'Invalid category ID'}, status=400)
            products = products.filter(category_id=category_id)
        
        # Pagination logic
        try:
            page_number = int(request.GET.get('page', 1))  # Default to page 1
            page_size = int(request.GET.get('page_size', 12))  # Default to 12 items per page
        except ValueError:
            return JsonResponse({'error': 'Invalid page or page_size parameter'}, status=400)

        paginator = Paginator(products, page_size)
        try:
            page = paginator.get_page(page_number)
        except EmptyPage:
            return JsonResponse({'error': 'Page not found'}, status=404)

        # Prepare product data for response
        product_data = [
            {
                'id': product.id,
                'name': product.name,
                'description': product.description,
                'price': float(product.price),
                'image_url': request.build_absolute_uri(product.image.url) if product.image else None,
                'category': {
                    'id': product.category.id,
                    'name': product.category.name
                } if product.category else None
            }
            for product in page
        ]

        # Return paginated response
        return JsonResponse({
            'total_items': paginator.count,
            'total_pages': paginator.num_pages,
            'current_page': page.number,
            'results': product_data
        })

from django.http import JsonResponse
from django.views import View
from django.shortcuts import get_object_or_404
from .models import Product, Cart, CartItem
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

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

    @method_decorator(csrf_exempt)  # Exempting CSRF for simplicity, you may want to handle it differently
    def post(self, request, product_id):
        # Handle add-to-cart, increase, or decrease quantity
        
        action = request.POST.get('action')  # The action can be 'increase' or 'decrease'
        quantity_change = int(request.POST.get('quantity', 1))  # The quantity to update

        # Fetch the product to update cart item
        product = get_object_or_404(Product, id=product_id)
        
        # Get or create the user's cart
        cart, created = Cart.objects.get_or_create(user=request.user)
        
        # Get the cart item for this product, if it exists
        cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)
        
        # Handle increasing or decreasing quantity
        if action == 'increase':
            cart_item.quantity += quantity_change
        elif action == 'decrease' and cart_item.quantity > 1:
            cart_item.quantity -= quantity_change
        else:
            return JsonResponse({"error": "Cannot decrease quantity below 1."}, status=400)

        # Save the updated cart item
        cart_item.save()

        # Return updated cart information
        return JsonResponse({
            "message": "Cart updated successfully.",
            "cart_item": {
                "product_id": cart_item.product.id,
                "name": cart_item.product.name,
                "quantity": cart_item.quantity,
                "subtotal": cart_item.product.price * cart_item.quantity,
            },
        })


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
@method_decorator(csrf_exempt, name='dispatch')  # Disable CSRF if using token authentication
class UpdateProductView(View):

    def get(self, request, id):
        try:
            # Fetch product details
            product = Product.objects.get(id=id)
            return JsonResponse({
                'id': product.id,
                'name': product.name,
                'description': product.description,
                'price': product.price,
                'image_url': product.image.url if product.image else None,
            })
        except Product.DoesNotExist:
            return JsonResponse({"error": "Product not found"}, status=404)
    
    def put(self, request, id):
        try:
            # Fetch the product by ID
            product = Product.objects.get(id=id)

            # Parse the data from the request body
            data = json.loads(request.body)
            name = data.get('name')
            description = data.get('description')
            price = data.get('price')
            image = data.get('image')  # Assuming image is sent as URL or base64 string

            # Validate fields
            if not name or not description or not price:
                return JsonResponse({"error": "All fields are required."}, status=400)

            # Parse the price into a float
            try:
                price = float(price)
            except ValueError:
                return JsonResponse({"error": "Invalid price format"}, status=400)

            # Update product details
            product.name = name
            product.description = description
            product.price = price

            # Handling image if it's uploaded (if image is a file, it will be in request.FILES)
            if 'image' in request.FILES:
                product.image = request.FILES['image']
            
            product.save()

            return JsonResponse({"message": "Product updated successfully"}, status=200)

        except Product.DoesNotExist:
            return JsonResponse({"error": "Product not found"}, status=404)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON format in the request body"}, status=400)
        except Exception as e:
            return JsonResponse({"error": f"An error occurred: {str(e)}"}, status=500)

class AddToCartView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, product_id):
        # Ensure the user is authenticated
        if not request.user.is_authenticated:
            return Response({
                "success": False,
                "message": "You must be logged in to add products to the cart."
            }, status=401)  # Unauthorized error if not logged in
        
        product = get_object_or_404(Product, id=product_id)
        cart, _ = Cart.objects.get_or_create(user=request.user)  # Create or get the user's cart
        
        # Add product to cart
        cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)
        
        if not created:
            cart_item.quantity += 1
            cart_item.save()

        # Return the updated cart quantity
        return Response({
            "success": True,
            "message": f"Added {product.name} to your cart.",
            "cart_quantity": cart_item.quantity,
        })

class CartView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            # Ensure the cart exists for the user
            cart, created = Cart.objects.get_or_create(user=request.user)

            # Fetch cart items
            cart_items = CartItem.objects.filter(cart=cart).select_related('product')

            if not cart_items:
                return Response({'message': 'No items in your cart.'}, status=200)

            # Calculate total price
            total_price = sum(item.product.price * item.quantity for item in cart_items)

            data = {
                'cart_items': [
                    {
                        'id': item.id,
                        'product': {
                            'id': item.product.id,
                            'name': item.product.name,
                            'price': item.product.price,
                            'image': request.build_absolute_uri(item.product.image.url),  # Construct full URL for image
                        },
                        'quantity': item.quantity,
                        'subtotal': item.product.price * item.quantity,
                    }
                    for item in cart_items
                ],
                'total_price': total_price,
            }
            return Response(data)

        except Exception as e:
            return Response({'error': str(e)}, status=500)

class IncreaseQuantity(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, item_id):
        try:
            # Get the cart item by ID and ensure it belongs to the current user
            cart_item = CartItem.objects.get(id=item_id, cart__user=request.user)

            # Increase the quantity
            cart_item.quantity += 1
            cart_item.save()

            # Optionally, return updated cart data
            cart, created = Cart.objects.get_or_create(user=request.user)
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
                            'image': request.build_absolute_uri(item.product.image.url),
                        },
                        'quantity': item.quantity,
                        'subtotal': item.product.price * item.quantity,
                    }
                    for item in cart_items
                ],
                'total_price': total_price,
            }

            return Response(data, status=200)
        except CartItem.DoesNotExist:
            return Response({'error': 'Item not found'}, status=404)


class DecreaseQuantity(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, item_id):
        try:
            # Get the cart item by ID and ensure it belongs to the current user
            cart_item = CartItem.objects.get(id=item_id, cart__user=request.user)

            # Decrease the quantity if it's greater than 1
            if cart_item.quantity > 1:
                cart_item.quantity -= 1
                cart_item.save()

                # Fetch the updated cart items and total price for the logged-in user
                cart = cart_item.cart
                cart_items = CartItem.objects.filter(cart=cart).select_related('product')
                total_price = sum(item.product.price * item.quantity for item in cart_items)

                # Prepare the response with updated cart items and total price
                data = {
                    'cart_items': [
                        {
                            'id': item.id,
                            'product': {
                                'id': item.product.id,
                                'name': item.product.name,
                                'price': item.product.price,
                                'image': request.build_absolute_uri(item.product.image.url),
                            },
                            'quantity': item.quantity,
                            'subtotal': item.product.price * item.quantity,
                        }
                        for item in cart_items
                    ],
                    'total_price': total_price,
                }

                return Response(data, status=200)
            else:
                return Response({'error': 'Cannot decrease quantity below 1'}, status=400)
        except CartItem.DoesNotExist:
            return Response({'error': 'Item not found'}, status=404)

from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import CartItem

class RemoveItem(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, item_id):
        try:
            # Get the cart item by ID
            cart_item = CartItem.objects.get(id=item_id)

            # Ensure that the cart item belongs to the current user
            if cart_item.cart.user != request.user:
                return Response({'error': 'You do not own this item'}, status=403)

            # Remove the item from the cart
            cart_item.delete()

            # Fetch the updated cart items and total price for the logged-in user
            cart_items = CartItem.objects.filter(cart__user=request.user)
            total_price = sum(item.total_price() for item in cart_items)

            # Prepare the response with updated cart items and total price
            return Response({
                'cart_items': [item.to_dict() for item in cart_items],
                'total_price': total_price
            }, status=200)

        except CartItem.DoesNotExist:
            return Response({'error': 'Item not found'}, status=404)


class CartCountView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not request.user.is_authenticated:
            return JsonResponse({
                'success': False,
                'message': 'You must be logged in to view the cart count.'
            }, status=401)

        try:
            cart = Cart.objects.get(user=request.user)
            cart_count = cart.cartitem_set.count()  # Count the number of items in the cart
        except Cart.DoesNotExist:
            cart_count = 0  # No cart found for the user

        return JsonResponse({'cart_count': cart_count})
class LikedProductsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Fetch all products liked by the authenticated user without using a serializer."""
        user = request.user
        liked_products = Product.objects.filter(likes__user=user)  # Use 'likes' for the reverse relationship

        # Prepare the list of liked products as dictionaries
        product_list = []
        for product in liked_products:
            product_data = {
                'id': product.id,
                'name': product.name,
                'description': product.description,
                'price': str(product.price),  # Ensure price is converted to a string for JSON response
                'image_url': product.image.url if product.image else None,  # Get the URL of the image if it exists
                'likes_count': product.likes.count(),  # Number of likes for the product
            }
            product_list.append(product_data)

        return Response(product_list, status=status.HTTP_200_OK)

class CategoryListView(APIView):
    def get(self, request):
        categories = Category.objects.all()
        categories_data = [{"id": category.id, "name": category.name} for category in categories]
        return Response(categories_data, status=status.HTTP_200_OK)
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from .models import Cart, CartItem, Order, OrderItem
from .models import Product  # Assuming you have a Product model
from django.utils import timezone


class CheckoutAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # Extract data from the request
        address = request.data.get('address')
        phone_number = request.data.get('phone_number')
        payment_method = request.data.get('payment_method')  # Payment option
        product_id = request.data.get('product_id')  # For "Buy Now" specific product

        if not address or not phone_number or not payment_method:
            return Response(
                {'error': 'Address, phone number, and payment method are required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Initialize variables
        total_price = 0
        cart_items = None

        if product_id:
            # Handle "Buy Now" for a specific product
            try:
                product = Product.objects.get(id=product_id)
                total_price = product.price  # Only calculate the price for this product
                cart_items = [{'product': product, 'quantity': 1}]  # Single product checkout
            except Product.DoesNotExist:
                return Response({'error': 'Product not found.'}, status=status.HTTP_404_NOT_FOUND)
        else:
            # Handle Cart Checkout (all items in cart)
            try:
                cart = Cart.objects.get(user=request.user)
                cart_items = CartItem.objects.filter(cart=cart)
                if not cart_items.exists():
                    return Response({'error': 'Cart is empty.'}, status=status.HTTP_400_BAD_REQUEST)
                total_price = sum(item.product.price * item.quantity for item in cart_items)
            except Cart.DoesNotExist:
                return Response({'error': 'Cart not found.'}, status=status.HTTP_404_NOT_FOUND)

        # Create the order
        order = Order.objects.create(
            user=request.user,
            total_price=total_price,
            address=address,
            phone_number=phone_number,
            payment_method=payment_method,
            status='Pending',
            ordered_at=timezone.now(),
        )

        # Create order items (only the selected product for "Buy Now", or all items in cart)
        for item in cart_items:
            # Accessing CartItem attributes using dot notation
            OrderItem.objects.create(
                order=order,
                product=item.product,  # Access product using dot notation
                quantity=item.quantity,  # Access quantity using dot notation
                price=item.product.price,
            )
        # Return the order ID in the response
        return Response(
            {'order_id': order.id, 'message': 'Checkout successful.'},
            status=status.HTTP_201_CREATED
        )



from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .models import Order

class OrderConfirmationAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            print(f"User: {request.user}, Order ID: {pk}")
            # Ensure the user can only access their own orders
            order = Order.objects.get(id=pk, user=request.user)
        except Order.DoesNotExist:
            return Response({'error': 'Order not found.'}, status=status.HTTP_404_NOT_FOUND)

        # Serialize the order details
        order_data = {
            'id': order.id,
            'total_price': order.total_price,
            'address': order.address,
            'phone_number': order.phone_number,
            'status': order.status,
            'ordered_at': order.ordered_at,
            'items': [
                {
                    'product': item.product.name,
                    'quantity': item.quantity,
                    'price': item.price,
                }
                for item in order.order_items.all()  # Use the correct related name
            ],
        }

        return Response(order_data, status=status.HTTP_200_OK)
from io import BytesIO
from django.http import HttpResponse
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from .models import Order
from django.contrib.auth.models import User

class InvoiceAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            # Fetch the order for the current user
            order = Order.objects.get(id=pk, user=request.user)
        except Order.DoesNotExist:
            return HttpResponse('Order not found', status=404)

        # Create PDF in memory using BytesIO
        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=letter)

        # Add Order Details to the PDF
        c.drawString(100, 750, f"Invoice for Order ID: {order.id}")
        c.drawString(100, 730, f"Date: {order.ordered_at.strftime('%Y-%m-%d %H:%M:%S')}")
        c.drawString(100, 710, f"Total Price: ${order.total_price}")
        c.drawString(100, 690, f"Shipping Address: {order.address}")
        c.drawString(100, 670, f"Phone Number: {order.phone_number}")

        # Add Order Items to the PDF
        y_position = 650
        for item in order.order_items.all():
            c.drawString(100, y_position, f"Product: {item.product.name}, Quantity: {item.quantity}, Price: {item.price}")
            y_position -= 20

        # Close the canvas and save PDF
        c.showPage()
        c.save()

        # Move to the start of the BytesIO buffer
        buffer.seek(0)

        # Return the PDF as an HttpResponse
        response = HttpResponse(buffer, content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="invoice_{order.id}.pdf"'
        return response
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.core.mail import EmailMessage
from django.conf import settings
import os

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.core.mail import EmailMessage
from django.conf import settings
import os

class SendInvoiceEmailView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, order_id):
        # Get the authenticated user's email
        user_email = request.user.email

        # Generate the file path for the invoice
        invoice_path = f'{settings.MEDIA_ROOT}/invoices/Invoice_{order_id}.pdf'

        # Check if the invoice file exists
        if not os.path.exists(invoice_path):
            return Response({'error': 'Invoice file not found'}, status=404)

        try:
            # Send the email with the invoice
            email = EmailMessage(
                subject=f'Invoice for Order {order_id}',
                body='Please find your invoice attached.',
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[user_email],
            )
            email.attach_file(invoice_path)
            email.send()

            return Response({'success': 'Invoice sent successfully'}, status=200)
        except Exception as e:
            return Response({'error': f'Failed to send invoice: {str(e)}'}, status=500)
from django.contrib.auth import get_user_model
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

User = get_user_model()  # Get the custom user model

class ProfileView(APIView):
    """
    Handles fetching and updating user profiles.
    Users can edit all fields except the username.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Fetch the current user's profile data.
        """
        user = request.user
        user_data = {
            'username': user.username,  # Username is read-only
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'phone_number': getattr(user, 'phone_number', None),
            'address': getattr(user, 'address', None),
        }
        return Response(user_data, status=200)

    def put(self, request):
        """
        Update the current user's profile data, excluding the username.
        """
        user = request.user
        data = request.data

        # Update fields except for username
        user.email = data.get('email', user.email)
        user.first_name = data.get('first_name', user.first_name)
        user.last_name = data.get('last_name', user.last_name)
        user.phone_number = data.get('phone_number', getattr(user, 'phone_number', None))
        user.address = data.get('address', getattr(user, 'address', None))
        
        user.save()

        return Response({"success": "Profile updated successfully"}, status=200)
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from .models import Order, Rating

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .models import Order, Rating

class RateOrderAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, order_id):
        # Extract review and comment from the request
        review = request.data.get('review')
        comment = request.data.get('comment')

        if not review or not comment:
            return Response({'error': 'Review and comment are required.'}, status=status.HTTP_400_BAD_REQUEST)

        if review not in dict(Rating.REVIEW_CHOICES).keys():
            return Response({'error': 'Invalid review value.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            order = Order.objects.get(id=order_id, user=request.user)
        except Order.DoesNotExist:
            return Response({'error': 'Order not found.'}, status=status.HTTP_404_NOT_FOUND)

        # Check if the user has already rated this order
        existing_rating = Rating.objects.filter(order=order, user=request.user).first()
        if existing_rating:
            return Response({'error': 'You have already rated this order.'}, status=status.HTTP_400_BAD_REQUEST)

        # Create a new rating entry
        Rating.objects.create(
            order=order,
            user=request.user,
            review=review,
            comment=comment,
        )

        return Response({'message': 'Rating submitted successfully.'}, status=status.HTTP_201_CREATED)
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.views.generic import View
from .models import Order

class OrderHistoryView(APIView):
    def get(self, request, *args, **kwargs):
        """
        This function retrieves the orders for the logged-in user
        and returns the data as a JSON response.
        """
        orders = Order.objects.filter(user=request.user).order_by('-ordered_at')  # Use 'ordered_at' for order date
        order_data = [
            {
                'id': order.id,
                'order_date': order.ordered_at,  # 'ordered_at' is the correct field for order date
                'total_amount': str(order.total_price),  # Use 'total_price' for total amount
                'order_status': order.status,  # Use 'status' for order status
            }
            for order in orders
        ]
        return JsonResponse({'orders': order_data})
