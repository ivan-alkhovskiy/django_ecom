from django.shortcuts import render, redirect
from cart.cart import Cart
from payment.forms import ShippingForm, PaymentForm
from payment.models import ShippingAddress, Order, OrderItem
from django.contrib.auth.models import User
from django.contrib import messages
from store.models import Product, Profile
import datetime


def orders(request, pk):
    if request.user.is_authenticated and request.user.is_superuser:
        # get order
        order = Order.objects.get(id=pk)

    # get the order itmes
        items = OrderItem.objects.filter(order=pk)

        if request.POST:
            status = request.POST['shipping_status']
            # check if true or false
            if status == "true":
                # get the order
                order = Order.objects.filter(id=pk)
                # update the status
                now = datetime.datetime.now()
                order.update(shipped=True, date_shipped=now)
            else:
                # get the order
                order = Order.objects.filter(id=pk)
                # update the status
                order.update(shipped=False)
            messages.success(request, "Shipping Status Updated")
            return redirect('home')

        return render(request, 'payment/orders.html', {"order": order, "items": items})

    else:
        messages.success(request, "access denied")
        return redirect('home')


def not_shipped_dash(request):
    if request.user.is_authenticated and request.user.is_superuser:
        orders = Order.objects.filter(shipped=False)
        if request.POST:
            status = request.POST['shipping_status']
            num = request.POST['num']
            # get the order
            order = Order.objects.filter(id=num)
            # grab Date and time
            now = datetime.datetime.now()
            # update order
            order.update(shipped=True, date_shipped=now)
            # redirect
            messages.success(request, "Shipping Status Updated")
            return redirect('home')

        return render(request, "payment/not_shipped_dash.html", {"orders": orders})
    else:
        messages.success(request, "access denied")
        return redirect('home')


def shipped_dash(request):
    if request.user.is_authenticated and request.user.is_superuser:
        orders = Order.objects.filter(shipped=True)
        if request.POST:
            status = request.POST['shipping_status']
            num = request.POST['num']
            # grab the order
            order = Order.objects.filter(id=num)

            # grab Date and time
            now = datetime.datetime.now()
            # update order
            order.update(shipped=False)
            # redirect
            messages.success(request, "Shipping Status Updated")
            return redirect('home')

        return render(request, "payment/shipped_dash.html", {"orders": orders})
    else:
        messages.success(request, "order placed")
        return redirect('home')


def process_order(request):

    if request.POST:

        # get the cart
        cart = Cart(request)
        cart_products = cart.get_prods
        quantities = cart.get_quants
        totals = cart.cart_total()

        # get billing info from the last page
        payment_form = PaymentForm(request.POST or None)
        # get shipping session data
        my_shipping = request.session.get('my_shipping')

        # gather order info
        full_name = my_shipping['shipping_full_name']
        email = my_shipping['shipping_email']

        # create shipping address from sessioninfo
        shipping_address = f"{my_shipping['shipping_address1']}\n{my_shipping['shipping_address2']}\n{my_shipping['shipping_address2']}\n{
            my_shipping['shipping_city']}\n{my_shipping['shipping_state']}\n{my_shipping['shipping_country']}\n{my_shipping['shipping_zipcode']}"
        amount_paid = totals

        # create an order
        if request.user.is_authenticated:
            # logged in
            user = request.user
            # create order
            create_order = Order(user=user, full_name=full_name, email=email,
                                 shipping_address=shipping_address, amount_paid=amount_paid)
            create_order.save()

            # add order ittems
            # get the order ID
            order_id = create_order.pk

            for product in cart_products():  # get product info
                product_id = product.id  # get product ID
                if product.is_sale:  # get product price
                    price = product.sale_price
                else:
                    price = product.price

                for key, value in quantities().items():  # get quantity
                    if int(key) == product.id:  # if int(key) == product.id:

                        create_order_item = OrderItem(
                            order_id=order_id, product_id=product_id, user=user, quantity=value, price=price)
                        create_order_item.save()  # create order item

            # delete our cart

            for key in list(request.session.keys()):
                if key == "session_key":
                    # delete the key
                    del request.session[key]

            # delete Cart from database(old_cart field)
            current_user = Profile.objects.filter(user__id=request.user.id)
            # delete shopping cart in database (old_cart field)
            current_user.update(old_cart="")

            messages.success(request, "order placed")
            return redirect('home')

        else:
            # not logged in
            create_order = Order(full_name=full_name, email=email,
                                 shipping_address=shipping_address, amount_paid=amount_paid)
            create_order.save()

            # add order ittems
            # get the order ID
            order_id = create_order.pk

            for product in cart_products():  # get product info
                product_id = product.id  # get product ID
                if product.is_sale:  # get product price
                    price = product.sale_price
                else:
                    price = product.price

                for key, value in quantities().items():  # get quantity
                    if int(key) == product.id:  # if int(key) == product.id:

                        create_order_item = OrderItem(
                            order_id=order_id, product_id=product_id, quantity=value, price=price)
                        create_order_item.save()  # create order item

            for key in list(request.session.keys()):
                if key == "session_key":
                    # delete the key
                    del request.session[key]

            messages.success(request, "order placed")
            return redirect('home')

        messages.success(request, "order placed")
        return redirect('home')

    else:
        messages.success(request, "Access Denied")
        return redirect('home')


def billing_info(request):
    if request.POST:

        cart = Cart(request)
        cart_products = cart.get_prods
        quantities = cart.get_quants
        totals = cart.cart_total()

        # Create a session with shipping info
        my_shipping = request.POST
        request.session['my_shipping'] = my_shipping

        # check to see if user is logged in
        if request.user.is_authenticated:
            # get the billing form
            billing_form = PaymentForm()
            return render(request, "payment/billing_info.html", {"cart_products": cart_products, "quantities": quantities, "totals": totals, "shipping_info": request.POST, "billing_form": billing_form})
        else:
            # not logged in
            # get the billing form
            billing_form = PaymentForm()
            return render(request, "payment/billing_info.html", {"cart_products": cart_products, "quantities": quantities, "totals": totals, "shipping_info": request.POST, "billing_form": billing_form})

        shipping_form = request.POST
        return render(request, "payment/billing_info.html", {"cart_products": cart_products, "quantities": quantities, "totals": totals, "shipping_form": shipping_form})
    else:
        messages.success(request, "Access Denied")
        return redirect('home')


def checkout(request):

    cart = Cart(request)
    cart_products = cart.get_prods
    quantities = cart.get_quants
    totals = cart.cart_total()

    if request.user.is_authenticated:
        # checked as logged in user
        # shipping user
        shipping_user = ShippingAddress.objects.get(user__id=request.user.id)
        # shipping form
        shipping_form = ShippingForm(
            request.POST or None, instance=shipping_user)
        return render(request, "payment/checkout.html", {"cart_products": cart_products, "quantities": quantities, "totals": totals, "shipping_form": shipping_form})
    else:
        # check out as guest
        shipping_form = ShippingForm(request.POST or None)
        return render(request, "payment/checkout.html", {"cart_products": cart_products, "quantities": quantities, "totals": totals, "shipping_form": shipping_form})


def payment_success(request):
    return render(request, "payment/payment_success.html", {})
