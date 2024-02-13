import os
import smtplib
from datetime import date
from flask import Flask, render_template, redirect, url_for, flash
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Email


# SMTP Configuration
MAIL_RECIPIENT = os.environ.get("MAIL_RECIPIENT")
MAIL_SMTP_ADDRESS = os.environ.get("MAIL_SMTP_ADDRESS")
MAIL_APP_PW = os.environ.get("MAIL_APP_PW")
MAIL_SMTP_HOST = os.environ.get("MAIL_SMTP_HOST")

# Flask Configuration
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('FLASK_KEY')
Bootstrap5(app)

# CONNECT TO DB
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DB_URI")
db = SQLAlchemy()
db.init_app(app)


def send_email(name, email, message):
    email_message = f"Subject:New contact from portfolio contact form - {email}\n\nName: {name}\nEmail: {email}\nMessage:\n{message}"
    with smtplib.SMTP(MAIL_SMTP_HOST, port=587) as connection:
        connection.starttls()
        connection.login(MAIL_SMTP_ADDRESS, MAIL_APP_PW)
        connection.sendmail(MAIL_SMTP_ADDRESS, MAIL_RECIPIENT, email_message)


class ContactForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired()])
    email = StringField("Email", validators=[DataRequired(), Email("Please enter email address in correct format.")])
    message = TextAreaField("Message", validators=[DataRequired()])
    send_message = SubmitField("Send Message")


class Contacts(db.Model):
    __tablename__ = "contacts"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(250), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    message = db.Column(db.Text, nullable=False)
    date = db.Column(db.String(250), nullable=False)


with app.app_context():
    db.create_all()


@app.route('/', methods=["GET", "POST"])
def home():
    contact_form = ContactForm()
    if contact_form.validate_on_submit():

        # Check if user email is already present in the database
        result = db.session.execute(db.select(Contacts).where(Contacts.email == contact_form.email.data))
        contact = result.scalar()
        if contact:
            # Contact already made
            flash("You've already contacted me, please wait for my reaction!")
            return redirect(url_for("home"))
        try:
            send_email(contact_form.name.data, contact_form.email.data, contact_form.message.data)
        except Exception as e:
            print(e)
            flash("Something went wrong, try again later!")
        else:
            new_contact = Contacts(
                email=contact_form.email.data,
                name=contact_form.name.data,
                message=contact_form.message.data,
                date=date.today()
            )
            db.session.add(new_contact)
            db.session.commit()
            flash("Email successfully sent!")
            return redirect(url_for("home"))
    return render_template("index.html", contact_form=contact_form)


if __name__ == "__main__":
    app.run(debug=True, port=5001)
