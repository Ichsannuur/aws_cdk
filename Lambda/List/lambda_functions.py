# filepath: /Users/ichsannuur/Documents/Backend Project/cdk_tutorial/Layers/python/common.py
import json
import boto3
import os
from decimal import Decimal
from typing import Dict, Any

# AWS X-Ray tracing and PowerTools
from aws_lambda_powertools import Tracer, Logger, Metrics
from aws_lambda_powertools.metrics import MetricUnit

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


class Handler(DynamoDBBase):
    """Handler class for CREATE operations on DynamoDB with X-Ray tracing"""

    @tracer.capture_method
    def get_all_items(self) -> Dict[str, Any]:
        """Retrieve all items from DynamoDB"""
        try:
            # Add tracing annotations
            tracer.put_annotation("operation", "get_all_items")
            logger.info("Fetching all items from DynamoDB", extra={"table_name": self.table_name})

            response = self.table.scan()
            items = response.get('Items', [])

            # Add success annotations and metadata
            tracer.put_annotation("success", True)
            tracer.put_metadata("item_count", len(items))
            logger.info("Items fetched successfully", extra={"item_count": len(items)})

            return {
                "items": items,
                "count": len(items)
            }

        except Exception as e:
            # Add error tracking
            tracer.put_annotation("success", False)
            tracer.put_annotation("error", str(e))
            logger.error("Failed to fetch items", extra={"error": str(e)})
            raise RuntimeError(f"Failed to fetch items: {str(e)}")


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


@tracer.capture_lambda_handler
def lambda_handler(event, context):
    """AWS Lambda handler function for LIST operations"""
    try:
        # Add correlation ID and initial logging
        logger.info("List Lambda invoked", extra={"event": event})

        # Initialize handler
        handler = Handler()

        # Parse request details
        tracer.put_annotation("operation_type", "get_all_items")
        tracer.put_metadata("lambda_event", {
            "headers": event.get('headers', {}),
            "body": event.get('body')
        })

        # Perform the operation
        result = handler.get_all_items()

        # Add success tracking
        tracer.put_annotation("request_success", True)
        logger.info("Get all items request processed successfully", extra={"result": result})
        
        return APIResponse.success(result, 200)
        
    except ValueError as e:
        # Client errors (bad input)
        tracer.put_annotation("request_success", False)
        tracer.put_annotation("error_type", "client_error")
        tracer.put_annotation("error_message", str(e))
        logger.error("Client error", extra={"error": str(e)})
        return APIResponse.error(str(e), 400)
        
    except RuntimeError as e:
        # Server errors (database issues, etc.)
        tracer.put_annotation("request_success", False)
        tracer.put_annotation("error_type", "server_error")
        tracer.put_annotation("error_message", str(e))
        logger.error("Server error", extra={"error": str(e)}, exc_info=True)
        return APIResponse.error(f"Internal server error: {str(e)}", 500)
        
    except Exception as e:
        # Unexpected errors
        tracer.put_annotation("request_success", False)
        tracer.put_annotation("error_type", "unexpected_error")
        tracer.put_annotation("error_message", str(e))
        logger.error("Unexpected error", extra={"error": str(e)}, exc_info=True)
        return APIResponse.error(f"Internal server error: {str(e)}", 500)