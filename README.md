# metaflow-intent-prediction
An end-to-end implementation of intent prediction with Metaflow and other cool tools


### Configure Metaflow

If you have an AWS profile configured with a metaflow-friendly user, and you created 
metaflow stack with CloudFormation, you can run the following command with the resources
created by CloufFormation to set up metaflow on AWS:

`metaflow configure aws --profile metaflow`

Remember to use `METAFLOW_PROFILE=metaflow` to use this profile when running a flow. Once
you completed the [setup](https://admin-docs.metaflow.org/metaflow-on-aws/deployment-guide/aws-cloudformation-deployment), you can run `flow_playground.py` to test the AWS setup is working
as expected (in particular, GPU batch jobs can run correctly). To run the flow with the
custom profile created, you should do:

`METAFLOW_PROFILE=metaflow python flow_playground.py run`