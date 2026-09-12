import tempfile
import unittest
from pathlib import Path

import app as shop


class MocStoreSmokeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp_dir = tempfile.TemporaryDirectory()
        shop.DB_PATH = Path(cls.temp_dir.name) / "test-shop.db"
        shop.init_db()
        shop.app.config.update(TESTING=True)

    @classmethod
    def tearDownClass(cls):
        cls.temp_dir.cleanup()

    def test_storefront_pages_render(self):
        client = shop.app.test_client()
        for path in ["/", "/search?q=Hoodie", "/product?id=1", "/cart"]:
            response = client.get(path)
            self.assertEqual(response.status_code, 200, path)
        self.assertIn("MỘC".encode(), client.get("/").data)
        self.assertEqual(client.get("/account").status_code, 302)

    def test_normal_customer_and_admin_login(self):
        customer = shop.app.test_client()
        response = customer.post("/login", data={"username": "demo", "password": "demo"})
        self.assertEqual(response.status_code, 302)

        admin = shop.app.test_client()
        response = admin.post("/login", data={"username": "admin", "password": "admin123"})
        self.assertIn("/admin", response.location)
        self.assertEqual(admin.get("/admin").status_code, 200)

    def test_untrusted_inputs_are_handled(self):
        client = shop.app.test_client()
        blocked = client.post(
            "/login", data={"username": "admin' -- ", "password": ""}
        )
        self.assertEqual(blocked.status_code, 200)
        self.assertIn("không đúng".encode(), blocked.data)
        product = client.get("/product", query_string={"id": "not-a-number"})
        self.assertEqual(product.status_code, 200)
        self.assertIn("Không có sản phẩm".encode(), product.data)
        search = client.get(
            "/search",
            query_string={"q": "' <từ khóa không hợp lệ>"},
        )
        self.assertEqual(search.status_code, 200)
        self.assertNotIn(b"admin123", search.data)

    def test_size_cart_coupon_and_checkout(self):
        client = shop.app.test_client()
        client.post("/login", data={"username": "demo", "password": "demo"})
        client.post(
            "/cart/add/1",
            data={"size": "S", "color": "do-san-ho", "quantity": "2"},
        )
        client.post(
            "/cart/add/1",
            data={"size": "M", "color": "do-san-ho", "quantity": "1"},
        )
        cart = client.get("/cart")
        self.assertIn(b"Size S", cart.data)
        self.assertIn(b"Size M", cart.data)

        client.post("/cart/coupon", data={"coupon": "MOCTREK10"})
        checkout = client.get("/checkout")
        self.assertEqual(checkout.status_code, 200)
        self.assertIn("Thông tin thanh toán".encode(), checkout.data)

        placed = client.post(
            "/checkout",
            data={
                "full_name": "Nguyễn Minh Anh",
                "phone": "0988123456",
                "email": "minhanh@example.com",
                "address": "12 Nguyễn Trãi",
                "district": "Thanh Xuân",
                "city": "Hà Nội",
                "checkout_note": "Gọi trước khi giao",
                "payment": "cod",
            },
        )
        self.assertIn("/checkout/success", placed.location)
        confirmation = client.get(placed.location)
        self.assertIn("Đặt hàng thành công".encode(), confirmation.data)

    def test_customer_admin_order_connection(self):
        admin = shop.app.test_client()
        admin.post("/login", data={"username": "admin", "password": "admin123"})
        dashboard = admin.get("/admin")
        self.assertIn("demo".encode(), dashboard.data)
        self.assertIn("admin-status-form".encode(), dashboard.data)

        updated = admin.post("/admin/orders/1/status", data={"status": "Đang giao"})
        self.assertIn("/admin", updated.location)

        customer = shop.app.test_client()
        customer.post("/login", data={"username": "demo", "password": "demo"})
        account = customer.get("/account")
        self.assertEqual(account.status_code, 200)
        self.assertIn("Hoodie nam Hành Trình Đỏ".encode(), account.data)
        self.assertIn("Đang giao".encode(), account.data)


if __name__ == "__main__":
    unittest.main()
