# api/sql.py  —  SQLite 版本（本地 db2025class）
import os
import sqlite3
from dotenv import load_dotenv

# 載入 .env，可選；DB_PATH 預設為 'db2025class'（可無副檔名）
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))
DB_PATH = os.getenv('db2025class', 'db2025class')

# 建立單一連線（開發用）；若日後要更穩定可改成每請求/每次操作新建 cursor
_connection = sqlite3.connect(DB_PATH, check_same_thread=False)
# 若想用 dict-like row，可開啟下行：
# _connection.row_factory = sqlite3.Row
_connection.execute("PRAGMA foreign_keys = ON;")

class DB:
    @staticmethod
    def connect():
        return _connection

    @staticmethod
    def release(_conn):
        # 單一連線模式無需釋放
        pass

    @staticmethod
    def execute_input(sql, params):
        if not isinstance(params, (tuple, list)):
            raise TypeError(f"Input should be a tuple or list, got: {type(params).__name__}")
        conn = DB.connect()
        cur = conn.cursor()
        try:
            cur.execute(sql, params)
            conn.commit()
        except sqlite3.Error as e:
            conn.rollback()
            print(f"Error executing SQL: {e}")
            raise
        finally:
            cur.close()

    @staticmethod
    def execute(sql):
        conn = DB.connect()
        cur = conn.cursor()
        try:
            cur.execute(sql)
            conn.commit()
        except sqlite3.Error as e:
            conn.rollback()
            print(f"Error executing SQL: {e}")
            raise
        finally:
            cur.close()

    @staticmethod
    def fetchall(sql, params=None):
        conn = DB.connect()
        cur = conn.cursor()
        try:
            if params is None:
                cur.execute(sql)
            else:
                cur.execute(sql, params)
            return cur.fetchall()
        except sqlite3.Error as e:
            print(f"Error fetching data: {e}")
            raise
        finally:
            cur.close()

    @staticmethod
    def fetchone(sql, params=None):
        conn = DB.connect()
        cur = conn.cursor()
        try:
            if params is None:
                cur.execute(sql)
            else:
                cur.execute(sql, params)
            return cur.fetchone()
        except sqlite3.Error as e:
            print(f"Error fetching data: {e}")
            raise
        finally:
            cur.close()


# ========= Helper =========
def _next_tno():
    """模擬 PG 的序列：取 cart.tno 的下一號"""
    row = DB.fetchone("SELECT COALESCE(MAX(tno), 0) + 1 FROM cart")
    return row[0] if row else 1


# ========= Tables =========
class Member:
    @staticmethod
    def get_member(account):
        sql = '''SELECT account, password, mid, identity, (lname || fname) AS name FROM member WHERE account = ?'''
        return DB.fetchall(sql, (account,))

    @staticmethod
    def get_all_account():
        sql = "SELECT account FROM member"
        return DB.fetchall(sql)

    @staticmethod
    def create_member(input_data):
        # 注意欄位名稱需與實際表一致；若不是 name/account/password/identity，請改成你的實際欄位
        sql = 'INSERT INTO member (lname,fname, account, password, identity) VALUES (?, ?, ?, ?, ?)'
        DB.execute_input(sql, (
            input_data['lname'],
            input_data['fname'],
            input_data['account'],
            input_data['password'],
            input_data['identity']
        ))

    @staticmethod
    def delete_product(tno, pid):
        sql = 'DELETE FROM record WHERE tno = ? AND pid = ?'
        DB.execute_input(sql, (tno, pid))

    @staticmethod
    def get_order(userid):
        sql = 'SELECT * FROM order_list WHERE mid = ? ORDER BY ordertime DESC'
        return DB.fetchall(sql, (userid,))

    @staticmethod
    def get_role(userid):
        sql = 'SELECT identity, (lname || fname) AS name FROM member WHERE mid = ?'
        return DB.fetchone(sql, (userid,))


class Cart:
    @staticmethod
    def check(user_id):
        sql = '''
        SELECT *
        FROM cart
        JOIN record ON cart.tno = record.tno
        WHERE cart.mid = ?
        LIMIT 1
        '''
        return DB.fetchone(sql, (user_id,))

    @staticmethod
    def get_cart(user_id):
        sql = 'SELECT * FROM cart WHERE mid = ?'
        return DB.fetchone(sql, (user_id,))

    @staticmethod
    def add_cart(user_id, time):
        # PG: nextval('cart_tno_seq') → SQLite: 用 MAX(tno)+1 模擬
        new_tno = _next_tno()
        sql = 'INSERT INTO cart (mid, carttime, tno) VALUES (?, ?, ?)'
        DB.execute_input(sql, (user_id, time, new_tno))

    @staticmethod
    def clear_cart(user_id):
        sql = 'DELETE FROM cart WHERE mid = ?'
        DB.execute_input(sql, (user_id,))


class Product:
    @staticmethod
    def count():
        sql = 'SELECT COUNT(*) FROM product'
        return DB.fetchone(sql)

    @staticmethod
    def get_product(pid):
        sql = 'SELECT * FROM product WHERE pid = ?'
        return DB.fetchone(sql, (pid,))

    @staticmethod
    def get_all_product():
        sql = 'SELECT * FROM product'
        return DB.fetchall(sql)

    @staticmethod
    def get_name(pid):
        sql = 'SELECT pname FROM product WHERE pid = ?'
        row = DB.fetchone(sql, (pid,))
        return row[0] if row else None

    @staticmethod
    def add_product(input_data):
        sql = 'INSERT INTO product (pid, pname, price, category, pdesc) VALUES (?, ?, ?, ?, ?)'
        DB.execute_input(sql, (
            input_data['pid'],
            input_data['pname'],
            input_data['price'],
            input_data['category'],
            input_data['pdesc']
        ))

    @staticmethod
    def delete_product(pid):
        sql = 'DELETE FROM product WHERE pid = ?'
        DB.execute_input(sql, (pid,))

    @staticmethod
    def update_product(input_data):
        sql = 'UPDATE product SET pname = ?, price = ?, category = ?, pdesc = ? WHERE pid = ?'
        DB.execute_input(sql, (
            input_data['pname'],
            input_data['price'],
            input_data['category'],
            input_data['pdesc'],
            input_data['pid']
        ))


class Record:
    @staticmethod
    def get_total_money(tno):
        sql = 'SELECT SUM(total) FROM record WHERE tno = ?'
        row = DB.fetchone(sql, (tno,))
        return row[0] if row else None

    @staticmethod
    def check_product(pid, tno):
        sql = 'SELECT * FROM record WHERE pid = ? AND tno = ?'
        return DB.fetchone(sql, (pid, tno))

    @staticmethod
    def get_price(pid):
        sql = 'SELECT price FROM product WHERE pid = ?'
        row = DB.fetchone(sql, (pid,))
        return row[0] if row else None

    @staticmethod
    def add_product(input_data):
        sql = 'INSERT INTO record (pid, tno, amount, saleprice, total) VALUES (?, ?, 1, ?, ?)'
        DB.execute_input(sql, (
            input_data['pid'],
            input_data['tno'],
            input_data['saleprice'],
            input_data['total']
        ))

    @staticmethod
    def get_record(tno):
        sql = 'SELECT * FROM record WHERE tno = ?'
        return DB.fetchall(sql, (tno,))

    @staticmethod
    def get_amount(tno, pid):
        sql = 'SELECT amount FROM record WHERE tno = ? AND pid = ?'
        row = DB.fetchone(sql, (tno, pid))
        return row[0] if row else None

    @staticmethod
    def update_product(input_data):
        sql = 'UPDATE record SET amount = ?, total = ? WHERE pid = ? AND tno = ?'
        DB.execute_input(sql, (
            input_data['amount'],
            input_data['total'],
            input_data['pid'],
            input_data['tno']
        ))

    @staticmethod
    def delete_check(pid):
        sql = 'SELECT * FROM record WHERE pid = ?'
        return DB.fetchone(sql, (pid,))

    @staticmethod
    def get_total(tno):
        sql = 'SELECT SUM(total) FROM record WHERE tno = ?'
        row = DB.fetchone(sql, (tno,))
        return row[0] if row else None


class Order_List:
    @staticmethod
    def add_order(input_data):
        # PG 的 DEFAULT OID + TO_TIMESTAMP(format) 改為：
        # - 假設 ordertime 是已格式化好的字串，直接入庫
        sql = 'INSERT INTO order_list (mid, ordertime, price, tno) VALUES (?, ?, ?, ?)'
        DB.execute_input(sql, (
            input_data['mid'],
            input_data['ordertime'],   # e.g. '2025-10-16 13:45:00'
            input_data['total'],
            input_data['tno']
        ))

    @staticmethod
    def get_order():
        # 避免 NATURAL JOIN 的隱式欄位匹配，改成明確 JOIN
        sql = '''
        SELECT o.oid, ("m.lName" || "m.fName") AS name, o.price, o.ordertime
        FROM order_list o
        JOIN member m ON o.mid = m.mid
        ORDER BY o.ordertime DESC
        '''
        return DB.fetchall(sql)

    @staticmethod
    def get_orderdetail():
        sql = '''
        SELECT o.oid, p.pname, r.saleprice, r.amount
        FROM order_list o
        JOIN record r ON o.tno = r.tno
        JOIN product p ON r.pid = p.pid
        '''
        return DB.fetchall(sql)


class Analysis:
    @staticmethod
    def month_price(i):
        # EXTRACT(MONTH ...) → strftime('%m', ...)；i 應為 '01'~'12' 或 int 1~12
        # 為避免 '1' / '01' 差異，統一轉為兩位數字字串
        month_str = f"{int(i):02d}"
        sql = '''
        SELECT strftime('%m', ordertime) AS mon, SUM(price)
        FROM order_list
        WHERE strftime('%m', ordertime) = ?
        GROUP BY mon
        '''
        return DB.fetchall(sql, (month_str,))

    @staticmethod
    def month_count(i):
        month_str = f"{int(i):02d}"
        sql = '''
        SELECT strftime('%m', ordertime) AS mon, COUNT(oid)
        FROM order_list
        WHERE strftime('%m', ordertime) = ?
        GROUP BY mon
        '''
        return DB.fetchall(sql, (month_str,))

    @staticmethod
    def category_sale():
        sql = '''
        SELECT SUM(total), category
        FROM product
        JOIN record ON product.pid = record.pid
        GROUP BY category
        '''
        return DB.fetchall(sql)

    @staticmethod
    def member_sale():
        sql = '''
        SELECT SUM(price), member.mid, (lname || fname) AS name
        FROM order_list
        JOIN member ON order_list.mid = member.mid
        WHERE member.identity = ?
        GROUP BY member.mid, member.lname, member.fname
        ORDER BY SUM(price) DESC
        '''
        return DB.fetchall(sql, ('user',))

    @staticmethod
    def member_sale_count():
        sql = '''
        SELECT COUNT(*), member.mid, (lname || fname) AS name
        FROM order_list
        JOIN member ON order_list.mid = member.mid
        WHERE member.identity = ?
        GROUP BY member.mid, member.lname, member.fname
        ORDER BY COUNT(*) DESC
        '''
        return DB.fetchall(sql, ('user',))
