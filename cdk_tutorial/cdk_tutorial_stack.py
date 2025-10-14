from aws_cdk import (
    Duration,
    Stack,
    aws_dynamodb as dynamodb,
    aws_lambda as _lambda,
    aws_iam as iam,
    aws_apigateway as apigateway,
    CfnOutput,
)
from constructs import Construct


class CdkTutorialStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        lambda_role = iam.Role.from_role_arn(
            self, "LambdaRole",
            role_arn="arn:aws:iam::460278301291:role/LambdaRole",
        )

        lambda_dir = './Lambda/'

        lambda_base_layer = _lambda.LayerVersion.from_layer_version_arn(
            self, "LambdaBaseLayer",
            layer_version_arn="arn:aws:lambda:ap-southeast-1:460278301291:layer:LambdaBaseLayer:4"
        )

        generic_layer = _lambda.LayerVersion.from_layer_version_arn(
            self, "GenericLayer",
            layer_version_arn="arn:aws:lambda:ap-southeast-1:460278301291:layer:GenericLayer:19"
        )

        # Create Lambda function with X-Ray tracing
        create_items = _lambda.Function(
            self, "CreateItems",
            runtime=_lambda.Runtime.PYTHON_3_9,
            code=_lambda.Code.from_asset(lambda_dir + 'CreateUpdate'),
            handler="lambda_functions.lambda_handler",
            role=lambda_role,
            layers=[lambda_base_layer, generic_layer],
            timeout=Duration.seconds(30),
            memory_size=128,
            tracing=_lambda.Tracing.ACTIVE,  # Enable X-Ray tracing
            environment={
                "TABLE_NAME": "ItemsTable",
                "LOG_LEVEL": "INFO"
            }
        )

        # List Lambda function with X-Ray tracing
        list_items = _lambda.Function(
            self, "ListItems",
            runtime=_lambda.Runtime.PYTHON_3_9,
            code=_lambda.Code.from_asset(lambda_dir + 'List'),
            handler="lambda_functions.lambda_handler",
            role=lambda_role,
            layers=[lambda_base_layer, generic_layer],
            timeout=Duration.seconds(30),
            memory_size=128,
            tracing=_lambda.Tracing.ACTIVE,  # Enable X-Ray tracing
            environment={
                "TABLE_NAME": "ItemsTable",
                "LOG_LEVEL": "INFO"
            }
        )

        # Delete Lambda function with X-Ray tracing
        delete_items = _lambda.Function(
            self, "DeleteItems",
            runtime=_lambda.Runtime.PYTHON_3_9,
            code=_lambda.Code.from_asset(lambda_dir + 'Delete'),
            handler="lambda_functions.lambda_handler",
            role=lambda_role,
            layers=[lambda_base_layer, generic_layer],
            timeout=Duration.seconds(30),
            memory_size=128,
            tracing=_lambda.Tracing.ACTIVE,  # Enable X-Ray tracing
            environment={
                "TABLE_NAME": "ItemsTable",
                "LOG_LEVEL": "INFO"
            }
        )

        # Create API Gateway
        api = apigateway.RestApi(
            self, "CRUD-API",
            rest_api_name="Simple CRUD API",
            deploy=False,
            description="Simple CRUD API with Lambda and DynamoDB",
        )

        rest_api_deployment = apigateway.Deployment(
            self, "Deployment",
            api=api,
            retain_deployments=True
        )

        rest_api_stage = apigateway.Stage(
            self, "Stage",
            deployment=rest_api_deployment,
            stage_name="dev",
            tracing_enabled=True,
            data_trace_enabled=True,
            logging_level=apigateway.MethodLoggingLevel.ERROR
        )

        api.deployment_stage = rest_api_stage

        # Add /items resource
        items_resource = api.root.add_resource("items")
        create_resource = items_resource.add_resource("create")
        # Add path parameter for delete: /items/{id}
        delete_resource = items_resource.add_resource("{id}")

        # Enable CORS for /items
        items_resource.add_cors_preflight(
            allow_origins=apigateway.Cors.ALL_ORIGINS,
            allow_methods=["GET", "POST", "DELETE", "OPTIONS"]
        )

        # Enable CORS for /items/create
        create_resource.add_cors_preflight(
            allow_origins=apigateway.Cors.ALL_ORIGINS,
            allow_methods=["POST", "OPTIONS"]
        )

        # Enable CORS for /items/{id}
        delete_resource.add_cors_preflight(
            allow_origins=apigateway.Cors.ALL_ORIGINS,
            allow_methods=["DELETE", "POST", "OPTIONS"]
        )

        # Add methods to /items
        items_resource.add_method(
            "GET",
            apigateway.LambdaIntegration(list_items),
        )

        # Add methods to /items/create
        create_resource.add_method(
            "POST",
            apigateway.LambdaIntegration(create_items),
        )

        # Add methods to /items/{id}
        delete_resource.add_method(
            "DELETE",
            apigateway.LambdaIntegration(delete_items),
        )

        # Output the API endpoint
        CfnOutput(
            self, "APIEndpoint",
            value=api.url,
            description="API Gateway endpoint URL"
        )