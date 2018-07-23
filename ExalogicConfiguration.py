#!/usr/bin/python

import sys;

#export PATH=/usr/local/bin:${PATH}
#Modules required to be installed
import json
from netaddr import *

# To change this license header, choose License Headers in Project Properties.
# To change this template file, choose Tools | Templates
# and open the template in the editor.

__author__="Biju"
__date__ ="$Apr 15, 2015 9:07:24 AM$"

class ExalogicConfiguration:    
    """    
    Class representing the Exalogic Rack Configuration    
    """
    
    def __init__(self,configurationDirectory,compute_nodes_info="cnodes_target.json",rack_config="rack_info.json",eth_network_info="eth_networks.json",ipoib_network_info="ipoib_networks.json",common_host_config_info="common_host_config.json",ib_switch_info="switches_target.json",nimbula_info="nimbula.json",passwords_info="passwords.json",logger=None,debug=0):

       self.configurationDirectory=configurationDirectory;
       self.compute_nodes_info=compute_nodes_info;
       self.rack_config=rack_config;
       self.eth_network_info=eth_network_info;
       self.ipoib_network_info=ipoib_network_info;        
       self.common_host_config_info=common_host_config_info;
       self.ib_switch_info=ib_switch_info;
       self.nimbula_info=nimbula_info;
       self.passwords_info=passwords_info;
       self.logger=logger;
       self.debug=0;


    def GetCnodesInfo(self):        
        """
        Fetch information on compute nodes in the rack from the Exalogic ECU configuration files
        This method returns the information in the form of a dictionary object with compute node number as index 
        """

        cnodes_file=self.configurationDirectory+"/"+self.compute_nodes_info;

        try:

            cnodes_fobj=open(cnodes_file);

        except IOError:

            if (self.logger is not None ): 
                self.logger.info("I/O error:"+sys.exc_info()[0]);            

            if(self.debug):
                    print "I/O error:"+sys.exc_info()[0];
            raise;

        except:

            if (self.logger is not None ): 
                self.logger.info("Unexpected error:"+sys.exc_info()[0]);            
                raise;

            if(self.debug):
                    print "Unexpected error:"+sys.exc_info()[0];

            raise;

        cnodes=json.load(cnodes_fobj);

        return cnodes;

    def GetVirtualCnodesInfo(self):        
        """
        Fetch information on all compute nodes designated to be Virtual in the rack from the Exalogic ECU configuration files
        This method returns the information in the form of a dictionary object with compute node number as index 
        """

        file=self.configurationDirectory+"/"+self.compute_nodes_info;

        try:

            fobj=open(file);

        except IOError:

            if (self.logger is not None ): 
                self.logger.info("I/O error:"+sys.exc_info()[0]);            

            if(self.debug):
                    print "I/O error:"+sys.exc_info()[0];
            raise;

        except:

            if (self.logger is not None ): 
                self.logger.info("Unexpected error:"+sys.exc_info()[0]);            
                raise;

            if(self.debug):
                    print "Unexpected error:"+sys.exc_info()[0];

            raise;

        vnodes=json.load(fobj);
        outerLoop=1;
        
        while (outerLoop):
            outerLoop=0;
            innerLoop=1;
            for i in range(len(vnodes)):
                if (innerLoop):                
                    if (vnodes[i]['type']!="Virtual"):
                        innerLoop=0;
                        del vnodes[i];
                        outerLoop=1;
                        
        
        return vnodes;

    def GetDomain(self):
        """
        Fetch domain of Exalogic rack from ECU configuration files
        """        

        file=self.configurationDirectory+"/"+self.common_host_config_info;

        try:

               fobj=open(file);

        except IOError:

           if (self.logger is not None): 
               self.logger.info("I/O error:"+sys.exc_info()[0]);            

           if(self.debug):
                   print "I/O error:"+sys.exc_info()[0];
           raise;

        except:

           if (self.logger is not None): 
               self.logger.info("Unexpected error:"+sys.exc_info()[0]);            
               raise;

           if(self.debug):
                   print "Unexpected error:"+sys.exc_info()[0];
           raise;

        rack_config=json.load(fobj);

        return rack_config.get("domain","");		


    def GetRackSize(self):
        """
        Get rack size from ECU configuration file. Method returns 0,1,2,3 respectively for Eigth,Quarter,Half & Full rack sizes
        """

        file=self.configurationDirectory+"/"+self.rack_config;

        try:
           fobj=open(file);

        except IOError:

           if (self.logger is not None): 
               self.logger.info("I/O error:"+sys.exc_info()[0]);            

           if(self.debug):
                   print "I/O error:"+sys.exc_info()[0];
           raise;

        except:

           if (self.logger is not None): 
               self.logger.info("Unexpected error:"+sys.exc_info()[0]);            
               raise;

           if(self.debug):
                   print "Unexpected error:"+sys.exc_info()[0];
           raise;

        rack_config=json.load(fobj);
        if (rack_config.get("size",0)):
               if (rack_config['size']=="Eigth"):
                       #One Eighth Rack
                       return 0;
               elif(rack_config['size']=="Quarter"):
                       #Quarter Rack
                       return 1;
               elif(rack_config['size']=="Half"):
                       #Half Rack
                       return 2;			
               elif(rack_config['size']=="Full"):
                       #Full Rack
                       return 3;						

        return "";		

    def GetIbSwitchInfo(self):        
        """
        Fetch information on Infiniband switches in the rack from the Exalogic ECU configuration files
        This method returns the information in the form of a dictionary object with switches as index 
        """        

        switches_file=self.configurationDirectory+"/"+self.ib_switch_info;

        try:
           switches_fobj=open(switches_file);
        except IOError:

           if (self.logger is not None): 
               self.logger.info("I/O error:"+sys.exc_info()[0]);            

           if(self.debug):
                   print "I/O error:"+sys.exc_info()[0];
           raise;

        except:

           if (self.logger is not None): 
               self.logger.info("Unexpected error:"+sys.exc_info()[0]);            
               raise;

           if(self.debug):
                   print "Unexpected error:"+sys.exc_info()[0];
           raise;

        switches=json.load(switches_fobj);

        return switches;

    def GetEthDefaultGateway(self):
        """
        Fetch default gateway of eth default networm from Exalogic ECU configuration files
        """        

        file=self.configurationDirectory+"/"+self.common_host_config_info;

        try:
               fobj=open(file);
        except IOError:

           if (self.logger is not None): 
               self.logger.info("I/O error:"+sys.exc_info()[0]);            

           if(self.debug):
                   print "I/O error:"+sys.exc_info()[0];
           raise;

        except:

           if (self.logger is not None): 
               self.logger.info("Unexpected error:"+sys.exc_info()[0]);            
               raise;

           if(self.debug):
                   print "Unexpected error:"+sys.exc_info()[0];
           raise;

        rack_config=json.load(fobj);
        if (rack_config.get("default_gateway",1)):
               return rack_config['default_gateway'];
        else:
               return "";		

    def GetIPoIBDefaultAttr(self,network_name,attribute):        
        """
        Fetch any attribute of any given IPoIB network from Exalogic ECU configuration files
        """

        file=self.configurationDirectory+"/"+self.ipoib_network_info;
        i=0;

        try:

           fobj=open(file);

        except IOError:

           if (self.logger is not None): 
               self.logger.info("I/O error:"+sys.exc_info()[0]);            

           if(self.debug):
                   print "I/O error:"+sys.exc_info()[0];
           raise;

        except:

           if (self.logger is not None): 
               self.logger.info("Unexpected error:"+sys.exc_info()[0]);            
               raise;

           if(self.debug):
                   print "Unexpected error:"+sys.exc_info()[0];
           raise;

        network_info=json.load(fobj);

        for i in range(0,i<len(network_info)):
               if(str(network_info[i]['name'])==network_name):
                       ip_network=IPNetwork(network_info[i]['ip_network']);
                       return ip_network.netmask;
               i+=1;

        return "";		

    def GetEthDefaultAttr(self,network_name,attribute):
        """
        Fetch any attribute of any given IPoIB network from Exalogic ECU configuration files
        """

        file=self.configurationDirectory+"/"+self.eth_network_info;
        i=0;

        try:

           fobj=open(file);

        except IOError:

           if (self.logger is not None): 
               self.logger.info("I/O error:"+sys.exc_info()[0]);            

           if(self.debug):
                   print "I/O error:"+sys.exc_info()[0];
           raise;

        except:

           if (self.logger is not None): 
               self.logger.info("Unexpected error:"+sys.exc_info()[0]);            
               raise;

           if(self.debug):
                   print "Unexpected error:"+sys.exc_info()[0];
           raise;

        network_info=json.load(fobj);

        for i in range(0,i<len(network_info)):
               if(str(network_info[i]['name'])==network_name):
                       ip_network=IPNetwork(network_info[i]['ip_network']);
                       return ip_network.netmask;
               i+=1;

        return "";

    def GetNimbulaInfo(self):        
        """
        Fetch information on Nimbula from the Exalogic ECU configuration files
        This method returns the Nimbula information in the form of a dictionary object
        """

        file=self.configurationDirectory+"/"+self.nimbula_info;

        try:

            fobj=open(file);

        except IOError:

            if (self.logger is not None ): 
                self.logger.info("I/O error:"+sys.exc_info()[0]);            

            if(self.debug):
                    print "I/O error:"+sys.exc_info()[0];
            raise;

        except:

            if (self.logger is not None ): 
                self.logger.info("Unexpected error:"+sys.exc_info()[0]);            
                raise;

            if(self.debug):
                    print "Unexpected error:"+sys.exc_info()[0];

            raise;

        nimbula=json.load(fobj);

        return nimbula;
        
    def GetPasswords(self):        
        """
        Fetch information on password of various entities from the Exalogic ECU configuration files
        This method returns the Nimbula information in the form of a dictionary object
        """

        file=self.configurationDirectory+"/"+self.passwords_info;

        try:

            fobj=open(file);

        except IOError:

            if (self.logger is not None ): 
                self.logger.info("I/O error:"+sys.exc_info()[0]);            

            if(self.debug):
                    print "I/O error:"+sys.exc_info()[0];
            raise;

        except:

            if (self.logger is not None ): 
                self.logger.info("Unexpected error:"+sys.exc_info()[0]);            
                raise;

            if(self.debug):
                    print "Unexpected error:"+sys.exc_info()[0];

            raise;

        passwords=json.load(fobj);

        return passwords;
        
