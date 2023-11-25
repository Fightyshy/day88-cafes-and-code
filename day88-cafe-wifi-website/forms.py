from flask_wtf import FlaskForm
from wtforms import StringField, URLField, BooleanField, SelectField, DecimalField, SubmitField, PasswordField, EmailField
from wtforms.validators import DataRequired, URL, Email
from flask_ckeditor import CKEditorField

class AddNewCafe(FlaskForm):
    name = StringField(label="what's the name of the cafe? ", validators=[DataRequired()])
    map_url = URLField(label="Share with us the cafe's map location: ", validators=[DataRequired(), URL()])
    img_url = URLField(label="Share with us a image link of the location: ", validators=[DataRequired(), URL()])
    location = StringField(label="Location: ", validators=[DataRequired()])
    has_sockets = BooleanField(label="Does the cafe have sockets? ")
    has_toilet = BooleanField(label="Does the cafe have toilets? ")
    has_wifi = BooleanField(label="Does the cafe have wifi? ")
    can_take_calls = BooleanField(label="Can you take calls? ")
    seats = SelectField(label="Number of seats: ", choices=["0-10","10-20","20-30","30-40","40-50","50+"], default="0-10")
    coffee_price = DecimalField(label="Coffee price (£): ", validators=[DataRequired()])
    submit = SubmitField(label="Add to the list!")

class CommentForm(FlaskForm):
    comment = CKEditorField(label="Comment", validators=[DataRequired()])
    submit = SubmitField(label="Comment")

class Login(FlaskForm):
    email = EmailField(label="Email", validators=[DataRequired(), Email()])
    password = PasswordField(label="Password", validators=[DataRequired()])
    submit = SubmitField(label="Login")

class Register(FlaskForm):
    username = StringField(label="Username", validators=[DataRequired()])
    email = EmailField(label="Email Address", validators=[DataRequired(), Email()])
    password = PasswordField(label="Password", validators=[DataRequired()])
    repeat_pw = PasswordField(label="Repeat Password", validators=[DataRequired()])
    submit = SubmitField(label="Signup")