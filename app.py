import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from datetime import datetime
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")

# Make sure API key is set
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/", methods=["GET", "POST"])
@login_required
def index():
    if request.method == "POST":
        # check for symbol
        if not request.form.get("symbol"):
            return apology("an error has accured", 500)
        symbol = request.form.get("symbol")
        # check for ammount shares sould/bought
        if not request.form.get("shares"):
            return redirect("/")

        number_shares = int(request.form.get("shares"))

        # make shure the user owns shares of the stock
        if not db.execute("SELECT * FROM stocks WHERE user_id =(?) AND symbol = (?)", session["user_id"], request.form.get("symbol")):
            return apology("you dont own sahres in this stock")

        ammount = int(db.execute("SELECT * FROM stocks WHERE user_id = (?) AND symbol = (?)",
                                            session["user_id"], symbol)[0]["ammount"])

        # get price per share
        price = lookup(request.form.get("symbol"))["price"]
        # get the users balance
        balance = float(db.execute("SELECT cash FROM users WHERE id = (?)", session["user_id"])[0]["cash"])

        # makeing shure the numbers of shares can be sould
        if number_shares < (- ammount):
            return appology("cant selll more then owned")

        if number_shares == 0:
            return redirect("/")

        # do the buying
        elif number_shares > 0:
            # check if he has ennougth money to buy the stock
            if balance < price * number_shares:
                return appology("balance is to low")
            # execute the transaction, set new balance
            db.execute("UPDATE users SET cash = (?) WHERE id = (?)", (balance - (price * number_shares)), session["user_id"])
            # add shares to the profile
            db.execute("UPDATE stocks SET ammount = (?) WHERE user_id = (?) AND symbol = (?)", (ammount + number_shares), session["user_id"], symbol)
            # log the purches
            db.execute("INSERT INTO purcheses (user_id, symbol, ammount, price, date, type) VALUES(?, ?, ?, ?, ?, ?)",
                   session["user_id"], symbol, number_shares, price, datetime.now().strftime("%d/%m %H:%M"), "buy")

        elif number_shares < 0:
            if number_shares == - ammount:
                # execute the transaction, set new balance
                db.execute("UPDATE users SET cash = (?) WHERE id = (?)", (balance + (price * (- number_shares))), session["user_id"])
                # delete the share from portfolio
                db.execute("DELETE FROM stocks WHERE user_id = (?) AND symbol = (?)", session["user_id"], symbol)
                # lock purches
                db.execute("INSERT INTO purcheses (user_id, symbol, ammount, price, date, type) VALUES(?, ?, ?, ?, ?, ?)",
                   session["user_id"], symbol, (- number_shares), price, datetime.now().strftime("%d/%m %H:%M"), "sell")
            else:
                # execute the transaction, set new balance
                db.execute("UPDATE users SET cash = (?) WHERE id = (?)", (balance + (price * (- number_shares))), session["user_id"])
                # add shares to the profile
                db.execute("UPDATE stocks SET ammount = (?) WHERE user_id = (?) AND symbol = (?)", (ammount + number_shares), session["user_id"], symbol)
                 # lock purches
                db.execute("INSERT INTO purcheses (user_id, symbol, ammount, price, date, type) VALUES(?, ?, ?, ?, ?, ?)",
                   session["user_id"], symbol, (- number_shares), price, datetime.now().strftime("%d/%m %H:%M"), "sell")
        return redirect("/")

    else:
        # select the needet informations from the db
        stocks = db.execute("SELECT * FROM stocks WHERE user_id =(?)", session["user_id"])
        # caldulate the current cash of the user
        cash = float(db.execute("SELECT cash FROM users WHERE id = (?)", session["user_id"])[0]["cash"])
        # creating a list for the stocks owned whitch will store dictonaries
        ls_stocks = []

        # total = cash + value of all stocks
        total = cash
        for stock in stocks:
            # lookingup the stock by symbol
            look = lookup(stock["symbol"])
            # creating dic with the needet infos for index
            ds = {"price": usd(float(lookup(stock["symbol"])["price"])),
                "symbol": stock["symbol"],
                "name": look["name"],
                "shares": stock["ammount"],
                "total": usd(float(look["price"]) * float(stock["ammount"])), }
            # adding the stocks value to total
            total = total + float(look["price"]) * float(stock["ammount"])
            # append to list
            ls_stocks.append(ds)
        # render the website
        return render_template("index.html", stocks=ls_stocks, cash=usd(cash), TOTAL=usd(total))


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    # check if the request is post
    if request.method == "POST":

        # check if a symbole was given
        if not request.form.get("symbol"):
            return apology("need a symbol")

        # check if it exists
        if not lookup(request.form.get("symbol")):
            return apology("Symbol does not exist")

        # check if an amout has been choosen if not returne error
        if not request.form.get("shares"):
            return apology("need to give ammount of shares")

        # get the ammount as string from the request
        ammount = request.form.get("shares")

        # check if the sting is mumeric
        if not ammount.isnumeric():
            return apology("shares needs to be a positiv int")

        # turn into int
        ammount = int(ammount)

        # look if ammount is a positiv int
        if ammount < 1:
            return apology("shares needs to be a positiv int")

        # get the price of the stock from lookup
        price = lookup(request.form.get("symbol"))["price"]

        # check the current balance of the user
        balance = db.execute("SELECT cash FROM users WHERE id = (?)", session["user_id"])[0]["cash"]

        # check if the user has enougth chash
        if price * ammount > balance:
            return apology("your balance is to low")

        # set new balance
        db.execute("UPDATE users SET cash = (?) WHERE id = (?)", (balance - price * ammount), session["user_id"])

        # lock the buy in the purcheses lock
        db.execute("INSERT INTO purcheses (user_id, symbol, ammount, price, date, type) VALUES(?, ?, ?, ?, ?, ?)",
                   session["user_id"], request.form.get("symbol"), ammount, price, datetime.now().strftime("%d/%m %H:%M"), "buy")

        # add stock if user does not own allready
        if not db.execute("SELECT * FROM stocks WHERE user_id = (?) AND symbol = (?)", session["user_id"], request.form.get("symbol")):
            db.execute("INSERT INTO stocks (user_id, symbol, ammount) VALUES(?, ?,?)",
                       session["user_id"], request.form.get("symbol"), ammount)

        # change the ammount if he owns
        else:
            number = db.execute("SELECT ammount FROM stocks WHERE user_id = (?) AND symbol = (?)",
                                session["user_id"], request.form.get("symbol"))[0]["ammount"]
            db.execute("UPDATE stocks SET ammount = (?) WHERE user_id = (?) AND symbol = (?)",
                       (number + ammount), session["user_id"], request.form.get("symbol"))

        # return to homepage
        return redirect("/")

    # if GET render the html
    else:
        return render_template("buy.html")


@app.route("/history")
@login_required
def history():
    history = db.execute("SELECT * FROM purcheses WHERE user_id = (?) ORDER BY purches_id DESC", session["user_id"])
    return render_template("history.html", history=history)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    if request.method == "POST":

        # check the input
        if not request.form.get("symbol"):
            return apology("no symbole inputed")
        # check ikf th symbol does return a result
        if not lookup(request.form.get("symbol")):
            return apology("symbol does not exist")

        # save result in a carriable and use it to render the templet
        info = lookup(request.form.get("symbol"))
        return render_template("quoted.html", info=info, a=20.00)

    else:
        return render_template("quote.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":

        #Ensure there was a Username given
        if not request.form.get("username"):
             return render_template("register.html", missing="You have to input a Username")

        #ensure a password was given
        elif not request.form.get("password"):
             return render_template("register.html", pword="You need to imput the same password two times")

        #ensure there is a conformaiton of the password
        elif not request.form.get("confirmation"):
             return render_template("register.html", pword="You need to imput the same password two times")

        # Check if username is free
        if db.execute("SELECT * FROM users WHERE username = (?)", request.form.get("username")):
             return render_template("register.html", used="Username is already used")

        # check if password math
        elif request.form.get("confirmation") == request.form.get("password"):
            # get the inputet password from the request to chek if it meets the requierments
            password = request.form.get("password")
            # chasks if it has atleast 8 caracters
            if len(password) < 8:
                return render_template("register.html", pword="Password needs to have atlast 8 caracters")
            #cheks if it contains a number
            valid = False

            for i in password:
                if i.isnumeric():
                    valid = True

            if not valid:
                return render_template("register.html", pword="Password has to contain a number")
            # checks if it contains symbols
            valid1 = False

            for i in password:
                if not i.isalnum():
                    valid1 = True
            if not valid1:
                return render_template("register.html", pword="Password has to contain a symbol")

            # add new accout to the database
            db.execute("INSERT INTO users (username, hash) VALUES(?, ?)",
                       request.form.get("username"), generate_password_hash(request.form.get("password")))

            # create a seccion for the user
            rows = db.execute("SELECT * FROM users WHERE username = (?)", request.form.get("username"))
            session["user_id"] = rows[0]["id"]
            return redirect("/")

        return render_template("register.html", pword="Passwords do not math")
    else:
        return render_template("register.html")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    if request.method == "POST":
        # CHeck the Post request
        if not request.form.get("symbol"):
            return apology("Need a symbol")

        if not request.form.get("shares"):
            return apology("Need ammount of shares")

        # gets the constants symbols, ammount of shares sould and price
        symbol = request.form.get("symbol")
        shares_sould = int(request.form.get("shares"))
        price = float(lookup(symbol)["price"])

        if not db.execute("SELECT cash FROM users WHERE id = (?)", session["user_id"])[0]["cash"]:
            return apology("upps")

        # gets the balance of the user
        cash = db.execute("SELECT cash FROM users WHERE id = (?)", session["user_id"])[0]["cash"]

        # checks if its a positiv int
        if shares_sould < 1:
            return apology("shares needs to be a positiv int")

        # checks if the user owns the stock
        if not db.execute("SELECT * FROM stocks WHERE user_id = (?) AND symbol = (?)", session["user_id"], symbol):
            return apology("cant sell stock whitch is not owned")

        # ammount of owned stocks
        shares_owned = db.execute("SELECT ammount FROM stocks WHERE user_id = (?) AND symbol = (?)",
                                  session["user_id"], symbol)[0]["ammount"]

        # if all get sould
        if shares_sould == shares_owned:
            # erais the stock from the owned stocks whitch get displayes in history
            db.execute("DELETE FROM stocks WHERE user_id = (?) AND symbol = (?)", session["user_id"], symbol)
            db.execute("UPDATE users SET cash = (?) WHERE id = (?)", (cash + price * shares_sould), session["user_id"])
            # log the sell
            db.execute("INSERT INTO purcheses (user_id, symbol, ammount, price, date, type) VALUES (?, ?, ?, ?, ?, ?)",
                       session["user_id"], symbol, shares_sould, price, datetime.now().strftime("%d/%m %H:%M"), "sell")

        # if not all are sould
        elif shares_sould < shares_owned:
            # update the owned stocks
            db.execute("UPDATE stocks SET ammount = (?) WHERE user_id = (?) AND symbol = (?)",
                       (shares_owned - shares_sould), session["user_id"], symbol)
            # log the event
            db.execute("UPDATE users SET cash = (?) WHERE id = (?)", (cash + price * shares_sould), session["user_id"])
            db.execute("INSERT INTO purcheses (user_id, symbol, ammount, price, date, type) VALUES (?, ?, ?, ?, ?, ?)",
                       session["user_id"], symbol, shares_sould, price, datetime.now().strftime("%d/%m %H:%M"), "sell")

        # if they want to sell more then owned
        else:
            return apology("You cant sell more then you own")
        return redirect("/")

        # if get requst to the server
    else:
        symbols = db.execute("SELECT symbol FROM stocks WHERE user_id = (?)", session["user_id"])
        return render_template("sell.html", symbols=symbols)

