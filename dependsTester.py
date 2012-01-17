#!/usr/bin/env python

#  This software is distributed WITHOUT ANY WARRANTY; without even
#  the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
#  PURPOSE.  See the above copyright notice for more information.

import fileinput, glob, string, sys, os, re, argparse, tempfile, subprocess 

# -c console mode
# -f full paths
# -pa:1 turn on ALL profiling options
# -pb automatically start profiling after depends opens

#we will add on the -oc: argument to specify the path to the output file
dependsArgs = ["-c", "-f1","-pa1","-pb"]
dependsOutputArg = "-oc"
dependsFileHandle = None

#makes the path a window path if it isn't already
def makeWindowsPath(path):
    return os.path.abspath(path)

def generateTempFile():
  (handle,filePath)=tempfile.mkstemp(suffix='.csv',prefix='dependsTesterResult',text=True)
  dependsFileHandle = handle
  filePath = makeWindowsPath(filePath)
  return filePath

#builds the string to be used to launch dependency walker
def buildDependsCommandString(dependsPath,appPath,appArgs):
  #no space between oc: and path
  tempFile = '"'+generateTempFile()+'"'
  outputArg = ' '.join([dependsOutputArg,tempFile]) 
  dependsArgs.append(outputArg)
  dependsArgs.append(appPath)  
  #flatten the list into a string
  if(appArgs):
    flattenedAppArgs = ' '.join(appArgs)
    dependsArgs.append(flattenedAppArgs)
  
  flatArgs = ' '.join(dependsArgs)
  return dependsPath+" "+flatArgs

#verfies that a file exists and is an executable
def isExecutable(execPath):
  if(not os.path.exists(execPath)):
    raise IOError
  if(not os.path.isfile(execPath)):
    raise IOError
  (root,ext) = os.path.splitext(execPath)
  if(ext.lower() != ".exe"):
    raise IOError
  return True

#launches dependency walker
def launchDepends(depends,application,appArgs):
  command = buildDependsCommandString(depends,application,appArgs)
  print "command is", command
  result = subprocess.call(command,shell=True)
  return result

#adds the list of paths in envpath to the system path variable
#before we launch dependency walker
def addPaths(envpath):
  p = ';'.join(envpath)
  os.environ['PATH']=os.environ['PATH']+';'+p

def main():
  #arguments we need. Path to Depends
  #path to application, arguments for application
  parser = argparse.ArgumentParser(description='profile an application with dependency walker')
  parser.add_argument('-d', '--depends',
                     required=True,
                     help='path to dependency walker')
  parser.add_argument('-a', '--application',
                      required=True,
                      help='path to application to test')
  parser.add_argument('-g','--applicationArguments',
                      dest='appArgs',
                      nargs='+',
                      help='stores all the application arguments')
  parser.add_argument('-p','--envpath',
                      nargs='+',
                      help='add paths to the system path')
  args = parser.parse_args()

  args.depends = makeWindowsPath(args.depends)
  args.application = makeWindowsPath(args.application)
  try:
    isExecutable(args.depends)
    isExecutable(args.application)
  except IOError:
    if(dependsFileHandle):
      dependsFileHandle.close()
    print("Unable to launch depends because of invalid executable paths")
  else:
    addPaths(args.envpath)
    launchDepends(args.depends,args.application,args.appArgs)

if __name__ == '__main__':
  main()
