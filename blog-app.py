from flask import Flask, render_template, request, redirect
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

app = Flask(__name__)
app.config["CACHE_TYPE"] = "null"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///posts.db'
db = SQLAlchemy(app)



class BlogPost(db.Model):
    
    # 创建博客数据库， 指定字段， 主键

    id = db.Column(db.Integer, primary_key=True)
    # 内容，标题等不可为空
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    author = db.Column(db.String(30), nullable=False, default='Not Available')
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return "Blog Post " + str(self.id)


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
        all_posts = BlogPost.query.order_by(BlogPost.date_posted)
        return render_template('posts.html', post_db=all_posts)


@app.route("/home/users/<string:name>/posts/<int:tag>")
def hello(name, tag):
    return "Hello, " + name + " Your ID is: " + str(tag)


@app.route('/methods', methods=['GET', 'POST'])
def method():
    return "保留一些其他的功能"


@app.route('/posts/delete/<int:idx>')
def delete_post(idx):
    # 从数据库中删除博客
    post = BlogPost.query.get_or_404(idx)
    db.session.delete(post)
    db.session.commit()
    return redirect('/posts')


@app.route('/posts/edit/<int:idx>', methods=['GET', 'POST'])
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
    # 修改模板后立即生效
    app.jinja_env.auto_reload = True
    app.run(port=2011, debug=True)
