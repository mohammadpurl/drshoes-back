# دادهٔ محصولات (کنار پروژه)

## ساختار

```
Backend/
├── data/
│   ├── products.json    ← لیست اولیه محصولات (seed)
│   └── README.md
└── media/
    └── products/
        └── {slug}/      ← عکس و ویدئوی هر کفش (آپلود ادمین)
            ├── abc.jpg
            └── def.mp4
```

## `products.json`

- خروجی export از فرانت یا ویرایش دستی
- در **اولین اجرای سرور** اگر دیتابیس خالی باشد import می‌شود
- فقط **متادیتا** (نام، قیمت، توضیحات، …) — نه فایل باینری

## `media/products/{slug}/`

- فایل‌های واقعی تصویر/ویدئو
- ساختار استاندارد بعد از `python -m scripts.organize_media`:

```
media/products/
├── adizero-boston-12/
│   └── _adizero-boston-1238-....jpg
├── on-cloudmonster-2/
│   ├── black/
│   ├── white/
│   └── orange/
└── nike-v2k/
    └── v2k.jpg
```

- لیست URLها: **`data/media_manifest.json`** (بعد از organize)
- تحلیل تکراری‌ها: **`data/media_analysis.json`**

## بعداً: مهاجرت به S3

1. در `.env`: `STORAGE_BACKEND=s3` و تنظیمات S3/Supabase
2. اجرا: `python -m scripts.migrate_media_to_s3`
3. آپلودهای جدید مستقیم به S3 می‌روند
