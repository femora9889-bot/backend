"""
بيانات تجريبية للتطوير — مأخوذة من واجهات Femora
شغّلي: docker compose exec app python seed.py
"""
import asyncio
import uuid

from sqlalchemy import text

from app.core.database import AsyncSessionLocal
from app.core.security import hash_password
from app.models.product import Product, ProductImage, ProductVariant, SizeGuide
from app.models.store import Category, Store, StoreCategory
from app.models.user import User, UserRole
from app.models.address import Address
from app.models.cart import Cart, CartItem
from app.models.order import Order, OrderItem, OrderStatus, OrderStore
from app.models.wishlist import StoreWishlist, Wishlist


def uid() -> str:
    return str(uuid.uuid4())


async def seed():
    async with AsyncSessionLocal() as db:

        # تنظيف البيانات القديمة
        await db.execute(text("TRUNCATE TABLE categories, users RESTART IDENTITY CASCADE"))
        await db.commit()

        # ── Categories (integer IDs — autoincrement) ───────────────
        categories = [
            Category(name="Clothing",    name_ar="ملابس"),
            Category(name="Accessories", name_ar="إكسسوارات"),
            Category(name="Makeup",      name_ar="مكياج"),
            Category(name="Shoes",       name_ar="أحذية"),
        ]
        for c in categories:
            db.add(c)
        await db.flush()

        # cat IDs: 1=ملابس  2=إكسسوارات  3=مكياج  4=أحذية

        # ── Merchant users (UUID) ──────────────────────────────────
        m1_id = uid(); m2_id = uid(); m3_id = uid(); m4_id = uid()
        merchants = [
            User(id=m1_id, name="بوتيك الأميرة", phone="+963991111111", password_hash=hash_password("merchant123"), role=UserRole.merchant),
            User(id=m2_id, name="دار الجمال",     phone="+963992222222", password_hash=hash_password("merchant123"), role=UserRole.merchant),
            User(id=m3_id, name="أناقة دمشق",     phone="+963993333333", password_hash=hash_password("merchant123"), role=UserRole.merchant),
            User(id=m4_id, name="لمسة أنثى",      phone="+963994444444", password_hash=hash_password("merchant123"), role=UserRole.merchant),
        ]
        for m in merchants:
            db.add(m)
        await db.flush()

        # ── Stores (UUID) ─────────────────────────────────────────
        s1_id = uid(); s2_id = uid(); s3_id = uid(); s4_id = uid()
        stores = [
            Store(id=s1_id, owner_id=m1_id, name="بوتيك الأميرة",
                  description="أجمل فساتين السهرات والمناسبات في دمشق",
                  city="دمشق", address="المالكي، شارع الجلاء",
                  phone="+963991111111", is_verified=True, is_active=True),
            Store(id=s2_id, owner_id=m2_id, name="دار الجمال",
                  description="عطور وعناية ومكياج من أفخم الماركات",
                  city="دمشق", address="أبو رمانة",
                  phone="+963992222222", is_verified=True, is_active=True),
            Store(id=s3_id, owner_id=m3_id, name="أناقة دمشق",
                  description="حقائب ومجوهرات بتضيف لمسة أناقة لإطلالتك",
                  city="دمشق", address="الشعلان",
                  phone="+963993333333", is_verified=False, is_active=True),
            Store(id=s4_id, owner_id=m4_id, name="لمسة أنثى",
                  description="بلوزات وتنانير وكاجوال راقي للمرأة العصرية",
                  city="دمشق", address="المزة، فيلات شرقية",
                  phone="+963994444444", is_verified=True, is_active=True),
        ]
        for s in stores:
            db.add(s)

        store_cats = [
            StoreCategory(store_id=s1_id, category_id=1),
            StoreCategory(store_id=s2_id, category_id=3),
            StoreCategory(store_id=s3_id, category_id=2),
            StoreCategory(store_id=s4_id, category_id=1),
        ]
        for sc in store_cats:
            db.add(sc)
        await db.flush()

        # ── Products (UUID) ────────────────────────────────────────
        product_ids = []
        products_data = [
            {
                "store_id": s1_id, "category_id": 1, "product_type": "فستان", "fabric": "مخمل",
                "name": "فستان سهرة مخمل",
                "description": "فستان سهرة طويل من المخمل الناعم، قصته بتبين الخصر وبتنزل واسعة بشكل أنيق.",
                "base_price": 7500, "original_price": 9500,
                "image": "https://images.unsplash.com/photo-1566174053879-31528523f8ae?w=500",
                "variants": [
                    {"color": "بنفسجي", "color_hex": "#7B2D8B", "size": "S",  "stock": 3},
                    {"color": "بنفسجي", "color_hex": "#7B2D8B", "size": "M",  "stock": 5},
                    {"color": "بنفسجي", "color_hex": "#7B2D8B", "size": "L",  "stock": 2},
                    {"color": "بنفسجي", "color_hex": "#7B2D8B", "size": "XL", "stock": 1},
                    {"color": "أسود",   "color_hex": "#000000", "size": "S",  "stock": 4},
                    {"color": "أسود",   "color_hex": "#000000", "size": "M",  "stock": 6},
                    {"color": "خمري",   "color_hex": "#722F37", "size": "M",  "stock": 3},
                    {"color": "خمري",   "color_hex": "#722F37", "size": "L",  "stock": 2},
                ],
                "size_guide": {
                    "XS": {"bust": 80,  "waist": 62, "hips": 86,  "length": 140},
                    "S":  {"bust": 84,  "waist": 66, "hips": 90,  "length": 142},
                    "M":  {"bust": 88,  "waist": 70, "hips": 94,  "length": 144},
                    "L":  {"bust": 92,  "waist": 74, "hips": 98,  "length": 146},
                    "XL": {"bust": 96,  "waist": 78, "hips": 102, "length": 148},
                },
            },
            {
                "store_id": s3_id, "category_id": 2, "product_type": "حقيبة", "fabric": "جلد طبيعي",
                "name": "حقيبة يد جلد طبيعي",
                "description": "حقيبة يد من الجلد الطبيعي بحجم عملي، خياطة متينة وتفاصيل أنيقة.",
                "base_price": 4800, "original_price": None,
                "image": "https://images.unsplash.com/photo-1584917865442-de89df76afd3?w=500",
                "variants": [
                    {"color": "بيج",  "color_hex": "#F5F5DC", "size": "one-size", "stock": 10},
                    {"color": "أسود", "color_hex": "#000000", "size": "one-size", "stock": 7},
                ],
                "size_guide": {},
            },
            {
                "store_id": s2_id, "category_id": 3, "product_type": "مكياج", "fabric": None,
                "name": "باليت ظلال العيون",
                "description": "باليت ظلال عيون بدرجات دافئة، تركيبة ناعمة بتمدد بسهولة وبتثبت طويل.",
                "base_price": 2200, "original_price": 2900,
                "image": "https://images.unsplash.com/photo-1512496015851-a90fb38ba796?w=500",
                "variants": [
                    {"color": "درجات دافئة", "color_hex": "#C4813A", "size": "one-size", "stock": 15},
                ],
                "size_guide": {},
            },
            {
                "store_id": s4_id, "category_id": 1, "product_type": "بلوزة", "fabric": "حرير",
                "name": "بلوزة حرير ناعمة",
                "description": "بلوزة من الحرير الناعم بقصة واسعة شوي ومريحة، لمسة أنيقة لإطلالتك اليومية.",
                "base_price": 2900, "original_price": None,
                "image": "https://images.unsplash.com/photo-1551163943-3f6a855d1153?w=500",
                "variants": [
                    {"color": "وردي",   "color_hex": "#FFB6C1", "size": "S", "stock": 8},
                    {"color": "وردي",   "color_hex": "#FFB6C1", "size": "M", "stock": 6},
                    {"color": "أبيض",   "color_hex": "#FFFFFF", "size": "M", "stock": 5},
                    {"color": "أبيض",   "color_hex": "#FFFFFF", "size": "L", "stock": 3},
                    {"color": "لافندر", "color_hex": "#E6E6FA", "size": "S", "stock": 4},
                    {"color": "لافندر", "color_hex": "#E6E6FA", "size": "M", "stock": 4},
                ],
                "size_guide": {
                    "S": {"bust": 84, "waist": 66, "hips": 90, "length": 60},
                    "M": {"bust": 88, "waist": 70, "hips": 94, "length": 62},
                    "L": {"bust": 92, "waist": 74, "hips": 98, "length": 64},
                },
            },
            {
                "store_id": s3_id, "category_id": 2, "product_type": "مجوهرات", "fabric": None,
                "name": "عقد لؤلؤ كلاسيك",
                "description": "عقد لؤلؤ كلاسيكي بيضيف لمسة رقيقة وأنيقة لأي إطلالة.",
                "base_price": 1750, "original_price": 2300,
                "image": "https://images.unsplash.com/photo-1599643478518-a784e5dc4c8f?w=500",
                "variants": [
                    {"color": "أبيض لؤلؤي", "color_hex": "#F8F8FF", "size": "one-size", "stock": 2},
                ],
                "size_guide": {},
            },
            {
                "store_id": s2_id, "category_id": 3, "product_type": "عطر", "fabric": None,
                "name": "عطر زهري فاخر",
                "description": "عطر زهري أنثوي فخم بنفحات ورد ولمسة دافئة، ثباته طويل.",
                "base_price": 4100, "original_price": None,
                "image": "https://images.unsplash.com/photo-1541643600914-78b084683702?w=500",
                "variants": [
                    {"color": "90 مل", "color_hex": "#FFD700", "size": "one-size", "stock": 20},
                ],
                "size_guide": {},
            },
        ]

        first_variant_ids = []
        for p_data in products_data:
            p_id = uid()
            product_ids.append(p_id)
            product = Product(
                id=p_id,
                store_id=p_data["store_id"],
                category_id=p_data.get("category_id"),
                name=p_data["name"],
                description=p_data["description"],
                base_price=p_data["base_price"],
                fabric=p_data.get("fabric"),
                product_type=p_data.get("product_type"),
                is_available=True,
            )
            db.add(product)

            db.add(ProductImage(
                id=uid(),
                product_id=p_id,
                url=p_data["image"],
                is_primary=True,
                display_order=0,
            ))

            for i, v in enumerate(p_data["variants"]):
                v_id = uid()
                if i == 0:
                    first_variant_ids.append(v_id)
                db.add(ProductVariant(
                    id=v_id,
                    product_id=p_id,
                    color=v["color"],
                    color_hex=v["color_hex"],
                    size=v["size"],
                    stock_quantity=v["stock"],
                    original_price=p_data.get("original_price"),
                    is_available=True,
                ))

            for size_label, dims in p_data["size_guide"].items():
                db.add(SizeGuide(
                    id=uid(),
                    product_id=p_id,
                    size_label=size_label,
                    bust_cm=dims.get("bust"),
                    waist_cm=dims.get("waist"),
                    hips_cm=dims.get("hips"),
                    length_cm=dims.get("length"),
                ))

        # ── Customer ───────────────────────────────────────────────
        customer_id = uid()
        customer = User(
            id=customer_id,
            name="أمل",
            phone="+963999999999",
            password_hash=hash_password("customer123"),
            role=UserRole.customer,
        )
        db.add(customer)
        await db.flush()

        # ── Cart ──────────────────────────────────────────────────
        cart_id = uid()
        db.add(Cart(id=cart_id, user_id=customer_id))
        # فستان سهرة (variant بنفسجي M) + بلوزة حرير (variant وردي S)
        db.add(CartItem(id=uid(), cart_id=cart_id, product_variant_id=first_variant_ids[0], quantity=1))
        db.add(CartItem(id=uid(), cart_id=cart_id, product_variant_id=first_variant_ids[3], quantity=2))

        # ── Address ───────────────────────────────────────────────
        addr_id = uid()
        db.add(Address(
            id=addr_id, user_id=customer_id,
            label="البيت", city="دمشق", area="المالكي",
            street="شارع الجلاء", building="بناء 5",
            is_default=True,
        ))
        await db.flush()

        # ── Orders ────────────────────────────────────────────────
        # طلب 1: فستان سهرة — مسلّم (delivered)
        o1_id = uid(); os1_id = uid()
        db.add(Order(id=o1_id, user_id=customer_id, address_id=addr_id, total_amount=7500))
        db.add(OrderStore(id=os1_id, order_id=o1_id, store_id=s1_id,
                          status=OrderStatus.delivered, subtotal=7500, delivery_fee=0))
        db.add(OrderItem(id=uid(), order_store_id=os1_id,
                         product_variant_id=first_variant_ids[0],
                         product_name="فستان سهرة مخمل", color="بنفسجي", size="S",
                         unit_price=7500, quantity=1))

        # طلب 2: بلوزة + باليت — قيد التجهيز (preparing)
        o2_id = uid(); os2_id = uid(); os3_id = uid()
        db.add(Order(id=o2_id, user_id=customer_id, address_id=addr_id, total_amount=5100))
        db.add(OrderStore(id=os2_id, order_id=o2_id, store_id=s4_id,
                          status=OrderStatus.preparing, subtotal=2900, delivery_fee=0))
        db.add(OrderItem(id=uid(), order_store_id=os2_id,
                         product_variant_id=first_variant_ids[3],
                         product_name="بلوزة حرير ناعمة", color="وردي", size="S",
                         unit_price=2900, quantity=1))
        db.add(OrderStore(id=os3_id, order_id=o2_id, store_id=s2_id,
                          status=OrderStatus.preparing, subtotal=2200, delivery_fee=0))
        db.add(OrderItem(id=uid(), order_store_id=os3_id,
                         product_variant_id=first_variant_ids[2],
                         product_name="باليت ظلال العيون", color="درجات دافئة", size="one-size",
                         unit_price=2200, quantity=1))

        # ── Wishlist — منتجات ──────────────────────────────────────
        # فستان سهرة + بلوزة حرير + باليت ظلال
        for pid in product_ids[:3]:
            db.add(Wishlist(id=uid(), user_id=customer_id, product_id=pid))

        # ── Wishlist — متاجر ───────────────────────────────────────
        # بوتيك الأميرة + لمسة أنثى
        db.add(StoreWishlist(user_id=customer_id, store_id=s1_id))
        db.add(StoreWishlist(user_id=customer_id, store_id=s4_id))

        await db.commit()
        print("✓ Seed data created successfully")
        print("\nTest accounts:")
        print("  Customer : +963999999999 / customer123")
        print("  Merchant1: +963991111111 / merchant123  (بوتيك الأميرة)")
        print("  Merchant2: +963992222222 / merchant123  (دار الجمال)")
        print("  Merchant3: +963993333333 / merchant123  (أناقة دمشق)")
        print("  Merchant4: +963994444444 / merchant123  (لمسة أنثى)")


if __name__ == "__main__":
    asyncio.run(seed())
