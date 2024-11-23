from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from datetime import timedelta
import random
from django.conf import settings
from django.contrib.auth import get_user_model

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

# Product model to represent a product
class Product(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to='product_images/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

# Like model to represent user likes on products
class Like(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="likes")
    created_at = models.DateTimeField(auto_now_add=True)
from django.db import models
from django.utils import timezone

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
