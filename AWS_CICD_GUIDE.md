# Your first AWS deployment with CI/CD

> Archived alternative: the active workflow is now `main.yml` using ECR and a self-hosted EC2 runner. Its requirements are in [EC2_CICD_NOTES.md](EC2_CICD_NOTES.md). The ECS Express/OIDC workflow files described below have been removed; these instructions do not apply to the active workflow. The unused bootstrap template and OIDC helper remain available for reference.

This guide is for this project. The automation files are implemented; a public deployment is complete only after the workflow succeeds in your GitHub and AWS accounts and the real URL passes its prediction check.

## What the pipeline does

```text
Change code and push to GitHub main
                 |
                 v
GitHub Actions: install dependencies and validate AWS template
                 |
                 v
Rebuild model from the prepared dataset -> run API tests
                 |
                 v
Build Docker image -> run container -> test health and prediction
                 |
          All checks passed?
          No: deployment stops
          Yes: continue when AWS is configured
                 |
                 v
Use temporary AWS credentials -> push image to Amazon ECR
                 |
                 v
Amazon ECS Express Mode runs the image on Fargate
                 |
                 v
Verify the public HTTPS frontend and prediction API
```

**CI** means automatically checking a change when it is integrated. Here it validates the infrastructure template, rebuilds the model, runs API tests, and runs a container smoke test.

**CD** means automatically delivering or deploying a change after the checks pass. Here successful `main` runs deploy automatically after AWS is configured. There is no manual approval gate inside this workflow. Pull requests do not deploy.

Rebuilding the final model from this fixed prepared dataset is not a full automated raw-data cleaning or model-selection system. The notebook research and preprocessing are separate.

## Step 1 — Create the repository and push

Create an empty GitHub repository. For a new repository, leave the initial README, license, and gitignore options unchecked because these files already exist locally. In this project folder, replace `YOUR_USERNAME` and `YOUR_REPOSITORY` below:

```powershell
git init -b main
git add .
git status --short
git commit -m "Add Flask frontend and AWS CI/CD workflow"
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPOSITORY.git
git push -u origin main
```

If Git asks for your identity, configure your own name and email before committing. Sign in to GitHub when the credential manager prompts you. If the repository is already initialized, reuse it instead of running initialization or adding the same remote again.

The gitignore excludes `*.pkl`, the virtual environment, local credentials, generated model CSV, and deployment archives. **Keep `train_model.py` and `gurgaon_properties_missing_value_imputation.csv` in the repository**: CI needs them to generate the model. GitHub blocks ordinary files larger than 100 MiB, so the approximately 140 MiB saved pipeline is not committed. See [GitHub's file-size documentation](https://docs.github.com/en/repositories/working-with-files/managing-large-files/about-large-files-on-github).

If model files were committed before this gitignore existed, they must also be removed from the Git index/history before pushing. Merely adding a gitignore does not remove an existing commit. Do not delete your working local model files.

## Step 2 — See the first CI run

Open the GitHub repository's **Actions** tab, then **Test and deploy to AWS**. The first run should train, test, and check the container. The deployment job is skipped while `AWS_ROLE_ARN` is unset; that is expected.

If any CI step fails, open that step's logs and fix it before configuring production deployment. Docker on the GitHub runner is sufficient for this pipeline; Docker Desktop on your own laptop is only required for local container testing.

## Step 3 — Get the exact AWS login subject

In **Actions**, select **Show AWS login subject**, click **Run workflow**, and choose branch **main**. Open its summary and copy the complete value beginning with `repo:`.

This is not a password. It identifies exactly which repository and branch AWS should trust. The script never prints the usable OIDC token.

New GitHub repositories can include immutable owner and repository IDs in this value. Copy the actual output rather than using a guessed `repo:owner/name:ref:refs/heads/main` string. See [GitHub's OIDC subject reference](https://docs.github.com/en/actions/reference/security/oidc).

## Step 4 — Prepare AWS using CloudShell

Sign in to the AWS console using an account with permission to create the template's ECR, ECS, log, and IAM resources. Do not share your password or access keys in chat. Choose the intended region, for example Mumbai (`ap-south-1`), and open **CloudShell** from the console.

Before deploying the application, review the charges for Fargate, Application Load Balancer, public networking, ECR storage, and logs. This is not guaranteed to be free. Express Mode itself adds no extra service fee; its underlying AWS resources are billed. This setup deliberately uses one running task, with 0.5 vCPU and 1 GiB RAM, and sets both the minimum and maximum task counts to one. See [AWS Express Mode pricing and behavior](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/express-service-overview.html).

Upload `infra/bootstrap.yaml` and `infra/bootstrap.sh` into a folder named `infra` in CloudShell, or upload `aws-cicd-source.zip` generated by `python scripts/package_cicd.py` and unzip it into a fresh working directory. CloudShell runs the shell script; it does not need your local Windows AWS CLI.

From the directory containing `infra`, run this command, replacing the first value with your actual subject:

```bash
bash infra/bootstrap.sh 'COPY_THE_EXACT_SUBJECT_HERE' ap-south-1 gurgaon-property-estimator
```

The script verifies the account identity, checks for a default VPC, reuses an existing GitHub OIDC provider if necessary, and deploys the bootstrap CloudFormation stack. The stack creates:

- An ECR repository for application images.
- An ECS cluster and a log group with seven-day log retention.
- A task execution role for pulling images and writing logs.
- An ECS infrastructure role for managing the public application infrastructure.
- A GitHub deployment role that trusts the exact main-branch OIDC subject.

The GitHub role can push only to this ECR repository. Its ECS deployment permissions are restricted to the selected region, and it can pass only the two application roles. Some ECS create and discovery APIs use `Resource: '*'`; this is not an AdministratorAccess policy. OIDC means you do not store permanent AWS access keys in GitHub. See [GitHub's AWS OIDC guide](https://docs.github.com/en/actions/how-tos/secure-your-work/security-harden-deployments/oidc-in-aws).

If there is no default VPC in the chosen region, the script stops. Select a region with the intended default VPC or add custom networking to the ECS configuration before deploying. A new account may require IAM permissions or service quotas to be enabled before resources can launch.

## Step 5 — Add the AWS variables in GitHub

The bootstrap script prints the actual values. Open:

**Repository → Settings → Secrets and variables → Actions → Variables → New repository variable**

Add all eight values:

| Variable | Purpose |
| --- | --- |
| `AWS_REGION` | Region containing the application resources. |
| `AWS_ROLE_ARN` | Role assumed by GitHub Actions using OIDC. |
| `AWS_EXECUTION_ROLE_ARN` | Role ECS uses to pull images and write logs. |
| `AWS_INFRASTRUCTURE_ROLE_ARN` | Role ECS uses to manage its supporting infrastructure. |
| `ECR_REPOSITORY` | Repository name for Docker images. |
| `ECS_CLUSTER` | ECS cluster name. |
| `ECS_SERVICE` | Application service name. |
| `CLOUDWATCH_LOG_GROUP` | Log group for the application. |

These identifiers are configuration values, not AWS secret keys. Keep the deploy workflow without a GitHub `environment:` setting unless you also update the OIDC trust subject: adding an environment changes that subject.

## Step 6 — Deploy and get your real URL

In **Actions → Test and deploy to AWS**, choose **Run workflow** on `main`. CI runs again. On success the deployment job:

1. Downloads the exact model artifacts from that CI run.
2. Gets temporary AWS credentials.
3. Builds a Linux Docker image and pushes a unique commit/run/attempt tag to ECR.
4. Creates or updates the ECS Express Mode service and waits for readiness.
5. Calls the deployed health endpoint and makes a real prediction.
6. Writes the actual endpoint, service ARN, image tag, and commit to the run summary.

Open the actual HTTPS endpoint in the summary, click **Load example**, and submit a prediction. Open it from another device too. That endpoint is your deployment URL for the interview. A subsequent successful push to `main` updates the same service.

AWS ECS Express Mode supports public HTTPS applications and creates the load balancer, TLS, networking, and Fargate service infrastructure. The action used here is [AWS's ECS Express deployment action](https://github.com/aws-actions/amazon-ecs-deploy-express-service). This project does not separately implement EC2, CodeDeploy, or an EC2 Auto Scaling Group.

AWS App Runner stopped accepting new customers on April 30, 2026, so the earlier App Runner walkthrough is superseded by this guide. See [AWS's availability notice](https://docs.aws.amazon.com/apprunner/latest/dg/apprunner-availability-change.html).

## If a step fails

| Failure | First check |
| --- | --- |
| `AssumeRoleWithWebIdentity` / access denied | Copy the exact OIDC subject, use `main`, and check the role ARN. |
| Missing repository variable | Add the exact values printed by the bootstrap script. |
| Failed to assume a new ECS role | Allow time for IAM propagation, then rerun the workflow. |
| No default VPC | Use the correct region or configure custom networking. |
| Container or health check fails | Open CloudWatch logs; confirm port 8000, `/api/health`, and that both model files are inside the image. |
| Task stops for insufficient memory | Review its logs/metrics and increase `memory` in the deployment step if necessary. |
| Duplicate image tags | Each attempt has a unique tag; do not replace the tag with a fixed `latest` in this immutable repository. |

Deployment runs are serialized so one deployment does not interrupt another. If the deployment or public smoke test fails, the workflow is marked failed; do not assume the previous version was automatically restored. Use the ECS console to inspect the running version and redeploy a previously verified ECR image if rollback is needed.

## Stop ongoing demo charges

After the demonstration, delete the **Express Mode service** in the ECS console and wait for its infrastructure cleanup. Stopping only the container or closing the browser is insufficient. Check the associated load balancer and networking resources and the billing console afterward.

Once the service is deleted, you can delete the bootstrap CloudFormation stack if no longer needed. The ECR repository and any created GitHub OIDC provider are retained deliberately; remove unused images/repositories after checking that nothing needs them. The OIDC provider can be shared by other repositories. Do not remove it if another project depends on it.

## Explain it in your interview after it succeeds

“I configured GitHub Actions for this Flask application. Pull requests run CI checks. A push to main rebuilds the final model from the prepared dataset, runs API tests, and builds and smoke-tests the Docker container. After the checks pass, the workflow assumes an AWS role using OIDC, pushes the image to ECR, and deploys it using ECS Express Mode on Fargate. It then verifies the public frontend and a real prediction. The image tag identifies the exact source commit and workflow attempt.”

If you have only prepared the files, say “I prepared and locally validated the pipeline; the AWS account setup and live run are pending.” Say it is deployed only after you can show the successful run and real URL.
