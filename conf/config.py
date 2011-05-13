#-------------------------------------------------------------------------------
# Name:        config.py
# Purpose:     Init config files
#
# Author:      alex
#
# Created:     28/07/2009
# Copyright:   (c) alex 2009
# Licence:     <your licence>
#-------------------------------------------------------------------------------
#!/usr/bin/env python
# -*- coding: utf-8 -*-


import os, string


class config():
    def __init__(self):

        path = os.getcwd()
        self.logging_file = os.path.join(path,'conf','logging.conf')
        self.conf_file = os.path.join(path,'conf','conf.ini')

        if not os.path.isfile(self.logging_file):
            print '无有效的logging.conf！'.decode('UTF-8').encode('mbcs')
            self.logging_file = ''

        if not os.path.isfile(self.conf_file):
            print '无有效的conf.ini！'.decode('UTF-8').encode('mbcs')
            self.conf_file = ''

