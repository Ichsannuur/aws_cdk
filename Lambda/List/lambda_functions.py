from typing import Dict, Any
from common import DynamoDBBase, APIResponse, tracer, logger


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