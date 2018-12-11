def lambda_handler(event, context):
    import boto3
    import datetime
    ports = set()
    public_cidr = {'CidrIp': '0.0.0.0/0'}
    html_body_inner = ""
    count = 0
    response = boto3.client("ec2").describe_regions()
    #Iterating over all regions
    for regname in response['Regions']:
        ec2 = boto3.client("ec2",region_name=regname['RegionName'])
        all_instances = ec2.describe_instances(Filters=[{'Name':
'instance-state-name', 'Values': ['running']}])
        for res in all_instances["Reservations"] :
            for instance in res["Instances"] :
                count = count + 1
                ports = set()
                size = instance["InstanceType"][instance["InstanceType"].find(".")+1:]
                # Checking if the running instance has open ports and
#fetching the list of open ports
                for SG in instance["SecurityGroups"] :
                    desc_sg = ec2.describe_security_groups(GroupIds=[SG["GroupId"]])
                    for sec_grp in desc_sg["SecurityGroups"] :
                        for ip_per in sec_grp["IpPermissions"] :
                            for cidr in ip_per["IpRanges"] :
                                if cidr == public_cidr :
                                   if ip_per.get("FromPort") :
                                       ports.add(ip_per["FromPort"])
                                   else :
                                       ports.add('ALL')

                #Print instance details if it has open ports
                if len(ports) == 0:
                    ports.add('-----')
                ports = ",".join(repr(e) for e in ports).replace("'", '')
                instance_name = "-----"
                if instance.get("Tags") :
                    for tag in instance["Tags"] :
                        if tag["Key"] == "Name" :
                            instance_name = tag["Value"]

                html_body_inner = html_body_inner +("<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td bgcolor=white>%s</td><td>%s</td><td bgcolor=white>%s</td></tr>"%(count,regname['RegionName'],instance["InstanceId"], instance_name,instance["InstanceType"], ports, instance["LaunchTime"].date()))
    #Create HTML Report
    html_body = "<!DOCTYPE html><html><body>"
    html_body = html_body + ("<h3>Total number of running instances : %s</h3>" %(count))
    html_body = html_body + '<table border="1" CELLPADDING=1 CELLSPACING=0 width="86%"><col width="2%"><col width="13%"><col width="17%"><col width="14%"><col width="5%"><col width="15%"><col width="10%"><col width="10%"><tr bgcolor="#5BAAF5"><th><font color="#fff">Sr.</font></th><th><font color="#fff">Region</font></th><th><font color="#fff">Instance Id</font></th><th><font color="#fff">Instance Name</font></th><th><font color="#fff">Type</font></th><th><font color="#fff">Publicly Open Ports</font></th><th><font color="#fff">Launch Date</font></th></tr>'
    html_body = html_body + html_body_inner + '</table></body></html>'

    #Send email notification
    ses = boto3.client('ses')
    ses.send_raw_email(        Source='bangashish@gmail.com',        Destinations=['bangashish@gmail.com'],        RawMessage= {'Data': 'Subject: AWS EC2 runninginstances\nMIME-Version: 1.0 \nContent-Type: text/html;\n\n' + html_body }
    )