import boto3
import json
from pkg_resources import resource_filename
from typing import List, Tuple, Dict
import csv
import sys

# Search product filter. This will reduce the amount of data returned by the
# get_products function of the Pricing API
FLT = '[{{"Field": "tenancy", "Value": "shared", "Type": "TERM_MATCH"}},'\
      '{{"Field": "operatingSystem", "Value": "{o}", "Type": "TERM_MATCH"}},'\
      '{{"Field": "preInstalledSw", "Value": "NA", "Type": "TERM_MATCH"}},'\
      '{{"Field": "instanceType", "Value": "{t}", "Type": "TERM_MATCH"}},'\
      '{{"Field": "location", "Value": "{r}", "Type": "TERM_MATCH"}},'\
      '{{"Field": "capacitystatus", "Value": "Used", "Type": "TERM_MATCH"}}]'


# Get current AWS price for an on-demand instance
def get_price(region, instance, os):
    f = FLT.format(r=region, t=instance, o=os)
    data = pricing_client.get_products(ServiceCode='AmazonEC2', Filters=json.loads(f))
    #print(data)
    if data['PriceList'] == []:
        return 0
    od = json.loads(data['PriceList'][0])['terms']['OnDemand']
    id1 = list(od)[0]
    id2 = list(od[id1]['priceDimensions'])[0]
    return od[id1]['priceDimensions'][id2]['pricePerUnit']['USD']

# Translate region code to region name. Even though the API data contains
## regionCode field, it will not return accurate data. However using the location
# # field will, but then we need to translate the region code into a region name.
# You could skip this by using the region names in your code directly, but most
# other APIs are using the region code.
def get_region_name(region_code):
    default_region = 'Europe (Frankfurt)'
    endpoint_file = resource_filename('botocore', 'data/endpoints.json')
    try:
        with open(endpoint_file, 'r') as f:
            data = json.load(f)
        # Botocore is using Europe while Pricing API using EU...sigh...
        return data['partitions'][0]['regions'][region_code]['description'].replace('Europe', 'EU')
    except IOError:
        return default_region

# https://www.programcreek.com/python/?CodeExample=list+instances
# https://github.com/ray-project/ray/blob/7425fa621245415e6a5a2d2b09d3f219e283e26b/release/ray_release/scripts/get_aws_instance_information.py
def get_aws_instance_information() -> List[Dict[str, Tuple[int, int, float]]]:
    rows = []

    args = {}
    while True:
        result = ec2_client.describe_instance_types(**args)

        for instance in result["InstanceTypes"]:
            rows.append(
                {
                    "instance": instance["InstanceType"],
                    "cpus": instance["VCpuInfo"]["DefaultVCpus"],
                    "mem (GB)": int(instance["MemoryInfo"]["SizeInMiB"])/1024,
                    "cost (USD)": get_price(get_region_name('eu-central-1'), instance["InstanceType"], 'Linux')
                }
            )

        if "NextToken" not in result:
            break

        args["NextToken"] = result["NextToken"]

    return rows

ec2_client = boto3.client("ec2", region_name='eu-central-1')

# Use AWS Pricing API through Boto3
# API only has us-east-1 and ap-south-1 as valid endpoints.
# It doesn't have any impact on your selected region for your instance.
pricing_client = boto3.client('pricing', region_name='us-east-1')

rows = []

rows += get_aws_instance_information()
#print((rows))
with open("D:\\00Research\\00Fog\\006Nikolay\\real-experiments\\processing-load\\type_cpu_memory_cost.csv", 'w') as file:
    writer = csv.DictWriter(file, fieldnames=["instance", "cpus", "mem (GB)", "cost (USD)"])
    writer.writeheader()
    for row in sorted(rows, key=lambda item: item["instance"]):
        writer.writerow(row)