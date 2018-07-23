#! /usr/bin/python

#Exalogic internal modules
from ExalogicConfiguration import *;
from Exceptions import *;
from Nimbula import *;

__author__ = "Biju"
__date__ = "$Apr 17, 2015 10:57:16 AM$"

class ECUTests(object):
    
    @staticmethod
    def checkNimbulaVersion(jsonConfigDirectory,expectedNimbulaVersion,logger=None):        
        """
        Check if Nimbula version is as expected
        """
                
        if ( logger is not None):
            logger.info("Checking Nimbula version");
            logger.info("Expected nimbula version:"+expectedNimbulaVersion);
        
        # Get nimbula instance & passwords
        rack_config=ExalogicConfiguration(configurationDirectory=jsonConfigDirectory);                
        nimbula_info=rack_config.GetNimbulaInfo();        
        passwords=rack_config.GetPasswords();                
        
        nimbula=Nimbula(host_api=nimbula_info['host_api_ip'],nimbula_admin_user="/cloud/administrator",nimbula_admin_password=passwords['api_password']['root']);        
        nimbulaVersion=nimbula.getVersion();
        
        if ( logger is not None):
            logger.info("Actual nimbula version from node:"+nimbula_info['host_api_ip']+" is "+nimbulaVersion);
        
        if(nimbulaVersion!=expectedNimbulaVersion):                    
            if ( logger is not None):
                logger.error("Step result:Fail");
                raise ECUTestFailureError("Nimbula version is not as expected");
        else:
            if ( logger is not None):
                logger.info("Step result:Pass");

    @staticmethod
    def checkNimbulaNodes(jsonConfigDirectory,logger=None):        
        """
        Check if all virtual compute nodes are in Nimbula cluster and are in active state
        """        
        
        if ( logger is not None):
            logger.info("Checking if compute nodes designated to be virtual are a part of Nimbula cluster");
        
        # Get nimbula instance & passwords
        rack_config=ExalogicConfiguration(configurationDirectory=jsonConfigDirectory);                
        nimbula_info=rack_config.GetNimbulaInfo();
        passwords=rack_config.GetPasswords();
        
        # Get expected node list from ECU config
        vnodes=rack_config.GetVirtualCnodesInfo();
        
        # Get actual nodes from Nimbula
        nimbula=Nimbula(host_api=nimbula_info['host_api_ip'],nimbula_admin_user="/cloud/administrator",nimbula_admin_password=passwords['api_password']['root'],logger=logger);        
        nimbulaNodes=nimbula.getNodes();
        
        # Check if all expected nodes are in Nimbula cluster and active
        result=1;
        passed=1;
        for i in range(len(vnodes)):        
            if ( logger is not None):
                logger.debug("Checking if "+vnodes[i]['IPoIB-management']['ip']+" is part of the Nimbula cluster");
                found=0;
                for nNode in nimbulaNodes:
                    if (nimbulaNodes[nNode]['ip']==vnodes[i]['IPoIB-management']['ip']):
                        found=1;
                if(found!=1):
                    if ( logger is not None):
                        logger.error("No, it is not !!...");
                    passed=0;
        
        if (not passed):
            result=0;
            if ( logger is not None):
                logger.error("Some nodes not a part of Nimbula cluster");
                    
        #Check if there are any extra nodes in cluster !! (If nodes designated Physical have been added by mistake..)        
        passed=1;
        for nNode in nimbulaNodes:
            found=1;
            for i in range(len(vnodes)):
                if (nimbulaNodes[nNode]['ip']==vnodes[i]['IPoIB-management']['ip']):
                    found=0;                    
            if(found):
                passed=0;
                result=result and 0;

        if (not passed):
            if ( logger is not None):
                logger.error("Some extra nodes found in Nimbula cluster");
                        
        #Check if all nodes are active
        passed=1;
        for nNode in nimbulaNodes:
                if (nimbulaNodes[nNode]['state']!="active"):
                    if ( logger is not None):
                        logger.error("Node "+nimbulaNodes[nNode]['ip']+" not active");
                    result=result and 0;
                    passed=0;
        
        if (not result):
            raise ECUTestFailureError("Nimbula nodes number/state not as expected");
