#!/usr/bin/python2.7
import MySQLdb
import cgitb
cgitb.enable()


# connect db
db = MySQLdb.connect(host='birowaks.mysql.pythonanywhere-services.com', user='birowaks', passwd='Baraka4me2!', db='birowaks$buythebeat')
cursor = db.cursor()

print "Content-Type: text/plain;charset=utf-8"
print

def itemlist(buyer):
    db.ping(True)
    try:
        # print buyer
        # return buyer
        cursor.execute("select * from cart where buyer='"+str(buyer)+"'")
        beats=cursor.fetchall()
        x = []
        for b in beats:
            x.append( '{ "name": "'+ b[2]+'", "sku": "'+ str(b[1])+'", "price": "'+ str(b[5]) +'", "currency": "USD", "quantity": "1"}')
        return x
    except Exception as e:
        return str(e)

# itemlist('142301443810')
