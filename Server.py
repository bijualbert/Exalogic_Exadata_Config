__author__="Biju"
__date__ ="$Apr 13, 2015 1:21:07 PM$"

import sys;
import re;

import OSUtils;
import pexpect;

class Server(object):
    """
    A server, could be physical or virtual with any OS
    
    Attributes:
    name: Hostname
    ip: Primary management IP
    user: Username
    password: Password
    prompt: Command line prompt string
    type: physical or virtual    
    os: linux,solaris,ovs etc
    cpu:
    memory:
    disk:
    network_interfaces:
    
    """
    
    def __init__(self,name,ip,user,password,prompt=".*?>",logger=None,debug=0,timeout=30):
        
        self.name=name;
        self.ip=ip;
        self.user=user;
        self.password=password;
        self.prompt=prompt;
        self.timeout=timeout;
        self.logger=logger;
        self.debug=debug;
        
    def getOS(self):
        
        rc=1;
        rmsg=None;
        rout=None;
        
        (rc,rmsg,rout)=Server.ExecCmd(self,"uname -a");
        
        if (re.search(r".*?linux.*?", rout, re.M|re.I)):
                return "linux";
        else:
                return "unknown";
    
    def ExecCmd(self,command):

	cmd_output=None;
	rc=1;
	rmsg=None;

	child = pexpect.spawn('ssh',['-o','UserKnownHostsFile=/dev/null',self.user+'@'+self.ip]);
	if (self.debug):
            child.logfile = sys.stdout
		
	(rc,rmsg,cmd_output)=OSUtils.JustType(child,"Are you sure you want to continue connecting.*","yes");
	if(rc==1):
            return 1;

	rc,rmsg,cmd_output=OSUtils.JustType(child,".*?(P|p)assword:",self.password);
	if(rc==1):
            return 1;
		
	try:
            index = child.expect (self.prompt,timeout=self.timeout);
            if index == 0:
                child.sendline(str(command));
	
        except pexpect.EOF:
            
            if ( self.debug ):
                print "Connection dropped while executing command"+cmd_output;
            if (self.logger is not None ): 
                self.logger.error("Connection dropped while executing command"+cmd_output);
            return (1,"Connection dropped while executing command",cmd_output);
        
	except pexpect.TIMEOUT:
	
            if ( self.debug ):
                print "Connection dropped while executing command"+cmd_output;
            if (self.logger is not None ): 
                self.logger.error("Connection dropped while executing command"+cmd_output);
            
            return (1,"Connection dropped while executing command",cmd_output);

	try:
            
            index = child.expect (self.prompt,timeout=self.timeout);
            if index == 0:
                cmd_output=child.after;
		child.sendline("exit");			
                
	except pexpect.EOF:
		
            if ( self.debug ):
                print "Connection dropped while executing command"+cmd_output;
        
            if (self.logger is not None ): 
                self.logger.error("Connection dropped while executing command"+cmd_output);
	
            return (1,"Connection dropped while executing command",cmd_output);
        
	except pexpect.TIMEOUT:
	
            if ( self.debug ):
                print "Connection dropped while executing command"+cmd_output;
            
            if (self.logger is not None ): 
                self.logger.error("Connection dropped while executing command"+cmd_output);
	
            return (1,"Connection dropped while executing command",cmd_output);
        
        if(self.debug):
            print "Command output is:"+cmd_output;
        
        if (self.logger is not None ): 
            self.logger.debug("Command output is:"+cmd_output);
                
	return (0,"Successfully executed command",cmd_output);
