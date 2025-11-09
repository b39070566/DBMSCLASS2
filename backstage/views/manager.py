from flask import Blueprint, render_template, request, url_for, redirect, flash
from flask_login import login_required, current_user
from api.sql import Team, Player, Coach, Game

manager = Blueprint('manager', __name__, template_folder='../templates')


# ========== 首頁重導向 ==========
@manager.route('/')
@login_required
def home():
    if current_user.role != 'manager':
        flash('No permission')
        return redirect(url_for('index'))
    return redirect(url_for('manager.teamManager'))


# ========== 隊伍管理 ==========
@manager.route('/teamManager', methods=['GET', 'POST'])
@login_required
def teamManager():
    if current_user.role != 'manager':
        flash('No permission')
        return redirect(url_for('index'))

    if request.method == 'POST' and 'add' in request.form:
        Team.add_team({
            'tName': request.form.get('tName'),
            'chiefCoach': request.form.get('chiefCoach'),
            'companyName': request.form.get('companyName'),
            'cPhone': request.form.get('cPhone'),
            'cAddress': request.form.get('cAddress'),
            'fName': request.form.get('fName')
        })
        flash('新增成功')
        return redirect(url_for('manager.teamManager'))

    if 'delete' in request.form:
        Team.delete_team(request.form['delete'])
        flash('刪除成功')
        return redirect(url_for('manager.teamManager'))

    if 'edit' in request.form:
        return redirect(url_for('manager.editTeam', tName=request.form['edit']))

    rows = Team.get_all_teams()
    data = [
        {
            'tName': r[0],
            'chiefCoach': r[1],
            'companyName': r[2],
            'cPhone': r[3],
            'cAddress': r[4],
            'fName': r[5]
        } for r in rows
    ]
    return render_template('teamManager.html', team_data=data, user=current_user.name)


@manager.route('/editTeam', methods=['GET', 'POST'])
@login_required
def editTeam():
    tName = request.args.get('tName')
    if request.method == 'POST':
        Team.update_team({
            'tName': tName,
            'chiefCoach': request.form.get('chiefCoach'),
            'companyName': request.form.get('companyName'),
            'cPhone': request.form.get('cPhone'),
            'cAddress': request.form.get('cAddress'),
            'fName': request.form.get('fName')
        })
        flash('修改成功')
        return redirect(url_for('manager.teamManager'))

    r = Team.get_team_detail(tName)
    if r:
        data = {'tName': r[0], 'chiefCoach': r[1], 'companyName': r[2],
                'cPhone': r[3], 'cAddress': r[4], 'fName': r[5]}
    else:
        data = {}
    return render_template('editTeam.html', data=data, user=current_user.name)


# ========== 球員管理 ==========
@manager.route('/playerManager', methods=['GET', 'POST'])
@login_required
def playerManager():
    if current_user.role != 'manager':
        flash('No permission')
        return redirect(url_for('index'))

    # ✅ 新增球員
    if request.method == 'POST' and 'add' in request.form:
        Player.add_player({
            'tName': request.form.get('tName'),
            'pNo': request.form.get('pNo'),
            'name': request.form.get('name'),
            'birthday': request.form.get('birthday') or None,
            'position': request.form.get('position'),
            'height': request.form.get('height'),
            'weight': request.form.get('weight'),
            'education': request.form.get('education')
        })
        flash('球員新增成功')
        return redirect(url_for('manager.playerManager'))

    # ✅ 刪除球員
    if 'delete' in request.form:
        Player.delete_player(request.form['delete'])
        flash('刪除成功')
        return redirect(url_for('manager.playerManager'))

    # ✅ 編輯按鈕 → 轉址帶參數
    if 'edit' in request.form:
        return redirect(url_for('manager.editPlayer',
                                tName=request.form['tName'],
                                pNo=request.form['edit']))

    # ✅ 顯示所有球員
    rows = Player.get_all_players()
    data = [
        {
            'tName': r[0],
            'pNo': r[1],
            'name': r[2],
            'birthday': r[3],
            'position': r[4],
            'height': r[5],
            'weight': r[6],
            'education': r[7]
        } for r in rows
    ]

    # ✅ 給新增表單的隊伍清單（下拉選單用）
    teams = [{'tName': t[0]} for t in Team.get_all_team()]
    return render_template('playerManager.html', player_data=data, team_list=teams, user=current_user.name)


# ========== 編輯球員 ==========
@manager.route('/editPlayer', methods=['GET', 'POST'])
@login_required
def editPlayer():
    tName = request.args.get('tName')
    pNo = request.args.get('pNo')

    # ✅ 更新資料
    if request.method == 'POST':
        Player.update_player({
            'tName': request.form.get('tName'),
            'pNo': pNo,
            'name': request.form.get('name'),
            'birthday': request.form.get('birthday') or None,
            'position': request.form.get('position'),
            'height': request.form.get('height'),
            'weight': request.form.get('weight'),
            'education': request.form.get('education')
        })
        flash('球員修改成功')
        return redirect(url_for('manager.playerManager'))

    # ✅ 撈單筆資料（for edit 頁面）
    row = Player.get_player(tName, pNo)
    if row:
        data = {
            'tName': row[0],
            'pNo': row[1],
            'name': row[2],
            'birthday': row[3],
            'height': row[4],
            'weight': row[5],
            'education': row[6],
            'position': row[7]
        }
    else:
        data = {}

    # ✅ 下拉選單顯示全部隊伍
    teams = [{'tName': t[0]} for t in Team.get_all_team()]
    return render_template('editPlayer.html', data=data, team_list=teams, user=current_user.name)






# ========== 教練管理 ==========
@manager.route('/coachManager', methods=['GET', 'POST'])
@login_required
def coachManager():
    if current_user.role != 'manager':
        flash('No permission')
        return redirect(url_for('index'))

    if request.method == 'POST' and 'add' in request.form:
        Coach.add_coach({
            'cNo': request.form.get('cNo'),
            'cName': request.form.get('cName'),
            'birthday': request.form.get('birthday'),
            'tName': request.form.get('tName')
        })
        flash('教練新增成功')
        return redirect(url_for('manager.coachManager'))

    if 'delete' in request.form:
        Coach.delete_coach(request.form['delete'])
        flash('刪除成功')
        return redirect(url_for('manager.coachManager'))

    if 'edit' in request.form:
        return redirect(url_for('manager.editCoach', cNo=request.form['edit']))

    rows = Coach.get_all_coaches()
    data = [{'cNo': r[0], 'cName': r[1], 'birthday': r[2], 'tName': r[3]} for r in rows]
    return render_template('coachManager.html', coach_data=data, user=current_user.name)


@manager.route('/editCoach', methods=['GET', 'POST'])
@login_required
def editCoach():
    cNo = request.args.get('cNo')
    if request.method == 'POST':
        Coach.update_coach({
            'cNo': cNo,
            'cName': request.form.get('cName'),
            'birthday': request.form.get('birthday'),
            'tName': request.form.get('tName')
        })
        flash('教練修改成功')
        return redirect(url_for('manager.coachManager'))

    r = Coach.get_coach(cNo)
    data = {'cNo': r[0], 'cName': r[1], 'birthday': r[2], 'tName': r[3]} if r else {}
    return render_template('editCoach.html', data=data, user=current_user.name)


# ========== 賽局管理 ==========
@manager.route('/gameManager', methods=['GET', 'POST'])
@login_required
def gameManager():
    if current_user.role != 'manager':
        flash('No permission')
        return redirect(url_for('index'))

    if request.method == 'POST' and 'add' in request.form:
        Game.add_game({
            'winTeam': request.form.get('winTeam'),
            'loseTeam': request.form.get('loseTeam'),
            'date': request.form.get('date'),
            'fName': request.form.get('fName'),
            'result': request.form.get('result')
        })
        flash('賽局新增成功')
        return redirect(url_for('manager.gameManager'))

    if 'delete' in request.form:
        parts = request.form['delete'].split('|')
        if len(parts) == 3:
            Game.delete_game(parts[0], parts[1], parts[2])
            flash('刪除成功')
        else:
            flash('刪除參數錯誤')
        return redirect(url_for('manager.gameManager'))

    if 'edit' in request.form:
        parts = request.form['edit'].split('|')
        if len(parts) == 3:
            return redirect(url_for('manager.editGame',
                                    winTeam=parts[0],
                                    loseTeam=parts[1],
                                    date=parts[2]))

    rows = Game.get_all_games()
    data = [
        {'winTeam': r[0], 'loseTeam': r[1], 'date': r[2], 'fName': r[3]}
        for r in rows
    ]
    return render_template('gameManager.html', game_data=data, user=current_user.name)


@manager.route('/editGame', methods=['GET', 'POST'])
@login_required
def editGame():
    oldWinTeam = request.args.get('winTeam')
    oldLoseTeam = request.args.get('loseTeam')
    oldDate = request.args.get('date')

    if request.method == 'POST':
        Game.update_game({
            'winTeam': request.form.get('winTeam'),
            'loseTeam': request.form.get('loseTeam'),
            'date': request.form.get('date'),
            'fName': request.form.get('fName'),
            'result': request.form.get('result'),
            'oldWinTeam': oldWinTeam,
            'oldLoseTeam': oldLoseTeam,
            'oldDate': oldDate
        })
        flash('賽局修改成功')
        return redirect(url_for('manager.gameManager'))

    data = Game.get_more_info(oldWinTeam, oldLoseTeam, oldDate)
    if data:
        game_info = {
            'winTeam': data[0],
            'loseTeam': data[1],
            'date': data[2],
            'fName': data[3],
            'result': data[4]
        }
    else:
        flash('查無資料')
        return redirect(url_for('manager.gameManager'))

    return render_template('editGame.html', data=game_info, user=current_user.name)
