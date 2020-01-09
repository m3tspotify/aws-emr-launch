#!/usr/bin/env python3

import os

from aws_cdk import (
    aws_ec2 as ec2,
    aws_s3 as s3,
    core
)

from aws_emr_launch.constructs.emr_constructs import (
    emr_code,
    cluster_configuration
)

app = core.App()
stack = core.Stack(app, 'ClusterConfigurationsStack', env=core.Environment(
    account=os.environ["CDK_DEFAULT_ACCOUNT"],
    region=os.environ["CDK_DEFAULT_REGION"]))

vpc = ec2.Vpc.from_lookup(stack, 'Vpc', vpc_id='vpc-01c3cc44009934845')
artifacts_bucket = s3.Bucket.from_bucket_name(stack, 'ArtifactsBucket', 'chamcca-emr-launch-artifacts-uw2')

# This prepares the project's bootstrap_source/ folder for deployment
# We use the Artifacts bucket configured and authorized on the EMR Profile
bootstrap_code = emr_code.Code.from_path(
    path='./bootstrap_source',
    deployment_bucket=artifacts_bucket,
    deployment_prefix='emr_launch_testing/bootstrap_source')

# Define a Bootstrap Action using the bootstrap_source/ folder's deployment location
bootstrap = emr_code.EMRBootstrapAction(
    name='bootstrap-1',
    path=f'{bootstrap_code.s3_path}/test_bootstrap.sh',
    args=['Arg1', 'Arg2'],
    code=bootstrap_code)

# Cluster Configurations that use InstanceGroups are deployed to a Private subnet
subnet = vpc.private_subnets[0]

# Create a basic Cluster Configuration using InstanceGroups, the Subnet and Bootstrap
# Action defined above, the EMR Profile we loaded, and defaults defined in
# the InstanceGroupConfiguration
basic_cluster_config = cluster_configuration.InstanceGroupConfiguration(
    stack, 'BasicClusterConfiguration',
    configuration_name='basic-instance-group-cluster',
    subnet=subnet,
    bootstrap_actions=[bootstrap],
    step_concurrency_level=2)

# Here we create another Cluster Configuration using the same subnet, bootstrap, and
# EMR Profile while customizing the default Instance Type and Instance Count
high_mem_cluster_config = cluster_configuration.InstanceGroupConfiguration(
    stack, 'HighMemClusterConfiguration',
    configuration_name='high-mem-instance-group-cluster',
    subnet=subnet,
    bootstrap_actions=[bootstrap],
    step_concurrency_level=5,
    core_instance_type='r5.2xlarge',
    core_instance_count=2)

app.synth()
