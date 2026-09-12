# MỘC Store

Website thương mại điện tử thời trang/dã ngoại Việt Nam, chuyển thể từ giao diện [eCommerce-alpine](https://github.com/mahelhelou/eCommerce-alpine) và nối với Flask + SQLite.

MỘC có danh mục 128 sản phẩm khớp với ảnh, size áo S–XL, cỡ giày 36–44, giỏ hàng theo biến thể, mã giảm giá, checkout, lịch sử đơn hàng và dashboard quản trị. Các phương thức COD, chuyển khoản và thẻ chỉ là mô phỏng; website không thu tiền thật và không lưu dữ liệu thẻ.

## Chạy local bằng uv trên Windows PowerShell

```powershell
uv sync
uv run python app.py
```

Mở `http://127.0.0.1:5000`.

Nếu cổng 5000 đang được ứng dụng khác sử dụng:

```powershell
$env:MOC_PORT="5051"
uv run python app.py
```

Tài khoản mẫu:

- Quản trị: `admin / admin123`
- Khách hàng: `demo / demo`
- Khách hàng: `mai / mai2025`

Mã ưu đãi: `MOCTREK10` giảm 10% hoặc `MOCVIET5` giảm 5%.

## Deploy Vercel

Bản deploy dùng SQLite tạm thời trong `/tmp`, phù hợp để demo giao diện và luồng checkout. Dữ liệu đơn hàng không nên xem là dữ liệu production; muốn vận hành thật cần thay bằng database managed như Postgres và tích hợp payment gateway riêng.

```powershell
uv sync
npx vercel login
npx vercel
npx vercel --prod
```

Trong Vercel Project Settings, đặt `DEMO_SECRET_KEY` thành một giá trị bí mật riêng.

## Nguồn giao diện

Ảnh, CSS và JavaScript từ Alpine Ecommerce Template của PixelRocket, giấy phép MIT. Bản quyền và giấy phép được giữ tại `THIRD_PARTY_LICENSES/ALPINE-MIT.txt`.
