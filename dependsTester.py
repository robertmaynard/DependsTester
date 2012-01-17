#!/usr/bin/env python

#  This software is distributed WITHOUT ANY WARRANTY; without even
#  the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
#  PURPOSE.  See the above copyright notice for more information.

import fileinput, glob, string, sys, os, re, argparse
import subprocess, time, csv, operator

# -c console mode
# -f full paths
# -pa:1 turn on ALL profiling options
# -pb automatically start profiling after depends opens

#we will add on the -oc: argument to specify the path to the output file
dependsArgs = ["-c", "-f1","-pa1","-pb"]
dependsOutputArg = "-oc:"

#global variables that we need
dependsFileName = None
applicationBaseDir = None

#known modules not to test as they don't cause harm
knownFalsePositives = ["IESHIMS.DLL","MMTIMER.DLL","WINTAB32.DLL","NVOGLV64.DLL","IEFRAME.DLL","GDI32.DLL","DWMAPI.DLL"]

#generator that skips false positive modules
def skip_false_positives(reader):
  for row in reader:
    valid = True
    mod = row["Module"]
    for fp in knownFalsePositives:
      if fp in mod:
        valid = False
        break
    if(valid):
      yield row


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

#determine the base directory of the application we are testing
#this is needed to verify module loading
def setupApplicationGlobals(appPath):
  global applicationBaseDir
  #we use lower to make sure captilization doesn't report
  #incorrect paths because of that
  applicationBaseDir = os.path.dirname(appPath).lower()
  print "applicationBaseDir: ", applicationBaseDir

def verifyStatus(row,statusErrors,statusWarnings):
  status = row["Status"]
  #Status with a  ? means missing module
  #Status with a E means error
  #Status with a D means delayed load
  if('DE' in status):
    #E with a D is grounds for a warning
    statusWarnings.append(row["Module"])
  elif ('?' in status or 'E' in status):
    #E without a D is ground for error
    statusErrors.append(row["Module"])

def verifyCPU(row,cpuTypes):
  #CPU entry has to be the same across the board
  #we are going to count the number of each cpu type occurs
  #if we find more than 1 we will report it
  cpu = row["CPU"]
  if cpu in cpuTypes:
    cpuTypes[cpu]+=1
  else:
    cpuTypes["xUnkown"]=1

def verifyModule(row,moduleErrors):
  #Module if not in c:\windows\ something
  #or in binarydir it is an error
  modPath = row["Module"].lower() #remove any captilization to reduce false positives
  sysPath = "c:\\windows\\"
  if(modPath.find(sysPath) == 0):
    #system path, okay is valid
    return
  elif(modPath.find(applicationBaseDir) == 0):
    #module is in the binary package that is valid
    return
  moduleErrors.append(row["Module"])


#parses the temp file with the results of the run
def parseResults():
  rawFile = open(dependsFileName)
  reader = csv.DictReader(rawFile)

  #keep track of all the different type of cpu's we see. we will
  #report back all the least popular types
  CPUTypes = dict(x64=0,x32=0,xUnkown=0)

  #contain the lines that have issues
  StatusErrors = []
  StatusWarnings = []
  ModuleLoadErrors = []
  numModules = 0
  for row in skip_false_positives(reader):
    #parse each line skip false positives
    verifyStatus(row,StatusErrors,StatusWarnings)
    verifyCPU(row,CPUTypes)
    verifyModule(row,ModuleLoadErrors)
    numModules+=1

  rawFile.close()

  validResults = True
  if(len(StatusErrors) > 0):
    validResults = False
    print(" ")
    print("Modules that failed to load:")
    for entry in StatusErrors:
      print entry

  if(len(StatusWarnings) > 0):
    print(" ")
    print("Status Warnings (might no load at a later time):")
    for entry in StatusWarnings:
      print entry

  if(len(ModuleLoadErrors) > 0):
    validResults = False
    print(" ")
    print("Modules that have incorrect path:")
    for entry in ModuleLoadErrors:
      print entry

  #remove highest counted cpu type
  #sort values
  sorted_cputypes = sorted(CPUTypes.iteritems(), key=operator.itemgetter(1))
  properCPU = sorted_cputypes[-1]
  if(numModules != properCPU[1]):
    #number of modules in the largest cpu type doesn't equal total number of modules
    #we tested
    print(" ")
    print("We have modules that have the incorrect CPU Type:")
    rawFile = open(dependsFileName)
    reader = csv.DictReader(rawFile)
    for row in skip_false_positives(reader):
      if row["CPU"] != properCPU[0]:
         print row["Module"]
    rawFile.close()

  print(" ")
  if(not validResults):
    print("!" * 80)
    print("!" * 80)
    print(" Program Failed Dependency Check ")
    print("!" * 80)
    print("!" * 80)
  else:
    print("#" * 80)
    print("#" * 80)
    print(" Program Valid ")
    print("#" * 80)
    print("#" * 80)
  print(" ")

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
      setupApplicationGlobals(args.application)
      parseResults()
  finally:
    removeTempFile()

if __name__ == '__main__':
  main()
