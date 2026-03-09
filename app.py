from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_socketio import SocketIO, emit

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secretkey'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'

db = SQLAlchemy(app)
socketio = SocketIO(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

####################################
# DATABASE MODELS
####################################

class User(UserMixin, db.Model):

    id = db.Column(db.Integer, primary_key=True)

    username = db.Column(db.String(150), unique=True)

    password = db.Column(db.String(150))


class Task(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    title = db.Column(db.String(200))

    description = db.Column(db.String(500))

    status = db.Column(db.String(50))

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


####################################
# AUTH ROUTES
####################################

@app.route("/register", methods=["GET","POST"])
def register():

    if request.method == "POST":

        username = request.form["username"]

        password = request.form["password"]

        user = User(username=username,password=password)

        db.session.add(user)

        db.session.commit()

        flash("Registration successful")

        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET","POST"])
def login():

    if request.method == "POST":

        username = request.form["username"]

        password = request.form["password"]

        user = User.query.filter_by(username=username,password=password).first()

        if user:

            login_user(user)

            return redirect(url_for("dashboard"))

        flash("Invalid credentials")

    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():

    logout_user()

    return redirect(url_for("login"))


####################################
# TASK ROUTES
####################################

@app.route("/")
@login_required
def dashboard():

    tasks = Task.query.filter_by(user_id=current_user.id).all()

    return render_template("dashboard.html",tasks=tasks)


@app.route("/create",methods=["GET","POST"])
@login_required
def create_task():

    if request.method=="POST":

        title=request.form["title"]

        description=request.form["description"]

        task = Task(title=title,description=description,status="Pending",user_id=current_user.id)

        db.session.add(task)

        db.session.commit()

        socketio.emit("task_update")

        return redirect(url_for("dashboard"))

    return render_template("create_task.html")


@app.route("/edit/<int:id>",methods=["GET","POST"])
@login_required
def edit_task(id):

    task = Task.query.get(id)

    if request.method=="POST":

        task.title=request.form["title"]

        task.description=request.form["description"]

        task.status=request.form["status"]

        db.session.commit()

        socketio.emit("task_update")

        return redirect(url_for("dashboard"))

    return render_template("edit_task.html",task=task)


@app.route("/delete/<int:id>")
@login_required
def delete_task(id):

    task = Task.query.get(id)

    db.session.delete(task)

    db.session.commit()

    socketio.emit("task_update")

    return redirect(url_for("dashboard"))


####################################
# SOCKET EVENTS
####################################

@socketio.on("connect")
def handle_connect():

    print("Client connected")


####################################
# RUN APP
####################################

if __name__ == "__main__":

    with app.app_context():
        db.create_all()

    socketio.run(app,debug=True)