#!/usr/bin/python

import sys;
import logging;

from ExalogicConfiguration import *;
from Server import *;
import generic;

global logger;
    
logger = logging.getLogger('MyLogger')

stdoutFileHandler = logging.StreamHandler(sys.stdout)
stdoutFileHandler.setLevel(logging.ERROR);
logger.addHandler(stdoutFileHandler);

rack_config=ExalogicConfiguration("/root/ECU/slce23/stack18/config");
domain=rack_config.GetDomain();
print domain;

cnodes=rack_config.GetCnodesInfo();

for i in range(len(cnodes)):
    print cnodes[i]['host'];
    
rackSize=rack_config.GetRackSize();

print rackSize;

defaultGateway=rack_config.GetEthDefaultGateway();

print defaultGateway;

ipoibNetMask=rack_config.GetIPoIBDefaultAttr("IPoIB-default","netmask");

print ipoibNetMask;

ethNetMask=rack_config.GetEthDefaultAttr("eth-admin","netmask");

print ethNetMask;

server=Server(name="slc01pcg",ip="10.240.106.31",user="root",password="root#123",prompt=".*?#",logger=logger,debug=0);
os=server.getOS();

print os;