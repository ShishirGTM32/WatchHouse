from django.contrib.auth.models import AbstractUser
from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import RegexValidator
from django.db.models import Sum, F

# User = get_user_model()
# Type Model
class Type(models.Model):
    type_id = models.AutoField(primary_key=True)
    type_name = models.CharField(max_length=100, help_text="Name of the watch type")

    def __str__(self):
        return self.type_name


# Brand Model
class Brand(models.Model):
    brand_id = models.AutoField(primary_key=True)
    brand_name = models.CharField(max_length=100, help_text="Name of the brand")

    def __str__(self):
        return self.brand_name


# Gender Model
class Gender(models.Model):
    gender_id = models.AutoField(primary_key=True)
    gender_name = models.CharField(max_length=100, help_text="Name of the gender")

    def __str__(self):
        return self.gender_name

# Watch Model
class Watch(models.Model):
    watch_id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=50)
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE)
    image_url = models.URLField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    gender = models.ForeignKey(Gender, on_delete=models.CASCADE)
    type = models.ForeignKey(Type, on_delete=models.CASCADE)

    def __str__(self):
        return (
            f"Watch: {self.title}, "
            f"Brand: {self.brand.brand_name}, "
            f"Price: ${self.price:.2f}, "
            f"Image URL: {self.image_url}, "
            f"Gender: {self.gender.gender_name}, "
            f"Type: {self.type.type_name}"
        )
    
# Contact Model
class Contact(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    message = models.TextField()

    def __str__(self):
        return f'{self.first_name} {self.last_name} ({self.email})'

# Custom User Model
class User(AbstractUser):
    # Add custom fields for the user model here if needed
    email = models.EmailField(unique=True)

    groups = models.ManyToManyField(
        'auth.Group',
        related_name='ecommerce_user_groups',  # Custom related_name
        blank=True,
        help_text="The groups this user belongs to.",
        verbose_name="groups",
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='ecommerce_user_permissions',  # Custom related_name
        blank=True,
        help_text="Specific permissions for this user.",
        verbose_name="user permissions",
    )

    def __str__(self):
        return self.username

    class Meta:
        db_table = 'ecommerce_user'

# Order Model
class Order(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Paid', 'Paid'),
        ('Shipped', 'Shipped'),
        ('Delivered', 'Delivered'),
        ('Cancelled', 'Cancelled'),
    ]

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    shipping_address = models.TextField()
    shipping_city = models.CharField(max_length=255)
    shipping_postal_code = models.CharField(max_length=20)
    shipping_country = models.CharField(max_length=255)
    email = models.EmailField()
    payment_method = models.CharField(max_length=255, default='Stripe')
    phone_number = models.CharField(max_length=20, null=True, blank=True)
    stripe_receipt_url = models.URLField(blank=True, null=True)

    def get_total_order_price(self):
        return sum(item.get_total_price() for item in self.order_items.all())

    def __str__(self):
        return f"Order #{self.id} by {self.user}"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='order_items', on_delete=models.CASCADE)
    product = models.ForeignKey(Watch, on_delete=models.SET_NULL, null=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.quantity} x {self.product.title}"

    def get_total_price(self):
        return self.price * self.quantity

# class Cart(models.Model):
#     user = models.OneToOneField(User, on_delete=models.CASCADE)
#     created_at = models.DateTimeField(auto_now_add=True)

#     def __str__(self):
#         return f"Cart for {self.user.username}"

#     def get_total_price(self):
#         # Annotate each CartItem with its total price (quantity * price of the watch) 
#         return self.items.annotate(
#             total_item_price=F('quantity') * F('watch__price')).aggregate(total_price=Sum('total_item_price'))['total_price'] or 0.00

#     def remove_item(self, cart_item_id):
#         try:
#             cart_item = self.items.get(id=cart_item_id)
#             cart_item.delete()
#         except CartItem.DoesNotExist:
#             return None

# class CartItem(models.Model):
#     cart = models.ForeignKey(Cart, related_name='items', on_delete=models.CASCADE)
#     watch = models.ForeignKey('Watch', on_delete=models.CASCADE)  # ForeignKey to Watch model
#     quantity = models.PositiveIntegerField(default=1)

#     @property
#     def total_price(self):
#         return self.watch.price * self.quantity if self.watch else 0

#     def __str__(self):
#         return f"{self.watch.title} (x{self.quantity})"
