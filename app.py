#!/usr/bin/env python3
import json
import os
import re
import sqlite3
import threading
from datetime import datetime, timezone
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse

BASE = Path(__file__).resolve().parent
DATA = Path(os.environ.get("COOKSY_DATA_DIR", "/data"))
DATA.mkdir(parents=True, exist_ok=True)
DB = DATA / "cooksy.sqlite3"
LOCK = threading.Lock()
MAX_BYTES = 16384

RECIPES = [
    {"id": "ghormeh", "name": "قرمه سبزی", "subtitle": "عطر سبزی تازه، لوبیا و لیمو عمانی", "emoji": "🍲", "category": "ایرانی", "minutes": 120, "unit_price": 185000, "ingredients": [{"name":"گوشت خورشتی", "amount":150, "unit":"گرم"},{"name":"سبزی قرمه خرد شده", "amount":180, "unit":"گرم"},{"name":"لوبیا قرمز", "amount":70, "unit":"گرم"},{"name":"لیمو عمانی", "amount":1, "unit":"عدد"},{"name":"پیاز", "amount":1, "unit":"عدد"}]},
    {"id": "gheymeh", "name": "قیمه", "subtitle": "مواد لازم برای قیمه خانگی با سیب زمینی", "emoji": "🥘", "category": "ایرانی", "minutes": 100, "unit_price": 172000, "ingredients": [{"name":"گوشت خورشتی", "amount":140, "unit":"گرم"},{"name":"لپه", "amount":75, "unit":"گرم"},{"name":"رب گوجه فرنگی", "amount":35, "unit":"گرم"},{"name":"سیب زمینی", "amount":1, "unit":"عدد"},{"name":"لیمو عمانی", "amount":1, "unit":"عدد"}]},
    {"id": "zereshk", "name": "زرشک پلو با مرغ", "subtitle": "مرغ مزه دار، برنج و زرشک", "emoji": "🍗", "category": "ایرانی", "minutes": 90, "unit_price": 198000, "ingredients": [{"name":"مرغ", "amount":230, "unit":"گرم"},{"name":"برنج ایرانی", "amount":120, "unit":"گرم"},{"name":"زرشک", "amount":25, "unit":"گرم"},{"name":"زعفران", "amount":0.2, "unit":"گرم"},{"name":"پیاز", "amount":1, "unit":"عدد"}]},
    {"id": "pasta", "name": "پاستا آلفردو", "subtitle": "خامه، قارچ، مرغ و پاستا", "emoji": "🍝", "category": "فرنگی", "minutes": 35, "unit_price": 215000, "ingredients": [{"name":"پاستا", "amount":120, "unit":"گرم"},{"name":"سینه مرغ", "amount":150, "unit":"گرم"},{"name":"قارچ", "amount":130, "unit":"گرم"},{"name":"خامه", "amount":80, "unit":"گرم"},{"name":"پنیر پارمزان", "amount":25, "unit":"گرم"}]},
    {"id": "kotlet", "name": "کتلت خانگی", "subtitle": "مواد تازه برای کتلت ترد و خوشمزه", "emoji": "🥔", "category": "سریع", "minutes": 45, "unit_price": 125000, "ingredients": [{"name":"گوشت چرخ کرده", "amount":130, "unit":"گرم"},{"name":"سیب زمینی", "amount":2, "unit":"عدد"},{"name":"تخم مرغ", "amount":1, "unit":"عدد"},{"name":"پیاز", "amount":1, "unit":"عدد"}]},
    {"id": "salad", "name": "سالاد سزار", "subtitle": "کاهو تازه، مرغ و سس مخصوص", "emoji": "🥗", "category": "سریع", "minutes": 25, "unit_price": 145000, "ingredients": [{"name":"کاهو", "amount":200, "unit":"گرم"},{"name":"سینه مرغ", "amount":130, "unit":"گرم"},{"name":"نان تست", "amount":2, "unit":"برش"},{"name":"پنیر پارمزان", "amount":30, "unit":"گرم"},{"name":"سس سزار", "amount":40, "unit":"گرم"}]}
]
BY_ID = {x["id"]: x for x in RECIPES}

def init_db():
    with sqlite3.connect(DB) as db:
        db.execute("""CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            customer_type TEXT NOT NULL,
            customer_name TEXT NOT NULL,
            phone TEXT NOT NULL,
            address TEXT NOT NULL,
            company_name TEXT,
            contact_name TEXT,
            notes TEXT,
            items_json TEXT NOT NULL,
            total_toman INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'new'
        )""")

def error_message(message):
    return {"error": message}

class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(BASE), **kwargs)

    def send_json(self, obj, status=200):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/healthz":
            return self.send_json({"status": "ok"})
        if path == "/api/recipes":
            return self.send_json({"recipes": RECIPES, "currency": "تومان", "pricing": "demo"})
        if path == "/api/orders":
            return self.send_json(error_message("دسترسی به سفارش ها عمومی نیست."), 403)
        if path.startswith("/api/"):
            return self.send_json(error_message("مسیر پیدا نشد."), 404)
        if path == "/":
            self.path = "/index.html"
        # Never serve application source, private data or dot-files.
        allow = {"/index.html", "/styles.css", "/app.js", "/favicon.svg"}
        if urlparse(self.path).path not in allow:
            self.send_error(404)
            return
        return super().do_GET()

    def do_POST(self):
        if urlparse(self.path).path != "/api/orders":
            return self.send_json(error_message("مسیر پیدا نشد."), 404)
        try:
            size = int(self.headers.get("Content-Length", "0"))
            if not 0 < size <= MAX_BYTES:
                return self.send_json(error_message("اندازه درخواست نامعتبر است."), 413)
            payload = json.loads(self.rfile.read(size))
            if not isinstance(payload, dict):
                raise ValueError("اطلاعات سفارش نامعتبر است.")
            kind = payload.get("customer_type")
            if kind not in ("home", "business"):
                raise ValueError("نوع مشتری نامعتبر است.")
            name = str(payload.get("customer_name", "")).strip()
            phone = str(payload.get("phone", "")).strip()
            address = str(payload.get("address", "")).strip()
            company = str(payload.get("company_name", "")).strip()
            contact = str(payload.get("contact_name", "")).strip()
            notes = str(payload.get("notes", "")).strip()
            if not 2 <= len(name) <= 120 or not 8 <= len(address) <= 500:
                raise ValueError("نام و آدرس معتبر وارد کنید.")
            if not re.fullmatch(r"\+?[0-9۰-۹٠-٩\s\-]{10,20}", phone):
                raise ValueError("شماره تماس معتبر وارد کنید.")
            if kind == "business" and (len(company) < 2 or len(contact) < 2):
                raise ValueError("نام شرکت و نام رابط را وارد کنید.")
            if len(notes) > 800:
                raise ValueError("توضیحات بیش از حد طولانی است.")
            raw = payload.get("items")
            if not isinstance(raw, list) or not 1 <= len(raw) <= 20:
                raise ValueError("سبد خرید خالی یا نامعتبر است.")
            items, total, seen = [], 0, set()
            for item in raw:
                if not isinstance(item, dict):
                    raise ValueError("آیتم سفارش نامعتبر است.")
                rid, count = item.get("id"), item.get("servings")
                if rid not in BY_ID or type(count) is not int or not 1 <= count <= 100 or rid in seen:
                    raise ValueError("تعداد نفرات یا غذای انتخاب شده نامعتبر است.")
                seen.add(rid)
                recipe = BY_ID[rid]
                subtotal = recipe["unit_price"] * count
                total += subtotal
                items.append({"id": rid, "name": recipe["name"], "servings": count, "unit_price": recipe["unit_price"], "subtotal": subtotal})
            with LOCK, sqlite3.connect(DB, timeout=10) as db:
                cur = db.execute("""INSERT INTO orders
                  (created_at,customer_type,customer_name,phone,address,company_name,contact_name,notes,items_json,total_toman)
                  VALUES (?,?,?,?,?,?,?,?,?,?)""",
                  (datetime.now(timezone.utc).isoformat(),kind,name,phone,address,company,contact,notes,json.dumps(items,ensure_ascii=False),total))
                oid = cur.lastrowid
            self.send_json({"order_id": oid, "total_toman": total, "status": "received", "message": "درخواست سفارش ثبت شد. برای تایید قیمت و زمان تحویل با شما تماس می گیریم."}, 201)
        except (ValueError, TypeError, json.JSONDecodeError) as exc:
            self.send_json(error_message(str(exc)), 400)
        except Exception:
            self.log_error("Unexpected failure while saving order")
            self.send_json(error_message("خطا در ثبت سفارش. دوباره تلاش کنید."), 500)

if __name__ == "__main__":
    init_db()
    ThreadingHTTPServer(("0.0.0.0", 8080), Handler).serve_forever()
