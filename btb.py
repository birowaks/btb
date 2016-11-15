from flask import Flask, render_template, request, session, redirect, url_for
from passlib.hash import sha256_crypt
from werkzeug.utils import secure_filename
from pydub import AudioSegment
import random
import MySQLdb
import smtplib
from email.mime.text import MIMEText
from email.MIMEMultipart import MIMEMultipart

# paypal integration
from paypalrestsdk import WebProfile, Payment, configure
import logging
import string

import requests
import urlparse

import sys
import items



print "Content-Type: text/plain;charset=utf-8"
print


logging.basicConfig(level=logging.INFO)

app =Flask(__name__)


db = MySQLdb.connect(host='birowaks.mysql.pythonanywhere-services.com', user='birowaks', passwd='Baraka4me2!', db='birowaks$buythebeat')
cursor = db.cursor()

base_url="http://www.buythebeat.com"
db.ping(True)




@app.route("/test/")
def itemlist():
    db.ping(True)
    try:
        thelist = items.itemlist(142301443810)
        y = ', '.join([str(i) for i in thelist])
        return y

        # render_template("test.html", x=thelist[0])
    except Exception as e:
        return str(e)


@app.route("/")
@app.route("/home/")
@app.route("/buybeat/")
def index():
    db.ping(True)
    cursor.execute("select * from beats ORDER BY RAND() LIMIT 6")
    top = cursor.fetchall()
    cart = []
    total = 0

    if 'userref' in session:
        cursor.execute("select * from cart where buyer='"+session['userref']+"'")
        cart = cursor.fetchall()

        cursor.execute("SELECT SUM(price) FROM cart where buyer='"+session['userref']+"'")
        total = cursor.fetchone()[0]

    def profileimg(email):
        db.ping(True)
        cursor.execute("select * from users where email='"+email+"'")
        user = cursor.fetchall()
        for img in user:
            return img[7]
    def producer(email):
        cursor.execute("select * from users where email='"+email+"'")
        user = cursor.fetchall()
        for img in user:
            return img[3]
    def producerref(email):
        cursor.execute("select * from users where email='"+email+"'")
        user = cursor.fetchall()
        for img in user:
            return img[1]
    return render_template('buybeat.html', data=top, img=profileimg, producer=producer, producerref=producerref, cart=cart, total=total, base_url=base_url)


@app.route("/sellbeat/")
def sellbeat():
    db.ping(True)
    if 'email' in session:
        return redirect(url_for('dashboard'))
    else:
        return render_template('sellbeat.html', base=base_url)

@app.route("/search/", methods=['POST', 'GET'])
def search():
    db.ping(True)

    try:
        param = request.form['param']
        cursor.execute("SELECT * FROM beats WHERE beatname LIKE %s LIMIT 30", ("%" + param + "%",))
        result = cursor.fetchall()
        return render_template('search.html', result=result)


    except Exception as e:
        return str(e)


@app.route("/login/", methods=['POST', 'GET'])
def login():
    db.ping(True)
    error = None
    if request.method == 'POST':
        uemail = request.form['email']

        try:
            cursor.execute("SELECT * from users where email='"+uemail+"'")
            results = cursor.fetchall()

            num = cursor.rowcount
            if num<1 :
                error = "The email you are using in not found within our network. Please check its spelling or signup if you have not"
                return render_template('login.html', error=error)

            for row in results:
                passd = row[4]
                uid= row[1]
                profile=row[7]
                cover=row[8]
                # return "check"
                if sha256_crypt.verify(request.form['password'], passd) == True:
                    session['email'] = request.form['email']
                    session['userref'] = uid
                    session['cover'] = cover
                    session['profile'] = profile

                    return redirect(url_for('dashboard'))
                else:
                    error = "Wrong password for "+ uemail
                    return render_template('login.html', error=error)
        except:
            error = "kuna sida na code yako: "
            return render_template('login.html', error=error)

    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    db.ping(True)
    session.pop('email', None)
    session.pop('userref', None)
    return redirect(url_for('index'))

@app.route("/signup/", methods=['POST', 'GET'])
def signup():
    db.ping(True)
    error = None

    if request.method == 'POST':
        userref = random.randint(9999999,999999999999)
        userref = str(userref)
        useremail = request.form['email']
        username = request.form['username']
        acctype = request.form['type']
        password = sha256_crypt.encrypt(request.form['password'])
        cursor.execute("select * from users where email='"+useremail+"'")
        num = cursor.rowcount

        if num >= 1:
            #return "Hapa tu2"
            error = "Sorry the email address you are trying to use is already registered with us."
            return render_template('signup.html', error=error)
        else:
            cursor.execute("insert into users set email='"+useremail+"', username='"+username+"', password='"+password+"', acctype='"+acctype+"', user_ref='"+userref+"', status='1'")
            db.commit()

            return redirect(url_for('login'))

    return render_template('signup.html', error=error)


@app.route("/beatshop/<beatmaker>")
def beatshop(beatmaker):

    cursor.execute("select * from users where username='"+beatmaker+"'")
    user = cursor.fetchone()
    cart = []
    total = 0

    if 'userref' in session:
        cursor.execute("select * from cart where buyer='"+session['userref']+"'")
        cart = cursor.fetchall()

        cursor.execute("SELECT SUM(price) FROM cart where buyer='"+session['userref']+"'")
        total = cursor.fetchone()[0]

    email = user[2]

    cursor.execute("select * from beats where email='"+email+"'")
    beats = cursor.fetchall()

    return render_template("beatstore.html", beats=beats, beatmaker=user, base=base_url, cart=cart, total=total)


#################################################################################################################

#ACCOUNT MANAGEMENT

@app.route("/dashboard/")
def dashboard():
    db.ping(True)
    cart = []
    total = 0

    if 'userref' in session:
        cursor.execute("select * from cart where buyer='"+session['userref']+"'")
        cart = cursor.fetchall()

        cursor.execute("SELECT SUM(price) FROM cart where buyer='"+session['userref']+"'")
        total = cursor.fetchone()[0]

    try:
        cursor.execute("select * from users where user_ref='"+session['userref']+"'")
        settings = cursor.fetchall()
        for row in settings:
            return render_template('dashboard.html', data=row, cart=cart, total=total)
    except:
        cursor.execute("select * from users where user_ref='"+session['userref']+"'")
        settings = cursor.fetchall()
        for row in settings:
            return render_template('dashboard.html', num=0, data=row, cart=cart, total=total)

@app.route("/forgotpass/", methods=['GET', 'POST'])
def forgotpass():
    db.ping(True)

    if request.method == 'POST':
        email=request.form['email']

        cursor.execute("select * from users where email='"+email+"'")
        users = cursor.fetchall()

        for u in users:
            changelink = base_url+"/changepass/"+u[1]
            #return changelink

            fromaddr = "mrcharlesngeno@gmail.com"
            toaddr = email
            msg = MIMEMultipart()
            msg['From'] = "mrcharlesngeno@gmail.com"
            msg['To'] = toaddr
            msg['Subject'] = "Password Change"

            body = "We have recieved a password change request from your buythebeat.com account. If this was not requested by you; please ignore this email. If you sent this email then click the following link: "+changelink
            #return changelink
            msg.attach(MIMEText(body, 'plain'))

            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(fromaddr, "jesusislord4ever")
            text = msg.as_string()
            server.sendmail(fromaddr, toaddr, text)
            server.quit()

            error = "Check your email to find password change link."
            return redirect(url_for('login'))

    return render_template('forgotpass.html')

@app.route('/changepass/<id>', methods=['GET', 'POST'])
def changepass(id):
    if request.method == 'POST':

        passwd = sha256_crypt.encrypt(request.form['password'])
        cursor.execute("UPDATE users SET password='"+passwd+"' WHERE user_ref='"+id+"'")
        db.commit()

        error = "Successful password change. Try logging in"

        return redirect(url_for('login'))

    return render_template('changepass.html')

@app.route('/newbeat/', methods=['GET', 'POST'])
def upload_file():
    db.ping(True)
    error = None
    if request.method == 'POST':
        #uploading and renaming the beat file.
        m = request.files['mp3']
        m.save('/home/birowaks/mysite/buythebeat/static/uploads/beats/'+session['email']+'-'+secure_filename(m.filename))

        #beat data
        beat = session['email']+'-'+secure_filename(m.filename)
        genre = request.form['genre']
        beatname = request.form['beatname']
        price = request.form['price']

        #create sample with audio tag
        beatfile = "/home/birowaks/mysite/buythebeat/static/uploads/beats/"+beat
        dropfile = "/home/birowaks/mysite/buythebeat/static/tag.mp3"



        sound2 = AudioSegment.from_file(dropfile)
        #return "hapa"
        sound = AudioSegment.from_file(beatfile)


        combined = sound.overlay(sound2, position=5000, loop=True)
        combined.export("/home/birowaks/mysite/buythebeat/static/samples/"+beatname+".mp3", format="mp3")

        #database info
        samplelink="/static/samples/"+beatname+".mp3"
        beatlink = "/static/uploads/beats/"+beat
        uemail = session['email']

        #save to database
        try:
            cursor.execute("INSERT INTO beats SET email='"+uemail+"', beatname='"+beatname+"', genre='"+genre+"', file='"+beatlink+"', sample='"+samplelink+"', price='"+price+"', status='1'")
            db.commit()
            #info = beatname+" has been successfully uploaded"
            return redirect(url_for('myshop'))
        except:
            error = "Error inserting your beat to the database."
            return render_template('newbeat.html', error=error)
    cursor.execute("select * from users where user_ref='"+session['userref']+"'")
    settings = cursor.fetchall()
    for row in settings:
        return render_template('newbeat.html', data=row)


@app.route('/editbeat/<beatid>', methods=['GET', 'POST'])
def editbeat(beatid):
    db.ping(True)
    if request.method == 'POST':
        genre = request.form['genre']
        beatname = request.form['beatname']
        price = request.form['price']

        cursor.execute("update beats set beatname='"+beatname+"', genre='"+genre+"', price='"+price+"' where beats_id='"+beatid+"'")
        db.commit()

        return redirect(url_for('myshop'))


    cursor.execute("select * from beats where beats_id='"+beatid+"'")
    #return "hapa"
    beats = cursor.fetchall()

    for beat in beats:
        cursor.execute("select * from users where user_ref='"+session['userref']+"'")
        settings = cursor.fetchall()
        for row in settings:
            return render_template('editbeat.html', data=row, beat=beat)


@app.route("/deletebeat/<beatid>")
def deletebeat(beatid):
    db.ping(True)
    cursor.execute("delete from beats where beats_id='"+beatid+"'")
    db.commit()
    return redirect(url_for('myshop'))



@app.route("/myshop/")
def myshop():
    db.ping(True)
    uemail=session['email']
    cursor.execute("select * from beats where email='"+uemail+"'")
    results = cursor.fetchall()
    cursor.execute("select * from users where user_ref='"+session['userref']+"'")
    settings = cursor.fetchall()
    for row in settings:
        return render_template('myshop.html', beat=results, data=row)


@app.route("/sales/")
def sales():
    db.ping(True)
    cursor.execute("select * from users where user_ref='"+session['userref']+"'")
    settings = cursor.fetchall()
    for row in settings:
        return render_template('sales.html', data=row)


@app.route("/reports/")
def reports():
    db.ping(True)
    cursor.execute("select * from users where user_ref='"+session['userref']+"'")
    settings = cursor.fetchall()
    for row in settings:
        return render_template('reports.html', data=row)


@app.route("/password/", methods=['GET', 'POST'])
def password():
    db.ping(True)
    error = None
    if request.method == 'POST':
        oldpassword = request.form['oldpassword']
        password = sha256_crypt.encrypt(request.form['newpassword'])

        try:
            cursor.execute("SELECT * from users where user_ref='"+session['userref']+"'")
            results = cursor.fetchall()
            for row in results:
                passd = row[4]
                if sha256_crypt.verify(oldpassword, passd) == True:
                    cursor.execute("UPDATE users SET password='"+password+"' where user_ref='"+session['userref']+"'")
                    db.commit()
                    cursor.execute("select * from users where user_ref='"+session['userref']+"'")
                    error = "Password change successful"
                    settings = cursor.fetchall()
                    for row in settings:
                        return render_template('password.html', data=row, error=error)
                else:
                    cursor.execute("select * from users where user_ref='"+session['userref']+"'")
                    error = "The old password you have entered is incorrect"
                    settings = cursor.fetchall()
                    for row in settings:

                        return render_template('password.html', data=row, error=error)
        except:
            return "angalia hapa"

    cursor.execute("select * from users where user_ref='"+session['userref']+"'")
    settings = cursor.fetchall()
    for row in settings:
        return render_template('password.html', data=row, error=error)

@app.route("/cover/", methods=['GET', 'POST'])
def cover():
    db.ping(True)
    if request.method == 'POST':
        #return "Tuko testing"
        c = request.files['cover']

        c.save('/home/birowaks/mysite/buythebeat/static/covers/'+session['email']+'-'+secure_filename(c.filename))
        cover = '/static/covers/'+session['email']+'-'+secure_filename(c.filename)

        cursor.execute("UPDATE users SET cover='"+cover+"' where user_ref='"+session['userref']+"'")
        db.commit()
        #return "tumefika"
        return redirect(url_for('settings'))

    cursor.execute("select * from users where user_ref='"+session['userref']+"'")
    settings = cursor.fetchall()

    for row in settings:
       return render_template('cover.html', data=row)

@app.route("/profile/", methods=['GET', 'POST'])
def profile():
    db.ping(True)
    if request.method == 'POST':

        p = request.files['photo']

        p.save('/home/birowaks/mysite/buythebeat/static/profiles/'+session['email']+'-'+secure_filename(p.filename))
        photo = '/static/profiles/'+session['email']+'-'+secure_filename(p.filename)

        cursor.execute("UPDATE users SET profile='"+photo+"' where user_ref='"+session['userref']+"'")
        db.commit()
        #return "tumefika"
        return redirect(url_for('settings'))

    cursor.execute("select * from users where user_ref='"+session['userref']+"'")
    settings = cursor.fetchall()

    for row in settings:
       return render_template('profile.html', data=row)

@app.route("/settings/", methods=['GET', 'POST'])
def settings():
    db.ping(True)
    if request.method == 'POST':

        userref = session['userref']
        temail = request.form['email']
        acctype = request.form['acctype']
        tusername = request.form['username']
        paypal = request.form['paypal']

        cursor.execute("UPDATE users SET email='"+temail+"', username='"+tusername+"', acctype='"+acctype+"', paypal='"+paypal+"', status='1' where user_ref='"+userref+"'")
        db.commit()

        return redirect(url_for('myshop'))

    #return session['userref']
    cursor.execute("select * from users where user_ref='"+session['userref']+"'")
    settings = cursor.fetchall()

    for row in settings:
       return render_template('settings.html', data=row)


###################################################################################################################

#SHOPPING CATALOGUE AND SALES

#addtocart
@app.route("/addtocart/<beat>")
def addtocart(beat):
    db.ping(True)
    #return beat
    #check if user is logged in
    if 'userref' in session:
        #Get info from url
        beat = beat.split('&')
        #return str(beat[1])
        cursor.execute("select * from beats where beats_id='"+beat[0]+"'")
        beats = cursor.fetchall()

        for b in beats:
            beatname = b[2]
            price = b[7]

            cursor.execute("insert into cart set beatid='"+beat[0]+"', beatname='"+beatname+"', seller='"+beat[1]+"', buyer='"+session['userref']+"', price='"+price+"' ")

            db.commit()

            # return redirect(url_for('index'))
    else:
        return redirect(url_for('login'))


@app.route("/deletefromcart/<cartid>")
def deletefromcart(cartid):
    db.ping(True)
    cursor.execute("delete from cart where cart_id='"+cartid+"'")
    db.commit()
    # return redirect(url_for('cart'))



@app.route("/cart/", methods=['GET', 'POST'])
def cart():
    db.ping(True)
    cursor.execute("select * from cart where buyer='"+session['userref']+"'")
    cart = cursor.fetchall()
    cursor.execute("SELECT SUM(price) FROM cart where buyer='"+session['userref']+"'")
    total = cursor.fetchone()[0]
    # num = cursor.rowcount

    thelist = items.itemlist(session['userref'])
    y = ', '.join([str(i) for i in thelist])

    try:
        if request.method == 'POST':

            configure({
              "mode": "sandbox", # sandbox or live
              "client_id": "ASD9BogtisKC0OKZzppc139ku4mHGAUsqN23scuS5RA9L83a4wT3pzbIET2BCPlq8TSb-0tIrBAsYJk7",
              "client_secret": "EERBGe7FTcY8pUla_9kZPTdu5L5GexpwomJTTs3Lg_dogfnvMLmU0zCSxTGnBeUE7W00Dd-bIq4XB-7-" })

            wpn = ''.join(random.choice(string.ascii_uppercase) for i in range(12))
            web_profile = WebProfile({
                    "name": wpn,
                    "presentation": {
                        "brand_name": "buythebeat.com",
                        "logo_image": "http://www.buythebeat.com/static/brand.png",
                        "locale_code": "US"
                        },
                    "input_fields": {
                        "allow_note": True,
                        "no_shipping": 0,
                        "address_override": 1
                        },
                    "flow_config": {
                        "landing_page_type": "Login"
                        }
                })
            web_profile.create() # Will return True or False
            # return web_profile.id

            payment = Payment({
              "intent": "sale",
              "experience_profile_id": web_profile.id,
              "payer": {
                "payment_method": "paypal",
              },
              "redirect_urls": {
                    "return_url": "http://www.buythebeat.com/success/",
                    "cancel_url": "http://www.buythebeat.com/cart/"},


              "transactions": [{
                "item_list": {
                    "items": [
                            y
                        ]
                    },
                "amount": {
                  "total": total,
                  "currency": "USD" },
                "description": "This is the payment transaction description." }]})

            if payment.create():
                try:
                    for link in payment.links:
                        if link.method == "REDIRECT":
                            redirect_url = str(link.href)
                            return redirect(redirect_url)
                except Exception as e:
                    return str(e)

            else:
              return "Payment Error: "+str(payment.error)
    except Exception as e:
        return str(e)


    return render_template('cart.html', cart=cart, total=total)



@app.route("/success/")
def success():
    db.ping(True)
    try:
        paymentId = request.args.get("paymentId")
        token = request.args.get("token")
        PayerID = str(request.args.get("PayerID"))
        configure({
              "mode": "sandbox", # sandbox or live
              "client_id": "ASD9BogtisKC0OKZzppc139ku4mHGAUsqN23scuS5RA9L83a4wT3pzbIET2BCPlq8TSb-0tIrBAsYJk7",
              "client_secret": "EERBGe7FTcY8pUla_9kZPTdu5L5GexpwomJTTs3Lg_dogfnvMLmU0zCSxTGnBeUE7W00Dd-bIq4XB-7-" })

        payment = Payment.find(paymentId)
        if payment.execute({"payer_id": PayerID}):
            msg = "Transaction Id: "+ paymentId
            return render_template('successful_transaction.html', msg=msg)
        else:
            return str(payment.error)
            # return paymentId
    except Exception as e:
        return str(e)

@app.route("/failure/")
def failure():
    db.ping(True)
    try:
        return render_template('failed_transaction.html')
    except Exception as e:
        return str(e)



app.secret_key = 'A0Zr98j/3yX R~XHH!jmN]LWX/,?RT'

# if __name__ == "__main__":
#     app.debug = True
#     app.run(host='127.0.0.1')
