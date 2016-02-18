import os.path
import sys
import re
import os
import time
import subprocess
import pexpect

def isProcessRunning(psName):
    
    rc=1;
    rmsg=None;
    
    cmd_str="/bin/ps","-af";
    
    (rc,rmsg)=ExecCmd(cmd_str,0);
    
    pattern=re.compile(r".*?"+psName+".*?",re.M|re.I);
    
    if (pattern.search(rmsg)):
        return 0;
    else:
        return 1;
    
def ExecCmd (command,debug):

	rc=1
	cmd_output="";
	cmd_error="";
        debug=1;

	try:

		if ( debug ):
			print "Command to execute:",command;

		cmd = subprocess.Popen(command,stdout=subprocess.PIPE, stderr=subprocess.STDOUT);
		
		# Poll cmd for new output until finished
		while True:
			if cmd.poll() != None:
				break

		cmd_output, cmd_error = cmd.communicate();
		rc = cmd.returncode

		if ( debug ):
			print "ExecCmd-Command output:",cmd_output
			print "ExecCmd-Command error:",cmd_error
			print "ExecCmd-Return Code:",rc

	except :

			if ( debug ):
				print "Error",cmd_error
				print "Output",cmd_output
	

	return (rc,cmd_output)

def ExecRemoteCmd(host,user,password,string_to_match,command):

	cmd_output=""
	debug=1
	rc=1;
	rmsg=""

	child = pexpect.spawn('ssh',['-o','UserKnownHostsFile=/dev/null',user+'@'+host]);
	if (debug):
		child.logfile = sys.stdout
		
	(rc,rmsg,cmd_output)=JustType(child,"Are you sure you want to continue connecting.*","yes");
	if(rc==1):
		return 1;

	rc,rmsg,cmd_output=JustType(child,".*?(P|p)assword:",password);
	if(rc==1):
		return 1;
		
	try:
		index = child.expect (string_to_match,timeout=600);
		if index == 0:
			child.sendline(str(command));
	except pexpect.EOF:
		if ( debug ):
			print "Connection dropped while executing command"
		return (1,"Connection dropped while executing command",cmd_output);
	except pexpect.TIMEOUT:
		if ( debug ):
			print "Timed out while executing command"
		return (1,"Connection dropped while executing command",cmd_output);

        cmd_output=child.after;
        
	try:
		index = child.expect (string_to_match,timeout=900);
    		if index == 0:
                        cmd_output=child.before;
			child.sendline("exit");			
	except pexpect.EOF:
		if ( debug ):
			print "Connection dropped while executing command"
		return (1,"Connection dropped while executing command",cmd_output);
	except pexpect.TIMEOUT:
		if ( debug ):
			print "Timed out while executing command"
		return (1,"Connection dropped while executing command",cmd_output);
        
	return (0,"Successfully executed command",cmd_output);


def JustType(child,string_to_match,command):
    
	debug=1;
	cmd_output="";
    
	try:
		index = child.expect (string_to_match,timeout=60);
		if index == 0:
                    child.sendline(str(command))
                    cmd_output=child.after
	except pexpect.EOF:
		if ( debug ):
			print "Connection dropped while executing command"
		return (1,"Connection dropped while executing command",cmd_output);
	except pexpect.TIMEOUT:
		if ( debug ):
			print "Timed out while executing command"
		return (1,"Connection dropped while executing command",cmd_output);
	
        #index = child.expect (string_to_match,timeout=60);
        #if index == 0:
        #    cmd_output=child.before
        
        return (0,"Successfully executed command",cmd_output);

def Sftp(host,user,password,src,target):
    
    cmd_output=""
    debug=1
    rc=1;
    rmsg=""
    child = "";

    sftpCmd='sftp -o UserKnownHostsFile=/dev/null '+user+'@'+host;
    putCmd='put '+src;
    
    child = pexpect.spawn(sftpCmd);

    if (debug):
            child.logfile = sys.stdout

    (rc,rmsg,cmd_output)=JustType(child,"Are you sure you want to continue connecting.*","yes");
    if(rc==1):
            return 1;

    rc,rmsg,cmd_output=JustType(child,".*?(P|p)assword:",password);
    if(rc==1):
            return 1;

    try:
            index = child.expect ("sftp>",timeout=60);
            if index == 0:
                    child.sendline("cd "+target);			
    except pexpect.EOF:
            if ( debug ):
                    print "Connection dropped while executing command"
            return (1,"Connection dropped while executing command",cmd_output);
    except pexpect.TIMEOUT:
            if ( debug ):
                    print "Timed out while executing command"
            return (1,"Connection dropped while executing command",cmd_output);

    try:
            index = child.expect ("sftp>",timeout=60);
            if index == 0:
                    child.sendline(putCmd);
    except pexpect.EOF:
            if ( debug ):
                    print "Connection dropped while executing command"
            return (1,"Connection dropped while executing command",cmd_output);
    except pexpect.TIMEOUT:
            if ( debug ):
                    print "Timed out while executing command"
            return (1,"Connection dropped while executing command",cmd_output);


    cmd_output=child.before;
    
    try:

            index = child.expect ("sftp>",timeout=60);
            if index == 0:
                    child.sendline("exit");			
    except pexpect.EOF:
            if ( debug ):
                    print "Connection dropped while executing command"
            return (1,"Connection dropped while executing command",cmd_output);
    except pexpect.TIMEOUT:
            if ( debug ):
                    print "Timed out while executing command"
            return (1,"Connection dropped while executing command",cmd_output);

    return (0,"Successfully executed command",cmd_output);
