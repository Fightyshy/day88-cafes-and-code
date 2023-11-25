from functools import wraps
from typing import List
from flask import *
from flask_bootstrap import Bootstrap5
from forms import *
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_user, LoginManager, current_user, logout_user
from flask_ckeditor import CKEditor
from sqlalchemy import Integer, String, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey
from werkzeug.security import generate_password_hash, check_password_hash
import datetime as dt

# Lesson content recycled - day 66 APIs, day 71's blog auth and comments functionality

app = Flask(__name__)
app.config["SECRET_KEY"] = "8BYkEfBA6O6donzWlSihBXox7C0sKR6b" #csrf
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///cafes.db"

Bootstrap5(app)
ckededitor = CKEditor(app)
db = SQLAlchemy()
db.init_app(app)

# Configure Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return db.get_or_404(User, user_id)

# Create an admin-only decorator
def admin_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # If id is not 1 then return abort with 403 error
        if current_user.role != "admin":
            return abort(403)
        # Otherwise continue with the route function
        return f(*args, **kwargs)

    return decorated_function

# Models
class Cafe(db.Model):
    __tablename__ = "cafe"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String)
    location: Mapped[str] = mapped_column(String)
    map_url: Mapped[str] = mapped_column(String)
    img_url: Mapped[str] = mapped_column(String)
    has_sockets: Mapped[int] = mapped_column(Integer, nullable=False)
    has_toilet: Mapped[int] = mapped_column(Integer, nullable=False)
    has_wifi: Mapped[int] = mapped_column(Integer, nullable=False)
    can_take_calls: Mapped[int] = mapped_column(Integer, nullable=False)
    seats: Mapped[str] = mapped_column(String)
    coffee_price: Mapped[str] = mapped_column(String)

    comments: Mapped[List["Comment"]] = relationship(back_populates="cafe")

    # Recycle dict converter from day 66 - cafe API
    def to_dict(self):
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}
    
class User(UserMixin, db.Model):
    __tablename__ = "user"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    email: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    password: Mapped[str] = mapped_column(String, nullable=False)
    role: Mapped[str] = mapped_column(String, nullable=False)

    comments: Mapped[List["Comment"]] = relationship(back_populates="author")

class Comment(db.Model):
    __tablename__ = "comment"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    body: Mapped[str] = mapped_column(String, nullable=False)
    # https://stackoverflow.com/questions/75363733/sqlalchemy-2-0-orm-model-datetime-insertion
    timestamp: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    author_id: Mapped[int] = mapped_column(ForeignKey("user.id"))
    author: Mapped["User"] = relationship(back_populates="comments")

    cafe_id: Mapped[int] = mapped_column(ForeignKey("cafe.id"))
    cafe: Mapped["Cafe"] = relationship(back_populates="comments")

with app.app_context():
    db.create_all()


# Endpoints
@app.route("/")
def main_page():
    # # Remember to use scalars to convert from obj to list
    alldbcafes = db.session.execute(db.select(Cafe)).scalars()
    return render_template("index.html", cafes=alldbcafes, current_user=current_user)

@app.route("/cafe/<int:cafe_id>", methods=["GET","POST"])
def show_cafe(cafe_id):
    commentform = CommentForm()
    selected_cafe = db.get_or_404(Cafe, cafe_id)

    if commentform.validate_on_submit():
        if not current_user.is_authenticated:
            flash("You need to be logged in to do this!")
            return redirect(url_for("login"))
        
        new_comment = Comment(
            body = commentform.comment.data,
            author=current_user,
            cafe=selected_cafe
        )

        db.session.add(new_comment)
        db.session.commit()
        return redirect(url_for("show_cafe",cafe_id=selected_cafe.id))
    return render_template("cafe.html", form=commentform, cafe=selected_cafe)

@app.route("/add-cafe", methods=["GET","POST"])
@admin_only
def add_cafe():
    cafeform = AddNewCafe()
    if cafeform.validate_on_submit():
        new_cafe = Cafe(
            name=cafeform.name.data,
            map_url=cafeform.map_url.data,
            img_url=cafeform.img_url.data,
            location=cafeform.location.data,
            has_sockets=bool_to_int(cafeform.has_sockets.data),
            has_toilet=bool_to_int(cafeform.has_toilet.data),
            has_wifi=bool_to_int(cafeform.has_wifi.data),
            can_take_calls=bool_to_int(cafeform.can_take_calls.data),
            seats=cafeform.seats.data,
            coffee_price=f"£{cafeform.coffee_price.data}"
        )

        db.session.add(new_cafe)
        db.session.commit()
        return (redirect(url_for("main_page")))
    return render_template("add-cafe.html", form=cafeform, current_user=current_user)

@app.route("/edit-cafe/<int:cafe_id>", methods=["GET", "POST"])
@admin_only
def edit_cafe(cafe_id):
    selected_cafe = db.get_or_404(Cafe, cafe_id)
    editform = AddNewCafe(
        name=selected_cafe.name,
        map_url=selected_cafe.map_url,
        img_url=selected_cafe.img_url,
        location=selected_cafe.location,
        has_sockets=int_to_bool(selected_cafe.has_sockets),
        has_toilet=int_to_bool(selected_cafe.has_toilet),
        has_wifi=int_to_bool(selected_cafe.has_wifi),
        can_take_calls=int_to_bool(selected_cafe.can_take_calls),
        seats=selected_cafe.seats,
        coffee_price=float(selected_cafe.coffee_price[1:])
    )

    if editform.validate_on_submit():
        selected_cafe.name=editform.name.data
        selected_cafe.map_url=editform.map_url.data
        selected_cafe.img_url=editform.img_url.data
        selected_cafe.location=editform.location.data
        selected_cafe.has_sockets=int(bool_to_int(editform.has_sockets.data))
        selected_cafe.has_toilet=int(bool_to_int(editform.has_toilet.data))
        selected_cafe.has_wifi=int(bool_to_int(editform.has_wifi.data))
        selected_cafe.can_take_calls=int(bool_to_int(editform.can_take_calls.data))
        selected_cafe.seats=editform.seats.data
        selected_cafe.coffee_price=f"£{editform.coffee_price.data}"
        db.session.commit()
        return redirect(url_for("main_page"))
    return render_template("add-cafe.html", cafe_id=selected_cafe.id, form=editform, editing=True, current_user=current_user)

@app.route("/delete-cafe/<int:cafe_id>", methods=["GET"])
def delete_cafe(cafe_id):
    selected_cafe = db.get_or_404(Cafe, cafe_id)
    db.session.delete(selected_cafe)
    db.session.commit()
    return redirect(url_for("main_page"))

@app.route("/cafe/<int:cafe_id>/comments/<int:comment_id>", methods=["GET", "POST"])
def delete_comment(cafe_id, comment_id):
    selected_comment = db.get_or_404(Comment, comment_id)
    db.session.delete(selected_comment)
    db.session.commit()
    return redirect(url_for("show_cafe", cafe_id=cafe_id))

@app.route("/register", methods=["GET", "POST"])
def register():
    registerform = Register()
    if registerform.validate_on_submit():
        if db.session.execute(db.select(User).where(User.email==registerform.email.data)):
            flash("User email already exists, login using it")
            return redirect((url_for("login")))
        if registerform.password.data == registerform.repeat_pw.data:
            hashed_pw = generate_password_hash(registerform.password.data)
            new_user = User(
                username = registerform.username.data,
                email = registerform.email.data,
                password = hashed_pw,
                role = "user"
            )
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user)
            return redirect(url_for('main_page'))
        else:
            pass
    return render_template("register.html", form=registerform, current_user=current_user)

@app.route("/login", methods=["GET","POST"])
def login():
    loginform = Login()
    if loginform.validate_on_submit():
        result = db.session.execute(db.select(User).where(User.email == loginform.email.data))
        user = result.scalar()
        if not user:
            flash("User does not exist, please make a new account")
            return redirect(url_for("login"))
        if not check_password_hash(user.password, loginform.password.data):
            flash("Wrong password")
            return redirect(url_for("login"))
        else:
            login_user(user)
            return redirect(url_for("main_page"))
    return render_template("login.html", form=loginform, current_user=current_user)

@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("main_page"))

# Utility
def bool_to_int(input:bool)->int:
    return 1 if input else 0

def int_to_bool(input:int)->bool:
    return True if input==1 else False

if __name__ == "__main__":
    app.run(debug=True)