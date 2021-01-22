import re
import gzip
import os,glob
from flask import jsonify
import traceback
import pymongo
from pymongo import MongoClient
import pandas as pd
from datetime import datetime
from dateutil.tz import tzutc

from config import config



class LogSearch:
    def mongo_con(self):
        client = MongoClient()
        db = client.plog
        return db
    def log_search(self,filter_,offset,per_page):
        log = filter_.get("log")
        pipeline= []
        start_date = None
        end_date = None
        if filter_.get("date_range").get("start"):
            start_date = datetime.strptime(filter_.get("date_range").get("start"), '%m/%d/%Y %I:%M %p')
        if filter_.get("date_range").get("end"): 
            end_date = datetime.strptime(filter_.get("date_range").get("end"), '%m/%d/%Y %I:%M %p')
        
        if filter_.get("log_type"):
            log_type = {"$or":[{"log_type":i} for i in filter_["log_type"]]}
            pipeline.append({"$match": log_type})
            
        if start_date and end_date:
            pipeline.append({"$match":{"date":{'$gte':start_date,'$lt':end_date}}})
        else :
            if start_date:
                pipeline.append({"$match":{"date":{'$gte':start_date}}})
            if end_date:
                pipeline.append({"$match":{"date":{'$lt':end_date}}})

            
        if filter_.get("log_search"):
            log_search = {"log" :{"$regex":".*{key}.*".format(key=filter_.get("log_search"))}}
            pipeline.append({"$match" : log_search})
        
        if not filter_.get("log_type") and not filter_.get("date_range") and not filter_.get("log_search"):
            pipeline = []
        if filter_.get("sort"):
            pipeline.append({"$sort":{"date":int(filter_.get("sort"))}})

        result_count = pipeline.copy()
        result_count.append({"$count":"count"})
        pipeline.append({"$skip":offset})
        pipeline.append({"$limit":per_page})
        # import pdb;pdb.set_trace()
        #print(pipeline)
        # db = self.mongo_con()
        # data = list(db.plog.aggregate(pipeline))
        db = self.mongo_con()
        data = db[log].aggregate(pipeline,allowDiskUse=True)
        record = list(db[log].aggregate(pipeline,allowDiskUse=True))
        print(pipeline)
        if record:
            count = list(db[log].aggregate(result_count,allowDiskUse=True))[0].get("count")
            return [[count,data],False]
        else : 
            return ["No Records Found !!!!!!!!!!!",True]

    def last_sync_query(self):
        pipeline = [{"$match":{"Status":"Done"}},{"$sort":{"_id":-1}},{"$limit":1}]
        db = self.mongo_con()
        data = list(db.sync_log.aggregate(pipeline))
        if data:
            l_u=data[0].get('DateTime').strftime("%m-%d-%Y  %H:%M:%S")
        else :
            l_u = None
        return l_u

    def last_sync_query_1(self):
        pipeline = [{"$match":{"Status":"Done"}},{"$sort":{"_id":-1}}]
        db = self.mongo_con()
        data = db.sync_log.aggregate(pipeline)
        return data

    def col_names(self):
        db = self.mongo_con()
        collection_names = db.list_collection_names()
        collection_names.remove("sync_log")
        return collection_names
                
        

class Synclog:
    def __init__(self):
        self.response = {}
        self.log_path = config.log_path + "personify.log"
        self.db = self.mongo_con()
    def mongo_con(self):
        client = MongoClient()
        db = client.plog
        return db
    
    def col_drop(self,name):
        con = self.mongo_con()
        res = con[name].drop()
        return res
    def syn_log(self,username,status,count):
        self.response = {"UserName":username,"DateTime":datetime.now() ,"log_count":count,"Status":status}
        self.db.sync_log.insert_one(self.response)

    def sync(self):
        try :
            self.zip_db()
            log_obj = open(self.log_path,"r")
            log = log_obj.read()            
            log = re.split("\[(\d{2}\/\w{3}\/\d{4}\s\d{2}:\d{2}:\d{2})\]",log)
            del log[0]
            df = pd.DataFrame({"date":log[0::2],"log":log[1::2]})
            df["date"] = pd.to_datetime(df["date"],format="%d/%b/%Y %H:%M:%S")
            df["log_type"] = df["log"].str.split(" ").str[1]
            drop_col = self.col_drop("personify.log")
            self.db["personify.log"].insert_many(df.to_dict('records'))
            self.syn_log("admin1","Done",len(df))
            return jsonify(str(self.response))
        except:
            error = 'This should not be happening... hmmm %s', traceback.format_exc()
            return jsonify(error)
    def zip_db(self):
        try:
            db = self.mongo_con()
            current_dir = os.getcwd()
            os.chdir(config.log_path)
            zip_files = glob.glob('*.gz')
            collection_names = db.list_collection_names()
            os.chdir(current_dir)
            collection_ = list(set(zip_files+collection_names))
            collection_.remove("personify.log")
            collection_.remove("sync_log")
            for col in collection_:
                log_obj = gzip.open(config.log_path+col, 'rb')
                log = log_obj.read() 
                log = str(log)           
                log = re.split("\[(\d{2}\/\w{3}\/\d{4}\s\d{2}:\d{2}:\d{2})\]",log)
                del log[0]
                df = pd.DataFrame({"date":log[0::2],"log":log[1::2]})
                df["date"] = pd.to_datetime(df["date"],format="%d/%b/%Y %H:%M:%S")
                df["log_type"] = df["log"].str.split(" ").str[1]
                self.db[col].insert_many(df.to_dict('records'))
            return True
        except:
            error = 'This should not be happening... hmmm %s', traceback.format_exc()
            print(error)
            return False



        
#Synclog().sync()
#LogSearch().log_search({"log_type":["INFO","WARNING"],"date_range":{"start":"2019-5-25","end":"2020-12-24"},"log_search":"72F4ABCF104B"})
   
        
        
        
        