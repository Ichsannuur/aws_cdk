#!/usr/bin/env python3

import aws_cdk as cdk

from cdk_tutorial.cdk_tutorial_stack import CdkTutorialStack


app = cdk.App()
CdkTutorialStack(app, "CdkTutorialStack", env=cdk.Environment(region="ap-southeast-1"))

app.synth()
