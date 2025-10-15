# AWS CDK CRUD API Design Guidelines

## Overview
This document outlines the design principles, architectural patterns, and best practices used in our AWS CDK-based CRUD API project. These guidelines ensure consistency, maintainability, and scalability across similar projects.

## Project Architecture

### High-Level Architecture
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   API Gateway   │────│   Lambda Funcs  │────│    DynamoDB     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
        │                        │
        │                ┌─────────────────┐
        │                │   Lambda Layers │
        │                └─────────────────┘
        │
┌─────────────────┐
│   X-Ray Tracing │
└─────────────────┘
```

## Design Principles

### 1. Separation of Concerns
- **Configuration Management**: Centralized in `config.py` with environment-specific settings
- **Infrastructure**: Defined in CDK stack classes
- **Business Logic**: Isolated in Lambda functions
- **Common Utilities**: Shared via Lambda layers

### 2. Environment Isolation
- Clear separation between development and production environments
- Environment-specific configuration management
- Stage-based resource naming and settings

### 3. Observability First
- AWS X-Ray tracing enabled for all Lambda functions and API Gateway
- Structured logging using AWS Lambda PowerTools
- Environment-specific log levels (DEBUG for dev, ERROR for prod)

### 4. Security Best Practices
- IAM roles with least privilege principle
- CORS configuration for API endpoints
- Environment variable injection for sensitive configuration

## Infrastructure Standards

### CDK Stack Structure
```python
class CdkTutorialStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, stage: str = None, **kwargs):
        # 1. Configuration loading
        # 2. IAM roles and permissions
        # 3. Lambda layers
        # 4. Lambda functions
        # 5. API Gateway setup
        # 6. Outputs and exports
```

### Naming Conventions
- **Stack Names**: `{ProjectName}Stack` (e.g., `CdkTutorialStack`)
- **Resource Names**: PascalCase with descriptive names (e.g., `CreateItems`, `ListItems`)
- **API Names**: `{Purpose}-API` (e.g., `CRUD-API`)
- **Stage Names**: Lowercase environment names (`dev`, `prod`)

### Resource Configuration Standards

#### Lambda Functions
```python
# Standard Lambda configuration
lambda_function = _lambda.Function(
    self, "FunctionName",
    runtime=_lambda.Runtime.PYTHON_3_9,
    code=_lambda.Code.from_asset(lambda_dir + 'FunctionDir'),
    handler="lambda_functions.lambda_handler",
    role=lambda_role,
    layers=[lambda_base_layer, generic_layer, common_layer],
    timeout=Duration.seconds(30),
    memory_size=128,
    tracing=_lambda.Tracing.ACTIVE,  # Always enable X-Ray
    environment=config.lambda_env_vars
)
```

#### API Gateway
```python
# Standard API Gateway configuration
api = apigateway.RestApi(
    self, "API-Name",
    rest_api_name=f"API Description - {config.stage_name}",
    deploy=False,  # Manual deployment control
    description="API purpose description",
)

# Always enable tracing and appropriate logging
rest_api_stage = apigateway.Stage(
    self, "Stage",
    deployment=rest_api_deployment,
    stage_name=config.stage_name,
    tracing_enabled=True,
    data_trace_enabled=config.stage_name != "prod",
    logging_level=apigateway.MethodLoggingLevel.ERROR
)
```

## Configuration Management

### Environment Configuration Structure
```python
@dataclass
class Config:
    region: str
    stage_name: str
    table_name: str
    log_level: str

    @property
    def lambda_env_vars(self):
        return {
            "TABLE_NAME": self.table_name,
            "LOG_LEVEL": self.log_level
        }
```

### Environment-Specific Settings
- **Development**: DEBUG logging, data tracing enabled
- **Production**: ERROR logging, data tracing disabled
- Use dataclass for type safety and property methods for computed values

## Lambda Architecture

### Directory Structure
```
Lambda/
├── CreateUpdate/
│   └── lambda_functions.py
├── List/
│   └── lambda_functions.py
└── Delete/
    └── lambda_functions.py
```

### Handler Pattern
```python
import json
from typing import Dict, Any
from common import DynamoDBBase, APIResponse, tracer, logger

class OperationHandler(DynamoDBBase):
    @tracer.capture_method
    def operation_method(self, data: Dict[str, Any]) -> Dict[str, Any]:
        # Implementation with tracing annotations
        tracer.put_annotation("operation", "operation_name")
        # ... business logic
        return result

@tracer.capture_lambda_handler
def lambda_handler(event, context):
    try:
        handler = OperationHandler()
        # Process event and return response
        return APIResponse.success(data, 200)
    except Exception as e:
        return APIResponse.error(str(e), 500)
```

## Layer Architecture

### Common Layer Structure
```
Layers/
└── python/
    ├── __init__.py
    └── common.py
```

### Base Classes and Utilities
- `DynamoDBBase`: Abstract base class for database operations
- `APIResponse`: Standardized API response formatting
- `tracer`: AWS X-Ray tracer instance
- `logger`: AWS Lambda PowerTools logger

## API Design Standards

### RESTful Endpoint Structure
```
/items                  # GET (list all items)
/items/create          # POST (create new item)
/items/{id}            # DELETE (delete specific item)
```

### CORS Configuration
```python
# Enable CORS for all relevant methods
resource.add_cors_preflight(
    allow_origins=apigateway.Cors.ALL_ORIGINS,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"]
)
```

### Response Standards
- Success responses: HTTP 200/201 with data payload
- Error responses: Appropriate HTTP status codes with error messages
- Consistent JSON structure across all endpoints

## Security Guidelines

### IAM Configuration
- Use existing IAM roles when possible: `iam.Role.from_role_arn()`
- Follow least privilege principle
- Environment-specific role ARNs

### Environment Variables
- Never hardcode sensitive values
- Use environment variables for configuration
- Validate required environment variables at runtime

## Monitoring and Observability

### X-Ray Tracing
- Enable tracing on all Lambda functions
- Enable tracing on API Gateway stages
- Use tracing annotations for business metrics
- Add metadata for debugging context

### Logging Standards
```python
# Use structured logging
logger.info("Operation completed", extra={
    "operation": "create_item",
    "item_id": item_id,
    "execution_time": execution_time
})
```

### Error Handling
- Comprehensive exception handling in Lambda functions
- Meaningful error messages for API responses
- Proper HTTP status codes for different error types

## Deployment Guidelines

### CDK Application Structure
```python
app = cdk.App()
stage = app.node.try_get_context("stage") or "dev"
config = get_config(stage)

Stack(
    app,
    "StackName",
    env=cdk.Environment(region=config.region),
    stage=stage
)
```

### Stage Management
- Use CDK context for stage selection
- Default to "dev" environment
- Environment-specific resource configuration

## Testing Standards

### Unit Testing
- Test Lambda handlers independently
- Mock AWS services using moto or similar
- Test configuration loading and validation

### Integration Testing
- Test API endpoints end-to-end
- Validate CORS configuration
- Test error scenarios and edge cases

## Performance Guidelines

### Lambda Configuration
- Memory: Start with 128MB, adjust based on monitoring
- Timeout: 30 seconds for CRUD operations
- Use layers to reduce deployment package size

### DynamoDB Optimization
- Proper primary key design
- Use consistent naming conventions
- Implement proper error handling for throttling

## Maintenance and Updates

### Dependency Management
- Pin CDK versions for consistency
- Regular security updates for dependencies
- Use requirements.txt and requirements-dev.txt separation

### Documentation Requirements
- Inline code documentation
- API endpoint documentation
- Architecture decision records (ADRs)

## Common Anti-Patterns to Avoid

1. **Hardcoded Values**: Always use configuration management
2. **Missing Tracing**: Every Lambda should have X-Ray enabled
3. **Inconsistent Naming**: Follow established naming conventions
4. **Missing CORS**: Always configure CORS for web applications
5. **Poor Error Handling**: Implement comprehensive exception handling
6. **Environment Mixing**: Keep environments strictly separated