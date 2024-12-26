import stripe, json
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, TemplateView, View, FormView, UpdateView, DetailView
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth import login, logout
from django.http import HttpResponse, JsonResponse, Http404
from django.urls import reverse_lazy, reverse
from django.contrib.auth.views import LoginView, PasswordResetConfirmView
from django.core.mail import send_mail
from django.contrib import messages
from django.conf import settings
from django.utils.functional import SimpleLazyObject 
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Watch, Order, OrderItem, Brand, Type, Gender
from .forms import CustomUserCreationForm, ContactForm, CheckoutForm
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.db.models import Sum
from django.contrib.auth import get_user_model
from urllib.parse import urlencode
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

User = get_user_model()

stripe.api_key = settings.STRIPE_SECRET_KEY

# Authentication Views
class CustomLoginView(LoginView):
    template_name = 'login.html'
    redirect_authenticated_user = True

    def get_success_url(self):
        return reverse_lazy('account')

class RegisterPage(View):
    def get(self, request):
        if request.user.is_authenticated:
            return redirect('account')

        form = CustomUserCreationForm()
        return render(request, 'register.html', {'form': form})

    def post(self, request):
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('Home')
        return render(request, 'register.html', {'form': form})

class CustomLogoutView(View):
    def get(self, request):
        logout(request)
        return redirect('LogIn')

class PasswordResetRequestView(View):
    def get(self, request):
        form = PasswordResetForm()
        return render(request, 'password_reset.html', {'form': form})

    def post(self, request):
        form = PasswordResetForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            associated_users = User.objects.filter(email=email)
            if associated_users.exists():
                for users in associated_users:
                    subject = "Password Reset Requested"
                    email_template_name = "password_reset_email.txt"
                    domain = get_current_site(request).domain
                    context = {
                        "email": users.email,
                        'domain': domain,
                        'site_name': 'WatchHouse',
                        "uid": urlsafe_base64_encode(force_bytes(users.pk)),
                        "token": default_token_generator.make_token(users),
                        "username": users.username,
                    }
                    email_content = render_to_string(email_template_name, context)
                    try:
                        send_mail(subject, email_content, 'your_email@example.com', [users.email], fail_silently=False)
                    except Exception as e:
                        messages.error(request, f"Error sending email: {str(e)}")
                        return render(request, 'password_reset.html', {'form': form})
                messages.success(request, "Password reset email sent successfully!")
                return redirect("password_reset_done")
            else:
                messages.error(request, "No user is associated with this email address.")
        return render(request, 'password_reset.html', {'form': form})

# Home view (show some watches)
class Home(ListView):
    template_name = 'index.html'
    model = Watch
    context_object_name = 'watches'

    def get_queryset(self):
        return Watch.objects.all()[:9] 

class AboutView(TemplateView):
    template_name = 'about.html'

class ContactView(FormView):
    template_name = 'contact.html'
    form_class = ContactForm
    success_url = reverse_lazy('contact_thank_you')

    def form_valid(self, form):        
        first_name = form.cleaned_data['first_name']
        last_name = form.cleaned_data['last_name']
        email = form.cleaned_data['email']
        message = form.cleaned_data['message']

        send_mail(
            subject=f'Contact Form Submission from {first_name} {last_name}',
            message=message,
            from_email=email,
            recipient_list=['your_email@example.com'],
            fail_silently=False,
        )

        return super().form_valid(form)

    def form_invalid(self, form):
        return super().form_invalid(form)

class OrderConfirmationView(View):
    def get(self, request, order_id):
        try:
            order = Order.objects.get(id=order_id)
        except Order.DoesNotExist:
            messages.error(request, "Order not found.")
            return redirect('home')

        return render(request, 'order_confirmation.html', {'order': order})

    def post(self, request, order_id):
        try:
            order = Order.objects.get(id=order_id)
        except Order.DoesNotExist:
            messages.error(request, "Order not found.")
            return redirect('home')

        user = order.user

        try:
            payment_intent = stripe.PaymentIntent.retrieve(session.payment_intent)
            receipt_url = payment_intent.get('charges', {}).get('data', [{}])[0].get('receipt_url')

        except Exception as e:
            messages.error(request, f"Error fetching receipt: {str(e)}")
            return redirect('home')

        subject = "Order Confirmation - Your Payment was Successful"
        email_template_name = "orderconfirm.txt"
        domain = get_current_site(request).domain
        context = {
            "user": user,
            "order": order,
            "domain": domain,
            "site_name": 'WatchHouse',
            "uid": urlsafe_base64_encode(force_bytes(user.pk)),
            "order_id": order.id,
            "total_price": order.total_price,
            "status": order.status,
            "receipt_url": receipt_url, 
        }

        email_content = render_to_string(email_template_name, context)
        try:
            send_mail(
                subject,
                email_content,
                'your_email@example.com',
                [user.email],
                fail_silently=False,
            )
            messages.success(request, "Order confirmation email sent successfully!")
        except Exception as e:
            messages.error(request, f"Error sending email: {str(e)}")
            return render(request, 'order_confirmation.html', {'order': order})

        return redirect('order_success', order_id=order.id)

class CartView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        cart = request.session.get('cart', {})
        if not isinstance(cart, dict):
            cart = {}  
        
        return render(request, 'cart.html', {'cart': cart})

class AddToCartView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        cart = request.session.get('cart', {})
        if not isinstance(cart, dict):
            cart = {} 
        
        try:
            watch = Watch.objects.get(watch_id=kwargs['watch_id'])
        except Watch.DoesNotExist:
            return redirect('cart')
        
        if str(watch.watch_id) in cart:
            cart[str(watch.watch_id)]['quantity'] += 1  
        else:
            cart[str(watch.watch_id)] = {
                'watch_id': watch.watch_id,
                'title': watch.title,
                'price': float(watch.price),  
                'image_url': watch.image_url,
                'quantity': 1  
            }

        print("Updated cart:", cart)
        
        request.session['cart'] = cart
        request.session.modified = True  
        
        return redirect('cart')  

class ClearCartView(LoginRequiredMixin, View):
    def post(self, request):
        request.session['cart'] = []
        messages.success(request, "Your cart has been cleared.")
        return redirect('cart')

class UpdateQuantityView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        cart = request.session.get('cart', {})
        if not isinstance(cart, dict):
            cart = {}
        print("Cart before update:", cart)

        watch_id = str(kwargs['watch_id'])  
        action = kwargs['action']

        print(f"Updating watch {watch_id} with action {action}")

        if watch_id in cart:
            print(f"Current cart item: {cart[watch_id]}")
            if action == 'increase':
                cart[watch_id]['quantity'] += 1 
            elif action == 'decrease' and cart[watch_id]['quantity'] > 1:
                cart[watch_id]['quantity'] -= 1 
        
            request.session['cart'] = cart

        print("Cart after update:", cart)

        return redirect('cart')

class RemoveItemView(LoginRequiredMixin, View): 
    def post(self, request, watch_id):
        cart = request.session.get('cart', {})
        
        if str(watch_id) in cart:
            del cart[str(watch_id)]
            messages.success(request, "Item has been removed from your cart.")
        else:
            messages.error(request, "Item not found in your cart.")
        
        request.session['cart'] = cart
        
        return redirect('cart')

class AccountView(LoginRequiredMixin,TemplateView):
    template_name = 'account.html' 

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user'] = self.request.user 
        return context

class OrderSuccessView(TemplateView):
    template_name = 'order_success.html'
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        order = Order.objects.get(id=kwargs['order_id'])
        context['order'] = order
        return context

class ViewOrdersView(LoginRequiredMixin, ListView):
    model = Order
    template_name = 'view_orders.html'
    context_object_name = 'orders'

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).order_by('-created_at')

class ShopView(ListView):
    model = Watch
    template_name = 'shop.html'
    context_object_name = 'watches'
    paginate_by = 9

    def get_queryset(self):
        queryset = Watch.objects.all()
        selected_brand = self.request.GET.get('brand', None)
        selected_gender = self.request.GET.get('gender', None)
        selected_price_range = self.request.GET.get('price_range', None)
        selected_type = self.request.GET.get('type', None)

        if selected_brand:
            queryset = queryset.filter(brand__brand_name=selected_brand)

        if selected_gender:
            queryset = queryset.filter(gender__gender_name=selected_gender)

        if selected_price_range:
            price_ranges = {
                "0-50": (0, 50),
                "51-100": (51, 100),
                "101-200": (101, 200),
                "201-500": (201, 500),
                "500+": (500, None),
            }
            min_price, max_price = price_ranges.get(selected_price_range, (None, None))
            if min_price is not None:
                queryset = queryset.filter(price__gte=min_price)
            if max_price is not None:
                queryset = queryset.filter(price__lte=max_price)

        if selected_type:
            queryset = queryset.filter(type__type_name=selected_type)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['brands'] = Brand.objects.all()
        context['genders'] = Gender.objects.all()
        context['types'] = Type.objects.all()
        context['selected_brand'] = self.request.GET.get('brand', None)
        context['selected_gender'] = self.request.GET.get('gender', None)
        context['selected_price_range'] = self.request.GET.get('price_range', None)
        context['selected_type'] = self.request.GET.get('type', None)

        query_params = self.request.GET.copy()
        if 'page' in query_params:
            query_params.pop('page')

        context['query_params'] = urlencode(query_params)

        return context

stripe.api_key = settings.STRIPE_SECRET_KEY

class ShippingDetailsView(LoginRequiredMixin, View):
    def get(self, request):
        cart = request.session.get('cart', {})

        if not cart:
            return redirect('cart')

        total_price = 0
        cart_items = []  

        for item in cart.values():
            try:
                product = Watch.objects.get(watch_id=item['watch_id'])
                cart_items.append({
                    'title': product.title, 
                    'price': item['price'], 
                    'quantity': item['quantity'] 
                })
                total_price += float(item['price']) * int(item['quantity'])
            except (ValueError, KeyError, Watch.DoesNotExist) as e:
                return HttpResponse(f"Invalid data in cart: {e}", status=400)

        return render(request, 'shipping_details.html', {
            'cart_items': cart_items,  
            'total_price': total_price
        })

    def post(self, request):
        cart = request.session.get('cart', {})
        if not cart:
            return redirect('cart')

        shipping_address = request.POST.get('shipping_address')
        shipping_city = request.POST.get('shipping_city')
        shipping_postal_code = request.POST.get('shipping_postal_code')
        shipping_country = request.POST.get('shipping_country')
        email = request.POST.get('email')
        phone_number = request.POST.get('phone_number')

        if not request.user.is_authenticated:
            return redirect('login')

        user = request.user

        total_price = 0
        for item in cart.values():
            try:
                price = float(item['price'])
                quantity = int(item['quantity'])
                total_price += price * quantity
            except (ValueError, KeyError) as e:
                return HttpResponse(f"Invalid data in cart: {e}", status=400)

        order = Order.objects.create(
            user=user,
            total_price=total_price,
            shipping_address=shipping_address,
            shipping_city=shipping_city,
            shipping_postal_code=shipping_postal_code,
            shipping_country=shipping_country,
            email=email,
            phone_number=phone_number,
            status='Pending',
        )

        for item in cart.values():
            try:
                product = Watch.objects.get(watch_id=item['watch_id'])
                price = float(item['price'])
                quantity = int(item['quantity'])
                OrderItem.objects.create(
                    order=order,
                    product=product,
                    price=price,
                    quantity=quantity,
                )
            except Watch.DoesNotExist:
                return HttpResponse(f"Watch with ID {item['watch_id']} not found", status=404)
            except (ValueError, KeyError) as e:
                return HttpResponse(f"Invalid data in cart: {e}", status=400)

        request.session['cart'] = {}

        session = self.create_stripe_checkout_session(request, order)
        return redirect(session.url)

    def create_stripe_checkout_session(self, request, order):
        line_items = []
        
        for item in order.order_items.all():  
            line_items.append({
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': item.product.title, 
                    },
                    'unit_amount': int(item.price * 100), 
                },
                'quantity': item.quantity, 
            })

        try:
   
            session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=line_items, 
                mode='payment', 
                success_url=request.build_absolute_uri(reverse('payment_success')) + '?session_id={CHECKOUT_SESSION_ID}',  
                cancel_url=request.build_absolute_uri(reverse('payment_cancelled')),  
                metadata={'order_id': order.id},  
            )
            return session  
        except stripe.error.StripeError as e:
        
            print(f"Error creating Stripe checkout session: {e}")
            return None

class PaymentSuccessView(TemplateView):
    template_name = 'payment_success.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get session ID from URL parameters
        session_id = self.request.GET.get('session_id')
        if not session_id:
            logger.error("No session ID provided in request")
            raise Http404("Session ID not provided")
        
        try:
            # Retrieve Stripe session
            session = stripe.checkout.Session.retrieve(session_id)
            
            # Retrieve payment intent to get receipt URL
            payment_intent = stripe.PaymentIntent.retrieve(session.payment_intent)
            logger.info(f"Payment Intent Charges: {payment_intent.get('charges', {})}")
            receipt_url = payment_intent.get('charges', {}).get('data', [{}])[0].get('receipt_url')

            # Get order from session metadata
            order_id = session.metadata.get('order_id')
            if not order_id:
                logger.error(f"No order ID found in session {session_id}")
                raise Http404("Order ID not found in session metadata")
            
            order = get_object_or_404(Order, id=order_id)
            
            # Update order status
            order.status = 'Paid'
            order.stripe_receipt_url = receipt_url
            order.save()
            
            # Send confirmation email
            self.send_confirmation_email(order, session, receipt_url)
            
            # Add order to context
            context['order'] = order
            return context

        except stripe.error.StripeError as e:
            logger.error(f"Stripe error: {str(e)}")
            raise Http404(f"Stripe session retrieval failed: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            raise Http404(f"An unexpected error occurred: {str(e)}")
    
    def send_confirmation_email(self, order, session, receipt_url):
        """Send confirmation email with Stripe receipt."""
        user = order.user
        shipping_details = session.get('shipping', {}).get('address', {})
        
        # Prepare email context
        email_context = {
            'user': user,
            'order': order,
            'receipt_url': receipt_url,
            'name': f"{user.first_name} {user.last_name}",
            'shipping_details': shipping_details,
            'domain': get_current_site(self.request).domain,
        }
        
        # Render text and HTML email versions
        text_content = render_to_string('orderconfirm.txt', email_context)
        html_content = render_to_string('order_confirmation.html', email_context)
        
        subject = f"Payment Confirmation - Order #{order.id}"
        from_email = settings.DEFAULT_FROM_EMAIL
        
        try:
            # Create email message
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=from_email,
                to=[user.email],
            )
            email.attach_alternative(html_content, "text/html")
            email.send(fail_silently=False)
            
            logger.info(f"Confirmation email sent for order {order.id}")
        except Exception as e:
            logger.error(f"Failed to send confirmation email for order {order.id}: {str(e)}")


class PaymentCancelledView(TemplateView):
    template_name = 'payment_cancelled.html'


class StripeWebhookView(View):
    @method_decorator(csrf_exempt)
    def post(self, request):
        payload = request.body
        sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')

        try:
            # Verify webhook signature
            event = stripe.Webhook.construct_event(payload, sig_header, settings.STRIPE_WEBHOOK_SECRET)
        except ValueError as e:
            logger.error(f"Invalid payload: {str(e)}")
            return HttpResponse(status=400)
        except stripe.error.SignatureVerificationError as e:
            logger.error(f"Invalid signature: {str(e)}")
            return HttpResponse(status=400)

        # Handle the event
        if event['type'] == 'checkout.session.completed':
            session = event['data']['object']
            payment_intent = stripe.PaymentIntent.retrieve(session['payment_intent'])
            receipt_url = payment_intent.get('charges', {}).get('data', [{}])[0].get('receipt_url')

            order_id = session['client_reference_id']
            try:
                order = Order.objects.get(id=order_id)
                order.status = 'Paid'
                order.stripe_receipt_url = receipt_url
                order.save()
                logger.info(f"Order {order.id} marked as paid.")
            except Order.DoesNotExist:
                logger.error(f"Order {order_id} not found for session {session.id}")

        return HttpResponse(status=200)

