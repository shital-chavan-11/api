from django.db import models
from django.utils import timezone
from django.contrib.auth.models import AbstractUser
import random
from datetime import timedelta
from django.conf import settings

# Category model definition
class Category(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

# Product model to represent a product
class Product(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to='product_images/', blank=True, null=True)
    category = models.ForeignKey(Category, related_name="products", on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

# Custom user model
class CustomUser(AbstractUser):
    phone_number = models.CharField(max_length=15)
    address = models.TextField()
    email = models.EmailField(unique=True)  # Ensure email is unique

# OTP model for verification
class OTP(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    otp_code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    def is_expired(self):
        return timezone.now() > self.expires_at

    @classmethod
    def generate_otp(cls, user):
        otp_code = str(random.randint(100000, 999999))  # Generate 6-digit OTP
        expires_at = timezone.now() + timedelta(minutes=5)  # OTP valid for 5 minutes
        otp = OTP(user=user, otp_code=otp_code, expires_at=expires_at)
        otp.save()
        return otp

# Like model to represent user likes on products
class Like(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="likes")
    created_at = models.DateTimeField(auto_now_add=True)

# Cart model to represent the user's cart
class Cart(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)  # Link to your custom user model
    created_at = models.DateTimeField(default=timezone.now)  # Use timezone.now for the default value
    updated_at = models.DateTimeField(auto_now=True)  # Automatically updates timestamp when the cart is modified

# CartItem model to represent items in the cart
class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE)  # Links to the user's cart
    product = models.ForeignKey(Product, on_delete=models.CASCADE)  # Links to a product
    quantity = models.PositiveIntegerField(default=1)  # Quantity of the product in the cart

    def __str__(self):
        return f"{self.quantity} x {self.product.name} in cart"

    def total_price(self):
        return self.product.price * self.quantity  # Calculate total price of this cart item

class Order(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Paid', 'Paid'),
        ('Shipped', 'Shipped'),
        ('Completed', 'Completed'),
        ('Cancelled', 'Cancelled'),
    ]

    PAYMENT_METHOD_CHOICES = [
        ('Credit Card', 'Credit Card'),
        ('PayPal', 'PayPal'),
        ('Cash on Delivery', 'Cash on Delivery'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)  # User who placed the order
    total_price = models.DecimalField(max_digits=10, decimal_places=2)  # Total price of the order
    address = models.TextField()  # Shipping address for the order
    phone_number = models.CharField(max_length=15)  # Contact number of the user
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')  # Current status of the order
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default='Credit Card')  # Payment method
    ordered_at = models.DateTimeField(auto_now_add=True)  # Timestamp when the order was placed

    def __str__(self):
        return f"Order {self.id} by {self.user.username} with {self.payment_method}"


# OrderItem model to represent the products in an order (many-to-many relationship)
class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='order_items')  # Link to the order
    product = models.ForeignKey(Product, on_delete=models.CASCADE)  # Product in the order
    quantity = models.PositiveIntegerField()  # Quantity of the product in the order
    price = models.DecimalField(max_digits=10, decimal_places=2)  # Price of the product at the time of order
    
    def __str__(self):
        return f"{self.product.name} (x{self.quantity})"
class Profile(models.Model):
    """
    Model to store additional user profile information without a photo.
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='profile'  # Allows user.profile to access the profile
    )
    phone_number = models.CharField(max_length=15, blank=True, null=True)  # Optional phone number
    address = models.TextField(blank=True, null=True)  # Optional address

    def __str__(self):
        return f"{self.user.username}'s Profile"
from django.db import models
from django.contrib.auth.models import User
from .models import Product, Order

class Rating(models.Model):
    REVIEW_CHOICES = [
        ('Excellent', 'Excellent'),
        ('Very Good', 'Very Good'),
        ('Good', 'Good'),
        ('Average', 'Average'),
        ('Poor', 'Poor'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    review = models.CharField(max_length=20, choices=REVIEW_CHOICES)
    comment = models.TextField()  # Additional comments by the user

    def __str__(self):
        return f"Rating for {self.product.name} by {self.user.username}"
