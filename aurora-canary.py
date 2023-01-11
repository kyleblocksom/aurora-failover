import json
import boto3
import time
from datetime import datetime
from datetime import timedelta
from botocore.vendored import requests

#demo code; not production code
def querySite():
    response = requests.get('http://<Enter-ELB-DNS-Name-Here>', timeout=3)
    if response.status_code > 200:
        raise Exception("failed")
        
def cnameChange():
    HOSTED_ZONE_ID = '<Enter-R53-Hosted-Zone-ID-Here>'
    DNS_RECORD_NAME = '<Enter-R53-Record-Name-Here>'
    VALUE = '<Enter-ELB-DNS-Name-Here>'
    client1 = boto3.client('route53')

    response = client1.change_resource_record_sets(
    ChangeBatch={
        'Changes': [
            {
                'Action': 'UPSERT',
                'ResourceRecordSet': {
                    'Name': DNS_RECORD_NAME,
                    'TTL': 1,
                    'Type': 'CNAME',
                    'ResourceRecords': [
                        {
                            'Value': VALUE,
                        },
                    ],
                    'Weight': 0,
                    'SetIdentifier': 'us-east-1'
                },
            },
        ],
    },
    HostedZoneId=HOSTED_ZONE_ID,
    )
    
def lambda_handler(event, context):
    statusCode=200
    now = datetime.now()
    end= now + timedelta(seconds = 50)
    failures=0
    
    while (datetime.now()<end):
        try:
            querySite()
        except Exception as e:
            failures=failures+1
        if failures>1:
            cnameChange()
            return {
                'statusCode': 500
            }
        time.sleep(10)
    return {
        'statusCode': statusCode
    }
