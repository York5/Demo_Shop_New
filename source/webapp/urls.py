from django.urls import path
from .views import IndexView, ProductView, ProductCreateView, BasketChangeView, BasketView,\
    ProductUpdateView, ProductDeleteView, OrderListView, OrderDetailView, OrderCreateView, OrderCancelView,\
    OrderUpdateView, OrderDeliverView, OrderProductCreateView

app_name = 'webapp'

urlpatterns = [
    path('', IndexView.as_view(), name='index'),
    path('products/<int:pk>/', ProductView.as_view(), name='product_detail'),
    path('products/create/', ProductCreateView.as_view(), name='product_create'),
    path('basket/change/', BasketChangeView.as_view(), name='basket_change'),
    path('basket/', BasketView.as_view(), name='basket'),
    path('products/<int:pk>/update/', ProductUpdateView.as_view(), name='product_update'),
    path('products/<int:pk>/delete/', ProductDeleteView.as_view(), name='product_delete'),

    path('orders/', OrderListView.as_view(), name='orders_index'),
    path('orders/<int:pk>/', OrderDetailView.as_view(), name='order_detail'),
    path('orders/create', OrderCreateView.as_view(), name='order_create'),
    path('orders/<int:pk>/delete/', OrderCancelView.as_view(), name='order_delete'),
    path('orders/<int:pk>/deliver/', OrderDeliverView.as_view(), name='order_delivered'),
    path('orders/<int:pk>/update/', OrderUpdateView.as_view(), name='order_update'),

    path('order/<int:pk>/add-product/', OrderProductCreateView.as_view(), name='order_product_create'),

]
