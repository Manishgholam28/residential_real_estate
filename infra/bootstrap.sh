#!/usr/bin/env bash
# Run in AWS CloudShell after reading AWS_CICD_GUIDE.md.
set -euo pipefail

subject="${1:?Usage: bash infra/bootstrap.sh 'EXACT_OIDC_SUBJECT' [REGION] [APP_NAME]}"
region="${2:-ap-south-1}"
app_name="${3:-gurgaon-property-estimator}"
script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"

python3 - "$subject" "$app_name" <<'PY'
import re, sys
if not re.fullmatch(r'repo:[A-Za-z0-9_.@/-]+:ref:refs/heads/main', sys.argv[1]):
    raise SystemExit('Copy the exact subject from the Show AWS login subject workflow on main.')
if not re.fullmatch(r'[a-z][a-z0-9-]{2,39}', sys.argv[2]):
    raise SystemExit('Use an app name of 3–40 lowercase letters, digits, and hyphens.')
PY

echo 'Confirm the AWS account below is the account you intend to use:'
aws sts get-caller-identity --query '{Account:Account,Arn:Arn}' --output table

default_vpc="$(aws ec2 describe-vpcs --region "$region" --filters Name=is-default,Values=true --query 'Vpcs[0].VpcId' --output text)"
if [[ "$default_vpc" == 'None' || -z "$default_vpc" ]]; then
  echo 'No default VPC exists in this region. Use a region with a default VPC, or configure custom ECS networking before deploying.' >&2
  exit 1
fi

existing_oidc="$(aws iam list-open-id-connect-providers --query "OpenIDConnectProviderList[?ends_with(Arn, '/token.actions.githubusercontent.com')].Arn | [0]" --output text)"
if [[ "$existing_oidc" == 'None' ]]; then existing_oidc=''; fi
# Keep the create condition unchanged if this stack already owns the provider.
owned_oidc="$(aws cloudformation describe-stack-resource --region "$region" --stack-name "${app_name}-ci-bootstrap" --logical-resource-id GitHubOidcProvider --query 'StackResourceDetail.PhysicalResourceId' --output text 2>/dev/null || true)"
if [[ -n "$owned_oidc" && "$owned_oidc" == "$existing_oidc" ]]; then existing_oidc=''; fi

aws cloudformation deploy \
  --region "$region" \
  --stack-name "${app_name}-ci-bootstrap" \
  --template-file "$script_dir/bootstrap.yaml" \
  --capabilities CAPABILITY_IAM \
  --no-fail-on-empty-changeset \
  --parameter-overrides "AppName=$app_name" "GitHubOidcSubject=$subject" "ExistingOidcProviderArn=$existing_oidc"

outputs="$(aws cloudformation describe-stacks --region "$region" --stack-name "${app_name}-ci-bootstrap" --query 'Stacks[0].Outputs' --output json)"
python3 - "$outputs" <<'PY'
import json, sys
mapping = {
    'AwsRegion': 'AWS_REGION', 'GitHubRoleArn': 'AWS_ROLE_ARN',
    'TaskExecutionRoleArn': 'AWS_EXECUTION_ROLE_ARN',
    'InfrastructureRoleArn': 'AWS_INFRASTRUCTURE_ROLE_ARN',
    'EcrRepository': 'ECR_REPOSITORY', 'EcsCluster': 'ECS_CLUSTER',
    'EcsService': 'ECS_SERVICE', 'LogGroup': 'CLOUDWATCH_LOG_GROUP',
}
print('\nAdd these as GitHub repository Actions VARIABLES (not access-key secrets):\n')
for item in json.loads(sys.argv[1]):
    print(f"{mapping[item['OutputKey']]}={item['OutputValue']}")
PY

echo 'Bootstrap complete. Add the variables, then run Test and deploy to AWS on main.'
