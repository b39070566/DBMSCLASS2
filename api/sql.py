import os
from typing import Optional
import psycopg2
from psycopg2 import pool
from dotenv import load_dotenv
#--------------------------------
get_team_records_sql = """
/* CTE 1: 取得所有球隊的完整列表 */
WITH all_teams AS (
    /* * *** 修正 ***
     * 這裡從 'team' 資料表讀取 'tname' 欄位,
     * 並把它重新命名 (AS) 為 'team_name' 供後續查詢使用。
     */
    SELECT tname AS team_name FROM team
),

/* CTE 2: 計算所有球隊的勝場數 */
win_stats AS (
    SELECT
        winteam AS team_name, /* 這裡的 team_name 只是別名 */
        COUNT(*) AS wins
    FROM game
    WHERE winteam IS NOT NULL /* 忽略和局 (NULL) */
    GROUP BY winteam
),

/* CTE 3: 計算所有球隊的敗場數 */
lose_stats AS (
    SELECT
        loseteam AS team_name, /* 這裡的 team_name 只是別名 */
        COUNT(*) AS losses
    FROM game
    WHERE loseteam IS NOT NULL /* 忽略和局 (NULL) */
    GROUP BY loseteam
),

/* CTE 4: 合併所有資料 (以 all_teams 為基礎) */
merged AS (
    SELECT
        t.team_name, /* 來自 all_teams (也就是 tname) */
        COALESCE(w.wins, 0) AS wins,
        COALESCE(l.losses, 0) AS losses,
        /* 計算勝率 (W / (W+L)) */
        ROUND(
            /* COALESCE 避免 0 / 0 的錯誤 */
            COALESCE(
                w.wins::NUMERIC / NULLIF((COALESCE(w.wins, 0) + COALESCE(l.losses, 0)), 0),
            0),
        3) AS win_rate
    FROM
        all_teams t
    /* LEFT JOIN 確保 0 勝 0 敗的球隊也能顯示 */
    LEFT JOIN
        win_stats w ON t.team_name = w.team_name
    LEFT JOIN
        lose_stats l ON t.team_name = l.team_name
)

/* 最終 Select: 計算勝差 (GB) */
SELECT 
    team_name,
    wins,
    losses,
    win_rate,
    /* 勝差公式: [ (第一名的勝 - 自己的勝) + (自己的敗 - 第一名的敗) ] / 2.0 */
    ROUND(
        ( (MAX(wins) OVER() - wins) + (losses - MIN(losses) OVER()) ) / 2.0,
    1) AS games_behind
FROM merged
ORDER BY win_rate DESC, wins DESC;
"""
#-----------------------------


load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))
USER = os.getenv('DB_USER')
PASSWORD = os.getenv('DB_PASSWORD')
DBNAME = os.getenv('DB_NAME')
HOST = os.getenv('DB_HOST')
PORT = os.getenv('DB_PORT')

class DB:
    connection_pool = pool.SimpleConnectionPool(
        1, 100,  # 最小和最大連線數
        user=USER,
        password=PASSWORD,
        host=HOST,
        port=PORT,
        dbname=DBNAME
    )

    @staticmethod
    def connect():
        return DB.connection_pool.getconn()

    @staticmethod
    def release(connection):
        DB.connection_pool.putconn(connection)

    @staticmethod
    def execute_input(sql, input):
        if not isinstance(input, (tuple, list)):
            raise TypeError(f"Input should be a tuple or list, got: {type(input).__name__}")
        connection = DB.connect()
        try:
            with connection.cursor() as cursor:
                cursor.execute(sql, input)
                connection.commit()
        except psycopg2.Error as e:
            print(f"Error executing SQL: {e}")
            connection.rollback()
            raise e
        finally:
            DB.release(connection)

    @staticmethod
    def execute(sql):
        connection = DB.connect()
        try:
            with connection.cursor() as cursor:
                cursor.execute(sql)
        except psycopg2.Error as e:
            print(f"Error executing SQL: {e}")
            connection.rollback()
            raise e
        finally:
            DB.release(connection)

    @staticmethod
    def fetchall(sql, input=None):
        connection = DB.connect()
        try:
            with connection.cursor() as cursor:
                cursor.execute(sql, input)
                return cursor.fetchall()
        except psycopg2.Error as e:
            print(f"Error fetching data: {e}")
            raise e
        finally:
            DB.release(connection)

    @staticmethod
    def fetchone(sql, input=None):
        connection = DB.connect()
        try:
            with connection.cursor() as cursor:
                cursor.execute(sql, input)
                return cursor.fetchone()
        except psycopg2.Error as e:
            print(f"Error fetching data: {e}")
            raise e
        finally:
            DB.release(connection)


class Member:
    @staticmethod
    def get_member(account):
        sql = "SELECT account, password, mid, identity, (lname || fname) AS name FROM member WHERE account = %s"
        return DB.fetchall(sql, (account,))

    @staticmethod
    def get_all_account():
        sql = "SELECT account FROM member"
        return DB.fetchall(sql)

    @staticmethod
    def create_member(input_data):
        sql = 'INSERT INTO member (lname, fname, account, password, identity) VALUES (%s, %s, %s, %s, %s)'
        DB.execute_input(sql, (input_data['lname'], input_data['fname'], input_data['account'], input_data['password'], input_data['identity']))

    @staticmethod
    def delete_product(tno, pid):
        sql = 'DELETE FROM record WHERE tno = %s and pid = %s'
        DB.execute_input(sql, (tno, pid))

    @staticmethod
    def get_order(userid):
        sql = 'SELECT * FROM order_list WHERE mid = %s ORDER BY ordertime DESC'
        return DB.fetchall(sql, (userid,))

    @staticmethod
    def get_role(userid):
        sql = 'SELECT identity, (lname || fname) AS name FROM member WHERE mid = %s'
        return DB.fetchone(sql, (userid,))


class Cart:
    @staticmethod
    def check(user_id):
        sql = '''SELECT * FROM cart, record 
                 WHERE cart.mid = %s::bigint 
                 AND cart.tno = record.tno::bigint'''
        return DB.fetchone(sql, (user_id,))

    @staticmethod
    def get_cart(user_id):
        sql = 'SELECT * FROM cart WHERE mid = %s'
        return DB.fetchone(sql, (user_id,))

    @staticmethod
    def add_cart(user_id, time):
        sql = 'INSERT INTO cart (mid, carttime, tno) VALUES (%s, %s, nextval(\'cart_tno_seq\'))'
        DB.execute_input(sql, (user_id, time))

    @staticmethod
    def clear_cart(user_id):
        sql = 'DELETE FROM cart WHERE mid = %s'
        DB.execute_input(sql, (user_id,))


class Product:
    @staticmethod
    def count():
        sql = 'SELECT COUNT(*) FROM product'
        return DB.fetchone(sql)

    @staticmethod
    def get_product(pid):
        sql = 'SELECT * FROM product WHERE pid = %s'
        return DB.fetchone(sql, (pid,))

    @staticmethod
    def get_all_product():
        sql = 'SELECT * FROM product'
        return DB.fetchall(sql)

    @staticmethod
    def get_name(pid):
        sql = 'SELECT pname FROM product WHERE pid = %s'
        return DB.fetchone(sql, (pid,))[0]

    @staticmethod
    def add_product(input_data):
        sql = 'INSERT INTO product (pid, pname, price, category, pdesc) VALUES (%s, %s, %s, %s, %s)'
        DB.execute_input(sql, (input_data['pid'], input_data['pname'], input_data['price'], input_data['category'], input_data['pdesc']))

    @staticmethod
    def delete_product(pid):
        sql = 'DELETE FROM product WHERE pid = %s'
        DB.execute_input(sql, (pid,))

    @staticmethod
    def update_product(input_data):
        sql = 'UPDATE product SET pname = %s, price = %s, category = %s, pdesc = %s WHERE pid = %s'
        DB.execute_input(sql, (input_data['pname'], input_data['price'], input_data['category'], input_data['pdesc'], input_data['pid']))


class Record:
    @staticmethod
    def get_total_money(tno):
        sql = 'SELECT SUM(total) FROM record WHERE tno = %s'
        return DB.fetchone(sql, (tno,))[0]

    @staticmethod
    def check_product(pid, tno):
        sql = 'SELECT * FROM record WHERE pid = %s and tno = %s'
        return DB.fetchone(sql, (pid, tno))

    @staticmethod
    def get_price(pid):
        sql = 'SELECT price FROM product WHERE pid = %s'
        return DB.fetchone(sql, (pid,))[0]

    @staticmethod
    def add_product(input_data):
        sql = 'INSERT INTO record (pid, tno, amount, saleprice, total) VALUES (%s, %s, 1, %s, %s)'
        DB.execute_input(sql, (input_data['pid'], input_data['tno'], input_data['saleprice'], input_data['total']))

    @staticmethod
    def get_record(tno):
        sql = 'SELECT * FROM record WHERE tno = %s'
        return DB.fetchall(sql, (tno,))

    @staticmethod
    def get_amount(tno, pid):
        sql = 'SELECT amount FROM record WHERE tno = %s and pid = %s'
        return DB.fetchone(sql, (tno, pid))[0]

    @staticmethod
    def update_product(input_data):
        sql = 'UPDATE record SET amount = %s, total = %s WHERE pid = %s and tno = %s'
        DB.execute_input(sql, (input_data['amount'], input_data['total'], input_data['pid'], input_data['tno']))

    @staticmethod
    def delete_check(pid):
        sql = 'SELECT * FROM record WHERE pid = %s'
        return DB.fetchone(sql, (pid,))

    @staticmethod
    def get_total(tno):
        sql = 'SELECT SUM(total) FROM record WHERE tno = %s'
        return DB.fetchone(sql, (tno,))[0]


class Order_List:
    @staticmethod
    def add_order(input_data):
        sql = 'INSERT INTO order_list (oid, mid, ordertime, price, tno) VALUES (DEFAULT, %s, TO_TIMESTAMP(%s, %s), %s, %s)'
        DB.execute_input(sql, (input_data['mid'], input_data['ordertime'], input_data['format'], input_data['total'], input_data['tno']))

    @staticmethod
    def get_order():
        sql = '''
            SELECT o.oid, (m.lname || m.fname) AS name, o.price, o.ordertime
            FROM order_list o
            NATURAL JOIN member m
            ORDER BY o.ordertime DESC
        '''
        return DB.fetchall(sql)

    @staticmethod
    def get_orderdetail():
        sql = '''
        SELECT o.oid, p.pname, r.saleprice, r.amount
        FROM order_list o
        JOIN record r ON o.tno = r.tno -- 確保兩者都是 bigint 類型
        JOIN product p ON r.pid = p.pid
        '''
        return DB.fetchall(sql)


class Analysis:
    @staticmethod
    def month_price(i):
        sql = 'SELECT EXTRACT(MONTH FROM ordertime), SUM(price) FROM order_list WHERE EXTRACT(MONTH FROM ordertime) = %s GROUP BY EXTRACT(MONTH FROM ordertime)'
        return DB.fetchall(sql, (i,))

    @staticmethod
    def month_count(i):
        sql = 'SELECT EXTRACT(MONTH FROM ordertime), COUNT(oid) FROM order_list WHERE EXTRACT(MONTH FROM ordertime) = %s GROUP BY EXTRACT(MONTH FROM ordertime)'
        return DB.fetchall(sql, (i,))

    @staticmethod
    def category_sale():
        sql = 'SELECT SUM(total), category FROM product, record WHERE product.pid = record.pid GROUP BY category'
        return DB.fetchall(sql)

    @staticmethod
    def member_sale():
        sql = 'SELECT SUM(price), member.mid, (member.lname || member.fname) AS name FROM order_list, member WHERE order_list.mid = member.mid AND member.identity = %s GROUP BY member.mid, member.lname, member.fname ORDER BY SUM(price) DESC'
        return DB.fetchall(sql, ('user',))

    @staticmethod
    def member_sale_count():
        sql = 'SELECT COUNT(*), member.mid, (member.lname || member.fname) AS name FROM order_list, member WHERE order_list.mid = member.mid AND member.identity = %s GROUP BY member.mid, member.lname, member.fname ORDER BY COUNT(*) DESC'
        return DB.fetchall(sql, ('user',))

#----------------------------------------------
class Team:
    @staticmethod
    def get_all_teams():
        """
        取得所有球隊 (修正: 透過 LEFT JOIN 取得總教練姓名)
        """
        sql = '''
            SELECT 
                T.tName, 
                C.cName AS chiefCoach,  -- 確保這裡將教練姓名別名為 chiefCoach
                T.companyName, 
                T.cPhone, 
                T.cAddress, 
                T.fName
            FROM 
                team T
            LEFT JOIN 
                coach C ON T.chiefCoach = C.cNo -- 確保這裡有 LEFT JOIN
        '''
        return DB.fetchall(sql)

    @staticmethod
    def search_teams(tName=None, chiefCoach=None, companyName=None):
        """
        搜尋球隊資料，可依球隊名稱、總教練、公司名稱過濾
        (修正: 透過 LEFT JOIN 取得總教練姓名，並以姓名進行搜尋)
        """
        sql = """
            SELECT 
                T.tName, 
                C.cName AS chiefCoach, 
                T.companyName, 
                T.cPhone, 
                T.cAddress, 
                T.fName
            FROM 
                team T
            LEFT JOIN 
                coach C ON T.chiefCoach = C.cNo
            WHERE 1=1
        """
        params = []

        if tName:
            sql += " AND T.tName ILIKE %s"
            params.append(f"%{tName}%")

        if chiefCoach:
            # 修正: 搜尋條件需針對教練姓名 (C.cName) 進行
            sql += " AND C.cName ILIKE %s"
            params.append(f"%{chiefCoach}%")

        if companyName:
            sql += " AND T.companyName ILIKE %s"
            params.append(f"%{companyName}%")

        sql += " ORDER BY T.tName"

        return DB.fetchall(sql, tuple(params))



    @staticmethod
    def get_team_detail(tName):
        """
        取得單一球隊詳細資訊 (修正: 透過 LEFT JOIN 取得總教練姓名)
        """
        sql = '''
            SELECT 
                T.tName, 
                C.cName AS chiefCoach,  -- 確保這裡將教練姓名別名為 chiefCoach
                T.companyName, 
                T.cPhone, 
                T.cAddress, 
                T.fName
            FROM 
                team T
            LEFT JOIN 
                coach C ON T.chiefCoach = C.cNo -- 確保這裡有 LEFT JOIN
            WHERE 
                T.tName = %s
        '''
        return DB.fetchone(sql, (tName,))


    @staticmethod
    def add_team(data):
        sql = '''
            INSERT INTO team (tname, chiefcoach, companyname, cphone, caddress, fname)
            VALUES (%s, %s, %s, %s, %s, %s)
        '''
        DB.execute_input(sql, (
            data['tName'],
            data.get('chiefCoach', None),   # 可為空
            data.get('companyName', None),
            data.get('cPhone', None),
            data.get('cAddress', None),
            data.get('fName', None)
        ))

    @staticmethod
    def update_team(data):
        sql = '''
              UPDATE team
              SET tname       = %s,
                  chiefcoach  = %s,
                  companyname = %s,
                  cphone      = %s,
                  caddress    = %s,
                  fname       = %s
              WHERE tname = %s \
              '''
        DB.execute_input(sql, (
            data.get('tName'),
            data.get('chiefCoach', None),
            data.get('companyName', None),
            data.get('cPhone', None),
            data.get('cAddress', None),
            data.get('fName', None),
            data.get('oldTName')
        ))


# -------------------------------
# Team 球隊管理
# -------------------------------


# -------------------------------
# Player 球員管理
# -------------------------------
class Player:
    @staticmethod
    def get_all_players(keyword=None):
        if keyword:
            sql = '''
                  SELECT tname, \
                         pno, \
                         name, \
                         birthday, \
                         position, \
                         height, \
                         weight, \
                         education
                  FROM player
                  WHERE name ILIKE %s
                  ORDER BY tname \
                  '''
            return DB.fetchall(sql, (f'%{keyword}%',))
        else:
            sql = '''
                  SELECT tname, \
                         pno, \
                         name, \
                         birthday, \
                         position, \
                         height, \
                         weight, \
                         education
                  FROM player
                  ORDER BY tname \
                  '''
            return DB.fetchall(sql)

    @staticmethod
    def get_players_by_team(tName, keyword=None):
        if keyword:
            sql = '''
                SELECT pno, name, position, height, weight, education
                FROM player
                WHERE tname = %s AND name ILIKE %s
                ORDER BY pno
            '''
            return DB.fetchall(sql, (tName, f'%{keyword}%',))
        else:
            sql = '''
                SELECT pno, name, position, height, weight, education
                FROM player
                WHERE tname = %s
                ORDER BY pno
            '''
            return DB.fetchall(sql, (tName,))

    @staticmethod
    def get_player(tName, pNo):
        sql = '''
            SELECT tname, pno, name, birthday, height, weight, education, position
            FROM player
            WHERE tname = %s AND pno = %s
        '''
        return DB.fetchone(sql, (tName, pNo))

    @staticmethod
    def add_player(data):
        sql = '''
            INSERT INTO player (tname, pno, name, birthday, position, height, weight, education)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        '''
        DB.execute_input(sql, (
            data['tName'], data['pNo'], data['name'], data['birthday'],
            data['position'], data['height'], data['weight'], data['education']
        ))

    @staticmethod
    def update_player(input_data):
        def safe_date(value):
            return value if value not in (None, '', 'None') else None

        sql = '''
              UPDATE player
              SET name      = %s,
                  birthday  = %s,
                  position  = %s,
                  height    = %s,
                  weight    = %s,
                  education = %s
              WHERE tname = %s \
                AND pno = %s \
              '''
        DB.execute_input(sql, (
            input_data['name'],
            safe_date(input_data['birthday']),  # ✅ 處理空生日
            input_data['position'],
            input_data['height'],
            input_data['weight'],
            input_data['education'],
            input_data['tName'],
            input_data['pNo']
        ))

    @staticmethod
    def delete_player(pNo):
        sql = "DELETE FROM player WHERE pno = %s"
        DB.execute_input(sql, (pNo,))

    @staticmethod
    def search_players(team=None, keyword=None, position=None):
        sql = '''
            SELECT tname, pno, name, position, height, weight, education
            FROM player
            WHERE 1=1
        '''
        params = []
        if team:
            sql += " AND tname ILIKE %s"
            params.append(f'%{team}%')
        if keyword:
            sql += " AND name ILIKE %s"
            params.append(f'%{keyword}%')
        if position:
            sql += " AND position ILIKE %s"
            params.append(f'%{position}%')

        sql += " ORDER BY tname"
        return DB.fetchall(sql, tuple(params))


# -------------------------------
# Coach 教練管理
# -------------------------------
class Coach:
    @staticmethod
    def get_all_coaches():
        sql = '''
            SELECT cno, cname, birthday, tname
            FROM coach
            ORDER BY tname
        '''
        return DB.fetchall(sql)

    @staticmethod
    def get_coach(cNo):
        sql = '''
            SELECT cno, cname, birthday, tname
            FROM coach
            WHERE cno = %s
        '''
        return DB.fetchone(sql, (cNo,))

    @staticmethod
    def add_coach(data):
        sql = '''
            INSERT INTO coach (cno, cname, birthday, tname)
            VALUES (%s, %s, %s, %s)
        '''
        DB.execute_input(sql, (
            data['cNo'], data['cName'], data['birthday'], data['tName']
        ))

    @staticmethod
    def update_coach(data):
        sql = '''
            UPDATE coach
            SET cname = %s, birthday = %s, tname = %s
            WHERE cno = %s
        '''
        DB.execute_input(sql, (
            data['cName'], data['birthday'], data['tName'], data['cNo']
        ))

    @staticmethod
    def delete_coach(cNo):
        sql = "DELETE FROM coach WHERE cno = %s"
        DB.execute_input(sql, (cNo,))


# -------------------------------
# Game 賽局管理
# -------------------------------
class Game:
    @staticmethod
    def get_all_games():
        sql = '''
            SELECT winteam, loseteam, date, fname
            FROM game
            ORDER BY date DESC
        '''
        return DB.fetchall(sql)

    @staticmethod
    def get_more_info(winTeam, loseTeam, date):
        sql = '''
              SELECT winteam, loseteam, date, fname, result
              FROM game
              WHERE winteam = %s \
                AND loseteam = %s \
                AND date = %s \
              '''
        return DB.fetchone(sql, (winTeam, loseTeam, date))  # ✅ fetchone

    @staticmethod
    def search_games(team=None, field=None, date=None):
        sql = "SELECT winteam, loseteam, date, fname FROM game WHERE 1=1"
        params = []
        if team:
            sql += " AND (winteam ILIKE %s OR loseteam ILIKE %s)"
            params.extend([f"%{team}%", f"%{team}%"])
        if field:
            sql += " AND fname ILIKE %s"
            params.append(f"%{field}%")
        if date:
            sql += " AND date = %s"
            params.append(date)
        sql += " ORDER BY date DESC"
        return DB.fetchall(sql, tuple(params))

    @staticmethod
    def add_game(data):
        sql = '''
            INSERT INTO game (winteam, loseteam, date, fname, result)
            VALUES (%s, %s, %s, %s, %s)
        '''
        DB.execute_input(sql, (
            data['winTeam'], data['loseTeam'], data['date'], data['fName'], data['result']
        ))

    @staticmethod
    def update_game(data):
        sql = '''
              UPDATE game
              SET winteam  = %s,
                  loseteam = %s,
                  date     = %s,
                  fname    = %s,
                  result   = %s
              WHERE winteam = %s \
                AND loseteam = %s \
                AND date = %s \
              '''
        DB.execute_input(sql, (
            data['winTeam'], data['loseTeam'], data['date'],
            data['fName'], data['result'],
            data['oldWinTeam'], data['oldLoseTeam'], data['oldDate']
        ))

    @staticmethod
    def delete_game(winTeam, loseTeam, date):
        sql = "DELETE FROM game WHERE winteam = %s AND loseteam = %s AND date = %s"
        DB.execute_input(sql, (winTeam, loseTeam, date))

class Field:
    @staticmethod
    def get_all_fields():
        sql = '''
            SELECT fid, fname, address
            FROM field
            ORDER BY fid
        '''
        return DB.fetchall(sql)

    @staticmethod
    def get_field_detail(fId):
        sql = '''
            SELECT fid, fname, address
            FROM field
            WHERE fid = %s
        '''
        return DB.fetchone(sql, (fId,))

    @staticmethod
    def add_field(data):
        sql = '''
            INSERT INTO field (fid, fname, address)
            VALUES (%s, %s, %s)
        '''
        DB.execute_input(sql, (
            data['fId'], data['fName'], data['address']
        ))

    @staticmethod
    def update_field(data):
        sql = '''
            UPDATE field
            SET fname = %s, address = %s
            WHERE fid = %s
        '''
        DB.execute_input(sql, (
            data['fName'], data['address'], data['fId']
        ))

    @staticmethod
    def delete_field(fId):
        sql = "DELETE FROM field WHERE fid = %s"
        DB.execute_input(sql, (fId,))
#--------------------------------------
class TeamRecord:
    """
    球隊戰績功能：
    顯示每隊的勝場、敗場、勝率與勝差
    """
    @staticmethod
    def get_team_records():
        sql = """
        SELECT 
            t.tname AS team_name,
            COALESCE(w.wins, 0) AS wins,
            COALESCE(l.losses, 0) AS losses,
            ROUND(
                COALESCE(
                    w.wins::NUMERIC / NULLIF((COALESCE(w.wins, 0) + COALESCE(l.losses, 0)), 0),
                0),
            3) AS win_rate,
            ROUND(
                ((MAX(COALESCE(w.wins,0)) OVER() - COALESCE(w.wins,0)) 
                 + (COALESCE(l.losses,0) - MIN(COALESCE(l.losses,0)) OVER())) / 2.0,
            1) AS games_behind
        FROM team t
        LEFT JOIN (
            SELECT winteam AS team_name, COUNT(*) AS wins
            FROM game
            WHERE winteam IS NOT NULL
            GROUP BY winteam
        ) w ON t.tname = w.team_name
        LEFT JOIN (
            SELECT loseteam AS team_name, COUNT(*) AS losses
            FROM game
            WHERE loseteam IS NOT NULL
            GROUP BY loseteam
        ) l ON t.tname = l.team_name
        ORDER BY win_rate DESC, wins DESC;
        """
        return DB.fetchall(sql)

