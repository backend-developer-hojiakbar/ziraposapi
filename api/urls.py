from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import *

router = DefaultRouter()
router.register(r'products', ProductViewSet)
router.register(r'customers', CustomerViewSet)
router.register(r'suppliers', SupplierViewSet)
router.register(r'roles', RoleViewSet)
router.register(r'employees', EmployeeViewSet)
router.register(r'units', UnitViewSet)
router.register(r'stock-movements', StockMovementViewSet)
router.register(r'warehouses', WarehouseViewSet)
router.register(r'warehouse-products', WarehouseProductViewSet)
router.register(r'expense-types', ExpenseTypeViewSet)
router.register(r'expenses', ExpenseViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('auth/login/', LoginView.as_view(), name='login'),
    path('auth/me/', MeView.as_view(), name='me'),
    path('data/initial/', InitialDataView.as_view(), name='initial-data'),
    path('settings/', SettingsView.as_view(), name='settings'),
    path('sales/', SaleCreateView.as_view(), name='create-sale'),
    path('goods-receipts/', GoodsReceiptCreateView.as_view(), name='create-goods-receipt'),
    path('debt-payments/', DebtPaymentCreateView.as_view(), name='create-debt-payment'),
    path('dashboard/stats/', DashboardStatsView.as_view(), name='dashboard-stats'),
]