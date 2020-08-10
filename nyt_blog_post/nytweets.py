## CITATIONS 

## Data provided by The New York Times
## Data provided by Twitter

# Required modules 
from time import sleep
import tweepy 
import configparser 
import json 
import pandas as pd 
import numpy as np 
import requests 
import datetime
import os
import boto3
# Set filepaths 

out_dir = '/Users/aleedom/Dropbox/Projects/Python Projects/New York Times API Project'

# import credentials 

parser = configparser.ConfigParser() 
parser.read('creds.cfg')


consumer_key = parser['KEYS']['TWITTER_CONSUMER']
consumer_secret = parser['KEYS']['TWITTER_CONSUMER_SECRET']
nyt_key = parser['KEYS']['NYT_KEY']
nyt_secret = parser['KEYS']['NYT_SECRET']
twitter_access_token = parser['KEYS']['TWITTER_ACCESS_TOKEN'] 
twitter_access_secret = parser['KEYS']['TWITTER_ACCESS_SECRET']
aws_key = parser['AWS']['AWS_KEY']
aws_secret = parser['AWS']['AWS_SECRET_KEY']

# tweepy setup and auth 

auth = tweepy.OAuthHandler(consumer_key, consumer_secret) # add auth 

auth.set_access_token(twitter_access_token, twitter_access_secret) # add access token 

api = tweepy.API(auth) 

# set urls for api access 

wire_url = 'https://api.nytimes.com/svc/news/v3/content/{source}/{section}.json?api-key={key}'.format(source = 'all', section = 'all',
    key = nyt_key)

twitter_search_url = 'https://api.twitter.com/1.1/search/tweets.json'

##
## feature list -- # tweets at 15, 30, 1h, 2, 6, 12, 24? 
##

# Initialize boto3 

bucket = 'nyt-archive-test'

s3 = boto3.client('s3', 
                   aws_access_key_id = aws_key, 
                   aws_secret_access_key = aws_secret, 
                   region_name = 'us-west-2')

# helpers

def upload_file(file_name, bucket, object_name = None): ## from AWS docs 
    """Upload a file to an S3 bucket

    :param file_name: File to upload
    :param bucket: Bucket to upload to
    :param object_name: S3 object name. If not specified then file_name is used
    :return: True if file was uploaded, else False
    """

    # If S3 object_name was not specified, use file_name
    if object_name is None:
        object_name = file_name

    # Upload the file
    s3_client = s3
    
    try:
        response = s3_client.upload_file(file_name, bucket, object_name)
    except ClientError as e:
        logging.error(e)
        return False
    return True

today = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

def clean_results(directory = out_dir + '/clean_outputs'): 
    """Concatenates csvs stored locally and removes duplicate records"""
    # get files 
    
    f_list = glob.glob(directory + '/*.csv')
    df_list = [pd.read_csv(f) for f in f_list]
    df_list = pd.concat(df_list)
    df_list = df_list.drop_duplicates(subset = 'uuid')
    df_list.to_csv(directory + f"""_clean_{today}.csv""")

def get_tweets(url_list): 
        """Calls tweepy to search tweets for wire stories"""
        
        # get tweet, retweet, favorite counts 
        
        for url in url_list: 
            df_list = []
            out_dict = {}
            print(url)
        
        for page in tweepy.Cursor(api.search, q = url).pages(): 
            res = [status._json for status in page]

            
    
# Classes 
    
class nyt_stories:
    """
    Helper class to parse NYT wire stories APIs
    Methods: get_stories: Creates self.df 
    """

    def __init__(self, source = 'all', key = nyt_key, section = 'all'):
    
        self.path = '/Users/aleedom/Dropbox/Projects/Python Projects/New York Times API Project'
        self.key = key
        self.source = source
        self.section = section
        self.url = 'https://api.nytimes.com/svc/news/v3/content/{source}/{section}.json?api-key={key}'\
        .format(source = self.source,
                section = self.section,
                key = self.key)
    
    def get_stories(self): 
            """Gets wire stories from all sources"""
            
            url = self.url 
            res = requests.get(url).json()
            
            # check status 
            
            if res['status'] != 'OK': 
                raise ValueError 
            
            df = pd.DataFrame(res['results'])
            
            df['uuid'] = [hash(x) for x in df['slug_name']] # add unique id to drop dupes 
            
            self.df = df
            
    def add_out_dir(self, out_path = ''): # probably need to clean this feature up 
        """Allows user to specify output directory
        Param out_path: path to output directory"""
        self.out_path = self.path + '/' + out_path
        print(self.out_path)
    
    def write_locally(self, quiet = False): 
        """
        Writes self.df as a csv to the specified out_dir. If no out_dir is specified, will output to the default out_dir.
        Param: out_dir: directory to output the file 
        """
        df = self.df
        
        self.out_string = f'{self.out_path}/{self.section}'
        
        print(self.out_string)
        
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        os.makedirs(f'{self.out_string}', exist_ok = True)
        
        self.df.to_csv(f'{self.out_string}/wire_stories_{timestamp}.csv')
        
        if quiet == False: 
            print('file written...')
                   

                
    def write_stories_to_s3(self, bucket = bucket):
        """
        Writes a file to csv, uploads to s3, then deletes the file locally.
        Requires a self.df of stories 
        :param bucket: destination bucket name
        """
        self.bucket = bucket
        
        # save file locally
        
        df = self.df 
        os.mkdir('./tmp')
        tmp_save_path = f'./tmp/{self.section}_stories_{today}.csv'
        df.to_csv(tmp_save_path)
        
        # upload the file
        
        upload_file(file_name = os.path.abspath(tmp_save_path),
                   bucket = bucket, 
                   object_name = tmp_save_path)
        
        # remove the file 
        
        os.remove(tmp_save_path)
        
        # remove tmp 
        
        os.rmdir('./tmp')

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
    
    
