#!/usr/bin/env
# -*- coding: utf-8 -*-
"""
This program is used to schmooze formats from firefox and add new ones
"""
import os
import subprocess
import json


def getFirefoxProfilePath(osUser=None,profileId=None):
    """
    get the path to a firefox profile
    :property osUser: user on the os to find (default=current user)
    :property profileId: firefox profile id (default=first with shortest name)

    TODO: only works on windows
    """
    path=os.environ['appdata']
    if osUser is not None:
        path=path.replace('\\%s\\'%os.environ['USERNAME'],'\\%s\\'%osUser)
    path=path+'\\Mozilla\\Firefox\\Profiles\\'
    if profileId is None:
        # find one
        profiles=[]
        selectedProfile=None
        for filename in os.listdir(path):
            filename=path+filename
            if os.path.isdir(filename) and filename.find('.default')>=0:
                profiles.append(filename)
                if selectedProfile is None or len(filename)<len(selectedProfile):
                    selectedProfile=filename
        if not profiles:
            raise Exception('WARN: no firefox profiles found in "%s"'%path)
        if len(profiles)>1:
            print('WARN: Multiple profiles to choose from:')
            for p in profiles:
                print(' ',p.rsplit('\\',1)[-1])
            print('Choosing:',selectedProfile.rsplit('\\',1)[-1])
        path=selectedProfile+'\\'
    else:
        path=path+profileId+'\\'
    return path


class FirefoxHandler:
    """
    A registered handler for a specific mimeType or url protocol

    The target can be either a path to an application on the local filesystem
    or a uriTemplate url linking to a webservice.
    """

    def __init__(self,name='',path=None,uriTemplate=None):
        self.name=name
        self.mimeType=None # if this is a mimeType hanler, this is the type
        self.urlProtocol=None # if this is a urlProtocol type handler, this is the url protocol (without ":")
        self.path=path # if present, the path to the file that will handle this protocol
        self.uriTemplate=uriTemplate # if present, the webservice that will handle this protocol

    @property
    def json(self):
        """
        a json string
        """
        return json.dumps(self.jsonDict)
    @json.setter
    def json(self,jsonString):
        self.jsonDict=json.loads(jsonString)

    @property
    def jsonDict(self):
        """
        a json-compatible dict
        """
        ret={}
        if self.name is not None and self.name:
            ret['name']=self.name
        if self.path is not None:
            ret['path']=self.path
        if self.uriTemplate is not None:
            ret['uriTemplate']=self.uriTemplate
        return ret
    @jsonDict.setter
    def jsonDict(self,jsonDict):
        self.name=jsonDict.get('name')
        self.path=jsonDict.get('path')
        self.uriTemplate=jsonDict.get('uriTemplate')

    def getCallString(self,url):
        """
        get a properly-formatted string of what calling this handler with this url would look like
        """
        ret=None
        if self.path is not None:
            import shlex
            ret=self.path
            url=shlex.quote(url)
            if ret.find('%%s')>=0:
                ret=ret.replace('%%s',url)
            else:
                ret='%s %s'%(ret,url)
        elif self.uriTemplate is not None:
            import urllib.parse
            ret=self.uriTemplate
            url=urllib.parse.quote_plus(url)
            if ret.find(r"""%s""")>=0:
                ret=ret.replace(r"""%s""",url)
            else:
                raise NotImplementedError("no \%s in handler - not sure what to do.\n  Handler = %s"%ret)
        return ret

    def __call__(self,url):
        """
        call this like a function, using data at a url as the input
        """
        cs=self.getCallString(url)
        if cs is None:
            raise Exception('Unable to run "%s" with no associated application or webservice uri to call'%url)
        if self.path is not None:
            print('Executing:',cs)
            po=subprocess.Popen(cs,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
            out,_=po.communicate()
            print(out)
        else:
            import webbrowser
            print('Opening URL:',cs)
            webbrowser.open(cs)

    @property
    def target(self):
        """
        The target can be either a path to an application on the local filesystem
        or a uriTemplate url linking to a webservice.
        """
        if self.path is not None:
            return self.path
        return self.uriTemplate

    def __repr__(self,indent=''):
        """
        string representation of this object
        """
        ret=[]
        if self.name:
            ret.append(self.name)
        else:
            ret.append('[unnamed]')
        if self.mimeType:
            ret.append('mimeType: %s'%self.mimeType)
        if self.urlProtocol:
            ret.append('urlProtocol: %s://'%self.urlProtocol)
        if self.target:
            ret.append('target: %s'%self.target)
        return indent+(('\n      '+indent).join(ret))


class FirefoxHandlerSet:
    """
    There can be multiple handlers for a given type
    """

    ACTION_EXECUTE_OS_DEFAULT_APPLICATION=0
    ACTION_MYSTERY=1 # TODO: I have never seen this set
    ACTION_EXECUTE_APPLICATION=2
    ACTION_OPEN_IN_FIREFOX=3
    ACTION_EXECUTE_APPLICATION_X=4 # TODO: don't know what the difference is

    def __init__(self,name='',extensions=None,handlers=None,action=None,stubEntry=False,ask=False):
        self.name=name # can sometimes be empty
        self.extensions=extensions # any file extensions associated with this
        self.action=action # one of the FirefoxHandlerSet.ACTION_* constants
        self.stubEntry=stubEntry # TODO: not sure what this means
        self.ask=ask # whether or not to prompt the user - we don't care about this
        self.handlers=[]
        if handlers is not None:
            for h in handlers:
                if h is None: # not sure what this means
                    h=FirefoxHandler()
                elif isinstance(h,dict):
                    h=FirefoxHandler(**h)
                self.handlers.append(h)

    @property
    def actionName(self):
        """
        same as self.action only as a decoded string
        """
        if self.action==self.ACTION_EXECUTE_OS_DEFAULT_APPLICATION:
            return 'ACTION_EXECUTE_OS_DEFAULT_APPLICATION'
        if self.action==self.ACTION_EXECUTE_APPLICATION:
            return 'ACTION_EXECUTE_APPLICATION'
        if self.action==self.ACTION_OPEN_IN_FIREFOX:
            return 'ACTION_OPEN_IN_FIREFOX'
        if self.action==self.ACTION_EXECUTE_APPLICATION_X:
            return 'ACTION_EXECUTE_APPLICATION_X'
        return 'Unknown action (%d)'%self.action
    @actionName.setter
    def actionName(self,actionName):
        if actionName.startswith('ACTION_') and hasattr(self,actionName):
            self.action=getattr(self,actionName)
        else:
            raise Exception('Uknown action name "%s"'%actionName)

    @property
    def jsonDict(self):
        """
        a json-compatible dict
        """
        ret={}
        if self.name is not None and self.name:
            ret['name']=self.name
        if self.extensions is not None:
            ret['extensions']=self.extensions
        if self.action is not None:
            ret['action']=self.action
        if self.stubEntry is not None and self.stubEntry:
            ret['stubEntry']=self.stubEntry
        if self.ask is not None and self.ask:
            ret['ask']=self.ask
        handlers=[]
        for handler in self.handlers:
            handlers.append(handler.jsonDict)
        if handlers:
            ret['handlers']=handlers
        return ret
    @jsonDict.setter
    def jsonDict(self,jsonDict):
        self.name=jsonDict.get('name')
        self.extensions=jsonDict.get('extensions')
        self.action=jsonDict.get('action')
        self.stubEntry=jsonDict.get('stubEntry',False)
        self.ask=jsonDict.get('ask',False)
        self.handlers=[]
        handlers=jsonDict.get('handlers')
        if handlers is not None:
            for h in handlers:
                if h is None: # not sure what this means
                    h=FirefoxHandler()
                elif isinstance(h,dict):
                    h=FirefoxHandler(**h)
                self.handlers.append(h)

    @property
    def json(self):
        """
        a json string
        """
        return json.dumps(self.jsonDict)
    @json.setter
    def json(self,jsonString):
        self.jsonDict=json.loads(jsonString)

    def getHandler(self,handlerName=None):
        """
        get the handler with the given name, or the default handler
        """
        if not self.handlers:
            p=(self.name,self.extensions)
            raise Exception('No handler explicitly defined for "%s" / %s'%p)
        if handlerName is None:
            return self.handlers[0]
        for handler in self.handlers:
            if handler.name==handlerName:
                return handler
        return self.handlers[0]

    def __call__(self,url,handlerName=None):
        """
        call like a function

        if handlerName is None, use the default handler for this type
        """
        if self.action in (self.ACTION_EXECUTE_APPLICATION,self.ACTION_EXECUTE_APPLICATION_X):
            return self.getHandler(handlerName)(url)
        if self.action==self.ACTION_OPEN_IN_FIREFOX:
            import webbrowser
            webbrowser.open(url)
        elif self.action==self.ACTION_EXECUTE_OS_DEFAULT_APPLICATION:
            # TODO: only works on windows
            po=subprocess.Popen(['start',url],shell=True,
                stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
            out,_=po.communicate()
            print(out)
        else:
            raise Exception('Unknown action %d'%self.action)
        return ''

    def __repr__(self,indent=''):
        ret=[]
        if self.name:
            ret.append('name: %s'%self.name)
        ret.append('ask: %s'%self.ask)
        if self.extensions is not None:
            ret.append('extensions: %s'%(', '.join(self.extensions)))
        ret.append('action: %s'%self.actionName)
        ret.append('stubEntry: %s'%self.stubEntry)
        if self.handlers:
            ret.append('handlers:')
            for h in self.handlers:
                ret.append(h.__repr__(indent+'  '))
        return indent+(('\n'+indent).join(ret))


class FirefoxFormats:
    """
    This program is used to schmooze formats from firefox and add new ones

    See also:
        firefox format handler plugins
        https://developer.mozilla.org/en-US/docs/Mozilla/Tech/XPCOM/Reference/Interface/nsIProtocolHandler

        interestingly, you can do webservice protocol handlers
        https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/manifest.json/protocol_handlers

        and a list of all firefox config files
        https://support.mozilla.org/en-US/kb/profiles-where-firefox-stores-user-data

        for example microsoft teams
        https://docs.microsoft.com/en-us/microsoftteams/platform/concepts/build-and-test/deep-links
    """

    def __init__(self,filename=None,osUser=None,profileId=None):
        self._osUser=osUser
        self._profileId=profileId
        self._filename=filename
        self._ext2mime=None
        self._mimeTypeHandlers=None
        self._urlProtocolHandlers=None
        self._version=None

    def _clear(self):
        """
        clearing data will force a reload next time anything is requested
        """
        self._filename=None
        self._ext2mime=None
        self._mimeTypeHandlers=None
        self._urlProtocolHandlers=None
        self._version=None

    @property
    def osUser(self):
        """
        the operating system user
        """
        return self._osUser
    @osUser.setter
    def osUser(self,osUser):
        self._osUser=osUser
        self._clear()

    @property
    def profileId(self):
        """
        the firefox profile id
        """
        return self._profileId
    @profileId.setter
    def profileId(self,profileId):
        self._profileId=profileId
        self._clear()


    @property
    def mimeTypeHandlers(self):
        """
        handlers for a certain mime type
        """
        if self._mimeTypeHandlers is None:
            self.load()
        return self._mimeTypeHandlers
    @property
    def urlProtocolHandlers(self):
        """
        handlers for a certain url type (eg. ftp: mailto: etc)
        """
        if self._urlProtocolHandlers is None:
            self.load()
        return self._urlProtocolHandlers
    @property
    def version(self):
        """
        the version of this format
        """
        if self._version is None:
            self.load()
        return self._version

    @property
    def ext2mime(self):
        """
        file extenstion to mime type mapping dictionary
        """
        if self._ext2mime is None:
            self._ext2mime={}
            for mimeType,handlers in self.mimeTypeHandlers.items():
                extensions=handlers.extensions
                if extensions is not None:
                    for ext in extensions:
                        self._ext2mime[ext]=mimeType
        return self._ext2mime

    def load(self,filename=None):
        """
        load everything from the profile

        (Called automatically as needed)
        """
        if filename is None:
            if self._filename is None:
                # find the current profile
                currentProfile=getFirefoxProfilePath(self.osUser,self.profileId)
                self._filename='%shandlers.json'%(currentProfile)
                print('Loading firefox profile:\n  %s'%self._filename)
            filename=self._filename
        else:
            self._filename=filename
        f=open(filename,'rb')
        data=f.read()
        f.close()
        self.json=data

    @property
    def json(self):
        """
        a json string
        """
        return json.dumps(self.jsonDict)
    @json.setter
    def json(self,jsonString):
        self.jsonDict=json.loads(jsonString)

    @property
    def jsonDict(self):
        """
        a json-compatible dict
        """
        mimesDict={}
        for k,v in self.mimeTypeHandlers.items():
            mimesDict[k]=v.jsonDict
        schemesDict={}
        for k,v in self.urlProtocolHandlers.items():
            schemesDict[k]=v.jsonDict
        return {
            'defaultHandlersVersion':self.version,
            'mimeTypes':mimesDict,
            'schemes':schemesDict
            }
    @jsonDict.setter
    def jsonDict(self,jsonDict):
        self._ext2mime=None
        self._version=jsonDict.get('defaultHandlersVersion')
        self._mimeTypeHandlers={}
        self._urlProtocolHandlers={}
        for name,v in jsonDict.get('mimeTypes',{}).items():
            handlers=FirefoxHandlerSet(**v)
            if name in self.mimeTypeHandlers:
                raise Exception('NAME COLLISION "%s"'%name)
            self._mimeTypeHandlers[name]=handlers
        for name,v in jsonDict.get('schemes',{}).items():
            handlers=FirefoxHandlerSet(**v)
            if name in self.urlProtocolHandlers:
                raise Exception('NAME COLLISION "%s"'%name)
            self._urlProtocolHandlers[name]=handlers

    def __repr__(self):
        """
        string representation of this object
        """
        ret=[]
        ret.append('MimeTypes:')
        for k,v in self.mimeTypeHandlers.items():
            ret.append('  '+k)
            ret.append(v.__repr__(indent='    '))
        ret.append('URL protocols:')
        for k,v in self.urlProtocolHandlers.items():
            ret.append('  '+k)
            ret.append(v.__repr__(indent='    '))
        return '\n'.join(ret)

    def doMime(self,url,mime=None,handler=None):
        """
        execute the handler for a mime type

        :property url:
        :property mime: the mime type of the resource at this url address
        :property handler: the name of a specific handler to use (if absent, use default hander)
        """
        if mime is None:
            # TODO: if mime is None, can we figure it out by doing sending like HTTP OPTIONS?
            raise Exception('No mime type specified')
        handlers=self.mimeTypeHandlers.get(mime)
        if handlers is None:
            raise Exception('No registered hander for mime type "%s"'%mime)
        return handlers(url,handler)

    def doUrl(self,url,handler=None):
        """
        execute the handler for a url type

        :property url: if this is http or https and there is no specific handler
            specified, then we will call doMime() instead
        :property handler: the name of a specific handler to use (if absent, use default hander)
        """
        proto=url.split(':',1)[0]
        if handler is None and proto in ('http','https'):
            self.doMime(url)
        handlers=self.urlProtocolHandlers.get(proto)
        if handlers is None:
            raise Exception('No registered hander for url type "%s:"'%proto)
        return handlers(url,handler)

    def fileExtensionToMime(self,path):
        """
        lookup the file extension of a given path
        """
        path=path.rsplit('.',1)[-1]
        return self.ext2mime.get(path)

    def doExtn(self,path,handler=None):
        """
        execute a handler based upon its file extension

        :property handler: the name of a specific handler to use (if absent, use default hander)

        (file extension is taken from path)
        """
        mime=self.fileExtensionToMime(path)
        if mime is None:
            raise Exception('unknown file extension for "%s"'%path)
        return self.doMime(path,mime,handler)

    def findFormat(self,url):
        """
        get a format handler for a given url
        """

    def setFormat(self,formatHandler):
        """
        set a format handler for a given format
        """


def cmdline(args):
    """
    Run the command line

    :param args: command line arguments (WITHOUT the filename)
    """
    printhelp=False
    if not args:
        printhelp=True
    else:
        fff=FirefoxFormats()
        for arg in args:
            if arg.startswith('-'):
                arg=[a.strip() for a in arg.split('=',1)]
                if arg[0] in ['-h','--help']:
                    printhelp=True
                elif arg[0] in ('--list','--ls'):
                    print(fff)
                elif arg[0]=='--doUrl':
                    if len(arg)>1:
                        url=arg[1].split(':',1)
                        handler=url[0].split(',')
                        if len(handler)>1:
                            url[0]=handler[-1]
                            handler=handler[0]
                        else:
                            handler=None
                        fff.doUrl(':'.join(url),handler)
                elif arg[0]=='--doExtn':
                    if len(arg)>1:
                        url=arg[1].split(':',1)
                        handler=url[0].split(',')
                        if len(handler)>1:
                            url[0]=handler[-1]
                            handler=handler[0]
                        else:
                            handler=None
                        fff.doExtn(':'.join(url),handler)
                elif arg[0]=='--doMime':
                    if len(arg)>1:
                        url=arg[1].split(':',1)
                        mime=url[0].split(',')
                        if len(mime)>1:
                            url[0]=handler[-1]
                            if len(mime)>2:
                                handler=mime[1]
                            else:
                                handler=None
                            mime=mime[0]
                        else:
                            mime=None
                            handler=None
                        fff.doMime(':'.join(url),mime,handler)
                elif arg[0]=='--json':
                    print(fff.json)
                elif arg[0]=='--ext2mime':
                    print(fff.ext2mime)
                elif arg[0]=='--user':
                    if len(arg)>1:
                        fff.osUser=arg[1]
                    else:
                        fff.osUser=None
                elif arg[0]=='--profile':
                    if len(arg)>1:
                        fff.profileId=arg[1]
                    else:
                        fff.profileId=None
                else:
                    print('ERR: unknown argument "'+arg[0]+'"')
            else:
                fff.doUrl(arg)
    if printhelp:
        print('Usage:')
        print('  _firefoxFormats.py [options] [urls]')
        print('Options:')
        print('   --user= ............ select an os user')
        print('   --profile= ......... select a firefox profile')
        print('   --list ............. list all external formats known to firefox')
        print('   --ls ............... list all external formats known to firefox')
        print('   --doMime=mimetype,[handler,]url')
        print('                        open the handler for a mime type')
        print('   --doUrl=[handler,]url')
        print('                        open the handler for a url protocol')
        print('   --doExtn=[handler,]url')
        print('                        open the handler for a file extension type')
        print('   --json ............. dump the json configuration to the console')
        print('   --ext2mime ......... list file extension -> mimetype mappings')
        print('Urls:')
        print('   does the same thing as doUrl')
        return -1
    return 0


if __name__=='__main__':
    import sys
    sys.exit(cmdline(sys.argv[1:]))