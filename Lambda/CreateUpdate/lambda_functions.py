import json
import uuid
from datetime import datetime
from typing import Dict, Any
from common import DynamoDBBase, APIResponse, tracer, logger, Key


class CreateHandler(DynamoDBBase):
    """Handler class for CREATE operations on DynamoDB with X-Ray tracing"""

    @tracer.capture_method
    def create_item(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new item in DynamoDB"""
        if not data:
            raise ValueError("Item data is required")
        
        name = data.get('name')
        if not name:
            raise ValueError("Name is required")
        
        # Check if there's existing item with the same name
        if self.is_name_exists(name):
            raise ValueError("Item with the same name already exists")

        # Generate unique ID and timestamp
        item_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat()

        # Add tracing annotations and metadata
        tracer.put_annotation("operation", "create_item")
        tracer.put_annotation("item_id", item_id)
        tracer.put_metadata("input_data", data)

        logger.info("Creating new item", extra={"item_id": item_id, "data": data})

        # Prepare item with validation
        item = {
            'id': item_id,
            'name': name,
            'created_at': timestamp,
        }

        try:
            self.table.put_item(Item=item)

            # Add success metrics and logging
            tracer.put_annotation("success", True)
            logger.info("Item created successfully", extra={"item_id": item_id})

            return {
                'message': 'Item created successfully',
                'item': item
            }
        except Exception as e:
            # Add error tracking
            tracer.put_annotation("success", False)
            tracer.put_annotation("error", str(e))
            logger.error("Failed to create item", extra={"item_id": item_id, "error": str(e)})
            raise RuntimeError(f"Failed to create item: {str(e)}")
        
    
    @tracer.capture_method
    def update_item(self, item_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing item in DynamoDB"""
        if not data:
            raise ValueError("Item data is required")

        # Generate unique ID and timestamp
        timestamp = datetime.utcnow().isoformat()

        # Add tracing annotations and metadata
        tracer.put_annotation("operation", "update_item")
        tracer.put_metadata("input_data", data)
        
        # Check if item exists first
        response = self.table.get_item(Key={'id': item_id})
        if 'Item' not in response:
            raise ValueError(f"Item with id {item_id} not found")
        
        # Validate name if it's being updated
        name = data.get('name')
        if not name:
            raise ValueError("Name is required")
        
        # Check if there's existing item with the same name
        if self.is_name_exists(name):
            raise ValueError("Item with the same name already exists")
        item = response['Item']

        try:            
            # Update the item
            item["name"] = name
            item["updated_at"] = timestamp
            self.table.put_item(Item=item)
            
            # Get the updated item to return
            updated_response = self.table.get_item(Key={'id': item_id})
            item = updated_response['Item']

            # Add success metrics and logging
            tracer.put_annotation("success", True)
            logger.info("Item updated successfully", extra={"item_id": item_id})

            return {
                'message': 'Item updated successfully',
                'item': item
            }

        except Exception as e:
            # Add error tracking
            tracer.put_annotation("success", False)
            tracer.put_annotation("error", str(e))
            logger.error("Failed to create item", extra={"item_id": item_id, "error": str(e)})
            raise RuntimeError(f"Failed to create item: {str(e)}")
        

    def is_name_exists(self, name: str) -> bool:
        """Check if an item with the given name already exists"""
        response = self.table.query(
            IndexName='gsi-name',
            KeyConditionExpression=Key('name').eq(name)
        )
        return len(response.get('Items', [])) > 0


@tracer.capture_lambda_handler
def lambda_handler(event, context):
    """AWS Lambda handler function for CREATE operations"""
    try:
        # Add correlation ID and initial logging
        logger.info("Create Lambda invoked", extra={"event": event})
        
        # Initialize CREATE handler
        create_handler = CreateHandler()
        
        # Parse request details
        tracer.put_annotation("operation_type", "create")
        tracer.put_metadata("lambda_event", {
            "headers": event.get('headers', {}),
            "body": event.get('body')
        })
        
        # Parse body
        body = json.loads(event.get('body', '{}'))

        # check if there's an id in the body for update operation
        if 'id' in body:
            item_id = body.pop('id')
            result = create_handler.update_item(item_id, body)
        else:
            result = create_handler.create_item(body)

        # Add success tracking
        tracer.put_annotation("request_success", True)
        logger.info("Create request processed successfully", extra={"result": result})
        
        return APIResponse.success(result, 201)  # 201 Created
        
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