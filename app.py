# ================================== MODLUES & PACKAGES ==================================

from flask import Flask, render_template, url_for, request as flask_request, flash
from flask import redirect
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone
from model import db, User as user, Category as category_model
from model import Item as item_model, ItemRequest as item_request
from model import Cart as cart_model, CartItem as cart_item, Order as order_model
from model import Notes as note_model, Customer as customer_model
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
import csv
import os
import numpy as np
from flask_restful import Resource, Api
from matplotlib import pyplot as plt
import matplotlib
matplotlib.use('Agg')


# ================================== INTIALIZATION ==================================
lm = LoginManager()
lm.login_view = 'login'

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SECRET_KEY'] = 'inventory'

lm.init_app(app)

db.init_app(app)
app.app_context().push()
api = Api(app)

with app.app_context():
    db.create_all()


@lm.user_loader
def load_user(id):
    return user.query.get(int(id))


# ================================== ROUTES ==================================
@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template('index.html')


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if flask_request.method == 'GET':
        return render_template('signup.html')
    elif flask_request.method == 'POST':
        name = flask_request.form.get('name')
        email = flask_request.form.get('email')
        pw = flask_request.form.get('password')
        u = user.query.filter_by(email=email).first()
        if not u:
            u_ser = user(username=name,
                         email=email, password=pw, role='user')
            db.session.add(u_ser)
            db.session.commit()
            flash(f'Now please log in !',
                  category='success')
            return redirect(url_for('login'))
        else:
            flash(f'You are already signed up. please login !',
                  category='success')
            return redirect(url_for('login'))
    return render_template('signup.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if flask_request.method == 'GET':
        return render_template('login.html')
    elif flask_request.method == 'POST':
        email = flask_request.form.get('email')
        pw = flask_request.form.get('password')
        u = user.query.filter_by(email=email).first()
        if u:
            if u.password == pw:
                login_user(u)
                flash(f'Welcome {current_user.username}!',
                      category='success')
                return redirect(url_for('home'))
            else:
                flash(f'Wrong password !',
                      category='error')
                return redirect(url_for('login'))
        else:
            flash(f'Please sign up first !',
                  category='warning')
            return redirect(url_for('signup'))
    return render_template('login.html')


@app.route('/home', methods=['GET', 'POST'])
@login_required
def home():
    if current_user.is_authenticated == True:
        if flask_request.method == 'GET':
            items = item_model.query.all()
            categories = category_model.query.all()
            if current_user.role == 'user':
                return render_template('userhome.html',
                                       items=items, cats=categories)
            elif current_user.role == 'admin':
                return render_template('adminhome.html')
        elif flask_request.method == 'POST':
            return redirect(url_for('home'))
    else:
        return redirect(url_for('login'))


@app.route('/items', methods=['GET'])
@login_required
def show_all_items():
    items = item_model.query.filter_by(deleted=False).all()
    cats = category_model.query.all()
    return render_template('showallitems.html',
                           items=items, cats=cats, currentuser=current_user)


@app.route('/item/<int:itemid>')
@login_required
def showitem(itemid):
    item = item_model.query.filter_by(itemid=itemid).first()
    cats = category_model.query.all()
    if current_user.role == 'user':
        notes = note_model.query.filter_by(userid=current_user.id).all()
    elif current_user.role == 'admin':
        notes = note_model.query.filter_by(itemid=itemid).all()
    return render_template('item.html',
                           currentuser=current_user, item=item, cats=cats, notes=notes)


@app.route('/requests', methods=['GET'])
@login_required
def show_all_requests():
    users = user.query.all()
    irs = item_request.query.all()
    items = item_model.query.all()
    cats = category_model.query.all()
    return render_template('showallrequests.html',
                           users=users, items=items, cats=cats, irs=irs)


@app.route('/add_new_product', methods=['GET', 'POST'])
@login_required
def add_new_product():
    categories = category_model.query.all()
    if flask_request.method == 'POST':
        name = flask_request.form.get('name')
        partno = flask_request.form.get('partno')
        qty = flask_request.form.get('qty')
        price = flask_request.form.get('price')
        category = flask_request.form.get('category')
        if not category:
            category = 1
        location = flask_request.form.get('location')
        already = item_model.query.filter_by(name=name, partno=partno).first()
        if already:
            return render_template('addnewproduct.html', categories=categories)
        else:
            current_time = datetime.now(timezone.utc)
            it = item_model(name=name, partno=partno, quantity=qty,
                            category=category, date_stocked=current_time,
                            location=location, price=price)
            db.session.add(it)
            db.session.commit()
            it = item_model.query.filter_by(itemid=it.itemid).first()
            pic_uploaded = flask_request.files.get('photo')
            if pic_uploaded:
                item_id = it.itemid
                pic_name = f"{item_id}.jpg"
                save_path = os.path.join('static', 'media', pic_name)
                try:
                    pic_uploaded.save(save_path)
                except Exception as e:
                    print(f'Error Saving File !!! {e}')
            flash(f'You have added {it.name} item !', category='success')
            return redirect(url_for('home'))

    return render_template('addnewproduct.html', categories=categories)


@app.route('/add_new_category', methods=['GET', 'POST'])
@login_required
def add_new_category():
    if flask_request.method == 'POST':
        category = flask_request.form.get('category')
        desc = flask_request.form.get('description')
        already = category_model.query.filter_by(name=category).first()
        if already:
            return redirect(url_for('home'))
        else:
            c = category_model(name=category, description=desc)
            db.session.add(c)
            db.session.commit()
            flash(f'You have added {c.name} category !', category='success')
            return redirect(url_for('home'))

    return render_template('addnewcategory.html')


@app.route('/<int:id>/update/item', methods=['GET', 'POST'])
@login_required
def update(id):
    it = item_model.query.filter_by(itemid=id).first()
    categories = category_model.query.all()
    if flask_request.method == 'GET':
        return render_template('updateitem.html', item=it, categories=categories)
    elif flask_request.method == 'POST':
        name = flask_request.form.get('name')
        partno = flask_request.form.get('partno')
        description = flask_request.form.get('description')
        qty = flask_request.form.get('qty')
        price = flask_request.form.get('price')
        category = flask_request.form.get('category')
        location = flask_request.form.get('location')
        current_time = datetime.now(timezone.utc)
        it = item_model.query.filter_by(itemid=id)
        it.update({item_model.name: name, item_model.partno: partno,
                   item_model.quantity: qty, item_model.category: category,
                   item_model.date_stocked: current_time, item_model.location: location,
                   item_model.price: price, item_model.description: description})
        db.session.commit()
        flash(f'You have updated {it[0].name} item !',
              category='success')
        return redirect(url_for('home'))
    return render_template('updateitem.html', item=it, categories=categories)


@app.route('/<int:catid>/update/category', methods=['GET', 'POST'])
@login_required
def updatecategory(catid):
    c = category_model.query.filter_by(catid=catid).first()
    if flask_request.method == 'GET':
        return render_template('updatecategory.html', cat=c)
    elif flask_request.method == 'POST':
        category = flask_request.form.get('category')
        description = flask_request.form.get('description')
        c = category_model.query.filter_by(catid=catid)
        c.update({category_model.name: category,
                 category_model.description: description})
        db.session.commit()
        flash(f'You have updated {c[0].name} !',
              category='success')
        return redirect(url_for('home'))
    return render_template('updatecategory.html', cat=c)


@app.route('/categories', methods=['GET'])
@login_required
def show_all_categories():
    cats = category_model.query.all()
    return render_template('showallcategories.html', cats=cats, currentuser=current_user)


@app.route('/category/<name>', methods=['GET'])
@login_required
def opencategory(name):
    currentcat = category_model.query.filter_by(name=name).first()
    items = item_model.query.filter_by(
        category=currentcat.catid).all()
    if current_user.role == 'admin':
        return render_template('category.html', cat=currentcat, items=items)
    else:
        return render_template('usercategory.html', cat=currentcat, items=items)


@app.route('/<int:userid>/request/<int:itemid>/accept')
@login_required
def acceptrequest(userid, itemid):
    ir = item_request.query.filter_by(userid=userid, itemid=itemid).first()
    ir.fulfilled = True
    it = item_model.query.filter_by(itemid=itemid).first()
    q = it.quantity
    q += int(ir.qty)
    it.quantity = q
    db.session.commit()
    flash(f'You have accepted request of {ir.userid} of {it.name} item !',
          category='success')
    return redirect(url_for('show_all_requests'))


@app.route('/<int:userid>/request/<int:itemid>/reject')
@login_required
def rejectrequest(userid, itemid):
    ir = item_request.query.filter_by(userid=userid, itemid=itemid).first()
    us, it = ir.userid, ir.itemid
    db.session.delete(ir)
    db.session.commit()
    flash(f'You have rejected request of {us} of {it} item !',
          category='warning')
    return redirect(url_for('show_all_requests'))


@app.route('/<int:id>/stock', methods=['GET', 'POST'])
@login_required
def stock(id):
    it = item_model.query.filter_by(itemid=id).first()
    categories = category_model.query.filter_by(catid=it.category)
    if flask_request.method == 'POST':
        stqty = flask_request.form.get('stqty')
        current_time = datetime.now(timezone.utc)
        it = item_model.query.filter_by(itemid=id)
        new_qty = int(it[0].quantity)+int(stqty)
        it.update({item_model.quantity: new_qty,
                  item_model.date_stocked: current_time})
        db.session.commit()
        flash(f'You have added {stqty} Qty of{it[0].name} item !',
              category='success')
        return redirect(url_for('home'))
    return render_template('stockitem.html',
                           item=it, categories=categories)


@app.route('/<int:id>/sell', methods=['GET', 'POST'])
@login_required
def sell(id):
    it = item_model.query.filter_by(itemid=id).first()
    categories = category_model.query.filter_by(catid=it.category)
    if flask_request.method == 'POST':
        stqty = flask_request.form.get('sellqty')
        it = item_model.query.filter_by(itemid=id)
        new_qty = int(it[0].quantity)-int(stqty)
        it.update({item_model.quantity: new_qty})
        db.session.commit()
        name = it.name
        flash(f'You have sold {stqty} Qty of{name} item !',
              category='success')
        return redirect(url_for('home'))
    return render_template('sellitem.html',
                           item=it, categories=categories)


@app.route('/<int:id>/delete')
@login_required
def delete(id):
    it = item_model.query.get_or_404(id)
    name = it.name
    db.session.query(cart_item).filter_by(
        itemid=it.itemid, purchased=False).delete()
    db.session.query(item_request).filter_by(itemid=it.itemid).delete()
    db.session.query(note_model).filter_by(itemid=it.itemid).delete()
    it.deleted = True
    db.session.commit()
    flash(f'You have deleted {name} item !', category='error')
    return redirect(url_for('home'))


@app.route('/items/deleted', methods=['GET'])
@login_required
def show_deleted_items():
    if current_user.role == 'admin':
        items = item_model.query.filter_by(deleted=True)
        cats = category_model.query.all()
        return render_template('deleteditems.html',
                               items=items, cats=cats, currentuser=current_user)
    else:
        flash(f'You are unauthorized !', category='error')
        return redirect(url_for('home'))


@app.route('/restore/<int:itemid>')
@login_required
def restore(itemid):
    it = item_model.query.get_or_404(itemid)
    it.deleted = False
    db.session.commit()
    flash(f'You have restored {it.name} item !', category='primary')
    return redirect(url_for('home'))


@app.route('/<int:id>/request', methods=['GET', 'POST'])
@login_required
def request(id):
    if flask_request.method == 'POST':
        ir = item_request.query.filter_by(
            userid=current_user.id, itemid=id).first()
        if ir:
            q = ir.qty
            if q == None or q == '':
                q = 0
            qty = flask_request.form.get('qty')
            if qty == None or qty == '':
                qty = 0
            q += int(qty)
            ir.qty = q
            db.session.commit()
            return redirect(url_for('home'))
        else:
            qty = flask_request.form.get('qty')
            if qty == None or qty == '':
                qty = 0
            itr = item_request(userid=current_user.id, itemid=id, qty=qty)
            db.session.add(itr)
            db.session.commit()
            flash('You have requested the item ! Please wait for response !',
                  category='success')
            return redirect(url_for('home'))
    return redirect(url_for('home'))


@app.route('/cart/add/<int:item_id>', methods=['GET', 'POST'])
@login_required
def add_item_cart(item_id):
    usercart = cart_model.query.filter_by(
        userid=current_user.id, type='current').first()
    if not usercart:
        newcart = cart_model(userid=current_user.id, type='current')
        db.session.add(newcart)
        db.session.commit()
    usercart = cart_model.query.filter_by(
        userid=current_user.id, type='current').first()
    if flask_request.method == 'GET':
        return redirect(url_for('cart'))
    elif flask_request.method == 'POST':
        already = cart_item.query.filter_by(
            cartid=usercart.cartid, itemid=item_id).first()
        if already:
            flash("You already have the item in your cart !", category='warning')
        else:
            additem = cart_item(cartid=usercart.cartid, itemid=item_id)
            db.session.add(additem)
            db.session.commit()
            flash("You added the item in your cart !", category='success')
        return redirect(url_for('cart'))
    return render_template


@app.route('/cart', methods=['GET', 'POST'])
@login_required
def cart():
    usercart = cart_model.query.filter_by(
        userid=current_user.id, type='current').first()
    if not usercart:
        newcart = cart_model(userid=current_user.id, type='current')
        db.session.add(newcart)
        db.session.commit()
    usercart = cart_model.query.filter_by(
        userid=current_user.id, type='current').first()
    cartitems = cart_item.query.filter_by(cartid=usercart.cartid).all()
    items = item_model.query.all()
    if flask_request.method == 'GET':
        return render_template('cart.html',
                               usercart=usercart, cartitems=cartitems, items=items)
    elif flask_request.method == 'POST':
        incqty = flask_request.form.get('qty')

        return render_template('cart.html',
                               usercart=usercart, cartitems=cartitems, items=items)
    return render_template('cart.html',
                           usercart=usercart, cartitems=cartitems, items=items)


@app.route('/cart/update/<int:itemid>', methods=['GET', 'POST'])
@login_required
def updatecart(itemid):
    currentcart = cart_model.query.filter_by(
        userid=current_user.id, type='current').first()
    cartitem = cart_item.query.filter_by(
        cartid=currentcart.cartid, itemid=itemid).first()
    if flask_request.method == 'POST':
        incqty = flask_request.form.get('incqty')
        cartitem.qty = incqty
        db.session.commit()
        return redirect(url_for('cart'))
    return redirect(url_for('cart'))


@app.route('/cart/delete/<int:itemid>')
@login_required
def deletecartitem(itemid):
    currentcart = cart_model.query.filter_by(
        userid=current_user.id, type='current').first()
    cartitem = cart_item.query.filter_by(
        cartid=currentcart.cartid, itemid=itemid).first()
    db.session.delete(cartitem)
    db.session.commit()
    return redirect(url_for('cart'))


@app.route('/checkout/<int:cartid>', methods=['GET', 'POST'])
@login_required
def checkout(cartid):
    cartitems = cart_item.query.filter_by(cartid=cartid).all()
    totalqty, totalprice = 0, 0.0
    for i in cartitems:
        item = item_model.query.filter_by(itemid=i.itemid).first()
        totalqty += i.qty
        totalprice += float(i.qty*item.price)
    items = item_model.query.all()
    for ci in cartitems:
        item = item_model.query.filter_by(itemid=ci.itemid).first()
        if ci.qty > item.quantity:
            flash(f'The quantity of {item.name} is unavailable ! Please reduce the quantity ! Available quantity : {item.quantity}...',
                  category='error')
            return redirect(url_for('cart'))
    if flask_request.method == 'GET':
        return render_template('checkout.html', cartid=cartid,
                               cartitems=cartitems, items=items,
                               totalqty=totalqty, totalprice=totalprice)
    elif flask_request.method == 'POST':
        try:
            cname = flask_request.form.get('customername')
        except:
            cname = ''
        try:
            caddress = flask_request.form.get('customeraddress')
        except:
            caddress = ''
        try:
            cgstin = flask_request.form.get('customergstin')
        except:
            cgstin = ''
        existingc = customer_model.query.filter_by(name=cname).first()
        if not existingc:
            existingc = customer_model(
                name=cname, address=caddress, gstno=cgstin)
            db.session.add(existingc)
            db.session.commit()
        return redirect(url_for('checkoutcomplete', cartid=cartid,
                                customerid=existingc.customerid))


@app.route('/checkout/<int:cartid>/complete/<int:customerid>')
@login_required
def checkoutcomplete(cartid, customerid):
    cart = cart_model.query.filter_by(cartid=cartid).first()
    cart.type = 'ordered'
    cartitems = cart_item.query.filter_by(cartid=cartid).all()
    totalprice = 0.0
    for i in cartitems:
        item = item_model.query.filter_by(itemid=i.itemid).first()
        totalprice += float(item.price)*int(i.qty)
        item.quantity -= i.qty
        i.purchased = True
        db.session.commit()
    order = order_model(cartid=cartid, totalqty=len(cartitems),
                        totalprice=totalprice, userid=current_user.id,
                        customerid=customerid)
    db.session.add(order)
    db.session.commit()
    return redirect(url_for('orders'))


@app.route('/orders')
@login_required
def orders():
    cartitems = cart_item.query.all()
    items = item_model.query.all()
    customers = customer_model.query.all()
    if current_user.role == 'user':
        userorders = order_model.query.filter_by(userid=current_user.id).all()
        return render_template('order.html',
                               userorders=userorders, cartitems=cartitems,
                               items=items, currentuser=current_user,
                               customers=customers)
    elif current_user.role == 'admin':
        userorders = order_model.query.all()
        users = user.query.all()
        return render_template('order.html',
                               userorders=userorders, cartitems=cartitems,
                               items=items, currentuser=current_user,
                               users=users, customers=customers)


@app.route('/addnote/<int:itemid>', methods=['GET', 'POST'])
def addnote(itemid):
    if flask_request.method == 'POST':
        title = flask_request.form.get('notetitle')
        text = flask_request.form.get('notetext')
        newnote = note_model(notetitle=title, notetext=text,
                             userid=current_user.id, itemid=itemid)
        db.session.add(newnote)
        db.session.commit()
        return redirect(url_for('showitem', itemid=itemid))


@app.route('/deletenote/<int:noteid>')
def deletenote(noteid):
    note = note_model.query.get_or_404(noteid)
    itemid = note.itemid
    db.session.delete(note)
    db.session.commit()
    return redirect(url_for('showitem', itemid=itemid))


@app.route('/search', methods=['GET', 'POST'])
@login_required
def search():
    if flask_request.method == 'GET':
        return render_template('search.html', result='', searchterm='')
    elif flask_request.method == 'POST':
        searchterm = flask_request.form.get('searchterm')
        searchitems = item_model.query.filter(
            item_model.name.like(f'%{searchterm}%')).all()
        cats = category_model.query.all()
        return render_template('search.html',
                               results=searchitems, searchterm=searchterm,
                               cats=cats, currentuser=current_user)


@app.route('/analyze')
@login_required
def analyze():
    barchart = adminbarchart()
    piechart = adminpiechart()
    return render_template('analysis.html',
                           barchart=barchart, piechart=piechart)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

# ================================== GRAPHS & CHARTS ==================================


def adminbarchart():
    categories = category_model.query.all()
    cartitems = cart_item.query.filter_by(purchased=True).all()
    category_counts = {}
    categorynames = []
    item_counts = []
    for category in categories:
        categorynames.append(category.name)
        item_counts.append(0)
        if category not in category_counts:
            category_counts[category.catid] = 0
    for i in cartitems:
        item = item_model.query.filter_by(itemid=i.itemid).first()
        if item.category not in category_counts:
            category_counts[item.category] = 0
        category_counts[item.category] += i.qty
    for category in categories:
        item_counts[category.catid-1] = category_counts[category.catid]
    print(item_counts)
    print(item_counts)
    plt.figure(figsize=(10, 6))
    plt.bar(categorynames, item_counts, color='skyblue')
    plt.xlabel('Items Sold by category')
    plt.ylabel('Frequency')
    plt.title('Category Wise Analysis')
    plt.xticks(rotation=45, ha='right')
    plt.yticks(np.arange(0, max(item_counts) + 1, 1))
    plt.tight_layout()
    chart_filename = 'admin_bargraph.jpg'
    chart_path = os.path.join(app.static_folder, 'charts', chart_filename)
    plt.savefig(chart_path)
    plt.close()
    return chart_path


def adminpiechart():
    allorders = order_model.query.all()
    user_orders = {}
    for order in allorders:
        if order.userid not in user_orders:
            user_orders[order.userid] = 0
        user_orders[order.userid] += order.totalprice
    users = user.query.all()
    user_list = []
    user_total = []
    for u in users:
        if u.id not in user_orders:
            user_orders[u.id] = 0
        user_list.append(u.username)
        user_total.append(user_orders[u.id])
    if len(user_total) == 0:
        for i in range(len(user_list)):
            user_total.append(0)
    print(user_total)
    colors = ['lightskyblue', 'lightcoral',
              'lightpink', 'lightyellow', 'lightgreen']
    plt.figure(figsize=(8, 8))
    plt.pie(user_total, labels=user_list, colors=colors,
            autopct='%1.1f%%', startangle=140)
    plt.axis('equal')
    plt.title('Total sales by users')
    chart_filename = 'admin_piechart.jpg'
    chart_path = os.path.join(app.static_folder, 'charts', chart_filename)
    plt.savefig(chart_path)
    plt.close()
    return chart_path


# ================================== API RESOURCES ==================================
class ItemResources(Resource):
    def get(self, itemid):
        item = item_model.query.get_or_404(int(itemid))
        return {
            'itemid': item.itemid,
            'item_name': item.name,
            'part_no': item.partno,
            'category': item.category,
            'description': item.description,
            'quantity': item.quantity,
            'price': float(item.price),
        }

    def delete(self, itemid):
        it = item_model.query.get_or_404(itemid)
        db.session.query(cart_item).filter_by(
            itemid=it.itemid, purchased=False).delete()
        db.session.query(item_request).filter_by(itemid=it.itemid).delete()
        db.session.query(note_model).filter_by(itemid=it.itemid).delete()
        it.deleted = True
        db.session.commit()
        return {
            'message': 'item successfully deleted !',
        }

    def put(self, itemid):
        data = flask_request.get_json()
        item = item_model.query.filter_by(itemid=int(itemid))
        item.update({
            item_model.name: data['name'],
            item_model.partno: data['partno'],
            item_model.category: data['category'],
            item_model.description: data['description'],
            item_model.quantity: data['quantity'],
            item_model.price: float(data['price']), })
        db.session.commit()
        return {'message': 'item successfully updated !'}


class ItemListResources(Resource):
    def get(self):
        items = item_model.query.all()
        result = []
        for item in items:
            result.append({
                'itemid': item.itemid,
                'item_name': item.name,
                'part_no': item.partno,
                'category': item.category,
                'quantity': item.quantity,
                'price': float(item.price),
            })
        return result

    def post(self):
        data = flask_request.get_json()
        newitem = item_model(
            name=data['name'],
            partno=data['partno'],
            category=data['category'],
            description=data['description'],
            quantity=data['quantity'],
            price=float(data['price'])
        )
        db.session.add(newitem)
        db.session.commit()
        return {'message': 'new item added !'}


api.add_resource(ItemResources, '/api/item/<itemid>')
api.add_resource(ItemListResources, '/api/item/list')

# ================================== GENERATE ITEMS FRON CSV ==================================


def datagen():
    u = user.query.all()
    if not u:
        us1 = user(username='admin', email="admin@gmail.com",
                   password='password', role='admin')
        db.session.add(us1)
        us2 = user(username='user', email="user1@gmail.com",
                   password='password', role='user')
        db.session.add(us2)
        db.session.commit()

    c = category_model.query.all()
    if not c:
        with open('./static/category.csv', newline='') as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                des = category_model(
                    name=row[0], description=row[1])
                db.session.add(des)
            db.session.commit()
    i = item_model.query.all()
    if not i:
        with open('./static/item.csv', newline='') as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                des = item_model(
                    name=row[0], partno=row[1],
                    description=row[2], quantity=row[3],
                    price=row[4], category=row[5], location=row[6])
                db.session.add(des)
            db.session.commit()


datagen()

# ================================== RUN THE APP ==================================
if __name__ == "__main__":
    app.run(debug=True)
