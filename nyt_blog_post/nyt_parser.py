## CITATIONS 

## Data provided by The New York Times
## Data provided by Twitter

# Required modules 
from time import sleep

import configparser 
import json 
import pandas as pd 
import numpy as np 
import requests 
import datetime
import os

# Set filepaths 



# import credentials 

parser = configparser.ConfigParser() 
parser.read('creds.cfg')



nyt_key = parser['KEYS']['NYT_KEY']
nyt_secret = parser['KEYS']['NYT_SECRET']

def clean_results(directory = out_dir + '/clean_outputs'): 
    """Concatenates csvs stored locally and removes duplicate records"""
    # get files 
    
    f_list = glob.glob(directory + '/*.csv')
    df_list = [pd.read_csv(f) for f in f_list]
    df_list = pd.concat(df_list)
    df_list = df_list.drop_duplicates(subset = 'uuid')
    df_list.to_csv(directory + f"""_clean_{today}.csv""")

    
# Classes 

class NytArchive():
    def __init__(self, year = 2020, month = 6): 
        
        self.key = nyt_key
                
    def get_stories(self, year = 2020, month = 6): 
        self.year = year
        self.month = month
        url = f"https://api.nytimes.com/svc/archive/v1/{self.year}/{self.month}.json?api-key={self.key}"
        print(url)
        res = requests.get(url).json() 
        out = []
        
        # features available: 
        
        for result in res['response']['docs']: 
            master = {}
            master['url'] = result['web_url']
            if ('print_section') in result.keys():
                master['print_section'] = result['print_section']
            else: 
                master['print_section'] = np.nan
            if 'print_page' in result.keys():
                master['print_page'] = result['print_page']
            else:
                master['print_page'] = np.nan
            master['pub_date'] = result['pub_date']
            master['headline'] = result['headline']['main']
            master['byline'] = result['byline']['original']
            master['word_count'] = result['word_count']
            if len(result['keywords']) >0:
                master['topic'] = result['keywords'][0]['value']
            else:
                pass
            out.append(pd.DataFrame([master]))
        
        df = pd.concat(out)
        df['byline'].str.replace('By', '')
        self.df = df
        
    def upload_raw_to_s3(self, bucket = 'nyt-archive-test'): 
        
        bucket = bucket
        
        df = self.df 
        
        tmp_save_path = f'archive_{self.year}_{self.month}.csv'
        
        #os.mkdir(tmp_save_path)
        df.to_csv(tmp_save_path, index = False)
        
        # upload the file
        
        upload_file(file_name = os.path.abspath(tmp_save_path),
                   bucket = bucket, 
                   object_name = f'archive/{self.year}/{self.month}/nyt_archive_{self.year}_{self.month}')
        
        # remove the file 
        
        os.remove(tmp_save_path)
        
        # remove tmp 

# run 
    
if __name__ == "__main__" :
    
    archive = NytArchive()
    
    years = range(2015, 2021, 1) # specify range
    months = range(1, 13, 1)
    
    for year in years: # build archive 
        for month in months: 
            archive.get_stories(year, month)
            archive.upload_raw_to_s3()
            sleep(6)
    
    # get tweets 
    
    
