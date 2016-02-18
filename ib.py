import sys
import re
import os
import time
import subprocess
import pexpect
import OSUtils

def verifyNoPartitions(switch,user,password):
    
    rc=1;
    cmd="smpartition list active"
    
    (rc,rmsg,rout)=generic.ExecRemoteCmd(switch,user,password,"\["+user+"@.*?~\]",cmd);    
    
    pattern=re.compile(r'.*?ALL_SWITCHES=full;\s*$',re.M);
    
    if (pattern.search(rout)):
        return 0;
    else:
        return 1;