# Package imports
from unittest import result
import pymysql
pymysql.install_as_MySQLdb()
from flask import Flask, render_template, request, redirect, session, flash
from flask_bootstrap import Bootstrap
from flask_mysqldb import MySQL
from flask_ckeditor import CKEditor
import yaml
import base64


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
    cur.execute("SELECT * FROM blog ORDER BY blog_id DESC")
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
        checkUsername = cur.execute("SELECT * FROM user WHERE username = %s", ([userDetails['username']]))
        checkEmail = cur.execute("SELECT * FROM user WHERE email = %s", ([userDetails['email']]))
        if checkUsername > 0:
            flash('Username already taken! Try again.', 'danger')
            return render_template('register.html')
        if checkEmail > 0:
            flash('Email already taken! Try again.', 'danger')
            return render_template('register.html')
        if '' in [userDetails['first_name'], userDetails['last_name'], userDetails['username'],
        userDetails['email'], userDetails['password'], userDetails['confirm_password']]:
            flash('Please fill in required fields!', 'danger')
            return render_template('register.html')

        password = userDetails['password'].encode("utf-8")
        encoded = base64.b64encode(password)

        cur.execute("INSERT INTO user(first_name, last_name, username, email, password) "\
        "VALUES(%s,%s,%s,%s,%s)",(userDetails['first_name'], userDetails['last_name'], \
        userDetails['username'], userDetails['email'], encoded))
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
            password = userDetails['password'].encode("utf-8")
            encoded = base64.b64encode(password)
            decoded = encoded.decode("utf-8") 
            if decoded == user['password']:
                session['login'] = True
                session['firstName'] = user['first_name']
                session['lastName'] = user['last_name']
                session['user_id'] = user['user_id']
                session['username'] = user['username']
                flash('Welcome ' + session['firstName'] +'! You have been successfully logged in', 'success')
            else:
                cur.close()
                flash('Your password is incorrect', 'danger')
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
        artist = blogpost['artist']
        rating = blogpost['rating']
        author = session['firstName'] + ' ' + session['lastName']
        user_id = session['user_id']
        username = session['username']
        if '' in [title, artist, rating]:
            flash('Please fill in all required fields', 'danger')
            return redirect('/write-blog/')
        else:
            cur = mysql.connection.cursor()
            cur.execute("INSERT INTO blog(user_id, title, body, author, username, artist, rating) VALUES(%s, %s, %s, %s, %s, %s, %s)", (user_id, title, body, author, username, artist, rating))
            mysql.connection.commit()
            cur.close()
            flash('Successfully posted new blog', 'success')
            return redirect('/')
    return render_template('write-blog.html')


# View my blog
@app.route('/my-blogs/')
def view_blogs():
    user_id = session['user_id']
    cur = mysql.connection.cursor()
    result_value = cur.execute("SELECT * FROM blog WHERE user_id = {} ORDER BY blog_id DESC".format(user_id))
    if result_value > 0:
        my_blogs = cur.fetchall()
        return render_template('my-blogs.html',my_blogs=my_blogs)
    else:
        return render_template('my-blogs.html',my_blogs=None)


# View my blog (edit mode)
@app.route('/my-blogs-edit-mode/')
def view_blogs_edit_mode():
    user_id = session['user_id']
    cur = mysql.connection.cursor()
    result_value = cur.execute("SELECT * FROM blog WHERE user_id = {} ORDER BY blog_id DESC".format(user_id))
    if result_value > 0:
        my_blogs = cur.fetchall()
        return render_template('my-blogs-edit-mode.html',my_blogs=my_blogs)
    else:
        return render_template('my-blogs-edit-mode.html',my_blogs=None)


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
        username = blogpost['username']
        return redirect('/search/{}'.format(username))
    return render_template('search.html')


# Search results
@app.route('/search/<username>')
def search_results(username):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM user WHERE username LIKE '%{}%'".format(username))
    users = cur.fetchall()
    if len(users) == 0:
        flash('User not found! Please refine your search.', 'info')
        return redirect('/search')
    else:
        return render_template('search-results.html', users=users)


# View any users blogs
@app.route('/user-blogs/<username>')
def user_blogs(username):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM blog WHERE username = %s ORDER BY blog_id DESC", ([username]))
    blogs = cur.fetchall()
    cur.execute("SELECT * FROM user WHERE username = %s", ([username]))
    name = cur.fetchone()
    return render_template('user-blogs.html', blogs=blogs, name=name)


# Others profile
@app.route('/user-profile/<username>')
def user_profile(username):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM blog WHERE username = %s", ([username]))
    blogs = cur.fetchall()
    num_of_blogs = len(blogs)
    cur.execute("SELECT * FROM user WHERE username = %s", ([username]))
    name = cur.fetchone()
    return render_template('user-profile.html', num_of_blogs=num_of_blogs, name=name, username=username)


# My profile
@app.route('/my-profile/')
def my_profile():
    author = session['firstName'] + ' ' + session['lastName']
    user_id = session['user_id']
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM blog WHERE user_id = {}".format(user_id))
    blogs = cur.fetchall()
    num_of_blogs = len(blogs)
    return render_template('my-profile.html', author=author, num_of_blogs=num_of_blogs)


# Delete profile
@app.route('/delete-profile/')
def delete_profile():
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM user WHERE user_id = {}".format(session['user_id']))
    mysql.connection.commit()
    session.clear()
    flash("Your profile has been deleted", 'success')
    return redirect('/')


# Main
if __name__ == '__main__':
    app.run(debug=True, port=5001)