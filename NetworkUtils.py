import sys
import re
import os
import time
import subprocess
import pexpect
import OSUtils

def isHostUp(host):

	cmd="/bin/ping","-c","3",host;
	rc,rmsg=OSUtils.ExecCmd(cmd,1);
	
	return rc;
	
def isSSHUpOnHost(host):

	cmd="nmap","-p","22",host;
	rc,rmsg=OSUtils.ExecCmd(cmd,1);
	
	#[root@appdev31 exa]# nmap scae11cn02

	#Starting Nmap 4.11 ( http://www.insecure.org/nmap/ ) at 2015-01-26 22:21 PST
	#Interesting ports on scae11cn02.us.oracle.com (10.128.74.198):
	#Not shown: 1678 closed ports
	#PORT    STATE SERVICE
	#22/tcp  open  ssh
	#111/tcp open  rpcbind

	#Nmap finished: 1 IP address (1 host up) scanned in 0.675 seconds
	
	matchObj = re.search("tcp\s+open\s+ssh", rmsg, re.M|re.I)
	
	if matchObj:
		#print "SSH Service on "+host+" is up"
		return 0;	
	else:
		#print "SSH Service on "+host+" is NOT up"
		return 1;	
