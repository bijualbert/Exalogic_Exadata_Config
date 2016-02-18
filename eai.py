import sys
import re
import os
import time
import subprocess
import logging

#export PATH=/usr/local/bin:${PATH}
#Modules required to be installed
import pexpect
import json
from netaddr import *
import getopt
import ConfigParser

#Exalogic internal modules
from ExalogicConfiguration import *;
from ECUTests import *;
import OSUtils;
import NetworkUtils;
from ILOM import *;
import ib;


CONFIG_FILE="/root/NetBeansProjects/ECU/src/ECUInstall.properties";

def exaCdromInstall (config_file_dir,ilom_user,ilom_password,compute_node_user,compute_node_password,compute_nodes_json,rack_config_json,eth_network_info_json,ipoib_network_info_json,common_host_config_json,seed_node,physical_image_path,seed_node_image_path,configure_network_only,storage_redir_bin_dir,java_bin_dir,startNode,endNode,max_number_parallel_installs,interval_between_installs,minimum_image_install_time,maximum_image_install_time,polling_interval):
        
	global logger;
        
        rc=1;
	rmsg="";
        
        if ( configure_network_only!=1):
            MINIMUM_IMAGE_INSTALL_TIME=int(minimum_image_install_time);
            MAXIMUM_IMAGE_INSTALL_TIME=int(maximum_image_install_time);        
            TIME_BETWEEN_PARALLEL_INSTALL=int(interval_between_installs);
            timer=int(MINIMUM_IMAGE_INSTALL_TIME);
            MAX_NUMBER_OF_PARALLEL_INSTALLS=int(max_number_parallel_installs);
        else:
            MINIMUM_IMAGE_INSTALL_TIME=3;
            MAXIMUM_IMAGE_INSTALL_TIME=120;        
            TIME_BETWEEN_PARALLEL_INSTALL=3;
            timer=int(MINIMUM_IMAGE_INSTALL_TIME);
            MAX_NUMBER_OF_PARALLEL_INSTALLS=32;        
        
        serialInstallCycle=0;
	installStatus={};
        ilomObjArr={};
	result=0;

	### Get Exalogic information from ECU configuration jsons
        
        rack_config=ExalogicConfiguration(config_file_dir);
        
        domain=rack_config.GetDomain();
	cnodes=rack_config.GetCnodesInfo();		
	rackSize=rack_config.GetRackSize();
	defaultGateway=rack_config.GetEthDefaultGateway();
	ipoibNetMask=rack_config.GetIPoIBDefaultAttr("IPoIB-default","netmask");
	ethNetMask=rack_config.GetEthDefaultAttr("eth-admin","netmask");

	### Perform a CD ROM install of the nodes provided
	logger.info("Initializing install status");
	i=int(startNode);
	while (i <= int(endNode)):
		
                installStatus['next_install_start_time']=0;
		installStatus[i] = installStatus.get(i, {});
		installStatus[i]['status'] = installStatus[i].get('status', "");
		installStatus[i]['install_attempt'] = installStatus[i].get('install_attempt', "");
                installStatus[i]['install_attempt']=0;
                installStatus[i]['install_start_time'] = installStatus[i].get('install_start_time', 0);
		installStatus[i]['install_timeout_threshhold'] = installStatus[i].get('install_timeout_threshhold', 0);
		installStatus[i]['status']="to_be_attempted";
                ilomObjArr[i]=ILOM(cnodes[(i-1)]['ilom-host'],ilom_user,ilom_password,logger);
		i+=1;                


	### Perform a CD ROM install of the nodes provided
        numberInstallsInProgress=0;
	endInstallCycle=0;
        installMode="parallel";
        ILOM.storageRedirBinDir=storage_redir_bin_dir;
        ILOM.javaBinDir=java_bin_dir;
        ILOM.vncServerPort=0;
        
        while (endInstallCycle==0 or endInstallCycle==1):
            
            i=int(startNode);
            logger.debug("Install mode:"+installMode);
        
            ### Loop and kick off install per configuration
            while ( i<=int(endNode)):


                logger.debug("\nNumber of installs in progress:"+str(numberInstallsInProgress));
                
                logger.debug("Processing node index:"+str(i)+" ,node name:"+str(cnodes[(i-1)]['ilom-host'])+", Status:"+str(installStatus[i]['status']));

                endInstallCycle=2;

                currentTime=int(time.mktime(time.localtime())); 

                if ( ( (installMode=="parallel" and installStatus[i]['status'] == "to_be_attempted") or (installMode=="serial" and installStatus[i]['status'] == "to_be_retried") ) and numberInstallsInProgress<MAX_NUMBER_OF_PARALLEL_INSTALLS and currentTime>=installStatus['next_install_start_time'] ):

                        logger.info("Starting "+installMode+" mode CDROM install for node index:"+str(i)+" ,node name:"+str(cnodes[(i-1)]['host'])+" ,with current status as:"+str(installStatus[i]['status']));	
                        logger.info("Time after which next install can start:"+str(installStatus['next_install_start_time']));                            
                        logger.info("Install timeout for this node:"+str(installStatus[i]['install_timeout_threshhold']));
                        logger.info("Install start time for this node:"+str(installStatus[i]['install_start_time']));

                        currentTime=int(time.mktime(time.localtime())); 

                        if(installMode=="serial"):                            
                            rc=ilomObjArr[i].restartSP(360);
                        
                        if ( configure_network_only!=1):
                            rc=1;
                            try:
                                if(i==int(seed_node)):
                                    logger.info("Installation of seed node:"+str(seed_node)+", with image:"+seed_node_image_path);                                
                                    ilomObjArr[i].cdromInstall(seed_node_image_path);                              
                                else:
                                    logger.info("Installation of non seed node:"+str(i)+"with image"+physical_image_path);                                
                                    rc=ilomObjArr[i].cdromInstall(physical_image_path);
                            except:
                                rc=1;
                            else:
                                rc=0;
                                    
                        if (rc==0):
                            installStatus[i]['status']="in_progress";                    
                            numberInstallsInProgress+=1;
                            installStatus['next_install_start_time']=currentTime+TIME_BETWEEN_PARALLEL_INSTALL;
                            if (numberInstallsInProgress==MAX_NUMBER_OF_PARALLEL_INSTALLS):
                                logger.info("Maximum number of installs ("+str(MAX_NUMBER_OF_PARALLEL_INSTALLS)+ ") reached");
                            installStatus[i]['install_timeout_threshhold']=currentTime+int(MAXIMUM_IMAGE_INSTALL_TIME);
                            installStatus[i]['install_start_time']=currentTime;

                elif ((installStatus[i]['status'] == "to_be_attempted" or installStatus[i]['status'] == "to_be_retried") and numberInstallsInProgress>=MAX_NUMBER_OF_PARALLEL_INSTALLS):

                        logger.debug("Maximum number of parallel installs in progress, cannot start install for this node");

                elif ((installStatus[i]['status'] == "to_be_attempted" or installStatus[i]['status'] == "to_be_retried") and currentTime<installStatus['next_install_start_time']):

                        logger.debug("The time to start next parallel install has not arrived yet, "+str((installStatus['next_install_start_time']-currentTime))+" secs to go");

                elif ( installStatus[i]['status'] == "failed" ):
                        logger.debug("Install status is:"+str(installStatus[i]['status'])+", need not kick off install for this");	        
                elif ( installStatus[i]['status'] == "in_progress" ):
                        logger.debug("Install status is:"+str(installStatus[i]['status'])+", nothing more to do here");                        

                ### Loop and check status for nodes whose install is in progress
                currentTime=int(time.mktime(time.localtime())); 
                if( installStatus[i]['status'] == "in_progress" ):
                    logger.debug("Install in progress for node index:"+str(i)+" ,node name:"+str(cnodes[(i-1)]['host']));	        
                    if ( (currentTime < installStatus[i]['install_timeout_threshhold'] ) and (currentTime >= (installStatus[i]['install_start_time']+int(MINIMUM_IMAGE_INSTALL_TIME)))  ):

                        logger.debug("Checking if SSH is up on "+cnodes[(i-1)]['host']+" after install");				
                        rc=1;
                        rc=NetworkUtils.isSSHUpOnHost(cnodes[(i-1)]['host']);
                        
                        #if(os.path.isfile(str(i))):
                        #    installStatus[i]['status']="done";
                        #    numberInstallsInProgress-=1;
                        #elif(os.path.isfile(str(i)+".fail")):                            
                        #    if (installMode=="parallel"):
                        #        installStatus[i]['status']="to_be_retried";
                        #        numberInstallsInProgress-=1;
                        #    else:
                        #        installStatus[i]['status']="failed";
                        #        numberInstallsInProgress-=1;
                                
                        if(rc==0):				

                                if ( configure_network_only!=1):
                                    waitTime=120;
                                else:
                                    waitTime=15;
                                    
                                tmpTimer=0;
                                while ( tmpTimer < waitTime ):                                    
                                    rc=1;                                    
                                    rc=NetworkUtils.isSSHUpOnHost(cnodes[(i-1)]['host']);                                    
                                    if (rc==1):
                                        break;
                                    time.sleep(10);
                                    tmpTimer+=10;
                                        
                                if (rc==0):

                                    logger.debug("SSH service is up on "+cnodes[(i-1)]['host']+" after install");
                                    logger.debug("============================= Configuring network for, "+cnodes[(i-1)]['host']);
                                    rc=1;
                                    rc=ConfigureNetwork( cnodes[(i-1)]['host'],compute_node_user,compute_node_password,rackSize,i,cnodes[(i-1)]['IPoIB-default']['ip'],ipoibNetMask,cnodes[(i-1)]['eth-admin']['ip'],ethNetMask,defaultGateway,domain);

                                    #rc=0;

                                    if (rc==0):
                                            installStatus[i]['status']="done";
                                            numberInstallsInProgress-=1;
                                            logger.info("============================= Installation succeeded for node "+cnodes[(i-1)]['host']);
                                            logger.info("============================= Time taken "+str(timer)+" secs");
                                            continue;
                                    else:
                                            logger.debug("Network configuration failed for "+cnodes[(i-1)]['host']+", will retry");
                                else:
                                    logger.debug("SSH service went down after initially coming up on "+cnodes[(i-1)]['host']+" after install, this is expected");
                        else:
                                logger.debug("Install has not completed on "+cnodes[(i-1)]['host']+", ssh service is still NOT UP after invoking install, "+str(installStatus[i]['install_timeout_threshhold']-currentTime)+" secs to go before reaching configured timeout of "+str(MAXIMUM_IMAGE_INSTALL_TIME)+" secs");

                    elif ( currentTime >= installStatus[i]['install_timeout_threshhold'] ):

                        logger.info("Installation not completed for node within configured time out period:"+cnodes[(i-1)]['host']);
                        logger.info("Install kicked off at, "+str(installStatus[i]['install_start_time'])+", node not up after waiting for "+str(MAXIMUM_IMAGE_INSTALL_TIME)+" secs");
                        
                        if (installMode=="parallel"):
                            
                            installStatus[i]['status']="to_be_retried";
                        else:
                            installStatus[i]['status']="failed";
                        numberInstallsInProgress-=1;
                        
                        logger.info("Changing the status to"+installStatus[i]['status']);
                        logger.info("Decrementing number of installs in progress to"+str(numberInstallsInProgress));
                        

                    else:

                        logger.debug("The minimum wait time to check status for node "+cnodes[(i-1)]['host']+" has not elapsed, "+str((installStatus[i]['install_start_time']+int(MINIMUM_IMAGE_INSTALL_TIME))-currentTime)+" secs to go");


                i+=1;

            logger.info("\n\n");
            k=int(startNode);
            while ( k<=int(endNode) ):
                logger.info("Status for node index:"+str(k)+" ,node name:"+str(cnodes[(k-1)]['ilom-host'])+" is:"+str(installStatus[k]['status']));	
                if(installMode == "parallel" and ( installStatus[k]['status']=="in_progress" or installStatus[k]['status']=="to_be_attempted") ):
                    endInstallCycle=0;
                if(installMode == "serial" and ( installStatus[k]['status']=="in_progress" or installStatus[k]['status']=="to_be_retried") ):
                    endInstallCycle=1;    
                k+=1;

            if (endInstallCycle!=2):
                
                logger.debug("Sleeping for "+str(polling_interval)+" secs before starting next install/status check");
                time.sleep(int(polling_interval));
                
            else:
                
                logger.info("End of install mode:"+installMode);
                k=int(startNode);                
                while ( k<=int(endNode) ):                    
                    logger.info("Status for node index :"+str(k)+" ,node name:"+str(cnodes[(k-1)]['ilom-host'])+" is:"+str(installStatus[k]['status']));
                    
                    if(installMode == "parallel" and installStatus[k]['status']!="done"):                            
                            endInstallCycle=1;
                            installStatus['next_install_start_time']=0;                            
                            installStatus[k]['status']="to_be_retried";
                            installStatus[k]['install_timeout_threshhold']=0;
                            installStatus[k]['install_start_time']=0;
                            
                    elif(installMode == "serial" and installStatus[k]['status']!="done"):
                            endInstallCycle==3;

                    k+=1;

                if(endInstallCycle==1):

                        logger.info("Switching install mode to serial to attempt installs for failed nodes");
                        MAX_NUMBER_OF_PARALLEL_INSTALLS=1;
                        installMode="serial";

                        numberInstallsInProgress=0;

                elif(endInstallCycle==3):
                    logger.info("Install failed for some nodes at the end of serial install cycle");
                    return 1;
                else:
                    logger.info("Install done successfully for all nodes");	
                    return 0;        
	
	return 0;
	

				
def ConfigureNetwork( compute_node_name,user,password,rack_type,node_position,ipiob_net_ip,ipiob_net_netmask,eth_net_ip,eth_net_netmask,eth_net_gateway,domain_name):
    
	global logger;
        
        cmd_output=""
	debug=1
	rc=1;
	rmsg=""
        image_type=0

        (rc,rmsg,cmd_output)=OSUtils.ExecRemoteCmd(compute_node_name,user,password,"\["+user+"@.*?"+"\s+~\]","ls /opt/exalogic/ebi/install_scripts/configure_NetworkUtils.sh");

        pattern=re.compile(r".*?No such file or directory.*?", re.M|re.I);

        if (pattern.search(cmd_output)):
                image_type=1;    	
        
	child = pexpect.spawn('ssh',['-o','UserKnownHostsFile=/dev/null',user+'@'+compute_node_name]);
	if (debug):
		child.logfile = sys.stdout

	rc,rmsg,cmd_output=OSUtils.JustType(child,"Are you sure you want to continue connecting.*","yes");
	if(rc==1):
		return 1;

	rc,rmsg,cmd_output=OSUtils.JustType(child,".*?(P|p)assword:",password);
	if(rc==1):
		return 1;
		
	if(image_type==1):
		rc,rmsg,cmd_output=OSUtils.JustType(child,"\["+user+"\@.*","/opt/exalogic/install_scripts/configure_NetworkUtils.sh");		
	else:
		rc,rmsg,cmd_output=OSUtils.JustType(child,"\["+user+"\@.*","/opt/exalogic/ebi/install_scripts/configure_NetworkUtils.sh");	
		
	
        rc,rmsg,cmd_output=OSUtils.JustType(child,"Enter the exalogic rack type.*",rack_type);
        
	if(rc==1):
		return 1;
		
	rc,rmsg,cmd_output=OSUtils.JustType(child,"Use.*","y");
	if(rc==1):
		return 1;	

	rc,rmsg,cmd_output=OSUtils.JustType(child,"Enter the exalogic node index.*",node_position);
	if(rc==1):
		return 1;
		
	rc,rmsg,cmd_output=OSUtils.JustType(child,"Use.*","y");
	if(rc==1):
		return 1;	

	rc,rmsg,cmd_output=OSUtils.JustType(child,"Enter bond\d+ ipaddress.*",ipiob_net_ip);
	if(rc==1):
		return 1;
		
	rc,rmsg,cmd_output=OSUtils.JustType(child,"Use.*","y");
	if(rc==1):
		return 1;	

	rc,rmsg,cmd_output=OSUtils.JustType(child,"Enter bond\d+ netmask address.*",ipiob_net_netmask);
	if(rc==1):
		return 1;
		
	rc,rmsg,cmd_output=OSUtils.JustType(child,"Use.*","y");
	if(rc==1):
		return 1;	

	rc,rmsg,cmd_output=OSUtils.JustType(child,"Enter eth\d+ ipaddress.*",eth_net_ip);
	if(rc==1):
		return 1;
		
	rc,rmsg,cmd_output=OSUtils.JustType(child,"Use.*","y");
	if(rc==1):
		return 1;	

	rc,rmsg,cmd_output=OSUtils.JustType(child,"Enter eth\d+ netmask address.*",eth_net_netmask);
	if(rc==1):
		return 1;
		
	rc,rmsg,cmd_output=OSUtils.JustType(child,"Use.*","y");
	if(rc==1):
		return 1;	

	rc,rmsg,cmd_output=OSUtils.JustType(child,"Enter eth\d+ gateway address.*",eth_net_gateway);
	if(rc==1):
		return 1;
		
	rc,rmsg,cmd_output=OSUtils.JustType(child,"Use.*","y");
	if(rc==1):
		return 1;	

	rc,rmsg,cmd_output=OSUtils.JustType(child,"Enter hostname.*",compute_node_name);
	if(rc==1):
		return 1;
		
	rc,rmsg,cmd_output=OSUtils.JustType(child,"Use.*","y");
	if(rc==1):
		return 1;	

	rc,rmsg,cmd_output=OSUtils.JustType(child,"Enter domainname.*",domain_name);
	if(rc==1):
		return 1;
		
	rc,rmsg,cmd_output=OSUtils.JustType(child,"Use.*","y");
	if(rc==1):
		return 1;
		
	rc,rmsg,cmd_output=OSUtils.JustType(child,"Do you want to continue.*","y");
	if(rc==1):
		return 1;
		
	rc,rmsg,cmd_output=OSUtils.JustType(child,"\["+user+"\@.*","ls");
	if(rc==1):
		return 1;
		
	time.sleep(120);

	rc,rmsg,cmd_output=OSUtils.JustType(child,"\["+user+"\@.*","reboot");
	
	rc,rmsg,cmd_output=OSUtils.JustType(child,"\["+user+"\@.*","exit");
		
	child.close

	return 0;

def CopyConfigFilesToSeedNode(seed_node,config_file_dir,compute_node_user,compute_node_password,seed_node_config_directory,compute_nodes_json):    
    
    global logger;
    
    rc=1;
    rmsg=None;
    rout=None;
    
    ### Get compute node information from ECU cnodes_current json
    cnodes=GetCnodesInfo(config_file_dir,compute_nodes_json);
    
    (rc,rmsg,rout)=OSUtils.ExecRemoteCmd(cnodes[int(seed_node)-1]['host'],compute_node_user,compute_node_password,"\["+compute_node_user+"@.*?~\]","mkdir -p "+seed_node_config_directory);
    
    if(rc==1):
        return 1;

    (rc,rmsg,rout)=OSUtils.ExecRemoteCmd(cnodes[int(seed_node)-1]['host'],compute_node_user,compute_node_password,"\["+compute_node_user+"@.*?~\]","/bin/rm -rf "+seed_node_config_directory+"/*");
    if(rc==1):
        return 1;    
    
    rc=OSUtils.Sftp(cnodes[int(seed_node)-1]['host'],compute_node_user,compute_node_password,config_file_dir+"/*",seed_node_config_directory);
    if(rc==1):
        return 1;
    
    return 0;    

def areAllComputeNodesUp(config_file_dir,ilom_user,ilom_password,compute_node_user,compute_node_password,compute_nodes_json,max_wait_time):

    global logger;
    
    result=0;
    
    ### Get compute node information from ECU cnodes_current json
    cnodes=GetCnodesInfo(config_file_dir,compute_nodes_json);
    
    for i in range(len(cnodes)):
        
        rc=1;
        
        ilomObjArr[i]=ILOM(cnodes[(i-1)]['ilom-host'],user=ilom_user,password=ilom_password,logger=logger);
        
        rc=NetworkUtils.isSSHUpOnHost(cnodes[i]['host']);                                    
        
        if(rc==1):
            
            logger.info(cnodes[i]['host']+" is down, will attempt to start it");
            timer=0;
            rc=ilomObjArr[i].restart(tries=3);
            
            if(rc==0):
                while(timer<=max_wait_time):
                    logger.debug("Sleeping for 30 secs");
                    timer+=30;
                    time.sleep(30);
                    rc=1;
                    rc=NetworkUtils.isSSHUpOnHost(cnodes[i]['host']);
                    if(rc==0):
                        logger.debug(cnodes[i]['ilom-host']+" is up now");
                        break;
                    else:
                        logger.debug(cnodes[i]['ilom-host']+" is STILL down");
                        result=1;
            else:
                logger.debug("Unable to (re) start "+cnodes[i]['host']);
                result=1;
        else:
            logger.info(cnodes[i]['host']+" is already up, no need to start it");
    
    return result;

def ecuCleanup(seed_node,config_file_dir,compute_node_user,compute_node_password,compute_nodes_json):

    global logger;
    
    rc=1;
    rmsg=None;
    rout=None;
    
    ### Get compute node information from ECU cnodes_current json
    cnodes=GetCnodesInfo(config_file_dir,compute_nodes_json);
    
    cmd="echo y | /opt/exalogic/tools/ecu/ecu.sh cleanall;echo $? > /tmp/cleanUpStatus";
        
    (rc,rmsg,rout)=OSUtils.ExecRemoteCmd(cnodes[int(seed_node)-1]['host'],compute_node_user,compute_node_password,"\["+compute_node_user+"@.*?~\]",cmd);    
    
    pattern=re.compile(r'SUCCESS:\s+ECU\s+Cleanup',re.M|re.I);
    
    if (pattern.search(rout)):
        return 0;
    else:
        return 1;
    
def verifyCleanup(config_file_dir,switch_info_json,switch_user,switch_password):    

    global logger;
    
    rc=1;
    
    switches=GetIbSwitchInfo(config_file_dir,switch_info_json);
    
    rc=ib.verifyNoPartitions(switches[0]['ilom']['host'],switch_user,switch_password);
    
    return rc;
    
def main (debug):

    ### Setup logging
    # Set up a specific logger with our desired output level
    global logger;
    logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s',datefmt='%m/%d/%Y %I:%M:%S %p')
    
    logger = logging.getLogger('MyLogger')
    logger.setLevel(logging.DEBUG)
    
    LOG_FILENAME = 'ecu_install.log';

    # Add the log message handler to the logger
    fileHandler = logging.FileHandler(LOG_FILENAME,mode="w");
    fileHandler.setLevel(logging.DEBUG);
    logger.addHandler(fileHandler);

    stdoutFileHandler = logging.StreamHandler(sys.stdout)
    stdoutFileHandler.setLevel(logging.DEBUG)
    logger.addHandler(stdoutFileHandler);
    
    ### Check inputs
    "Function to check the inputs passed"
    if ( len(sys.argv) < 2 ) :
        logger.error("Number of arguments passed is wrong:"+str(len(sys.argv)));
        logger.error("Usage: eai.py --config_file_dir --seed_node_image_path--physical_image_path --start_node --end_node --seed_node=0 --batch_input --prep_cnodes --prep_ecu --configure_network_only --preinstall_validation --postinstall_validation");
        sys.exit(1);
    
    config_file_dir="";
    seed_node_image_path="";
    physical_image_path ="";
    start_node = 0;
    end_node = 0;
    seed_node=0;
    batch_input="";
    prep_cnodes="";
    prep_ecu="";
    configure_network_only="";
    preinstall_validation="";
    postinstall_validation="";
    

    #logger.debug('ARGV:'+sys.argv[1:]);
    options, remainder = getopt.getopt(sys.argv[1:], 'c:s:p:b:e:n:abcd', [
                                                        'config_file_dir=', 
                                                        'seed_node_image_path=',
                                                        'physical_image_path=',
                                                        'start_node=',
                                                        'end_node=',
                                                        'batch_input=',
                                                        'seed_node_index=',
                                                        'prep_cnodes',
                                                        'prep_ecu',
                                                        'configure_network_only',
                                                        'preinstall_validation',
                                                        'postinstall_validation'
                                                        ])


    for opt, arg in options:
            if opt in ('--config_file_dir'):
                    config_file_dir= arg;
            elif opt in ('--seed_node_image_path'):
                    seed_node_image_path=arg;
            elif opt in ('--physical_image_path'):
                    physical_image_path=arg;                    
            elif opt in ('--start_node'):
                    start_node=arg;
            elif opt in ('--end_node'):
                    end_node=arg;
            elif opt in ('--batch_input'):
                    batch_input=arg;
            elif opt in ('--seed_node_index'):
                    seed_node=arg;
            elif opt in ('--prep_cnodes'):
                    prep_cnodes=1;
            elif opt in ('--prep_ecu'):
                    prep_ecu=1;
            elif opt in ('--configure_network_only'):
                    configure_network_only=1;
            elif opt in ('--preinstall_validation'):
                    preinstall_validation=1;
            elif opt in ('--postinstall_validation'):
                    postinstall_validation=1;                    
                    
    if (end_node==0):
        end_node=start_node;

    logger.debug('config_file_dir:'+config_file_dir);
    logger.debug('seed_node_image_path:'+seed_node_image_path);
    logger.debug('start_node:'+str(start_node));
    logger.debug('end_node:'+str(end_node));
    logger.debug('physical_image_path:'+physical_image_path);
    logger.debug('batch_input:'+batch_input);
    logger.debug('seed_node:'+str(seed_node));
    logger.debug('prep_cnodes:'+str(prep_cnodes));
    logger.debug('prep_ecu:'+str(prep_ecu));
    logger.debug('preinstall_validation:'+str(preinstall_validation));
    logger.debug('postinstall_validation:'+str(postinstall_validation));
    
    ### Get default properties
    config = ConfigParser.RawConfigParser()
    config.read('/root/NetBeansProjects/ECU/src/ECUInstall.properties')
    ilom_user=config.get('ECU', 'ilom_user');
    ilom_password=config.get('ECU', 'ilom_password');
    storage_redir_bin_dir=config.get('ECU', 'storage_redir_bin_dir');
    java_bin_dir=config.get('ECU', 'java_bin_dir');
    compute_node_user=config.get('ECU','compute_node_user');
    compute_node_password=config.get('ECU','compute_node_password');

    compute_nodes_json=config.get('ECU', 'compute_nodes_info');
    rack_config_json=config.get('ECU', 'rack_config');
    eth_network_info_json=config.get('ECU', 'eth_network_info');
    ipoib_network_info_json=config.get('ECU', 'ipoib_network_info');
    common_host_config_json=config.get('ECU', 'common_host_config_info');
    switch_info_json=config.get('ECU', 'ib_switch_info');
    seed_node_config_directory=config.get('ECU', 'seed_node_config_directory');
    if(seed_node==-1):
        seed_node=config.get('ECU', 'default_seed_node_index');

    if (prep_cnodes==1):
        rc=1;
        rc=exaCdromInstall(config_file_dir,ilom_user,ilom_password,compute_node_user,compute_node_password,compute_nodes_json,rack_config_json,eth_network_info_json,ipoib_network_info_json,common_host_config_json,seed_node,physical_image_path,seed_node_image_path,configure_network_only,storage_redir_bin_dir,java_bin_dir,start_node,end_node,config.get('ECU','max_number_of_parallel_installs'),config.get('ECU','minimum_interval_between_installs'),config.get('ECU', 'minimum_image_install_time'),config.get('ECU', 'maximum_image_install_time'),config.get('ECU', 'image_install_status_polling_interval'));
        
    if (prep_ecu==1):
        rc=CopyConfigFilesToSeedNode(seed_node,config_file_dir,compute_node_user,compute_node_password,seed_node_config_directory,compute_nodes_json);

        if(rc==0):
            areAllComputeNodesUp(config_file_dir,ilom_user,ilom_password,compute_node_user,compute_node_password,compute_nodes_json,config.get('ECU', 'compute_node_startup_max_wait_time'));

        if(rc==0):
            rc=ecuCleanup(seed_node,config_file_dir,compute_node_user,compute_node_password,compute_nodes_json);

        if(rc==0):
            verifyCleanup(config_file_dir,switch_info_json,compute_node_user,compute_node_password);
    
    if (postinstall_validation==1):
        
        
        #Check if Nimbula nodes have the expected version
        try:
            ECUTests.checkNimbulaVersion(jsonConfigDirectory=config_file_dir,expectedNimbulaVersion=config.get('TestData','nimbula_version'),logger=logger);
        except ECUTestFailureError:
            raise ECUTestFailureError;        
        
        #Check if all virtual nodes are part of the Nimbula cluster
        try:
            ECUTests.checkNimbulaNodes(jsonConfigDirectory=config_file_dir,logger=logger);
        except ECUTestFailureError:
            logger.error("Nimbula node check failed");
            raise ECUTestFailureError;

#####
main(1);
