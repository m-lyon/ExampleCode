#!/usr/bin/env python
'''
Created on 20/02/2019

This class handles generalized low(ish) level methods to interact with the cluster

@author: Matt Lyon
'''
import random
import string
import commands
import subprocess
import getpass
import os

# =========== CONSTANTS =================================================
CLUSTER_ADDRESS = 'user@address.of.cluster'
DEFAULT_JOB_DIR = '/home/cluster_user/jobs'
CLUSTER_ENV_SETUP = '/share/apps/Setup/envSetup_Cluster.sh'
DEFAULT_QUEUE_NAME = 'run.q'


class ClusterDB(object):
    
    def __init__(self, job_name=None, working_dir=DEFAULT_JOB_DIR):
        '''Cluster object, offers generalized methods to submit jobs on the Cluster
        :param job_name (string): custom name of job, leaving blank will give randomly
        assigned name
        :param working_dir (string): path to working directory on the Cluster head-node
        leave blank to assign default job directory
        '''
        if job_name:
            self.job_name = job_name
        else:
            self.job_name = ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(7))
        self.working_dir = working_dir    
        self.qsub_script_name = 'qsub_' + self.job_name + '.sh'
        self.tmp_path = os.path.join('/tmp', self.qsub_script_name)
        self.cluster_tmp_path = os.path.join(self.working_dir, self.qsub_script_name)
        self.user_address = '%s@%s' %(getpass.getuser(), commands.getoutput('hostname -I').rstrip())
        
    def buildRunScript(self, run_string, queue_name=DEFAULT_QUEUE_NAME):
        '''This method handles the qsub specific commands needed to submit a job
        Adds boilerplate code that counts time taken
        :param run_string (string): string containing actual run commands to be
        inserted in between boilerplate code
        :param queue_name (string): name of the queue to send job to. leave
        blank for default
        '''
        script_str = '#!/bin/bash\n'
        script_str += '\n'
        script_str += '#$ -S /bin/bash\n'
        script_str += '#$ -wd %s\n' %(self.working_dir)
        script_str += '#$ -V\n'
        script_str += '#$ -q %s\n' %(queue_name)
        script_str += '#$ -N %s\n' %(self.job_name)
        script_str += '\n'
        script_str += 'source %s\n' %(CLUSTER_ENV_SETUP)
        script_str += 'echo "This job was run on: $(hostname)"\n'
        script_str += 'start=$(date +%s)\n\n'
        script_str += run_string
        script_str += '\nend=$(date +%s)\n'
        script_str += 'runtime=$((end-start))\n'
        script_str += 'echo "Runtime: ${runtime} seconds"\n'
        with open(self.tmp_path, 'w') as fp:
            fp.write(script_str)
        os.chmod(self.tmp_path, 0755)
    
    def copyRunScriptToCluster(self):
        '''This copies tmp qsub script to Cluster'''
        run_list = ['scp',self.tmp_path,'%s:%s' %(CLUSTER_ADDRESS, self.cluster_tmp_path)]
        rc = subprocess.call(run_list)
        if rc == 0:
            os.unlink(self.tmp_path)
        
    def submitToQueue(self):
        '''This submits the job to the queue'''
        submit_command = "'source /etc/profile; qsub %s'" %(self.cluster_tmp_path)
        run_str = "ssh %s %s" %(CLUSTER_ADDRESS, submit_command)
        try:
            print 'Submitting Job to Cluster...'
            subprocess.check_output(run_str, shell=True, stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as e:
            raise RuntimeError("command '{}' return with error (code {}): {}".format(e.cmd, e.returncode, e.output))
        print 'Job name: %s' %(self.job_name)
        print 'Done'
        
    def createDirOnCluster(self, dir_path):
        '''Creates a directory on the Cluster via ssh command
        :param dir_path (string): directory to create
        Can create parent directories
        '''
        submit_command = "'mkdir -p %s'" %(dir_path)
        run_str = "ssh %s %s" %(CLUSTER_ADDRESS, submit_command)
        try:
            print 'Creating directory on Cluster...'
            subprocess.check_output(run_str, shell=True, stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as e:
            raise RuntimeError("command '{}' return with error (code {}): {}".format(e.cmd, e.returncode, e.output))
        print 'Done'

    