# Prerequisites for your ECR and EC2 workflow

The active workflow is `.github/workflows/main.yml`. It follows your chosen approach: GitHub-hosted jobs test and publish an image, then a self-hosted runner on EC2 runs that image. It uses AWS credentials from GitHub repository secrets, not OIDC or ECS Express Mode.

## Configure these before deploying

1. Create a private ECR repository in your chosen AWS region. The workflow uses a unique commit/run/attempt tag; it does not require a mutable `latest` tag.
2. In GitHub **Settings -> Secrets and variables -> Actions -> Secrets**, add `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION`, and `ECR_REPOSITORY_NAME`. Use an IAM user's keys with ECR login and push/pull permissions for this repository, not AWS root-account keys. Do not put these values in source files. `AWS_ECR_LOGIN_URI` is unnecessary: the ECR login action obtains the registry address.
3. Use a Linux x86_64 EC2 instance. Install Docker and Python 3. The runner's user must be able to run `docker info` without sudo. Leave enough memory for both the loaded model and the operating system.
4. In GitHub **Settings -> Actions -> Runners -> New self-hosted runner**, choose Linux x64 and follow the current displayed commands on your EC2 instance. Keep the runner online, preferably as a service. The workflow matches the default `self-hosted`, `Linux`, and `X64` labels; ensure that the matching runner belongs to this application instance. See [GitHub's runner setup instructions](https://docs.github.com/en/actions/how-tos/manage-runners/self-hosted-runners/add-runners).
5. The instance must have a public IP/DNS and an internet route. Allow inbound TCP port **8080** in its security group from the clients that need the demo. Allow SSH only from your own address if you use SSH. Check any host firewall too.

## What happens on a push

- **Continuous Integration:** installs Python dependencies, checks syntax, trains `pipeline.pkl` and `df.pkl` from the prepared CSV, and runs the real API tests. Syntax checking is not a full style linter.
- **Continuous Delivery:** downloads those same tested models, builds the Linux image, checks its frontend and prediction API, publishes it to ECR, and passes its digest and original tag as job outputs.
- **Continuous Deployment:** logs in to ECR on the EC2 runner, pulls the exact digest supplied by the successful build job, replaces only the `mltest` container, and verifies the application locally on EC2. A deploy-only retry reuses that published image instead of constructing a tag from the retry attempt number.

Jobs do not share a filesystem. Artifact upload/download transfers the model files between the first two jobs. The `.pkl` files stay excluded from Git; `train_model.py` and `gurgaon_properties_missing_value_imputation.csv` must be committed.

The application listens on port 8000 inside Docker. `8080:8000` exposes it on port 8080 of EC2. After the run succeeds, open **`http://YOUR_EC2_PUBLIC_IP:8080`**, substituting your real address, and make a prediction from your own browser. The runner's localhost test cannot establish public access. This direct demo endpoint uses HTTP; TLS requires additional configuration.

Repeat deployments remove the previous named container after the image has been pulled. This causes brief downtime and does not implement automatic rollback. `--restart unless-stopped` restarts the container after a host reboot when Docker starts. The application receives no AWS access keys because its predictions use local model files. The workflow does not prune unrelated Docker containers or images.

The workflow runs on pushes to `main` except changes affecting only the root README. You can also run it manually from **Actions -> workflow -> Run workflow** on `main`. EC2 and ECR resources incur AWS charges; delete resources you no longer need after practice.

## If a job fails

- **Missing repository secret:** add all four exact names under Secrets, not Variables.
- **ECR repository not found or access denied:** check its name, region, AWS account, and IAM permissions.
- **Image tag not found after retrying only deployment:** the earlier workflow recomputed a tag using the retry attempt number even though the image had been published in a previous attempt. The current workflow passes the successful build's digest into deployment. Commit and push this fix to start a new complete run; retrying an old run uses its old workflow. Keep the AWS account, region, and repository secrets consistent between publishing and deployment, and do not delete the referenced image from ECR.
- **Deployment queued:** the matching EC2 self-hosted runner is offline or not registered.
- **Cannot access Docker:** check the Docker service and runner user's permissions.
- **Local prediction check fails:** inspect `docker logs mltest` on EC2.
- **Local check passes but browser fails:** check the public address, internet routing, inbound TCP 8080, and host firewall.

## Exit code 137 / a Python process is killed

Exit 137 indicates SIGKILL; it does not by itself prove an out-of-memory event. If the deployment's small standard-library smoke-test process is killed, check memory pressure on the EC2 host. The application, Docker, runner, and operating system share the instance's RAM. A local measurement of the current application image showed about 395 MiB of steady container memory after prediction; it is not a measurement of the EC2 host or startup peak.

Run these in the EC2 terminal before restarting it:

```bash
free -h
sudo journalctl -k --no-pager | grep -Ei 'out of memory|oom|killed process' | tail -20
docker stats --no-stream mltest
```

The workflow prints host memory before deployment, and memory, container state, logs, and available kernel OOM evidence after a failure. Kernel log access may require running the command yourself with sudo. A container's `OOMKilled=false` does not rule out the kernel killing the smoke-test process outside the container.

If the kernel confirms OOM on a t3.micro (1 GiB), t3.small (2 GiB) is a reasonable next size to try; monitor memory after rerunning rather than assuming the issue is resolved. Changing instance type requires stopping the instance and has different AWS charges. A stop/start changes the ordinary public IPv4 address unless an Elastic IP is used. Restart the GitHub runner if it is not installed as a service, ensure it is online, then rerun the workflow and test the new public address. See [AWS's instance specifications](https://aws.amazon.com/ec2/instance-types/t3/) and [instance-type change instructions](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/change-instance-type-of-ebs-backed-instance.html).

**Status:** the workflow being present is not proof of a successful GitHub run or live AWS deployment. Verify the actual run and public prediction before describing it as deployed.
