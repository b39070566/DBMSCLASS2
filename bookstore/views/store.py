# 檔案位置: bookstore/views/store.py (完整取代)

import re
from typing_extensions import Self
from flask import Flask, request, template_rendered, Blueprint
from flask import url_for, redirect, flash
from flask import render_template
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from datetime import datetime
from numpy import identity, product
import random, string
from sqlalchemy import null
from link import *
import math
from base64 import b64encode
# 導入 DB class
from api.sql import Member, Order_List, Product, Record, Cart, DB

store = Blueprint('bookstore', __name__, template_folder='../templates')

@store.route('/', methods=['GET', 'POST'])
@login_required
def bookstore():
    # --- 這是你原有的 bookstore() 函式，我們保留它 ---
    result = Product.count()
    count = math.ceil(result[0]/9)
    flag = 0
    
    if request.method == 'GET':
        if(current_user.role == 'manager'):
            flash('No permission')
            return redirect(url_for('manager.home'))

    if 'keyword' in request.args and 'page' in request.args:
        total = 0
        single = 1
        page = int(request.args['page'])
        start = (page - 1) * 9
        end = page * 9
        search = request.values.get('keyword')
        keyword = search
        
        sql = "SELECT pid, pname, price FROM product WHERE pname ILIKE %s" 
        book_row = DB.fetchall(sql, ('%' + search + '%',))
        
        book_data = []
        final_data = []
        
        for i in book_row:
            book = {
                '商品編號': i[0],
                '商品名稱': i[1],
                '商品價格': i[2]
            }
            book_data.append(book)
            total = total + 1
        
        if(len(book_data) < end):
            end = len(book_data)
            flag = 1
            
        for j in range(start, end):
            final_data.append(book_data[j])
            
        count = math.ceil(total/9)
        
        return render_template('bookstore.html', single=single, keyword=search, book_data=book_data, user=current_user.name, page=1, flag=flag, count=count) 

    
    elif 'pid' in request.args:
        pid = request.args['pid']
        data = Product.get_product(pid)
        
        pname = data[1]
        price = data[2]
        category = data[3]
        description = data[4]
        image = 'sdg.jpg'
        
        product = {
            '商品編號': pid,
            '商品名稱': pname,
            '單價': price,
            '類別': category,
            '商品敘述': description,
            '商品圖片': image
        }

        return render_template('product.html', data = product, user=current_user.name)
    
    elif 'page' in request.args:
        page = int(request.args['page'])
        start = (page - 1) * 9
        end = page * 9
        
        book_row = Product.get_all_product()
        book_data = []
        final_data = []
        
        for i in book_row:
            book = {
                '商品編號': i[0],
                '商品名稱': i[1],
                '商品價格': i[2]
            }
            book_data.append(book)
            
        if(len(book_data) < end):
            end = len(book_data)
            flag = 1
            
        for j in range(start, end):
            final_data.append(book_data[j])
        
        return render_template('bookstore.html', book_data=final_data, user=current_user.name, page=page, flag=flag, count=count) 
    
    elif 'keyword' in request.args:
        single = 1
        search = request.values.get('keyword')
        keyword = search
        
        sql = "SELECT pid, pname, price FROM product WHERE pname ILIKE %s" 
        book_row = DB.fetchall(sql, ('%' + search + '%',))
        
        book_data = []
        total = 0
        
        for i in book_row:
            book = {
                '商品編號': i[0],
                '商品名稱': i[1],
                '商品價格': i[2]
            }

            book_data.append(book)
            total = total + 1
            
        if(len(book_data) < 9):
            flag = 1
        
        count = math.ceil(total/9) 
        
        return render_template('bookstore.html', keyword=search, single=single, book_data=book_data, user=current_user.name, page=1, flag=flag, count=count) 
    
    else:
        book_row = Product.get_all_product()
        book_data = []
        temp = 0
        for i in book_row:
            book = {
                '商品編號': i[0],
                '商品名稱': i[1],
                '商品價格': i[2],
            }
            if len(book_data) < 9:
                book_data.append(book)
        
        return render_template('bookstore.html', book_data=book_data, user=current_user.name, page=1, flag=flag, count=count)


@store.route('/cart', methods=['GET', 'POST'])
@login_required 
def cart():
    # 當有人 POST (例如嘗試加入購物車) 到這個頁面時，
    # 我們把他導向主頁，因為這個頁面現在只顯示戰績。
    if request.method == 'POST':
        flash('Action completed, returning to store.')
        return redirect(url_for('bookstore.bookstore'))

    # 當有人 GET 瀏覽這個頁面時:
    # 檢查是否為管理者
    if (current_user.role == 'manager'):
        flash('No permission')
        return redirect(url_for('manager.home'))
    
    # 顯示戰績頁面 (cart.html)
    return render_template('cart.html', user=current_user.name)

