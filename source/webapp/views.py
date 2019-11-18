from django.http import HttpResponseRedirect
from django.shortcuts import reverse, redirect, get_object_or_404

from django.urls import reverse_lazy
from django.views import View
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView

from webapp.forms import BasketOrderCreateForm
from webapp.models import Product, OrderProduct, Order, CANCELED, DELIVERED
from django.contrib.auth.mixins import PermissionRequiredMixin, LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from webapp.mixins import StatsMixin


class IndexView(StatsMixin, ListView):
    model = Product
    template_name = 'index.html'

    def get_queryset(self):
        return Product.objects.filter(in_order=True)


class ProductView(StatsMixin, DetailView):
    model = Product
    template_name = 'product/detail.html'


class ProductCreateView(PermissionRequiredMixin, StatsMixin, CreateView):
    model = Product
    template_name = 'product/create.html'
    fields = ('name', 'category', 'price', 'photo', 'in_order')
    permission_required = 'webapp.add_product', 'webapp.can_have_piece_of_pizza'
    permission_denied_message = '403 Доступ запрещён!'

    def get_success_url(self):
        return reverse('webapp:product_detail', kwargs={'pk': self.object.pk})


class ProductUpdateView(LoginRequiredMixin, StatsMixin, UpdateView):
    model = Product
    template_name = 'product/update.html'
    fields = ('name', 'category', 'price', 'photo', 'in_order')
    context_object_name = 'product'

    def get_success_url(self):
        return reverse('webapp:product_detail', kwargs={'pk': self.object.pk})


class ProductDeleteView(LoginRequiredMixin, StatsMixin, DeleteView):
    model = Product
    template_name = 'product/delete.html'
    success_url = reverse_lazy('webapp:index')
    context_object_name = 'product'

    def delete(self, request, *args, **kwargs):
        product = self.object = self.get_object()
        product.in_order = False
        product.save()
        return HttpResponseRedirect(self.get_success_url())


class BasketChangeView(StatsMixin, View):
    def get(self, request, *args, **kwargs):
        products = request.session.get('products', [])

        pk = request.GET.get('pk')
        action = request.GET.get('action')
        next_url = request.GET.get('next', reverse('webapp:index'))

        if action == 'add':
            product = get_object_or_404(Product, pk=pk)
            if product.in_order:
                products.append(pk)
        else:
            for product_pk in products:
                if product_pk == pk:
                    products.remove(product_pk)
                    break

        request.session['products'] = products
        request.session['products_count'] = len(products)

        return redirect(next_url)


class BasketView(StatsMixin, CreateView):
    model = Order
    form_class = BasketOrderCreateForm
    template_name = 'product/basket.html'
    success_url = reverse_lazy('webapp:index')

    def get_context_data(self, **kwargs):
        basket, basket_total = self._prepare_basket()
        kwargs['basket'] = basket
        kwargs['basket_total'] = basket_total
        return super().get_context_data(**kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        if self._basket_empty():
            form.add_error(None, 'В корзине отсутствуют товары!')
            return self.form_invalid(form)
        response = super().form_valid(form)
        self._save_order_products()
        self._clean_basket()
        messages.success(self.request, 'Заказ оформлен!')
        return response

    def _prepare_basket(self):
        totals = self._get_totals()
        basket = []
        basket_total = 0
        for pk, qty in totals.items():
            product = Product.objects.get(pk=int(pk))
            total = product.price * qty
            basket_total += total
            basket.append({'product': product, 'qty': qty, 'total': total})
        return basket, basket_total

    def _get_totals(self):
        products = self.request.session.get('products', [])
        totals = {}
        for product_pk in products:
            if product_pk not in totals:
                totals[product_pk] = 0
            totals[product_pk] += 1
        return totals

    def _basket_empty(self):
        products = self.request.session.get('products', [])
        return len(products) == 0

    def _save_order_products(self):
        totals = self._get_totals()
        for pk, qty in totals.items():
            OrderProduct.objects.create(product_id=pk, order=self.object, amount=qty)

    def _clean_basket(self):
        if 'products' in self.request.session:
            self.request.session.pop('products')
        if 'products_count' in self.request.session:
            self.request.session.pop('products_count')


class OrderListView(ListView):
    template_name = 'order/list.html'
    context_object_name = 'orders'

    def get_queryset(self):
        if self.request.user.has_perm('webapp:view_order'):
            self.queryset = Order.objects.all().order_by('-created_at')
        elif self.request.user.is_authenticated:
            self.queryset = Order.objects.filter(user=self.request.user)
        return super(OrderListView, self).get_queryset()


class OrderDetailView(UserPassesTestMixin, DetailView):
    model = Order
    template_name = 'order/detail.html'

    def test_func(self):
        order_pk = self.kwargs.get('pk')
        order = get_object_or_404(Order, pk=order_pk)
        return self.request.user.has_perm('webapp.view_order') or self.request.user.pk == order.user.pk


class OrderCreateView(PermissionRequiredMixin, CreateView):
    model = Order
    fields = ['user', 'first_name', 'last_name', 'phone', 'email', 'status']
    template_name = 'order/order_create.html'
    permission_required = 'webapp.add_order'
    permission_denied_message = '403 Access Denied!'

    def get_success_url(self):
        return reverse('webapp:order_detail', kwargs={'pk': self.object.pk})


class OrderUpdateView(UpdateView):
    model = Order
    template_name = 'order/order_update.html'
    fields = ['first_name', 'last_name', 'phone', 'email', 'status']
    permission_required = 'webapp.change_order'
    permission_denied_message = '403 Access Denied!'

    def get_success_url(self):
        return reverse('webapp:order_detail', kwargs={'pk': self.object.pk})


class OrderDeliverView(PermissionRequiredMixin, DeleteView):
    model = Order
    template_name = 'order/order_delivered.html'
    permission_required = 'webapp.is_courier'
    permission_denied_message = "403 Access Denied!"

    def get_success_url(self):
        return reverse('webapp:order_detail', kwargs={'pk': self.object.pk})

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.status = DELIVERED
        self.object.save()
        return HttpResponseRedirect(self.get_success_url())


class OrderCancelView(PermissionRequiredMixin, DeleteView):
    model = Order
    template_name = 'order/order_delete.html'
    success_url = 'webapp:order_index'
    permission_required = 'webapp.delete_order'
    permission_denied_message = '403 Access Denied!'

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.status = CANCELED
        self.object.save()
        return redirect('webapp:order_detail', self.object.pk)


class OrderProductCreateView(CreateView):
    model = OrderProduct
    pass


class OrderProductUpdateView(UpdateView):
    model = OrderProduct
    pass


class OrderProductDeleteView(DeleteView):
    model = OrderProduct
    pass
