import httplib2, os, shutil
import urllib, time, logging, datetime
import xml.etree.ElementTree as ET

"""
ownSync is a module used to sync files to/from ownCloud.
"""

class ownClient():

  """
  ownClient main class for the ownSync utility, it makes a connection to the ownCloud
  server and then allows modification and retrival of files.
  """
  def __init__(self, url):
    """
    The URL in http or https format to the owncloud server, the remote.php/webdav is required
    """
    self.log = logging.getLogger("root.ownClient")
    self.url = url
    self.base = "/".join(url[8:].split("/")[1:])
    self.http = httplib2.Http(disable_ssl_certificate_validation=True)
    self.good = False
    self.DIRS = dict()
    self.FILES = dict()

  def set_auth(self, username, password):
    """
    Sets the username and password to use for the Client
    """
    self.http.add_credentials(username, password)

  def updateTree(self, path="/"):
    """
    Updates the Local dictionary of directories and files
    """
    self.log.debug("updating Local DataTrees %s"%path)
    DATA = "<?xml version='1.0' encoding='UTF-8' ?><propfind xmlns:D='DAV:'><prop><D:allprop/></prop></propfind>"
    r, c = self.http.request(self.url+"/"+path, 'PROPFIND', body=DATA)
    if r['status'] != '207':
      self.good = False
      return
    self.good = True
    obj = ET.XML(c)
    if obj.tag != "{DAV:}multistatus":
      return
    for i in obj.getchildren():
      if i.tag == "{DAV:}response":
        newEntry = dict()
        for d in i.getchildren():
          if d.tag == "{DAV:}href":
            name = urllib.unquote(d.text[len(self.base)+1:])
            newEntry['name'] = name
          elif d.tag == "{DAV:}propstat":
            X = d.find("{DAV:}prop")
            if X != None:
              ID = X.find("{http://owncloud.org/ns}id")
              ETAG = X.find("{DAV:}etag")
              lastMod = X.find("{DAV:}getlastmodified")
              length = X.find("{DAV:}getcontentlength")
#              if ID != None:
#                newEntry['id'] = ID.text
#              if ETAG != None:
#                newEntry['etag'] = ETAG.text
              if lastMod != None:
                try:
                  T = time.strptime(lastMod.text,"%a, %d %b %Y %H:%M:%S GMT")
                  newEntry['lastMod'] = int((time.mktime(T)-time.altzone)*1000)
                except Exception as e:
                  self.log.error("Problem converting time stamp: %s, %s"%(newEntry['name'], lastMod.text))
                  newEntry['lastMod'] = 0
              if length != None:
                newEntry['size'] = length.text
                newEntry['type'] = "FILE"
                self.FILES[newEntry['name']] = newEntry
              else:
                newEntry['type'] = "DIR"
                self.DIRS[newEntry['name']] = newEntry
        if newEntry['type'] == "DIR" and newEntry['name']!=path:
          self.updateTree(newEntry['name'])
    if "/" in self.FILES:
      del(self.FILES["/"])
    if "/" in self.DIRS:
      del(self.DIRS["/"])

  def updateModTime(self, path, ftime):
    """
    This Call updates the modified time of a file in owncloud.
    """
    self.log.debug("Updating Modified time of %s to %d"%(path, ftime))
    DATA = "<?xml version='1.0' encoding='UTF-8' ?><D:propertyupdate xmlns:D='DAV:'><D:set><D:prop><D:lastmodified>%d</D:lastmodified></D:prop></D:set></D:propertyupdate>"%(ftime)
    r, c = self.http.request(self.url+"/"+urllib.quote(path), 'PROPPATCH', body=DATA)

  def mkdir(self, path):
    """
    mkdir creates a dirctory on owncloud, it will create the full path even if parent directories do not exist
    """
    self.log.debug("Creating Path %s"%(path))
    r, c = self.http.request(self.url+"/"+urllib.quote(path), "MKCOL")
    

  def delete(self, path):
    """
    delete deletes any path/file on the owncloud server, and will do so recursivly.
    """
    self.log.debug("Deleting Path %s"%(path))
    r, c = self.http.request(self.url+"/"+urllib.quote(path), "DELETE")

  def getFile(self, path):
    """
    getFile retireves the contents of the give file
    """
    self.log.debug("Getting File contents: %s"%(path))
    r, c = self.http.request(self.url+"/"+urllib.quote(path))
    if r['status'] == "200":
      return c

  def addFile(self, newFile, path):
    """
    This adds the given file to the owncloud server.  newFile is a string path to a local file and 
    that file name will be used as its name.
    """
    self.log.debug("Adding New File: %s/%s"%(path, os.path.basename(newFile)))
    fp = open(newFile, "r")
    if path not in self.DIRS:
      self.mkdir(path)
    r, c = self.http.request(self.url+"/%s/%s"%(urllib.quote(path), urllib.quote(os.path.basename(newFile))), "PUT", body=fp.read())

  def getLocalDIRS(self, path):
    DIRS = dict()
    if os.path.isdir(path):
      for root, dirs, files in os.walk(path):
        for d in dirs:
          R = root+"/"+d
          X = fixPath("/"+R[len(path):]+"/")
          DIRS[X] = dict()
          DIRS[X]['type']="DIR"
          DIRS[X]['lastMod']=int(os.path.getmtime(R))*1000
    return DIRS

  def getLocalFILES(self, path):
    FILES = dict()
    if os.path.isdir(path):
      for root, dirs, files in os.walk(path):
        for f in files:
          R = root+"/"+f
          X = R[len(path):]
          FILES[X] = dict()
          FILES[X]['type']="FILE"
          FILES[X]['lastMod']=int(os.path.getmtime(R))*1000
    return FILES


  def syncBOTH(self, path, base="/"):
    self.updateTree(path=base)
    base = fixPath(base)
    if os.path.isdir(path):
      FILES = self.getLocalFILES(path)
      DIRS = self.getLocalDIRS(path)

      for d in DIRS:
        newpath = fixPath("%s/%s"%(base,d))
        if newpath not in self.DIRS:
          self.mkdir(newpath)

      for d in self.DIRS:
        if d[:len(base)] == base:
          newpath = fixPath(d[len(base):])
          if newpath not in DIRS:
            try:
              os.makedirs("%s/%s"%(path,newpath))
            except Exception as e:
              pass
      
      for f in FILES:
        newfile = fixPath("%s/%s"%(base,f))
        if newfile in self.FILES:
          if FILES[f]['lastMod'] > self.FILES[newfile]['lastMod']:
            self.log.info("Uploading Updated File %s"%(f))
            self.delete(newfile)
            self.addFile("%s/%s"%(path,f), fixPath(os.path.dirname(newfile)+"/"))
            self.updateModTime(newfile, FILES[f]['lastMod']/1000)
        else:
          self.log.info("Uploading New File %s"%(f))
          self.addFile("%s/%s"%(path,f), fixPath(os.path.dirname(newfile)+"/"))
          self.updateModTime(newfile, FILES[f]['lastMod']/1000)
      self.updateTree(path=base)

      for f in self.FILES:
        if f[:len(base)] == base:
          newfile = fixPath(f[len(base):])
          if newfile in FILES:
            if self.FILES[f]['lastMod'] > FILES[newfile]['lastMod']:
              self.log.info("Downloading Updated file %s"%(f))
              open("%s/%s"%(path,newfile), "w").write(self.getFile(f))
              os.utime("%s/%s"%(path,newfile), (self.FILES[f]['lastMod']/1000, self.FILES[f]['lastMod']/1000))
          else:
            self.log.info("Downloading new file %s"%(f))
            open("%s/%s"%(path,newfile), "w").write(self.getFile(f))
            os.utime("%s/%s"%(path,newfile), (self.FILES[f]['lastMod']/1000, self.FILES[f]['lastMod']/1000))
      self.updateTree(path=base)

  def syncTO(self, path, base="/"):
    self.updateTree(path=base)
    base = fixPath(base)
    if os.path.isdir(path):
      FILES = self.getLocalFILES(path)
      DIRS = self.getLocalDIRS(path)
      for d in DIRS:
        newpath = fixPath("%s/%s"%(base,d))
        if newpath not in self.DIRS:
          self.mkdir(newpath)

      for d in self.DIRS:
        if d[:len(base)] == base:
          newpath = fixPath(d[len(base):])
          if newpath not in DIRS and newpath != "/" and newpath != "":
            self.delete(d)
      self.updateTree(path=base)

      for f in FILES:
        newfile = fixPath("%s/%s"%(base,f))
        if newfile in self.FILES:
          if FILES[f]['lastMod'] != self.FILES[newfile]['lastMod']:
            self.log.info("Uploading Updated File %s"%(f))
            self.delete(newfile)
            self.addFile("%s/%s"%(path,f), fixPath(os.path.dirname(newfile)+"/"))
            self.updateModTime(newfile, FILES[f]['lastMod']/1000)
        else:
          self.log.info("Uploading New File %s"%(f))
          self.addFile("%s/%s"%(path,f), fixPath(os.path.dirname(newfile)+"/"))
          self.updateModTime(newfile, FILES[f]['lastMod']/1000)

      
      for f in self.FILES:
        if f[:len(base)] == base:
          newfile = fixPath(f[len(base):])
          if newfile not in FILES:
            self.delete(f)
      self.updateTree(path=base)

  def syncFROM(self, path, base="/"):
    self.log.info("Syncing from host to %s from %s"%(path, base))
    self.updateTree(path=base)
    base = fixPath(base)
    if os.path.isdir(path):
      DIRS = self.getLocalDIRS(path)

      for d in DIRS:
        newpath = fixPath("%s/%s"%(base,d))
        if newpath not in self.DIRS and newpath != "/":
          try:
            self.log.debug("Removing local directory %s/%s"%(path,d))
            shutil.rmtree("%s/%s"%(path,d))
          except:
            pass

      for d in self.DIRS:
        if d[:len(base)] == base:
          newpath = fixPath(d[len(base):])
          if newpath not in DIRS:
            try:
              self.log.debug("Creating local directory %s/%s"%(path,newpath))
              os.makedirs("%s/%s"%(path,newpath))
            except Exception as e:
              pass

          
      FILES = self.getLocalFILES(path)

      for f in self.FILES:
        if f[:len(base)] == base:
          newfile = fixPath(f[len(base):])
          if newfile not in FILES:
            self.log.info("Creating New file %s"%(f))
            open("%s/%s"%(path,newfile), "w").write(self.getFile(f))
            os.utime("%s/%s"%(path,newfile), (self.FILES[f]['lastMod']/1000, self.FILES[f]['lastMod']/1000))
          elif FILES[newfile]['lastMod'] != self.FILES[f]['lastMod']:
            self.log.info("Downloading Updated file %s"%(f))
            open("%s/%s"%(path,newfile), "w").write(self.getFile(f))
            os.utime("%s/%s"%(path,newfile), (self.FILES[f]['lastMod']/1000, self.FILES[f]['lastMod']/1000))

      for f in FILES:
        newfile = fixPath("%s/%s"%(base,f))
        if newfile not in self.FILES:
          self.log.info("Removing Local File: %s"%(f))
          os.remove("%s/%s"%(path,f))
      self.updateTree(path=base)



def fixPath(path):
  """
  This class kind of sucks is makes sure that paths have the correct number of /'s in them.
  I could not get any of the os.path fuctions to do this reliably, not sure why.
  """
  if path[0] != "/":
    path = "/"+path
  while path.find("//") != -1:
    path = path.replace("//", "/")
  return path


def getOwn(url):
  """
  Simple class to verify a url is an ownCloud instance
  """
  http = httplib2.Http(disable_ssl_certificate_validation=True)
  if url.find("remote.php")==-1 and url[-1:] == "/":
    url = url+"remote.php/webdav"
  elif url.find("remote.php") != 1 and url[-1:] != "/":
    if url.find("webdav") == -1:
      url = url+"/webdav"
  elif url.find("remote.php")==-1 and url[-1:] != "/":
    url = url+"/remote.php/webdav"
  else:
    return None
  r, c = http.request(url)
  if r['status'] == '401' and r['www-authenticate'].find("ownCloud") != -1:
    return url
  return None
