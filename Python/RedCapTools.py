#!/usr/bin/env python
'''
Various tools used for importing of data into redcap

Created on 16 May 2018

@author: Matt Lyon
'''
from redcap import Project
import redcap
import StringIO
import cStringIO
import pycurl
import pandas as pd
import csv
import numpy as np

def ImportCSV(csvFile):
    '''
    Imports a given csv file to a pandas dataframe, with values turned into type=string
    '''
    try:
        data = pd.read_csv(csvFile, delimiter=',',dtype=str)
    except:
        print('[ERROR]: importing csv')
        exit()
    return data

def ExportRedcapData(api_url,api_key,ids,fields,indexname):
    '''
    Exports redcap data (as type string) into pandas dataframe
    '''
    project = Project(api_url,api_key)
    data = project.export_records(records=ids, fields=fields, format='df', df_kwargs={'dtype': str})
    data.set_index(indexname, inplace=True)
    return data

def ExportRedcapReport(api_url,api_key,report_id,indexname=False):
    '''
    Exports contents of a redcap report into a dataframe
    '''
    try:
        buf = cStringIO.StringIO()
        data = {
                'token': api_key,
                'content': 'report',
                'format': 'csv',
                'report_id': report_id,
                'rawOrLabel': 'raw',
                'rawOrLabelHeaders': 'raw',
                'exportCheckboxLabel': 'true',
                'returnFormat': 'csv'
                }
        ch = pycurl.Curl()
        ch.setopt(ch.URL, api_url)
        ch.setopt(ch.HTTPPOST, data.items())
        ch.setopt(ch.WRITEFUNCTION, buf.write)
        ch.perform()
        ch.close()
        csv = buf.getvalue()
        buf.close()
        csv_data = StringIO.StringIO(csv)
        data = pd.read_csv(csv_data, sep=",", dtype=str)
        if indexname:
            data.set_index(indexname, inplace=True)
    except:
        raise NameError('Failed to import redcap report')
    return data

def ModifyIndex(data,id_dict):
    '''
    Changes the index entries of a dataframe based on a given dictionary
    Dictionary must be in the form [key]: old_index -> [entry]: new_index
    '''
    idname = data.index.name
    id_list = data.index.tolist()
    for key in id_dict:
        idx = id_list.index(key)
        id_list[idx] = id_dict[key]
    data.index = id_listindexname
    data.index.name = idname
    return data

def MatchIDs(prev_import_file,data_source,data_source_ID,data_input,data_input_ID):
    '''
    -Creates list from previously imported IDs to exclude from import
    -Iterates over data_source (redcap report generated df), finds matching id in data_input (df you wish to find matches for) (if not in previously imported list)
    -Returns dictionary => {'data_input_ID':'data_source_ID'}
    '''
    text_file = open(prev_import_file, 'r')
    lines = text_file.read().split('\n')
    id_match = {}
    for index_s, row_s in data_source.iterrows():
        id_to_match = row_s[data_source_ID]
        if not index_s in lines:
            for index_i, row_i in data_input.iterrows():
                if id_to_match == row_i[data_input_ID] and id_to_match:
                    id_match[index_i] = index_s
                    break               
    return id_match

def MatchColumns(prev_import_file,data_source,source_column1,source_column2,data_input,input_column1,input_column2):
    '''
    -Creates list from previously imported IDs to exclude from import
    -Requires data_source to have redcap_id as index
    -Iterates over data_source (redcap report generated df), finds matching column 1 & 2 in data_input (df you wish to find matches for) (if not in previously imported list)
    -Returns dictionary => {'data_input_index':'data_source_index'}
    '''
    text_file = open(prev_import_file, 'r')
    lines = text_file.read().split('\n')
    id_match = {}
    for index_s, row_s in data_source.iterrows():
        if not index_s in lines:
            for index_i, row_i in data_input.iterrows():
                if row_s[source_column1] == row_i[input_column1] and row_s[source_column2] == row_i[input_column2]:
                    id_match[index_i] = index_s
                    break               
    return id_match

def ModifyFieldNames(data,index_name,field_dict):
    '''
    Changes the fieldnames of a pandas dataframe given a fieldnames dictionary and an index name
    field name dictionary in the form of [key]: old_fieldname -> [entry]: new_fieldname
    '''
    data.index.name = index_name
    data.rename(columns=field_dict, inplace=True)
    return data

def CsvToDict(csvfile):
    '''
    Creates dictionary from csv in form of 'entry_1=entry2', newline separated
    dictionary key = entry_1
    dictionary entry = entry_2
    '''
    matchedDict = {}
    with open(csvfile, 'r') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            e_1, e_2 = row[0].split("=")
            matchedDict[e_1] = e_2
        return matchedDict

def ImportRecords(api_url,api_key,data,imported_textfile):
    '''
    Imports records as type string to redcap using a redcap Project object and pandas dataframe as argument
    '''
    project = Project(api_url,api_key)
    print('Importing...')
    try:
        imported = project.import_records(data, format='csv', overwrite='normal',return_format='csv', return_content='ids')
    except redcap.RedcapError:
            print("oops this hasn't worked")
    if imported.split("\n",1)[0] == 'id':
        print('Imported IDs:')
        print(imported.split("\n",1)[1])
        text_file = open(imported_textfile, 'a')
        text_file.write(imported.split("\n",1)[1])
        text_file.write('\n')
        text_file.close()
        print 'records imported stored in %s' % imported_textfile
    else:
        print(imported)
    
def DFToIDs(data,id_name):
    '''
    Outputs list of STIL IDs contained within a given dataframe
    '''
    IDs = data[id_name].tolist()
    for ID in IDs:
        if not isinstance(ID,str):
            IDs.remove(ID)
    return IDs


