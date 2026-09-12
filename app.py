"""MOC Store - Vietnamese ecommerce demo storefront."""

import os
import re
import secrets
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

from flask import Flask, flash, g, redirect, render_template, request, session, url_for


ROOT = Path(__file__).resolve().parent
DB_PATH = Path(os.getenv("MOC_DB_PATH", "/tmp/moc-store.db" if os.getenv("VERCEL") else str(ROOT / "shop.db")))

app = Flask(__name__)
app.config.update(
    SECRET_KEY=os.getenv("DEMO_SECRET_KEY", "moc-store-demo-secret"),
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
)


COUPONS = {"MOCTREK10": 10, "MOCVIET5": 5}
ORDER_STATUSES = ("Chờ xác nhận", "Đang chuẩn bị", "Đang giao", "Hoàn tất", "Đã hủy")

# The upstream template ships 15 distinct product photos.  Keep the catalogue
# tied to those photos so a shoe is never presented as a jacket (or vice versa).
CATALOG_VERSION = "photo-matched-v3"
CATALOG = [
    {
        "name": "Hoodie nam Hành Trình Đỏ",
        "price": 829000,
        "description": "Nỉ cotton đỏ san hô, phom unisex và hình in cảm hứng cắm trại.",
        "stock": 42,
        "image": "product-1.jpg",
        "hover": "product-1b.jpg",
        "category": "Hoodie",
        "sizes": ("S", "M", "L", "XL"),
        "colors": (("do-san-ho", "Đỏ san hô", "#ef334f"),),
    },
    {
        "name": "Hoodie nữ Rừng Xanh",
        "price": 769000,
        "description": "Hoodie xanh lá phom rộng, mặt trong mềm và bo tay giữ dáng.",
        "stock": 31,
        "image": "product-2.jpg",
        "category": "Hoodie",
        "sizes": ("S", "M", "L", "XL"),
        "colors": (("xanh-rung", "Xanh rừng", "#18a866"),),
    },
    {
        "name": "Hoodie nam Đỉnh Mây",
        "price": 849000,
        "description": "Sắc tím lam nổi bật, nỉ dày vừa và túi kangaroo tiện dụng.",
        "stock": 36,
        "image": "product-3.jpg",
        "category": "Hoodie",
        "sizes": ("S", "M", "L", "XL"),
        "colors": (("tim-lam", "Tím lam", "#6667e8"),),
    },
    {
        "name": "Hoodie nữ Than Đá",
        "price": 789000,
        "description": "Tông xám than dễ phối, phom nữ thoải mái và lớp nỉ ấm nhẹ.",
        "stock": 28,
        "image": "product-4.jpg",
        "category": "Hoodie",
        "sizes": ("S", "M", "L", "XL"),
        "colors": (("xam-than", "Xám than", "#343b3b"),),
    },
    {
        "name": "Áo phao nữ Sương Mai",
        "price": 1190000,
        "description": "Áo phao tím nhạt, nhẹ và giữ nhiệt tốt cho những ngày se lạnh.",
        "stock": 18,
        "image": "product-5.jpg",
        "hover": "product-5b.jpg",
        "category": "Áo phao",
        "sizes": ("S", "M", "L", "XL"),
        "colors": (("tim-suong", "Tím sương", "#c6c8f4"),),
    },
    {
        "name": "Hoodie nam Dốc Nắng",
        "price": 739000,
        "description": "Hoodie xanh chanh trẻ trung, mềm thoáng cho hoạt động hằng ngày.",
        "stock": 55,
        "image": "product-6.jpg",
        "category": "Hoodie",
        "sizes": ("S", "M", "L", "XL"),
        "colors": (("xanh-chanh", "Xanh chanh", "#b9ed68"),),
    },
    {
        "name": "Hoodie nữ Biển Sớm",
        "price": 749000,
        "description": "Phom dài rộng, màu xanh ngọc và họa tiết tối giản cho ngày dạo phố.",
        "stock": 38,
        "image": "product-7.jpg",
        "category": "Hoodie",
        "sizes": ("S", "M", "L", "XL"),
        "colors": (("xanh-ngoc", "Xanh ngọc", "#38d0cc"),),
    },
    {
        "name": "Hoodie nam Mây Trời",
        "price": 779000,
        "description": "Hoodie xanh da trời, phom cơ bản và túi trước rộng tiện dụng.",
        "stock": 47,
        "image": "product-8.jpg",
        "category": "Hoodie",
        "sizes": ("S", "M", "L", "XL"),
        "colors": (("xanh-troi", "Xanh da trời", "#8ccce9"),),
    },
    {
        "name": "Giày trekking nữ Vách Đá",
        "price": 1690000,
        "description": "Cổ cao bảo vệ cổ chân, đế bám địa hình và mũi giày gia cường.",
        "stock": 23,
        "image": "product-10.jpg",
        "category": "Giày trekking",
        "sizes": ("36", "37", "38", "39", "40"),
        "colors": (("xam-do", "Xám phối đỏ", "#5b6062"),),
    },
    {
        "name": "Giày trekking Cam Lửa",
        "price": 1790000,
        "description": "Đế cao su chống trượt, cổ giày chắc chắn và màu cam dễ nhận diện.",
        "stock": 19,
        "image": "product-11.jpg",
        "category": "Giày trekking",
        "sizes": ("39", "40", "41", "42", "43", "44"),
        "colors": (("cam-den", "Cam phối đen", "#f28b20"),),
    },
    {
        "name": "Áo thun Adventure Xanh Biển",
        "price": 359000,
        "description": "Cotton thoáng khí, cổ tròn bền dáng và hình thêu cảm hứng khám phá.",
        "stock": 64,
        "image": "product-12.jpg",
        "category": "Áo thun",
        "sizes": ("S", "M", "L", "XL"),
        "colors": (("xanh-bien", "Xanh biển", "#19608a"),),
    },
    {
        "name": "Áo thun Wanderlust Xanh Ngọc",
        "price": 369000,
        "description": "Áo thun cotton xanh ngọc, mềm nhẹ và phù hợp chuyến đi mùa hè.",
        "stock": 58,
        "image": "product-13.jpg",
        "category": "Áo thun",
        "sizes": ("S", "M", "L", "XL"),
        "colors": (("ngoc-nhat", "Xanh ngọc nhạt", "#66d0cf"),),
    },
    {
        "name": "Áo thun Núi Rừng Xanh Lá",
        "price": 379000,
        "description": "Cotton xanh rêu đậm cùng hình in ngọn núi, dễ phối cho ngày thường.",
        "stock": 52,
        "image": "product-14.jpg",
        "category": "Áo thun",
        "sizes": ("S", "M", "L", "XL"),
        "colors": (("xanh-reu", "Xanh rêu", "#173f2b"),),
    },
    {
        "name": "Áo thun Trại Núi Cam Đất",
        "price": 389000,
        "description": "Tông cam đất ấm, hình in nhiều màu và chất cotton dễ chịu.",
        "stock": 49,
        "image": "product-15.jpg",
        "category": "Áo thun",
        "sizes": ("S", "M", "L", "XL"),
        "colors": (("cam-dat", "Cam đất", "#c96f56"),),
    },
    {
        "name": "Áo thun Đi Xa Xanh Than",
        "price": 379000,
        "description": "Áo thun xanh than với hình in rừng thông, phom unisex gọn gàng.",
        "stock": 61,
        "image": "product-16.jpg",
        "category": "Áo thun",
        "sizes": ("S", "M", "L", "XL"),
        "colors": (("xanh-than", "Xanh than", "#202b49"),),
    },
]


def catalog_entry(product_id):
    """Return consistent merchandising data for any of the 128 demo IDs."""
    product_id = max(1, int(product_id))
    base = CATALOG[(product_id - 1) % len(CATALOG)]
    edition = (product_id - 1) // len(CATALOG) + 1
    item = dict(base)
    if edition > 1:
        item["name"] = f"{base['name']} · Bản {edition:02d}"
        item["price"] = base["price"] + (edition - 1) * 12000
        item["description"] = f"{base['description']} Phiên bản màu mùa {edition:02d}."
        item["stock"] = max(8, base["stock"] - edition * 2)
    return item


def product_options(product_id):
    item = catalog_entry(product_id)
    size_kind = "shoe" if item["category"] == "Giày trekking" else "apparel"
    colors = [
        {"key": key, "label": label, "hex": color_hex}
        for key, label, color_hex in item["colors"]
    ]
    return {
        "category": item["category"],
        "sizes": item["sizes"],
        "default_size": "M" if size_kind == "apparel" else item["sizes"][len(item["sizes"]) // 2],
        "colors": colors,
        "default_color": colors[0]["key"],
        "size_kind": size_kind,
    }


ALL_PRODUCT_SIZES = {size for item in CATALOG for size in item["sizes"]}
ALL_PRODUCT_COLORS = {
    key: label for item in CATALOG for key, label, _color_hex in item["colors"]
}


def db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(_error=None):
    connection = g.pop("db", None)
    if connection is not None:
        connection.close()


def sync_photo_matched_catalog(connection):
    """Seed or migrate products once when the photo-matched catalogue changes."""
    connection.execute(
        "CREATE TABLE IF NOT EXISTS app_meta (key TEXT PRIMARY KEY, value TEXT NOT NULL)"
    )
    current = connection.execute(
        "SELECT value FROM app_meta WHERE key='catalog_version'"
    ).fetchone()
    if current and current[0] == CATALOG_VERSION:
        return

    for product_id in range(1, 129):
        item = catalog_entry(product_id)
        values = (item["name"], item["price"], item["description"], item["stock"])
        exists = connection.execute(
            "SELECT 1 FROM products WHERE id=?", (product_id,)
        ).fetchone()
        if exists:
            connection.execute(
                "UPDATE products SET name=?,price=?,description=?,stock=? WHERE id=?",
                (*values, product_id),
            )
        else:
            connection.execute(
                "INSERT INTO products (id,name,price,description,stock) VALUES (?,?,?,?,?)",
                (product_id, *values),
            )
        color_label = item["colors"][0][1]
        connection.execute(
            "UPDATE orders SET color=? WHERE product_id=? AND (color IS NULL OR color IN ('Đỏ đất','Be cát','Đen than'))",
            (color_label, product_id),
        )
    connection.execute(
        "INSERT OR REPLACE INTO app_meta (key,value) VALUES ('catalog_version',?)",
        (CATALOG_VERSION,),
    )


def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH)
    connection.executescript(
        """
        CREATE TABLE IF NOT EXISTS users (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          username TEXT UNIQUE NOT NULL,
          password TEXT NOT NULL,
          is_admin INTEGER NOT NULL DEFAULT 0,
          phone TEXT,
          address TEXT
        );
        CREATE TABLE IF NOT EXISTS products (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          name TEXT NOT NULL,
          price INTEGER NOT NULL,
          description TEXT NOT NULL,
          stock INTEGER NOT NULL DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS orders (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          user_id INTEGER NOT NULL,
          product_id INTEGER NOT NULL,
          quantity INTEGER NOT NULL,
          total INTEGER NOT NULL,
          note TEXT DEFAULT '',
          size TEXT DEFAULT 'M',
          color TEXT DEFAULT 'Đỏ đất',
          order_code TEXT,
          customer_name TEXT,
          email TEXT,
          phone TEXT,
          shipping_address TEXT,
          payment_method TEXT DEFAULT 'cod',
          status TEXT DEFAULT 'Đang xử lý',
          created_at TEXT,
          FOREIGN KEY (user_id) REFERENCES users (id),
          FOREIGN KEY (product_id) REFERENCES products (id)
        );
        """
    )
    existing_columns = {
        row[1] for row in connection.execute("PRAGMA table_info(orders)").fetchall()
    }
    order_columns = {
        "size": "TEXT DEFAULT 'M'",
        "color": "TEXT DEFAULT 'Đỏ đất'",
        "order_code": "TEXT",
        "customer_name": "TEXT",
        "email": "TEXT",
        "phone": "TEXT",
        "shipping_address": "TEXT",
        "payment_method": "TEXT DEFAULT 'cod'",
        "status": "TEXT DEFAULT 'Đang xử lý'",
        "created_at": "TEXT",
    }
    for column, definition in order_columns.items():
        if column not in existing_columns:
            connection.execute(f"ALTER TABLE orders ADD COLUMN {column} {definition}")
    if connection.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 0:
        connection.executemany(
            "INSERT INTO users (username,password,is_admin,phone,address) VALUES (?,?,?,?,?)",
            [
                ("admin", "admin123", 1, "0901 234 567", "Văn phòng MỘC, Hà Nội"),
                ("demo", "demo", 0, "0988 123 456", "12 Nguyễn Trãi, Thanh Xuân, Hà Nội"),
                ("mai", "mai2025", 0, "0935 222 888", "08 Lê Lợi, Hải Châu, Đà Nẵng"),
            ],
        )
    if connection.execute("SELECT COUNT(*) FROM orders").fetchone()[0] == 0:
        connection.executemany(
            "INSERT INTO orders (user_id,product_id,quantity,total,note) VALUES (?,?,?,?,?)",
            [
                (2, 1, 1, 829000, "Giao giờ hành chính"),
                (3, 5, 2, 1318000, "Gọi trước khi giao"),
                (1, 2, 1, 1190000, "Đơn kiểm thử nội bộ"),
            ],
        )
    sync_photo_matched_catalog(connection)
    connection.commit()
    connection.close()


def reset_database():
    if DB_PATH.exists():
        DB_PATH.unlink()
    init_db()


def visual(product_id):
    try:
        item = catalog_entry(product_id)
    except (TypeError, ValueError):
        item = CATALOG[0]
    image = item["image"]
    return {"image": image, "hover": item.get("hover", image)}


@app.template_filter("vnd")
def vnd(value):
    try:
        return f"{int(value):,}".replace(",", ".") + " ₫"
    except (TypeError, ValueError):
        return str(value)


@app.context_processor
def template_context():
    cart = session.get("cart", {})
    return {
        "current_user": session.get("user"),
        "cart_count": sum(cart.values()),
        "visual": visual,
        "product_options": product_options,
    }


@app.before_request
def ensure_database():
    if not DB_PATH.exists():
        init_db()


@app.before_request
def refresh_user_role():
    user = session.get("user")
    if not user:
        return
    try:
        row = db().execute("SELECT id,username,is_admin FROM users WHERE id=?", (user["id"],)).fetchone()
    except sqlite3.Error:
        return
    if row:
        session["user"] = dict(row)


@app.route("/")
def index():
    products = db().execute(
        "SELECT id,name,price,description,stock FROM products ORDER BY id LIMIT 8"
    ).fetchall()
    return render_template("index.html", products=products)


@app.route("/search")
def search():
    q = request.args.get("q", "")
    sort = request.args.get("sort", "newest")
    sort_sql = {"newest": "id DESC", "price_asc": "price ASC", "price_desc": "price DESC"}.get(sort, "id DESC")
    try:
        max_price = max(0, min(int(request.args.get("max_price", "2000000")), 2000000))
    except ValueError:
        max_price = 2000000
    connection = db()
    sql = f"SELECT id,name,price,description,stock FROM products WHERE (name LIKE ? OR description LIKE ?) AND price <= ? ORDER BY {sort_sql} LIMIT 128"
    params = (f"%{q}%", f"%{q}%", max_price)
    rows = connection.execute(sql, params).fetchall()
    return render_template("search.html", products=rows, q=q, sort=sort, max_price=max_price)


@app.route("/product")
def product():
    product_id = request.args.get("id", "1")
    try:
        number = int(product_id)
    except ValueError:
        number = -1
    row = db().execute(
        "SELECT id,name,price,description,stock FROM products WHERE id=?", (number,)
    ).fetchone()
    return render_template("product.html", product=row, product_id=product_id, error=None)


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")
    username = request.form.get("username", "")
    password = request.form.get("password", "")
    user = db().execute(
        "SELECT id,username,password,is_admin FROM users WHERE username=? AND password=?",
        (username, password),
    ).fetchone()
    if user:
        session["user"] = {"id": user["id"], "username": user["username"], "is_admin": user["is_admin"]}
        flash(f"Xin chào {user['username']}!", "success")
        next_url = session.pop("next_url", None)
        if next_url:
            return redirect(next_url)
        return redirect(url_for("admin" if user["is_admin"] else "index"))
    flash("Tên đăng nhập hoặc mật khẩu không đúng.", "danger")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.pop("user", None)
    flash("Bạn đã đăng xuất.", "success")
    return redirect(url_for("index"))


@app.post("/cart/add/<int:product_id>")
def add_cart(product_id):
    product_row = db().execute(
        "SELECT id,stock FROM products WHERE id=?", (product_id,)
    ).fetchone()
    if not product_row:
        flash("Không tìm thấy sản phẩm.", "danger")
        return redirect(url_for("index"))

    options = product_options(product_id)
    size = request.form.get("size", options["default_size"]).upper()
    color = request.form.get("color", options["default_color"])
    valid_sizes = set(options["sizes"])
    valid_colors = {item["key"] for item in options["colors"]}
    if size not in valid_sizes or color not in valid_colors:
        flash("Kích cỡ hoặc màu sắc không hợp lệ.", "danger")
        return redirect(request.referrer or url_for("index"))
    try:
        quantity = max(1, min(int(request.form.get("quantity", "1")), 5))
    except ValueError:
        quantity = 1

    cart = session.get("cart", {})
    key = f"{product_id}:{size}:{color}"
    cart[key] = min(cart.get(key, 0) + quantity, min(product_row["stock"], 9))
    session["cart"] = cart
    flash(f"Đã thêm size {size} vào giỏ hàng.", "success")
    return redirect(request.referrer or url_for("index"))


def parse_cart_key(key):
    parts = key.split(":")
    try:
        product_id = int(parts[0])
    except (TypeError, ValueError):
        return None
    options = product_options(product_id)
    valid_sizes = set(options["sizes"])
    valid_colors = {item["key"] for item in options["colors"]}
    size = parts[1] if len(parts) > 1 and parts[1] in valid_sizes else options["default_size"]
    color = parts[2] if len(parts) > 2 and parts[2] in valid_colors else options["default_color"]
    return product_id, size, color


def get_cart_items(connection):
    cart = session.get("cart", {})
    if not cart:
        return [], 0
    parsed = {key: parse_cart_key(key) for key in cart}
    parsed = {key: value for key, value in parsed.items() if value is not None}
    ids = sorted({value[0] for value in parsed.values()})
    if not ids:
        session["cart"] = {}
        return [], 0
    placeholders = ",".join("?" for _ in ids)
    rows = connection.execute(
        f"SELECT id,name,price,description,stock FROM products WHERE id IN ({placeholders})", ids
    ).fetchall()
    products = {row["id"]: row for row in rows}
    items, total = [], 0
    for key, (product_id, size, color) in parsed.items():
        row = products.get(product_id)
        if not row:
            continue
        quantity = max(1, min(int(cart[key]), min(row["stock"], 9)))
        subtotal = row["price"] * quantity
        items.append(
            {
                "key": key,
                "product": row,
                "quantity": quantity,
                "size": size,
                "color": ALL_PRODUCT_COLORS[color],
                "color_key": color,
                "category": product_options(product_id)["category"],
                "subtotal": subtotal,
            }
        )
        total += subtotal
    return items, total


def order_totals(subtotal):
    coupon = session.get("coupon")
    percent = COUPONS.get(coupon, 0)
    discount = subtotal * percent // 100
    shipping = 0 if subtotal - discount >= 799000 or subtotal == 0 else 30000
    return {
        "subtotal": subtotal,
        "discount": discount,
        "shipping": shipping,
        "grand_total": subtotal - discount + shipping,
        "coupon": coupon,
        "coupon_percent": percent,
    }


@app.post("/cart/update")
def update_cart():
    cart_data = session.get("cart", {})
    key = request.form.get("line_key", "")
    action = request.form.get("action", "")
    if key not in cart_data:
        flash("Sản phẩm trong giỏ không còn tồn tại.", "danger")
        return redirect(url_for("cart"))
    if action == "remove":
        cart_data.pop(key, None)
    elif action == "increase":
        parsed = parse_cart_key(key)
        stock = 0
        if parsed:
            row = db().execute("SELECT stock FROM products WHERE id=?", (parsed[0],)).fetchone()
            stock = row["stock"] if row else 0
        cart_data[key] = min(int(cart_data[key]) + 1, stock, 9)
    elif action == "decrease":
        cart_data[key] = int(cart_data[key]) - 1
        if cart_data[key] <= 0:
            cart_data.pop(key, None)
    session["cart"] = cart_data
    return redirect(url_for("cart"))


@app.post("/cart/coupon")
def apply_coupon():
    code = request.form.get("coupon", "").strip().upper()
    if code in COUPONS:
        session["coupon"] = code
        flash(f"Đã áp dụng mã {code}.", "success")
    else:
        session.pop("coupon", None)
        flash("Mã ưu đãi không hợp lệ.", "danger")
    return redirect(url_for("cart"))


@app.route("/cart")
def cart():
    connection = db()
    items, subtotal = get_cart_items(connection)
    totals = order_totals(subtotal)
    return render_template(
        "cart.html",
        items=items,
        **totals,
    )


def validate_checkout(form):
    errors = []
    full_name = form.get("full_name", "").strip()
    email = form.get("email", "").strip()
    phone = re.sub(r"\D", "", form.get("phone", ""))
    address = form.get("address", "").strip()
    district = form.get("district", "").strip()
    city = form.get("city", "").strip()
    payment = form.get("payment", "cod")

    if len(full_name) < 2:
        errors.append("Vui lòng nhập họ và tên.")
    if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email):
        errors.append("Email chưa đúng định dạng.")
    if not 9 <= len(phone) <= 11:
        errors.append("Số điện thoại phải có từ 9 đến 11 chữ số.")
    if not address or not district or not city:
        errors.append("Vui lòng nhập đầy đủ địa chỉ giao hàng.")
    if payment not in {"cod", "bank", "card"}:
        errors.append("Phương thức thanh toán không hợp lệ.")
    if payment == "card":
        card_number = re.sub(r"\D", "", form.get("card_number", ""))
        expiry = form.get("expiry", "").strip()
        cvv = re.sub(r"\D", "", form.get("cvv", ""))
        if len(card_number) != 16 or not re.fullmatch(r"(0[1-9]|1[0-2])/\d{2}", expiry) or len(cvv) not in {3, 4}:
            errors.append("Thông tin thẻ test chưa hợp lệ.")
    return errors


@app.route("/checkout", methods=["GET", "POST"])
def checkout():
    if not session.get("user"):
        session["next_url"] = url_for("checkout")
        flash("Đăng nhập để tiếp tục thanh toán.", "danger")
        return redirect(url_for("login"))

    connection = db()
    items, subtotal = get_cart_items(connection)
    if not items:
        flash("Giỏ hàng đang trống.", "danger")
        return redirect(url_for("cart"))
    totals = order_totals(subtotal)
    profile = connection.execute(
        "SELECT username,phone,address FROM users WHERE id=?", (session["user"]["id"],)
    ).fetchone()

    if request.method == "POST":
        errors = validate_checkout(request.form)
        if errors:
            for message in errors:
                flash(message, "danger")
            return render_template(
                "checkout.html", items=items, profile=profile, form=request.form, **totals
            )

        payment = request.form["payment"]
        payment_labels = {
            "cod": "Thanh toán khi nhận hàng",
            "bank": "Chuyển khoản ngân hàng",
            "card": "Thẻ test (mô phỏng)",
        }
        status = {
            "cod": "Chờ xác nhận",
            "bank": "Chờ chuyển khoản",
            "card": "Đã thanh toán (mô phỏng)",
        }[payment]
        order_code = "MOC" + datetime.now().strftime("%y%m%d%H%M") + secrets.token_hex(2).upper()
        shipping_address = ", ".join(
            [request.form["address"].strip(), request.form["district"].strip(), request.form["city"].strip()]
        )
        created_at = datetime.now().strftime("%d/%m/%Y %H:%M")
        note = request.form.get("checkout_note", "").strip()
        order_ids = []
        for item in items:
            item_total = item["subtotal"] * (100 - totals["coupon_percent"]) // 100
            cursor = connection.execute(
                """
                INSERT INTO orders (
                    user_id,product_id,quantity,total,note,size,color,order_code,
                    customer_name,email,phone,shipping_address,payment_method,status,created_at
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                """,
                (
                    session["user"]["id"], item["product"]["id"], item["quantity"],
                    item_total, note, item["size"], item["color"], order_code,
                    request.form["full_name"].strip(), request.form["email"].strip(),
                    request.form["phone"].strip(), shipping_address, payment, status, created_at,
                ),
            )
            order_ids.append(cursor.lastrowid)
        connection.commit()

        session["last_order"] = {
            "code": order_code,
            "total": totals["grand_total"],
            "payment": payment_labels[payment],
            "status": status,
            "address": shipping_address,
            "created_at": created_at,
            "item_count": sum(item["quantity"] for item in items),
            "order_ids": order_ids,
        }
        session["cart"] = {}
        session.pop("coupon", None)
        return redirect(url_for("checkout_success"))

    return render_template("checkout.html", items=items, profile=profile, form={}, **totals)


@app.route("/checkout/success")
def checkout_success():
    order = session.get("last_order")
    if not order:
        return redirect(url_for("index"))
    return render_template("checkout_success.html", order=order)


@app.route("/account")
def account():
    if not session.get("user"):
        session["next_url"] = url_for("account")
        flash("Đăng nhập để xem đơn hàng của bạn.", "danger")
        return redirect(url_for("login"))
    orders = db().execute(
        """
        SELECT o.id,o.order_code,o.quantity,o.total,o.size,o.color,o.status,o.created_at,
               o.shipping_address,o.payment_method,p.name product_name
        FROM orders o JOIN products p ON p.id=o.product_id
        WHERE o.user_id=? ORDER BY o.id DESC
        """,
        (session["user"]["id"],),
    ).fetchall()
    return render_template("account.html", orders=orders)


@app.route("/admin")
def admin():
    user = session.get("user")
    if not user or not user["is_admin"]:
        flash("Bạn cần quyền quản trị.", "danger")
        return redirect(url_for("login"))
    connection = db()
    users = connection.execute("SELECT id,username,is_admin,phone,address FROM users ORDER BY id").fetchall()
    orders = connection.execute(
        """
        SELECT o.id,u.username,p.name product_name,o.quantity,o.total,o.note,
               o.size,o.color,o.order_code,o.payment_method,o.status,o.created_at,
               o.customer_name,o.email,o.phone,o.shipping_address
        FROM orders o
        JOIN users u ON u.id=o.user_id
        JOIN products p ON p.id=o.product_id
        ORDER BY o.id DESC
        """
    ).fetchall()
    return render_template("admin.html", users=users, orders=orders, revenue=sum(row["total"] for row in orders))


@app.post("/admin/orders/<int:order_id>/status")
def update_order_status(order_id):
    user = session.get("user")
    if not user or not user["is_admin"]:
        flash("Bạn cần quyền quản trị.", "danger")
        return redirect(url_for("login"))
    status = request.form.get("status", "").strip()
    if status not in ORDER_STATUSES:
        flash("Trạng thái đơn hàng không hợp lệ.", "danger")
    else:
        cursor = db().execute("UPDATE orders SET status=? WHERE id=?", (status, order_id))
        db().commit()
        message = "Đã cập nhật trạng thái đơn hàng." if cursor.rowcount else "Không tìm thấy đơn hàng."
        flash(message, "success" if cursor.rowcount else "danger")
    return redirect(url_for("admin"))


if __name__ == "__main__":
    if "--reset" in sys.argv:
        reset_database()
        print("Da khoi phuc du lieu demo.")
    else:
        init_db()
    try:
        port = int(os.getenv("MOC_PORT", "5000"))
    except ValueError:
        port = 5000
    app.run(host="127.0.0.1", port=port, debug=False)
