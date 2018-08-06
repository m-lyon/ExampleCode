#!/usr/bin/env python
import os
import Dashboard
import datetime
import fnmatch
import subprocess
import argparse
import multiprocessing
import time

class DashboardProcessor(object):
    
    def __init__(self,verbose,processType):
        '''Processing specific text files'''
        self.verbose = verbose
        self.processType = processType
        self.dashboardDir = '/Volume/Dashboard'
        self.dataDir = 'Volume/Data'
        self.processDir = '%s/PROCESSING/%s' % (self.dashboardDir, self.processType)
        self.processingLog = '%s/Processing.log' % self.processDir
        self.currentlyProcessingFP = '%s/CURRENTLY_PROCESSING.txt' % self.processDir
        self.exceptionsFP = '%s/EXCEPTIONS.txt' % self.processDir
        self.failedFP = '%s/FAILED.txt' % self.processDir
        self.processedFP = '%s/PROCESSED.txt' % self.processDir
        self.toProcessFP = '%s/TO_PROCESS.txt' % self.processDir
        self.exceptionFileList = [ self.currentlyProcessingFP, self.exceptionsFP, self.failedFP, self.processedFP ]
        self.projectReportFile = '%s/Project_Reports.txt' % self.dashboardDir
        self.projectsOutputDir = '%s/Project_outputs' % self.dashboardDir
        
        '''Initialising lists & dicts'''
        self.projectReportFile = Dashboard.CreateProjectDict(self.projectReportFile).keys()
        if self.processType == 'MRtrix':
            self.MRtrixProcessFile = '%s/Projects.txt' % self.processDir
            self.mrtrixDict = Dashboard.CreateProjectDict(self.MRtrixProcessFile)
        self.exceptionIDList = []
        self.IDtoProcess = None
        self.IDList = []
        self.IDProcessingType = None
    
    def CreateExceptions(self):
        for excFilePath in self.exceptionFileList:
            if os.path.isfile(excFilePath):
                try:
                    with open(excFilePath,'r') as fn:
                        for line in fn:
                            self.exceptionIDList.append(line.rstrip())
                except:
                    raise ValueError('Failed to read %s' % excFilePath)
        
    def CreateMRtrixProcessingList(self):
        processingIDs = {}
        for project in self.projectReportFile:
            if project in self.mrtrixDict:
                projDir = '%s/%s' % (self.projectsOutputDir,project)
                for root, dirs, files in os.walk(projDir):
                    for fn in files:
                        if fnmatch.fnmatch(fn, '*_mrtrix_unprocessed.txt'):
                            with open('%s/%s' % (projDir,fn)) as fp:
                                for line in fp:
                                    if not line.rstrip() in self.exceptionIDList:
                                        processingIDs[line.rstrip()] = self.mrtrixDict[project]
        if os.path.isfile(self.toProcessFP):
            os.remove(self.toProcessFP)
            
        outputFile = open(self.toProcessFP,'w')
        for ID in processingIDs:
            outputFile.write('%s=%s\n' %(ID,processingIDs[ID]))
        outputFile.close()
        
    def CreateFreesurferProcessingList(self):
        processingIDs = []
        for project in self.projectReportFile:
            projDir = '%s/%s' % (self.projectsOutputDir,project)
            for root, dirs, files in os.walk(projDir):
                for fn in files:
                    if fnmatch.fnmatch(fn, '*_fs_unprocessed.txt'):
                        with open('%s/%s' % (projDir,fn)) as fp:
                            for line in fp:
                                if not line.rstrip() in self.exceptionIDList:
                                    processingIDs.append(line.rstrip())
        outputFile = open(self.toProcessFP,'w')
        for ID in processingIDs:
            outputFile.write('%s\n' %ID)
        outputFile.close()
        
    def MoveIDtoProcessingFile(self):
        #Open Processing list file
        with open(self.toProcessFP, 'r') as fin:
            try:
                data = fin.read().splitlines(True)
                #Read the first line
                if self.processType == 'MRtrix':
                    self.IDtoProcess, self.IDProcessingType = data[0].rstrip().split('=')
                elif self.processType == 'Freesurfer':
                    self.IDtoProcess = data[0].rstrip()
                    self.IDList.append(self.IDtoProcess)
            except IndexError:
                raise ValueError('No IDs left to process')
            if self.verbose:
                print(self.IDtoProcess)
                print(self.IDProcessingType)
        #Rewrite file without 1st line
        with open(self.toProcessFP, 'w') as fout:
            fout.writelines(data[1:])
        #Write to processing file
        with open(self.currentlyProcessingFP,'a') as fp:
            fp.write('%s\n' % self.IDtoProcess)
            
    def RemoveFromProcessingFile(self):
            fp = open(self.currentlyProcessingFP,'r')
            lines = fp.readlines()
            fp.close
            fp = open(self.currentlyProcessingFP,'w')
            for line in lines:
                if self.processType == 'MRtrix':
                    if line != self.IDtoProcess + '\n':
                        fp.write(line)
                elif self.processType == 'Freesurfer':
                    if line.rstrip() not in self.IDList:
                        fp.write(line)
            fp.close()
        
    def AppendProcessedFile(self):
        if self.processType == 'MRtrix':
            with open(self.processedFP,'a') as fp:
                fp.write('%s\n'%self.IDtoProcess)
        elif self.processType == 'Freesurfer':
            with open(self.processedFP,'a') as fp:
                for ID in self.IDList:
                    fp.write('%s\n'%ID)
                
    def WriteToErrorFile(self,error):
        if self.verbose:
            print(error)
        if self.processType == 'MRtrix':    
            with open(self.failedFP,'a') as fp:
                fp.write('%s\n' % self.IDtoProcess)
            with open(self.processingLog,'a') as fp:
                fp.write('TIME: %s\nSUBJECT: %s\nPROCESSING TYPE: %s\n%s\n\n' %(datetime.datetime.now().replace(microsecond=0),self.IDtoProcess,self.IDProcessingType,str(error)))
        elif self.processType == 'Freesurfer':
            #this is incomplete because handling parallel errors is hard. might want to revisit.
            with open(self.processingLog,'a') as fp:
                fp.write('TIME: %s\nSUBJECT: %s\nPROCESSING TYPE: %s\n%s\n\n' %(datetime.datetime.now().replace(microsecond=0),self.IDList,self.IDProcessingType,str(error)))
    
    def RunMRtrixForID(self):
        self.MoveIDtoProcessingFile()
        if self.verbose:
            print 'PROCESSING MRTRIX FOR %s' % self.IDtoProcess
        #Begin processing
        runL = ['processData.py','-y','-s',self.IDtoProcess,self.IDProcessingType]
        try:  
            subprocess.check_output(runL)
        except subprocess.CalledProcessError as e:
            self.WriteToErrorFile(e)
        else:
            self.AppendProcessedFile()
        self.RemoveFromProcessingFile()

    def RunFreesurfer(self):
        '''Runs freesurfer in parallel'''
        #Core checking
        nCPU = multiprocessing.cpu_count()
        cpuDict = {
            12: 5,
            10: 4,
            8: 3,
            6: 2
            }
        if nCPU in cpuDict:
            nJ = cpuDict[nCPU]
        else:
            raise OSError('Invalid number of cores detected for parallelisation')
        #Move IDs to PROCESSING.txt
        for n in range(0, nJ):
            self.MoveIDtoProcessingFile()
        runL = ['parallel','-j',str(nJ),'processData.py','-y','-rF','-s',':::']
        for ID in self.IDList:
            runL.append(ID)
        try: 
            subprocess.check_output(runL)
        except subprocess.CalledProcessError as e:
                self.WriteToErrorFile(e)
        self.AppendProcessedFile()
        self.RemoveFromProcessingFile()
    
if __name__ == '__main__':
    
    #------------------------
    # Argument Parsing
    # -----------------------
    ap = argparse.ArgumentParser(description='Dashboard Processing')
    
    sp = ap.add_argument_group('Script Parameters')
    sp.add_argument('-U',dest='UPDATE',help='Updates the TO_PROCESS.txt list',action='store_true')
    sp.add_argument('-mrtrix',dest='MRtrix',help='Begins processing MRtrix for first in list',action='store_true')
    sp.add_argument('-freesurfer',dest='FREESURFER',help='Begins processing freesurfer for first in list',action='store_true')
    
    op = ap.add_argument_group('Optional Parameters')
    op.add_argument('-v',dest='verbose',help='Verbose printout',action='store_true',default=False)
    
    args = ap.parse_args()        
    # Initialise
    if args.UPDATE:
        ## MRtrix
        DBProcessor = DashboardProcessor(args.verbose,'MRtrix')
        DBProcessor.CreateExceptions()
        DBProcessor.CreateMRtrixProcessingList()
        ## Freesurfer
        DBProcessor = DashboardProcessor(args.verbose,'Freesurfer')
        DBProcessor.CreateExceptions()
        DBProcessor.CreateFreesurferProcessingList()
        
    if args.MRtrix:
        DBProcessor = DashboardProcessor(args.verbose,'MRtrix')
        DBProcessor.RunMRtrixForID()
    if args.FREESURFER:
        DBProcessor = DashboardProcessor(args.verbose,'Freesurfer')
        DBProcessor.RunFreesurfer()
        