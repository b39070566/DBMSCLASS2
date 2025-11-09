import imp
from flask import render_template, Blueprint, redirect, request, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from link import *
from api.sql import *
#--------------------------------------
from sql import get_team_records_sql
#--------------------------------------

api = Blueprint('api', __name__, template_folder='./templates')

login_manager = LoginManager(api)
login_manager.login_view = 'api.login'
login_manager.login_message = "請先登入"

class User(UserMixin):
    pass

@login_manager.user_loader
def user_loader(userid):  
    user = User()
    user.id = userid
    data = Member.get_role(userid)
    try:
        user.role = data[0]
        user.name = data[1]
    except:
        pass
    return user

@api.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':

        account = request.form['account']
        password = request.form['password']
        data = Member.get_member(account) 

        try:
            DB_password = data[0][1]
            user_id = data[0][2]
            identity = data[0][3]

        except:
            flash('*沒有此帳號')
            return redirect(url_for('api.login'))

        if(DB_password == password ):
            user = User()
            user.id = user_id
            login_user(user)

            if( identity == 'user'):
                return redirect(url_for('bookstore.bookstore'))
            else:
                return redirect(url_for('manager.productManager'))
        
        else:
            flash('*密碼錯誤，請再試一次')
            return redirect(url_for('api.login'))

    
    return render_template('login.html')

@api.route('/register', methods=['POST', 'GET'])
def register():
    if request.method == 'POST':
        user_account = request.form['account']
        exist_account = Member.get_all_account()
        account_list = []
        for i in exist_account:
            account_list.append(i[0])

        if(user_account in account_list):
            flash('Falied!')
            return redirect(url_for('api.register'))
        else:
            input = { 
                'lname': request.form['userlname'],
                'fname': request.form['userfname'],
                'account':user_account, 
                'password':request.form['password'], 
                'identity':request.form['identity'] 
            }
            Member.create_member(input)
            return redirect(url_for('api.login'))

    return render_template('register.html')

@api.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

#-------------------------------------------
@api.route('/records', methods=['GET'])
def get_team_records():
    try:
        # 使用 sql.py 裡的 DB.fetchall() 來執行 SQL
        rows = DB.fetchall(get_team_records_sql)
        
        # 你的 SQL 欄位名稱
        columns = ['team_name', 'wins', 'losses', 'win_rate', 'games_behind']
        
        # 將資料 (rows) 轉換為字典 (JSON)
        data = [dict(zip(columns, row)) for row in rows]
        
        return jsonify(data)
        
    except Exception as e:
        print(f"Error fetching team records: {e}")
        return jsonify({"error": str(e)}), 500
#-----------------------------------------------