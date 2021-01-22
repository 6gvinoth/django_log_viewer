from flask import Flask, request, session, g,current_app ,redirect, url_for, abort, render_template, flash
from flask.ext.bcrypt import Bcrypt
from flask.ext.csrf import csrf
import logging

from utils.worker import LogSearch
from utils.worker import Synclog
from flask_paginate import Pagination, get_page_parameter
from pymongo import MongoClient
from threading import Thread
app = Flask(__name__,static_url_path='/static')
app.config.from_object('settings')
bcrypt = Bcrypt(app)
csrf(app)

def get_css_framework():
    return current_app.config.get('CSS_FRAMEWORK', 'bootstrap3')


def get_link_size():
    return current_app.config.get('LINK_SIZE', 'sm')


def show_single_page_or_not():
    return current_app.config.get('SHOW_SINGLE_PAGE', False)


def get_page_items():
    page = int(request.args.get('page', 1))
    per_page = request.args.get('limit')
    if not per_page:
            per_page = current_app.config.get('PER_PAGE', 10)
    else:
            per_page = int(per_page)

    offset = (page - 1) * per_page
    return page, per_page, offset


def get_pagination(**kwargs):
       kwargs.setdefault('record_name', 'records')
       return Pagination(css_framework=get_css_framework(),
          link_size=get_link_size(),
          show_single_page=show_single_page_or_not(),
          **kwargs
          )



@app.route('/')
def index():
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    log = request.args.get("log","personify.log")
    c_error = request.args.get("ERROR",0)
    c_warning = request.args.get("WARNING",0)
    c_debug = request.args.get("DEBUG",0)
    c_info = request.args.get("INFO",0)
    log_search = request.args.get("log_search",{})
    # sort = int(request.args.get("sort",1))
    sort = request.args.get("sort")
    log_type = []
    if c_error or c_warning or c_debug or c_info:
        if c_error:
            log_type.append("ERROR")
        if c_warning:
            log_type.append("WARNING")
        if c_debug:
            log_type.append("DEBUG")
        if c_info:
            log_type.append("INFO")
    filter_ = {"log_type": log_type,"log_search": log_search,"sort":sort,
    "log":log,"date_range":{"start":start_date,"end":end_date}}

    page, per_page, offset = get_page_items()
    response=LogSearch().log_search(filter_,offset,per_page)
    last_update = LogSearch().last_sync_query()

    collection_names = LogSearch().col_names()
    
    if not response[1]:
        
        total,data = response[0][0],response[0][1]
        pagination = get_pagination(page=page,
                per_page=per_page,
                total=total,
                record_name=data,
                )
        return render_template('index.html', data=data,
              page=page,
              per_page=per_page,
              pagination=pagination,
              c_error = c_error,c_warning=c_warning,c_debug=c_debug,c_info=c_info,
              log_search = log_search,
              last_update = last_update,
              sort = sort,log = log,
              collection_names = collection_names,
              start_date =start_date,
              end_date = end_date,
              error_ff =response[1]
              )
    else :
        return render_template('index.html',
            page=page,
              per_page=per_page,
              c_error = c_error,c_warning=c_warning,c_debug=c_debug,c_info=c_info,
              log_search = log_search,
              last_update = last_update,
              sort = sort,log = log,
              collection_names = collection_names,
              start_date =start_date,
              end_date = end_date,
              error_ff =response[1])

    
    


# @app.route('/')
# def index():
#     page=2
#     search = True
#     d= LogSearch().last_sync_query_1()
#     pagination = Pagination(page=page, total=2, search=search, record_name='users')
#     return render_template('index.html',
#                            users=d,
#                            pagination=pagination,
#                            )
@app.route('/sync', methods=['POST','GET'])
def sync():
    syn_obj = Synclog()
    res = syn_obj.sync
    thread = Thread(target=res)
    thread.start()
    return "Sucessfully Triggered"

@app.route('/last_update', methods=['POST','GET'])
def last_update():
    query_obj = LogSearch()
    res = LogSearch().last_sync_query()
    return res


if __name__ == '__main__':
    app.debug = app.config['DEBUG']
    app.run(host='0.0.0.0')
