# ذخیرهٔ محصولات — لوکال الان، S3 بعداً

## ساختار کنار پروژه

```
Backend/
├── data/
│   └── products.json       # متادیتای کفش‌ها (seed)
└── media/
    └── products/
        └── nike-pegasus-41/
            ├── photo1.jpg
            └── clip.mp4
```

- **`data/`** → اطلاعات متنی/JSON (در git می‌ماند)
- **`media/`** → فایل‌های آپلودشده (در gitignore — فقط روی دیسک شما)

## الان (لوکال)

`.env`:

```env
STORAGE_BACKEND=local
STATIC_URL_BASE=http://localhost:8000/static
```

آپلود ادمین → فایل در `media/products/{slug}/` → URL مثل:

`http://localhost:8000/static/products/nike-pegasus-41/abc.jpg`

## بعداً (S3)

1. در `.env` بگذارید `STORAGE_BACKEND=s3` و کلیدهای S3/Supabase را پر کنید
2. فایل‌های قدیمی را منتقل کنید:

```powershell
python -m scripts.migrate_media_to_s3 --dry-run
python -m scripts.migrate_media_to_s3
```

اسکریپت فایل‌های `media/` را به S3 می‌فرستد و URLهای دیتابیس را به‌روز می‌کند.

## پنل ادمین (فرانت)

1. `POST /admin/uploads/media?slug=...` + فایل
2. URL برگشتی → `images` / `videos` در `POST /admin/products`

جزئیات: [data/README.md](../data/README.md)
