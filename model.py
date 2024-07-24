from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta, timezone
from flask_login import UserMixin

db = SQLAlchemy()

current_timeutc = datetime.now(timezone.utc)
ist_offset = timedelta(hours=5, minutes=30)
current_time = current_timeutc + ist_offset


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String)
    email = db.Column(db.String(255), unique=True)
    password = db.Column(db.String(255))
    active = db.Column(db.Boolean)
    role = db.Column(db.String)
    itemrequest = db.relationship(
        'ItemRequest', backref='itemreq_ref', lazy=True)
    cart = db.relationship(
        'Cart', backref='cart_ref', lazy=True)
    order = db.relationship(
        'Order', backref='order_ref1', lazy=True)

    def __repr__(self):
        return '<User %r>' % self.id

    def get_id(self):
        return str(self.id)


class Category(db.Model):
    catid = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(200), nullable=False)
    items = db.relationship('Item', backref='category_ref', lazy=True)
    description = db.Column(db.Text)

    def __repr__(self):
        return '<Category %r>' % self.id


class Item(db.Model):
    itemid = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(200), nullable=False)
    partno = db.Column(db.String(10), default='-')
    description = db.Column(db.Text)
    date_stocked = db.Column(db.DateTime, default=current_time)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    price = db.Column(db.Numeric(precision=10, scale=2))
    location = db.Column(db.Text)
    deleted = db.Column(db.Boolean, default=False)
    category = db.Column(db.Integer, db.ForeignKey(
        'category.catid'), nullable=False)
    itemrequest = db.relationship('ItemRequest', backref='item_ref', lazy=True)

    def __repr__(self):
        return '<Item ID:%r Name:%r>' % (self.itemid, self.name)


class ItemRequest(db.Model):
    itemid = db.Column(db.Integer, db.ForeignKey(
        'item.itemid'), primary_key=True)
    userid = db.Column(db.Integer, db.ForeignKey(
        'user.id'), primary_key=True)
    qty = db.Column(db.Integer, default=0)
    date = db.Column(db.DateTime, default=current_time)
    fulfilled = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return '<Item Request:%r User:%r>' % (self.itemid, self.userid)


class Cart(db.Model):
    cartid = db.Column(db.Integer, primary_key=True, autoincrement=True)
    userid = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    type = db.Column(db.String(10), default='current')
    last_updated = db.Column(db.DateTime, default=current_time)
    totalqty = db.Column(db.Integer)
    totalprice = db.Column(db.Integer)
    order = db.relationship(
        'Order', backref='order_ref2', lazy=True)

    def __repr__(self):
        return '<Cart : %r, User ID : %r>' % (self.cartid, self.userid)


class CartItem(db.Model):
    cartid = db.Column(db.Integer, db.ForeignKey(
        'cart.cartid'), primary_key=True)
    itemid = db.Column(db.Integer, primary_key=True)
    qty = db.Column(db.Integer, default=1)
    purchased = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return '<CartItem : Cart ID : %r Item ID : %r>' % (self.cartid, self.itemid)


class Order(db.Model):
    userid = db.Column(db.Integer, db.ForeignKey('user.id'))
    orderid = db.Column(db.Integer, primary_key=True, autoincrement=True)
    cartid = db.Column(db.Integer, db.ForeignKey('cart.cartid'))
    totalqty = db.Column(db.Integer)
    totalprice = db.Column(db.Integer)
    date = db.Column(db.DateTime, default=current_time)
    customerid = db.Column(db.Integer, db.ForeignKey('customer.customerid'))

    def __repr__(self):
        return '<Order ID : %r Cart ID : %r>' % (self.orderid, self.cartid)


class Customer(db.Model):
    customerid = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String)
    address = db.Column(db.Text)
    gstno = db.Column(db.String(20))

    def __repr__(self):
        return '<Customer ID : %r>' % (self.customerid)


class Notes(db.Model):
    noteid = db.Column(db.Integer, primary_key=True, autoincrement=True)
    userid = db.Column(db.Integer, db.ForeignKey('user.id'))
    itemid = db.Column(db.Integer, db.ForeignKey('item.itemid'))
    notetitle = db.Column(db.Text)
    notetext = db.Column(db.Text)
    date = db.Column(db.DateTime, default=current_time)

    def __repr__(self):
        return '<Note ID : %r User ID : %r Item ID : %r>' % (self.customerid, self.userid, self.itemid)
