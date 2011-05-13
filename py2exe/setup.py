from distutils.core import setup
import py2exe 



includes = ["encodings", "encodings.*"]

options = {"py2exe":
                {"compressed": 1, 
                 "optimize": 2,
                 "ascii": 1,
                 "includes":includes,
                 "bundle_files": 1, 
                }
           }

    
setup( 
    options = options,
    zipfile=None,
    console=[ { "script": "hf_robot.py", "icon_resources" : [(1, "package\hf.ico")]  } ],
    data_files=[ ( "conf", ["conf\conf.ini", "conf\logging.conf"] ) ,
                 # ( "", [r"C:\py2exe\dlls\kernel32.dll",    r"C:\py2exe\dlls\advapi32.dll", 
                 # r"C:\py2exe\dlls\shell32.dll",     r"C:\py2exe\dlls\oleaut32.dll", 
                 # r"C:\py2exe\dlls\ole32.dll",       r"C:\py2exe\dlls\user32.dll", 
                 # r"C:\py2exe\dlls\wsock32.dll",     r"C:\py2exe\dlls\ws2_32.dll"] ) ,
               ]


    )

