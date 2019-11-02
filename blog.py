from flask import Flask,render_template,flash,redirect,url_for,session,logging,request
from flask_mysqldb import MySQL
from wtforms import Form,StringField,TextAreaField,PasswordField,validators
from passlib.hash import sha256_crypt


#Kontrol paneli decoratoru

from functools import wraps
from flask import g, request, redirect, url_for

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        
        if("log_in" in session and session["admin"] == 1):
            return f(*args, **kwargs)
        else:
            return redirect(url_for("login"))

    return decorated_function


#Qeydiyyat Formu

class RegisterForm(Form):
    name = StringField("İsim Soyisim",validators=[validators.Length(min = 4,max = 25)])
    username = StringField("Kullanıcı Adı",validators=[validators.Length(min = 5,max = 35)])
    email = StringField("Email Adresi",validators=[validators.Email(message = "Lütfen Geçerli Bir Email Adresi Girin...")])
    password = PasswordField("Parola:",validators=[
        validators.DataRequired(message = "Lütfen bir parola belirleyin"),
        validators.EqualTo(fieldname = "confirm",message="Parolanız Uyuşmuyor...")
    ])
    confirm = PasswordField("Parola Doğrula")

#Giris Formu

class LoginForm(Form):
    username = StringField("Nikiniz")
    password = PasswordField("Parolunuz")


#AddArticle form

class AddArticleForm(Form):
    title = StringField("Title",validators=[validators.InputRequired()])
    content = TextAreaField("Content",validators=[validators.InputRequired()])

app = Flask(__name__)
app.secret_key = "blog"

app.config["MYSQL_HOST"] = "localhost"
app.config["MYSQL_USER"] = "root"
app.config["MYSQL_PASSWORD"] = ""
app.config["MYSQL_DB"] = "blog"
app.config["MYSQL_CURSORCLASS"] = "DictCursor"


mysql = MySQL(app)



@app.route("/")
def index():
    return render_template("index.html")

@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/dashboard")
@login_required
def dashboard():
    
    cursor = mysql.connection.cursor()
    
    sorgu = "Select * From articles where author = %s"

    result = cursor.execute(sorgu,(session["username"],))

    if result > 0:
        articles = cursor.fetchall()
        return render_template("dashboard.html",articles = articles)
    else:
        return render_template("dashboard.html")



@app.route("/articles")
def articles():

    cursor = mysql.connection.cursor()

    sorgu = "Select * from articles"

    result = cursor.execute(sorgu)

    if result > 0:
        articles = cursor.fetchall()



        return render_template("articles.html", articles = articles)
    else:
        return render_template("articles.html")

@app.route("/addarticle",methods = ["GET","POST"])
def addarticle():
    form = AddArticleForm(request.form)

    if request.method == "POST" and form.validate:
        title = form.title.data
        content = form.content.data
        username = session["username"]


        cursor = mysql.connection.cursor()

        sorgu = "Insert into articles(title,content,author) VALUES(%s,%s,%s)"

        result = cursor.execute(sorgu,(title,content,username))

        if result > 0:

            mysql.connection.commit()
            cursor.close()
            flash("Basariyla elave olundu","success")

            return redirect(url_for("articles"))

    return render_template("addarticle.html", form =form)


@app.route("/login",methods = ["GET","POST"])
def login():
    form = LoginForm(request.form)
    if request.method == "POST":

        username = form.username.data
        password_entered = form.password.data
        
        cursor = mysql.connection.cursor()
        
        sorgu = "Select * From users where username = %s"

        result = cursor.execute(sorgu,(username,))

        if result > 0:
            data = cursor.fetchone()
            real_password = data["password"]
            admin = data["admin"]

            if sha256_crypt.verify(password_entered,real_password):
                flash("Giris olundu","success")


                session["log_in"] = True
                session["admin"] = admin
                session["username"] = username


                return redirect(url_for("index"))
            else:
                flash("sifre sefdir","danger")
                return redirect(url_for("login"))
        else:
            flash("istifadeci yoxdur","danger")
            return redirect(url_for("login"))


    else:
        return render_template("login.html",form = form)


#Detay seeifesi

@app.route("/article/<string:id>")
def article(id):
    cursor = mysql.connection.cursor()

    sorgu = "Select * from articles where id = %s"

    result = cursor.execute(sorgu,(id,))

    if result > 0:
        article = cursor.fetchone()
        return render_template("article.html", article=article)
    else:
        return render_template("article.html")



@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


@app.route("/register",methods = ["GET","POST"])
def register():

    form = RegisterForm(request.form)

    if request.method == "POST" and form.validate():

        name = form.name.data
        username = form.username.data
        email = form.email.data
        password = sha256_crypt.encrypt(form.password.data)

        cursor = mysql.connection.cursor()
        
        sorgu = "Insert into users(name,username,email,password) VALUES(%s,%s,%s,%s)"

        cursor.execute(sorgu,(name,username,email,password))
        mysql.connection.commit()

        cursor.close()

        flash("Basarili...","success")


        return redirect(url_for("login"))
    else:
        return render_template("register.html", form=form)

#Meqale Silmey
@app.route("/delete/<string:id>")
@login_required
def delete(id):
    cursor = mysql.connection.cursor()

    sorgu = "Select * from articles where author = %s and id = %s"

    result = cursor.execute(sorgu,(session["username"],id))

    if result > 0:
        sorgu2 = "Delete from articles where id = %s"
        cursor.execute(sorgu2,(id,))
        mysql.connection.commit()
        return redirect(url_for("dashboard"))
    else:
        flash("Bele bir meqale tapilmir ve ya huququnuz yoxdur...","danger")
        return redirect(url_for("index"))

#Meqale Update
@app.route("/edit/<string:id>", methods = ["GET","POST"])
@login_required
def update(id):
    if request.method == "GET":
        cursor = mysql.connection.cursor()
        sorgu = "Select * from articles where id = %s and author = %s"
        result = cursor.execute(sorgu,(id,session["username"]))

        if result == 0:
            flash("Bele bir meqale yoxdur ve ya icazeniz yoxdur...","danger")
            return redirect(url_for("index"))
        else:
            article = cursor.fetchone()
            form = AddArticleForm()
            form.title.data = article["title"]
            form.content.data = article["content"]
            return render_template("update.html",form = form)
            
    else:
       #Post Request
       form = AddArticleForm(request.form)

       newTitle = form.title.data
       newContent = form.content.data

       sorgu2 = "Update articles set title = %s,content = %s where id = %s"

       cursor = mysql.connection.cursor()
       cursor.execute(sorgu2,(newTitle,newContent,id))
       mysql.connection.commit()
       flash("Muveffeqiyyetle yenilendi...","success")

       return redirect(url_for("dashboard"))

#Search buttonu
@app.route("/search",methods = ["GET","POST"])
def search():
    if request.method == "GET":
        return render_template("index.html")
    else:
        keyword = request.form.get("keyword")

        cursor = mysql.connection.cursor()
        sorgu = "Select * from articles where title like '%" + keyword + "%'"
        result = cursor.execute(sorgu)

        if result == 0:
            flash("Basliq tapilmadi...","warning")
            return redirect(url_for("articles"))
        else:
            articles = cursor.fetchall()
            return render_template("articles.html",articles = articles)




        
if __name__ == "__main__":
    app.run(debug= True)