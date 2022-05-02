# Package imports
import pymysql
pymysql.install_as_MySQLdb()
from flask import Flask, render_template, request, redirect, session, flash
from flask_bootstrap import Bootstrap
from flask_mysqldb import MySQL
from flask_ckeditor import CKEditor
import yaml


# Initialize app
app = Flask(__name__)
Bootstrap(app)
ckeditor = CKEditor(app)


# Connect DB
db = yaml.safe_load(open('db.yaml'))
app.config['MYSQL_HOST'] = db['mysql_host']
app.config['MYSQL_USER'] = db['mysql_user']
app.config['MYSQL_PASSWORD'] = db['mysql_password']
app.config['MYSQL_DB'] = db['mysql_db']
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
mysql = MySQL(app)

app.config['SECRET_KEY'] = 'secret'


# Home
@app.route('/')
def index():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM blog")
    all_blogs = cur.fetchall()
    return render_template('index.html', all_blogs=all_blogs)


# About
@app.route('/about/')
def about():
    return render_template('about.html')


# Register
@app.route('/register/', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        userDetails = request.form
        if userDetails['password'] != userDetails['confirm_password']:
            flash('Passwords do not match! Try again.', 'danger')
            return render_template('register.html')
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO user(first_name, last_name, username, email, password) "\
        "VALUES(%s,%s,%s,%s,%s)",(userDetails['first_name'], userDetails['last_name'], \
        userDetails['username'], userDetails['email'], userDetails['password']))
        mysql.connection.commit()
        cur.close()
        flash('Registration successful! Please login.', 'success')
        return redirect('/login')
    return render_template('register.html')


# Login
@app.route('/login/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        userDetails = request.form
        username = userDetails['username']
        cur = mysql.connection.cursor()
        resultValue = cur.execute("SELECT * FROM user WHERE username = %s", ([username]))
        if resultValue > 0:
            user = cur.fetchone()
            if userDetails['password'] == user['password']:
                session['login'] = True
                session['firstName'] = user['first_name']
                session['lastName'] = user['last_name']
                session['user_id'] = user['user_id']
                flash('Welcome ' + session['firstName'] +'! You have been successfully logged in', 'success')
            else:
                cur.close()
                flash('Password does not match', 'danger')
                return render_template('login.html')
        else:
            cur.close()
            flash('User not found', 'danger')
            return render_template('login.html')
        cur.close()
        return redirect('/')
    return render_template('login.html')


# Logout
@app.route('/logout/')
def logout():
    session.clear()
    flash("You have been logged out", 'info')
    return redirect('/')


# Write a new blog
@app.route('/write-blog/',methods=['GET', 'POST'])
def write_blog():
    if request.method == 'POST':
        blogpost = request.form
        title = blogpost['title']
        body = blogpost['body']
        author = session['firstName'] + ' ' + session['lastName']
        user_id = session['user_id']
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO blog(user_id, title, body, author) VALUES(%s, %s, %s, %s)", (user_id, title, body, author))
        mysql.connection.commit()
        cur.close()
        flash("Successfully posted new blog", 'success')
        return redirect('/')
    return render_template('write-blog.html')


# View my blog
@app.route('/my-blogs/')
def view_blogs():
    user_id = session['user_id']
    cur = mysql.connection.cursor()
    result_value = cur.execute("SELECT * FROM blog WHERE user_id = {}".format(user_id))
    if result_value > 0:
        my_blogs = cur.fetchall()
        return render_template('my-blogs.html',my_blogs=my_blogs)
    else:
        return render_template('my-blogs.html',my_blogs=None)


# Edit blog
@app.route('/edit-blog/<int:id>/', methods=['GET', 'POST'])
def edit_blog(id):
    if request.method == 'POST':
        cur = mysql.connection.cursor()
        title = request.form['title']
        body = request.form['body']
        cur.execute("UPDATE blog SET title = %s, body = %s where blog_id = %s",(title, body, id))
        mysql.connection.commit()
        cur.close()
        flash('Blog updated successfully', 'success')
        return redirect('/blogs/{}'.format(id))
    cur = mysql.connection.cursor()
    result_value = cur.execute("SELECT * FROM blog WHERE blog_id = {}".format(id))
    if result_value > 0:
        blog = cur.fetchone()
        blog_form = {}
        blog_form['title'] = blog['title']
        blog_form['body'] = blog['body']
        return render_template('edit-blog.html', blog_form=blog_form)


# Delete blog
@app.route('/delete-blog/<int:id>/')
def delete_blog(id):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM blog WHERE blog_id = {}".format(id))
    mysql.connection.commit()
    flash("Your blog has been deleted", 'success')
    return redirect('/my-blogs')


# View specific blog
@app.route('/blogs/<int:id>/')
def view_blog(id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM blog WHERE blog_id = {}".format(id))
    blog = cur.fetchall()
    return render_template('blogs.html', blog=blog)


# Search for a user
@app.route('/search/',methods=['GET', 'POST'])
def search():
    if request.method == 'POST':
        blogpost = request.form
        user_id = blogpost['username']
        cur = mysql.connection.cursor()
        mysql.connection.commit()
        cur.close()
        return redirect('/user-blogs/{}'.format(user_id))
    return render_template('search.html')


# View any users blogs
@app.route('/user-blogs/<int:id>')
def user_blogs(id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM blog WHERE user_id = {}".format(id))
    blogs = cur.fetchall()
    return render_template('user-blogs.html', blogs=blogs)


# Main
if __name__ == '__main__':
    app.run(debug=True, port=5001)