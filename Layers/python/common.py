import json
import boto3
import os
from decimal import Decimal
from typing import Dict, Any
from boto3.dynamodb.conditions import Key

# AWS X-Ray tracing and PowerTools
from aws_lambda_powertools import Tracer, Logger

# Initialize PowerTools
tracer = Tracer()
logger = Logger()


class DynamoDBBase:
    """Base class for DynamoDB operations with X-Ray tracing"""

    @tracer.capture_method
    def __init__(self):
        self.dynamodb = boto3.resource('dynamodb')
        self.table_name = os.environ.get('TABLE_NAME')
        if not self.table_name:
            raise ValueError("TABLE_NAME environment variable is required")
        self.table = self.dynamodb.Table(self.table_name)

        # Add tracing metadata
        tracer.put_metadata("dynamodb_table", self.table_name)
        logger.info("DynamoDBBase initialized", extra={"table_name": self.table_name})

    @tracer.capture_method
    def _validate_item_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and sanitize item data"""
        tracer.put_annotation("operation", "validate_data")
        
        if not isinstance(data, dict):
            tracer.put_annotation("validation_success", False)
            raise ValueError("Item data must be a dictionary")
        
        # Remove any None values
        validated = {k: v for k, v in data.items() if v is not None}
        
        # Add validation metrics
        tracer.put_annotation("fields_before_validation", len(data))
        tracer.put_annotation("fields_after_validation", len(validated))
        tracer.put_annotation("validation_success", True)
        
        return validated


class DecimalEncoder(json.JSONEncoder):
    """JSON encoder for DynamoDB Decimal types"""
    
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super().default(obj)


class APIResponse:
    """Helper class for creating standardized API responses"""
    
    @staticmethod
    def success(data: Dict[str, Any], status_code: int = 200) -> Dict[str, Any]:
        """Create a successful response"""
        return {
            'statusCode': status_code,
            'headers': APIResponse._get_cors_headers(),
            'body': json.dumps(data, cls=DecimalEncoder)
        }
    
    @staticmethod
    def error(message: str, status_code: int = 400) -> Dict[str, Any]:
        """Create an error response"""
        return {
            'statusCode': status_code,
            'headers': APIResponse._get_cors_headers(),
            'body': json.dumps({'error': message})
        }
    
    @staticmethod
    def _get_cors_headers() -> Dict[str, str]:
        """Get CORS headers"""
        return {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
            'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
        }


# Export commonly used items for easy import
__all__ = [
    'DynamoDBBase', 
    'DecimalEncoder', 
    'APIResponse', 
    'tracer', 
    'logger', 
    'metrics',
    'Key'
]