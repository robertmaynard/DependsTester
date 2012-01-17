#!/usr/bin/env python

#  This software is distributed WITHOUT ANY WARRANTY; without even
#  the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
#  PURPOSE.  See the above copyright notice for more information.

import fileinput, glob, string, sys, os, re, argparse, subprocess, time

# -c console mode
# -f full paths
# -pa:1 turn on ALL profiling options
# -pb automatically start profiling after depends opens

#we will add on the -oc: argument to specify the path to the output file
dependsArgs = ["-c", "-f1","-pa1","-pb"]
dependsOutputArg = "-oc:"
dependsFileName = None

#makes the path a window path if it isn't already
def makeWindowsPath(path):
    return os.path.abspath(path)

def generateTempFileName():
  fileName = "dependsTesterResult" + str(time.time()) + ".txt"
  fileDir = "."
  if('TEMP' in os.environ):
    fileDir = os.environ['TEMP']
  elif('TMP' in os.environ):
    fileDir = os.environ['TMP']

  print fileDir,fileName
  filePath = os.path.join(fileDir,fileName)
  filePath = makeWindowsPath(filePath)

  global dependsFileName  #yes I know that global vars are yucky
  dependsFileName = filePath
  return filePath

def removeTempFile():
  if(dependsFileName):
    os.remove(dependsFileName)

#builds the string to be used to launch dependency walker
def buildDependsCommandString(dependsPath,appPath,appArgs):
  #no space between oc: and path
  outputArg = ''.join([dependsOutputArg,generateTempFileName()])
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
  print "dependency command is: ", command
  result = subprocess.call(command,shell=True)
  return result

#adds the list of paths in envpath to the system path variable
#before we launch dependency walker
def addPaths(envpath):
  if(envpath):
    os.environ['PATH']=os.environ['PATH']+';'+envpath

#parses the temp file with the results of the run
def parseResults():
  print dependsFileName
  for line in open(dependsFileName):
    print line

def main():
  #arguments we need. Path to Depends
  #path to application, arguments for application
  parser = argparse.ArgumentParser(description='profile an application with dependency walker')
  parser.add_argument('--envpath',
                      help='add paths to the system path')
  parser.add_argument("depends", help='path to dependency walker')
  parser.add_argument(dest="application", help='path to application to test')
  args,appArgs = parser.parse_known_args()

  args.depends = makeWindowsPath(args.depends)
  args.application = makeWindowsPath(args.application)
  try:
    isExecutable(args.depends)
    isExecutable(args.application)
  except IOError:
    print("Unable to launch depends because of invalid executable paths")
  else:
    addPaths(args.envpath)
    result = launchDepends(args.depends,args.application,appArgs)
    if(result):
      parseResults()
  finally:
    removeTempFile()

if __name__ == '__main__':
  main()
