from typing import Dict, Any
from common import DynamoDBBase, APIResponse, tracer, logger


class DeleteHandler(DynamoDBBase):
    """Handler class for DELETE operations on DynamoDB with X-Ray tracing"""

    @tracer.capture_method
    def delete_item(self, item_id: str) -> Dict[str, Any]:
        """Delete an item from DynamoDB"""
        if not item_id:
            raise ValueError("Item ID is required")

        # Add tracing annotations and metadata
        tracer.put_annotation("operation", "delete_item")
        tracer.put_annotation("item_id", item_id)

        logger.info("Deleting item", extra={"item_id": item_id})

        try:
            # Check if item exists first
            response = self.table.get_item(Key={'id': item_id})
            if 'Item' not in response:
                raise ValueError(f"Item with id {item_id} not found")

            # Delete the item
            self.table.delete_item(Key={'id': item_id})

            # Add success metrics and logging
            tracer.put_annotation("success", True)
            logger.info("Item deleted successfully", extra={"item_id": item_id})

            return {
                'message': 'Item deleted successfully',
            }
            
        except Exception as e:
            # Add error tracking
            tracer.put_annotation("success", False)
            tracer.put_annotation("error", str(e))
            logger.error("Failed to delete item", extra={"item_id": item_id, "error": str(e)})
            raise RuntimeError(f"Failed to delete item: {str(e)}")





@tracer.capture_lambda_handler
def lambda_handler(event, context):
    """AWS Lambda handler function for DELETE operations"""
    try:
        # Add correlation ID and initial logging
        logger.info("Delete Lambda invoked", extra={"event": event})
        
        # Initialize DELETE handler
        delete_handler = DeleteHandler()
        
        # Parse request details
        tracer.put_annotation("operation_type", "delete")
        tracer.put_metadata("lambda_event", {
            "headers": event.get('headers', {}),
            "pathParameters": event.get('pathParameters', {})
        })
        
        # Get item ID from path parameters
        path_parameters = event.get('pathParameters') or {}
        item_id = path_parameters.get('id')
        
        if not item_id:
            raise ValueError("Item ID is required in path parameters")

        # Perform delete operation
        result = delete_handler.delete_item(item_id)

        # Add success tracking
        tracer.put_annotation("request_success", True)
        logger.info("Delete request processed successfully", extra={"result": result})
        
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