import sys
import hashlib
import os, os.path
import commands

class ServerCheck:


  def __init__(self, xfile, indivo_server_location):
    self.xfile = xfile
    self.server = 'sudo /etc/init.d/apache2 '
    self.server_commands = {'restart' : 'restart', 'status' : 'status'}
    self.indivo_server_location = indivo_server_location + '/'

  def check(self):
    if os.path.exists(self.indivo_server_location):
      m = hashlib.md5()
      m.update(self.hash_dir(self.indivo_server_location))
      saved_digest = self.read_xfile()
      if self.write_xfile(m.hexdigest()) and \
        m.hexdigest() != saved_digest:
        if self.exec_server_cmd('status')[0] == 0:
          if self.exec_server_cmd('restart')[0] == 0:
            return True
      return False
    else:
      return False

  def exec_server_cmd(self, cmd):
    return commands.getstatusoutput(self.server + self.server_commands[cmd])

  def hash_dir(self, start_dir):
    hash_list = []
    dirs = [start_dir]
    while len(dirs) > 0:
      dir = dirs.pop()
      for n in os.listdir(dir):
        fpath = os.path.join(dir, n)
        if os.path.isfile(fpath):
          hash_value = self.hash_file(fpath)
          if hash_value:
            hash_list.append(hash_value)
        elif os.path.isdir(fpath):
          dirs.append(fpath)
    return ''.join(hash_list)

  def hash_file(self, fpath):
    m = hashlib.md5()
    if os.path.isfile(fpath):
      f = open(fpath, 'r')
      lines = f.readlines()
      for line in lines:
        m.update(line)
      return m.hexdigest()
    else:
      return False

  def read_xfile(self):
    if os.path.isfile(self.xfile):
      f = open(self.xfile, 'r')
      saved_digest = f.readlines()
      if len(saved_digest) > 0:
        return saved_digest[0]
      else:
        return False
    else:
      return False

  def write_xfile(self, content):
    try:
      f = open(self.xfile, 'w+')
      f.write(content)
      #f.flush()
      f.close()
      return True
    except:
      return False

if __name__ == "__main__":
  xfile = '/tmp/x.tmp'
  sc = ServerCheck(xfile)
  sc.check()
