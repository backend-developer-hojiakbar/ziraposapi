from rest_framework import viewsets, status, generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.db import transaction
import shortuuid
from .models import *
from .serializers import *
from .permissions import HasPermission

class LoginView(APIView):
    permission_classes = [AllowAny]
    def post(self, request, *args, **kwargs):
        pin = request.data.get('pin')
        if not pin: return Response({'error': 'PIN is required'}, status=status.HTTP_400_BAD_REQUEST)
        user = None
        for employee in Employee.objects.all():
            if employee.check_password(pin):
                user = employee
                break
        if user:
            refresh = RefreshToken.for_user(user)
            employee_data = EmployeeSerializer(user).data
            return Response({'token': str(refresh.access_token), 'employee': employee_data})
        return Response({'error': 'Invalid PIN'}, status=status.HTTP_401_UNAUTHORIZED)

class MeView(generics.RetrieveAPIView):
    serializer_class = EmployeeSerializer
    permission_classes = [IsAuthenticated]
    def get_object(self): return self.request.user

class InitialDataView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, *args, **kwargs):
        settings_obj, _ = StoreSettings.objects.get_or_create(id='singleton', defaults={'name': 'My Store', 'currency': 'UZS', 'address': 'Default Address', 'phone': 'Default Phone'})
        goods_receipts_qs = GoodsReceipt.objects.select_related('supplier').prefetch_related('items__product').order_by('-date')[:100]
        sales_qs = Sale.objects.select_related('seller', 'seller__role', 'customer').prefetch_related('items__product').order_by('-date')[:200]
        employees_qs = Employee.objects.select_related('role').all()
        stock_movements_qs = StockMovement.objects.select_related('product').order_by('-date')[:200]
        warehouses_qs = Warehouse.objects.all()
        warehouse_products_qs = WarehouseProduct.objects.select_related('warehouse', 'product').all()
        data = {
            'products': ProductSerializer(Product.objects.all(), many=True).data,
            'customers': CustomerSerializer(Customer.objects.all(), many=True).data,
            'suppliers': SupplierSerializer(Supplier.objects.all(), many=True).data,
            'sales': SaleSerializer(sales_qs, many=True).data,
            'debtPayments': DebtPaymentSerializer(DebtPayment.objects.order_by('-date')[:200], many=True).data,
            'settings': StoreSettingsSerializer(settings_obj).data,
            'units': UnitSerializer(Unit.objects.all(), many=True).data,
            'goodsReceipts': GoodsReceiptSerializer(goods_receipts_qs, many=True).data,
            'roles': RoleSerializer(Role.objects.all(), many=True).data,
            'employees': EmployeeSerializer(employees_qs, many=True).data,
            'stockMovements': StockMovementSerializer(stock_movements_qs, many=True).data,
            'warehouses': WarehouseSerializer(warehouses_qs, many=True).data,
            'warehouseProducts': WarehouseProductSerializer(warehouse_products_qs, many=True).data,
        }
        return Response(data)

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated, HasPermission]
    required_permission = 'manage_products'
    
    def create(self, request, *args, **kwargs):
        # Handle both regular JSON and multipart form data
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
    
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)
    
    def perform_create(self, serializer):
        serializer.save(id=f'prod_{shortuuid.random(10)}')
    
    def perform_update(self, serializer):
        serializer.save()

class CustomerViewSet(viewsets.ModelViewSet):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    permission_classes = [IsAuthenticated, HasPermission]
    required_permission = 'manage_customers'

class SupplierViewSet(viewsets.ModelViewSet):
    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializer
    permission_classes = [IsAuthenticated, HasPermission]
    required_permission = 'manage_suppliers'

class RoleViewSet(viewsets.ModelViewSet):
    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    permission_classes = [IsAuthenticated, HasPermission]
    required_permission = 'manage_employees'

class EmployeeViewSet(viewsets.ModelViewSet):
    queryset = Employee.objects.all()
    serializer_class = EmployeeSerializer
    permission_classes = [IsAuthenticated, HasPermission]
    required_permission = 'manage_employees'

class UnitViewSet(viewsets.ModelViewSet):
    queryset = Unit.objects.all()
    serializer_class = UnitSerializer
    permission_classes = [IsAuthenticated, HasPermission]
    required_permission = 'manage_settings'
    def perform_create(self, serializer):
        serializer.save(id=f'unit_{shortuuid.random(6)}')

class SettingsView(generics.RetrieveUpdateAPIView):
    serializer_class = StoreSettingsSerializer
    permission_classes = [IsAuthenticated, HasPermission]
    required_permission = 'manage_settings'
    def get_object(self):
        obj, _ = StoreSettings.objects.get_or_create(id='singleton')
        return obj

class SaleCreateView(generics.CreateAPIView):
    serializer_class = SaleSerializer
    permission_classes = [IsAuthenticated, HasPermission]
    required_permission = 'use_sales_terminal'
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save(seller=self.request.user)
        response_serializer = self.get_serializer(instance)
        headers = self.get_success_headers(response_serializer.data)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED, headers=headers)

class GoodsReceiptCreateView(generics.CreateAPIView):
    serializer_class = GoodsReceiptSerializer
    permission_classes = [IsAuthenticated, HasPermission]
    required_permission = 'manage_warehouse'

class DebtPaymentCreateView(generics.CreateAPIView):
    serializer_class = DebtPaymentSerializer
    permission_classes = [IsAuthenticated, HasPermission]
    required_permission = 'manage_customers'
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            customer_id = serializer.validated_data['customer_id']
            amount = serializer.validated_data['amount']
            customer = Customer.objects.get(id=customer_id)
            customer.debt -= amount
            customer.save()
            payment = DebtPayment.objects.create(
                id=f"debt_pay_{shortuuid.random(10)}",
                customer=customer, amount=amount,
                paymentType=serializer.validated_data['paymentType']
            )
        return Response(DebtPaymentSerializer(payment).data, status=status.HTTP_201_CREATED)


class StockMovementViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = StockMovement.objects.select_related('product').order_by('-date')
    serializer_class = StockMovementSerializer
    permission_classes = [IsAuthenticated, HasPermission]
    required_permission = 'manage_warehouse'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        product_id = self.request.query_params.get('product_id', None)
        movement_type = self.request.query_params.get('type', None)
        
        if product_id:
            queryset = queryset.filter(product_id=product_id)
        if movement_type:
            queryset = queryset.filter(type=movement_type)
            
        return queryset


class WarehouseViewSet(viewsets.ModelViewSet):
    queryset = Warehouse.objects.all()
    serializer_class = WarehouseSerializer
    permission_classes = [IsAuthenticated, HasPermission]
    required_permission = 'manage_warehouse'


class WarehouseProductViewSet(viewsets.ModelViewSet):
    queryset = WarehouseProduct.objects.select_related('warehouse', 'product').all()
    serializer_class = WarehouseProductSerializer
    permission_classes = [IsAuthenticated, HasPermission]
    required_permission = 'manage_warehouse'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        warehouse_id = self.request.query_params.get('warehouse_id', None)
        product_id = self.request.query_params.get('product_id', None)
        
        if warehouse_id:
            queryset = queryset.filter(warehouse_id=warehouse_id)
        if product_id:
            queryset = queryset.filter(product_id=product_id)
            
        return queryset
