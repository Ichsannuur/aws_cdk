# MYPATTERNS

# AWS CDK CRUD Patterns - Items Management System

This document outlines the architectural patterns and best practices used in this AWS CDK project for implementing a simple, cost-effective CRUD (Create, Read, Update, Delete) system for items management.

## Project Overview

A learning project focused on implementing basic CRUD operations in AWS using CDK with Python. The system manages items data with the following operations:

- **Create/Update** items
- **Get** item by ID  
- **List** all items
- **Delete** item (with referential integrity checks)

## Architecture Patterns

### 1. Serverless CRUD Pattern

```
API Gateway → Lambda Functions → DynamoDB
```

**Components:**
- **API Gateway REST API**: Single entry point with resource-based routing
- **Lambda Functions**: One function per CRUD operation  
- **DynamoDB**: NoSQL database for data persistence
- **IAM Roles**: Pre-existing role for Lambda execution

### 2. CDK Stack Organization Pattern

**File Structure:**
```
cdk_tutorial/
├── app.py                      # CDK application entry point
├── cdk.json                    # CDK configuration  
├── config.py                   # Environment configuration
├── requirements.txt            # Python dependencies
├── requirements-dev.txt        # Development dependencies
├── README.md                   # Project documentation
├── cdk_tutorial/               # CDK stack modules
│   ├── __init__.py
│   └── cdk_tutorial_stack.py   # Main stack definition
├── Lambda/                     # Lambda function code
│   ├── CreateUpdate/           # Create/Update operations
│   ├── List/                   # List all items
│   └── Delete/                 # Delete operations
├── Layers/                     # Shared Lambda layers
│   └── python/
│       ├── __init__.py
│       └── common.py           # Shared utilities (DynamoDBBase, APIResponse)
└── tests/                      # Test files
```

### 3. Configuration Management Pattern

**Environment-Based Configuration:**
- Uses dataclass for type safety
- Environment-specific configurations (dev/prod)
- Property methods for computed values
- Table name: "ItemsTable"
- Region: "ap-southeast-1"
- Log levels: DEBUG for dev, ERROR for prod

### 4. Lambda Layer Pattern

**Shared Utilities Structure:**
- Common utilities layer containing shared classes
- DynamoDBBase class for database operations
- APIResponse helper for standardized responses  
- X-Ray tracer and logger integration
- DecimalEncoder for JSON serialization

## Implementation Patterns

**Stack Organization:**
1. **Configuration Loading**: Environment-specific settings via get_config()
2. **IAM Role Setup**: Uses existing role via role ARN reference
3. **Lambda Layers**: External layers + local common utilities layer
4. **Lambda Functions**: One function per CRUD operation (CreateItems, ListItems, DeleteItems)
5. **API Gateway**: REST API with stage-based deployment
6. **Resource Routing**: /items endpoints with method mappings

### 2. Lambda Function Pattern

**Standard Configuration:**
- Runtime: Python 3.9
- Timeout: 30 seconds
- Memory: 128MB
- X-Ray tracing: Always enabled
- Layers: Base layer + Generic layer + Common utilities
- Environment variables from config

**Handler Structure:**
- Import from common layer (DynamoDBBase, APIResponse, tracer, logger)
- Handler class inherits from DynamoDBBase
- Method-level tracing with annotations
- Standardized error handling and responses

### 3. API Gateway Pattern

**Resource Structure:**
- `/items` - GET (list all items)
- `/items/create` - POST (create/update items)
- `/items/{id}` - DELETE (delete item by ID)

**Configuration:**
- Manual deployment control (deploy=False)
- Stage-based configuration
- X-Ray tracing enabled
- Environment-specific data tracing
- CORS enabled for all origins and methods

### 4. External Resource Reference Pattern

**External AWS Resources:**
- Uses existing IAM role via `iam.Role.from_role_arn()`
- References external Lambda layers via `LayerVersion.from_layer_version_arn()`
- Uses existing DynamoDB table (not created by CDK stack)
- External resources referenced through ARNs and environment variables

### 5. API Gateway Deployment Control Pattern

**Manual Deployment Management:**
- API created with `deploy=False` for explicit control
- Separate `Deployment` and `Stage` constructs
- Environment-specific stage configuration
- CloudFormation outputs for API endpoints

**DynamoDB Configuration:**
- Uses existing DynamoDB table (ItemsTable)
- Table name provided through environment variables
- Primary key: 'id' (String)
- Additional item attributes as needed
- **Note:** Table is external - not created by this CDK stack

**Base Database Operations:**
- DynamoDBBase class provides common database operations
- X-Ray tracing on all database methods
- Standard CRUD operations: create, read, list, delete
- Error handling and validation
- Referential integrity checks for delete operations
## Item-Specific Operations

### 1. Create/Update Item
**Endpoint:** `POST /items/create`
**Functionality:**
- Creates new item with unique ID
- Updates existing item by name
- Validates required fields (name)
- Checks for duplicate names
- Adds timestamps (created_at, updated_at)

### 2. List Items  
**Endpoint:** `GET /items`
**Functionality:**
- Returns all items
- Handles pagination if needed
- Includes all item attributes

### 3. Delete Item
**Endpoint:** `DELETE /items/{id}`  
**Functionality:**
- Deletes item by ID
- Performs referential integrity checks
- Returns appropriate error if item doesn't exist
## Observability Patterns

### 1. X-Ray Tracing
**Implementation:**
- Enabled on all Lambda functions
- Enabled on API Gateway stage
- Custom annotations for business metrics
- Method-level tracing decorators

**Features:**
- Operation tracking and performance monitoring
- Validation success/failure metrics
- Request correlation across services

### 2. AWS PowerTools Integration Pattern
**Components:**
- **Tracer**: X-Ray integration with method-level tracing decorators
- **Logger**: Structured logging with correlation IDs

**Usage Pattern:**
```python
from aws_lambda_powertools import Tracer, Logger
tracer = Tracer()
logger = Logger()

@tracer.capture_method  # Method-level tracing
def operation():
    tracer.put_annotation("key", "value")  # Custom annotations
    logger.info("message", extra={"field": "value"})  # Structured logging
```

**Configuration:**
- Environment-specific log levels (DEBUG/ERROR)
- Correlation IDs for request tracking
- Structured log format with extra fields
- X-Ray tracing metadata and annotations
## Security Patterns

### 1. IAM Configuration
**Approach:**
- Uses pre-existing IAM role (`iam.Role.from_role_arn()`)
- Follows least privilege principle
- Separate roles for different environments

### 2. Environment Variables
**Pattern:**
### 2. Environment Variables
**Pattern:**
- TABLE_NAME and LOG_LEVEL passed to Lambda functions
- Stage-specific configuration values
- No hardcoded sensitive information

### 3. CORS Security
**Configuration:**
- Allows all origins (consider restricting in production)
- Supports GET, POST, DELETE, OPTIONS methods
- Includes standard headers for authentication
- Applied to all API resources and methods

## Deployment Patterns

### 1. Dependency Management Pattern
**Requirements:**
- `aws-cdk-lib==2.215.0` - Core CDK library
- `constructs>=10.0.0,<11.0.0` - CDK constructs
- `aws-lambda-powertools==3.21.0` - PowerTools for observability
- `requirements-dev.txt` for development dependencies

### 2. Multi-Environment Deployment
**Commands:**
- Development: `cdk deploy --context stage=dev`
- Production: `cdk deploy --context stage=prod`

### 3. Application Entry Point
**app.py Structure:**
- CDK app initialization
- Stage detection from context (`app.node.try_get_context("stage")`)
- Environment-specific stack creation
- AWS account and region configuration
- Single stack deployment with stage parameter