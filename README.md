# Dr.Shoes Backend

بک‌اند فروشگاه آنلاین: FastAPI + PostgreSQL + احراز هویت JWT + سبد خرید + سفارش + آپلود تصویر.

## Setup

```bash
cd Backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
docker compose up -d
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

در **اولین اجرا** سرور خودکار:
- جداول را می‌سازد (`create_all`)
- کاربر ادمین پیش‌فرض را اضافه می‌کند (اگر `users` خالی باشد)
- اگر محصولی نباشد، `data/products.json` را import می‌کند

اسکریپت `python -m scripts.seed` فقط برای اجرای دستی همان فرایند است (اختیاری).

- API: http://localhost:8000/docs
- ادمین پیش‌فرض (اولین اجرا): `admin@drshoes.local` / `admin123456`

## ذخیرهٔ تصویر و ویدئو (MinIO / S3)

راهنمای کامل: **[docs/STORAGE.md](docs/STORAGE.md)**

خلاصه: `docker compose up -d minio` → تنظیم `.env` با `STORAGE_BACKEND=s3` → در MinIO Console باکت را **public** کنید → آپلود با `POST /api/v1/admin/uploads/media`.

---

## ذخیرهٔ تصاویر (نسخهٔ قدیمی — local)

1. ادمین تصویر را آپلود می‌کند: `POST /api/v1/admin/uploads/image` (Bearer ادمین + `multipart/form-data`)
2. فایل در پوشه `Backend/uploads/products/` ذخیره می‌شود
3. API آدرس عمومی برمی‌گرداند، مثلاً:  
   `http://localhost:8000/static/products/a1b2c3....jpg`
4. هنگام ساخت/ویرایش محصول، همان URLها را در فیلد `images` قرار دهید

```bash
# مثال آپلود (PowerShell)
curl -X POST "http://localhost:8000/api/v1/admin/uploads/image" `
  -H "Authorization: Bearer <ADMIN_TOKEN>" `
  -F "file=@C:\path\to\shoe.jpg"
```

تنظیمات در `.env`:

| متغیر | توضیح |
|--------|--------|
| `STATIC_URL_BASE` | پیش‌وند URL تصاویر (در production دامنه/API خودتان) |
| `MAX_UPLOAD_SIZE_MB` | حداکثر حجم (پیش‌فرض ۵ مگ) |

فایل‌ها از مسیر `/static/...` سرو می‌شوند (`StaticFiles` روی `uploads/`).

### روش پیشنهادی برای production (S3 / CDN)

1. تصویر را به **S3**، **Cloudflare R2** یا **Arvan Cloud** آپلود کنید
2. URL نهایی CDN را در `Product.images` ذخیره کنید (همان آرایهٔ رشته در دیتابیس)
3. `STATIC_URL_BASE` را به دامنه CDN تغییر دهید، یا endpoint آپلود را طوری عوض کنید که مستقیم URL ابری برگرداند

**نکته:** دیتابیس فقط **آدرس URL** نگه می‌دارد، نه خود فایل باینری. برای seed فعلی از Unsplash استفاده شده؛ محصولات جدید می‌توانند URL آپلود لوکال یا CDN داشته باشند.

## API خلاصه

### عمومی
| Method | Path | توضیح |
|--------|------|--------|
| GET | `/api/v1/products` | لیست + فیلتر |
| GET | `/api/v1/products/{slug}` | جزئیات |
| GET | `/api/v1/cart` | سبد (مهمان: هدر `X-Cart-Token`) |
| POST | `/api/v1/cart/items` | افزودن به سبد |

### احراز هویت
| Method | Path |
|--------|------|
| POST | `/api/v1/auth/register` |
| POST | `/api/v1/auth/login` |
| GET | `/api/v1/auth/me` |

هدر: `Authorization: Bearer <token>`

### کاربر لاگین‌شده
| Method | Path |
|--------|------|
| GET/POST/PATCH/DELETE | `/api/v1/addresses` |
| POST | `/api/v1/orders/checkout` |
| GET | `/api/v1/orders` |
| POST | `/api/v1/products/{slug}/reviews` |

### ادمین
| Method | Path |
|--------|------|
| POST | `/api/v1/admin/uploads/image` |
| POST/PATCH/DELETE | `/api/v1/admin/products` |
| PATCH | `/api/v1/admin/orders/{id}/status` |

## Connect Next.js

```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

برای سبد مهمان، `X-Cart-Token` از پاسخ را در `localStorage` نگه دارید و در هر درخواست بفرستید.

## ساختار

```
Backend/
├── app/
│   ├── core/          # JWT, dependencies
│   ├── models/        # User, Cart, Order, Product, ...
│   ├── routes/        # API + admin/
│   └── services/
├── uploads/           # تصاویر آپلودشده (در gitignore)
├── data/products.json
└── scripts/seed.py
```
