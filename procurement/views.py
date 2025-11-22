import json
from django.db import transaction
from django.utils import timezone
from rest_framework import viewsets, status, mixins
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter, OpenApiResponse, OpenApiExample
from drf_spectacular.types import OpenApiTypes

from .models import PurchaseRequest, Approval
from .serializers import (
    PurchaseRequestSerializer,
    PurchaseRequestCreateSerializer,
    PurchaseRequestUpdateSerializer,
    ApproveRequestSerializer,
    RejectRequestSerializer,
    ReceiptUploadSerializer,
)
from .document_processor import document_processor

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
    queryset = PurchaseRequest.objects.all().select_related('created_by')
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
        if profile and getattr(profile, 'role', None) == 'staff':
            return self.queryset.filter(created_by=user).order_by('-created_at')
        return self.queryset.order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

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
        if not profile or not str(profile.role).startswith('approver'):
            return Response({"detail":"Not authorized to approve."}, status=status.HTTP_403_FORBIDDEN)

        pr = get_object_or_404(PurchaseRequest, pk=pk)
        serializer = ApproveRequestSerializer(data=request.data, context={'purchase_request': pr})
        serializer.is_valid(raise_exception=True)

        level = 1 if profile.role == 'approver1' else 2

        with transaction.atomic():
            pr_locked = PurchaseRequest.objects.select_for_update().get(pk=pr.pk)
            if pr_locked.status != 'PENDING':
                return Response({"detail":"Cannot approve non-pending request."}, status=status.HTTP_400_BAD_REQUEST)
            Approval.objects.create(request=pr_locked, approver=user, level=level, approved=True, comment=request.data.get('comment',''))
            if level == 2:
                pr_locked.status = 'APPROVED'
                pr_locked.final_approved_by = user
                pr_locked.save()
                # TODO: generate PO sync/async (placeholder)
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
        if not profile or not str(profile.role).startswith('approver'):
            return Response({"detail":"Not authorized to reject."}, status=status.HTTP_403_FORBIDDEN)

        pr = get_object_or_404(PurchaseRequest, pk=pk)
        serializer = RejectRequestSerializer(data=request.data, context={'purchase_request': pr})
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            pr_locked = PurchaseRequest.objects.select_for_update().get(pk=pr.pk)
            if pr_locked.status != 'PENDING':
                return Response({"detail":"Cannot reject non-pending request."}, status=status.HTTP_400_BAD_REQUEST)
            lvl = 1 if profile.role == 'approver1' else 2
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
        serializer = ReceiptUploadSerializer(instance=pr, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        
        # Save the receipt file
        updated_pr = serializer.save()
        
        # AI-powered receipt validation
        validation_result = None
        if updated_pr.receipt and updated_pr.purchase_order_data:
            try:
                # Load PO data from JSON field
                po_data = json.loads(updated_pr.purchase_order_data) if isinstance(updated_pr.purchase_order_data, str) else updated_pr.purchase_order_data
                
                # Validate receipt against PO
                validation_result = document_processor.validate_receipt(
                    updated_pr.receipt.file, 
                    po_data
                )
                
                # Store validation results
                updated_pr.receipt_validation_data = json.dumps(validation_result)
                updated_pr.save()
                
            except Exception as e:
                validation_result = {
                    'error': f'Receipt validation failed: {str(e)}',
                    'is_valid': False
                }
        
        return Response({
            'message': 'Receipt uploaded successfully',
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
        
        if not pr.proforma:
            return Response({
                'error': 'No proforma file uploaded'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Extract data from proforma using AI
            extracted_data = document_processor.extract_proforma_data(pr.proforma.file)
            
            # Store extracted data in the model
            pr.proforma_data = json.dumps(extracted_data)
            pr.save()
            
            return Response({
                'message': 'Proforma processed successfully',
                'extracted_data': extracted_data
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
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
                # Generic text extraction
                text = document_processor._extract_text_from_file(file)
                result = {
                    'extracted_text': text,
                    'analysis': 'Generic document analysis completed'
                }
            
            return Response({
                'message': 'Document analyzed successfully',
                'analysis_type': analysis_type,
                'result': result
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'error': f'Document analysis failed: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response({"status":"RECEIPT_UPLOADED"}, status=status.HTTP_200_OK)
