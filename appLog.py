# -*- coding: utf-8 -*-
'''
SNSAPP Log Tools
'''

import logging
import inspect
import os
from time import strftime

class SNSAPPLog(object):

    #Static variables
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL

    VERBOSE = True

    def __init__(self):
        if not os.path.exists('applog'):
            os.mkdir('applog')
        super(SNSAPPLog).__init__()
        raise SNSAPPLogNoInstantiation

    @staticmethod
    def init(logfile = None, level = WARNING, verbose = True):
        """
        Init the log basic configurations. It should
        be called only once over the entire execution.

        If you invoke it for multiple times, only the
        first one effects. This is the behaviour of
        logging module.

        """

        # Debug information writes to log using SNSAPPLog.debug().
        # How do you debug the logger itself...?
        # Here it is...
        # We fall back to the print.
        # They should be comment out to make the screen clean.
        #print "=== init log ==="
        #print "logfile:%s" % logfile
        #print "level:%s" % level
        #print "verbose:%s" % verbose

        if logfile:
            logging.basicConfig(\
                    format='[%(levelname)s][%(asctime)s]%(message)s', \
                    datefmt='%Y%m%d-%H%M%S', \
                    level = level, \
                    filename = logfile
                    )
        else:
            logging.basicConfig(\
                    format='[%(levelname)s][%(asctime)s]%(message)s', \
                    datefmt='%Y%m%d-%H%M%S', \
                    level = level
                    )
        SNSAPPLog.VERBOSE = verbose

    @staticmethod
    def __env_info():
        if SNSAPPLog.VERBOSE:
            caller = inspect.stack()[2]
            fn = os.path.basename(caller[1])
            no = caller[2]
            func = caller[3]
            return "[%s][%s][%s]" % (fn, func, no)
        else:
            return ""

    @staticmethod
    def debug(fmt, *args):
        logging.debug(SNSAPPLog.__env_info() + fmt, *args)

    @staticmethod
    def info(fmt, *args):
        logging.info(SNSAPPLog.__env_info() + fmt, *args)

    @staticmethod
    def warning(fmt, *args):
        logging.warning(SNSAPPLog.__env_info() + fmt, *args)

    @staticmethod
    def warn(fmt, *args):
        logging.warn(SNSAPPLog.__env_info() + fmt, *args)

    @staticmethod
    def error(fmt, *args):
        logging.error(SNSAPPLog.__env_info() + fmt, *args)

    @staticmethod
    def critical(fmt, *args):
        logging.critical(SNSAPPLog.__env_info() + fmt, *args)
    
    @staticmethod
    def status_user(status='No status', action='No action'):
        time = strftime("%a, %d %b %Y %H:%M:%S")
        with open('APPLOG/status_user_behaviour.log','a') as logfile_status_user:
            logfile_status_user.write('[Status User Behaviour][{0}][{1}][{2}] \n'.format(time,status,action))
        
        logging.info(SNSAPPLog.__env_info() + '[Status User Behaviour][{0}][{1}][{2}] \n'.format(time,status,action))
            
    @staticmethod
    def system_info(status='No status', action='No action'):
        time = strftime("%a, %d %b %Y %H:%M:%S")
        with open('APPLOG/system_info.log','a') as logfile_system_info:
            logfile_system_info.write('[SYSTEM INFO][{0}][{1}][{2}] \n'.format(time,status,action))
            
        logging.info(SNSAPPLog.__env_info() + '[SYSTEM INFO][{0}][{1}][{2}] \n'.format(time,status,action))
            
    @staticmethod
    def user_behaviour(status='No status', action='No action'):
        time = strftime("%a, %d %b %Y %H:%M:%S")
        with open('APPLOG/user_behaviour.log','a') as logfile_user_behaviour:
            logfile_user_behaviour.write('[User behaviour][{0}][{1}][{2}] \n'.format(time,status,action))
            
        logging.info(SNSAPPLog.__env_info() + '[User behaviour][{0}][{1}][{2}] \n'.format(time,status,action))
            
    @staticmethod
    def device_behaviour(status='No status', action='No action'):
        time = strftime("%a, %d %b %Y %H:%M:%S")
        with open('APPLOG/device_behaviour.log','a') as logfile_device_behaviour:
            logfile_device_behaviour.write('[Device behaviour][{0}][{1}][{2}] \n'.format(time,status,action))
            
        logging.info(SNSAPPLog.__env_info() + '[Device behaviour][{0}][{1}][{2}] \n'.format(time,status,action))
    
    @staticmethod
    def device_stop():
        time = strftime("%a, %d %b %Y %H:%M:%S")
        with open('APPLOG/system_info.log','a') as logfile_system_info:
            logfile_system_info.write('[SYSTEM INFO][{0}][{1}][{2}] \n'.format(time,'No status','App stop'))
            logfile_system_info.write('-------------CYCLE END--------------- \n \n')
        with open('APPLOG/status_user_behaviour.log','a') as logfile_system_info:
            logfile_system_info.write('[Status User Behaviour][{0}][{1}][{2}] \n'.format(time,'No status','App stop'))
            logfile_system_info.write('-------------CYCLE END--------------- \n \n')
        with open('APPLOG/user_behaviour.log','a') as logfile_system_info:
            logfile_system_info.write('[User behaviour][{0}][{1}][{2}] \n'.format(time,'No status','App stop'))
            logfile_system_info.write('-------------CYCLE END--------------- \n \n')
        with open('APPLOG/device_behaviour.log','a') as logfile_system_info:
            logfile_system_info.write('[Device behaviour][{0}][{1}][{2}] \n'.format(time,'No status','App stop'))
            logfile_system_info.write('-------------CYCLE END--------------- \n \n')
            
        logging.info(SNSAPPLog.__env_info() + '-------------CYCLE END--------------- \n \n')
            
    @staticmethod
    def device_pause():
        time = strftime("%a, %d %b %Y %H:%M:%S")
        with open('APPLOG/system_info.log','a') as logfile_system_info:
            logfile_system_info.write('[SYSTEM INFO][{0}][{1}][{2}] \n \n'.format(time,'No status','App pause'))
        with open('APPLOG/status_user_behaviour.log','a') as logfile_system_info:
            logfile_system_info.write('[Status User Behaviour][{0}][{1}][{2}] \n \n'.format(time,'No status','App pause'))
        with open('APPLOG/user_behaviour.log','a') as logfile_system_info:
            logfile_system_info.write('[User behaviour][{0}][{1}][{2}] \n \n'.format(time,'No status','App pause'))
        with open('APPLOG/device_behaviour.log','a') as logfile_system_info:
            logfile_system_info.write('[Device behaviour][{0}][{1}][{2}] \n \n'.format(time,'No status','App pause'))
            
        logging.info(SNSAPPLog.__env_info() + 'App pause \n \n')
            
    @staticmethod
    def device_start():
        time = strftime("%a, %d %b %Y %H:%M:%S")
        with open('APPLOG/system_info.log','a') as logfile_system_info:
            logfile_system_info.write('-------------CYCLE START------------- \n')
            logfile_system_info.write('[SYSTEM INFO][{0}][{1}][{2}] \n'.format(time,'No status','App start'))
        with open('APPLOG/status_user_behaviour.log','a') as logfile_system_info:
            logfile_system_info.write('-------------CYCLE START------------- \n')
            logfile_system_info.write('[Status User Behaviour][{0}][{1}][{2}] \n'.format(time,'No status','App start')) 
        with open('APPLOG/user_behaviour.log','a') as logfile_system_info:
            logfile_system_info.write('-------------CYCLE START------------- \n')
            logfile_system_info.write('[User behaviour][{0}][{1}][{2}] \n'.format(time,'No status','App start')) 
        with open('APPLOG/device_behaviour.log','a') as logfile_system_info:
            logfile_system_info.write('-------------CYCLE START------------- \n')
            logfile_system_info.write('[Device behaviour][{0}][{1}][{2}] \n'.format(time,'No status','App start'))
            
        logging.info(SNSAPPLog.__env_info() + '-------------CYCLE START------------- \n') 
        
class SNSAPPLogNoInstantiation(Exception):
    """docstring for SNSAPPLogNoInstantiation"""
    def __init__(self):
        super(SNSAPPLogNoInstantiation, self).__init__()

    def __str__(self):
        return "You can not instantiate SNSAPPLog. "\
                "Call its static methods directly!"
