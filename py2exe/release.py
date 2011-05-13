#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""to release package for hf_robot

    Copyright (C) 2009, Suzhou, bin.c.chen@gmail.com

    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    *KEEP THIS HEADER INFORMATION*

"""

__author__ = "alex (bin.c.chen@gmail.com)"
__version__ = "$Revision:  $"
__date__ = "$Date: 2009/08/08 08:08:00 $"
__copyright__ = "Copyright (c) 2009 Alex"
__license__ = "Python"

import os, time
import re
import  shutil


DEBUG = 1



class Release(object):
    def __init__(self):
        curDate = r'__date__ = "$%s $"' %time.strftime( "%a, %d %b %Y %H:%M:%S", time.localtime() )

        self.relRepStr = {
           # search item          File  target  source
           "debug"                :{"FILE": ["hf_robot.py"],
                                    "TGT": r"DEBUG = False",
                                    "SRC": r"DEBUG = True" },

           "wrMode"               :{"FILE": ["hf_robot.py"],
                                    "TGT": r'debug_file = open("debug.txt", "w")',
                                    "SRC": r"debug_file = open\(\"debug\.txt\", \"a\"\)" },

           "date"                 :{"FILE": ["hf_robot.py"],
                                    "TGT": curDate,
                                    "SRC": r"__date__ = \"\$Date: 2009/08/07 14:50:59 \$\""},

           "auto"                 :{"FILE": ["conf", "conf.ini"],
                                    "TGT": r"auto                = 0",
                                    "SRC": r"auto ([^\n]+)" },

           "email"                :{"FILE": ["conf", "conf.ini"],
                                    "TGT": r"email               = 0",
                                    "SRC": r"email([^\n]+)" },

           "password"             :{"FILE": ["conf", "conf.ini"],
                                    "TGT": r"password            = 0",
                                    "SRC": r"password([^\n]+)" },
                                    
           "seed_CID"             :{"FILE": ["conf", "conf.ini"],
                                    "TGT": r"seed_CID            = 517",
                                    "SRC": r"seed_CID([^\n]+)" },
        }
        
    def chg_version(self,fs):
   	    # change version number

        verReStr = "Revision: (?P<ver1>\d+)\.(?P<ver2>\d+)\.(?P<ver3>\d+)"
        folder = r'F:\svn\hf_robot'
        rel_ver = ""
        
        for f in fs:
        	f = os.path.join(folder, f)
        	rFile = open(f, 'r')
        	lines = rFile.read()
        	rFile.close()
        	
        	obj = re.compile(verReStr).search(lines)
       		if obj:
       		    rel_ver = "%s.%s" %(obj.group("ver1"), obj.group("ver2"))
        	    verSubStr = "Revision: %s.%03d" \
                    %(rel_ver, int(obj.group("ver3"))+1 )
        	else:
        	    verSubStr = ""

        	print verSubStr
        	temp_lines,n = re.compile(verReStr).subn(verSubStr, lines)
        	# print 'n: ',n

        	wFile = open(f, 'w')
        	wFile.write(temp_lines)
        	wFile.close()
        
        # hf_setup_script.nsi
        rStr = "!define PRODUCT_VERSION \"([\d\.]+)\""
        rSubStr = "!define PRODUCT_VERSION \"%s\"" %rel_ver
        f = r'package\hf_setup_script.nsi'
        
    	rFile = open(f, 'r')
    	lines = rFile.read()
    	rFile.close()

    	print rSubStr
    	temp_lines,n = re.compile(rStr).subn(rSubStr, lines)
    	# print 'n: ',n

    	wFile = open(f, 'w')
    	wFile.write(temp_lines)
    	wFile.close()
        	
        
    def cp(self,objs):
        srcPath = r'F:\svn\hf_robot'
        dstPath = r'.'
    
        for obj in objs:
             
            src = os.path.join(srcPath, obj)
            dst = os.path.join(dstPath, obj)
            # copy  file
            if os.path.isfile(src):
                if os.path.exists(dst):
                   # print "Remove file: %s" % dst
                   os.remove(dst)
                shutil.copyfile(src, dst)
                print "Copy %s --> %s" % (src, dst)
                
            # copy  folder
            if os.path.isdir(src):
                if os.path.exists(dst):
                    # print "Remove folder: %s" % dst
                    if os.name == 'nt':
                        os.system('rd /S /Q ' + dst) # for Windows
                    else:
                        os.system('rm -rf ' + dst) # for Linux

                try :
                    shutil.copytree(src, dst)
                    print "Copy %s --> %s" % (src, dst)
                except Exception, e:
                    print e
            
    def rep(self):

		# extend (called by SGMLParser.__init__)
		for key in self.relRepStr:
		    s =  "changing %s ..." % key
		    print s,
		    
		    if len(self.relRepStr[key]["FILE"]) == 2:
		        file = os.path.join(self.relRepStr[key]["FILE"][0], self.relRepStr[key]["FILE"][1] )
		    else:
		        file = self.relRepStr[key]["FILE"][0]

		    if not os.path.isfile(file):
		        print "Can't find file! %s" %file
		        return
		    
		    rFile = open(file, 'r')
		    lines = rFile.read()
		    rFile.close()

		    re_sub = re.compile(self.relRepStr[key]["SRC"])
		    temp_lines = re_sub.sub(self.relRepStr[key]["TGT"], lines)
		    
		    wFile = open(file, 'w')
		    wFile.write(temp_lines)
		    wFile.close()
		    print "\tDone."
	

if __name__ == "__main__":
    rel = Release()
    
    fs = ['hf_robot.py']
    rel.chg_version(fs) 
    objs = ['hf_robot.py', 'AdvancedConfigParser.py', 'conf']
    rel.cp(objs)
    rel.rep()
