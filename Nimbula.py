#! /usr/bin/python

__author__ = "Arvind"
__date__ = "$Apr 17, 2015 9:12:53 AM$"

from Server import *;

class Nimbula(object):
    """    
    Class which represents Nimbula 
    
    Attributes:
        
        host_api: DNS Name or IP of Nimbula Admin API
        nimbula_node_user: Name of any Nimbula compute node user (Assumption is all nodes have this user)
        nimbula_node_password: Name of any Nimbula compute node password (Assumption is all nodes have this user)
        nimbula_admin_user: Nimbula admin user
        nimbula_admin_password: Nimbula admin password
            
    """
    
    def __init__(self,host_api,nimbula_node_user="oracleadmin",nimbula_node_password="welcome1",nimbula_admin_user="/cloud/administrator",nimbula_admin_password="EXAlogic_123",logger=None):
        
        self.host_api=host_api;
        self.nimbula_node_user=nimbula_node_user;
        self.nimbula_node_password=nimbula_node_password;
        self.nimbula_admin_user=nimbula_admin_user;
        self.nimbula_admin_password=nimbula_admin_password;
        self.logger=logger;
        
    def getVersion(self):
        """
        Get Nimbula version
        """

        nimbulaVersion=rc=rMsg=cmdOut=None;
        
        apiNode=Server("apiNode",ip=self.host_api,user=self.nimbula_node_user,password=self.nimbula_node_password,prompt=".*?~]\$");
        (rc,rMsg,cmdOut)=apiNode.ExecCmd("cat /etc/nimbula_version");

        #Version: 14.1.13-20150327.1754\r\nBase: el\r\nDate: 20150329\r\nArch: x86_64\r\nHypervisor: xen
        match=re.search(".*?Version:\s+([\d.]+?)\-.*?",cmdOut,re.M);
        
        if(match):
            nimbulaVersion=match.group(1);
        
        return nimbulaVersion;
    
    def getNodes(self):
        """
        Get compute nodes that are part of the Nimbula cluster
        """
        
        rc=rMsg=cmdOut=None;
        nimbulaNodes={};
        
        apiNode=Server("apiNode",ip=self.host_api,user=self.nimbula_node_user,password=self.nimbula_node_password,prompt=".*?~]\$");
        
        if (self.logger is not None):
            self.logger.debug("Executing command:nimbula-get-nodes --user "+self.nimbula_admin_user+" --password "+self.nimbula_admin_password+" --all");
            
        (rc,rMsg,cmdOut)=apiNode.ExecCmd("nimbula-get-nodes --user "+self.nimbula_admin_user+" --password "+self.nimbula_admin_password+" --all");                    
        
        if (self.logger is not None):
            self.logger.debug("Output:");
            self.logger.debug("Output:"+cmdOut);
        
        match=re.search("^.*?\n(.*)\n.*?$",cmdOut,re.S);
        
        if(match):
            if (self.logger is not None):
                self.logger.debug("Matched:");
                self.logger.debug("Matched:"+match.group(1));
                
            nodeList=match.group(1).split("\n");
        else:
            if (self.logger is not None):
                self.logger.error("Unable to get list of nimbula nodes");
            raise ECUKnownError("Unable to get list of nimbula nodes");
                
        for index in range(len(nodeList)):
            nodeInfo=nodeList[index].split();
            nimbulaNodes[index]=nimbulaNodes.get(index,{});
            nimbulaNodes[index]['id']=nodeInfo[0];
            nimbulaNodes[index]['state']=nodeInfo[1];
            nimbulaNodes[index]['ip']=nodeInfo[2];
            
        if (len(nimbulaNodes)==0):
            self.logger.error("Unable to identify nimbula nodes attributes");
            raise ECUKnownError("Unable to identify nimbula nodes attributes");
        
        return nimbulaNodes;
            
            
        
        
        
        
        
        