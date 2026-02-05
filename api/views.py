from rest_framework import viewsets, status, generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.db import transaction
from django.db.models import Sum, Count
from django.utils import timezone
from datetime import timedelta
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
        try:
            settings_obj, _ = StoreSettings.objects.get_or_create(id='singleton', defaults={'name': 'My Store', 'currency': 'UZS', 'address': 'Default Address', 'phone': 'Default Phone'})
            
            # Safely fetch each dataset with error handling
            try:
                goods_receipts_qs = GoodsReceipt.objects.select_related('supplier').prefetch_related('items__product').order_by('-date')[:100]
                goods_receipts_data = GoodsReceiptSerializer(goods_receipts_qs, many=True).data
            except Exception as e:
                print(f'Error fetching goods receipts: {e}')
                goods_receipts_data = []
            
            try:
                sales_qs = Sale.objects.select_related('seller', 'seller__role', 'customer').prefetch_related('items__product').order_by('-date')[:200]
                sales_data = SaleSerializer(sales_qs, many=True).data
            except Exception as e:
                print(f'Error fetching sales: {e}')
                sales_data = []
            
            try:
                employees_qs = Employee.objects.select_related('role').all()
                employees_data = EmployeeSerializer(employees_qs, many=True).data
            except Exception as e:
                print(f'Error fetching employees: {e}')
                employees_data = []
            
            try:
                stock_movements_qs = StockMovement.objects.select_related('product').order_by('-date')[:200]
                stock_movements_data = StockMovementSerializer(stock_movements_qs, many=True).data
            except Exception as e:
                print(f'Error fetching stock movements: {e}')
                stock_movements_data = []
            
            try:
                warehouses_qs = Warehouse.objects.all()
                warehouses_data = WarehouseSerializer(warehouses_qs, many=True).data
            except Exception as e:
                print(f'Error fetching warehouses: {e}')
                warehouses_data = []
            
            try:
                warehouse_products_qs = WarehouseProduct.objects.select_related('warehouse', 'product').all()
                warehouse_products_data = WarehouseProductSerializer(warehouse_products_qs, many=True).data
            except Exception as e:
                print(f'Error fetching warehouse products: {e}')
                warehouse_products_data = []
            
            try:
                expenses_qs = Expense.objects.select_related('employee', 'employee__role').order_by('-date')[:200]
                expenses_data = ExpenseSerializer(expenses_qs, many=True).data
            except Exception as e:
                print(f'Error fetching expenses: {e}')
                expenses_data = []
            
            try:
                expense_types_data = ExpenseTypeSerializer(ExpenseType.objects.all(), many=True).data
            except Exception as e:
                print(f'Error fetching expense types: {e}')
                expense_types_data = []
            
            # Fetch other data sets
            try:
                products_data = ProductSerializer(Product.objects.all(), many=True).data
            except Exception as e:
                print(f'Error fetching products: {e}')
                products_data = []
            
            try:
                customers_data = CustomerSerializer(Customer.objects.all(), many=True).data
            except Exception as e:
                print(f'Error fetching customers: {e}')
                customers_data = []
            
            try:
                suppliers_data = SupplierSerializer(Supplier.objects.all(), many=True).data
            except Exception as e:
                print(f'Error fetching suppliers: {e}')
                suppliers_data = []
            
            try:
                debt_payments_data = DebtPaymentSerializer(DebtPayment.objects.order_by('-date')[:200], many=True).data
            except Exception as e:
                print(f'Error fetching debt payments: {e}')
                debt_payments_data = []
            
            try:
                settings_data = StoreSettingsSerializer(settings_obj).data
            except Exception as e:
                print(f'Error fetching settings: {e}')
                settings_data = {}
            
            try:
                units_data = UnitSerializer(Unit.objects.all(), many=True).data
            except Exception as e:
                print(f'Error fetching units: {e}')
                units_data = []
            
            try:
                roles_data = RoleSerializer(Role.objects.all(), many=True).data
            except Exception as e:
                print(f'Error fetching roles: {e}')
                roles_data = []
            
            data = {
                'products': products_data,
                'customers': customers_data,
                'suppliers': suppliers_data,
                'sales': sales_data,
                'debtPayments': debt_payments_data,
                'settings': settings_data,
                'units': units_data,
                'goodsReceipts': goods_receipts_data,
                'roles': roles_data,
                'employees': employees_data,
                'stockMovements': stock_movements_data,
                'warehouses': warehouses_data,
                'warehouseProducts': warehouse_products_data,
                'expenses': expenses_data,
                'expenseTypes': expense_types_data,
            }
            return Response(data)
        except Exception as e:
            print(f'Critical error in InitialDataView: {e}')
            return Response({'error': 'Failed to load initial data'}, status=500)

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


class ExpenseTypeViewSet(viewsets.ModelViewSet):
    queryset = ExpenseType.objects.all()
    serializer_class = ExpenseTypeSerializer
    permission_classes = [IsAuthenticated, HasPermission]
    required_permission = 'manage_settings'
    
    def perform_create(self, serializer):
        serializer.save(id=f'exp_type_{shortuuid.random(8)}')


class ExpenseViewSet(viewsets.ModelViewSet):
    queryset = Expense.objects.select_related('type', 'employee', 'employee__role').order_by('-date')
    serializer_class = ExpenseSerializer
    permission_classes = [IsAuthenticated, HasPermission]
    required_permission = 'manage_settings'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        expense_type_id = self.request.query_params.get('type_id', None)
        start_date = self.request.query_params.get('start_date', None)
        end_date = self.request.query_params.get('end_date', None)
        
        if expense_type_id:
            queryset = queryset.filter(type_id=expense_type_id)
        if start_date:
            queryset = queryset.filter(date__gte=start_date)
        if end_date:
            queryset = queryset.filter(date__lte=end_date)
            
        return queryset


class DashboardStatsView(APIView):
    permission_classes = [IsAuthenticated, HasPermission]
    required_permission = 'view_dashboard'
    
    def get(self, request, *args, **kwargs):
        try:
            # Calculate total sales
            total_sales = Sale.objects.aggregate(
                total=Sum('total')
            )['total'] or 0
            
            # Calculate total expenses
            total_expenses = Expense.objects.aggregate(
                total=Sum('amount')
            )['total'] or 0
            
            # Calculate net profit
            net_profit = total_sales - total_expenses
            
            # Get recent sales (last 30 days)
            thirty_days_ago = timezone.now() - timedelta(days=30)
            recent_sales = Sale.objects.filter(date__gte=thirty_days_ago).aggregate(
                total=Sum('total'),
                count=Count('id')
            )
            
            # Get recent expenses (last 30 days)
            recent_expenses = Expense.objects.filter(date__gte=thirty_days_ago).aggregate(
                total=Sum('amount'),
                count=Count('id')
            )
            
            # Get top selling products (with error handling)
            try:
                top_products = Product.objects.filter(
                    items__sale__date__gte=thirty_days_ago
                ).annotate(
                    total_sold=Sum('items__quantity')
                ).order_by('-total_sold')[:5]
            except Exception:
                top_products = []
            
            # Get expense breakdown by type
            try:
                expense_breakdown = Expense.objects.values('type').annotate(
                    total=Sum('amount'),
                    count=Count('id')
                ).order_by('-total')
            except Exception:
                expense_breakdown = []
            
            data = {
                'total_sales': float(total_sales),
                'total_expenses': float(total_expenses),
                'net_profit': float(net_profit),
                'recent_sales_total': float(recent_sales['total'] or 0),
                'recent_sales_count': recent_sales['count'] or 0,
                'recent_expenses_total': float(recent_expenses['total'] or 0),
                'recent_expenses_count': recent_expenses['count'] or 0,
                'top_products': [{
                    'name': getattr(product, 'name', 'Unknown'),
                    'total_sold': float(getattr(product, 'total_sold', 0) or 0)
                } for product in top_products],
                'expense_breakdown': [{
                    'type': item.get('type', ''),
                    'total': float(item.get('total', 0) or 0),
                    'count': item.get('count', 0)
                } for item in expense_breakdown]
            }
            
            return Response(data)
        except Exception as e:
            # Return default values if there's an error
            return Response({
                'total_sales': 0,
                'total_expenses': 0,
                'net_profit': 0,
                'recent_sales_total': 0,
                'recent_sales_count': 0,
                'recent_expenses_total': 0,
                'recent_expenses_count': 0,
                'top_products': [],
                'expense_breakdown': []
            })
