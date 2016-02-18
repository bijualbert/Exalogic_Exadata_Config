#! /usr/bin/python

# To change this license header, choose License Headers in Project Properties.
# To change this template file, choose Tools | Templates
# and open the template in the editor.

__author__="Arvind"
__date__ ="$Apr 18, 2015 3:10:35 AM$"

class ECUTestFailureError(Exception):
    """Exception raised for ECU test validation errors

    Attributes:
        msg  -- explanation of the error
    """

    def __init__(self, msg):
        self.msg = msg

class ECUKnownError(Exception):
    """Exception raised for ECU test validation errors

    Attributes:
        msg  -- explanation of the error
    """

    def __init__(self, msg):
        self.msg = msg        
        
class ILOMError(Exception):
    """Exception raised for ILOM operation errors

    Attributes:
        msg  -- explanation of the error
    """    
    def __init__(self, msg):
        self.msg = msg        
        
class OSCmdError(Exception):
    """Exception raised for ILOM operation errors

    Attributes:
        msg  -- explanation of the error
    """    
    def __init__(self, msg):
        self.msg = msg                