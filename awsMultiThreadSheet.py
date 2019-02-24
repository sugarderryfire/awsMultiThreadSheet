import urllib2
import boto3
import time
import sys
import paramiko
import base64
import os
import random
import subprocess
import threading
import pandas as pd
import numpy as np


#global vars
regionList=["us-east-1","us-east-2","us-west-1","us-west-2","eu-west-2","ap-southeast-2","ap-northeast-1","eu-central-1"]
imageList=["ami-0ac019f4fcb7cb7e6","ami-0f65671a86f061fcd","ami-063aa838bd7631e0b","ami-0bbe6b35405ecebdb","ami-0b0a60c0a2bd40612","ami-07a3bd4944eb120a0","ami-07ad4b1c3af1ea214","ami-0bdf93799014acdc4"]
chosenImage=""
currentRegionName=""
currentImage=""
minInstances=2
maxInstances=4
ec2 = boto3.resource('ec2',region_name="us-east-1")
threads=[] # list of all the threads.
runningInstances=[]
limitCount=0
limitCounter=0


#create key pair in a random region.
def config_instances():
    global ec2
    regionIndex=0
    regionlistLength=len(regionList)
    regionRand=random.randint(regionIndex,regionlistLength-1) # get a random number between the region list length
    print regionList[regionRand]
    ec2 = boto3.resource('ec2',region_name=regionList[regionRand]) # create ec2 var from the random region.
    outfile = open('ec2keyInstance4.pem','w')
    key_pair = ec2.create_key_pair(KeyName='ec2keyInstance4')
    KeyPairOut = str(key_pair.key_material)
    outfile.write(KeyPairOut)
    os.system("chmod 400 ec2keyInstance4.pem")
    return regionRand



#return number of running instances.
def get_number_instances():
    # Boto 3
    # Use the filter() method of the instances collection to retrieve
    instancesNumber=0
    instances = ec2.instances.filter(
        Filters=[{'Name': 'instance-state-name', 'Values': ['running']}])
    for insta in instances:
	instancesNumber=instancesNumber+1
    return instancesNumber



#adding each running instance to our global list of running instances
def get_running_instances():
    global runningInstances
    instances = ec2.instances.filter(Filters=[{'Name': 'instance-state-name', 'Values': ['running']}])
    for instance in instances:
        if instance not in runningInstances:
	    runningInstances.append(instance.public_ip_address)
	    print(instance.id, instance.instance_type,instance.public_ip_address)
    return runningInstances



# create only 1 instance each call.
def create_instances():
    #create instances.
    global currentImage
    ec2_instances = ec2.create_instances(ImageId=currentImage,MinCount=1,MaxCount=1,KeyName="ec2keyInstance4",InstanceType='t2.micro')
    time.sleep(10)
    return ec2_instances


#check the index of the current thread.
def threadwhoami():
    global threads
    threadIndex=0
    t = threading.currentThread()
    for fred in threads:
        if t is fred:
            return threadIndex
        threadIndex=threadIndex+1
    threadIndex=-1 # if no threads in the list - return error -1.
    print 'error in threads index.'
    return threadIndex
            


#attach thread to an instance.
def attachThread2Instance():
    tIndex=threadwhoami()
    hostIP=runningInstances[tIndex]
    return hostIP
    


# execute all the commands with AutomainScript.
def commit_all(hostIP):
    mandatoryCommand="cat scr.sh | ssh -o StrictHostKeyChecking=no -i ec2keyInstance4.pem ubuntu@"
    mandatoryCommand=mandatoryCommand+hostIP
    key = paramiko.RSAKey.from_private_key_file('ec2keyInstance4.pem')
    client = paramiko.SSHClient()
    client.load_system_host_keys()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    # Connect/ssh to an instance
    try:
        # Here 'ubuntu' is user name and 'instance_ip' is public IP of EC2
        client.connect(hostname=hostIP, username="ubuntu", pkey=key)
        execute(client,'wget https://github.com/sugarderryfire/AutomAmazonFIles/blob/master/geckodriver?raw=true')
	execute(client,'mv geckodriver\?raw\=true geckodriver')
        execute(client,'wget https://raw.githubusercontent.com/sugarderryfire/AutomAmazonFIles/master/Automain.py')
        execute(client,'sudo apt -y install python')
        execute(client,'sudo apt update')
        execute(client,'sudo apt -y install python-pip')
	execute(client,'sudo pip install selenium')
	execute(client,'sudo pip install xlrd')
	execute(client,'sudo pip install pandas')
	execute(client,'sudo pip install openpyxl')
	execute(client,'sudo pip install stem')
	execute(client,'sudo pip install splinter')
	execute(client,'sudo apt -y install xvfb')
	time.sleep(5)
	print 'second stage'
        # Here 'ubuntu' is user name and 'instance_ip' is public IP of EC2
	execute(client,'sudo cp geckodriver /usr/local/bin/geckodriver')
	execute(client,'sudo chmod +x /usr/local/bin/geckodriver')
	execute(client,'sudo apt-get -y install firefox')
	time.sleep(5)
	print 'third stage'
        # Here 'ubuntu' is user name and 'instance_ip' is public IP of EC2
        client.connect(hostname=hostIP, username="ubuntu", pkey=key)
	execute(client,'sudo apt -y install xvfb')
	mandatoryCommand=mandatoryCommand+" &"
	os.system(mandatoryCommand)
	time.sleep(get_random(480,700))
        # close the client connection once the job is done
   	client.close()
	print 'finish commands'
    except Exception, e:
        print e


def execute(client,command):
    try:
        print 'running remote command'
        # Execute a command(cmd) after connecting/ssh to an instance
        stdin, stdout, stderr = client.exec_command(command)
        print stdout.read()
    except Exception, e:
        print e



def get_random(min1,max1):
    chosenNumber=random.randint(min1-1,max1-1)
    return chosenNumber



#terminate instances and clean list of instances and occupied instances threads.
def terminate_instances():
    global ec2, runningInstances
    print 'terminate'
    #terminate instances in ec2_instances arr
    instances = ec2.instances.filter(
        Filters=[{'Name': 'instance-state-name', 'Values': ['running']}])
    for instance in instances:
	instance.terminate()
	print instance.public_ip_address
    runningInstances=[]



#need to be cinfigured to the current region with key pair
def delete_key_pair(ec3):
    #ec2 = boto3.client('ec2',region_name="us-east-1")
    response = ec3.delete_key_pair(KeyName='ec2keyInstance4')
    

#start function for each thread. each thread create instances and execute modular functions.
def start_func(regionRand,instancesRandNumber):
    global currentImage
    #create the main program
    currentImage=imageList[regionRand] # get the current image by using regionRand number
    print 'Creating instances'
    print currentImage
    create_instances()
    #time.sleep(80)
    instancesNumber=get_number_instances()
    while(instancesNumber!=instancesRandNumber-1):
        time.sleep(random.randint(30,50))
        instancesNumber=get_number_instances()
    get_running_instances() # will be executed # of threads times. #save list of running instances IPs.
    hostIP=attachThread2Instance()
    commit_all(hostIP) # for a specific thread.    


    
#creating threads.
def createThreads(regionRand):
    global ec2,minInstances,maxInstances
    instancesRandNumber=random.randint(minInstances,maxInstances) # get a random number between the min max instances vars
    print 'rand is '
    print instancesRandNumber
    for inst in range(1,instancesRandNumber):
	t=threading.Thread(target=start_func,args=[regionRand,instancesRandNumber])
	threads.append(t)
	t.start()
    for thr in threads:
	thr.join()
    terminate_instances()
    ec3 = boto3.client('ec2',region_name=regionList[regionRand])
    delete_key_pair(ec3)


def changeFilescr(keyword,ID):
    line1="#!/bin/bash\n"
    line2="/usr/bin/Xvfb :99 -ac -screen 0 1024x768x8 & export DISPLAY=:99\n"
    filea=open('scr.sh','w')
    filea.write(line1)
    filea.write(line2)
    lineCommand='python Automain.py '
    lineCommand=lineCommand+keyword + ' ' + ID
    filea.write(lineCommand)
    filea.close()



def checkFinishXLSX():
    global limitCount,limitCounter
    if(limitCounter==limitCount+1):
	limitCounter=0
	

def incrementCounter():
    global limitCounter
    limitCounter=limitCounter+1


def readKeyword():
    global limitCount,limitCounter
    data=pd.read_excel('https://github.com/sugarderryfire/awsMultiThreadSheet/blob/master/kidum.xlsx?raw=true',sheet_name='sheet1')
    limitCount = len(data['keyword'])
    changeFilescr(data['keyword'][limitCounter],data['appID'][limitCounter])
    incrementCounter()
    checkFinishXLSX()
	



def main():
    while(True):
	regionRand=config_instances()
	readKeyword()
	createThreads(regionRand) # then each thread create instance.
	time.sleep(100)
	


if __name__ == "__main__":
    main()
