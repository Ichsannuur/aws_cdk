#!/usr/bin/env python3

import aws_cdk as cdk

from cdk_tutorial.cdk_tutorial_stack import CdkTutorialStack
from config import get_config

app = cdk.App()

stage = app.node.try_get_context("stage") or "dev"
config = get_config(stage)

CdkTutorialStack(
    app,
    "CdkTutorialStack",
    env=cdk.Environment(region=config.region),
    stage=stage
)

app.synth()
