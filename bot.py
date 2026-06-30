import os
import json
import logging
from datetime import datetime
import telebot
from telebot import types
from database import *
from utils import *

broadcast_states = {}

from config import *

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")
# Cấu hình log để tiện theo dõi lỗi
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


# Tên file cơ sở dữ liệu
DB_FILE = "db.json"

# Cấu trúc CSDL mặc định
DEFAULT_DB = {
    "users": {},
    "keys": {
        "fluorite_1d": [],
        "fluorite_7d": [],
        "fluorite_31d": [],
        "migui_lite_7d": [],
        "migui_lite_30d": [],
        "migul_pro_1h": [],
        "migul_pro_1d": [],
        "migui_pro_7d": [],
        "migui_pro_31d": [],
        "drip_30d": [],
        "drip_lifetime": [],
        "esign_1y": [],
        "8bp_7d": [],
        "8bp_30d": [],
        "proxy_7d": [],
        "proxy_31d": [],
        "tipa_sudo_30d": [],
        "tipa_iosviet_30d": [],
        "acc_clone_lv5": [],
        "acc_clone_lv8": [],
        "acc_clone_lv15": [],
        "acc_clone_lv30": []
    },
    "stats": {
        "total_revenue": 0,
        "keys_sold": 0
    }
}

# Danh mục sản phẩm (Cấu trúc dữ liệu tĩnh để dựng giao diện)
PRODUCTS = {
    "fluorite": {
        "name": "Fluorite",
        "items": {
            "fluorite_1d": {"name": "Fluorite 1 Ngày", "price": 65000},
            "fluorite_7d": {"name": "Fluorite 7 Ngày", "price": 160000},
            "fluorite_31d": {"name": "Fluorite 31 ngày", "price": 280000}
        }
    },
    "migul_lite": {
        "name": "Migul Lite",
        "items": {
            "migui_lite_7d": {"name": "Migui Lite 7 Ngày", "price": 150000},
            "migui_lite_30d": {"name": "Migui Lite 30 Ngày", "price": 350000}
        }
    },
    "migui_pro": {
        "name": "Migui Pro",
        "items": {
            "migul_pro_1h": {"name": "Migul Pro 1 Giờ", "price": 10000},
            "migul_pro_1d": {"name": "Migul Pro 1 Ngày", "price": 100000},
            "migui_pro_7d": {"name": "Migui Pro 7 Ngày", "price": 215000},
            "migui_pro_31d": {"name": "Migui Pro 31 Ngày", "price": 450000}
        }
    },
    "drip_client": {
        "name": "Drip Client ( Android",
        "items": {
            "drip_30d": {"name": "Drip Client 30 Ngày", "price": 150000},
            "drip_lifetime": {"name": "Drip Client Vĩnh Viễn", "price": 600000}
        }
    },
    "esign": {
        "name": "Chứng Chỉ Esign",
        "items": {
            "esign_1y": {"name": "Esign 1 Năm (Không thu hồi)", "price": 150000}
        }
    },
    "8bp_fluorite": {
        "name": "8BP_Fluorite",
        "items": {
            "8bp_7d": {"name": "8BP Fluorite 7 Ngày", "price": 180000},
            "8bp_30d": {"name": "8BP Fluorite 30 Ngày", "price": 380000}
        }
    },
    "proxy_android": {
        "name": "Proxy Androi",
        "items": {
            "proxy_7d": {"name": "7 Ngày", "price": 80000},
            "proxy_31d": {"name": "31 Ngày", "price": 170000}
        }
    },

    "tipa_ff_sudo": {
        "name": "Tipa FF Sudo",
        "items": {
            "tipa_sudo_30d": {"name": "Tipa FF Sudo 30 Ngày", "price": 200000}
        }
    },
    "tipa_ff_iosviet": {
        "name": "Tipa FF Iosviet",
        "items": {
            "tipa_iosviet_30d": {"name": "Tipa FF Iosviet 30 Ngày", "price": 150000}
        }
    },
    "acc_clone": {
        "name": "🧬 Acc Clone",
        "items": {
            "acc_clone_lv5":  {"name": "ACC LV5",  "price": 3000},
            "acc_clone_lv8":  {"name": "ACC LV8",  "price": 7000},
            "acc_clone_lv15": {"name": "ACC LV15", "price": 20000},
            "acc_clone_lv30": {"name": "ACC LV30", "price": 40000}
        }
    }
}

# --- CÁC HÀM XỬ LÝ CSDL JSON ---

def load_db():
    if not os.path.exists(DB_FILE):
        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump(DEFAULT_DB, f, indent=4, ensure_ascii=False)
        return DEFAULT_DB
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            db = json.load(f)
            # Đồng bộ khóa nếu db cũ thiếu các mục mới
            if "keys" not in db:
                db["keys"] = DEFAULT_DB["keys"]
            else:
                # Đồng bộ thêm các khóa sản phẩm mới nếu db cũ chưa có
                for pk, pkeys in DEFAULT_DB["keys"].items():
                    if pk not in db["keys"]:
                        db["keys"][pk] = pkeys
            if "users" not in db:
                db["users"] = {}
            if "stats" not in db:
                db["stats"] = DEFAULT_DB["stats"]
            return db
    except Exception as e:
        logger.error(f"Lỗi khi đọc file db.json: {e}")
        return DEFAULT_DB

def save_db(db):
    try:
        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump(db, f, indent=4, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Lỗi khi ghi file db.json: {e}")

def get_or_create_user(db, user_id, username, first_name, last_name):
    u_id = str(user_id)
    if u_id not in db["users"]:
        db["users"][u_id] = {
            "balance": 0,
            "username": username or "Không có",
            "full_name": f"{first_name or ''} {last_name or ''}".strip() or f"User_{user_id}",
            "join_date": datetime.now().strftime("%d/%m/%Y"),
            "history": []
        }
        save_db(db)
    else:
        # Cập nhật username và tên mới nếu có thay đổi
        db["users"][u_id]["username"] = username or "Không có"
        db["users"][u_id]["full_name"] = f"{first_name or ''} {last_name or ''}".strip() or f"User_{user_id}"
    return db["users"][u_id]

# --- HÀM KIỂM TRA QUYỀN ADMIN ---
def is_admin(user_id):
    return user_id in ADMIN_IDS

# Quản lý trạng thái Admin khi nạp key / cộng tiền
# admin_states[admin_id] = {"action": "awaiting_keys", "product_id": "..."}
admin_states = {}
user_states = {}

# Tiện ích định dạng tiền VND
def format_money(amount):
    return f"{amount:,.0f}đ"

# --- XÂY DỰNG KEYBOARDS ---

# Menu chính (Reply Keyboard)
def get_main_menu_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.row(types.KeyboardButton("🛍️ Mua Key/Acc"), types.KeyboardButton("🧬 Mua Acc Clone"))
    markup.row(types.KeyboardButton("💳 Nạp Tiền"), types.KeyboardButton("💎 Cá Nhân"))
    markup.row(types.KeyboardButton("🏆 Top Nạp"), types.KeyboardButton("📄 Lịch Sử Nạp"))
    markup.row(types.KeyboardButton("📁 FILE"))
    markup.row(types.KeyboardButton("🤵 Hỗ Trợ"))
    return markup

# Menu danh mục sản phẩm (Inline Keyboard)
def get_categories_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=2)
    buttons = []
    for cat_id, cat_data in PRODUCTS.items():
        buttons.append(types.InlineKeyboardButton(f"🛍️ {cat_data['name']}", callback_data=f"cat_{cat_id}"))
    
    for i in range(0, len(buttons), 2):
        if i + 1 < len(buttons):
            markup.row(buttons[i], buttons[i+1])
        else:
            markup.row(buttons[i])
    return markup

# Menu sản phẩm thuộc danh mục (Inline Keyboard)
def get_products_keyboard(category_id):
    db = load_db()
    markup = types.InlineKeyboardMarkup(row_width=1)
    category = PRODUCTS.get(category_id)
    if category:
        for prod_id, prod_data in category["items"].items():
            # Lấy tồn kho thực tế từ database
            stock = len(db["keys"].get(prod_id, []))
            btn_text = f"💠 {prod_data['name']} - {format_money(prod_data['price'])} (Kho: {stock})"
            markup.row(types.InlineKeyboardButton(btn_text, callback_data=f"prod_{category_id}_{prod_id}"))
    
    markup.row(types.InlineKeyboardButton("🔙 Quay Lại", callback_data="back_to_categories"))
    return markup

# Menu chọn số lượng mua (Inline Keyboard)
def get_purchase_keyboard(category_id, product_id):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.row(
        types.InlineKeyboardButton("🛒 Mua 1", callback_data=f"buy_{category_id}_{product_id}_1"),
        types.InlineKeyboardButton("🛒 Mua 5", callback_data=f"buy_{category_id}_{product_id}_5")
    )
    markup.row(
        types.InlineKeyboardButton("🛒 Mua 10", callback_data=f"buy_{category_id}_{product_id}_10"),
        types.InlineKeyboardButton("🛒 Mua 50", callback_data=f"buy_{category_id}_{product_id}_50")
    )
    markup.row(types.InlineKeyboardButton("🔙 Quay Lại Danh Mục", callback_data=f"cat_{category_id}"))
    return markup

# Menu quản lý Admin (Reply Keyboard nổi - chỉ hiện với admin)
def get_admin_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.row(
        types.KeyboardButton("➕ Nạp Key"),
        types.KeyboardButton("💸 Cộng Tiền")
    )
    markup.row(
        types.KeyboardButton("📊 Danh Sách Kho"),
        types.KeyboardButton("📢 Gửi Thông Báo")
    )
    markup.row(
        types.KeyboardButton("❌ Thoát Admin")
    )
    return markup

# Keyboard xác nhận broadcast (Inline)
def get_broadcast_confirm_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.row(
        types.InlineKeyboardButton("✅ Xác Nhận Gửi", callback_data="admin_broadcast_confirm"),
        types.InlineKeyboardButton("❌ Huỷ", callback_data="admin_broadcast_cancel")
    )
    return markup

# Menu nạp tiền (Inline Keyboard)
def get_deposit_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.row(types.InlineKeyboardButton("📥 Gửi bill nạp tiền", callback_data="user_send_bill_start"))
    markup.row(types.InlineKeyboardButton("👛 Xem ví", callback_data="user_view_wallet"))
    markup.row(types.InlineKeyboardButton("🔙 Quay lại", callback_data="user_close_deposit_menu"))
    return markup

# Nút hủy gửi bill (Inline Keyboard)
def get_bill_cancel_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.row(types.InlineKeyboardButton("❌ Huỷ", callback_data="cancel_bill_upload"))
    return markup

# Nút quay lại từ ví (Inline Keyboard)
def get_wallet_back_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.row(types.InlineKeyboardButton("🔙 Quay lại", callback_data="user_back_to_deposit_menu"))
    return markup

# Keyboard danh sách Acc Clone (Inline Keyboard)
def get_acc_clone_keyboard():
    db = load_db()
    markup = types.InlineKeyboardMarkup(row_width=1)
    acc_items = PRODUCTS["acc_clone"]["items"]
    for prod_id, prod_data in acc_items.items():
        stock = len(db["keys"].get(prod_id, []))
        btn_text = f"🧬 {prod_data['name']} — {format_money(prod_data['price'])}/1 acc  |  Kho: {stock}"
        markup.row(types.InlineKeyboardButton(btn_text, callback_data=f"acc_buy_{prod_id}"))
    markup.row(types.InlineKeyboardButton("🔙 Quay Lại Menu", callback_data="acc_back_main"))
    return markup

# Keyboard chọn số lượng Acc Clone
def get_acc_qty_keyboard(prod_id):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.row(
        types.InlineKeyboardButton("🛒 Mua 1", callback_data=f"acc_confirm_{prod_id}_1"),
        types.InlineKeyboardButton("🛒 Mua 5", callback_data=f"acc_confirm_{prod_id}_5")
    )
    markup.row(
        types.InlineKeyboardButton("🛒 Mua 10", callback_data=f"acc_confirm_{prod_id}_10"),
        types.InlineKeyboardButton("🛒 Mua 20", callback_data=f"acc_confirm_{prod_id}_20")
    )
    markup.row(types.InlineKeyboardButton("🔙 Quay Lại", callback_data="acc_back_list"))
    return markup

# Keyboard menu FILE (IMZ / FILZA)
def get_file_menu_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.row(
        types.InlineKeyboardButton("📱 IMZ", callback_data="file_imz"),
        types.InlineKeyboardButton("📂 FILZA", callback_data="file_filza")
    )
    return markup

# Keyboard quay lại menu FILE
def get_file_back_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.row(types.InlineKeyboardButton("🔙 Quay Lại", callback_data="file_back"))
    return markup

# --- ĐĂNG KÝ XỬ LÝ LỆNH & TIN NHẮN CHỮ ---

# Lệnh /cancel để hủy thao tác đang dở dang
@bot.message_handler(commands=['cancel'])
def cancel_current_action(message):
    if message.from_user.id in admin_states:
        del admin_states[message.from_user.id]
        bot.send_message(message.chat.id, "❌ Đã hủy thao tác admin hiện tại.", reply_markup=get_main_menu_keyboard())
    elif message.from_user.id in user_states:
        del user_states[message.from_user.id]
        bot.send_message(message.chat.id, "❌ Đã hủy thao tác nạp tiền.", reply_markup=get_main_menu_keyboard())
    else:
        bot.send_message(message.chat.id, "Không có thao tác nào đang được thực hiện.")

# Lệnh /admin dành cho quản trị viên
@bot.message_handler(commands=['admin'])
def show_admin_panel(message):
    if not is_admin(message.from_user.id):
        bot.send_message(message.chat.id, "❌ Bạn không có quyền truy cập lệnh này!")
        return
    
    db = load_db()
    total_users = len(db.get("users", {}))
    total_revenue = db.get("stats", {}).get("total_revenue", 0)
    keys_sold = db.get("stats", {}).get("keys_sold", 0)
    
    admin_text = (
        "🛠️ <b>BẢNG ĐIỀU KHIỂN QUẢN TRỊ</b>\n"
        "______________________\n\n"
        "📊 <b>Thống kê hệ thống:</b>\n"
        f"• Tổng số thành viên: <b>{total_users}</b>\n"
        f"• Tổng doanh thu: <b>{format_money(total_revenue)}</b>\n"
        f"• Tổng số key đã bán: <b>{keys_sold} chiếc</b>\n\n"
        "👇 Chọn chức năng quản trị từ bàn phím bên dưới:"
    )
    bot.send_message(message.chat.id, admin_text, reply_markup=get_admin_keyboard())

# Lệnh /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    db = load_db()
    get_or_create_user(db, message.from_user.id, message.from_user.username, message.from_user.first_name, message.from_user.last_name)
    
    user_display = message.from_user.username or message.from_user.first_name or "bạn"
    welcome_text = (
        "🌟 <b>HỆ THỐNG DỊCH VỤ TỰ ĐỘNG</b>\n"
        "______________________\n\n"
        f"👋 Chào mừng <b>{user_display}</b> đã đến với Bot. Hệ thống của chúng tôi luôn trực 24/7!\n\n"
        "🚀 Vui lòng sử dụng Menu Bàn Phím bên dưới để chọn các tính năng."
    )
    bot.send_message(message.chat.id, welcome_text, reply_markup=get_main_menu_keyboard())

# Xử lý khi nhấn "🛍️ Mua Key/Acc" từ menu bàn phím
@bot.message_handler(func=lambda message: message.text == "🛍️ Mua Key/Acc")
def show_categories(message):
    db = load_db()
    get_or_create_user(db, message.from_user.id, message.from_user.username, message.from_user.first_name, message.from_user.last_name)
    
    text = (
        "🛍️ <b>DANH SÁCH SẢN PHẨM</b>\n\n"
        "Chào mừng bạn đến với cửa hàng! Vui lòng chọn danh mục bạn muốn xem:"
    )
    bot.send_message(message.chat.id, text, reply_markup=get_categories_keyboard())

# Xử lý khi nhấn "🧬 Mua Acc Clone" từ menu bàn phím
@bot.message_handler(func=lambda message: message.text == "🧬 Mua Acc Clone")
def show_acc_clone(message):
    db = load_db()
    get_or_create_user(db, message.from_user.id, message.from_user.username, message.from_user.first_name, message.from_user.last_name)

    text = (
        "🧬 <b>MUA ACC CLONE</b>\n"
        "______________________\n\n"
        "👇 Chọn loại acc bạn muốn mua bên dưới:\n\n"
        "💠 <b>ACCLV5</b>  —  3,000đ/1 acc\n"
        "💠 <b>ACCLV8</b>  —  7,000đ/1 acc\n"
        "💠 <b>ACCLV15</b>  —  20,000đ/1 acc\n"
        "💠 <b>ACCLV30</b>  —  40,000đ/1 acc\n\n"
        "✅ Acc được giao tự động sau khi thanh toán!"
    )
    bot.send_message(message.chat.id, text, reply_markup=get_acc_clone_keyboard())

# Xử lý khi nhấn "💳 Nạp Tiền"
@bot.message_handler(func=lambda message: message.text == "💳 Nạp Tiền")
def show_payment_info(message):
    db = load_db()
    user_data = get_or_create_user(db, message.from_user.id, message.from_user.username, message.from_user.first_name, message.from_user.last_name)
    
    telegram_id = message.from_user.id
    qr_code_url = "https://i.postimg.cc/Bv3HQk9K/6273529661664989075.jpg"
    
    caption = (
        "💳 <b>THÔNG TIN NẠP TIỀN</b>\n"
        "______________________\n\n"
        f"💰 <b>Số dư hiện tại:</b> {format_money(user_data['balance'])}\n\n"
        "Vui lòng quét mã QR bên trên và chuyển khoản đúng nội dung:\n\n"
        f"📥 <b>Nội dung chuyển khoản:</b> <code>{telegram_id}</code>\n\n"
        "📸 Sau khi chuyển khoản, nhấn <b>\"Gửi Bill Nạp Tiền\"</b> và gửi ảnh bill cho Admin duyệt.\n\n"
        "⚠️ <i>Lưu ý: Ghi sai nội dung sẽ không được cộng tiền. Admin sẽ duyệt bill trong vòng 5-15 phút.</i>"
    )
    bot.send_photo(message.chat.id, photo=qr_code_url, caption=caption, reply_markup=get_deposit_keyboard())

# Xử lý khi nhấn "💎 Cá Nhân"
@bot.message_handler(func=lambda message: message.text == "💎 Cá Nhân")
def show_personal_info(message):
    db = load_db()
    user_id_str = str(message.from_user.id)
    user_data = get_or_create_user(db, message.from_user.id, message.from_user.username, message.from_user.first_name, message.from_user.last_name)
    
    personal_text = (
        "💎 <b>THÔNG TIN CÁ NHÂN</b>\n"
        "______________________\n\n"
        f"👤 Họ và tên: <b>{user_data['full_name']}</b>\n"
        f"🆔 ID Telegram: <code>{user_id_str}</code>\n"
        f"🏷️ Username: @{user_data['username']}\n"
        f"💰 Số dư tài khoản: <b>{format_money(user_data['balance'])}</b>\n"
        f"📅 Ngày tham gia: {user_data['join_date']}\n\n"
        "💡 <i>Mẹo: Hãy nhắn tin cho Admin hoặc nạp tiền để thực hiện giao dịch mua key.</i>"
    )
    bot.send_message(message.chat.id, personal_text)

# Xử lý khi nhấn "🏆 Top Nạp"
@bot.message_handler(func=lambda message: message.text == "🏆 Top Nạp")
def show_top_deposits(message):
    db = load_db()
    get_or_create_user(db, message.from_user.id, message.from_user.username, message.from_user.first_name, message.from_user.last_name)
    
    top_text = (
        "🏆 <b>BẢNG XẾP HẠNG TOP NẠP TIỀN</b>\n"
        "______________________\n\n"
        "Chưa có ai lên bảng xếp hạng.\n\n"
        "✨ <i>Hãy là người đầu tiên nạp tiền và lên top!</i>"
    )
    bot.send_message(message.chat.id, top_text)

# Xử lý khi nhấn "📄 Lịch Sử Nạp" (Hiển thị cả lịch sử nạp và lịch sử mua key)
@bot.message_handler(func=lambda message: message.text == "📄 Lịch Sử Nạp")
def show_deposit_history(message):
    db = load_db()
    user_id_str = str(message.from_user.id)
    user_data = get_or_create_user(db, message.from_user.id, message.from_user.username, message.from_user.first_name, message.from_user.last_name)
    
    history_text = (
        "📄 <b>LỊCH SỬ NẠP TIỀN & MUA HÀNG</b>\n"
        "______________________\n\n"
    )
    
    if user_data["history"]:
        history_text += "🔑 <b>Lịch sử mua Key của bạn:</b>\n\n"
        for idx, item in enumerate(user_data["history"][-5:], 1): # Hiển thị tối đa 5 giao dịch gần nhất
            keys_str = "\n".join([f"   • <code>{k}</code>" for k in item["keys"]])
            history_text += (
                f"<b>{idx}. Giao dịch: {item['product_name']}</b>\n"
                f"   • Thời gian: {item['date']}\n"
                f"   • Số lượng: {item['qty']} chiếc | Tổng: {format_money(item['price'])}\n"
                f"   • Key đã nhận:\n{keys_str}\n\n"
            )
    else:
        history_text += "❌ Bạn chưa có lịch sử giao dịch mua key nào trên hệ thống.\n"
        
    bot.send_message(message.chat.id, history_text)

# Xử lý khi nhấn "🤵 Hỗ Trợ"
@bot.message_handler(func=lambda message: message.text == "🤵 Hỗ Trợ")
def show_support_info(message):
    db = load_db()
    get_or_create_user(db, message.from_user.id, message.from_user.username, message.from_user.first_name, message.from_user.last_name)
    
    support_text = (
        "🤵 <b>HỖ TRỢ KHÁCH HÀNG / CSKH</b>\n"
        "______________________\n\n"
        "💬 Nếu gặp lỗi sản phẩm, lỗi nạp tiền hoặc cần tư vấn dịch vụ, vui lòng liên hệ Admin qua kênh hỗ trợ dưới đây:\n\n"
        "✈ "
        "<b>Telegram Admin:</b> @qhoanios18\n"
        "📞 <b>Hotline:</b> <code>0909.xxx.xxx</code>\n"
        "⏰ <b>Thời gian trực:</b> 24/7 (Phản hồi sau vài phút)\n\n"
        "🔒 <i>Lưu ý: Admin không bao giờ chủ động nhắn tin trước yêu cầu gửi mã thẻ hoặc mật khẩu tài khoản!</i>"
    )
    bot.send_message(message.chat.id, support_text)

# Xử lý khi nhấn "📁 FILE" (Nút nổi FILE -> IMZ / FILZA)
@bot.message_handler(func=lambda message: message.text == "📁 FILE")
def show_file_menu(message):
    db = load_db()
    get_or_create_user(db, message.from_user.id, message.from_user.username, message.from_user.first_name, message.from_user.last_name)

    file_text = (
        "📁 <b>FILE</b>\n"
        "______________________\n\n"
        "👇 Vui lòng chọn loại file bạn muốn xem bảng giá:"
    )
    bot.send_message(message.chat.id, file_text, reply_markup=get_file_menu_keyboard())

# --- XỬ LÝ CÁC NÚT ADMIN NỔI (REPLY KEYBOARD) ---

@bot.message_handler(func=lambda m: is_admin(m.from_user.id) and m.text == "➕ Nạp Key")
def admin_btn_add_keys(message):
    markup = types.InlineKeyboardMarkup(row_width=2)
    buttons = []
    for cat_id, cat_data in PRODUCTS.items():
        buttons.append(types.InlineKeyboardButton(f"📁 {cat_data['name']}", callback_data=f"cat_admin_{cat_id}"))
    for i in range(0, len(buttons), 2):
        if i + 1 < len(buttons):
            markup.row(buttons[i], buttons[i+1])
        else:
            markup.row(buttons[i])
    bot.send_message(
        message.chat.id,
        "➕ <b>NẠP KEY - CHỌN DANH MỤC</b>\n\nChọn danh mục bạn muốn nạp thêm key:",
        reply_markup=markup
    )

@bot.message_handler(func=lambda m: is_admin(m.from_user.id) and m.text == "💸 Cộng Tiền")
def admin_btn_add_balance(message):
    admin_states[message.from_user.id] = {"action": "awaiting_user_id"}
    bot.send_message(
        message.chat.id,
        "💸 <b>CỘNG TIỀN - BƯỚC 1: NHẬP ID NGƯỜI DÙNG</b>\n"
        "______________________\n\n"
        "Vui lòng nhập <b>ID Telegram</b> của thành viên bạn muốn điều chỉnh số dư.\n\n"
        "Khách hàng có thể kiểm tra ID của họ ở mục 💎 Cá Nhân.\n\n"
        "👉 <i>Nhắn lệnh /cancel để hủy thao tác.</i>"
    )

@bot.message_handler(func=lambda m: is_admin(m.from_user.id) and m.text == "📊 Danh Sách Kho")
def admin_btn_view_stocks(message):
    db = load_db()
    stock_text = (
        "📊 <b>CHI TIẾT TỒN KHO THỰC TẾ</b>\n"
        "______________________\n\n"
    )
    for cat_id, cat_data in PRODUCTS.items():
        stock_text += f"📂 <b>{cat_data['name']}:</b>\n"
        for prod_id, prod_data in cat_data["items"].items():
            qty = len(db["keys"].get(prod_id, []))
            stock_text += f"   • {prod_data['name']}: <b>{qty}</b> chiếc\n"
        stock_text += "\n"
    bot.send_message(message.chat.id, stock_text)

@bot.message_handler(func=lambda m: is_admin(m.from_user.id) and m.text == "📢 Gửi Thông Báo")
def admin_btn_broadcast(message):
    admin_states[message.from_user.id] = {"action": "awaiting_broadcast_message"}
    bot.send_message(
        message.chat.id,
        "📢 <b>GỬI THÔNG BÁO ĐẾN TẤT CẢ THÀNH VIÊN</b>\n"
        "______________________\n\n"
        "Vui lòng gửi nội dung thông báo:\n\n"
        "• <b>Chỉ text:</b> Nhập tin nhắn và gửi.\n"
        "• <b>Có ảnh:</b> Đính kèm ảnh (caption là nội dung).\n\n"
        "✏️ HTML được hỗ trợ: <code>&lt;b&gt;</code>, <code>&lt;i&gt;</code>, <code>&lt;code&gt;</code>\n\n"
        "👉 Gõ /cancel để huỷ."
    )

@bot.message_handler(func=lambda m: is_admin(m.from_user.id) and m.text == "❌ Thoát Admin")
def admin_btn_exit(message):
    broadcast_states.pop(message.from_user.id, None)
    admin_states.pop(message.from_user.id, None)
    bot.send_message(
        message.chat.id,
        "👋 Đã thoát bảng điều khiển Admin.",
        reply_markup=get_main_menu_keyboard()
    )

# --- XỬ LÝ NHẬP LIỆU CỦA ADMIN QUA TIN NHẮN CHỮ ---

@bot.message_handler(func=lambda message: is_admin(message.from_user.id) and message.from_user.id in admin_states)
def handle_admin_inputs(message):
    state = admin_states[message.from_user.id]
    action = state["action"]
    
    if action == "awaiting_keys":
        category_id = state["category_id"]
        product_id = state["product_id"]
        
        # Tách danh sách key được gửi (mỗi key một dòng)
        new_keys = [line.strip() for line in message.text.split("\n") if line.strip()]
        if not new_keys:
            bot.send_message(message.chat.id, "❌ Danh sách key không hợp lệ! Vui lòng nhập lại hoặc gửi lệnh /cancel để hủy.")
            return
            
        db = load_db()
        if product_id not in db["keys"]:
            db["keys"][product_id] = []
        
        db["keys"][product_id].extend(new_keys)
        save_db(db)
        
        product_name = PRODUCTS[category_id]["items"][product_id]["name"]
        success_text = (
            "✅ <b>NẠP KEY THÀNH CÔNG!</b>\n"
            "______________________\n\n"
            f"📦 <b>Sản phẩm:</b> {product_name}\n"
            f"➕ <b>Số key đã nạp:</b> {len(new_keys)} chiếc\n"
            f"📊 <b>Tổng tồn kho hiện tại:</b> {len(db['keys'][product_id])} chiếc\n\n"
            "💬 Bạn có thể gửi /admin để quay lại bảng quản trị."
        )
        del admin_states[message.from_user.id]
        bot.send_message(message.chat.id, success_text, reply_markup=get_main_menu_keyboard())

    elif action == "awaiting_user_id":
        target_user_id = message.text.strip()
        db = load_db()
        if target_user_id not in db["users"]:
            bot.send_message(message.chat.id, "❌ Không tìm thấy người dùng này trong hệ thống! Vui lòng nhập lại đúng ID Telegram hoặc gửi lệnh /cancel.")
            return
            
        user_data = db["users"][target_user_id]
        admin_states[message.from_user.id] = {
            "action": "awaiting_amount",
            "target_user_id": target_user_id
        }
        
        prompt_text = (
            "💸 <b>CỘNG TIỀN - BƯỚC 2: NHẬP SỐ TIỀN</b>\n"
            "______________________\n\n"
            f"👤 <b>Thành viên:</b> {user_data['full_name']} (ID: {target_user_id})\n"
            f"💰 <b>Số dư hiện tại:</b> {format_money(user_data['balance'])}\n\n"
            "Vui lòng nhập số tiền muốn cộng (Ví dụ: <code>100000</code>). Để trừ tiền, nhập số âm (Ví dụ: <code>-50000</code>).\n"
            "👉 <i>Nhắn /cancel để hủy.</i>"
        )
        bot.send_message(message.chat.id, prompt_text)

    elif action == "awaiting_amount":
        target_user_id = state["target_user_id"]
        try:
            amount = int(message.text.strip())
        except ValueError:
            bot.send_message(message.chat.id, "❌ Định dạng số tiền không hợp lệ! Vui lòng nhập một số nguyên hoặc gửi lệnh /cancel.")
            return
            
        db = load_db()
        user_data = db["users"].get(target_user_id)
        if not user_data:
            bot.send_message(message.chat.id, "❌ Đã xảy ra lỗi, không tìm thấy người dùng! Thao tác bị hủy.")
            del admin_states[message.from_user.id]
            return
            
        user_data["balance"] += amount
        save_db(db)
        
        del admin_states[message.from_user.id]
        
        success_text = (
            "✅ <b>ĐÃ CẬP NHẬT SỐ DƯ THÀNH CÔNG!</b>\n"
            "______________________\n\n"
            f"👤 <b>Thành viên:</b> {user_data['full_name']} (ID: {target_user_id})\n"
            f"💵 <b>Số tiền điều chỉnh:</b> {'+' if amount >= 0 else ''}{format_money(amount)}\n"
            f"💰 <b>Số dư mới:</b> {format_money(user_data['balance'])}\n\n"
            "Bấm /admin để quay lại bảng quản trị."
        )
        bot.send_message(message.chat.id, success_text, reply_markup=get_main_menu_keyboard())
        
        # Gửi thông báo cho thành viên nhận tiền
        try:
            notif_text = (
                "🔔 <b>BIẾN ĐỘNG SỐ DƯ TÀI KHOẢN</b>\n"
                "______________________\n\n"
                "Tài khoản của bạn vừa được Admin điều chỉnh số dư:\n"
                f"💵 <b>Số tiền:</b> {'+' if amount >= 0 else ''}{format_money(amount)}\n"
                f"💰 <b>Số dư hiện tại:</b> <b>{format_money(user_data['balance'])}</b>\n\n"
                "Chúc bạn một ngày mua sắm vui vẻ!"
            )
            bot.send_message(target_user_id, notif_text)
        except Exception as e:
            logger.warning(f"Không thể gửi tin nhắn thông báo đến user {target_user_id}: {e}")

    elif action == "awaiting_broadcast_message":
        # Admin nhập nội dung thông báo (text)
        content = message.text.strip()
        if not content:
            bot.send_message(message.chat.id, "❌ Nội dung không được để trống! Vui lòng nhập lại hoặc /cancel để hủy.")
            return

        broadcast_states[message.from_user.id] = {
            "type": "text",
            "content": content
        }
        del admin_states[message.from_user.id]

        db = load_db()
        total_users = len(db.get("users", {}))

        preview_text = (
            "👁 <b>XEM TRƯỚC THÔNG BÁO</b>\n"
            "______________________\n\n"
            f"{content}\n\n"
            "______________________\n"
            f"📤 Sẽ gửi đến <b>{total_users}</b> thành viên.\n\n"
            "👇 Xác nhận hoặc huỷ:"
        )
        bot.send_message(message.chat.id, preview_text, reply_markup=get_broadcast_confirm_keyboard())


# --- XỬ LÝ ẢNH BROADCAST TỪ ADMIN ---

@bot.message_handler(
    content_types=['photo'],
    func=lambda message: is_admin(message.from_user.id) and message.from_user.id in admin_states
    and admin_states[message.from_user.id].get("action") == "awaiting_broadcast_message"
)
def handle_broadcast_photo(message):
    caption = message.caption.strip() if message.caption else ""
    photo_file_id = message.photo[-1].file_id

    broadcast_states[message.from_user.id] = {
        "type": "photo",
        "file_id": photo_file_id,
        "caption": caption
    }
    del admin_states[message.from_user.id]

    db = load_db()
    total_users = len(db.get("users", {}))

    preview_caption = (
        (caption + "\n\n" if caption else "") +
        "______________________\n"
        f"📤 Sẽ gửi đến <b>{total_users}</b> thành viên.\n\n"
        "👇 Xác nhận hoặc huỷ:"
    )
    bot.send_photo(
        message.chat.id,
        photo=photo_file_id,
        caption=preview_caption,
        reply_markup=get_broadcast_confirm_keyboard()
    )


# --- XỬ LÝ NHẬP LIỆU CỦA KHÁCH HÀNG QUA TIN NHẮN CHỮ ---

@bot.message_handler(func=lambda message: message.from_user.id in user_states)
def handle_user_inputs(message):
    state = user_states[message.from_user.id]
    action = state["action"]
    
    if action == "awaiting_deposit_amount":
        try:
            amount = int(message.text.strip())
            if amount < 1000:
                raise ValueError("Số tiền tối thiểu là 1,000đ")
        except ValueError:
            bot.send_message(
                message.chat.id, 
                "❌ Số tiền nhập vào không hợp lệ (phải là số nguyên lớn hơn hoặc bằng 1,000)! Vui lòng nhập lại hoặc gõ /cancel để hủy thao tác."
            )
            return
            
        telegram_id = message.from_user.id
        # Tạo mã VietQR tự động
        qr_url = f"https://img.vietqr.io/image/MB-123456789999-print.jpg?amount={amount}&addInfo=NAP%20{telegram_id}&accountName=NGUYEN%20VAN%20A"
        
        caption = (
            "💳 <b>THÔNG TIN CHUYỂN KHOẢN NẠP TIỀN</b>\n"
            "______________________\n\n"
            f"💰 <b>Số tiền nạp:</b> {format_money(amount)}\n"
            "🏦 <b>Ngân hàng:</b> MB Bank (Ngân hàng Quân Đội)\n"
            "• Số tài khoản: <code>123456789999</code>\n"
            "• Chủ tài khoản: NGUYEN VAN A\n"
            f"• Nội dung chuyển khoản: <b>NAP {telegram_id}</b>\n\n"
            "👉 <i>Vui lòng quét mã QR bên trên bằng ứng dụng ngân hàng của bạn. Hệ thống sẽ tự động quét giao dịch và cộng tiền vào số dư của bạn sau 1-3 phút!</i>"
        )
        
        # Xóa trạng thái
        del user_states[message.from_user.id]
        
        # Gửi ảnh kèm caption và khôi phục Menu chính
        bot.send_photo(
            chat_id=message.chat.id,
            photo=qr_url,
            caption=caption,
            reply_markup=get_main_menu_keyboard()
        )

    elif action == "awaiting_bill_amount":
        # Bước 2: Người dùng nhập số tiền nạp trước khi gửi ảnh
        try:
            amount = int(message.text.strip())
            if amount < 10000:
                raise ValueError("Số tiền tối thiểu là 10,000đ")
        except ValueError:
            bot.send_message(
                message.chat.id,
                "❌ Số tiền không hợp lệ (tối thiểu 10,000đ, nhập số nguyên)!\nVui lòng nhập lại hoặc gõ /cancel để hủy."
            )
            return
        
        user_states[message.from_user.id] = {
            "action": "awaiting_bill_photo",
            "amount": amount
        }
        cancel_markup = types.InlineKeyboardMarkup()
        cancel_markup.row(types.InlineKeyboardButton("❌ Huỷ", callback_data="cancel_bill_upload"))
        bot.send_message(
            message.chat.id,
            f"📸 <b>BƯỚC 2: GỬI ẢNH BILL</b>\n\n"
            f"💰 Số tiền nạp: <b>{format_money(amount)}</b>\n\n"
            "Hãy chụp ảnh màn hình xác nhận chuyển khoản và gửi vào đây.\n\n"
            "⚠️ <i>Chỉ gửi 1 ảnh duy nhất. Admin sẽ xem xét và duyệt trong vài phút.</i>",
            reply_markup=cancel_markup
        )


# --- XỬ LÝ ẢNH BILL NẠP TIỀN TỪ NGƯỜI DÙNG ---

@bot.message_handler(content_types=['photo'], func=lambda message: message.from_user.id in user_states and user_states[message.from_user.id].get("action") == "awaiting_bill_photo")
def handle_bill_photo(message):
    state = user_states[message.from_user.id]
    amount = state["amount"]
    user_id = message.from_user.id
    user_id_str = str(user_id)
    
    db = load_db()
    user_data = get_or_create_user(db, user_id, message.from_user.username, message.from_user.first_name, message.from_user.last_name)
    
    # Lấy file_id ảnh chất lượng cao nhất
    photo_file_id = message.photo[-1].file_id
    
    # Tạo ID yêu cầu nạp tiền duy nhất
    deposit_request_id = f"DEP_{user_id}_{int(datetime.now().timestamp())}"
    
    # Lưu yêu cầu vào DB
    if "deposit_requests" not in db:
        db["deposit_requests"] = {}
    db["deposit_requests"][deposit_request_id] = {
        "user_id": user_id_str,
        "amount": amount,
        "photo_file_id": photo_file_id,
        "status": "pending",
        "created_at": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        "full_name": user_data["full_name"],
        "username": user_data["username"]
    }
    save_db(db)
    
    # Xóa trạng thái người dùng
    del user_states[user_id]
    
    # Thông báo người dùng đã gửi thành công
    bot.send_message(
        message.chat.id,
        "✅ <b>ĐÃ GỬI BILL NẠP TIỀN!</b>\n"
        "______________________\n\n"
        f"💰 Số tiền yêu cầu: <b>{format_money(amount)}</b>\n"
        f"🕐 Thời gian gửi: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n\n"
        "⏳ Admin đang xem xét bill của bạn. Bạn sẽ nhận được thông báo khi được duyệt.\n\n"
        "💡 <i>Thời gian duyệt thường từ 5-15 phút trong giờ hành chính.</i>",
        reply_markup=get_main_menu_keyboard()
    )
    
    # Gửi thông báo đến TẤT CẢ admin
    username_display = f"@{user_data['username']}" if user_data['username'] != "Không có" else "Không có"
    admin_caption = (
        "🔔 <b>YÊU CẦU NẠP TIỀN MỚI!</b>\n"
        "______________________\n\n"
        f"👤 <b>Người dùng:</b> {user_data['full_name']}\n"
        f"🆔 <b>Telegram ID:</b> <code>{user_id_str}</code>\n"
        f"📛 <b>Username:</b> {username_display}\n"
        f"💰 <b>Số tiền nạp:</b> {format_money(amount)}\n"
        f"🕐 <b>Thời gian:</b> {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n"
        f"🔑 <b>Mã yêu cầu:</b> <code>{deposit_request_id}</code>\n\n"
        "👇 Vui lòng kiểm tra bill và duyệt hoặc từ chối:"
    )
    
    # Nút duyệt / từ chối cho admin
    admin_markup = types.InlineKeyboardMarkup(row_width=2)
    admin_markup.row(
        types.InlineKeyboardButton("✅ Duyệt", callback_data=f"approve_dep_{deposit_request_id}"),
        types.InlineKeyboardButton("❌ Từ Chối", callback_data=f"reject_dep_{deposit_request_id}")
    )
    
    for admin_id in ADMIN_IDS:
        try:
            bot.send_photo(
                chat_id=admin_id,
                photo=photo_file_id,
                caption=admin_caption,
                reply_markup=admin_markup
            )
        except Exception as e:
            logger.warning(f"Không thể gửi bill đến admin {admin_id}: {e}")

# --- XỬ LÝ SỰ KIỆN CALLBACK QUERY (INLINE KEYBOARD) ---

@bot.callback_query_handler(func=lambda call: True)
def handle_callback_query(call):
    data = call.data
    logger.info(f"Nhận Callback: {data} từ chat_id: {call.message.chat.id}")

    try:
        db = load_db()
        
        # 1. Quay lại danh sách danh mục (Khách hàng)
        if data == "back_to_categories":
            text = (
                "🛍️ <b>DANH SÁCH SẢN PHẨM</b>\n\n"
                "Chào mừng bạn đến với cửa hàng! Vui lòng chọn danh mục bạn muốn xem:"
            )
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=text,
                reply_markup=get_categories_keyboard()
            )
            bot.answer_callback_query(call.id)

        # 2. Xem sản phẩm thuộc một danh mục (Khách hàng)
        elif data.startswith("cat_") and not data.startswith("cat_admin_"):
            category_id = data.split("_", 1)[1]
            category = PRODUCTS.get(category_id)
            if category:
                text = (
                    f"📁 <b>Mục: {category['name']}</b>\n\n"
                    "👇 Nhấn vào nút bên dưới để chọn sản phẩm bạn muốn mua:"
                )
                bot.edit_message_text(
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    text=text,
                    reply_markup=get_products_keyboard(category_id)
                )
                bot.answer_callback_query(call.id)
            else:
                bot.answer_callback_query(call.id, "❌ Không tìm thấy danh mục này!", show_alert=True)

        # 3. Xem chi tiết sản phẩm (Khách hàng)
        elif data.startswith("prod_") and not data.startswith("prod_admin_"):
            category_id = None
            product_id = None
            for c_id in PRODUCTS.keys():
                prefix = f"prod_{c_id}_"
                if data.startswith(prefix):
                    category_id = c_id
                    product_id = data[len(prefix):]
                    break
            
            if category_id and product_id:
                category = PRODUCTS[category_id]
                product = category["items"].get(product_id)
                stock = len(db["keys"].get(product_id, []))
                
                if product:
                    text = (
                        "📦 <b>THÔNG TIN SẢN PHẨM</b>\n"
                        "______________________\n\n"
                        f"🏷️ <b>Tên:</b> {product['name']}\n"
                        f"💎 <b>Giá:</b> {format_money(product['price'])}\n"
                        f"📊 <b>Số lượng trong kho:</b> {stock} chiếc\n\n"
                        "👇 Chọn số lượng bạn muốn mua:"
                    )
                    bot.edit_message_text(
                        chat_id=call.message.chat.id,
                        message_id=call.message.message_id,
                        text=text,
                        reply_markup=get_purchase_keyboard(category_id, product_id)
                    )
                    bot.answer_callback_query(call.id)
                else:
                    bot.answer_callback_query(call.id, "❌ Không tìm thấy sản phẩm này!", show_alert=True)
            else:
                bot.answer_callback_query(call.id, "❌ Dữ liệu sản phẩm không hợp lệ!", show_alert=True)

        # 4. Xử lý khi khách hàng mua hàng
        elif data.startswith("buy_"):
            category_id = None
            product_id = None
            qty = 1
            
            for c_id in PRODUCTS.keys():
                prefix = f"buy_{c_id}_"
                if data.startswith(prefix):
                    category_id = c_id
                    rest = data[len(prefix):]
                    parts = rest.rsplit("_", 1)
                    if len(parts) == 2:
                        product_id = parts[0]
                        try:
                            qty = int(parts[1])
                        except ValueError:
                            qty = 1
                    break
            
            if category_id and product_id:
                category = PRODUCTS[category_id]
                product = category["items"].get(product_id)
                
                if product:
                    available_keys = db["keys"].get(product_id, [])
                    stock = len(available_keys)
                    user_id_str = str(call.message.chat.id)
                    user_data = get_or_create_user(db, call.message.chat.id, call.from_user.username, call.from_user.first_name, call.from_user.last_name)
                    total_price = product["price"] * qty
                    
                    # Kiểm tra tồn kho trước
                    if stock <= 0:
                        bot.answer_callback_query(
                            call.id, 
                            "❌ Sản phẩm này hiện đã hết hàng, vui lòng quay lại sau hoặc liên hệ Admin!", 
                            show_alert=True
                        )
                    elif qty > stock:
                        bot.answer_callback_query(
                            call.id, 
                            f"❌ Số lượng trong kho chỉ còn {stock} chiếc, không đủ đáp ứng!", 
                            show_alert=True
                        )
                    # Kiểm tra số dư tài khoản
                    elif user_data["balance"] < total_price:
                        # Không đủ tiền -> Hiện hóa đơn yêu cầu nạp tiền kèm QR Code
                        qr_url = "https://i.postimg.cc/Bv3HQk9K/6273529661664989075.jpg"
                        payment_invoice_text = (
                            f'<a href="{qr_url}">&#8203;</a>'
                            "🛍️ <b>ĐƠN HÀNG THANH TOÁN</b>\n"
                            "______________________\n\n"
                            f"🏷️ <b>Sản phẩm:</b> {product['name']}\n"
                            f"📊 <b>Số lượng:</b> {qty} chiếc\n"
                            f"💰 <b>Tổng tiền:</b> {format_money(total_price)}\n\n"
                            "⚠️ <b>Trạng thái:</b> Chờ thanh toán\n"
                            f"<i>Số dư tài khoản: <b>{format_money(user_data['balance'])}</b> (Không đủ thanh toán).\n"
                            f"Vui lòng quét mã QR ở trên và ghi đúng nội dung chuyển khoản là <b>ID Telegram</b> của bạn để hệ thống cộng tiền:</i>\n\n"
                            f"📥 <b>Nội dung chuyển khoản:</b> <code>{user_id_str}</code>\n\n"
                            "⏱️ <i>Sau khi chuyển khoản thành công, hệ thống sẽ tự động đối soát giao dịch, cộng tiền và hoàn tất đơn hàng cho bạn!</i>"
                        )
                        
                        back_markup = types.InlineKeyboardMarkup()
                        back_markup.row(types.InlineKeyboardButton("🔙 Quay Lại Chi Tiết Sản Phẩm", callback_data=f"prod_{category_id}_{product_id}"))
                        
                        bot.edit_message_text(
                            chat_id=call.message.chat.id,
                            message_id=call.message.message_id,
                            text=payment_invoice_text,
                            reply_markup=back_markup
                        )
                        bot.answer_callback_query(call.id)
                    else:
                        # Đủ tiền và đủ key -> Thực hiện giao dịch mua bán
                        purchased_keys = []
                        for _ in range(qty):
                            purchased_keys.append(available_keys.pop(0))
                        
                        # Cập nhật số dư người dùng và kho hàng
                        user_data["balance"] -= total_price
                        db["keys"][product_id] = available_keys
                        db["stats"]["total_revenue"] += total_price
                        db["stats"]["keys_sold"] += qty
                        
                        # Lưu lịch sử giao dịch mua hàng
                        invoice = {
                            "date": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                            "product_name": f"{product['name']} (x{qty})",
                            "qty": qty,
                            "price": total_price,
                            "keys": purchased_keys
                        }
                        user_data["history"].append(invoice)
                        save_db(db)
                        
                        # Gửi key thành công
                        keys_text = "\n".join([f"   🔑 <code>{k}</code>" for k in purchased_keys])
                        success_text = (
                            "🎉 <b>MUA HÀNG THÀNH CÔNG!</b>\n"
                            "______________________\n\n"
                            f"🏷️ <b>Sản phẩm:</b> {product['name']}\n"
                            f"📊 <b>Số lượng:</b> {qty} chiếc\n"
                            f"💰 <b>Khấu trừ số dư:</b> -{format_money(total_price)}\n"
                            f"💳 <b>Số dư còn lại:</b> <b>{format_money(user_data['balance'])}</b>\n\n"
                            "🔑 <b>Danh sách mã Key của bạn:</b>\n"
                            f"{keys_text}\n\n"
                            "<i>Cảm ơn bạn đã tin tưởng ủng hộ shop! Bạn có thể xem lại mã key đã mua trong mục 📄 Lịch Sử Nạp bất kỳ lúc nào.</i>"
                        )
                        
                        bot.edit_message_text(
                            chat_id=call.message.chat.id,
                            message_id=call.message.message_id,
                            text=success_text
                        )
                        bot.answer_callback_query(call.id, "🎉 Mua hàng thành công!")
                else:
                    bot.answer_callback_query(call.id, "❌ Không tìm thấy sản phẩm này!", show_alert=True)
            else:
                bot.answer_callback_query(call.id, "❌ Thông tin mua hàng lỗi!", show_alert=True)

        # --- CÁC CALL QUERY LIÊN QUAN ĐẾN ADMIN ---

        # 5. Quay lại trang chọn danh mục nạp key (từ inline)
        elif data == "admin_panel_home":
            if not is_admin(call.from_user.id): return
            bot.answer_callback_query(call.id)
            bot.send_message(call.message.chat.id, "🛠️ Dùng bàn phím Admin bên dưới để tiếp tục.", reply_markup=get_admin_keyboard())

        # 6. Admin xác nhận gửi broadcast
        elif data == "admin_broadcast_confirm":
            if not is_admin(call.from_user.id): return

            state = broadcast_states.get(call.from_user.id)
            if not state:
                bot.answer_callback_query(call.id, "❌ Không tìm thấy nội dung thông báo!", show_alert=True)
                return

            bot.answer_callback_query(call.id, "⏳ Đang gửi thông báo...", show_alert=False)

            db = load_db()
            all_user_ids = list(db.get("users", {}).keys())
            total = len(all_user_ids)
            success_count = 0
            fail_count = 0

            for uid_str in all_user_ids:
                try:
                    if state["type"] == "text":
                        bot.send_message(int(uid_str), state["content"])
                    elif state["type"] == "photo":
                        bot.send_photo(
                            int(uid_str),
                            photo=state["file_id"],
                            caption=state.get("caption", "")
                        )
                    success_count += 1
                except Exception as e:
                    logger.warning(f"Broadcast: Không gửi được đến {uid_str}: {e}")
                    fail_count += 1

            del broadcast_states[call.from_user.id]

            result_text = (
                "✅ <b>ĐÃ GỬI THÔNG BÁO XONG!</b>\n"
                "______________________\n\n"
                f"👥 <b>Tổng thành viên:</b> {total}\n"
                f"✅ <b>Gửi thành công:</b> {success_count}\n"
                f"❌ <b>Thất bại (bị block/lỗi):</b> {fail_count}\n\n"
                f"🕐 <b>Thời gian:</b> {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}"
            )
            try:
                bot.edit_message_text(
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    text=result_text
                )
            except Exception:
                bot.send_message(call.message.chat.id, result_text)

        # 7. Admin huỷ broadcast
        elif data == "admin_broadcast_cancel":
            if not is_admin(call.from_user.id): return

            broadcast_states.pop(call.from_user.id, None)
            bot.answer_callback_query(call.id, "❌ Đã huỷ gửi thông báo.", show_alert=False)
            try:
                bot.edit_message_text(
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    text="❌ Đã huỷ gửi thông báo."
                )
            except Exception:
                pass

        # 8. Admin nạp key - Bước 2: Chọn sản phẩm
        elif data.startswith("cat_admin_"):
            if not is_admin(call.from_user.id): return
            
            category_id = data.split("_", 2)[2]
            category = PRODUCTS.get(category_id)
            
            if category:
                markup = types.InlineKeyboardMarkup(row_width=1)
                for prod_id, prod_data in category["items"].items():
                    qty = len(db["keys"].get(prod_id, []))
                    btn_text = f"🔹 {prod_data['name']} (Hiện có: {qty} key)"
                    markup.row(types.InlineKeyboardButton(btn_text, callback_data=f"prod_admin_{category_id}_{prod_id}"))
                markup.row(types.InlineKeyboardButton("🔙 Quay Lại", callback_data="admin_panel_home"))
                
                bot.send_message(
                    call.message.chat.id,
                    f"➕ <b>NẠP KEY — CHỌN SẢN PHẨM [{category['name']}]</b>\n\nChọn gói sản phẩm để nạp key:",
                    reply_markup=markup
                )
                bot.answer_callback_query(call.id)
            else:
                bot.answer_callback_query(call.id, "❌ Không tìm thấy danh mục!", show_alert=True)

        # 9. Admin nạp key - Bước 3: Đợi admin nhập key qua tin nhắn chat
        elif data.startswith("prod_admin_"):
            if not is_admin(call.from_user.id): return
            
            category_id = None
            product_id = None
            for c_id in PRODUCTS.keys():
                prefix = f"prod_admin_{c_id}_"
                if data.startswith(prefix):
                    category_id = c_id
                    product_id = data[len(prefix):]
                    break
            
            if category_id and product_id:
                product_name = PRODUCTS[category_id]["items"][product_id]["name"]
                qty_now = len(db["keys"].get(product_id, []))
                
                admin_states[call.from_user.id] = {
                    "action": "awaiting_keys",
                    "category_id": category_id,
                    "product_id": product_id
                }
                
                text = (
                    f"➕ <b>NẠP KEY: {product_name}</b>\n"
                    "______________________\n\n"
                    f"• Tồn kho hiện có: <b>{qty_now} chiếc</b>\n\n"
                    "Vui lòng nhập/dán danh sách Key mới vào tin nhắn bên dưới và gửi đi (Mỗi key nằm trên 1 dòng):\n\n"
                    "👉 <i>Nhắn lệnh /cancel để hủy thao tác nạp key.</i>"
                )
                bot.edit_message_text(
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    text=text
                )
                bot.answer_callback_query(call.id)
            else:
                bot.answer_callback_query(call.id, "❌ Thông tin sản phẩm không đúng!", show_alert=True)

        # 12. Admin duyệt bill nạp tiền
        elif data.startswith("approve_dep_"):
            if not is_admin(call.from_user.id): return
            
            deposit_request_id = data[len("approve_dep_"):]
            db = load_db()
            deposit_requests = db.get("deposit_requests", {})
            req = deposit_requests.get(deposit_request_id)
            
            if not req:
                bot.answer_callback_query(call.id, "❌ Không tìm thấy yêu cầu này!", show_alert=True)
                return
            
            if req["status"] != "pending":
                status_vi = "đã được duyệt" if req["status"] == "approved" else "đã bị từ chối"
                bot.answer_callback_query(call.id, f"⚠️ Yêu cầu này {status_vi} trước đó rồi!", show_alert=True)
                return
            
            # Cộng tiền vào tài khoản người dùng
            user_id_str = req["user_id"]
            amount = req["amount"]
            
            if user_id_str not in db["users"]:
                bot.answer_callback_query(call.id, "❌ Không tìm thấy tài khoản người dùng!", show_alert=True)
                return
            
            db["users"][user_id_str]["balance"] += amount
            db["deposit_requests"][deposit_request_id]["status"] = "approved"
            db["deposit_requests"][deposit_request_id]["approved_by"] = str(call.from_user.id)
            db["deposit_requests"][deposit_request_id]["approved_at"] = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            save_db(db)
            
            new_balance = db["users"][user_id_str]["balance"]
            
            # Cập nhật caption tin nhắn admin
            approved_caption = (
                call.message.caption + 
                f"\n\n✅ <b>ĐÃ DUYỆT</b> bởi Admin lúc {datetime.now().strftime('%H:%M:%S %d/%m/%Y')}"
            )
            try:
                bot.edit_message_caption(
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    caption=approved_caption
                )
            except Exception:
                pass
            
            bot.answer_callback_query(call.id, f"✅ Đã duyệt và cộng {format_money(amount)} cho user {user_id_str}!", show_alert=True)
            
            # Thông báo cho người dùng
            try:
                bot.send_message(
                    int(user_id_str),
                    "🎉 <b>BILL NẠP TIỀN ĐÃ ĐƯỢC DUYỆT!</b>\n"
                    "______________________\n\n"
                    f"💰 <b>Số tiền được cộng:</b> +{format_money(amount)}\n"
                    f"💳 <b>Số dư hiện tại:</b> <b>{format_money(new_balance)}</b>\n"
                    f"🕐 <b>Thời gian duyệt:</b> {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n\n"
                    "✨ Cảm ơn bạn đã nạp tiền! Hãy tận hưởng mua sắm nhé 🛍️"
                )
            except Exception as e:
                logger.warning(f"Không thể thông báo duyệt cho user {user_id_str}: {e}")

        # 13. Admin từ chối bill nạp tiền
        elif data.startswith("reject_dep_"):
            if not is_admin(call.from_user.id): return
            
            deposit_request_id = data[len("reject_dep_"):]
            db = load_db()
            deposit_requests = db.get("deposit_requests", {})
            req = deposit_requests.get(deposit_request_id)
            
            if not req:
                bot.answer_callback_query(call.id, "❌ Không tìm thấy yêu cầu này!", show_alert=True)
                return
            
            if req["status"] != "pending":
                status_vi = "đã được duyệt" if req["status"] == "approved" else "đã bị từ chối"
                bot.answer_callback_query(call.id, f"⚠️ Yêu cầu này {status_vi} trước đó rồi!", show_alert=True)
                return
            
            user_id_str = req["user_id"]
            amount = req["amount"]
            
            db["deposit_requests"][deposit_request_id]["status"] = "rejected"
            db["deposit_requests"][deposit_request_id]["rejected_by"] = str(call.from_user.id)
            db["deposit_requests"][deposit_request_id]["rejected_at"] = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            save_db(db)
            
            # Cập nhật caption tin nhắn admin
            rejected_caption = (
                call.message.caption +
                f"\n\n❌ <b>ĐÃ TỪ CHỐI</b> bởi Admin lúc {datetime.now().strftime('%H:%M:%S %d/%m/%Y')}"
            )
            try:
                bot.edit_message_caption(
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    caption=rejected_caption
                )
            except Exception:
                pass
            
            bot.answer_callback_query(call.id, f"❌ Đã từ chối yêu cầu nạp {format_money(amount)} của user {user_id_str}!", show_alert=True)
            
            # Thông báo cho người dùng
            try:
                bot.send_message(
                    int(user_id_str),
                    "❌ <b>BILL NẠP TIỀN BỊ TỪ CHỐI</b>\n"
                    "______________________\n\n"
                    f"💰 <b>Số tiền yêu cầu:</b> {format_money(amount)}\n"
                    f"🕐 <b>Thời gian:</b> {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n\n"
                    "⚠️ Bill của bạn không được xác nhận. Có thể do:\n"
                    "• Ảnh bill không rõ ràng hoặc không hợp lệ\n"
                    "• Thông tin chuyển khoản không khớp\n\n"
                    "💬 Vui lòng liên hệ mục 🤵 <b>Hỗ Trợ</b> để được hỗ trợ thêm."
                )
            except Exception as e:
                logger.warning(f"Không thể thông báo từ chối cho user {user_id_str}: {e}")

        # 14. Người dùng nhấn nút "Gửi bill nạp tiền"
        elif data == "user_send_bill_start":
            user_id = call.from_user.id
            user_states[user_id] = {"action": "awaiting_bill_amount"}
            
            bot.send_message(
                call.message.chat.id,
                "💸 <b>NẠP TIỀN QUA BILL - BƯỚC 1</b>\n"
                "______________________\n\n"
                "Vui lòng nhập <b>số tiền</b> bạn đã chuyển khoản (tối thiểu 10,000đ):\n\n"
                "📝 Ví dụ: <code>100000</code>\n\n"
                "👉 <i>Gõ /cancel để hủy.</i>",
                reply_markup=get_bill_cancel_keyboard()
            )
            bot.answer_callback_query(call.id)

        # 15. Người dùng hủy gửi bill
        elif data == "cancel_bill_upload":
            user_id = call.from_user.id
            if user_id in user_states:
                del user_states[user_id]
            bot.send_message(
                call.message.chat.id,
                "❌ Đã hủy gửi bill nạp tiền.",
                reply_markup=get_main_menu_keyboard()
            )
            bot.answer_callback_query(call.id)

        # 16. Người dùng xem ví
        elif data == "user_view_wallet":
            db = load_db()
            user_id_str = str(call.from_user.id)
            user_data = db["users"].get(user_id_str)
            if user_data:
                bot.answer_callback_query(
                    call.id,
                    f"💳 Số dư của bạn: {format_money(user_data['balance'])}",
                    show_alert=True
                )
            else:
                bot.answer_callback_query(call.id, "❌ Không tìm thấy tài khoản!", show_alert=True)

        # 17. Đóng menu nạp tiền / quay về main menu
        elif data in ("user_close_deposit_menu", "user_back_to_deposit_menu"):
            bot.answer_callback_query(call.id)
            bot.send_message(
                call.message.chat.id,
                "🏠 Quay về menu chính.",
                reply_markup=get_main_menu_keyboard()
            )

        # 17b. Người dùng chọn IMZ trong menu FILE
        elif data == "file_imz":
            text = (
                "📱 <b>BẢNG GIÁ IMZ</b>\n"
                "______________________\n\n"
                "💠 ĐỊNH VỊ: <b>60K</b>\n"
                "💠 AIM CỔ + DV: <b>100K</b>\n"
                "💠 AIMBODY + DV: <b>120K</b>\n"
                "💠 AIM CỔ: <b>65K</b>\n"
                "💠 AIMBODY: <b>75K</b>\n\n"
                "💬 Liên hệ 🤵 <b>Hỗ Trợ</b> để được tư vấn và mua hàng."
            )
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=text,
                reply_markup=get_file_back_keyboard()
            )
            bot.answer_callback_query(call.id)

        # 17c. Người dùng chọn FILZA trong menu FILE
        elif data == "file_filza":
            text = (
                "📂 <b>BẢNG GIÁ FILZA</b>\n"
                "______________________\n\n"
                "💠 AIM CỔ + DV: <b>120K</b>\n"
                "💠 AIMMAGIC + DV: <b>130K</b>\n"
                "💠 AIMBODY + DV: <b>120K</b>\n"
                "💠 AIM CỔ + AIMBODY: <b>150K</b>\n"
                "💠 ĐỊNH VỊ: <b>50K</b>\n\n"
                "💬 Liên hệ 🤵 <b>Hỗ Trợ</b> để được tư vấn và mua hàng."
            )
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=text,
                reply_markup=get_file_back_keyboard()
            )
            bot.answer_callback_query(call.id)

        # 17d. Quay lại menu FILE (IMZ / FILZA)
        elif data == "file_back":
            text = (
                "📁 <b>FILE</b>\n"
                "______________________\n\n"
                "👇 Vui lòng chọn loại file bạn muốn xem bảng giá:"
            )
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=text,
                reply_markup=get_file_menu_keyboard()
            )
            bot.answer_callback_query(call.id)

        # 18. Quay lại danh sách Acc Clone
        elif data == "acc_back_list":
            text = (
                "🧬 <b>MUA ACC CLONE</b>\n"
                "______________________\n\n"
                "👇 Chọn loại acc bạn muốn mua bên dưới:\n\n"
                "💠 <b>ACCLV5</b>  —  3,000đ/1 acc\n"
                "💠 <b>ACCLV8</b>  —  7,000đ/1 acc\n"
                "💠 <b>ACCLV15</b>  —  20,000đ/1 acc\n"
                "💠 <b>ACCLV30</b>  —  40,000đ/1 acc\n\n"
                "✅ Acc được giao tự động sau khi thanh toán!"
            )
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=text,
                reply_markup=get_acc_clone_keyboard()
            )
            bot.answer_callback_query(call.id)

        # 19. Quay về menu chính từ acc clone
        elif data == "acc_back_main":
            bot.answer_callback_query(call.id)
            bot.send_message(
                call.message.chat.id,
                "🏠 Quay về menu chính.",
                reply_markup=get_main_menu_keyboard()
            )

        # 20. Người dùng chọn loại acc clone để mua
        elif data.startswith("acc_buy_"):
            prod_id = data[len("acc_buy_"):]
            acc_items = PRODUCTS["acc_clone"]["items"]
            product = acc_items.get(prod_id)
            if not product:
                bot.answer_callback_query(call.id, "❌ Sản phẩm không tồn tại!", show_alert=True)
                return
            stock = len(db["keys"].get(prod_id, []))
            text = (
                f"🧬 <b>{product['name']}</b>\n"
                "______________________\n\n"
                f"💰 <b>Giá:</b> {format_money(product['price'])}/1 acc\n"
                f"📦 <b>Kho hiện có:</b> {stock} acc\n\n"
                "👇 Chọn số lượng bạn muốn mua:"
            )
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=text,
                reply_markup=get_acc_qty_keyboard(prod_id)
            )
            bot.answer_callback_query(call.id)

        # 21. Xử lý mua acc clone với số lượng đã chọn
        elif data.startswith("acc_confirm_"):
            parts = data[len("acc_confirm_"):].rsplit("_", 1)
            if len(parts) != 2:
                bot.answer_callback_query(call.id, "❌ Dữ liệu không hợp lệ!", show_alert=True)
                return
            prod_id, qty_str = parts[0], parts[1]
            try:
                qty = int(qty_str)
            except ValueError:
                bot.answer_callback_query(call.id, "❌ Số lượng không hợp lệ!", show_alert=True)
                return

            acc_items = PRODUCTS["acc_clone"]["items"]
            product = acc_items.get(prod_id)
            if not product:
                bot.answer_callback_query(call.id, "❌ Sản phẩm không tồn tại!", show_alert=True)
                return

            user_id = call.from_user.id
            user_id_str = str(user_id)
            user_data = db["users"].get(user_id_str)
            if not user_data:
                bot.answer_callback_query(call.id, "❌ Không tìm thấy tài khoản!", show_alert=True)
                return

            total_price = product["price"] * qty
            stock_list = db["keys"].get(prod_id, [])

            if len(stock_list) < qty:
                bot.answer_callback_query(
                    call.id,
                    f"❌ Kho không đủ hàng! Hiện chỉ còn {len(stock_list)} acc.",
                    show_alert=True
                )
                return

            if user_data["balance"] < total_price:
                bot.answer_callback_query(
                    call.id,
                    f"❌ Số dư không đủ! Cần {format_money(total_price)}, bạn có {format_money(user_data['balance'])}.",
                    show_alert=True
                )
                return

            # Trừ tiền, lấy acc từ kho
            purchased_accs = stock_list[:qty]
            db["keys"][prod_id] = stock_list[qty:]
            db["users"][user_id_str]["balance"] -= total_price
            db["stats"]["total_revenue"] = db["stats"].get("total_revenue", 0) + total_price
            db["stats"]["keys_sold"] = db["stats"].get("keys_sold", 0) + qty

            # Lưu lịch sử
            history_entry = {
                "product_name": product["name"],
                "qty": qty,
                "price": total_price,
                "date": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                "keys": purchased_accs
            }
            db["users"][user_id_str].setdefault("history", []).append(history_entry)
            save_db(db)

            acc_list_text = "\n".join([f"   • <code>{acc}</code>" for acc in purchased_accs])
            new_balance = db["users"][user_id_str]["balance"]
            result_text = (
                "✅ <b>MUA ACC CLONE THÀNH CÔNG!</b>\n"
                "______________________\n\n"
                f"🧬 <b>Loại acc:</b> {product['name']}\n"
                f"🔢 <b>Số lượng:</b> {qty} acc\n"
                f"💰 <b>Tổng tiền:</b> {format_money(total_price)}\n"
                f"💳 <b>Số dư còn lại:</b> {format_money(new_balance)}\n\n"
                f"📦 <b>Danh sách Acc của bạn:</b>\n{acc_list_text}\n\n"
                "🎉 Cảm ơn bạn đã mua hàng!"
            )
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=result_text,
                reply_markup=types.InlineKeyboardMarkup().row(
                    types.InlineKeyboardButton("🧬 Mua Thêm", callback_data="acc_back_list")
                )
            )
            bot.answer_callback_query(call.id, "✅ Mua thành công!", show_alert=False)

    except Exception as e:
        logger.error(f"Lỗi khi xử lý callback query: {e}")
        try:
            bot.answer_callback_query(call.id, "❌ Đã xảy ra lỗi, vui lòng thử lại sau!", show_alert=True)
        except Exception:
            pass

# Khởi chạy bot
if __name__ == "__main__":
    logger.info("Bot đang khởi chạy...")
    print("\n-------------------------------------------")
    print("Telegram Shop Bot đã khởi chạy thành công!")
    print("Hãy mở Telegram và gửi lệnh /start để trải nghiệm.")
    print("Nếu là Admin, cấu hình ADMIN_ID và gõ lệnh /admin để nạp key.")
    print("-------------------------------------------\n")
    bot.infinity_polling()