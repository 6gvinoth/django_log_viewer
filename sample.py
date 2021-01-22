#!/usr/bin/env python
#-*- coding: utf-8 -*-

from __future__ import unicode_literals
from flask import Flask, render_template, g, current_app, request
from flask.ext.paginate import Pagination
from pymongo import MongoClient

app = Flask(__name__)


@app.route('/')
def index():
    db_name = "plog"
    col_name = "plog"
    db = MongoClient()
    sDB = db[db_name][col_name]
    total = sDB.find().count()
    page, per_page, offset = get_page_items()
    users = sDB.find().skip(offset).limit(per_page)
    pagination = get_pagination(page=page,
                per_page=per_page,
                total=total,
                record_name=users,
                )
    return render_template('index.html', users=users,
              page=page,
              per_page=per_page,
              pagination=pagination,
              )


def get_css_framework():
    return current_app.config.get('CSS_FRAMEWORK', 'bootstrap3')


def get_link_size():
    return current_app.config.get('LINK_SIZE', 'sm')


def show_single_page_or_not():
    return current_app.config.get('SHOW_SINGLE_PAGE', False)


def get_page_items():
    page = int(request.args.get('page', 1))
    per_page = request.args.get('per_page')
    if not per_page:
            per_page = current_app.config.get('PER_PAGE', 20)
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

if __name__ == '__main__':
    app.run(debug=True)
