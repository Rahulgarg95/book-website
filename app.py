import os
import json

from flask import Flask, session, render_template, request, redirect, flash
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

from werkzeug.security import check_password_hash, generate_password_hash

import requests

#from helpers import login_required

app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv('DATABASE_URL'))
db = scoped_session(sessionmaker(bind=engine))
db=db()

@app.route("/login", methods=["GET","POST"])
def login():
    if(request.method == "POST"):
        #Checking if username is entered
        if(request.form.get("username")):
            name=request.form.get("username")
        else:
            msg="Please enter username"
            return render_template("error.html",msg=msg)
    
        #Checking if password is entered
        if(request.form.get("password")):
            password=request.form.get("password")
        else:
            msg="Please enter password"
            return render_template("error.html",msg=msg)
        
        result=db.execute("SELECT * FROM users WHERE user_id= :user_name",{"user_name":name}).fetchone()
        if(not result[0]):
            msg="Invalid userid. Please enter different id or create a account"
            return render_template("error.html",msg=msg)
        
        elif(not check_password_hash(result[1], password)):
            msg="Please enter valid password"
            return render_template("error.html",msg=msg)

        session["user_name"]=name
        print("Session details: " + session["user_name"])

        return redirect("/")

    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """ Log user out """

    # Forget any user ID
    session.clear()

    # Redirect user to login form
    return redirect("/")

#User registeration
@app.route("/register", methods=["GET","POST"])
def register():
    #User submitting the form
    if(request.method == "POST"):
        #Checking if username is entered
        if(request.form.get("username")):
            name=request.form.get("username")
        else:
            msg="Please enter username"
            return render_template("error.html",msg=msg)

        #Checking if password is entered
        if(request.form.get("password")):
            password=request.form.get("password")
        else:
            msg="Please enter password"
            return render_template("error.html",msg=msg)
        if(request.form.get("conf_password")):
            conf_password=request.form.get("conf_password")
        else:
            msg="Please enter password again"
            return render_template("error.html",msg=msg)
        
        #Check for email entered
        if(request.form.get("email")):
            email_id=request.form.get("email")
        else:
            msg="Please enter email id"
            return render_template("error.html",msg=msg)
        
        #Check if username already exists
        has_user_id=db.execute("SELECT user_id FROM users WHERE user_id= :user_name",{"user_name":name}).fetchone()
        if(has_user_id):
            msg="Entered Username already exists.... Please enter a different username"
            return render_template("error.html",msg=msg)

        #Check if the passwords entered match
        if(password != conf_password):
            msg="Passwords entered do not match. Kindly re-enter password again!!!!!!"
            return render_template("error.html",msg=msg)

        #Hashing the password
        hash_pass=generate_password_hash(password, method='pbkdf2:sha256', salt_length=8)

        #Making entry in db
        db.execute("INSERT INTO users (user_id,password,email) VALUES(:user_name, :password,:email_id)", {"user_name":name,"password":hash_pass,"email_id":email_id})

        db.commit()

        return redirect("/login")
    else:
        return render_template("register.html")

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/search", methods=["GET"])
def search_book():
    if(not request.args.get("search_book")):
        msg="Please enter book details"
        return render_template("error.html",msg=msg)

    book=request.args.get("search_book")
    book=book.title()

    search_cmd = "%" + book + "%"

    result=db.execute("SELECT isbn, title, author, year FROM books WHERE isbn LIKE :book_srch OR author LIKE :book_srch OR title LIKE :book_srch",{"book_srch":search_cmd})

    if(result.rowcount == 0):
        msg="No records found with given input"
        return render_template("error.html", msg=msg)

    array_result=result.fetchall()

    return render_template("results.html", books=array_result)

@app.route("/book/<isbn>", methods=["GET","POST"])
def book_details(isbn):

    if request.method == "POST":
        current_user=session["user_name"]

        book_rating = request.form.get("rating")
        comment = request.form.get("review_desc")

        row=db.execute("SELECT * FROM reviews WHERE book_id = :book_id AND user_name = :user_name",{"book_id":isbn,"user_name":current_user})

        if(row.rowcount == 1):
            return redirect("/book/" + isbn)

        book_rating=int(book_rating)

        db.execute("INSERT INTO reviews (book_id, user_name, review_desc, rating) VALUES(:book_id, :user_name, :review_desc, :rating)",{"book_id":isbn, "user_name":current_user, "review_desc":comment, "rating":book_rating})

        db.commit()

        return redirect("/book/" + isbn)
    else:
        row=db.execute("SELECT isbn, title, author, year FROM books WHERE isbn = :isbn_no",{"isbn_no":isbn})

        bookinfo=row.fetchall()

        api_key='yu2H1WDzEBGlVEnPezV9Jg'
        query=requests.get('https://www.goodreads.com/book/review_counts.json',params={"key":api_key, "isbns": isbn})

        response=query.json()

        bookinfo.append(response)

        result=db.execute("SELECT users.user_id,review_desc,rating,to_char(comment_ts, 'DD Mon YY - HH24:MI:SS') as comment_ts FROM users INNER JOIN reviews ON users.user_id = reviews.user_name WHERE book_id=:isbn ORDER BY comment_ts",{"isbn":isbn})

        reviews=result.fetchall()

        print("Bookinfo: " + str(bookinfo))

        print("Reviews: " + str(reviews))

        return render_template("book_det.html", bookInfo=bookinfo, reviews=reviews)