import stripe
from django.conf import settings
from django.http import JsonResponse
from django.views.generic import View

from apps.order.models import OrderInfo
from apps.user.models import User
from utils.mixin import CSRFExemptMixin

stripe.api_key = settings.STRIPE_API_KEY

endpoint_secret = settings.STRIPE_WEBHOOK_ENDPOINT_SK


# url: /webhooks/stripe
class StripeWebhookView(CSRFExemptMixin, View):

    def post(self, request):
        payload = request.body
        sig_header = request.META['HTTP_STRIPE_SIGNATURE']
        event = None

        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, endpoint_secret
            )
        except ValueError as e:
            return JsonResponse({'res': 400, 'errmsg': 'Invalid payload'})
        except stripe.error.SignatureVerificationError as e:
            return JsonResponse({'res': 400, 'errmsg': 'Invalid signature'})

        # Handle the checkout.session.completed event
        if event['type'] == 'checkout.session.completed':
            session = event['data']['object']
            order_id = session.get('client_reference_id')
            customer_email = session.get('customer_email')
            user = User.objects.get(email=customer_email)
            transaction_num = session.get('payment_intent')

            try:
                order_info = OrderInfo.objects.get(order_id=order_id,
                                                   user=user,
                                                   payment_method=1,
                                                   order_status=1)
            except OrderInfo.DoesNotExist:
                return JsonResponse({'res': 400, 'errmsg': 'Payment failed'})

            # update order_info status
            order_info.transaction_num = transaction_num
            order_info.order_status = 2
            order_info.save()
            return JsonResponse({'res': 200, 'message': 'Payment successful'})
        else:
            return JsonResponse({'res': 400, 'errmsg': 'Payment failed'})
