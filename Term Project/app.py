from flask import Flask, render_template, request, redirect, session
import psycopg2
import os
import random

connect = psycopg2.connect("host=localhost dbname=postgres port=5432 user=postgres password=workit0ut_")
cur = connect.cursor()

file = open("Movie.sql", "r")
sqlfile = file.read()
cur.execute(sqlfile)
connect.commit()
file.close()
# if your PSQL has no data from movie.sql, then run this.

app = Flask(__name__)
app.secret_key = os.urandom(20)
# using session, keep secret key.


@app.route('/')
def main():
    userid = session.get('userid', None)
    return render_template("main.html", userid=userid)
# two version of main: login or not

@app.route('/board', methods=['GET', 'POST'])
def board():
    userid = session.get('userid', None)

    cur.execute("SELECT distinct genre.name FROM movie, genre, genre_movie WHERE "
                "genre.id = genre_movie.genre_id AND genre_movie.movie_id = movie.id;")
    genre_list = cur.fetchall()

    cur.execute(
        "SELECT movie.id, movie.title, movie.year, movie.score, movie.running_time, movie.rating, country.country_name, genre.name "
        "FROM movie, country join country_movie on (country.id = country_movie.country_id),"
        "genre join genre_movie on (genre.id = genre_movie.genre_id) "
        "WHERE country_movie.movie_id = movie.id AND "
        "genre_movie.movie_id = movie.id ORDER BY movie.score DESC;")

    movie_list = cur.fetchall()
    movie_info = {}

    for item in movie_list:
        movie_info[item[0]] = [[], [], [], [], [], [], []]

    for item in movie_list:
        movie_info[item[0]][0] = item[1]
        movie_info[item[0]][1] = item[2]
        movie_info[item[0]][2] = item[3]
        movie_info[item[0]][3] = item[4]
        movie_info[item[0]][4] = item[5]
        if not item[6] in movie_info[item[0]][5]: movie_info[item[0]][5].append(item[6])
        if not item[7] in movie_info[item[0]][6]: movie_info[item[0]][6].append(item[7])


    if request.method == 'GET':

        return render_template("board.html", movie_id=movie_info.keys(), movie_list=movie_info, rank='score', userid=userid, genre='all', genre_list=genre_list)

    else:

        if request.form.get('clear'):
            session.pop('search', '')
            session.pop('search_type', None)
            session.pop('rank', None)
            session.pop('genre', '')
            return redirect('/board')

        # session has prior info(search, search_type, rank, genre). clear those and redirect itself.

        search = request.form.get('search')
        if search:
            session['search'] = search
        else:
            search = session.get('search', '')

        search_type = request.form.get('search_type')
        if search_type:
            session['search_type'] = search_type
        else:
            search_type = session.get('search_type', 'title')

        rank = request.form.get('rank')
        if rank:
            session['rank'] = rank
        else:
            rank = session.get('rank', 'score')
        if rank == 'time': rank = 'running_time'

        genre = request.form.get('genre')
        if genre:
            session['genre'] = genre
        else:
            genre = session.get('genre', 'all')
        print(type(genre))
        if genre == 'all': genre = ''

        # four criteria: (1). search: text data correspondent to db (2). search_type: title, director, writer, actor (3). genre: matching genre (4). rank: if data, ordered by this rank.
        # i.e. given searched data, filter those and order.

        if rank != 'mypick':

            if search_type == 'title':
                cur.execute(
                    "WITH genre_selected AS (SELECT movie.id AS genre_selected_id FROM movie, genre, genre_movie WHERE "
                    "movie.id = genre_movie.movie_id AND genre.id = genre_movie.genre_id AND genre.name LIKE '{}' ) "
                    "SELECT movie.id, movie.title, movie.year, movie.score, movie.running_time, movie.rating, country.country_name, genre.name "
                    "FROM movie, country join country_movie on (country.id = country_movie.country_id), "
                    "genre, genre_movie, genre_selected "
                    "WHERE country_movie.movie_id = movie.id AND genre_movie.movie_id = movie.id AND genre_movie.genre_id = genre.id AND movie.id = genre_selected.genre_selected_id AND "
                    "movie.title LIKE '{}' ORDER BY {} DESC;".format('%'+genre+'%', '%' + search + '%', rank))


            elif search_type == 'director':
                cur.execute(
                    "WITH genre_selected AS (SELECT movie.id AS genre_selected_id FROM movie, genre, genre_movie WHERE "
                    "movie.id = genre_movie.movie_id AND genre.id = genre_movie.genre_id AND genre.name LIKE '{}' ) "
                    "SELECT movie.id, movie.title, movie.year, movie.score, movie.running_time, movie.rating, country.country_name, genre.name "
                    "FROM movie, country join country_movie on (country.id = country_movie.country_id), "
                    "genre, genre_movie, genre_selected "
                    "WHERE country_movie.movie_id = movie.id AND genre_movie.movie_id = movie.id AND genre_movie.genre_id = genre.id AND movie.id = genre_selected.genre_selected_id AND "
                    "movie.id in (SELECT makes.movie_id FROM makes, director WHERE makes.director_id = director.id AND "
                    "director.name LIKE '{}') ORDER BY {} DESC;".format('%'+genre+'%', '%' + search + '%', rank))

            elif search_type == 'writer':
                cur.execute(
                    "WITH genre_selected AS (SELECT movie.id AS genre_selected_id FROM movie, genre, genre_movie WHERE "
                    "movie.id = genre_movie.movie_id AND genre.id = genre_movie.genre_id AND genre.name LIKE '{}' ) "
                    "SELECT movie.id, movie.title, movie.year, movie.score, movie.running_time, movie.rating, country.country_name, genre.name "
                    "FROM movie, country join country_movie on (country.id = country_movie.country_id), "
                    "genre, genre_movie, genre_selected "
                    "WHERE country_movie.movie_id = movie.id AND genre_movie.movie_id = movie.id AND genre_movie.genre_id = genre.id AND movie.id = genre_selected.genre_selected_id AND "
                    "movie.id in (SELECT writes.movie_id FROM writes, writer WHERE writes.writer_id = writer.id AND "
                    "writer.name LIKE '{}') ORDER BY {} DESC;".format('%'+genre+'%', '%' + search + '%', rank))

            else:
                cur.execute(
                    "WITH genre_selected AS (SELECT movie.id AS genre_selected_id FROM movie, genre, genre_movie WHERE "
                    "movie.id = genre_movie.movie_id AND genre.id = genre_movie.genre_id AND genre.name LIKE '{}' ) "
                    "SELECT movie.id, movie.title, movie.year, movie.score, movie.running_time, movie.rating, country.country_name, genre.name "
                    "FROM movie, country join country_movie on (country.id = country_movie.country_id), "
                    "genre, genre_movie, genre_selected "
                    "WHERE country_movie.movie_id = movie.id AND genre_movie.movie_id = movie.id AND genre_movie.genre_id = genre.id AND movie.id = genre_selected.genre_selected_id AND "
                    "movie.id in (SELECT plays.movie_id FROM plays, actor WHERE plays.actor_id = actor.id AND "
                    "actor.name LIKE '{}') ORDER BY {} DESC;".format('%'+genre+'%', '%' + search + '%', rank))

        elif rank == 'mypick':

            if search_type == 'title':
                cur.execute(
                    "WITH genre_selected AS (SELECT movie.id AS genre_selected_id FROM movie, genre, genre_movie WHERE "
                    "movie.id = genre_movie.movie_id AND genre.id = genre_movie.genre_id AND genre.name LIKE '{}' ) "
                    "SELECT movie.id, movie.title, movie.year, users_pick.score, movie.running_time, movie.rating, country.country_name, genre.name "
                    "FROM movie, country join country_movie on (country.id = country_movie.country_id), "
                    "genre, genre_movie, genre_selected, users_pick "
                    "WHERE country_movie.movie_id = movie.id AND genre_movie.movie_id = movie.id AND genre_movie.genre_id = genre.id AND movie.id = genre_selected.genre_selected_id AND "
                    "users_pick.movie_id = movie.id AND users_pick.user_id = '{}' AND "
                    "movie.title LIKE '{}' ORDER BY users_pick.score DESC;".format('%'+genre+'%', userid,
                                                                                   '%' + search + '%'))

            elif search_type == 'director':
                cur.execute(
                    "WITH genre_selected AS (SELECT movie.id AS genre_selected_id FROM movie, genre, genre_movie WHERE "
                    "movie.id = genre_movie.movie_id AND genre.id = genre_movie.genre_id AND genre.name LIKE '{}' ) "
                    "SELECT movie.id, movie.title, movie.year, users_pick.score, movie.running_time, movie.rating, country.country_name, genre.name "
                    "FROM movie, country join country_movie on (country.id = country_movie.country_id), "
                    "genre, genre_movie, genre_selected, users_pick "
                    "WHERE country_movie.movie_id = movie.id AND genre_movie.movie_id = movie.id AND genre_movie.genre_id = genre.id AND movie.id = genre_selected.genre_selected_id AND "
                    "users_pick.movie_id = movie.id AND users_pick.user_id = '{}' AND "
                    "movie.id in (SELECT makes.movie_id FROM makes, director WHERE makes.director_id = director.id AND "
                    "director.name LIKE '{}') ORDER BY users_pick.score;".format('%'+genre+'%', userid,
                                                                                 '%' + search + '%'))

            elif search_type == 'writer':
                cur.execute(
                    "WITH genre_selected AS (SELECT movie.id AS genre_selected_id FROM movie, genre, genre_movie WHERE "
                    "movie.id = genre_movie.movie_id AND genre.id = genre_movie.genre_id AND genre.name LIKE '{}' ) "
                    "SELECT movie.id, movie.title, movie.year, users_pick.score, movie.running_time, movie.rating, country.country_name, genre.name "
                    "FROM movie, country join country_movie on (country.id = country_movie.country_id), "
                    "genre, genre_movie, genre_selected, users_pick "
                    "WHERE country_movie.movie_id = movie.id AND genre_movie.movie_id = movie.id AND genre_movie.genre_id = genre.id AND movie.id = genre_selected.genre_selected_id AND "
                    "users_pick.movie_id = movie.id AND users_pick.user_id = '{}' AND "
                    "movie.id in (SELECT writes.movie_id FROM writes, writer WHERE writes.writer_id = writer.id AND "
                    "writer.name LIKE '{}') ORDER BY users_pick.score;".format('%'+genre+'%', userid,
                                                                               '%' + search + '%'))

            else:
                cur.execute(
                    "WITH genre_selected AS (SELECT movie.id AS genre_selected_id FROM movie, genre, genre_movie WHERE "
                    "movie.id = genre_movie.movie_id AND genre.id = genre_movie.genre_id AND genre.name LIKE '{}' ) "
                    "SELECT movie.id, movie.title, movie.year, users_pick.score, movie.running_time, movie.rating, country.country_name, genre.name "
                    "FROM movie, country join country_movie on (country.id = country_movie.country_id), "
                    "genre, genre_movie, genre_selected, users_pick "
                    "WHERE country_movie.movie_id = movie.id AND genre_movie.movie_id = movie.id AND genre_movie.genre_id = genre.id AND movie.id = genre_selected.genre_selected_id AND "
                    "users_pick.movie_id = movie.id AND users_pick.user_id = '{}' AND "
                    "movie.id in (SELECT plays.movie_id FROM plays, actor WHERE plays.actor_id = actor.id AND "
                    "actor.name LIKE '{}') ORDER BY users_pick.score;".format('%'+genre+'%', userid,
                                                                              '%' + search + '%'))
        print(rank)

        movie_list = cur.fetchall()
        movie_info = {}

        for item in movie_list:
            movie_info[item[0]] = [[], [], [], [], [], [], []]

        for item in movie_list:
            movie_info[item[0]][0] = item[1]
            movie_info[item[0]][1] = item[2]
            movie_info[item[0]][2] = item[3]
            movie_info[item[0]][3] = item[4]
            movie_info[item[0]][4] = item[5]
            if not item[6] in movie_info[item[0]][5]: movie_info[item[0]][5].append(item[6])
            if not item[7] in movie_info[item[0]][6]: movie_info[item[0]][6].append(item[7])

        return render_template("board.html", movie_id=movie_info.keys(), movie_list=movie_info, rank=rank, userid=userid, search=search, search_type=search_type, genre=genre, genre_list=genre_list)

@app.route('/board/movie/<int:movie_id>/', methods=['GET', 'POST'])
def movie(movie_id):
    userid = session.get('userid', None)
    scoremsg = None

    if request.method == 'POST':
        score = request.form.get('score')
        try:
            float(score)
            score = float(score)
            scoremsg = 'Success'
        except ValueError:
            scoremsg = 'Fail'

        # check if score is number

        if scoremsg == 'Success' and (score<0 or score>=10):
            scoremsg='Fail'

        # score boundary

        if scoremsg == 'Success':
            cur.execute("INSERT INTO users_pick (user_id, movie_id, score) VALUES ('{}', '{}', '{}') "
                        "ON CONFLICT (user_id, movie_id) DO UPDATE SET score = '{}';"
                        .format(userid, movie_id, score, score))
            connect.commit()

    cur.execute("SELECT * FROM movie WHERE id = '{}';".format(movie_id))
    movie = cur.fetchall()

    cur.execute("SELECT country.country_name FROM country join country_movie ON country.id = country_movie.country_id WHERE country_movie.movie_id = '{}';".format(movie_id))
    country = cur.fetchall()

    cur.execute("SELECT genre.name FROM genre join genre_movie ON genre.id = genre_movie.genre_id WHERE genre_movie.movie_id = '{}';".format(movie_id))
    genre = cur.fetchall()

    cur.execute("SELECT director.name FROM director, makes WHERE director.id = makes.director_id AND makes.movie_id = '{}';".format(movie_id))
    director = cur.fetchall()

    cur.execute("SELECT writer.name FROM writer, writes WHERE writer.id = writes.writer_id AND writes.movie_id = '{}';".format(movie_id))
    writer = cur.fetchall()

    cur.execute("SELECT actor.name, plays.role FROM actor, plays WHERE actor.id = plays.actor_id AND plays.movie_id = '{}';".format(movie_id))
    actor = cur.fetchall()

    # movie info gathered

    return render_template("board/movie_detail.html", movie=movie, country=country, genre=genre, director=director, writer=writer, actor=actor, userid=userid, scoremsg=scoremsg)


@app.route('/login', methods=['GET', 'POST'])
def login():

    logmsg = None

    if request.method == 'GET':
        return render_template("login.html", logmsg=None)
    else:

        if request.form.get('main'):
            return redirect('/')

        userid = request.form.get('userid')
        password = request.form.get('password')

        cur.execute("SELECT * FROM users;")
        users = cur.fetchall()

        for user in users:
            if user[0] == userid and user[1] == password:
                session['userid']=userid
                return redirect('/')
            elif user[0] == userid and user[1] != password:
                return render_template("login.html", logmsg='pw_error')
        return render_template("login.html", logmsg='id_error')
        # if user info correct, login.

@app.route('/logout', methods=['GET'])
def logout():
    session.pop('userid', None)
    # Since session has user's id, popped.
    return redirect('/')

@app.route('/register', methods=['GET', 'POST'])
def register():

    regimsg = None

    if request.method == 'GET':
        return render_template("register.html", regimsg=regimsg)
    else:

        if request.form.get('main'):
            return redirect('/')

        userid = request.form.get('userid')
        password = request.form.get('password')
        re_password = request.form.get('re_password')
        age = request.form.get('age')

        if age:
            try:
                age = int(age)
            except ValueError:
                regimsg = 'age_int'
                return render_template("register.html", regimsg=regimsg)

            if (age <= 0 or age > 100):
                regimsg = 'age_invalid'
                return render_template("register.html", regimsg=regimsg)
        else:
            age = 15

        # if age, check boundary

        if not (userid and password and re_password):
            regimsg = 'empty'
            return render_template("register.html", regimsg=regimsg)
        elif (password != re_password):
            regimsg = 'pw_check'
            return render_template("register.html", regimsg=regimsg)
        else:
            cur.execute("INSERT INTO users (id, pw, age) VALUES ('{}', '{}', {});".format(userid, password, age))
            connect.commit()
            regimsg = 'success'
            return render_template("register.html", regimsg=regimsg)
        # if valid, insert new user info to user table

@app.route('/myinfo', methods=['GET', 'POST'])
def myinfo():

    userid = session.get('userid', None)
    deletemsg = None

    if request.method == 'POST':
        title = request.form.get('title')
        cur.execute("SELECT * FROM users_pick WHERE user_id = '{}' AND movie_id = "
                    "(SELECT id FROM movie WHERE title = '{}');".format(userid, title))
        flag = cur.fetchall()
        if flag:
            cur.execute("DELETE FROM users_pick WHERE user_id = '{}' AND movie_id = "
                    "(SELECT id FROM movie WHERE title = '{}');".format(userid, title))
            connect.commit()
            deletemsg = 'Success'
        else:
            deletemsg = 'Fail'
    # delete movie picks


    cur.execute("SELECT id, age FROM users WHERE id = '{}';".format(userid))
    user_info = cur.fetchall()
    #display user's info

    cur.execute("SELECT movie.id, movie.title, users_pick.score, country.country_name, genre.name "
                "FROM movie join users_pick on (movie.id = users_pick.movie_id),"
                "country join country_movie on (country.id = country_movie.country_id),"
                "genre join genre_movie on (genre.id = genre_movie.genre_id) "
                "WHERE users_pick.user_id = '{}' AND country_movie.movie_id = movie.id AND "
                "genre_movie.movie_id = movie.id;".format(userid))
    users_pick = cur.fetchall()
    users_info = {}
    # display what you have picked


    for item in users_pick:
        users_info[item[0]] = [[], [], [], []]

    for item in users_pick:
        if item[1] not in users_info[item[0]][0]: users_info[item[0]][0].append(item[1])
        if item[2] not in users_info[item[0]][1]: users_info[item[0]][1].append(item[2])
        if item[3] not in users_info[item[0]][2]: users_info[item[0]][2].append(item[3])
        if item[4] not in users_info[item[0]][3]: users_info[item[0]][3].append(item[4])

    cur.execute("SELECT genre.name, count(*) as num_genre"
                " FROM movie, users_pick, genre, genre_movie"
                " WHERE movie.id = users_pick.movie_id AND"
                " users_pick.user_id = '{}' AND"
                " genre.id = genre_movie.genre_id AND"
                " genre_movie.movie_id = movie.id GROUP BY genre.name ORDER BY num_genre DESC;".format(userid))
    genre_info = cur.fetchall()
    total_count = len(users_info)

    if genre_info:
        genre_fav = genre_info[0][0]
        cur.execute("SELECT id FROM movie WHERE id IN (SELECT genre_movie.movie_id FROM genre, genre_movie WHERE "
                "genre_movie.genre_id = genre.id AND genre.name = '{}') "
                "AND id NOT IN (SELECT movie_id FROM users_pick WHERE user_id = '{}');".format(genre_fav, userid))
        movie_ids = cur.fetchall()
        movie_id = random.sample(movie_ids, 1)
        movie_id = movie_id[0][0]

        cur.execute("SELECT * FROM movie WHERE id = {};".format(movie_id))
        movie = cur.fetchall()

        cur.execute("SELECT country.country_name FROM country join country_movie ON country.id = country_movie.country_id WHERE country_movie.movie_id = {};".format(movie_id))
        country = cur.fetchall()

        cur.execute("SELECT genre.name FROM genre join genre_movie ON genre.id = genre_movie.genre_id WHERE genre_movie.movie_id = {};".format(movie_id))
        genre = cur.fetchall()

        cur.execute("SELECT director.name FROM director, makes WHERE director.id = makes.director_id AND makes.movie_id = {};".format(movie_id))
        director = cur.fetchall()

        cur.execute("SELECT writer.name FROM writer, writes WHERE writer.id = writes.writer_id AND writes.movie_id = {};".format(movie_id))
        writer = cur.fetchall()

        cur.execute("SELECT actor.name, plays.role FROM actor, plays WHERE actor.id = plays.actor_id AND plays.movie_id = {};".format(movie_id))
        actor = cur.fetchall()
        return render_template("myinfo.html", userid=userid, user_info=user_info, users_pick = users_info.values(), genre_info=genre_info, total_count=total_count, deletemsg = deletemsg,
                           movie=movie, country=country, genre=genre, director=director, writer=writer, actor=actor)

    return render_template("myinfo.html", userid=userid, user_info=user_info, users_pick=users_info.values(),
                           genre_info=genre_info, total_count=total_count, deletemsg=deletemsg)

@app.route('/myinfo/pw_change', methods=['GET', 'POST'])
def pw_change():
    userid = session.get('userid', None)
    changemsg = None

    if request.method == 'POST':
        password = request.form.get('password')
        new_password = request.form.get('new_password')

        cur.execute("SELECT pw FROM users WHERE id = '{}';".format(userid))
        cur_password = cur.fetchall()[0][0]

        if password == cur_password:
            cur.execute("UPDATE users SET pw = '{}' WHERE id = '{}';".format(new_password, userid))
            connect.commit()
            changemsg = 'Success'
        else:
            changemsg = 'Fail'
    # change your pw after current pw confirmed.

    return render_template("myinfo/pw_change.html", userid=userid, changemsg=changemsg)

@app.route('/myinfo/age_change', methods=['GET', 'POST'])
def age_change():
    userid = session.get('userid', None)
    changemsg = None
    if request.method == 'POST':
        age = request.form.get('new_age')

        try:
            int(age)
            age = int(age)
            changemsg = 'Success'
        except ValueError:
            changemsg = 'Fail'

        if changemsg == 'Success' and (age<=0 or age>100):
            changemsg = 'Fail'
        if changemsg == 'Success':
            cur.execute("UPDATE users SET age = '{}' WHERE id = '{}';".format(age, userid))
            connect.commit()
    # change your age.

    return render_template("myinfo/age_change.html", userid=userid, changemsg=changemsg)


@app.errorhandler(500)
def internal_error(error):
    connect.rollback()
    return render_template('register.html', regimsg='fail'), 500
    # if errors such as primary constraint violation occurs, python gets #500 error.
    # can occur when you register but enter duplicate user id so handle this situation.

if __name__ == '__main__':
    app.run()