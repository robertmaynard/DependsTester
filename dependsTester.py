#!/usr/bin/env python

#  This software is distributed WITHOUT ANY WARRANTY; without even
#  the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
#  PURPOSE.  See the above copyright notice for more information.

import fileinput, glob, string, sys, os, re, argparse, tempfile

# -c console mode
# -pa:1 turn on ALL profiling options
# -pb automatically start profiling after depends opens

#we will add on the -oc: argument to specify the path to the output file
dependsArgs = "-c -pa:1 -pb"
dependsOutputArg = "-oc:"
dependsFileHandle = None

def generateTempFile():
  (handle,filePath)=tempfile.mkstemp(suffix='.csv',prefix='dependsTesterResult',text=True)
  dependsFileHandle = handle
  return filePath

#builds the string to be used to launch dependency walker
def buildDependsCommandString(dependsPath,appPath,appArgs):
  #no space between oc: and path
  outputArg = ''.join([dependsOutputArg,generateTempFile()])
  #flatten the list into a string
  flattenedAppArgs = ' '.join(appArgs)
  #generate the final string needed to run dependency walker
  finalString = ' '.join([dependsPath,dependsArgs,outputArg,appPath,flattenedAppArgs])
  return finalString

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

#makes sure two paths aren't the same
def areSame(path1,path2):
  if(os.path.samefile(path1,path2)):
    raise IOError


#launches dependency walker
def launchDepends(depends,application,appArgs):
  print buildDependsCommandString(depends,application,appArgs)

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
  args = parser.parse_args()

  #make sure args is an empty list instead of none
  if (args.appArgs is None):
    args.appArgs = []

  try:
    isExecutable(args.depends)
    isExecutable(args.application)
    areSame(args.depends,args.application)
  except IOError:
    if(dependsFileHandle):
      dependsFileHandle.close()
    print("Unable to launch depends because of invalid paths")
  else:
    launchDepends(args.depends,args.application,args.appArgs)

if __name__ == '__main__':
  main()
