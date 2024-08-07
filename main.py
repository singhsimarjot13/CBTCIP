from datetime import date
from flask import Flask, abort, render_template, redirect, url_for, flash,request
from flask_bootstrap import Bootstrap5
from flask_ckeditor import CKEditor
from flask_gravatar import Gravatar
from flask_login import UserMixin, login_user, LoginManager, current_user, logout_user,login_required
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship, DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Text,Float
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
import os
import  sqlalchemy.exc
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
OWN_EMAIL=os.environ.get('EMAIL')
OWN_PASSWORD=os.environ.get('PASSWORD')

login_=LoginManager()
app = Flask(__name__)
app.config['SECRET_KEY'] =os.environ.get('KEY')
Bootstrap5(app)
login_.init_app(app)
class Base(DeclarativeBase):
    pass
app.config['SQLALCHEMY_DATABASE_URI'] =os.environ.get('DB')
db = SQLAlchemy(model_class=Base)
db.init_app(app)
@login_.user_loader
def load_user(user_id):
    return db.get_or_404(User,user_id)


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String, unique=True, nullable=False)
    password = db.Column(db.String, nullable=False)
    name = db.Column(db.String, nullable=False)
    username = db.Column(db.String, nullable=False)

    # Relationships
    events = db.relationship("Eventcreate", back_populates="user")
    guests = db.relationship("Guest", back_populates="user")


class Eventcreate(db.Model):
    __tablename__ = "create_event"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(250), unique=True, nullable=False)
    time = db.Column(db.String(250), nullable=False)
    date = db.Column(db.String(250), nullable=False)
    description = db.Column(db.Text, nullable=False)
    location = db.Column(db.String(250), nullable=False)
    category = db.Column(db.String(250), nullable=False)
    organizer = db.Column(db.String(150), nullable=False)

    # Foreign key column
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # Relationships
    user = db.relationship("User", back_populates="events")
    budgets = db.relationship("Budget", back_populates="event")
    guests = db.relationship("Guest", back_populates="event")


class Budget(db.Model):
    __tablename__ = "budget"
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('create_event.id'), nullable=False)
    expense_name = db.Column(db.String(250), nullable=False)
    expense_amount = db.Column(db.Float, nullable=False)

    # Relationship with Eventcreate
    event = db.relationship("Eventcreate", back_populates="budgets")


class Guest(db.Model):
    __tablename__ = "guests"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), nullable=False)
    rsvp = db.Column(db.String(10), default='pending')

    # Foreign key columns
    event_id = db.Column(db.Integer, db.ForeignKey('create_event.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # Relationships
    event = db.relationship("Eventcreate", back_populates="guests")
    user = db.relationship("User", back_populates="guests")

class Vendor(db.Model):
    __tablename__='Vendor'
    id=db.Column(db.Integer,primary_key=True, autoincrement=True)
    name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), nullable=False)
    contact_person=db.Column(db.String(150), nullable=False)
    phone_number=db.Column(db.String(20), nullable=False)
with app.app_context():
    db.create_all()

@app.route('/register',methods=['GET','POST'])
def register():
    if request.method=='POST':
        email=request.form['email']
        username=request.form['username']
        password=request.form['password']
        name=request.form['full-name']
        confirm_password=request.form['confirm-password']
        check_email=db.session.execute(db.Select(User).where(User.email==email))
        user=check_email.scalar()
        if user:
            # User already exists
            flash("You've already signed up with that email, log in instead!")
            return redirect(url_for('login'))
        elif password==confirm_password:
            user=User(
                email=email,
                username=username,
                password=password,
                name=name
            )
            try:
                db.session.add(user)
                db.session.commit()
                return redirect(url_for('login'))
            except:
                print('error occured')
        else:
            flash('your congfirm password and password doesnt match')
    return render_template('register.html',user=current_user)
@app.route('/login',methods=['GET','POST'])
def login():
    if request.method=='POST':
        email=request.form['username']
        password=request.form['password']
        check_user=db.session.execute(db.Select(User).where(User.username==email)).scalar()
        if check_user:
            if check_user.password==password:
                login_user(check_user)
                return redirect(url_for('home'))
            else:
                flash('Wrong password,try again!')
        else:
            flash('you are not registered,register')
            return redirect(url_for('register'))
    return render_template('login.html')
@app.route('/')
def home():
    return render_template('index.html',user=current_user)

@app.route('/eventcreate',methods=['GET','POST'])
@login_required
def event():
    if request.method=='POST':
        name=request.form['event-name']
        date=request.form['event-date']
        time=request.form['event-time']
        location=request.form['event-location']
        description=request.form['event-description']
        organizer=request.form['event-organizer']
        category=request.form['event-category']
        add_event=Eventcreate(
            name=name,
            date=date,
            time=time,
            location=location,
            description=description,
            organizer=organizer,
            category=category,
            user_id=current_user.id
        )
        db.session.add(add_event)
        db.session.commit()
        return redirect(url_for('list'))
    return render_template('event_creator.html',user=current_user)
@login_required
@app.route('/event_list')
def list():
    result = db.session.execute(db.select(Eventcreate))
    result = result.scalars().all()
    return render_template('event_list.html',user=current_user,event=result)

@app.route('/guest_list/<int:event_id>',methods=['GET','POST'])
@login_required
def guest_list(event_id):
    if request.method=='POST':
        name=request.form['name']
        email=request.form['email']
        add_guest=Guest(
            event_id=event_id,
            name=name,
            email=email,
            user_id=current_user.id
        )
        db.session.add(add_guest)
        db.session.commit()
        guest_mail=db.session.execute(db.select(Guest).where(Guest.name==name)).scalar()
        send_email(guest_mail.email,guest_mail.id)
        redirect(url_for('guest_list',event_id=event_id))
    guest = db.session.execute(db.select(Guest).where(Guest.event_id == event_id)).scalars().all()
    return render_template('guest.html',user=current_user,guest=guest,event_id=event_id)
@app.route('/delete_guest/<int:guest_id>',methods=['POST'])
@login_required
def delete_guest(guest_id):
    to_delete=db.session.execute(db.select(Guest).where(Guest.id==guest_id)).scalar()
    db.session.delete(to_delete)
    db.session.commit()
    return redirect(url_for('guest_list',event_id=to_delete.event_id))

@app.route('/invitation/<int:event_id>')
@login_required
def invitation(event_id):
    guests = Guest.query.all()  # Fetch all guests or filter as needed
    return render_template('invitation.html',user=current_user,guests=guests,event_id=event_id)

@app.route('/send_invitation', methods=['POST'])
@login_required
def send_invitation():
    guest_name = request.form['guest-name']
    guest_email = request.form['guest-email']
    event_id=request.form.get('event-id')
    # Create new guest entry
    new_guest = Guest(name=guest_name, email=guest_email, rsvp='pending',user_id=current_user.id,event_id=event_id)
    db.session.add(new_guest)
    db.session.commit()

    # Send the invitation email
    try:
        send_email(guest_email, new_guest.id)
        flash('Invitation sent successfully!', 'success')
    except Exception as e:
        print(e)
        flash('Failed to send invitation. Please try again later.', 'error')

    return redirect(url_for('invitation',event_id=event_id))
def send_email(recipient, guest_id):
    # Update the email content with a dynamic link
    url_yes = url_for('handle_rsvp', response='yes', guest_id=guest_id, _external=True)
    url_no = url_for('handle_rsvp', response='no', guest_id=guest_id, _external=True)
    print(f"Yes URL: {url_yes}")
    print(f"No URL: {url_no}")
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {{
                font-family: Arial, sans-serif;
                background-color: #f4f4f4;
                margin: 0;
                padding: 20px;
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
                color: #333;
            }}
            .container {{
                background: white;
                padding: 20px;
                border-radius: 8px;
                box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
                text-align: center;
            }}
            p {{
                font-size: 18px;
                margin-bottom: 20px;
            }}
            a {{
                display: inline-block;
                padding: 10px 20px;
                margin: 10px;
                color: white;
                text-decoration: none;
                border-radius: 4px;
                transition: background-color 0.3s ease;
            }}
            a.yes {{
                background-color: #28a745;
            }}
            a.yes:hover {{
                background-color: #218838;
            }}
            a.no {{
                background-color: #dc3545;
            }}
            a.no:hover {{
                background-color: #c82333;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <p>🎉 Hey there! You're invited to an exclusive event. We can't wait to see you there! Can you make it? 🎉</p>
            <a href="{url_for('handle_rsvp', response='yes', guest_id=guest_id, _external=True)}" class="yes">Yes</a>
            <a href="{url_for('handle_rsvp', response='no', guest_id=guest_id, _external=True)}" class="no">No</a>
        </div>
    </body>
    </html>
    """

    email_message = MIMEMultipart("alternative")
    email_message["Subject"] = "Invitation for my event"
    email_message["From"] = OWN_EMAIL
    email_message["To"] = recipient

    email_message.attach(MIMEText(html_content, "html"))

    with smtplib.SMTP("smtp.gmail.com", 587) as connection:
        connection.starttls()
        connection.login(OWN_EMAIL, OWN_PASSWORD)
        connection.sendmail(OWN_EMAIL, recipient, email_message.as_string())


@app.route('/rsvp/<string:response>/<int:guest_id>', methods=['GET'])
@login_required
def handle_rsvp(response, guest_id):
    print(f"Received response: {response}, guest_id: {guest_id}")
    # Find the guest by ID
    guest = Guest.query.get_or_404(guest_id)
    if guest:
        guest.rsvp = response
        db.session.commit()
        flash(f'Your RSVP response "{response}" has been recorded.', 'success')
    else:
        flash('Guest not found.', 'error')

    return f'You clicked {response.capitalize()}!'
@app.route('/about')
def about():
    return render_template('about.html',user=current_user)
@app.route('/budget-tracking/<int:event_id>',methods=['GET','POST'])
@login_required
def b_tracking(event_id):
    if request.method=='POST':
        expense_name=request.form['item-name']
        expense_amt=request.form['item-cost']
        new_budget=Budget(
            event_id=event_id,
            expense_name=expense_name,
            expense_amount=expense_amt
        )
        db.session.add(new_budget)
        db.session.commit()
        return redirect(url_for('b_tracking',event_id=event_id))
    budgets=db.session.execute(db.select(Budget).where(Budget.event_id==event_id)).scalars().all()
    total_budget = sum(budget.expense_amount for budget in budgets)
    return render_template('budget_tracking.html',user=current_user,budgets=budgets,total_budget=total_budget,event_id=event_id)
@app.route("/delete/<int:budget_id>")
@login_required
def delete(budget_id):
    to_delete = db.get_or_404(Budget,budget_id)
    db.session.delete(to_delete)
    db.session.commit()
    return redirect(url_for('b_tracking',event_id=current_user.id))

@app.route('/contact',methods=['GET','POST'])
def contact():
    if request.method=='POST':
        name=request.form['name']
        email=request.form['email']
        phone=request.form['phone']
        subject=request.form['subject']
        message=request.form['message']
        email_message = f"Subject:{subject}\n\nName: {name}\nEmail: {email}\nPhone: {phone}\nMessage:{message}"
        with smtplib.SMTP("smtp.gmail.com") as connection:
            connection.starttls()
            connection.login(OWN_EMAIL, OWN_PASSWORD)
            connection.sendmail(OWN_EMAIL, OWN_EMAIL, email_message)
        flash('your message sent succesfully!')
    return render_template('contact.html',user=current_user)

@app.route('/vendor-cordination/<int:event_id>',methods=['GET','POST'])
@login_required
def vendor(event_id):
    if request.method=='POST':
        vendor_name=request.form['vendor-name']
        contact_person=request.form['contact-person']
        vendor_email=request.form['vendor-email']
        vendor_phone=request.form['vendor-phone']
        add_vendor=Vendor(
            name=vendor_name,
            email=vendor_email,
            contact_person=contact_person,
            phone_number=vendor_phone
        )
        db.session.add(add_vendor)
        db.session.commit()
        return redirect(url_for('vendor',event_id=event_id))
    vendor_add=db.session.execute(db.select(Vendor)).scalars().all()
    return render_template('vendor.html',user=current_user,vendor_add=vendor_add,event_id=event_id)
@app.route('/edit_vendor/<int:event_id>',methods=['POST'])
@login_required
def edit_vendor(event_id):
    vendor_id = request.form['vendor-id']
    name = request.form['vendor-name']
    contact_person = request.form['contact-person']
    email = request.form['vendor-email']
    number = request.form['vendor-phone']

    vendor = db.session.execute(db.select(Vendor).where(Vendor.id == vendor_id)).scalar()
    if vendor:
        vendor.name = name
        vendor.contact_person = contact_person
        vendor.email = email
        vendor.phone_number = number
        db.session.commit()

    return redirect(url_for('vendor', event_id=event_id))
@app.route('/delete_vendor/<int:vendor_id>/<int:event_id>')
@login_required
def delete_vendor(vendor_id,event_id):
    to_delete_vendor=db.session.execute(db.select(Vendor).where(Vendor.id==vendor_id)).scalar()
    db.session.delete(to_delete_vendor)
    db.session.commit()
    return redirect(url_for('vendor',event_id=event_id))

@app.route('/bill')
@login_required
def bill():
    return render_template('bill.html',user=current_user)
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))
if __name__=='__main__':
    app.run(debug=True,port=5000)