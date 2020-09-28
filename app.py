from flask import Flask, render_template, request, redirect, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import pickle
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import MultinomialNB
from sklearn.metrics import classification_report
import joblib
import click
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_required, logout_user, login_user, LoginManager, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
# 富文本
from flask_ckeditor import CKEditor, CKEditorField


app = Flask(__name__)

app.config['CKEDITOR_SERVE_LOCAL'] = True
app.config['CKEDITOR_HEIGHT'] = 400
app.secret_key = 'secret string'
app.config["CACHE_TYPE"] = "null"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///posts.db'
# admin passwd
app.secret_key = '123'

ckeditor = CKEditor(app)
db = SQLAlchemy(app)


# 富文本
class PostForm(FlaskForm):
    title = StringField('Title')
    body = CKEditorField('Body', validators=[DataRequired()])
    author = StringField('Author')
    submit = SubmitField('Submit')

class ckddata(db.Model):
    __tablename__ = "ckd"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.Text, nullable=False)
    body = db.Column(db.Text, nullable=False)
    author = db.Column(db.String(50))
    time = db.Column(db.DateTime, nullable=False, default=datetime.now)

class User(db.Model, UserMixin):
    __tablename__ = 'User'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20))
    username = db.Column(db.String(20))
    password_hash = db.Column(db.String(128))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def validate_password(self, password):
        # 返回布尔值
        return check_password_hash(self.password_hash, password) 

@app.cli.command()
@click.option('--username', prompt=True, help='The username used to login.')
@click.option('--password', prompt=True, hide_input=True, confirmation_prompt=True, help='the password used to login')
def admin(username, password):
    # 创建管理员，负责修改删除博客
    user = User.query.first()
    if user is not None:
        click.echo('Updating user...')
        user.username = username
        user.set_password(password)
    else:
        click.echo('Creating user...')
        user = User(username=username, name='Admin')
        user.set_password(password)
        db.session.add(user)

    db.session.commit()
    click.echo('Done.')

login_manager = LoginManager(app)
@login_manager.user_loader
def load_user(user_id):
    user = User.query.get(int(user_id))
    return user

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if not username or not password:
            flash('Invalid input.')
            return redirect('/login')

        user = User.query.first()
        # 验证用户名和密码是否一致
        if username == user.username and user.validate_password(password):
            login_user(user)  # 登入用户
            flash('Login success.')
            return redirect('#')  # 重定向到主页

        flash('Invalid username or password.')  # 如果验证失败，显示错误消息
        return redirect('/login') # 重定向回登录页面

    return render_template('login.html')


# 退出登录
@app.route('/logout')
@login_required 
def logout():
    logout_user() 
    flash('Goodbye.')
    return redirect('/') 


class BlogPost(db.Model):

    __tablename__ = 'Blog'
    # 创建博客数据库， 指定字段， 主键

    id = db.Column(db.Integer, primary_key=True)
    # 内容，标题等不可为空
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    author = db.Column(db.String(30), nullable=False, default='Not Available')
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    def __repr__(self):
        return "Blog Post " + str(self.id)


class Textbook(db.Model):

    __tablename__ = 'Textbook'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30), nullable=False, default='Not Available')
    text = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)


class Customer(db.Model):
    __tablename__ = 'customer'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(200), nullable=False)
    phone = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=True)

# 留言板
@app.route('/textbook', methods=['POST', 'GET'])
def textbook():
    
    if request.method =='POST':
        name = request.form['name']
        text = request.form['text']
        newtext = Textbook(name=name, text=text)
        db.session.add(newtext)
        db.session.commit()
        return redirect('/textbook')
    else:
        data = Textbook.query.order_by(Textbook.timestamp.desc()).all()    
        return render_template('showtext.html', text_db=data)



# 用户信息
@app.route("/customerInfo", methods=['GET', 'POST'])
def getcustm():
    if request.method == 'POST':
        cname = request.form['name']
        cemail = request.form['email']
        cphone = request.form['phone']
        cmessage = request.form['message']
        newcust = Customer(name=cname, email=cemail, phone=cphone, message=cmessage)
        db.session.add(newcust)
        db.session.commit()
        with open('customer.txt', 'a') as f:
            f.write(cname+',')
            f.write(cemail+',')
    
    
    allcust = Customer.query.order_by(Customer.name)
    print(allcust)
    return redirect('/')



@app.route("/") 
def index():
    # 主页
    return render_template('index.html')



@app.route("/posts", methods=['GET', 'POST'])
def posts():
    # 接受页面输入数据
    if request.method == 'POST':
        post_title = request.form['title']
        post_content = request.form['content']
        post_author = request.form['author']
        new_post = BlogPost(title=post_title, content=post_content, author=post_author)
        db.session.add(new_post)
        # 存入数据库并确认
        db.session.commit()
        # 重定向， 在创建新博客之后返回posts页面
        return redirect('/posts') 
    else:
        # 如果不是添加新博客的操作， 则在posts页面显示所有博客
        all_ckd = ckddata.query.order_by(ckddata.id.desc())
        all_posts = BlogPost.query.order_by(BlogPost.date_posted)
        return render_template('posts.html', post_db=all_posts, cdk_db=all_ckd)


# 富文本博客

@app.route('/ckeditor', methods=['GET', 'POST'])
def cked():
    form = PostForm()
    if form.validate_on_submit():
        title = form.title.data
        body = form.body.data
        author = form.author.data
        ckd_data = ckddata(title=title, body=body, author=author)
        db.session.add(ckd_data)
        db.session.commit()
        flash("save success")
        all_ckd = ckddata.query.order_by(ckddata.id.desc())
        
        return redirect('/posts')
        #return render_template('cked.html', cdk_db = all_ckd)
    return render_template('ckedindex.html', form=form)
  

@app.route('/ckeditor/delete/<int:idx>')
@login_required  # 登录保护
def delete_ckdpost(idx):
    # 从数据库中删除博客
    ckd_post = ckddata.query.get_or_404(idx)
    db.session.delete(ckd_post)
    db.session.commit()
    return redirect('/posts')



# edit func problem
@app.route('/ckeditor/edit/<int:idx>', methods=['GET', 'POST'])
@login_required  # 登录保护
def edit_ckdpost(idx):
    form = PostForm()
    ckd_post = ckddata.query.get_or_404(idx)

    if form.validate_on_submit():
        # 修改
        ckd_post.title = form.title.data
        ckd_post.author = form.author.data
        ckd_post.body = form.body.data
        db.session.commit()
        all_ckd = ckddata.query.order_by(ckddata.id.desc())
        return redirect('/posts')
    return render_template('ckedindex.html', form=form)

 
@app.route('/ckeditor/details/<int:idx>', methods=['GET', 'POST'])
def ckd_details(idx):
    ckd_post = ckddata.query.get_or_404(idx)
    return render_template('ckd_details.html', posts=ckd_post) 


'''  
@app.route("/home/users/<string:name>/posts/<int:tag>")
def hello(name, tag):
    return "Hello, " + name + " Your ID is: " + str(tag)


@app.route('/methods', methods=['GET', 'POST'])
def method():
    return "保留一些其他的功能"

'''
@app.route('/posts/delete/<int:idx>')
@login_required  # 登录保护
def delete_post(idx):
    # 从数据库中删除博客
    post = BlogPost.query.get_or_404(idx)
    db.session.delete(post)
    db.session.commit()
    return redirect('/posts')


@app.route('/posts/edit/<int:idx>', methods=['GET', 'POST'])
@login_required  # 登录保护
def edit_post(idx):

    post = BlogPost.query.get_or_404(idx)

    if request.method == 'POST':
        # 修改
        post.title = request.form['title']
        post.author = request.form['author']
        post.content = request.form['content']
        db.session.commit()
        return redirect('/posts')
    else:
        return render_template('edit.html', posts=post)


# 查看文章详细信息


@app.route('/posts/details/<int:idx>', methods=['GET', 'POST'])
def details(idx):

    post = BlogPost.query.get_or_404(idx)
    return render_template('details.html', posts=post)


@app.route('/posts/new', methods=['GET', 'POST'])
def new_posts():
    # 添加新的博客
    if request.method == 'POST':
        post_title = request.form['title']
        post_author = request.form['author']
        post_content = request.form['content']
        new_post = BlogPost(title=post_title, author=post_author, content=post_content)
        
        db.session.add(new_post)
        db.session.commit()
        return redirect('/posts')
    else:
        return render_template('new_post.html')

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    return render_template('contact.html')

@app.route('/inputext')
def inputmail():
    return render_template('inputext.html')
    
@app.route('/spamdetect', methods=['GET', 'POST'])
def predict():
    # 垃圾邮件检测功能
    df = pd.read_csv('spam.csv', encoding='latin-1')
    df.drop(['Unnamed: 2', 'Unnamed: 3', 'Unnamed: 4'], axis=1, inplace=True)
    df.rename(columns={'v1':'tag', 'v2':'message'}, inplace=True)
    X = df['message']
    cv = CountVectorizer()
    X = cv.fit_transform(X)
    nb = open('nb_spam_model.pkl', 'rb')
    clf = joblib.load(nb)
    if request.method == 'POST':
        message = request.form['message']
        # 判断中文， 如果包含中文字符报错
        data = [message]
        vect = cv.transform(data).toarray()
        ret = clf.predict(vect)
        for ch in message:
            if u'\u4e00' <= ch <= u'\u9fff':
                ret = 3
                break
   
    return render_template('result.html', prediction=ret)




if __name__ == "__main__":
    # 创建管理员吧
    #admin()
    #db.drop_all()
    db.create_all()
    app.jinja_env.auto_reload = True
    app.run(port=5000, debug=True)
    
