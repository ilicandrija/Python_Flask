from flask import Flask, redirect, url_for, render_template,request,session,flash
from datetime import timedelta
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = "hello"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.sqlite3'
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.permanent_session_lifetime = timedelta(seconds = 600)

db = SQLAlchemy(app)

class Users(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100))
    password = db.Column(db.String(100))
    todos = db.relationship('Todo', backref='user', lazy=True)

    def __init__(self, name, email, password):
        self.name = name
        self.email = email
        self.password = password


class Todo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    task = db.Column(db.String(100))
    done = db.Column(db.Boolean,)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    def __init__(self, task, user_id):
        self.task = task
        self.done = False
        self.user_id = user_id


@app.route("/home")
def home():
    return render_template("home.html")

@app.route("/user", methods=["POST","GET"])
def user():
    email = None
    if "user" in session:
        user = session["user"]
        found_user = Users.query.filter_by(name=user).first()
        num_todos = len(found_user.todos)
        num_checked = sum(todo.done for todo in found_user.todos)
        num_not_checked = num_todos - num_checked

        if request.method == "POST":
            task = request.form["todo"]
            if task:
                todo = Todo(task)
                found_user.todos.append(todo)
                db.session.add(todo)
                db.session.commit()
                flash("Stavka uspešno dodata!","default")

        return render_template("user.html", user=found_user, num_todos=num_todos, num_checked=num_checked, num_not_checked=num_not_checked)
    else:
        flash("Niste ulogovani!","error")
        return redirect(url_for("login"))

@app.route("/logout")
def logout():
    if "user" in session:
        user = session["user"]
        flash(f"Uspešno ste se izlogovali, {user}.","info")
        session.pop("user", None)
        session.pop("email", None)
    else:
        session.pop("user", None)
        flash("Niste ulogovani!","error")
        return redirect(url_for("login"))
    return redirect(url_for("login"))

@app.route("/edit/<int:todo_id>", methods=["GET", "POST"])
def edit(todo_id):
    todo = Todo.query.get_or_404(todo_id)
    if request.method == "POST":
        todo.task = request.form["todo"]
        db.session.commit()
        flash("Stavka uspešno izmenjena!","default")
        return redirect(url_for("user"))
    else:
        return render_template("edit.html", todo=todo)


@app.route("/check/<int:todo_id>")
def check(todo_id):
    todo = Todo.query.get_or_404(todo_id)
    todo.done = not todo.done
    db.session.commit()
    return redirect(url_for("user"))



@app.route("/delete/<int:todo_id>")
def delete(todo_id):
    todo = Todo.query.get_or_404(todo_id)
    db.session.delete(todo)
    db.session.commit()
    flash("Stavka uspešno obrisana!","default")
    return redirect(url_for("user"))


   
@app.route("/add", methods=["POST"])
def add():
    task = request.form['todo']
    if task:
        user = Users.query.filter_by(name=session["user"]).first()
        todo = Todo(task, user.id)
        db.session.add(todo)
        db.session.commit()
        flash("Stavka uspešno dodata","default")
    return redirect(url_for("user"))




@app.route("/register", methods=["POST", "GET"])
def register():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]
        found_user = Users.query.filter_by(email=email).first()
        if found_user:
            flash("Korisnik već postoji!","error")
            return redirect(url_for("login"))
        new_user = Users(name, email, password)
        db.session.add(new_user)
        db.session.commit()
        session["user"] = name
        session["email"] = email
        flash("Uspešno ste se registrovali!","default")
        return redirect(url_for("user"))
    else:
        return render_template("register.html")



@app.route("/login", methods=["GET", "POST"])
def login():
    if "user" in session:
        # User is already logged in
        flash("Već si prijavljen/a.", "error")
        return redirect(url_for("user"))
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        user = Users.query.filter_by(email=email).first()
        if user and user.password == password:
           session["user"] = user.name
           flash(f"Dobrodošao/la {user.name}!","default")
           return redirect(url_for("user"))
        else:
           flash("Pogrešna email adresa ili šifra.","error")
           return redirect(url_for("login"))


    return render_template("login.html")



if __name__ == "__main__":  
    with app.app_context():

        db.create_all()
    app.run(debug=True)