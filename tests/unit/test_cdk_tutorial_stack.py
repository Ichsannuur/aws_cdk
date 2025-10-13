import aws_cdk as core
import aws_cdk.assertions as assertions

from cdk_tutorial.cdk_tutorial_stack import CdkTutorialStack

# example tests. To run these tests, uncomment this file along with the example
# resource in cdk_tutorial/cdk_tutorial_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = CdkTutorialStack(app, "cdk-tutorial")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
