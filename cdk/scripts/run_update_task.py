import boto3
import sys

REGION = "il-central-1"
CONTAINER_NAME = "MediaWikiContainer"
TASK_DEF_SUBSTRING = "Wiki7TaskDef"
CLUSTER_SUBSTRING = "ApplicationWiki7Cluster"

ecs = boto3.client("ecs", region_name=REGION)

def get_latest_task_definition():
    response = ecs.list_task_definitions(sort="DESC", maxResults=10)
    for arn in response.get("taskDefinitionArns", []):
        if TASK_DEF_SUBSTRING in arn:
            return arn
    print(f"No task definitions found with '{TASK_DEF_SUBSTRING}'")
    sys.exit(1)

def get_cluster_arn():
    response = ecs.list_clusters()
    for arn in response.get("clusterArns", []):
        if CLUSTER_SUBSTRING in arn:
            return arn
    print(f"No clusters found with '{CLUSTER_SUBSTRING}'")
    sys.exit(1)

def get_service_and_network_config(cluster_arn):
    response = ecs.list_services(cluster=cluster_arn, maxResults=10)
    service_arns = response.get("serviceArns", [])
    if not service_arns:
        print("No ECS services found in the cluster.")
        sys.exit(1)

    describe_response = ecs.describe_services(cluster=cluster_arn, services=service_arns)
    service = describe_response["services"][0]
    net_config = service.get("networkConfiguration", {}).get("awsvpcConfiguration", {})
    if not net_config:
        print("No network configuration found.")
        sys.exit(1)

    return service["serviceName"], net_config["subnets"], net_config["securityGroups"]

def run_update_php(cluster_arn, task_definition, subnets, security_groups):
    response = ecs.run_task(
        cluster=cluster_arn,
        launchType="FARGATE",
        taskDefinition=task_definition,
        networkConfiguration={
            "awsvpcConfiguration": {
                "subnets": subnets,
                "securityGroups": security_groups,
                "assignPublicIp": "ENABLED"
            }
        },
        overrides={
            "containerOverrides": [
                {
                    "name": CONTAINER_NAME,
                    "command": ["php", "maintenance/update.php"]
                }
            ]
        }
    )

    task_arn = response["tasks"][0]["taskArn"] if response.get("tasks") else "no-task"
    print(f"TASK_ARN::{task_arn}")

if __name__ == "__main__":
    cluster_arn = get_cluster_arn()
    task_def = get_latest_task_definition()
    _, subnets, sgs = get_service_and_network_config(cluster_arn)
    run_update_php(cluster_arn, task_def, subnets, sgs)
    