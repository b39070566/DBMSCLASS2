from flask import Blueprint, request, jsonify
from link import get_db

team_api = Blueprint('team_api', __name__)

# 查詢所有隊伍資料
@team_api.route('/teams', methods=['GET'])
def get_teams():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT t.tID, t.tName, c.coachName, t.companyName, t.cPhone, 
               t.cAddress, f.fName, t.win, t.lose, t.totalScore
        FROM team t
        LEFT JOIN coach c ON t.chiefCoach = c.coachID
        LEFT JOIN field f ON t.fName = f.fName
    """)
    teams = cursor.fetchall()
    return jsonify(teams)

# 新增隊伍
@team_api.route('/teams', methods=['POST'])
def add_team():
    data = request.json
    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        INSERT INTO team (tName, chiefCoach, companyName, cPhone, cAddress, fName)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (data['tName'], data['chiefCoach'], data['companyName'], 
          data['cPhone'], data['cAddress'], data['fName']))
    db.commit()
    return jsonify({"message": "Team added successfully"})

# 更新隊伍
@team_api.route('/teams/<int:tID>', methods=['PUT'])
def update_team(tID):
    data = request.json
    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        UPDATE team SET tName=%s, chiefCoach=%s, companyName=%s,
            cPhone=%s, cAddress=%s, fName=%s
        WHERE tID=%s
    """, (data['tName'], data['chiefCoach'], data['companyName'],
          data['cPhone'], data['cAddress'], data['fName'], tID))
    db.commit()
    return jsonify({"message": "Team updated successfully"})

# 刪除隊伍
@team_api.route('/teams/<int:tID>', methods=['DELETE'])
def delete_team(tID):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("DELETE FROM team WHERE tID = %s", (tID,))
    db.commit()
    return jsonify({"message": "Team deleted"})
