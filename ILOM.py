import sys
import re
import os
import time
import pexpect;

import OSUtils;
import NetworkUtils;
import io;

from Exceptions import *;

class ILOM(object):
    """    
    Class which represents an ILOM 
    
    Attributes:
        
        self.sp: DNS Name or IP of ILOM
        self.user: ILOM self.user
        self.password: ILOM self.password
            
    """
    
    storageRedirBinDir=None;
    javaBinDir=None;
    vncServerPort=None;
    

    def __init__(self,sp,user="root",password="welcome1",logger=None):
    
        self.sp=sp;
        self.user=user;
        self.password=password;
        self.logger=logger;
    
    def cdromInstall (self,cdROMImage):
        """
        Method to perform a OS install via the ILOM using a CDROM image

        Attributes:

            cdROMImage: OS CDROM Image to be install    

        """            
        rc=1;
        rmsg=None;
        
        try:

            self.logger.debug("Is storage redirection running?");
            rc=self.isStorageRedirectionServiceRunning();

            if ( not rc ):
                    self.logger.debug("Storage redirection service already running");
            else:
                    self.logger.debug("Storage redirection service is not running, will attempt to start it now");
                    ### Start storage redirection service
                    self.startStorageRedirectionService();

            ### Stop redirecion for this SP if running
            self.stopStorageRedirection();

            ### Attach cdrom to node
            self.startStorageRedirection(cdROMImage,3);        

            ### Set boot device to cdrom
            self.setBootDev("cdrom",3);

            ### Reset power to node
            self.restartServer(3);        

        except:
            raise ILOMError("Error"+str(sys.exc_info()[0]));
    
    def isStorageRedirectionServiceRunning(self):

        #/usr/java/jre1.6.0_45/bin/java -jar StorageRedir.jar test-service
                
        cmd_str=self.javaBinDir+"/java","-jar",self.storageRedirBinDir+"/StorageRedir.jar","test-service";
        self.logger.debug("Checking if storage redirection service is running: "+str(cmd_str));
        
        rc,rmsg=OSUtils.ExecCmd(cmd_str,1);        

        if ( re.search('Service connection passed', rmsg) ):
            #Storage redirection service already running
            self.logger.debug("Storage service running");            
            return 0;
        else:
            #Storage redirection service is not running
            self.logger.debug("Storage service NOT running");            
            return 1;

    def startStorageRedirectionService(self):

        hostname="";
        rc="";
        rmsg=""
        startVnc=0;

        vncPortFileName="/tmp/vncPortStorageRedirectionService";

        if(os.path.isfile(vncPortFileName)):

            fh=open(vncPortFileName,'rt');
            self.vncServerPort=fh.read();
            fh.close();
            self.vncServerPort=self.vncServerPort.strip();

            rc,hostname=OSUtils.ExecCmd("hostname",1);
            if(rc):
                raise OSCmdError("OS Command error");

            hostname=hostname.strip()

            rc,self.user=OSUtils.ExecCmd("whoami",1);
            if(rc):
                raise OSCmdError("OS Command error");

            self.user=self.user.strip()

            rc=OSUtils.isProcessRunning(hostname+":"+self.vncServerPort+"\s+\("+self.user+"\)");

            if (rc==0):
                self.logger.info("VNC session already running for port:"+str(self.vncServerPort));
            else:
                startVnc=1;

        else:

            startVnc=1;

        if (startVnc):

            ### Start vnc session for CDROM javaws
            rc,rmsg=OSUtils.ExecCmd("vncserver",1);
            if(rc):
                raise OSCmdError("OS Command error");

            matchObj = re.search(hostname+":(\d+)", rmsg, re.M|re.I)
            if matchObj:
                    self.vncServerPort=matchObj.group(1)
                    self.vncServerPort=self.vncServerPort.rstrip();
                    self.logger.debug("VNC Server Port is "+self.vncServerPort);
                    fh=open(vncPortFileName,'wt');
                    fh.write(self.vncServerPort);
                    fh.close();
            else:
                    self.logger.error("Unable to determine vnc port");
                    raise OSCmdError("Unable to determine vnc port");

        os.environ["DISPLAY"]=":"+self.vncServerPort+".0";
        cmd_str="xhost","+";
        rc,rmsg=OSUtils.ExecCmd(cmd_str,1);
        if(rc):
            raise OSCmdError("OS Command error");

        #/usr/java/jre1.6.0_45/bin/javaws -Xnoself.splash jnlpgenerator-cli
        cmd_str="nohup "+self.javaBinDir+"/javaws"+" -Xnoself.splash "+self.storageRedirBinDir+"/jnlpgenerator-cli &";

        self.logger.debug(cmd_str);
        os.system(cmd_str);
        time.sleep(30);                

        rc=self.isStorageRedirectionServiceRunning();
        if(rc):
                raise OSCmdError("Failed to start storage redirection service");

    def stopStorageRedirection(self):

        rc=0;
        rmsg=None;
        cmd_str=self.javaBinDir+"/java","-jar",self.storageRedirBinDir+"/StorageRedir.jar","stop","-r","cdrom_img","-u",self.user,"-s",self.password,self.sp;
        rc,rmsg=OSUtils.ExecCmd(cmd_str,1);
        if(rc):
            if ( not re.search('cdrom redirection has not been established',rmsg) ):
                raise OSCmdError("Error stopping CD ROM storage redirection for "+str(self.sp));

    def startStorageRedirection(self,cdROMImage,tries):

        i=0;
        done=0;
        rc=1;
        rmsg=None;

        error_pattern=re.compile(r'error', re.I|re.M);

        #/usr/java/jre1.6.0_45/bin/java -jar StorageRedir.jar start -r cdrom_img -t /scratch/arlogana/stack13/el_virtual_seed_node_image_3.1.1.0.0_64.iso -u root -s welcome1 slcn01cn01-c.us.oracle.com
        cmd_str=self.javaBinDir+"/java","-jar",self.storageRedirBinDir+"/StorageRedir.jar","start","-r","cdrom_img","-t",cdROMImage,"-u",self.user,"-s",self.password,self.sp;

        while ( i < tries and done==0):

            i+=1;
            rc,rmsg=OSUtils.ExecCmd(cmd_str,1);
            if (not rc):                    
                done=1;
        
        if (rc):
            raise OSCmdError("Error starting CD ROM storage redirection for "+str(self.sp));
        
        self.logger.debug("Started storage redirection for "+self.sp);        
            

    def setBootDev(self,bootdev,tries):

        #ipmitool -H slcn01cn01-c.us.oracle.com -U root -p welcome1 chassis bootdev cdrom
        i=0;
        done=0;
        debug=1;
        rc=1;
        rmsg=None;

        cmd_str="ipmitool","-H",self.sp,"-U",self.user,"-P",self.password,"chassis","bootdev",bootdev;

        while ( i < tries and done==0):
            i+=1;       
            rc,rmsg=OSUtils.ExecCmd(cmd_str,1);
            if(rc):
                raise OSCmdError("Error setting boot device for "+str(self.sp)+" to "+bootdev);

            bootdev=self.GetSpObjAttribute("/HOST","boot_device");
            
            if (not re.search(".*?cdrom.*?",bootdev,re.I|re.M)):
                raise OSCmdError("Error setting boot device for "+str(self.sp)+" to "+bootdev);                


    def restartServer(self,tries):
        
        state=None;

        try:
            
            self.logger.debug("Stopping server");
            
            self.powerServer("off",tries);
            
            self.logger.debug("Starting server");
            
            self.powerServer("on",tries);

            
        except:
            
            raise ILOMError("Error restarting server");                
            

    def powerServer(self,operation,tries):

        #ipmitool -H slcn01cn01-c.us.oracle.com -U root -P welcome1 chassis power reset
        i=0;
        done=0;
        rc=1;
        rmsg=None;

        cmd_str="ipmitool","-H",self.sp,"-U",self.user,"-P",self.password,"chassis","power",operation;

        while ( i < tries and done==0):

            self.logger.debug("Trying to change server state to:"+operation);            
            i+=1;
            rc,rmsg=OSUtils.ExecCmd(cmd_str,1);
            if (rc):
                time.sleep(3);                        
            else:
                status=self.getServerPowerStatus(tries=3);
                if(re.search(operation,status,re.I)):
                    done=1;
                    self.logger.debug("Server powered successfully");            
                else:
                    done=0;
            tries+=1;

        if(not done):
            self.logger.error("Error powering server");            
            raise ILOMError("Error powering server");                
        
    def getServerPowerStatus(self,tries):
        
        #ipmitool -I lanplus -H slcp02cn04-c -U root -P welcome1 chassis power status   
        status=None;   
        done=0;
        counter=0;
        
        cmd_str="ipmitool","-H",self.sp,"-U",self.user,"-P",self.password,"chassis","power","status";

        while (counter < 3 and done==0):
            rc,rmsg=OSUtils.ExecCmd(cmd_str,1);
            if ( rc ):
                counter+=1;
            else:
                done=1;

        pattern=re.compile(r'Chassis Power is\s+(\w+)',re.I);

        matchObj = pattern.search(rmsg);

        if matchObj:
                status=matchObj.group(1);            

        return status;

    def restartSP(self,timeout):

        timer=0;

        rc=OSUtils.ExecRemoteCmd(self.sp,self.user,self.password,"->","reset -script /SP");
        if ( rc ):
            raise ILOMError("Error restarting ILOM"+str(self.sp));                

        while ( timer <= timeout ):

            timer+=30;
            time.sleep(30);

            rc=NetworkUtils.isSSHUpOnHost(self.sp);
            if (not rc):
                return;
            
        if( rc ):
            raise ILOMError("ILOM not up after "+str(timeout));                                


    def GetSpObjAttribute(self,object,attribute):

      (rc,msg,cmdOut,value)=(1,None,None,None);
      ### Connect to SP and get attribute value
      (rc,msg,cmdOut)=OSUtils.ExecRemoteCmd(self.sp,self.user,self.password,"->","show "+object+" "+attribute);

      self.logger.debug(cmdOut);
      
      matchObj = re.search( attribute+' =\s+(.*)\n', cmdOut, re.M|re.I)
      if matchObj:
        value=matchObj.group(1);
        self.logger.debug("Attribute Value is "+value);       
        return value;
      else:
        self.logger.debug("Error fetching value for attribute"+object+" "+attribute);       
        raise ILOMError("Error fetching value for attribute"+object+" "+attribute);                
