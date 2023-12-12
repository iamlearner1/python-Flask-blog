# creating our first application which prints the message hello world and hello shiva
import json
import math
import os
from datetime import datetime
from werkzeug.utils import secure_filename
from werkzeug.datastructures import  FileStorage
from flask import Flask, render_template, request, session, redirect
from flask_mail import Mail
from flask_sqlalchemy import SQLAlchemy

import random
# fix jinja error by adding the parameter template_folder = 'template'\
OTP = random.randint(0000,9999)
with open('config.json','r') as c:
    params = json.load(c)["params"]
local_server = True
app = Flask(__name__, template_folder= 'static')
app.secret_key = 'super-secret-key'
app.config['UPLOAD_FOLDER'] = params['upload_location']
app.config.update(
    MAIL_SERVER = 'smtp.gmail.com',
    MAIL_PORT  = '465',
    MAIL_USE_SSL = True,
    MAIL_USERNAME = params['gmail-user'],
    MAIL_PASSWORD = params['gmail-password']

)
mail = Mail(app)
# app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://username:password@localhost/db_name'
if local_server:
    app.config['SQLALCHEMY_DATABASE_URI'] = params['local_uri']
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = params['prod_uri']

db = SQLAlchemy(app)

class Contacts(db.Model):
    """
    sno,name,phone,msg,date,email
    """
    sno = db.Column(db.Integer,primary_key = True)
    name = db.Column(db.String(60),nullable=False)
    phone_num = db.Column(db.String(12),unique = False,nullable=True)
    msg = db.Column(db.String(120),  nullable=False)
    date = db.Column(db.String(12))
    em = db.Column(db.String(20),  nullable=False)

class Posts(db.Model):
    """
    sno,name,phone,msg,date,email
    """
    Sno = db.Column(db.Integer,primary_key = True)
    title = db.Column(db.String(80),nullable=False)
    slug = db.Column(db.String(21),unique = False,nullable=True)
    Content = db.Column(db.String(120),  nullable=False)
    tag_line = db.Column(db.String(120), nullable=False)
    Date = db.Column(db.String(12))
    img_file = db.Column(db.String(12),nullable = True)

@app.route("/")
def home():
    posts = Posts.query.filter_by().all()
    last = math.floor(len(posts)/int(params['no_of_posts']))
    # [0:params['no_of_posts']]

    page = request.args.get('page')
    if(not(str(page).isnumeric())):
        page = 1
    page = int(page)
    posts = posts[(page-1)*int(params['no_of_posts']):(page-1)* int(params['no_of_posts'])+int(params['no_of_posts'])]
    if(page == 1):
        prev = '#'
        next = "/?page=" + str(page+1)
    elif(page == last):
        prev = "/?page=" + str(page -1)
        next = '#'
    else:
        prev = "/?page=" + str(page - 1)
        next = "/?page=" + str(page + 1)



    """    pagination logic
            first
            prev = # --blank
            next = page + 1
            middle
            prev = page -1
            next = page + 1
            last
            prev = page + 1
            next = #
    """
    return render_template('index.html ',params = params,posts = posts,prev = prev,next = next)

@app.route("/post/<string:post_slug>",methods  = ['GET'])
def post_route(post_slug):
    post =  Posts.query.filter_by(slug = post_slug).first()
    return render_template('post.html',params = params,post = post)

@app.route("/about")
def about():
    return render_template('about.html',params = params)


@app.route("/dashboard",methods = ['GET','POST'])
def dashboard():
    if 'user' in session and session['user'] == params['admin_user']:
        posts = Posts.query.all()
        return render_template("dashboard.html",params= params,posts = posts)
    if request.method == 'POST':
        # redirect to admin panel

        username = request.form.get('uname')
        userpass = request.form.get('pass')
        otp = request.form.get('otp')
        mail.send_message('OTP', sender=username, recipients=[username],body =str(OTP))
        if (username == params['admin_user'] and userpass == params['admin_password']):
                session['user'] = username
                posts = Posts.query.all()
                return render_template('dashboard.html',params = params,post = posts)

    else:
        return render_template('login.html',params = params)

@app.route("/verify",methods = ['GET','POST'])
def verify():
    pass


@app.route("/post")
def post():
    return render_template('post.html',params = params)
@app.route("/edit/<string:sno>",methods = ['GET','POST'])
def edit(sno):
    if 'user' in session and session['user'] == params['admin_user']:
        if request.method == 'POST':
            box_title = request.form.get('title')
            tagline = request.form.get('tagline')
            slug = request.form.get('slug')
            content = request.form.get('content')
            img_file = request.form.get('img_file')
            date = datetime.now()
            if sno == '0':
                post = Posts(title = box_title,slug = slug,Content = content,tag_line = tagline,img_file = img_file,Date = date)
                db.session.add(post)
                db.session.commit()
            else:
                post = Posts.query.filter_by(Sno=sno).first()
                post.title = box_title
                post.slug = slug
                post.Content = content
                post.tag_line = tagline
                post.img_file = img_file
                post.Date = date
                db.session.commit()
                return redirect('/edit/'+sno)
        post = Posts.query.filter_by(Sno=sno).first()
        return render_template('edit.html',params=params,post=post,Sno=sno)

@app.route("/uploader", methods=['GET', 'POST'])
def uploader():
    if 'user' in session and session['user'] == params['admin_user']:
        if (request.method == 'POST'):
            f = request.files['file1']
            f.save(os.path.join(app.config['UPLOAD_FOLDER'],secure_filename(f.filename)))
            return "Uploaded Successfully"

@app.route("/logout")
def logout():
    session.pop('user')
    return redirect('/dashboard')

@app.route("/delete/<string:sno>",methods = ['GET','POST'])
def delete(sno):
    if 'user' in session and session['user'] == params['admin_user']:
        post = Posts.query.filter_by(Sno=sno).first()
        db.session.delete(post)
        db.session.commit()
    return redirect('/dashboard')
@app.route("/contact",methods = ['GET','POST'])
def contact():
    if(request.method == 'POST'):
        """add entry to the data base"""
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        message = request.form.get('message')
        """ sno, name, phone, msg, date, email"""
        """Sno. Name Email PH Message"""
        entry = Contacts(name = name,phone_num = phone,msg = message,date = datetime.now() ,em = email,)
        db.session.add(entry)
        db.session.commit()
        mail.send_message('New message from Blog',sender = email,recipients = [params['gmail-user']],body = "Name :" +name +"\n"+"Email :" + email +"\n"+"Message :"+message + "\n"+"Phone :"+phone)
    return render_template('contact.html',params = params)

app.run(debug=True)