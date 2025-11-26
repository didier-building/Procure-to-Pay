import json
import logging
from django.db import transaction
from django.utils import timezone
from django.db.models import Count, Q, Case, When, IntegerField
from django.core.exceptions import ValidationError
from rest_framework import viewsets, status, mixins
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter, OpenApiResponse, OpenApiExample
from drf_spectacular.types import OpenApiTypes
from rest_framework.decorators import api_view
from .document_processor import document_processor
from .models import PurchaseRequest, Approval
from .serializers import (
    PurchaseRequestSerializer,
    PurchaseRequestCreateSerializer,
    PurchaseRequestUpdateSerializer,
    ApproveRequestSerializer,
    RejectRequestSerializer,
    ReceiptUploadSerializer,
)

logger = logging.getLogger(__name__)

def _validate_file_security(uploaded_file):
    """Validate uploaded file for security issues"""
    if not uploaded_file:
        return True
        
    # Check file size (max 10MB)
    if uploaded_file.size > 10 * 1024 * 1024:
        raise ValidationError("File size exceeds 10MB limit")
    
    # Check file extension
    allowed_extensions = ['.pdf', '.jpg', '.jpeg', '.png', '.txt']
    file_name = uploaded_file.name.lower()
    if not any(file_name.endswith(ext) for ext in allowed_extensions):
        raise ValidationError("File type not allowed")
    
    # Prevent path traversal in filename
    if '..' in file_name:
        raise ValidationError("Invalid filename: contains path traversal")
    
    return True


@extend_schema_view(
    list=extend_schema(
        summary="List Purchase Requests",
        description="Retrieve a list of purchase requests. Staff users see only their own requests, approvers see all requests.",
        tags=["Purchase Requests"],
    ),
    create=extend_schema(
        summary="Create Purchase Request", 
        description="Create a new purchase request with proforma upload and line items.",
        tags=["Purchase Requests"],
        examples=[
            OpenApiExample(
                name="Sample Request",
                value={
                    "title": "Office Supplies Purchase",
                    "description": "Monthly office supplies procurement",
                    "amount": "1500.00",
                    "department": "IT",
                    "urgency": "MEDIUM",
                    "justification": "Required for daily operations",
                    "items": [
                        {
                            "name": "Laptops",
                            "quantity": 5,
                            "unit_price": "800.00"
                        },
                        {
                            "name": "Monitors", 
                            "quantity": 5,
                            "unit_price": "200.00"
                        }
                    ]
                }
            )
        ]
    ),
    retrieve=extend_schema(
        summary="Get Purchase Request",
        description="Retrieve a specific purchase request by ID with all related data.",
        tags=["Purchase Requests"],
    ),
    update=extend_schema(
        summary="Update Purchase Request",
        description="Update a purchase request (only allowed for PENDING requests).",
        tags=["Purchase Requests"],
    ),
    partial_update=extend_schema(
        summary="Partially Update Purchase Request", 
        description="Partially update a purchase request (only allowed for PENDING requests).",
        tags=["Purchase Requests"],
    ),
    destroy=extend_schema(
        summary="Delete Purchase Request",
        description="Delete a purchase request (only allowed for PENDING requests).",
        tags=["Purchase Requests"],
    ),
)
class PurchaseRequestViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing purchase requests with multi-level approval workflow.
    
    Supports CRUD operations plus custom actions for approval workflow and AI processing.
    """
    queryset = PurchaseRequest.objects.none()  # Performance fix: use get_queryset for filtering
    permission_classes = [IsAuthenticated]
    lookup_field = 'pk'

    def get_serializer_class(self):
        if self.action == 'create':
            return PurchaseRequestCreateSerializer
        if self.action in ['update', 'partial_update']:
            return PurchaseRequestUpdateSerializer
        return PurchaseRequestSerializer

    def get_queryset(self):
        user = self.request.user
        profile = getattr(user, 'profile', None)
        
        # Base queryset with optimized joins
        base_queryset = PurchaseRequest.objects.select_related(
            'created_by', 'approved_by'
        ).prefetch_related('approvals__approver', 'items')
        
        # Staff users see only their own requests
        # Approvers and Finance see all requests
        if profile and getattr(profile, 'role', None) == 'staff':
            return base_queryset.filter(created_by=user).order_by('-created_at')
        
        # Approvers and Finance see all requests
        return base_queryset.order_by('-created_at')

    def perform_create(self, serializer):
        # SECURITY FIX: Only staff can create requests
        user = self.request.user
        profile = getattr(user, 'profile', None)
        
        # Allow if user has staff role OR no profile (for backward compatibility)
        if profile and getattr(profile, 'role', None) not in ['staff', None]:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Only staff users can create purchase requests")
        
        instance = serializer.save(created_by=user)
        
        # Auto-extract proforma data if uploaded (stays PENDING for approval)
        if instance.proforma:
            try:
                extracted_data = document_processor.extract_proforma_data(instance.proforma.file)
                import json
                from decimal import Decimal
                def decimal_default(obj):
                    if isinstance(obj, Decimal):
                        return str(obj)
                    raise TypeError
                
                json_str = json.dumps(extracted_data, default=decimal_default)
                instance.proforma_data = json.loads(json_str)
                instance.save()
                
                logger.info(f"Proforma data extracted for request {instance.id} - awaiting approval")
            except Exception as e:
                logger.warning(f"Proforma extraction failed for request {instance.id}: {str(e)}")
        
        return instance
    
    def create(self, request, *args, **kwargs):
        """Override create to return full object with ID"""
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            instance = self.perform_create(serializer)
            
            # Return full object using the main serializer
            response_serializer = PurchaseRequestSerializer(instance)
            headers = self.get_success_headers(response_serializer.data)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED, headers=headers)
        except Exception as e:
            logger.error(f"Create request failed: {str(e)}", exc_info=True)
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def perform_update(self, serializer):
        # CRITICAL FIX: Staff can only update their own requests
        user = self.request.user
        profile = getattr(user, 'profile', None)
        if profile and getattr(profile, 'role', None) == 'staff':
            if serializer.instance.created_by != user:
                from rest_framework.exceptions import PermissionDenied
                raise PermissionDenied("Can only update your own requests")
        serializer.save()
    
    def perform_destroy(self, instance):
        # CRITICAL FIX: Staff can only delete their own requests
        user = self.request.user
        profile = getattr(user, 'profile', None)
        if profile and getattr(profile, 'role', None) == 'staff':
            if instance.created_by != user:
                from rest_framework.exceptions import PermissionDenied
                raise PermissionDenied("Can only delete your own requests")
        instance.delete()

    @extend_schema(
        summary="Approve Purchase Request",
        description="Approve a purchase request. Level 1 approvers move request to pending final approval, Level 2 approvers fully approve and trigger PO generation.",
        tags=["Approvals"],
        request=OpenApiTypes.OBJECT,
        examples=[
            OpenApiExample(
                name="Approval with Comment",
                value={
                    "comment": "Approved for business necessity. Ensure delivery by month end."
                }
            )
        ],
        responses={
            200: OpenApiResponse(
                description="Request approved successfully",
                examples=[
                    OpenApiExample(
                        name="Level 1 Approval",
                        value={"status": "PENDING", "message": "Level 1 approved; awaiting final approval."}
                    ),
                    OpenApiExample(
                        name="Final Approval", 
                        value={"status": "APPROVED"}
                    )
                ]
            ),
            403: OpenApiResponse(description="Not authorized to approve"),
            400: OpenApiResponse(description="Cannot approve non-pending request")
        }
    )
    @action(detail=True, methods=['patch'], url_path='approve')
    def approve(self, request, pk=None):
        user = request.user
        profile = getattr(user, 'profile', None)
        if not profile or profile.role not in ['approver1', 'approver2']:
            return Response({"detail":"Not authorized to approve."}, status=status.HTTP_403_FORBIDDEN)

        pr = get_object_or_404(PurchaseRequest, pk=pk)
        serializer = ApproveRequestSerializer(data=request.data, context={'purchase_request': pr})
        serializer.is_valid(raise_exception=True)

        level = 1 if profile.role == 'approver1' else 2

        with transaction.atomic():
            pr_locked = PurchaseRequest.objects.select_for_update().get(pk=pr.pk)
            if pr_locked.status != 'PENDING':
                return Response({"detail":"Cannot approve non-pending request."}, status=status.HTTP_400_BAD_REQUEST)
                
            # Check if this user/level already has an approval
            existing_approval = Approval.objects.filter(request=pr_locked, level=level).first()
            if existing_approval:
                return Response({"detail":"Request has already been reviewed at this level."}, status=status.HTTP_400_BAD_REQUEST)
                
            Approval.objects.create(request=pr_locked, approver=user, level=level, approved=True, comment=request.data.get('comment',''))
            if level == 2:
                # CRITICAL FIX: Check Level 1 approval exists
                level1_approval = Approval.objects.filter(
                    request=pr_locked, level=1, approved=True
                ).first()
                if not level1_approval:
                    return Response({
                        "detail": "Level 1 approval required before Level 2"
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                pr_locked.status = 'APPROVED'
                pr_locked.approved_by = user
                pr_locked.save()
                
                # Generate PO on final approval
                try:
                    self._auto_generate_po(pr_locked)
                    logger.info(f"PO generated for approved request {pr_locked.id}")
                except Exception as e:
                    logger.error(f"PO generation failed for request {pr_locked.id}: {str(e)}")
                
                return Response({"status":"APPROVED"}, status=status.HTTP_200_OK)
            return Response({"status":"PENDING", "message":"Level 1 approved; awaiting final approval."}, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Reject Purchase Request",
        description="Reject a purchase request with optional comment. Rejection can happen at either approval level.",
        tags=["Approvals"], 
        request=OpenApiTypes.OBJECT,
        examples=[
            OpenApiExample(
                name="Rejection with Reason",
                value={
                    "comment": "Budget constraints. Please resubmit with reduced scope next quarter."
                }
            )
        ],
        responses={
            200: OpenApiResponse(
                description="Request rejected successfully",
                examples=[
                    OpenApiExample(
                        name="Rejection Response",
                        value={"status": "REJECTED"}
                    )
                ]
            ),
            403: OpenApiResponse(description="Not authorized to reject"),
            400: OpenApiResponse(description="Cannot reject non-pending request")
        }
    )
    @action(detail=True, methods=['patch'], url_path='reject')
    def reject(self, request, pk=None):
        user = request.user
        profile = getattr(user, 'profile', None)
        if not profile or profile.role not in ['approver1', 'approver2']:
            return Response({"detail":"Not authorized to reject."}, status=status.HTTP_403_FORBIDDEN)

        pr = get_object_or_404(PurchaseRequest, pk=pk)
        serializer = RejectRequestSerializer(data=request.data, context={'purchase_request': pr})
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            pr_locked = PurchaseRequest.objects.select_for_update().get(pk=pr.pk)
            if pr_locked.status != 'PENDING':
                return Response({"detail":"Cannot reject non-pending request."}, status=status.HTTP_400_BAD_REQUEST)
            lvl = 1 if profile.role == 'approver1' else 2
            
            # Check if this level already has an approval
            existing_approval = Approval.objects.filter(request=pr_locked, level=lvl).first()
            if existing_approval:
                return Response({"detail":"Request has already been reviewed at this level."}, status=status.HTTP_400_BAD_REQUEST)
                
            Approval.objects.create(request=pr_locked, approver=user, level=lvl, approved=False, comment=request.data.get('comment',''))
            pr_locked.status = 'REJECTED'
            pr_locked.save()
            return Response({"status":"REJECTED"}, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Submit Receipt", 
        description="Upload and validate receipt against purchase order using AI processing.",
        tags=["AI Processing"],
        request={
            'multipart/form-data': {
                'type': 'object',
                'properties': {
                    'receipt': {
                        'type': 'string',
                        'format': 'binary',
                        'description': 'Receipt file (PDF or image)'
                    }
                }
            }
        },
        responses={
            200: OpenApiResponse(
                description="Receipt uploaded and validated successfully",
                examples=[
                    OpenApiExample(
                        name="Valid Receipt",
                        value={
                            "message": "Receipt uploaded successfully",
                            "validation": {
                                "is_valid": True,
                                "discrepancies": [],
                                "receipt_data": {
                                    "vendor_name": "ABC Supplies Ltd",
                                    "total_amount": 1500.00,
                                    "currency": "USD"
                                }
                            }
                        }
                    )
                ]
            )
        }
    )
    @action(detail=True, methods=['post'], url_path='submit-receipt')
    def submit_receipt(self, request, pk=None):
        pr = get_object_or_404(PurchaseRequest, pk=pk)
        
        if request.user != pr.created_by:
            return Response({"detail": "Can only submit receipts for your own requests"}, status=status.HTTP_403_FORBIDDEN)
        
        if not pr.purchase_order_data:
            return Response({"detail": "No PO found - upload proforma first"}, status=status.HTTP_400_BAD_REQUEST)
        
        receipt_file = request.FILES.get('receipt')
        if not receipt_file:
            return Response({"detail": "No receipt file provided"}, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = ReceiptUploadSerializer(instance=pr, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        updated_pr = serializer.save()
        
        # Validate receipt against PO - trigger error if mismatch
        po_data = json.loads(updated_pr.purchase_order_data) if isinstance(updated_pr.purchase_order_data, str) else updated_pr.purchase_order_data
        validation_result = document_processor.validate_receipt(updated_pr.receipt.file, po_data)
        
        updated_pr.receipt_validation_data = validation_result
        updated_pr.save()
        
        if not validation_result.get('is_valid', False):
            return Response({
                'error': 'Receipt validation failed - mismatch detected',
                'discrepancies': validation_result.get('discrepancies', []),
                'validation': validation_result
            }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({
            'message': 'Receipt validated successfully',
            'validation': validation_result
        }, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Process Proforma Invoice",
        description="AI-powered extraction of data from uploaded proforma invoice using OCR and document processing.",
        tags=["AI Processing"],
        responses={
            200: OpenApiResponse(
                description="Proforma processed successfully",
                examples=[
                    OpenApiExample(
                        name="Extracted Data",
                        value={
                            "message": "Proforma processed successfully",
                            "extracted_data": {
                                "vendor_name": "ABC Supplies Ltd",
                                "vendor_email": "sales@abcsupplies.com",
                                "total_amount": 1500.00,
                                "currency": "USD", 
                                "items": [
                                    {
                                        "name": "Office Laptop",
                                        "quantity": 5,
                                        "unit_price": 800.00,
                                        "total_price": 4000.00
                                    }
                                ]
                            }
                        }
                    )
                ]
            ),
            400: OpenApiResponse(description="No proforma file uploaded"),
            500: OpenApiResponse(description="Processing failed")
        }
    )
    @action(detail=True, methods=['post'], url_path='process-proforma')
    def process_proforma(self, request, pk=None):
        """AI-powered proforma invoice processing and data extraction."""
        pr = get_object_or_404(PurchaseRequest, pk=pk)
        
        logger.info(f"Processing proforma for request {pk}, has proforma: {bool(pr.proforma)}")
        
        if not pr.proforma:
            return Response({
                'error': 'No proforma file uploaded',
                'request_id': pk
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Security: Validate proforma file
        try:
            _validate_file_security(pr.proforma)
        except ValidationError as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Extract data from proforma using AI
            extracted_data = document_processor.extract_proforma_data(pr.proforma.file)
            
            # Convert Decimal objects to float for JSON serialization
            def convert_decimals(obj):
                if isinstance(obj, dict):
                    return {k: convert_decimals(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [convert_decimals(item) for item in obj]
                elif hasattr(obj, '__float__'):
                    return float(obj)
                return obj
            
            # Store extracted data in the model
            pr.proforma_data = convert_decimals(extracted_data)
            pr.save()
            
            return Response({
                'message': 'Proforma processed successfully',
                'extracted_data': extracted_data
            }, status=status.HTTP_200_OK)
            
        except (ValidationError, ValueError) as e:
            logger.error(f"Proforma processing validation error for request {pr.id}: {str(e)}")
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.exception(f"Proforma processing failed for request {pr.id}: {str(e)}")
            return Response({
                'error': f'Proforma processing failed: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @extend_schema(
        summary="Generate Purchase Order",
        description="Automatically generate a purchase order from processed proforma data for approved requests.",
        tags=["AI Processing"],
        responses={
            200: OpenApiResponse(
                description="PO generated successfully",
                examples=[
                    OpenApiExample(
                        name="Generated PO",
                        value={
                            "message": "Purchase Order generated successfully",
                            "po_data": {
                                "po_number": "PO-20241126143000",
                                "vendor_name": "ABC Supplies Ltd",
                                "total_amount": 1500.00,
                                "status": "ISSUED",
                                "items": [],
                                "terms": "Payment Terms: Net 30 days..."
                            }
                        }
                    )
                ]
            ),
            400: OpenApiResponse(description="Can only generate PO for approved requests"),
            500: OpenApiResponse(description="PO generation failed")
        }
    )
    @action(detail=True, methods=['post'], url_path='generate-purchase-order')
    def generate_purchase_order(self, request, pk=None):
        """Generate Purchase Order from processed proforma data."""
        pr = get_object_or_404(PurchaseRequest, pk=pk)
        
        if pr.status != 'APPROVED':
            return Response({
                'error': 'Can only generate PO for approved requests'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Load proforma data
            proforma_data = {}
            if pr.proforma_data:
                proforma_data = json.loads(pr.proforma_data) if isinstance(pr.proforma_data, str) else pr.proforma_data
            
            # Prepare request data for PO generation
            request_data = {
                'created_by': pr.created_by.username,
                'department': pr.department,
                'urgency': pr.urgency,
                'justification': pr.justification
            }
            
            # Generate PO data using AI
            po_data = document_processor.generate_purchase_order_data(proforma_data, request_data)
            
            # Store PO data
            pr.purchase_order_data = json.dumps(po_data)
            pr.po_generated_at = timezone.now()
            pr.save()
            
            return Response({
                'message': 'Purchase Order generated successfully',
                'po_data': po_data
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'error': f'PO generation failed: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @extend_schema(
        summary="Analyze Document (Testing)",
        description="Generic document analysis endpoint for testing AI processing capabilities with various document types.",
        tags=["AI Processing"],
        parameters=[
            OpenApiParameter(
                name='type',
                description='Analysis type: proforma, receipt, or generic',
                required=False,
                type=str,
                default='proforma'
            )
        ],
        request={
            'multipart/form-data': {
                'type': 'object',
                'properties': {
                    'file': {
                        'type': 'string',
                        'format': 'binary',
                        'description': 'Document to analyze (PDF or image)'
                    },
                    'type': {
                        'type': 'string',
                        'enum': ['proforma', 'receipt', 'generic'],
                        'description': 'Type of analysis to perform'
                    }
                }
            }
        },
        responses={
            200: OpenApiResponse(
                description="Document analyzed successfully", 
                examples=[
                    OpenApiExample(
                        name="Analysis Result",
                        value={
                            "message": "Document analyzed successfully",
                            "analysis_type": "proforma",
                            "result": {
                                "vendor_name": "Extracted Company Name",
                                "total_amount": 1000.00,
                                "extracted_text": "Full document text..."
                            }
                        }
                    )
                ]
            ),
            400: OpenApiResponse(description="No file provided"),
            500: OpenApiResponse(description="Analysis failed")
        }
    )
    @action(detail=False, methods=['post'], url_path='analyze-document')
    def analyze_document(self, request):
        """Generic document analysis endpoint for testing AI capabilities."""
        if 'file' not in request.FILES:
            return Response({
                'error': 'No file provided'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        file = request.FILES['file']
        
        # Security: Validate uploaded file
        try:
            _validate_file_security(file)
        except ValidationError as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
        
        analysis_type = request.data.get('type', 'proforma')  # proforma, receipt, or generic
        
        try:
            if analysis_type == 'proforma':
                result = document_processor.extract_proforma_data(file)
            elif analysis_type == 'receipt':
                # For receipt analysis, we need PO data - use dummy data for testing
                dummy_po = {
                    'vendor_name': 'Test Vendor',
                    'total_amount': 100.00,
                    'items': []
                }
                result = document_processor.validate_receipt(file, dummy_po)
            else:
                # Generic text extraction - use public method
                try:
                    result = document_processor.extract_proforma_data(file)
                    result = {
                        'extracted_text': result.get('raw_text', ''),
                        'analysis': 'Generic document analysis completed'
                    }
                except Exception:
                    result = {
                        'extracted_text': 'Text extraction failed',
                        'analysis': 'Generic document analysis failed'
                    }
            
            return Response({
                'message': 'Document analyzed successfully',
                'analysis_type': analysis_type,
                'result': result
            }, status=status.HTTP_200_OK)
            
        except (ValidationError, ValueError) as e:
            logger.error(f"Document analysis validation error: {str(e)}")
            return Response({
                'error': 'Invalid document format'
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.exception(f"Document analysis failed: {str(e)}")
            return Response({
                'error': 'Document analysis failed'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _auto_generate_po(self, purchase_request):
        """Auto-generate PO when request is fully approved"""
        try:
            # Load proforma data if available
            proforma_data = {}
            if purchase_request.proforma_data:
                if isinstance(purchase_request.proforma_data, str):
                    proforma_data = json.loads(purchase_request.proforma_data)
                else:
                    proforma_data = purchase_request.proforma_data
            
            # Use request amount if no proforma data
            if not proforma_data.get('total_amount'):
                proforma_data['total_amount'] = float(purchase_request.amount)
                proforma_data['vendor_name'] = 'TBD - Vendor'
                proforma_data['currency'] = 'USD'
            
            # Prepare request data
            request_data = {
                'created_by': purchase_request.created_by.username,
                'title': purchase_request.title,
                'amount': str(purchase_request.amount)
            }
            
            # Generate PO data
            po_data = document_processor.generate_purchase_order_data(proforma_data, request_data)
            
            # Store PO data as JSON string
            purchase_request.purchase_order_data = json.dumps(po_data)
            purchase_request.po_generated_at = timezone.now()
            purchase_request.save()
            
            logger.info(f"PO generated successfully for request {purchase_request.id}")
            
        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"Invalid proforma data for PO generation in request {purchase_request.id}: {str(e)}")
            raise ValidationError("Invalid proforma data")
        except Exception as e:
            logger.exception(f"PO generation failed for request {purchase_request.id}: {str(e)}")
            raise


@api_view(['GET'])
@extend_schema(
    summary="Dashboard Statistics",
    description="Get procurement dashboard statistics including total, pending, approved, and rejected requests",
    tags=["Dashboard"],
    responses={
        200: OpenApiResponse(
            description="Dashboard statistics",
            examples=[
                OpenApiExample(
                    name="Stats Response",
                    value={
                        "total_requests": 25,
                        "pending_requests": 8,
                        "approved_requests": 15,
                        "rejected_requests": 2
                    }
                )
            ]
        )
    }
)
def dashboard_stats(request):
    """Get dashboard statistics for procurement requests"""
    user = request.user
    
    # Get base queryset based on user role
    base_queryset = PurchaseRequest.objects.all()
    profile = getattr(user, 'profile', None)
    if profile and getattr(profile, 'role', None) == 'staff':
        base_queryset = base_queryset.filter(created_by=user)
    
    # Performance optimization: Single aggregated query
    stats_data = base_queryset.aggregate(
        total_requests=Count('id'),
        pending_requests=Count(Case(When(status='PENDING', then=1), output_field=IntegerField())),
        approved_requests=Count(Case(When(status='APPROVED', then=1), output_field=IntegerField())),
        rejected_requests=Count(Case(When(status='REJECTED', then=1), output_field=IntegerField()))
    )
    
    return Response(stats_data)
