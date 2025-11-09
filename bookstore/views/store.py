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
from api.sql import Member, Order_List, Product, Record, Cart, Player, Team, Game,TeamRecord

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




@store.route('/playerlist', methods=['GET'])
@login_required
def playerlist():
    if current_user.role == 'manager':
        flash('No permission')
        return redirect(url_for('manager.home'))

    keyword = request.args.get('keyword', '').strip()

    # 先取得所有隊伍
    teams_data = Team.get_all_team()
    teams = []

    for team_row in teams_data:
        tName = team_row[0]
        # 依據關鍵字取該隊球員
        players = Player.get_players_by_team(tName, keyword)

        team = {
            'name': tName,
            'players': []
        }

        for p in players:
            team['players'].append({
                'pNo': p[0],
                'name': p[1] or '未命名球員',
                'position': p[2],
                'height': p[3],
                'weight': p[4],
                'education': p[5],
                'is_foreign': '*' in p[1] if p[1] else False
            })

        if keyword:
            if team['players']:
                teams.append(team)
        else:

            teams.append(team)

    return render_template('playerlist.html', teams=teams, keyword=keyword, user=current_user.name)


@store.route('/playerinfo')
@login_required
def playerinfo():
    tName = request.args.get('tName')
    pNo = request.args.get('pNo')

    if not tName or not pNo:
        flash('缺少球員資訊參數')
        return redirect(url_for('bookstore.playerlist'))

    player = Player.get_player(tName, pNo)
    if not player:
        flash('查無此球員')
        return redirect(url_for('bookstore.playerlist'))

    player_info = {
        'tName': player[0],
        'pNo': player[1],
        'name': player[2],
        'birthday': player[3],
        'height': player[4],
        'weight': player[5],
        'education': player[6],
        'position': player[7]
    }

    return render_template('playerinfo.html', player=player_info, user=current_user.name)


@store.route('/gamelist', methods=['GET'])
@login_required
def gamelist():
    if current_user.role == 'manager':
        flash('No permission')
        return redirect(url_for('manager.home'))

    team = request.args.get('team', '').strip()
    field = request.args.get('field', '').strip()
    date = request.args.get('date', '').strip()

    # 檢查是否有篩選
    if team or field or date:
        games_data = Game.search_games(team=team, field=field, date=date)
    else:
        games_data = Game.get_all_games()

    games = []
    for g in games_data:
        games.append({
            'winTeam': g[0],
            'loseTeam': g[1],
            'date': g[2],
            'fName': g[3],
        })

    return render_template('gamelist.html', games=games, user=current_user.name)


@store.route('/gameinfo')
@login_required
def gameinfo():
    winTeam = request.args.get('winTeam')
    loseTeam = request.args.get('loseTeam')
    date = request.args.get('date')

    if not winTeam or not loseTeam or not date:
        flash('缺少正確比賽資訊參數')
        return redirect(url_for('bookstore.gamelist'))

    game = Game.get_more_info(winTeam=winTeam, loseTeam=loseTeam, date=date)
    if not game:
        flash('查無此比賽紀錄')
        return redirect(url_for('bookstore.gamelist'))

    # ⚠️ 不要再加 game = game[0]
    game_info = {
        'winTeam': game[0],
        'loseTeam': game[1],
        'date': game[2],
        'fName': game[3],
        'result': game[4],
    }

    return render_template('gameinfo.html', game=game_info, user=current_user.name)


# 球隊列表
@store.route('/teamlist', methods=['GET'])
@login_required
def teamlist():
    if current_user.role == 'manager':
        flash('No permission')
        return redirect(url_for('manager.home'))

    keyword = request.args.get('keyword', '').strip()

    # 取得所有球隊
    teams_data = Team.get_all_teams()  # 呼叫 sql.py 的 Team.get_all_teams()
    print(teams_data)
    teams = []

    for t in teams_data:
        tName, chiefCoach, companyName, cPhone, cAddress, fName = t
        if keyword and keyword.lower() not in tName.lower():
            continue  # 篩選關鍵字
        teams.append({
            'tName': tName,
            'chiefCoach': chiefCoach,
            'companyName': companyName,
            'cPhone': cPhone,
            'cAddress': cAddress,
            'fName': fName
        })

    return render_template('teamlist.html', teams=teams, keyword=keyword, user=current_user.name)


# 單一球隊詳細資訊 
@store.route('/team_detail')
@login_required
def team_detail():
    # 從 URL 參數取得球隊名稱
    team_name = request.args.get("team_name")
    if not team_name:
        flash('未指定球隊名稱')
        return redirect(url_for('bookstore.teamlist'))

    # 權限檢查
    if current_user.role == 'manager':
        flash('No permission')
        return redirect(url_for('manager.home'))

    # 取得球隊資料
    team = Team.get_team_detail(team_name)
    if not team:
        flash('查無此球隊')
        return redirect(url_for('bookstore.teamlist'))

    # 整理成字典，方便 template 使用
    team_info = {
        'tName': team[0],
        'chiefCoach': team[1],
        'companyName': team[2],
        'cPhone': team[3],
        'cAddress': team[4],
        'fName': team[5]
    }
    print(f"DEBUG: team_info['chiefCoach'] is: {team_info['chiefCoach']}")

    # 傳給 template
    return render_template('team_detail.html', team=team_info, user=current_user.name)

#--------------------------------------------
@store.route('/race', methods=['GET', 'POST'])
@login_required
def race():
    if request.method == 'POST':
        flash('Action completed, returning to store.')
        return redirect(url_for('bookstore.bookstore'))

    if current_user.role == 'manager':
        flash('No permission')
        return redirect(url_for('manager.home'))

    race_data = TeamRecord.get_team_records()
    races = []
    print(race_data) 

    for r in race_data:
        races.append({
            'team_name': r[0],
            'wins': r[1] ,
            'losses': r[2],
            'win_rate': float(r[3]) if r[3] is not None else 0.0,
            'games_behind': float(r[4]) if r[4] is not None else 0.0
        })

    return render_template('race.html', teams=races,user=current_user.name)

