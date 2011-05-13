#AdvancedConfigParser.py

import re
from ConfigParser import *

class AdvancedRawConfigParser(RawConfigParser):

    def write(self, fp):
        """Write an .ini-format representation of the configuration state.

        write ini by line no 
        """
        
        if self._defaults:
            section = DEFAULTSECT
            lineno = self._location[section]
            self._data[lineno] = "[%s]\n" %section
            for (key, value) in self._defaults.items():
                if key != "__name__":
                    wholename = section + '_' + key  #KVS
                    lineno = self._location[wholename]
                    self._data[lineno] = "%s = %s\n" %(key, str(value).replace('\n', '\n\t'))
                    
        for section in self._sections:
            lineno = self._location[section]
            self._data[lineno] = "[%s]\n" % section
            for (key, value) in self._sections[section].items():
                if key != "__name__":
                    wholename = section + '_' + key  #KVS
                    lineno = self._location[wholename]
                    self._data[lineno] = "%s = %s\n" %(key, str(value).replace('\n', '\n\t'))
            
        for line in self._data:
            fp.write("%s"%line)
        fp.close()
            
    def _read(self, fp, fpname):
        """Parse a sectioned setup file.

        When parsing ini file, store the line no in self._location
        and store all lines in self._data
        """
        self._location = {}
        self._data = [] 
        cursect = None                            # None, or a dictionary
        optname = None
        lineno = 0
        e = None                                  # None, or an exception
        while True:
            line = fp.readline()
            self._data.append(line) #KVS
            if not line:
                break
            lineno = lineno + 1
            if line.strip() == '' or line[0] in '#;':
                continue
            if line.split(None, 1)[0].lower() == 'rem' and line[0] in "rR":
                # no leading whitespace
                continue
            if line[0].isspace() and cursect is not None and optname:
                value = line.strip()
                if value:
                    cursect[optname] = "%s\n%s" % (cursect[optname], value)
            else:
                mo = self.SECTCRE.match(line)
                if mo:
                    sectname = mo.group('header')
                    if sectname in self._sections:
                        cursect = self._sections[sectname]
                    elif sectname == DEFAULTSECT:
                        cursect = self._defaults
                        self._location[DEFAULTSECT] = lineno -1 #KVS
                        
                    else:
                        cursect = {'__name__': sectname}
                        self._location[sectname] = lineno -1 #KVS
                        self._sections[sectname] = cursect

                    optname = None
                elif cursect is None:
                    raise MissingSectionHeaderError(fpname, lineno, line)
                else:
                    mo = self.OPTCRE.match(line)
                    if mo:
                        optname, vi, optval = mo.group('option', 'vi', 'value')
                        if vi in ('=', ':') and ';' in optval:
                            pos = optval.find(';')
                            if pos != -1 and optval[pos-1].isspace():
                                optval = optval[:pos]
                        optval = optval.strip()
                        if optval == '""':
                            optval = ''
                        optname = self.optionxform(optname.rstrip())
                        cursect[optname] = optval
                         
                        if cursect == self._defaults:
                            wholename = DEFAULTSECT + '_' + optname  #KVS
                        else:
                            wholename = cursect['__name__'] + '_' + optname  #KVS
                        self._location[wholename] = lineno-1     #KVS
                    else:
                         if not e:
                            e = ParsingError(fpname)
                         e.append(lineno, repr(line))
        if e:
            raise e

    def add_section(self, section):
        """Create a new section in the configuration.

        Raise DuplicateSectionError if a section by the specified name
        already exists.
        """
        if section in self._sections:
            raise DuplicateSectionError(section)
        self._sections[section] = {}

        linecount = len(self._data)
        self._data.append('\n')
        self._data.append('%s'%section)
        self._location[section] = linecount + 1
        

    def set(self, section, option, value):
        """Set an option."""
        if not section or section == DEFAULTSECT:
            sectdict = self._defaults
        else:
            try:
                sectdict = self._sections[section]
            except KeyError:
                raise NoSectionError(section)
        option = self.optionxform(option)
        add = False
        if not option in sectdict:
            add = True
        sectdict[self.optionxform(option)] = value
        if add:
            lineno = self._location[section]
            self._data.append('')
            idx = len(self._data)
            while idx>lineno:
                self._data[idx-1] = self._data[idx-2]
                idx = idx-1
            self._data[idx+1] = '%s = %s\n'%(option,value)
            self._location[section+'_'+option]=idx+1
            for key in self._location:
                if self._location[key] > lineno:
                    self._location[key] = self._location[key] + 1
            self._data[idx+1] = '%s = %s\n'%(option,value)
            self._location[section+'_'+option]=idx+1
                
                
        
    def remove_option(self, section, option):
        """Remove an option. """
        if not section or section == DEFAULTSECT:
            sectdict = self._defaults
        else:
            try:
                sectdict = self._sections[section]
            except KeyError:
                raise NoSectionError(section)
        option = self.optionxform(option)
        existed = option in sectdict
        if existed:
            del sectdict[option]
            wholename = section + '_' + option
            lineno  = self._location[wholename]
            
            del self._location[wholename]
            for key in self._location:
                
                if self._location[key] > lineno:
                    self._location[key] = self._location[key] -1 
            del self._data[lineno]
        return existed

    def remove_section(self, section):
        """Remove a file section."""
        existed = section in self._sections
        if existed:
            lstOpts = []
            for option in self._sections[section]:
                if option == '__name__':
                    continue
                lstOpts.append(option)
            for option in lstOpts:
                self.remove_option(section,option)

            del self._sections[section]
            wholename = section
            lineno  = self._location[wholename]
            
            del self._location[wholename]
            for key in self._location:
                if self._location[key] > lineno:
                    self._location[key] = self._location[key] -1 
            del self._data[lineno]
        return existed


class AdvancedConfigParser(AdvancedRawConfigParser):

    pass


class AdvancedSafeConfigParser(AdvancedConfigParser):

    pass
