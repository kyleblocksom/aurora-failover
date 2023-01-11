"""
Lambda to promote Aurora writer in secondary region then change R53 entries for reader and writer endpoints
"""
from __future__ import print_function

def lambda_handler(event, context):
    import json
    import time
    import boto3
    import os
    
    # Initialize
    client = boto3.client("rds")
    dnsclient = boto3.client("route53")
    
    # populate the existing environment information
    vGlobalClusterIdentifier = os.environ['GLOBAL_CLUSTER_NAME']
    vDbClusterIdentifier = os.environ['SECONDARY_CLUSTER_ARN']
    vHostedZoneId = os.environ['HOSTED_ZONE_ID']    

    try:
 
        # promote the secondary region aurora cluster
        response = client.remove_from_global_cluster(
            GlobalClusterIdentifier = vGlobalClusterIdentifier,
            DbClusterIdentifier = vDbClusterIdentifier
        )

        # check status of secondary region aurora cluster in regular intervals until it becomes available and write endpoint is enabled
        response = client.describe_db_clusters(
            DBClusterIdentifier=vDbClusterIdentifier
        )
        status = response["DBClusters"][0]["Status"]
        checkWriter = response["DBClusters"][0]["DBClusterMembers"][0]["IsClusterWriter"]

        while status != "available" or not checkWriter:
            time.sleep(30)
            response = client.describe_db_clusters(
                DBClusterIdentifier=vDbClusterIdentifier
            )
            status = response["DBClusters"][0]["Status"]
            checkWriter = response["DBClusters"][0]["DBClusterMembers"][0]["IsClusterWriter"]

        if status == "available" and checkWriter:
         
            readerendpoint = response["DBClusters"][0]["ReaderEndpoint"]
            writeendpoint = response["DBClusters"][0]["Endpoint"]
     
            # change the Route53 CNAME records with latest database endpoints 
            routeresponse = dnsclient.change_resource_record_sets(
                HostedZoneId=vHostedZoneId,
                ChangeBatch={
                    "Comment": "string",
                    "Changes": [
                        {
                            "Action": "UPSERT",
                            "ResourceRecordSet": {
                                "Name": "aurorareadendpoint.aurora_private_hosted_zone",
                                "Type": "CNAME",
                                "TTL": 1,
                                "ResourceRecords": [{"Value": readerendpoint}]
                            }
                        },
                        {
                            "Action": "UPSERT",
                            "ResourceRecordSet": {
                                "Name": "aurorawriteendpoint.aurora_private_hosted_zone",
                                "Type": "CNAME",
                                "TTL": 1,
                                "ResourceRecords": [{"Value": writeendpoint}]
                            }
                        }
                    ]
                }
            )
            print ("Successfully Promoted Aurora Primary to - " + vDbClusterIdentifier)
            return True

    except Exception as e:
        print(e)
        message = "Error promoting Aurora db cluster - " + vDbClusterIdentifier
        print(message)
        raise Exception(message)
