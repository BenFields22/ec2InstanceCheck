from collections import defaultdict
from datetime import datetime, timezone

import boto3


def get_ec2_instance_uptimes():
    # Create an EC2 client
    ec2 = boto3.client("ec2")

    # Retrieve all EC2 instances
    instances = ec2.describe_instances()

    # Calculate uptime for each instance
    uptimes = []
    for reservation in instances["Reservations"]:
        for instance in reservation["Instances"]:
            launch_time = instance["LaunchTime"]
            current_time = datetime.now(timezone.utc)
            uptime = current_time - launch_time
            uptime_str = str(uptime).split(".")[
                0
            ]  # Removing microseconds for readability
            instance_id = instance["InstanceId"]
            instance_state = instance["State"]["Name"]
            instance_type = instance["InstanceType"]
            uptimes.append((instance_id, instance_type, instance_state, uptime_str))

    return uptimes


def get_ec2_instance_uptimes_dict():

    # Create an EC2 client
    ec2 = boto3.client("ec2")

    # Retrieve all EC2 instances
    instances = ec2.describe_instances()

    # Calculate uptime for each instance
    instance_uptimes = defaultdict(list)
    for reservation in instances["Reservations"]:
        for instance in reservation["Instances"]:
            launch_time = instance["LaunchTime"]
            current_time = datetime.now(timezone.utc)
            uptime_seconds = (current_time - launch_time).total_seconds()
            instance_type = instance["InstanceType"]
            instance_uptimes[instance_type].append(uptime_seconds)

    return instance_uptimes


def calculate_average_uptime_by_type(instance_uptimes):
    average_uptimes = {}
    for instance_type, uptimes in instance_uptimes.items():
        average_seconds = sum(uptimes) / len(uptimes)
        # Convert seconds to more readable format: days, hours, minutes
        days = average_seconds // (24 * 3600)
        hours = (average_seconds % (24 * 3600)) // 3600
        minutes = (average_seconds % 3600) // 60
        average_uptimes[instance_type] = f"{int(days)}d {int(hours)}h {int(minutes)}m"

    return average_uptimes


def list_spot_interruptions_by_instance_type():
    # Initialize a session using your credentials

    # Create an EC2 client
    ec2 = boto3.client("ec2")

    # Retrieve all Spot Instance Requests
    paginator = ec2.get_paginator("describe_spot_instance_requests")
    pages = paginator.paginate()

    # Count interruptions by instance type
    interruption_counts = defaultdict(int)
    for page in pages:
        for request in page["SpotInstanceRequests"]:
            if (
                request["State"] == "closed"
                and request["Status"]["Code"] == "instance-terminated-by-experiment"
            ):
                instance_type = request["LaunchSpecification"]["InstanceType"]
                interruption_counts[instance_type] += 1

    return interruption_counts


def list_all_spot_instances():
    # Initialize a session using your credentials

    # Create an EC2 client
    ec2 = boto3.client("ec2")

    # Describe instances filtered by Spot lifecycle
    response = ec2.describe_instances(
        Filters=[{"Name": "instance-lifecycle", "Values": ["spot"]}]
    )

    # Extract and print instance details
    instances = []
    for reservation in response["Reservations"]:
        for instance in reservation["Instances"]:
            instance_id = instance["InstanceId"]
            instance_type = instance["InstanceType"]
            state = instance["State"]["Name"]
            instances.append((instance_id, instance_type, state))

    return instances


# Running the function and printing the results
if __name__ == "__main__":
    uptimes = get_ec2_instance_uptimes()
    uptimesbytype = get_ec2_instance_uptimes_dict()
    average_uptimes = calculate_average_uptime_by_type(uptimesbytype)
    interruptions = list_spot_interruptions_by_instance_type()
    print("------------ALL INSTANCES------------")
    for uptime in uptimes:
        print(
            f"Instance ID: {uptime[0]}, Type: {uptime[1]}, State: {uptime[2]}, Uptime: {uptime[3]}"
        )
    print("------------AVERAGES-------------")
    for instance_type, avg_uptime in average_uptimes.items():
        print(f"Instance Type: {instance_type}, Average Uptime: {avg_uptime}")
    print("-------------SPOT INSTANCES------------")
    spot_instances = list_all_spot_instances()
    for instance in spot_instances:
        print(f"Instance ID: {instance[0]}, Type: {instance[1]}, State: {instance[2]}")
    print("-------------SPOT INTERUPTS------------")
    print("Count: ", len(interruptions))
    for instance_type, count in interruptions.items():
        print(f"Instance Type: {instance_type}, Interruptions: {count}")

