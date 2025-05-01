import json
import random
from telegram.ext import ConversationHandler
from telegram.constants import ParseMode
from telegram import InputMediaPhoto
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler
import os
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaAnimation
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler, MessageHandler, filters
(ADD_CODE, ADD_NAME, ADD_REWARD, ADD_DESCRIPTION, CONFIRM_ADD,
 EDIT_CHOOSE, EDIT_FIELD, EDIT_NEWVALUE, CONFIRM_EDIT) = range(9)

pending_task = {}
pending_edit = {}
MAIL_COLLECTING, MAIL_WAITING_SEND = range(2)


mail_data = {
    "media": [],
    "caption": ""
}
# ----- ID Admin -----
admin_id = "5998680632"

# ----- Tải dữ liệu từ file JSON -----
def load_data():
    try:
        with open('users.json', 'r', encoding='utf-8') as f:
            users = json.load(f)
    except:
        users = {}

    try:
        with open('giftcodes.json', 'r', encoding='utf-8') as f:
            giftcodes = json.load(f)
    except:
        giftcodes = {}

    try:
        with open('history.json', 'r', encoding='utf-8') as f:
            history = json.load(f)
    except:
        history = {}

    try:
        with open('withdraw.json', 'r', encoding='utf-8') as f:
            withdraw_requests = json.load(f)
    except:
        withdraw_requests = {}

    try:
        with open('nhiemvu.json', 'r', encoding='utf-8') as f:
            nhiemvu = json.load(f)
    except:
        nhiemvu = {}

    return users, giftcodes, history, withdraw_requests, nhiemvu

def save_data():
    with open('users.json', 'w', encoding='utf-8') as f:
        json.dump(users, f, ensure_ascii=False, indent=4)
    with open('giftcodes.json', 'w', encoding='utf-8') as f:
        json.dump(giftcodes, f, ensure_ascii=False, indent=4)
    with open('history.json', 'w', encoding='utf-8') as f:
        json.dump(history, f, ensure_ascii=False, indent=4)
    with open('withdraw.json', 'w', encoding='utf-8') as f:
        json.dump(withdraw_requests, f, ensure_ascii=False, indent=4)
    with open('nhiemvu.json', 'w', encoding='utf-8') as f:
        json.dump(nhiemvu, f, ensure_ascii=False, indent=4)

users, giftcodes, history, withdraw_requests, nhiemvu = load_data()

# ----- Hàm /start -----
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    username = update.effective_user.username or "NoUsername"

    # Kiểm tra nếu người dùng mới chưa có trong users
    if user_id not in users:
        users[user_id] = {
        "username": username,
        "balance": 0,
        "referrals": 0,
        "invited_users": [],
        "missions": [],
        "locked": False

    }
    save_data()


    keyboard = [
        [
            InlineKeyboardButton("👤 Tài Khoản", callback_data="tai_khoan"),
            InlineKeyboardButton("🎉 Mời Bạn Bè", callback_data="moi_ban_be")
        ],
        [
            InlineKeyboardButton("🕹 Trò chơi MEGAWIN", callback_data="menu_game"),
            InlineKeyboardButton("🎁 Nhập Giftcode", callback_data="nhap_giftcode")
        ],
        [
            InlineKeyboardButton("💵 Rút Tiền", callback_data="rut_tien"),
            InlineKeyboardButton("💳 Nạp Tiền", callback_data="nap_tien"),
            InlineKeyboardButton("📝 Nhiệm Vụ", callback_data="nhiem_vu"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)   

    if update.message:
        await update.message.reply_text(
            "🎯 Chào mừng bạn đến với MegaWin Game 2025!\n\nChọn chức năng bên dưới:",
            reply_markup=reply_markup,
        )
    elif update.callback_query:
        await update.callback_query.message.edit_text(
            "🎯 Chào mừng bạn đến với MegaWin Game 2025!\n\nChọn chức năng bên dưới:",
            reply_markup=reply_markup,
        )
        # Nếu có referrer
    if context.args:
        ref_id = context.args[0]
        if ref_id != user_id and ref_id in users:
            if user_id not in users[ref_id].get("invited_users", []):
                users[ref_id]['balance'] += 5000  # ✅ Thưởng giới thiệu 5k
                users[ref_id]['referrals'] += 1
                users[ref_id].setdefault("invited_users", []).append(user_id)
                await context.bot.send_message(
                    chat_id=ref_id,
                    text=f"🎉 Bạn vừa nhận 5.000 VNĐ từ việc mời @{username} tham gia bot!"
                )
                save_data()

# Menu admin
async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)

    if user_id == admin_id:
        text = (
            "🔒 Menu Admin:\n\n"
            "/mailing_all_user ➔ Thông báo cho tất cả ae\n"
            "/addgift <code> <số_tiền> ➔ Tạo giftcode\n"
            "/addcoin <user_id> <số_tiền> ➔ Cộng tiền user\n"
            "/listuser ➔ Xem danh sách user\n"
            "/ruttien ➔ Xem danh sách lệnh rút\n"
            "/setting_nhiemvu ➔ Quản lý Nhiệm vụ\n"
            "/timkiem_user ➔ Tìm kiếm user\n"
            "/user_history ➔ Xem lịch sử người dùng 📊\n"
        )
        await update.message.reply_text(text)
    else:
        await update.message.reply_text("⛔ Bạn không có quyền truy cập Admin.")


# ----- Mục Nhiệm Vụ -----
async def nhiemvu_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)

    if user_id not in users:
        await update.callback_query.answer("Bạn chưa đăng ký tài khoản.")
        return

    tasks = [task for task in nhiemvu.get('tasks', []) if task.get('active', True)]

    if not tasks:
        await update.callback_query.answer("Hiện tại không có nhiệm vụ nào.")
        return

    keyboard = []
    text = "📋 Danh sách nhiệm vụ:\n\n"

    for task in tasks:
        text += (
            f"🔖 Mã: {task.get('code', '')}\n"
            f"📝 Tên: {task.get('name', '')}\n"
            f"💰 Tiền thưởng: {task.get('reward', 0)} VNĐ\n"
            f"📄 Mô tả: {task.get('description', 'Không có mô tả')}\n\n"
        )
        keyboard.append([InlineKeyboardButton(f"🆙 Làm {task['name']}", callback_data=f"nhiemvu_{task['id']}")])

    keyboard.append([InlineKeyboardButton("🔙 Quay lại", callback_data="menu")])

    await update.callback_query.edit_message_text(
        text=text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# ----- Nhiệm Vụ Cụ Thể -----
async def process_nhiemvu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    task_id = int(update.callback_query.data.split('_')[1])

    # Kiểm tra nhiệm vụ
    task = next((task for task in nhiemvu.get('tasks', []) if task['id'] == task_id), None)
    if not task:
        await update.callback_query.answer("❌ Nhiệm vụ không tồn tại.")
        return

    # Đảm bảo danh sách nhiệm vụ tồn tại
    missions = users[user_id].get('missions', [])
    if not isinstance(missions, list):
        users[user_id]['missions'] = missions = []

    # Kiểm tra user đã làm chưa (không tính nếu nhiệm vụ chỉ ở trạng thái pending)
    if any(t['id'] == task_id and t['status'] == 'approved' for t in missions):
        await update.callback_query.message.edit_text(
        "⚠️ <b>Bạn đã hoàn thành nhiệm vụ này rồi và đã được admin duyệt.</b>\n\n"
        "⛔ Không thể làm lại nhiệm vụ này.",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Quay lại", callback_data="nhiem_vu")]
            ])
        )
        return



    # Nếu đã có nhiệm vụ này ở trạng thái pending thì không thêm lại, chỉ nhắc gửi ảnh
    existing = next((t for t in missions if t['id'] == task_id and t['status'] == 'pending'), None)
    if not existing:
        users[user_id]['missions'].append({
            'id': task['id'],
            'name': task['name'],
            'reward': task['reward'],
            'status': 'pending'
        })
        save_data()

    # Gửi hướng dẫn
    await update.callback_query.message.edit_text(
        f"🎯 Bạn đã chọn nhiệm vụ: {task['name']}\n"
        f"💰 Tiền thưởng: {task['reward']} VNĐ\n\n"
        "📸 Vui lòng GỬI ẢNH minh chứng vào đây.\n(Chỉ cần gửi ảnh, không cần nhấn nút Gửi)",
    )


async def receive_photo_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)

    await update.callback_query.answer()
    await update.callback_query.message.edit_text(
        "📸 Vui lòng gửi hình ảnh nhiệm vụ vào đây.\n(Chỉ gửi ảnh - Không gửi chữ)",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Quay lại", callback_data="menu")]
        ])
    )



# ----- Admin kiểm tra và duyệt nhiệm vụ -----
async def admin_nhiemvu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    count = 0

    for uid, data in users.items():
        username = data.get('username', 'Không có username')
        for task in data.get('missions', []):
            if task.get('status') == 'submitted' and 'photo_path' in task:
                task_id = task['id']
                keyboard = [
                    [
                        InlineKeyboardButton("✅ Duyệt", callback_data=f"approve_{uid}_{task_id}"),
                        InlineKeyboardButton("❌ Huỷ", callback_data=f"cancel_nhiemvu_{uid}_{task_id}")
                    ]
                ]
                caption = (
                    f"📥 Ảnh nhiệm vụ chờ duyệt\n"
                    f"🆔 User ID: {uid}\n"
                    f"👤 Username: @{username}\n"
                    f"📝 Nhiệm vụ: {task['name']}\n"
                    f"💰 Tiền thưởng: {task['reward']} VNĐ\n\n"
                    f"🛠 Admin chọn Duyệt hoặc Huỷ:"
                )

                try:
                    with open(task['photo_path'], 'rb') as img:
                        await context.bot.send_photo(
                            chat_id=update.effective_chat.id,
                            photo=img,
                            caption=caption,
                            reply_markup=InlineKeyboardMarkup(keyboard)
                        )
                    count += 1
                except Exception as e:
                    print(f"[ERROR] Không thể gửi ảnh nhiệm vụ: {e}")

    if count == 0:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text("📭 Hiện không có nhiệm vụ nào đang chờ xét duyệt.")
    else:
        await update.callback_query.answer("✅ Đã hiển thị danh sách nhiệm vụ đang chờ duyệt.")



# ----- Xét duyệt nhiệm vụ từ admin -----
async def approve_nhiemvu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        data = update.callback_query.data.split('_')
        if len(data) == 3:
            # Duyệt ảnh nộp nhiệm vụ
            _, user_id, task_id = data
            user_id = str(user_id)
            task_id = int(task_id)

            task = next((task for task in users[user_id]['missions'] if task['id'] == task_id), None)

            if task and task['status'] == 'submitted':  # Chỉ duyệt nếu đang ở trạng thái submitted
                task['status'] = 'approved'
                users[user_id]['balance'] += task['reward']
                save_data()

                await context.bot.send_message(
                    chat_id=user_id,
                    text=(
                        f"✅ Nhiệm vụ của bạn đã được duyệt!\n\n"
                        f"📝 Tên: {task['name']}\n"
                        f"💰 Tiền thưởng: {task['reward']} VNĐ\n\n"
                        f"🎉 Số tiền đã được cộng vào tài khoản."
                    ),
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("🔙 Quay lại Menu", callback_data="menu")]
                    ])
                )


                await update.callback_query.answer("✅ Đã duyệt nhiệm vụ.")
                # Sửa nội dung ảnh + bỏ nút
                caption = (
                    f"✅ ĐÃ DUYỆT NHIỆM VỤ\n"
                    f"👤 User: @{users[user_id].get('username', 'Không có username')} (ID: {user_id})\n"
                    f"📝 Nhiệm vụ: {task['name']}\n"
                    f"💰 Tiền thưởng: {task['reward']} VNĐ\n\n"
                    f"🎉 Tiền đã được cộng vào tài khoản người dùng."
                )

                await update.callback_query.edit_message_caption(
                    caption=caption,
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("🔙 Quay lại", callback_data="admin_nhiemvu")]
                    ])
                )

            else:
                await update.callback_query.answer("❌ Nhiệm vụ đã xử lý hoặc không tồn tại.", show_alert=True)

        else:
            await update.callback_query.answer("❌ Dữ liệu không hợp lệ.", show_alert=True)

    except Exception as e:
        await update.callback_query.answer(f"❌ Lỗi: {e}", show_alert=True)


# ----- Huỷ nhiệm vụ từ admin -----
async def cancel_nhiemvu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id, task_id = update.callback_query.data.split('_')[2:4]
        user_id = str(user_id)
        task_id = int(task_id)

        task = next((task for task in users[user_id]['missions'] if task['id'] == task_id), None)

        if task and task['status'] == 'submitted':  # Chỉ hủy nếu đang ở trạng thái submitted
            task['status'] = 'pending'  # Cho phép làm lại
            save_data()

            await context.bot.send_message(
            chat_id=user_id,
            text=(
                f"❌ Nhiệm vụ bạn gửi đã bị từ chối!\n\n"
                f"📝 Tên: {task['name']}\n"
                f"💰 Tiền thưởng: {task['reward']} VNĐ\n\n"
                f"📌 Bạn có thể làm lại nhiệm vụ này."
            ),
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Quay lại Menu", callback_data="menu")]
        ])
        )


            await update.callback_query.answer("❌ Đã huỷ nhiệm vụ.")
            # Sửa nội dung ảnh + bỏ nút
            caption = (
            f"❌ ĐÃ HUỶ NHIỆM VỤ\n"
            f"👤 User: @{users[user_id].get('username', 'Không có username')} (ID: {user_id})\n"
            f"📝 Nhiệm vụ: {task['name']}\n"
            f"💰 Tiền thưởng: {task['reward']} VNĐ\n\n"
            f"📌 User có thể làm lại nhiệm vụ này."
        )

            await update.callback_query.edit_message_caption(
                caption=caption,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 Quay lại", callback_data="admin_nhiemvu")]
                ])
)

        else:
            await update.callback_query.answer("❌ Nhiệm vụ đã xử lý hoặc không tồn tại.", show_alert=True)

    except Exception as e:
        await update.callback_query.answer(f"❌ Lỗi: {e}", show_alert=True)



# Admin menu lệnh /setting_nhiemvu
async def admin_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if user_id != admin_id:
        await update.message.reply_text("⛔ Bạn không có quyền truy cập Admin.")
        return

    keyboard = [
        [InlineKeyboardButton("📝 Xét Duyệt Nhiệm Vụ", callback_data="admin_nhiemvu")],
        [InlineKeyboardButton("✏️ Chỉnh Sửa Nhiệm Vụ", callback_data="edit_nhiemvu")],
        [InlineKeyboardButton("➕ Thêm Nhiệm Vụ", callback_data="add_nhiemvu")],
        [InlineKeyboardButton("📋 Danh Sách Nhiệm Vụ", callback_data="list_nhiemvu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text("🔒 Menu Admin Nhiệm Vụ:", reply_markup=reply_markup)


# ----- Admin tạo Giftcode ----- (with max usage)
async def addgift(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if user_id != admin_id:
        return

    try:
        code = context.args[0].upper()
        amount = int(context.args[1])
        max_usage = int(context.args[2])  # New parameter for max usage

        if code in giftcodes:
            # If giftcode exists, update max_usage and reset used counter
            giftcodes[code]["max_usage"] = max_usage
            giftcodes[code]["used"] = 0
        else:
            giftcodes[code] = {
                "amount": amount,
                "max_usage": max_usage,
                "used": 0
            }

        save_data()
        await update.message.reply_text(f"✅ Tạo giftcode {code} ({amount} VNĐ) với tối đa {max_usage} lần nhập thành công!")
    except Exception as e:
        await update.message.reply_text(f"❌ Cú pháp sai. Dùng: /addgift CODE SỐTIỀN MAX_USAGE\nError: {e}")

# ----- Admin cộng tiền cho user -----
async def addcoin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if user_id != admin_id:
        return

    try:
        target_id = str(context.args[0])
        amount = int(context.args[1])
        if target_id in users:
            users[target_id]['balance'] += amount
            save_data()
            await update.message.reply_text(f"✅ Đã cộng {amount} VNĐ cho {users[target_id]['username']}")
            
            # Gửi thông báo cho người dùng được cộng tiền
            await context.bot.send_message(
                chat_id=target_id,
                text=f"🎉 Bạn đã được Admin + {amount} VNĐ vào số dư, hãy kiểm tra nhé!"
            )
        else:
            await update.message.reply_text("❌ Không tìm thấy người dùng.")
    except:
        await update.message.reply_text("❌ Cú pháp sai. Dùng: /addcoin USERID SỐTIỀN")


# ----- Admin xem danh sách user -----
async def listuser(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if user_id != admin_id:
        return

    text = "👥Chọn user để thao tác:\n\n"
    await update.message.reply_text(text)
    buttons = [
        [InlineKeyboardButton("🔒 Khoá tài khoản", callback_data="lock_user")],
        [InlineKeyboardButton("🔓 Mở tài khoản", callback_data="unlock_user")],
        [InlineKeyboardButton("🚫 Danh sách tài khoản bị khoá", callback_data="list_locked_users")]
    ]
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(buttons))




withdraw_requests = {}  # Đặt biến global lưu yêu cầu rút tiền

# Admin xem yêu cầu rút tiền
async def view_withdraw_requests(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.effective_user.id) != str(admin_id):
        await update.message.reply_text("⛔ Bạn không có quyền truy cập tính năng này.")
        return

    if not withdraw_requests:
        await update.message.reply_text("📭 Hiện không có yêu cầu rút tiền nào đang chờ.")
        return

    for uid, request in withdraw_requests.items():
        if request["status"] != "pending":
            continue

        username = users.get(uid, {}).get("username", "(không rõ)")
        amount = request.get("amount", 0)
        method = request.get("method", "không rõ")
        info = request.get("info", "")

        text = (
            f"💸 <b>YÊU CẦU RÚT TIỀN</b> \n"
            f"👤 User: @{username} ({uid}) \n"
            f"💰 Số tiền: {amount} VNĐ \n"
            f"🏧 Phương thức: {method} \n"
            f"📝 Thông tin: {info}\n"
        )

        buttons = [
            [
                InlineKeyboardButton("✅ Duyệt", callback_data=f"confirm_{uid}"),
                InlineKeyboardButton("❌ Huỷ", callback_data=f"cancel_{uid}")
            ]
        ]

        await update.message.reply_text(
            text,
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(buttons)
        )



# ------ Các menu riêng cho admin quản lý nhiệm vụ ------
async def menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    user_id = str(query.from_user.id)

    # Default fallback
    text = "❌ Lựa chọn không hợp lệ. Vui lòng chọn lại."
    reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Quay lại", callback_data="menu")]])

    if data == "tai_khoan":
        info = users.get(user_id, {})
        text = (
            f"🆔 User ID: {user_id}\n"
            f"👤 Username: @{info.get('username', 'None')}\n"
            f"💰 Số dư: {info.get('balance', 0)} VNĐ"
        )

    elif data == "moi_ban_be":
        invite_link = f"https://t.me/{context.bot.username}?start={user_id}"
        referrals = users.get(user_id, {}).get('referrals', 0)
        text = f"🔗 Link mời (mời 1 bạn +5.000 VNĐ): {invite_link}\n👥 Đã mời: {referrals}"
    elif data == "menu_game":
        game_keyboard = [
            #--[InlineKeyboardButton("🎲 Tài Xỉu cổ điển", callback_data="choi_game")],
            [InlineKeyboardButton("🎰 Nổ Hũ", callback_data="choi_nohu")],
            [InlineKeyboardButton("🎲 Tài Xỉu cấp tốc", callback_data="taixiu_start")],
            [InlineKeyboardButton("🎯 Vòng quay may mắn", callback_data="vongquay_start")],
            [InlineKeyboardButton("🦀 Bầu Cua", callback_data="baucua_start")],
            [InlineKeyboardButton("💣 Đặt Bom – Lật Ô", callback_data="mines_start")],
            [InlineKeyboardButton("🃏 Lật Thẻ May Mắn", callback_data="latbai_start")],
            [InlineKeyboardButton("🎯 Đoán Số May Mắn", callback_data="doanso_start")],

            [InlineKeyboardButton("🃏 Poker Trên & Dưới", callback_data="poker_start")],

            [InlineKeyboardButton("🃏 Xì Dách (Blackjack)", callback_data="bj_start")],
            [InlineKeyboardButton("🔙 Quay lại", callback_data="menu")]
        ]
        await query.answer()
        await query.edit_message_text(
        "🎮 Chọn một trò chơi để bắt đầu:",
        reply_markup=InlineKeyboardMarkup(game_keyboard)
         )
        return

    elif data == "choi_game":
        keyboard = [
            [InlineKeyboardButton("🔵 Tài", callback_data="chon_tai")],
            [InlineKeyboardButton("🔴 Xỉu", callback_data="chon_xiu")],
            [InlineKeyboardButton("🔙 Quay lại", callback_data="menu")]
        ]
        await query.answer()
        await query.edit_message_text(
            f"🎲 Game Tài Xỉu Online\n\n💰 Số dư hiện tại: {users[user_id]['balance']} VNĐ\n\nChọn cược:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    elif data == "nhap_giftcode":
        await query.answer()
        await query.edit_message_text(
            "🎁 Gửi mã Giftcode vào ô chat để nhận tiền!",
            reply_markup=reply_markup
        )
        return
    elif data == "nap_tien":
        await query.answer()
        await query.edit_message_text(
        "💳 <b>NẠP TIỀN</b>\n\n"
        "👉 Vui lòng liên hệ trực tiếp với @nhusexy để được hỗ trợ nạp tiền.\n"
        "🎁 Ưu đãi: <b>Nạp lần đầu +100%</b> x1v!",
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Quay lại", callback_data="menu")]
        ])
    )
        return

    elif data == "rut_tien":
        await withdraw(update, context)
        return

    elif data == "nhiem_vu":
        await nhiemvu_menu(update, context)
        return

    elif data == "menu":
        await start(update, context)
        return

    # ===== ADMIN MENU =====
    elif data == "admin_nhiemvu":
        await admin_nhiemvu(update, context)
        return

    elif data == "add_nhiemvu":
        await add_nhiemvu(update, context)
        return

    elif data == "edit_nhiemvu":
        await edit_nhiemvu(update, context)
        return

    elif data == "list_nhiemvu":
        await list_nhiemvu(update, context)
        return

    # ===== fallback nếu không khớp =====
    await query.answer()
    await query.edit_message_text(text, reply_markup=reply_markup)


# Bắt đầu thêm nhiệm vụ
async def add_nhiemvu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    keyboard = [
        [InlineKeyboardButton("❌ Huỷ", callback_data="cancel_add")]
    ]
    await update.callback_query.edit_message_text(
        "🆔 Nhập mã nhiệm vụ (code):",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return ADD_CODE


async def get_task_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pending_task['code'] = update.message.text.strip()
    keyboard = [
        [InlineKeyboardButton("🔙 Nhập lại mã", callback_data="redo_code")],
        [InlineKeyboardButton("❌ Huỷ", callback_data="cancel_add")]
    ]
    await update.message.reply_text(
        "📝 Nhập tên nhiệm vụ (name):",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return ADD_NAME


async def get_task_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pending_task['name'] = update.message.text.strip()
    await update.message.reply_text("💰 Nhập số tiền thưởng:")
    return ADD_REWARD

async def get_task_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pending_task['name'] = update.message.text.strip()
    keyboard = [
        [InlineKeyboardButton("🔙 Nhập lại tên", callback_data="redo_name")],
        [InlineKeyboardButton("❌ Huỷ", callback_data="cancel_add")]
    ]
    await update.message.reply_text(
        "💰 Nhập số tiền thưởng (reward):",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return ADD_REWARD

async def get_task_reward(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        pending_task['reward'] = int(update.message.text.strip())
        keyboard = [
            [InlineKeyboardButton("🔙 Nhập lại số tiền", callback_data="redo_reward")],
            [InlineKeyboardButton("❌ Huỷ", callback_data="cancel_add")]
        ]
        await update.message.reply_text(
            "📄 Nhập mô tả nhiệm vụ (description):",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return ADD_DESCRIPTION
    except ValueError:
        await update.message.reply_text("❌ Vui lòng nhập số tiền hợp lệ!")
        return ADD_REWARD


async def get_task_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pending_task['description'] = update.message.text.strip()
    text = (
        f"📋 Xác nhận thêm nhiệm vụ:\n\n"
        f"🔖 Mã: {pending_task['code']}\n"
        f"📝 Tên: {pending_task['name']}\n"
        f"💰 Tiền thưởng: {pending_task['reward']} VND\n"
        f"📄 Mô tả: {pending_task['description']}\n\n"
        "✅ Gửi /confirmadd để lưu nhiệm vụ.\n"
        "❌ Hoặc gửi /canceladd để huỷ."
    )
    await update.message.reply_text(text)
    return CONFIRM_ADD

async def confirm_add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tasks = nhiemvu.setdefault('tasks', [])
    new_id = max([task['id'] for task in tasks], default=0) + 1

    tasks.append({
        'id': new_id,
        'code': pending_task['code'],
        'name': pending_task['name'],
        'reward': pending_task['reward'],
        'description': pending_task['description'],
        'active': True
    })
    save_data()
    pending_task.clear()

    await update.message.reply_text("✅ Đã thêm nhiệm vụ thành công!")
    return ConversationHandler.END


async def cancel_add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pending_task.clear()
    await update.message.reply_text("❌ Đã huỷ thêm nhiệm vụ.")
    return ConversationHandler.END

async def redo_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pending_task.pop('code', None)  # <<== Xóa dữ liệu cũ
    await update.callback_query.answer()
    keyboard = [[InlineKeyboardButton("❌ Huỷ", callback_data="cancel_add")]]
    await update.callback_query.edit_message_text("🆔 Nhập lại mã nhiệm vụ:", reply_markup=InlineKeyboardMarkup(keyboard))
    return ADD_CODE

async def redo_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pending_task.pop('name', None)
    await update.callback_query.answer()
    keyboard = [[InlineKeyboardButton("❌ Huỷ", callback_data="cancel_add")]]
    await update.callback_query.edit_message_text("📝 Nhập lại tên nhiệm vụ:", reply_markup=InlineKeyboardMarkup(keyboard))
    return ADD_NAME

async def redo_reward(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pending_task.pop('reward', None)
    await update.callback_query.answer()
    keyboard = [[InlineKeyboardButton("❌ Huỷ", callback_data="cancel_add")]]
    await update.callback_query.edit_message_text("💰 Nhập lại số tiền thưởng:", reply_markup=InlineKeyboardMarkup(keyboard))
    return ADD_REWARD

async def redo_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pending_task.pop('description', None)
    await update.callback_query.answer()
    keyboard = [[InlineKeyboardButton("❌ Huỷ", callback_data="cancel_add")]]
    await update.callback_query.edit_message_text("📄 Nhập lại mô tả nhiệm vụ:", reply_markup=InlineKeyboardMarkup(keyboard))
    return ADD_DESCRIPTION



async def edit_nhiemvu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tasks = nhiemvu.get('tasks', [])
    if not tasks:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text("📋 Không có nhiệm vụ để chỉnh sửa.")
        return ConversationHandler.END

    buttons = [[InlineKeyboardButton(f"{task['id']}: {task['name']}", callback_data=f"edit_{task['id']}")] for task in tasks]
    await update.callback_query.answer()
    await update.callback_query.edit_message_text("✏️ Chọn nhiệm vụ để chỉnh sửa:", reply_markup=InlineKeyboardMarkup(buttons))
    return EDIT_CHOOSE

async def choose_task_to_edit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    task_id = int(update.callback_query.data.split('_')[1])
    pending_edit['task_id'] = task_id
    await update.callback_query.answer()

    keyboard = [
        [InlineKeyboardButton("🔖 Code", callback_data="field_code")],
        [InlineKeyboardButton("📝 Name", callback_data="field_name")],
        [InlineKeyboardButton("💰 Reward", callback_data="field_reward")],
        [InlineKeyboardButton("📄 Description", callback_data="field_description")],
        [InlineKeyboardButton("🔙 Quay lại", callback_data="edit_nhiemvu")]
    ]

    await update.callback_query.edit_message_text(
        "🛠 Chọn trường bạn muốn chỉnh sửa:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return EDIT_FIELD

async def choose_field_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    field_map = {
        'field_code': 'code',
        'field_name': 'name',
        'field_reward': 'reward',
        'field_description': 'description'
    }
    field_key = update.callback_query.data
    if field_key in field_map:
        pending_edit['field'] = field_map[field_key]
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(
            f"✏️ Nhập giá trị mới cho {field_map[field_key]}:"
        )
        return EDIT_NEWVALUE
    else:
        await update.callback_query.answer("❌ Trường không hợp lệ.")
        return EDIT_FIELD


async def choose_field_to_edit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    field = update.message.text.strip().lower()
    if field not in ['code', 'name', 'reward', 'description']:
        await update.message.reply_text("❌ Trường không hợp lệ! Nhập lại: code, name, reward hoặc description")
        return EDIT_FIELD
    pending_edit['field'] = field
    await update.message.reply_text(f"✏️ Nhập giá trị mới cho {field}:")
    return EDIT_NEWVALUE

async def get_new_value(update: Update, context: ContextTypes.DEFAULT_TYPE):
    value = update.message.text.strip()
    task = next((t for t in nhiemvu.get('tasks', []) if t['id'] == pending_edit['task_id']), None)
    if not task:
        await update.message.reply_text("❌ Không tìm thấy nhiệm vụ.")
        return ConversationHandler.END
    if pending_edit['field'] == 'reward':
        try:
            value = int(value)
        except ValueError:
            await update.message.reply_text("❌ Tiền thưởng phải là số!")
            return EDIT_NEWVALUE
    task[pending_edit['field']] = value
    save_data()
    pending_edit.clear()
    await update.message.reply_text("✅ Đã lưu chỉnh sửa nhiệm vụ.")
    return ConversationHandler.END



# ----- Xử lý khi bấm "➕ Thêm Nhiệm Vụ" -----
async def add_nhiemvu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    keyboard = [
        [InlineKeyboardButton("❌ Huỷ", callback_data="cancel_add")]
    ]
    await update.callback_query.edit_message_text(
        "🆔 Nhập mã nhiệm vụ (code):",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return ADD_CODE


# ----- Xử lý khi bấm "✏️ Chỉnh Sửa Nhiệm Vụ" -----
async def edit_nhiemvu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    tasks = nhiemvu.get('tasks', [])

    if not tasks:
        await query.answer()
        await query.edit_message_text(
            "📋 Hiện chưa có nhiệm vụ nào để chỉnh sửa.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Quay lại", callback_data="setting_nhiemvu")]])
        )
        return

    keyboard = []
    for task in tasks:
        keyboard.append([
            InlineKeyboardButton(f"{task['id']}: {task['name']}", callback_data=f"edit_{task['id']}")
        ])
    
    keyboard.append([InlineKeyboardButton("🔙 Quay lại", callback_data="setting_nhiemvu")])

    await query.answer()
    await query.edit_message_text(
        "✏️ Chọn nhiệm vụ bạn muốn chỉnh sửa:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# Khi user bấm nút "Gửi ảnh" nhiệm vụ
async def receive_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    username = update.effective_user.username or "Không có Username"

    print(f"[DEBUG] User gửi ảnh - ID: {user_id} - Username: @{username}")
    print(f"[DEBUG] Nội dung message: {update.message}")

    if user_id not in users:
        print("[DEBUG] User chưa có trong hệ thống.")
        return

    if 'missions' not in users[user_id]:
        users[user_id]['missions'] = []

    # Kiểm tra có ảnh không
    if update.message and update.message.photo:
        os.makedirs('photos', exist_ok=True)
        photo_file = await update.message.photo[-1].get_file()
        photo_path = f"photos/{user_id}_{random.randint(1000, 9999)}.jpg"
        await photo_file.download_to_drive(photo_path)
        print(f"[DEBUG] Ảnh được lưu tại: {photo_path}")

        # Tìm nhiệm vụ đang pending
        task = next((t for t in users[user_id]['missions'] if t['status'] == 'pending'), None)
        if not task:
            await update.message.reply_text("❌ Không tìm thấy nhiệm vụ đang chờ gửi ảnh.")
            print("[DEBUG] Không tìm thấy nhiệm vụ pending.")
            return

        task['status'] = 'submitted'
        task['photo_path'] = photo_path
        save_data()
        task_id = task['id']

        keyboard = [
            [
                InlineKeyboardButton("✅ Duyệt", callback_data=f"approve_{user_id}_{task_id}"),
                InlineKeyboardButton("❌ Huỷ", callback_data=f"cancel_nhiemvu_{user_id}_{task_id}")
            ]
        ]

        caption = (
            f"📥 Ảnh mới từ người dùng\n"
            f"🆔 User ID: {user_id}\n"
            f"👤 Username: @{username}\n"
            f"📝 Nhiệm vụ: {task['name']}\n"
            f"💰 Tiền thưởng: {task['reward']} VNĐ\n\n"
            "🛠 Chọn Duyệt hoặc Huỷ:"
        )

        try:
            with open(photo_path, 'rb') as img:
                await context.bot.send_photo(
            chat_id=int(admin_id),
            photo=img,
            caption=caption,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
            print("[DEBUG] Ảnh đã gửi cho admin.")
        except Exception as e:
            print(f"[ERROR] Gửi ảnh admin lỗi: {e}")

# Phản hồi cho user vẫn diễn ra dù admin nhận hay không
        await update.message.reply_text(
         "✅ Ảnh đã được gửi cho admin xét duyệt.\n📌 Vui lòng đợi phản hồi.",
             reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Quay lại Menu", callback_data="menu")]
        ])
    )

    else:
        await update.message.reply_text("❌ Vui lòng gửi ảnh hợp lệ.")
        print("[DEBUG] Không nhận được ảnh trong message.")


# ----- Xử lý khi bấm "📋 Danh Sách Nhiệm Vụ" -----
async def list_nhiemvu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    tasks = nhiemvu.get('tasks', [])
    if not tasks:
        await query.answer()
        await query.edit_message_text(
            "📋 Hiện chưa có nhiệm vụ nào.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Quay lại", callback_data="setting_nhiemvu")]])
        )
        return

    text = "📋 Danh sách nhiệm vụ Admin:\n\n"
    keyboard = []

    for task in tasks:
        status = "🟢 Đang Mở" if task.get('active', True) else "🔴 Đã Ẩn"
        text += (
            f"🔖 Mã: {task.get('code', '')}\n"
            f"📝 Tên: {task.get('name', '')}\n"
            f"💰 Tiền thưởng: {task.get('reward', 0)} VNĐ\n"
            f"📄 Mô tả: {task.get('description', 'Không có mô tả')}\n"
            f"📶 Trạng thái: {status}\n\n"
        )
        # Thêm 3 nút cho mỗi nhiệm vụ
        keyboard.append([
            InlineKeyboardButton("✏️ Sửa", callback_data=f"edit_{task['id']}"),
            InlineKeyboardButton("🔄 Ẩn/Hiện", callback_data=f"toggle_{task['id']}"),
            InlineKeyboardButton("🗑️ Xoá", callback_data=f"delete_{task['id']}")
        ])

    # Thêm nút quay lại
    keyboard.append([InlineKeyboardButton("🔙 Quay lại", callback_data="setting_nhiemvu")])

    await query.answer()
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )



async def toggle_nhiemvu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    task_id = int(query.data.split('_')[1])

    tasks = nhiemvu.get('tasks', [])
    task = next((t for t in tasks if t['id'] == task_id), None)

    if not task:
        await query.answer()
        await query.edit_message_text("❌ Không tìm thấy nhiệm vụ cần đổi trạng thái.")
        return

    task['active'] = not task.get('active', True)
    save_data()

    status = "✅ Đang Hiện" if task['active'] else "🚫 Đang Ẩn"
    await query.answer()
    await query.edit_message_text(f"🔄 Đã đổi trạng thái nhiệm vụ thành: {status}",
    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Quay lại", callback_data="list_nhiemvu")]]))

async def delete_nhiemvu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    task_id = int(query.data.split('_')[1])

    tasks = nhiemvu.get('tasks', [])
    task = next((t for t in tasks if t['id'] == task_id), None)

    if not task:
        await query.answer()
        await query.edit_message_text("❌ Không tìm thấy nhiệm vụ cần xóa.")
        return

    nhiemvu['tasks'] = [t for t in tasks if t['id'] != task_id]
    save_data()

    await query.answer()
    await query.edit_message_text("✅ Đã xóa nhiệm vụ thành công!", reply_markup=InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 Quay lại", callback_data="list_nhiemvu")]
    ]))


# ----- Xử lý menu Rút Tiền (chọn mệnh giá) -----
async def withdraw(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = str(query.from_user.id)
     # 🚫 Kiểm tra nếu tài khoản bị khoá
    if users.get(user_id, {}).get("locked", False):
        await query.answer()
        await query.edit_message_text("🚫 Tài khoản của bạn đã bị khóa. Không thể sử dụng chức năng rút tiền.")
        return
    # Hiển thị các mức rút tiền
    keyboard = [
        [
            InlineKeyboardButton("💵 100K", callback_data="withdraw_100000"),
            InlineKeyboardButton("💵 200K", callback_data="withdraw_200000"),
            InlineKeyboardButton("💵 300K", callback_data="withdraw_300000")
        ],
        [
            InlineKeyboardButton("💵 500K", callback_data="withdraw_500000"),
            InlineKeyboardButton("💵 1.000K", callback_data="withdraw_1000000")
        ],
        [
            InlineKeyboardButton("💵 2.000K", callback_data="withdraw_2000000"),
            InlineKeyboardButton("💵 5.000K", callback_data="withdraw_5000000")
        ],
        [
            InlineKeyboardButton("💵 10.000K", callback_data="withdraw_10000000")
        ],
        [
            InlineKeyboardButton("🔙 Quay lại", callback_data="menu")
        ]
    ]

    await query.answer()
    await query.edit_message_text(
        "💵 Chọn số tiền bạn muốn rút:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# Xử lý "Xác nhận" yêu cầu rút tiền
async def confirm_withdraw_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = str(query.from_user.id)

    if user_id != admin_id:
        return

    uid = query.data.split('_')[1]  # Lấy user ID từ callback_data
    if uid in withdraw_requests:
        req = withdraw_requests.pop(uid)
        amount = req['amount']

        # Tạo nút "Quay lại"
        keyboard = [
            [InlineKeyboardButton("🔙 Quay lại", callback_data="menu")]
        ]
        # Thông báo cho người dùng
        await context.bot.send_message(
            chat_id=uid,
            text=f"✅ Yêu cầu rút {amount:,} VNĐ đã được xác nhận. Tiền sẽ được chuyển theo phương thức {req['method'].upper()}.",
            reply_markup=InlineKeyboardMarkup(keyboard)  
        )

        # Thông báo cho admin
        await context.bot.send_message(
            chat_id=admin_id,
            text=f"✅ Đã xác nhận yêu cầu rút tiền của @{users[uid]['username']} (ID: {uid}). Số tiền {amount:,} VNĐ đã được trừ khỏi tài khoản."
        )

        await query.answer()
        await query.edit_message_text("✅ Yêu cầu rút tiền đã được xác nhận thành công.")

        # Cập nhật lại danh sách yêu cầu
        save_data()

# Xử lý "Hủy" yêu cầu rút tiền (hoàn tiền vào số dư)
async def cancel_withdraw_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = str(query.from_user.id)

    if user_id != admin_id:
        return

    uid = query.data.split('_')[1]  # Lấy user ID từ callback_data
    if uid in withdraw_requests:
        req = withdraw_requests.pop(uid)
        amount = req['amount']

        # Hoàn tiền vào số dư người dùng
        users[uid]['balance'] += amount
        save_data()


        # Tạo nút "Quay lại"
        keyboard = [
            [InlineKeyboardButton("🔙 Quay lại", callback_data="menu")]
        ]

        # Gửi thông báo cho người dùng + kèm nút quay lại
        await context.bot.send_message(
            chat_id=uid,
            text=f"❌ Yêu cầu rút {amount:,} VNĐ của bạn đã bị hủy. Số tiền đã được hoàn trả vào tài khoản của bạn.",
            reply_markup=InlineKeyboardMarkup(keyboard)  # <<<< GẮN THÊM CÁI NÀY
        )
        # Thông báo cho admin
        await context.bot.send_message(
            chat_id=admin_id,
            text=f"❌ Đã hủy yêu cầu rút tiền của @{users[uid]['username']} (ID: {uid}). Số tiền {amount:,} VNĐ đã được hoàn trả."
        )
    
        await query.answer()
        await query.edit_message_text("❌ Yêu cầu rút tiền đã bị hủy.")
        # Hiển thị lại menu admin với nút "Quay lại"
        await query.message.reply_text(
            "Bạn có thể quay lại hoặc kiểm tra các yêu cầu khác.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

        # Cập nhật lại danh sách yêu cầu
        save_data()

# ----- Xử lý chọn mệnh giá rút tiền -----
async def select_withdraw_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = str(query.from_user.id)
    # 🚫 Kiểm tra nếu tài khoản bị khoá
    if users.get(user_id, {}).get("locked", False):
        await query.answer()
        await query.edit_message_text("🚫 Tài khoản của bạn đã bị khóa. Không thể thực hiện rút tiền.")
        return
        # Kiểm tra nếu đã có yêu cầu rút tiền đang chờ
    if user_id in withdraw_requests and withdraw_requests[user_id].get("status") == "pending":
        await query.answer()
        await query.edit_message_text(
            "❌ Bạn đang có 1 yêu cầu rút tiền đang chờ duyệt.\n\n📌 Vui lòng đợi Admin xử lý trước khi tạo yêu cầu mới.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Quay lại", callback_data="menu")]])
        )
        return

    amount = int(query.data.split('_')[1])  # Ví dụ: withdraw_100000 ➔ lấy 100000

    if users[user_id]['balance'] < amount:  
        # Không đủ số dư
        keyboard = [[InlineKeyboardButton("🔙 Quay lại", callback_data="rut_tien")]]
        await query.answer()
        await query.edit_message_text(
            "❌ Số dư của bạn không đủ để rút mệnh giá này!",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    # Đủ số dư: Lưu số tiền định rút vào context
    context.user_data['withdraw_amount'] = amount

    # Hiện chọn phương thức rút
    keyboard = [
        [
            InlineKeyboardButton("🏦 Banking", callback_data="withdraw_banking"),
            InlineKeyboardButton("📱 Momo", callback_data="withdraw_momo")
        ],
        [InlineKeyboardButton("🔙 Quay lại", callback_data="rut_tien")]
    ]
    await query.answer()
    await query.edit_message_text(
        f"✅ Bạn đã chọn rút {amount:,} VNĐ\n\nChọn phương thức nhận tiền:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ----- Xử lý chọn phương thức Banking hoặc Momo -----
async def select_withdraw_method(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = str(query.from_user.id)

    method = query.data.split('_')[1]  # banking hoặc momo
    context.user_data['withdraw_method'] = method

    if method == "banking":
        await query.answer()
        await query.edit_message_text(
            "🏦 Vui lòng gửi thông tin rút tiền theo mẫu:\n\n"
            "**Họ tên - Số tài khoản - Tên ngân hàng**\n\n"
            "Ví dụ: Nguyễn Văn A - 123456789 - Vietcombank",
        )
    else:  # momo
        await query.answer()
        await query.edit_message_text(
            "📱 Vui lòng gửi số điện thoại tài khoản Momo để nhận tiền!",
        )

# ----- Xử lý nhập thông tin rút tiền -----
async def handle_withdraw_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    message = update.message.text

    if 'withdraw_amount' in context.user_data and 'withdraw_method' in context.user_data:
        amount = context.user_data.pop('withdraw_amount')
        method = context.user_data.pop('withdraw_method')

        # Kiểm tra số dư 1 lần nữa cho chắc chắn
        if users[user_id]['balance'] < amount:
            await update.message.reply_text("❌ Số dư của bạn không đủ để thực hiện rút tiền này.")
            return

        # Trừ tiền ngay khi gửi yêu cầu
        users[user_id]['balance'] -= amount

        # Ghi yêu cầu vào withdraw_requests
        withdraw_requests[user_id] = {
            'amount': amount,
            'method': method,
            'info': message,
            'status': 'pending'  # trạng thái chờ duyệt
        }
        save_data()

        await update.message.reply_text(
            f"✅ Đã gửi yêu cầu rút {amount:,} VNĐ qua {method.upper()} thành công!\nChờ admin xét duyệt."
        )
        await context.bot.send_message(
            chat_id=admin_id,
            text=(
                f"📥 YÊU CẦU RÚT TIỀN MỚI\n"
                f"👤 User: @{users[user_id]['username']} (ID: {user_id})\n"
                f"💰 Số tiền: {amount:,} VNĐ\n"
                f"📲 Phương thức: {method.upper()}\n"
                f"📝 Thông tin tài khoản: {message}"
            )
        )
    else:
        await handle_text(update, context)  # Nếu không phải đang rút thì xử lý như nhập giftcode


# ----- Xử lý chọn Tài hoặc Xỉu -----
async def choose_tx(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    user_id = str(query.from_user.id)

    context.user_data['tx_choice'] = "tai" if data == "chon_tai" else "xiu"

    # Hiện chọn mức cược
    keyboard = [
        [
            InlineKeyboardButton("10K", callback_data="bet_10000"),
            InlineKeyboardButton("20K", callback_data="bet_20000"),
            InlineKeyboardButton("50K", callback_data="bet_50000")
        ],
        [
            InlineKeyboardButton("100K", callback_data="bet_100000"),
            InlineKeyboardButton("200K", callback_data="bet_200000"),
            InlineKeyboardButton("500K", callback_data="bet_500000")
        ],
        [InlineKeyboardButton("🔙 Quay lại", callback_data="choi_game")]
    ]
    await query.answer()
    await query.edit_message_text("💵 Chọn số tiền cược:", reply_markup=InlineKeyboardMarkup(keyboard))

# ----- Xử lý cược và quay game -----
async def play_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = str(query.from_user.id)

    bet_amount = int(query.data.split('_')[1])
    choice = context.user_data.get('tx_choice', None)

    if choice is None:
        await query.answer("Lỗi: Chưa chọn Tài/Xỉu", show_alert=True)
        return

    if users[user_id]['balance'] < bet_amount:
        await query.answer("Không đủ số dư!", show_alert=True)
        return

    # Quay xúc xắc
    dice = [random.randint(1, 6) for _ in range(3)]
    total = sum(dice)

    result = "tai" if total >= 11 else "xiu"
    win = (choice == result)

    change = bet_amount if win else -bet_amount
    users[user_id]['balance'] += change

    # Lưu lịch sử
    history.setdefault(user_id, []).append({
        "choice": choice,
        "total": total,
        "dice": dice,
        "result": result,
        "change": change
    })

    save_data()

    status = "✅ Thắng" if win else "❌ Thua"
    icon = "➕" if change > 0 else "➖"

    text = (
        f"🎲 Xúc xắc: {dice} ➔ {total}\n\n"
        f"{status} {icon}{abs(change)} VNĐ\n"
        f"💰 Số dư hiện tại: {users[user_id]['balance']} VNĐ"
    )

    keyboard = [
        [InlineKeyboardButton("🎲 Tiếp tục", callback_data="choi_game")],
        [InlineKeyboardButton("🏠 Trang chủ", callback_data="menu")],
        [InlineKeyboardButton("📜 Lịch sử cược", callback_data="lich_su")]
    ]

    await query.answer()
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

# ----- Hiển thị lịch sử cược -----
async def show_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = str(query.from_user.id)

    records = history.get(user_id, [])
    if not records:
        await query.answer()
        await query.edit_message_text("📜 Bạn chưa có lịch sử cược nào.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Quay lại", callback_data="menu")]]))
        return

    text = "📜 Lịch sử cược:\n\n"
    for rec in records[-10:][::-1]:  # Hiển thị 10 lần gần nhất
        res = "Thắng" if rec['change'] > 0 else "Thua"
        text += f"{res} | {rec['choice'].capitalize()} ➔ {rec['total']} ({rec['dice']}) | {'+' if rec['change']>0 else ''}{rec['change']} VNĐ\n"

    await query.answer()
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Quay lại", callback_data="menu")]]))



BET_LEVELS = [2000, 5000, 10000, 20000, 50000, 100000, 200000, 500000, 1000000, 2000000]
SLOTS = ['🍒', '🍋', '🔔', '💎', '💰']


async def nohu_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    context.user_data['nohu'] = {
        'bet_index': 2  # mặc định chọn 10K
    }
    await send_nohu_ui(update.callback_query, context)


async def send_nohu_ui(call, context):
    user_id = str(call.from_user.id)
    bet_index = context.user_data['nohu']['bet_index']
    bet = BET_LEVELS[bet_index]
    balance = users[user_id]['balance']
    symbols = random.choices(SLOTS, k=3)

    context.user_data['nohu']['last_symbols'] = symbols

    keyboard = [
        [InlineKeyboardButton("➖", callback_data="nohu_decrease"),
         InlineKeyboardButton("🎯 Quay", callback_data="nohu_spin"),
         InlineKeyboardButton("➕", callback_data="nohu_increase")],
        [InlineKeyboardButton("🏠 Menu chính", callback_data="menu")]
    ]

    text = (
        f"🎰 <b>NỔ HŨ</b> 🎰\n\n"
        f"{' | '.join(symbols)}\n\n"
        f"💵 Cược: {bet:,} VNĐ\n"
        f"💼 Số dư: {balance:,} VNĐ"
    )
    await call.edit_message_text(
        text=text,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def nohu_change_bet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    action = update.callback_query.data
    bet_index = context.user_data['nohu']['bet_index']

    if action == "nohu_increase" and bet_index < len(BET_LEVELS) - 1:
        context.user_data['nohu']['bet_index'] += 1
    elif action == "nohu_decrease" and bet_index > 0:
        context.user_data['nohu']['bet_index'] -= 1

    await send_nohu_ui(update.callback_query, context)


async def nohu_spin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.callback_query.from_user.id)
    bet_index = context.user_data['nohu']['bet_index']
    bet = BET_LEVELS[bet_index]

    if users[user_id]['balance'] < bet:
        await update.callback_query.answer("❌ Không đủ số dư!", show_alert=True)
        return

    users[user_id]['balance'] -= bet

    result = random.choices(SLOTS, k=3)
    context.user_data['nohu']['last_symbols'] = result

    # Tính thưởng
    reward = 0
    if result[0] == result[1] == result[2]:
        reward = bet * 10
    elif result[0] == result[1] or result[1] == result[2] or result[0] == result[2]:
        reward = bet * 2

    users[user_id]['balance'] += reward
    save_data()

    keyboard = [
        [InlineKeyboardButton("➖", callback_data="nohu_decrease"),
         InlineKeyboardButton("🎯 Quay", callback_data="nohu_spin"),
         InlineKeyboardButton("➕", callback_data="nohu_increase")],
        [InlineKeyboardButton("🏠 Menu chính", callback_data="menu")]
    ]

    text = (
        f"🎰 <b>NỔ HŨ</b> 🎰\n\n"
        f"{' | '.join(result)}\n\n"
        f"{'🎉 <b>BẠN THẮNG!</b>' if reward else '😢 <b>Không trúng!</b>'}\n"
        f"💵 Cược: {bet:,} VNĐ\n"
        f"💰 Thưởng: {reward:,} VNĐ\n"
        f"💼 Số dư: {users[user_id]['balance']:,} VNĐ"
    )
    await update.callback_query.edit_message_text(
        text=text,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


card_order = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
card_values = {
    '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7,
    '8': 8, '9': 9, '10': 10, 'J': 10, 'Q': 10, 'K': 10, 'A': 11
}
suits = ['♠️', '♥️', '♦️', '♣️']
BET_LEVELS = [2000, 5000, 10000, 20000, 50000, 100000, 200000, 500000, 1000000, 2000000]


async def blackjack_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    context.user_data['blackjack'] = {
        'bet_index': 2,  # 10k mặc định
        'player': [],
        'dealer': [],
        'finished': False
    }
    await deal_blackjack(update, context)


async def deal_blackjack(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bj = context.user_data['blackjack']
    bj['player'] = [draw_card(), draw_card()]
    bj['dealer'] = [draw_card()]
    bj['finished'] = False
    await render_blackjack(update, context)


async def blackjack_hit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bj = context.user_data['blackjack']
    if bj['finished']:
        return
    bj['player'].append(draw_card())
    if calc_total(bj['player']) > 21:
        bj['finished'] = True
    await render_blackjack(update, context)


async def blackjack_stand(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bj = context.user_data['blackjack']
    if bj['finished']:
        return
    while calc_total(bj['dealer']) < 17:
        bj['dealer'].append(draw_card())
    bj['finished'] = True
    await render_blackjack(update, context)


async def blackjack_increase(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bj = context.user_data['blackjack']
    if bj['bet_index'] < len(BET_LEVELS) - 1:
        bj['bet_index'] += 1
    await render_blackjack(update, context)

async def blackjack_decrease(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bj = context.user_data['blackjack']
    if bj['bet_index'] > 0:
        bj['bet_index'] -= 1
    await render_blackjack(update, context)


def draw_card():
    return f"{random.choice(suits)} {random.choice(card_order)}"

def calc_total(cards):
    total = 0
    aces = 0
    for card in cards:
        val = card.split()[1]
        total += card_values[val]
        if val == 'A':
            aces += 1
    while total > 21 and aces:
        total -= 10
        aces -= 1
    return total

async def render_blackjack(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    bj = context.user_data['blackjack']
    bet = BET_LEVELS[bj['bet_index']]
    balance = users[user_id]['balance']

    player_total = calc_total(bj['player'])
    dealer_total = calc_total(bj['dealer']) if bj['finished'] else "?"
    result = ""

    if bj['finished']:
        if player_total > 21:
            result = f"❌ Bạn quá 21 điểm! Mất {bet:,} VNĐ"
            users[user_id]['balance'] -= bet
        elif dealer_total > 21 or player_total > dealer_total:
            result = f"✅ Bạn thắng! Nhận {bet:,} VNĐ"
            users[user_id]['balance'] += bet
        elif player_total == dealer_total:
            result = "🤝 Hòa! Không mất gì"
        else:
            result = f"❌ Thua! Mất {bet:,} VNĐ"
            users[user_id]['balance'] -= bet
        save_data()

    text = (
        "🃏 <b>BLACKJACK - XÌ DÁCH</b>\n\n"
        f"👤 Bạn: {' '.join(bj['player'])}  ➤ Tổng: {player_total}\n"
        f"🤖 Nhà cái: {' '.join(bj['dealer'])}  ➤ Tổng: {dealer_total}\n\n"
        f"💵 Cược: {bet:,} VNĐ\n"
        f"💼 Số dư: {users[user_id]['balance']:,} VNĐ\n"
    )
    if result:
        text += f"\n<b>{result}</b>"

    keyboard = []

# Nếu ván đang chơi
    if not bj['finished']:
        keyboard.append([
        InlineKeyboardButton("➕ Rút bài", callback_data="bj_hit"),
        InlineKeyboardButton("✋ Dừng", callback_data="bj_stand")
    ])
        keyboard.append([
        InlineKeyboardButton("➖", callback_data="bj_decrease"),
        InlineKeyboardButton("🔁 Chơi lại", callback_data="bj_start"),
        InlineKeyboardButton("➕", callback_data="bj_increase")
    ])
    else:
        keyboard.append([
        InlineKeyboardButton("🔁 Chơi lại", callback_data="bj_start")
    ])

    keyboard.append([InlineKeyboardButton("🏠 Menu", callback_data="menu")])


    try:
        await update.callback_query.edit_message_text(
            text=text,
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    except:
        await update.message.reply_text(
            text=text,
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )


DICE_EMOJI = {1: "⚀", 2: "⚁", 3: "⚂", 4: "⚃", 5: "⚄", 6: "⚅"}
BET_LEVELS = [2000, 5000, 10000, 20000, 50000, 100000, 200000, 500000, 1000000, 2000000]

async def taixiu_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['taixiu'] = {
        'bet_index': 2,  # 10K mặc định
        'last_result': None
    }
    await render_taixiu(update, context)


async def taixiu_increase(update: Update, context: ContextTypes.DEFAULT_TYPE):
    game = context.user_data['taixiu']
    if game['bet_index'] < len(BET_LEVELS) - 1:
        game['bet_index'] += 1
    await render_taixiu(update, context)

async def taixiu_decrease(update: Update, context: ContextTypes.DEFAULT_TYPE):
    game = context.user_data['taixiu']
    if game['bet_index'] > 0:
        game['bet_index'] -= 1
    await render_taixiu(update, context)


async def taixiu_play(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    game = context.user_data.get('taixiu', {})
    bet = BET_LEVELS[game.get('bet_index', 2)]
    choice = update.callback_query.data  # taixiu_tai / taixiu_xiu

    if users[user_id]['balance'] < bet:
        await update.callback_query.answer("❌ Không đủ số dư!", show_alert=True)
        return

    users[user_id]['balance'] -= bet
    dice = [random.randint(1, 6) for _ in range(3)]
    total = sum(dice)
    is_tai = total >= 11
    user_pick_tai = (choice == "taixiu_tai")
    win = (is_tai == user_pick_tai)

    reward = bet * 2 if win else 0
    if win:
        users[user_id]['balance'] += reward

    game['last_result'] = {
        'dice': dice,
        'total': total,
        'result': 'TÀI' if is_tai else 'XỈU',
        'win': win,
        'choice': 'TÀI' if user_pick_tai else 'XỈU',
        'reward': reward
    }
    save_data()
    await render_taixiu(update, context)


async def render_taixiu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    game = context.user_data.get('taixiu', {})
    bet = BET_LEVELS[game.get('bet_index', 2)]
    balance = users[user_id]['balance']
    result = game.get('last_result')

    text = "🎲 <b>TÀI XỈU</b>\n\n"

    if result:
        dice_text = ' + '.join(DICE_EMOJI[d] for d in result['dice'])
        text += (
            f"🎲 Kết quả: {dice_text} = {result['total']}\n"
            f"📢 Kết luận: <b>{result['result']}</b>\n"
            f"🧠 Bạn chọn: <b>{result['choice']}</b>\n"
            f"{'✅ Thắng!' if result['win'] else '❌ Thua!'} "
            f"{'Nhận: ' + str(result['reward']) + ' VNĐ' if result['win'] else f'Mất: {bet:,} VNĐ'}\n\n"
        )

    text += f"💵 Cược: {bet:,} VNĐ\n💼 Số dư: {balance:,} VNĐ"

    keyboard = [
        [InlineKeyboardButton("🔴 TÀI", callback_data="taixiu_tai"),
         InlineKeyboardButton("🔵 XỈU", callback_data="taixiu_xiu")],
        [InlineKeyboardButton("➖", callback_data="taixiu_decrease"),
         InlineKeyboardButton("🔁 Chơi lại", callback_data="taixiu_start"),
         InlineKeyboardButton("➕", callback_data="taixiu_increase")],
        [InlineKeyboardButton("🏠 Menu", callback_data="menu")]
    ]

    try:
        await update.callback_query.edit_message_text(
            text=text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard)
        )
    except:
        await update.message.reply_text(
            text=text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard)
        )


BET_LEVELS = [2000, 5000, 10000, 20000, 50000, 100000, 200000, 500000, 1000000, 2000000]
async def vongquay_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['vongquay'] = {
        'bet_index': 2,
        'last_result': None
    }
    await render_vongquay(update, context)

async def vongquay_increase(update: Update, context: ContextTypes.DEFAULT_TYPE):
    game = context.user_data['vongquay']
    if game['bet_index'] < len(BET_LEVELS) - 1:
        game['bet_index'] += 1
    await render_vongquay(update, context)

async def vongquay_decrease(update: Update, context: ContextTypes.DEFAULT_TYPE):
    game = context.user_data['vongquay']
    if game['bet_index'] > 0:
        game['bet_index'] -= 1
    await render_vongquay(update, context)

async def vongquay_spin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    game = context.user_data.get('vongquay', {})
    bet = BET_LEVELS[game.get('bet_index', 2)]

    if users[user_id]['balance'] < bet:
        await update.callback_query.answer("❌ Không đủ số dư!", show_alert=True)
        return

    users[user_id]['balance'] -= bet

    multipliers = [0, 1, 2, 5, 10, 20]
    weights = [0.4, 0.25, 0.2, 0.1, 0.04, 0.01]  # xác suất quay ra
    result = random.choices(multipliers, weights)[0]
    reward = bet * result

    if reward > 0:
        users[user_id]['balance'] += reward

    game['last_result'] = {
        'multiplier': result,
        'reward': reward,
        'bet': bet
    }

    save_data()
    await render_vongquay(update, context)

async def render_vongquay(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    game = context.user_data.get('vongquay', {})
    bet = BET_LEVELS[game.get('bet_index', 2)]
    balance = users[user_id]['balance']
    result = game.get('last_result')

    text = "🎯 <b>VÒNG QUAY MAY MẮN</b>\n\n"

    if result:
        text += (
            f"🎡 Kết quả: x{result['multiplier']}\n"
            f"{'✅ Bạn thắng' if result['multiplier'] > 0 else '❌ Bạn thua'}\n"
            f"{'💰 Nhận: ' + str(result['reward']) + ' VNĐ' if result['reward'] else f'💸 Mất: {bet:,} VNĐ'}\n\n"
        )

    text += f"💵 Cược: {bet:,} VNĐ\n💼 Số dư: {balance:,} VNĐ"

    keyboard = [
        [InlineKeyboardButton("🎡 QUAY", callback_data="vongquay_spin")],
        [InlineKeyboardButton("➖", callback_data="vongquay_decrease"),
         InlineKeyboardButton("🔁 Chơi lại", callback_data="vongquay_start"),
         InlineKeyboardButton("➕", callback_data="vongquay_increase")],
        [InlineKeyboardButton("🏠 Menu", callback_data="menu")]
    ]

    try:
        await update.callback_query.edit_message_text(
            text=text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard)
        )
    except:
        await update.message.reply_text(
            text=text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard)
        )


BET_LEVELS = [2000, 5000, 10000, 20000, 50000, 100000, 200000, 500000, 1000000, 2000000]
BAUCUA_SYMBOLS = ["🐟", "🐔", "🦀", "🍐", "🐎", "🎯"]

async def baucua_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['baucua'] = {
        'selected': [],
        'bet_index': 2,
        'last_result': None
    }
    await render_baucua(update, context)


async def baucua_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['baucua'] = {
        'selected': [],
        'bet_index': 2,
        'last_result': None
    }
    await render_baucua(update, context)

async def baucua_toggle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    symbol = update.callback_query.data.split("_")[-1]
    game = context.user_data.get('baucua', {})
    selected = game.get('selected', [])
    if symbol in selected:
        selected.remove(symbol)
    else:
        if len(selected) < 3:
            selected.append(symbol)
    await render_baucua(update, context)


async def baucua_increase(update: Update, context: ContextTypes.DEFAULT_TYPE):
    game = context.user_data['baucua']
    if game['bet_index'] < len(BET_LEVELS) - 1:
        game['bet_index'] += 1
    await render_baucua(update, context)

async def baucua_decrease(update: Update, context: ContextTypes.DEFAULT_TYPE):
    game = context.user_data['baucua']
    if game['bet_index'] > 0:
        game['bet_index'] -= 1
    await render_baucua(update, context)

async def baucua_play(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    game = context.user_data['baucua']
    bet = BET_LEVELS[game['bet_index']]
    selected = game['selected']

    if not selected:
        await update.callback_query.answer("❌ Bạn phải chọn ít nhất 1 hình!", show_alert=True)
        return

    if users[user_id]['balance'] < bet:
        await update.callback_query.answer("❌ Không đủ số dư!", show_alert=True)
        return

    users[user_id]['balance'] -= bet

    result = [random.choice(BAUCUA_SYMBOLS) for _ in range(3)]
    reward = 0
    for sym in selected:
        reward += result.count(sym) * bet

    if reward > 0:
        users[user_id]['balance'] += reward

    game['last_result'] = {
        'result': result,
        'reward': reward,
        'bet': bet,
        'selected': selected.copy()
    }
    save_data()
    game['selected'] = []
    await render_baucua(update, context)

async def render_baucua(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    game = context.user_data.get('baucua', {})
    bet = BET_LEVELS[game.get('bet_index', 2)]
    balance = users[user_id]['balance']
    selected = game.get('selected', [])
    result = game.get('last_result')

    text = "<b>🦀 BẦU CUA TÔM CÁ</b>\n\n"
    if result:
        res_str = " | ".join(result['result'])
        text += (
            f"🎲 Kết quả: {res_str}\n"
            f"🧠 Bạn chọn: {' '.join(result['selected'])}\n"
            f"{'✅ Trúng! Nhận: ' + str(result['reward']) + ' VNĐ' if result['reward'] else f'❌ Không trúng! Mất: {result['bet']:,} VNĐ'}\n\n"
        )

    text += f"💵 Cược: {bet:,} VNĐ\n💼 Số dư: {balance:,} VNĐ\n"
    if selected:
        text += f"✅ Đã chọn: {' '.join(selected)}"

    # Tạo nút chọn hình
    keyboard = []
    for i in range(0, 6, 3):
        row = []
        for sym in BAUCUA_SYMBOLS[i:i+3]:
            mark = "✅" if sym in selected else ""
            row.append(InlineKeyboardButton(sym + mark, callback_data=f"baucua_toggle_{sym}"))
        keyboard.append(row)

    keyboard.append([InlineKeyboardButton("🎯 Lắc", callback_data="baucua_play")])
    keyboard.append([
        InlineKeyboardButton("➖", callback_data="baucua_decrease"),
        InlineKeyboardButton("🔁 Chơi lại", callback_data="baucua_start"),
        InlineKeyboardButton("➕", callback_data="baucua_increase")
    ])
    keyboard.append([InlineKeyboardButton("🏠 Menu", callback_data="menu")])

    try:
        await update.callback_query.edit_message_text(
            text=text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard)
        )
    except:
        await update.message.reply_text(
            text=text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard)
        )

BET_LEVELS = [2000, 5000, 10000, 20000, 50000, 100000, 200000, 500000, 1000000, 2000000]

async def mines_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    board_size = 5
    total_cells = board_size * board_size
    bombs = random.sample(range(total_cells), 3)  # chọn 3 vị trí bom khác nhau


    context.user_data['mines'] = {
        'bet_index': 2,
        'opened': [],
        'bombs': bombs,
        'multiplier': 1.0,
        'board_size': board_size,
        'finished': False
}

    await render_mines(update, context)

async def mines_increase(update: Update, context: ContextTypes.DEFAULT_TYPE):
    game = context.user_data['mines']
    if game['bet_index'] < len(BET_LEVELS) - 1:
        game['bet_index'] += 1
    await render_mines(update, context)

async def mines_decrease(update: Update, context: ContextTypes.DEFAULT_TYPE):
    game = context.user_data['mines']
    if game['bet_index'] > 0:
        game['bet_index'] -= 1
    await render_mines(update, context)


async def mines_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    game = context.user_data['mines']
    cell = int(update.callback_query.data.split("_")[-1])

    if game['finished'] or cell in game['opened']:
        return

    game['opened'].append(cell)
    if cell in game['bombs']:
        game['finished'] = True
        bet = BET_LEVELS[game['bet_index']]
        users[user_id]['balance'] -= bet
        save_data()
    else:
        game['multiplier'] += 0.3  # mỗi ô đúng nhân thêm 0.3 lần cược

    await render_mines(update, context)


async def mines_cashout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    game = context.user_data['mines']

    if game['finished'] or not game['opened']:
        return

    bet = BET_LEVELS[game['bet_index']]
    reward = int(bet * game['multiplier'])

    users[user_id]['balance'] += reward
    game['finished'] = True
    save_data()
    await render_mines(update, context)

async def render_mines(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    game = context.user_data['mines']
    bet = BET_LEVELS[game['bet_index']]
    balance = users[user_id]['balance']
    size = game['board_size']
    total_cells = size * size
    text = "<b>💣 ĐẶT BOM – LẬT Ô</b>\n\n"

    if game['finished']:
        if any(b in game['opened'] for b in game['bombs']):
            text += "💥 Bạn trúng BOM! Mất cược!\n\n"
        else:
            reward = int(bet * game['multiplier'])
            text += f"💰 Rút thành công: {reward:,} VNĐ\n\n"

    text += f"💵 Cược: {bet:,} VNĐ\n💼 Số dư: {balance:,} VNĐ\n"
    if not game['finished']:
        text += f"🎯 Hệ số thưởng: x{game['multiplier']:.1f}"

    keyboard = []
    for i in range(size):
        row = []
        for j in range(size):
            idx = i * size + j
            if idx in game['opened']:
                 icon = "💰" if idx not in game['bombs'] else "💣"
            else:
                icon = "⬜️" if not game['finished'] else ("💣" if idx in game['bombs'] else "⬜️")

            callback = f"mines_click_{idx}" if not game['finished'] else "disabled"
            row.append(InlineKeyboardButton(icon, callback_data=callback))
        keyboard.append(row)

    if not game['finished']:
        keyboard.append([InlineKeyboardButton("💰 Rút tiền", callback_data="mines_cashout")])

    keyboard.append([
        InlineKeyboardButton("➖", callback_data="mines_decrease"),
        InlineKeyboardButton("🔁 Chơi lại", callback_data="mines_start"),
        InlineKeyboardButton("➕", callback_data="mines_increase")
    ])
    keyboard.append([InlineKeyboardButton("🏠 Menu", callback_data="menu")])

    try:
        await update.callback_query.edit_message_text(
            text=text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard)
        )
    except:
        await update.message.reply_text(
            text=text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard)
        )

async def latbai_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    multipliers = [0, 0, 1, 2, 3, 10]
    random.shuffle(multipliers)

    context.user_data['latbai'] = {
        'bet_index': 2,
        'revealed': False,
        'result': None,
        'multipliers': multipliers
    }
    await render_latbai(update, context)


async def latbai_pick(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    game = context.user_data['latbai']
    if game['revealed']:
        return

    bet = BET_LEVELS[game['bet_index']]
    if users[user_id]['balance'] < bet:
        await update.callback_query.answer("❌ Không đủ số dư!", show_alert=True)
        return

    users[user_id]['balance'] -= bet
    idx = int(update.callback_query.data.split("_")[-1])
    multiplier = game['multipliers'][idx]
    reward = bet * multiplier

    if reward > 0:
        users[user_id]['balance'] += reward

    game['revealed'] = True
    game['result'] = {
        'index': idx,
        'multiplier': multiplier,
        'reward': reward,
        'bet': bet
    }

    save_data()
    await render_latbai(update, context)


async def latbai_increase(update: Update, context: ContextTypes.DEFAULT_TYPE):
    game = context.user_data['latbai']
    if game['bet_index'] < len(BET_LEVELS) - 1:
        game['bet_index'] += 1
    await render_latbai(update, context)

async def latbai_decrease(update: Update, context: ContextTypes.DEFAULT_TYPE):
    game = context.user_data['latbai']
    if game['bet_index'] > 0:
        game['bet_index'] -= 1
    await render_latbai(update, context)


async def render_latbai(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    game = context.user_data['latbai']
    bet = BET_LEVELS[game['bet_index']]
    balance = users[user_id]['balance']
    text = "<b>🎰 LẬT THẺ – ĐOÁN TRÚNG</b>\n\n"

    if game['revealed']:
        r = game['result']
        text += (
            f"🃏 Bạn chọn ô {r['index'] + 1} → x{r['multiplier']}\n"
            f"{'✅ Thắng: ' + str(r['reward']) + ' VNĐ' if r['reward'] else f'❌ Thua! Mất: {bet:,} VNĐ'}\n\n"
        )

    text += f"💵 Cược: {bet:,} VNĐ\n💼 Số dư: {balance:,} VNĐ"

    # Nút
    keyboard = []
    row = []
    for i in range(6):
        if game['revealed'] and i == game['result']['index']:
            label = f"x{game['multipliers'][i]}"
        else:
            label = "⬜️"
        row.append(InlineKeyboardButton(label, callback_data=f"latbai_pick_{i}"))
    keyboard.append(row)

    if game['revealed']:
        keyboard.append([InlineKeyboardButton("🔁 Chơi lại", callback_data="latbai_start")])
    else:
        keyboard.append([
            InlineKeyboardButton("➖", callback_data="latbai_decrease"),
            InlineKeyboardButton("🔁 Chơi lại", callback_data="latbai_start"),
            InlineKeyboardButton("➕", callback_data="latbai_increase")
        ])
    keyboard.append([InlineKeyboardButton("🏠 Menu", callback_data="menu")])

    try:
        await update.callback_query.edit_message_text(
            text=text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard)
        )
    except:
        await update.message.reply_text(
            text=text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard)
        )

async def doanso_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['doanso'] = {
        'bet_index': 2,
        'result': None
    }
    await render_doanso(update, context)


async def doanso_select(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    game = context.user_data['doanso']
    bet = BET_LEVELS[game['bet_index']]
    guess = int(update.callback_query.data.split("_")[-1])

    if users[user_id]['balance'] < bet:
        await update.callback_query.answer("❌ Không đủ số dư!", show_alert=True)
        return

    users[user_id]['balance'] -= bet
    bot_number = random.randint(1, 10)

    if guess == bot_number:
        reward = bet * 10
    elif abs(guess - bot_number) == 1:
        reward = bet * 2
    else:
        reward = 0

    if reward > 0:
        users[user_id]['balance'] += reward

    game['result'] = {
        'guess': guess,
        'bot': bot_number,
        'reward': reward,
        'bet': bet
    }
    save_data()
    await render_doanso(update, context)


async def doanso_increase(update: Update, context: ContextTypes.DEFAULT_TYPE):
    game = context.user_data['doanso']
    if game['bet_index'] < len(BET_LEVELS) - 1:
        game['bet_index'] += 1
    await render_doanso(update, context)

async def doanso_decrease(update: Update, context: ContextTypes.DEFAULT_TYPE):
    game = context.user_data['doanso']
    if game['bet_index'] > 0:
        game['bet_index'] -= 1
    await render_doanso(update, context)


async def render_doanso(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    game = context.user_data['doanso']
    bet = BET_LEVELS[game['bet_index']]
    balance = users[user_id]['balance']
    result = game['result']
    text = "<b>🎯 ĐOÁN SỐ MAY MẮN (1–10)</b>\n\n"

    if result:
        text += (
            f"🔢 Bạn chọn: {result['guess']}\n"
            f"🎲 Bot ra: {result['bot']}\n"
        )
        if result['guess'] == result['bot']:
            text += f"✅ Trùng số! Nhận: {result['reward']:,} VNĐ\n\n"
        elif abs(result['guess'] - result['bot']) == 1:
            text += f"✅ Gần đúng! Nhận: {result['reward']:,} VNĐ\n\n"
        else:
            text += f"❌ Sai! Mất: {result['bet']:,} VNĐ\n\n"

    text += f"💵 Cược: {bet:,} VNĐ\n💼 Số dư: {balance:,} VNĐ"

    # Nút chọn số
    keyboard = []
    row = []
    for i in range(1, 11):
        row.append(InlineKeyboardButton(str(i), callback_data=f"doanso_select_{i}"))
        if len(row) == 5:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)

    if result:
        keyboard.append([InlineKeyboardButton("🔁 Chơi lại", callback_data="doanso_start")])
    else:
        keyboard.append([
            InlineKeyboardButton("➖", callback_data="doanso_decrease"),
            InlineKeyboardButton("🔁 Chơi lại", callback_data="doanso_start"),
            InlineKeyboardButton("➕", callback_data="doanso_increase")
        ])
    keyboard.append([InlineKeyboardButton("🏠 Menu", callback_data="menu")])

    try:
        await update.callback_query.edit_message_text(
            text=text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard)
        )
    except:
        await update.message.reply_text(
            text=text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard)
        )


card_order = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
card_values = {c: i for i, c in enumerate(card_order, 2)}
BET_LEVELS = [2000, 5000, 10000, 20000, 50000, 100000, 200000, 500000, 1000000, 2000000]


async def poker_start_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['poker'] = {
        'bet_index': 2,
        'current_card': random.choice(card_order),
        'multiplier': 1.5,
        'history': [],
        'last_result': None,
        'finished': False
    }
    await render_poker(update, context)

async def poker_guess(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    game = context.user_data['poker']
    choice = update.callback_query.data  # poker_up hoặc poker_down
    bet = BET_LEVELS[game['bet_index']]

    prev = game['current_card']
    next_card = random.choice(card_order)

    prev_val = card_values[prev]
    next_val = card_values[next_card]

    is_correct = (
        (choice == "poker_up" and next_val > prev_val) or
        (choice == "poker_down" and next_val < prev_val)
    )

    if is_correct:
        game['multiplier'] += 0.5
        game['current_card'] = next_card
        game['history'].append(next_card)
    else:
        users[user_id]['balance'] -= bet
        game['finished'] = True
        save_data()

    game['last_result'] = {
        'prev_card': prev,
        'next_card': next_card,
        'is_correct': is_correct,
        'bet': bet
    }

    await render_poker(update, context)


async def poker_cashout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    game = context.user_data['poker']
    bet = BET_LEVELS[game['bet_index']]
    reward = int(bet * game['multiplier'])

    users[user_id]['balance'] += reward
    game['finished'] = True
    save_data()
    await render_poker(update, context)



async def poker_increase(update: Update, context: ContextTypes.DEFAULT_TYPE):
    game = context.user_data['poker']
    if game['bet_index'] < len(BET_LEVELS) - 1:
        game['bet_index'] += 1
    await render_poker(update, context)

async def poker_decrease(update: Update, context: ContextTypes.DEFAULT_TYPE):
    game = context.user_data['poker']
    if game['bet_index'] > 0:
        game['bet_index'] -= 1
    await render_poker(update, context)


async def render_poker(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    game = context.user_data['poker']
    bet = BET_LEVELS[game['bet_index']]
    balance = users[user_id]['balance']

    text = "<b>🃏 Poker Trên & Dưới</b>\n\n"

    result = game.get('last_result')
    if result:
        text += (
            f"🔄 <b>Bài trước:</b> {result['prev_card']} ➡ <b>{result['next_card']}</b>\n"
        )
        if result['is_correct']:
            text += "✅ <b>Bạn đoán đúng!</b>\n"
        else:
            text += f"❌ <b>Bạn đoán sai!</b>\n"
            text += f"💸 <b>Mất:</b> {result['bet']:,} VNĐ\n"
            text += f"💼 <b>Số dư:</b> {balance:,} VNĐ\n"
            text += "\n👉 <i>Hãy chơi lại để thử vận may tiếp!</i>\n"

    # Nếu game chưa kết thúc
    if not game['finished']:
        reward_now = int(bet * game['multiplier'])
        text += (
            f"\n🎴 <b>Bài hiện tại:</b> {game['current_card']}\n"
            f"💵 <b>Cược:</b> {bet:,} VNĐ\n"
            f"💰 <b>Hệ số thưởng:</b> x{game['multiplier']:.1f}\n"
            f"💸 <b>Thưởng hiện tại nếu rút:</b> <b><u>{reward_now:,} VNĐ</u></b>\n"
            f"💼 <b>Số dư:</b> {balance:,} VNĐ"
        )

    # Nếu đã rút tiền sau khi đoán đúng
    elif result and result['is_correct']:
        reward = int(bet * game['multiplier'])
        text += (
            f"\n💰 <b>Bạn đã rút thành công!</b>\n"
            f"🔢 <b>Hệ số:</b> x{game['multiplier']:.1f}\n"
            f"💵 <b>Thưởng:</b> <b><u>{reward:,} VNĐ</u></b>\n"
            f"💼 <b>Số dư:</b> {balance:,} VNĐ"
        )

    keyboard = []

    if not game['finished']:
        keyboard.append([
            InlineKeyboardButton("⬆️ Trên", callback_data="poker_up"),
            InlineKeyboardButton("⬇️ Dưới", callback_data="poker_down")
        ])
        keyboard.append([
            InlineKeyboardButton("💰 Rút tiền", callback_data="poker_cashout")
        ])
        keyboard.append([
            InlineKeyboardButton("➖", callback_data="poker_decrease"),
            InlineKeyboardButton("🔁 Chơi lại", callback_data="poker_start"),
            InlineKeyboardButton("➕", callback_data="poker_increase")
        ])
    else:
        keyboard.append([InlineKeyboardButton("🔁 Chơi lại", callback_data="poker_start")])

    keyboard.append([InlineKeyboardButton("🏠 Menu", callback_data="menu")])

    try:
        await update.callback_query.edit_message_text(
            text=text,
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    except:
        await update.message.reply_text(
            text=text,
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )


# Gắn lệnh /user_history
async def user_history(update, context):
    user_id = str(update.effective_user.id)
    if user_id != admin_id:
        await update.message.reply_text("⛔ Bạn không có quyền truy cập tính năng này.")
        return

    text = "📋 <b>Danh sách người dùng</b>:\n\n"
    keyboard = []

    for uid, info in users.items():
        username = info.get("username", "Không có")
        balance = info.get("balance", 0)
        referrals = info.get("referrals", 0)

        # Tính tổng tiền nạp
        total_deposit = sum(entry['amount'] for entry in info.get('deposits', []))
        total_withdraw = sum(entry['amount'] for entry in withdraw_requests.values() if entry.get('status') == 'confirmed' and str(uid) == entry.get('user_id', ''))

        text += (
            f"👤 <b>@{username}</b> (ID: {uid})\n"
            f"💰 Số dư: {balance:,} VNĐ\n"
            f"👥 Lượt mời: {referrals}\n"
            f"💳 Đã nạp: {total_deposit:,} VNĐ\n"
            f"🏧 Đã rút: {total_withdraw:,} VNĐ\n\n"
        )

        keyboard.append([InlineKeyboardButton(f"🔍 Xem chi tiết {uid}", callback_data=f"detail_{uid}")])

    await update.message.reply_text(
        text,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# Hàm xử lý khi admin bấm xem chi tiết user
async def handle_detail_callback(update, context):
    query = update.callback_query
    user_id = query.data.split("_")[1]
    info = users.get(user_id, {})
    history_list = history.get(user_id, [])
    missions = info.get("missions", [])
    deposits = info.get("deposits", [])

    giftcodes_used = [h['code'] for h in history_list if 'code' in h]
    total_bet = sum(abs(h.get('change', 0)) for h in history_list)
    total_rounds = len([h for h in history_list if 'change' in h])

    text = (
        f"📋 <b>Lịch sử người dùng {user_id}</b>\n\n"
        f"🎁 Giftcode đã dùng: {', '.join(giftcodes_used) if giftcodes_used else 'Không có'}\n"
        f"🎮 Số vòng cược: {total_rounds} vòng\n"
        f"🎰 Tổng tiền đặt cược: {total_bet:,} VNĐ\n"
        f"📋 Nhiệm vụ đã làm: {len(missions)}\n"
        f"💳 Nạp tiền: {sum(d['amount'] for d in deposits):,} VNĐ\n"
        f"🏧 Số yêu cầu rút: {len([r for r in withdraw_requests.values() if r.get('user_id') == user_id])}\n"
    )

    await query.answer()
    await query.edit_message_text(text=text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 Quay lại", callback_data="menu")]
    ]))


# ----- Xử lý nhập giftcode ----- (with max usage check)
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    message = update.message.text.strip()

    # Nếu ADMIN đang thêm nhiệm vụ
    if context.user_data.get('adding_task'):
        try:
            name, reward = message.split('|')
            name = name.strip()
            reward = int(reward.strip())

            tasks = nhiemvu.setdefault('tasks', [])
            new_id = max([task['id'] for task in tasks], default=0) + 1
            tasks.append({
                'id': new_id,
                'name': name,
                'reward': reward,
                'active': True
            })
            save_data()
            await update.message.reply_text(f"✅ Đã thêm nhiệm vụ: {name} ({reward} VNĐ)")
            context.user_data.pop('adding_task', None)
        except:
            await update.message.reply_text("❌ Sai định dạng. Gửi đúng: Tên nhiệm vụ | Số tiền thưởng")
        return

    # Nếu đang trong quá trình nhập thông tin rút tiền
    if 'withdraw_amount' in context.user_data and 'withdraw_method' in context.user_data:
        await handle_withdraw_info(update, context)
        return

    # Nếu không, kiểm tra giftcode
    code = message.upper()
    if code in giftcodes:
        giftcode_data = giftcodes[code]

        if 'used_by' not in giftcode_data:
            giftcode_data['used_by'] = []

        if user_id in giftcode_data['used_by']:
            keyboard = [[InlineKeyboardButton("🔙 Quay lại", callback_data="menu")]]
            await update.message.reply_text("⛔ Bạn đã sử dụng mã giftcode này rồi!", reply_markup=InlineKeyboardMarkup(keyboard))
            return

        giftcode_data['used_by'].append(user_id)
        amount = giftcode_data['amount']
        users[user_id]['balance'] += amount
        save_data()

        await update.message.reply_text(f"🎉 Nhập giftcode thành công! Nhận {amount} VNĐ!")
    else:
        await update.message.reply_text("⛔ Mã giftcode không hợp lệ hoặc đã dùng.")

    keyboard = [[InlineKeyboardButton("🔙 Quay lại", callback_data="menu")]]
    await update.message.reply_text("🎁 Quay lại menu chính:", reply_markup=InlineKeyboardMarkup(keyboard))

# ====== Đây là nơi bạn đã định nghĩa conv_add và conv_edit ======
conv_add = ConversationHandler(
    entry_points=[CallbackQueryHandler(add_nhiemvu, pattern="^add_nhiemvu$")],
    states={
        ADD_CODE: [
            MessageHandler(filters.TEXT, get_task_code),
            CallbackQueryHandler(redo_code, pattern="^redo_code$"),
            CallbackQueryHandler(cancel_add, pattern="^cancel_add$")
        ],
        ADD_NAME: [
            MessageHandler(filters.TEXT, get_task_name),
            CallbackQueryHandler(redo_name, pattern="^redo_name$"),
            CallbackQueryHandler(cancel_add, pattern="^cancel_add$")
        ],
        ADD_REWARD: [
            MessageHandler(filters.TEXT, get_task_reward),
            CallbackQueryHandler(redo_reward, pattern="^redo_reward$"),
            CallbackQueryHandler(cancel_add, pattern="^cancel_add$")
        ],
        ADD_DESCRIPTION: [
            MessageHandler(filters.TEXT, get_task_description),
            CallbackQueryHandler(redo_description, pattern="^redo_description$"),
            CallbackQueryHandler(cancel_add, pattern="^cancel_add$")
        ],
        CONFIRM_ADD: [
            CommandHandler('confirmadd', confirm_add),
            CommandHandler('canceladd', cancel_add),
            CallbackQueryHandler(cancel_add, pattern="^cancel_add$")
        ],
    },
    fallbacks=[CommandHandler('canceladd', cancel_add)],
    allow_reentry=True
)

conv_edit = ConversationHandler(
    entry_points=[CallbackQueryHandler(edit_nhiemvu, pattern="^edit_nhiemvu$")],
    states={
        EDIT_CHOOSE: [
            CallbackQueryHandler(choose_task_to_edit, pattern="^edit_\\d+$")
        ],
        EDIT_FIELD: [
            CallbackQueryHandler(choose_field_callback, pattern=r"^field_")
        ],
        EDIT_NEWVALUE: [
            MessageHandler(filters.ALL, get_new_value)
        ],
    },
    fallbacks=[],
    allow_reentry=True
)

async def start_mailing(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if user_id != str(admin_id):
        await update.message.reply_text("⛔ Bạn không có quyền sử dụng lệnh này.")
        return ConversationHandler.END

    context.user_data["mail_media"] = []
    context.user_data["mail_caption"] = ""
    await update.message.reply_text(
        "📨 Hãy gửi ảnh (có thể nhiều ảnh) và/hoặc caption. Gửi xong nội dung sẽ được gửi tới toàn bộ user.",
    )
    return MAIL_COLLECTING

async def collect_mail_content(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.effective_user.id) != str(admin_id):
        return ConversationHandler.END

    context.user_data.setdefault("mail_media", [])
    context.user_data.setdefault("mail_caption", "")
    if str(update.effective_user.id) != str(admin_id):
        return  # Chỉ admin mới có thể gửi nội dung mailing
    if update.message.caption and update.message.photo:
        photo_file_id = update.message.photo[-1].file_id
        context.user_data["mail_media"].append(InputMediaPhoto(media=photo_file_id))
        if not context.user_data["mail_caption"]:
            context.user_data["mail_caption"] = update.message.caption
    elif update.message.photo:
        photo_file_id = update.message.photo[-1].file_id
        mail_data["media"].append(InputMediaPhoto(media=photo_file_id))
    elif update.message.text:
        context.user_data["mail_caption"] += update.message.text + "\n"


    await update.message.reply_text("📬 Nhấn nút bên dưới để gửi nội dung đến tất cả user.", reply_markup=InlineKeyboardMarkup([
        [InlineKeyboardButton("📨 Gửi ngay", callback_data="confirm_send_mail")],
        [InlineKeyboardButton("❌ Huỷ", callback_data="cancel_send_mail")]
    ]))
    return MAIL_WAITING_SEND

async def confirm_send_mail(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    media = context.user_data.get("mail_media", [])
    caption = context.user_data.get("mail_caption", "")

    if not media and not caption:
        await update.callback_query.edit_message_text("⚠️ Không có nội dung để gửi.")
        return ConversationHandler.END

    count = 0
    failed = 0
    for uid in users:
        try:
            if media:
                batch = media[:10]
                if caption:
                    batch[0].caption = caption
                    batch[0].parse_mode = ParseMode.HTML
                await context.bot.send_media_group(chat_id=uid, media=batch)
            elif caption:
                await context.bot.send_message(chat_id=uid, text=caption, parse_mode=ParseMode.HTML)
            count += 1
        except Exception as e:
            failed += 1
            print(f"[ERROR] gửi tới {uid}: {e}")

    await update.callback_query.edit_message_text(f"✅ Đã gửi thông báo đến {count} người dùng thành công.")
    return ConversationHandler.END

async def cancel_send_mail(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.edit_message_text("❌ Đã huỷ gửi tin nhắn.")
    return ConversationHandler.END

mail_conv = ConversationHandler(
    entry_points=[CommandHandler("mailing_all_user", start_mailing)],
    states={
    MAIL_COLLECTING: [
        MessageHandler(filters.PHOTO | filters.TEXT, collect_mail_content)
    ],
    MAIL_WAITING_SEND: [
        CallbackQueryHandler(confirm_send_mail, pattern="^confirm_send_mail$"),
        CallbackQueryHandler(cancel_send_mail, pattern="^cancel_send_mail$")
    ]
},
    fallbacks=[],
    allow_reentry=True
)

SEARCH_INPUT = 1

async def timkiem_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.effective_user.id) != str(admin_id):
        await update.message.reply_text("⛔ Bạn không có quyền sử dụng lệnh này.")
        return ConversationHandler.END

    await update.message.reply_text(
        "🔍 Nhập <b>user ID</b> của người dùng cần tra cứu:",
        parse_mode="HTML"
    )
    return SEARCH_INPUT

async def process_search_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyword = update.message.text.strip()

    # Tìm user theo ID hoặc username
    target_uid = None
    for uid, info in users.items():
        if keyword == uid or keyword.lower() == info.get("username", "").lower():
            target_uid = uid
            break

    if not target_uid:
        await update.message.reply_text("❌ Không tìm thấy người dùng phù hợp.")
        return ConversationHandler.END

    # Lấy thông tin
    info = users.get(target_uid, {})
    username = info.get("username", "Không có")
    balance = info.get("balance", 0)
    referrals = info.get("referrals", 0)
    missions = info.get("missions", [])
    deposits = info.get("deposits", [])
    history_list = history.get(target_uid, [])

    giftcodes_used = [h['code'] for h in history_list if 'code' in h]
    total_bet = sum(abs(h.get('change', 0)) for h in history_list)
    total_rounds = len([h for h in history_list if 'change' in h])
    total_deposit = sum(d['amount'] for d in deposits)
    total_withdraw = sum(
        entry['amount'] for entry in withdraw_requests.values()
        if entry.get('status') == 'confirmed' and str(entry.get('user_id')) == target_uid
    )

    text = (
        f"👤 <b>@{username}</b> (ID: {target_uid})\n"
        f"💰 Số dư: {balance:,} VNĐ\n"
        f"👥 Mời bạn bè: {referrals} người\n"
        f"💳 Tổng nạp: {total_deposit:,} VNĐ\n"
        f"🏧 Tổng rút: {total_withdraw:,} VNĐ\n"
        f"🎮 Số vòng cược: {total_rounds} vòng\n"
        f"🎰 Tổng tiền đặt cược: {total_bet:,} VNĐ\n"
        f"📋 Nhiệm vụ đã làm: {len(missions)}\n"
        f"🎁 Giftcode đã nhận: {', '.join(giftcodes_used) if giftcodes_used else 'Không có'}"
    )

    await update.message.reply_text(text, parse_mode="HTML")
    return ConversationHandler.END

search_user_conv = ConversationHandler(
    entry_points=[CommandHandler("timkiem_user", timkiem_user)],
    states={
        SEARCH_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_search_input)]
    },
    fallbacks=[],
    allow_reentry=True
)

async def start_lock_user(update, context):
    await update.callback_query.answer()
    await update.callback_query.edit_message_text("🔒 Nhập ID user bạn muốn khoá:")
    context.user_data['lock_action'] = 'lock'
    return 1

async def start_unlock_user(update, context):
    await update.callback_query.answer()
    await update.callback_query.edit_message_text("🔓 Nhập ID user bạn muốn mở khoá:")
    context.user_data['lock_action'] = 'unlock'
    return 1

async def handle_lock_input(update, context):
    uid = update.message.text.strip()
    action = context.user_data.get("lock_action")
    if uid not in users:
        await update.message.reply_text("❌ User không tồn tại.")
        return ConversationHandler.END

    users[uid]['locked'] = (action == 'lock')
    save_data()
    status = "🔒 đã bị khoá" if action == 'lock' else "🔓 đã được mở khoá"
    await update.message.reply_text(f"✅ User {uid} {status}.")
    return ConversationHandler.END

lock_user_conv = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(start_lock_user, pattern="^lock_user$"),
        CallbackQueryHandler(start_unlock_user, pattern="^unlock_user$")
    ],
    states={1: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_lock_input)]},
    fallbacks=[],
)


async def list_locked_users(update, context):
    keyboard = []
    text = "🚫 Danh sách tài khoản bị khoá:\n\n"
    for uid, user in users.items():
        if user.get("locked"):
            text += f"🆔 {uid} | @{user.get('username')} | {user.get('balance')} VNĐ\n"
            keyboard.append([InlineKeyboardButton(f"🔓 Mở khoá {uid}", callback_data=f"unlock_{uid}")])
    if not keyboard:
        text += "✅ Không có tài khoản nào bị khoá."
    await update.callback_query.answer()
    await update.callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def unlock_specific_user(update, context):
    uid = update.callback_query.data.split("_")[1]
    if uid in users:
        users[uid]["locked"] = False
        save_data()
        await update.callback_query.answer("✅ Đã mở khoá tài khoản.")
        await update.callback_query.edit_message_text(f"✅ User {uid} đã được mở khoá.")


def main():
    application = Application.builder().token("7696784590:AAEu32_abpWLxi8hW_PExvp9ae0d3TdpPZc").build()
    
     # ConversationHandlers
    application.add_handler(conv_add)
    application.add_handler(conv_edit)
    application.add_handler(mail_conv)
    application.add_handler(search_user_conv)
    application.add_handler(lock_user_conv)


    

    # ====== Command Handler cơ bản ======
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("admin", admin))
    application.add_handler(CommandHandler("addgift", addgift))
    application.add_handler(CommandHandler("addcoin", addcoin))
    application.add_handler(CommandHandler("listuser", listuser))
    application.add_handler(CommandHandler("ruttien", view_withdraw_requests))
    application.add_handler(CommandHandler("user_history", user_history))

    

    # ====== Các nhiệm vụ người dùng ======
    application.add_handler(CommandHandler("menu_nhiemvu", nhiemvu_menu))
    application.add_handler(CommandHandler("setting_nhiemvu", admin_menu))
    application.add_handler(CommandHandler("duyet", admin_nhiemvu))
    application.add_handler(CallbackQueryHandler(process_nhiemvu, pattern=r"^nhiemvu_\d+$"))

    # ====== Xử lý Withdraw & Game ======
    application.add_handler(CallbackQueryHandler(approve_nhiemvu, pattern=r"^approve_"))
    application.add_handler(CallbackQueryHandler(cancel_nhiemvu, pattern=r"^cancel_nhiemvu_"))
    application.add_handler(CallbackQueryHandler(select_withdraw_amount, pattern=r"^withdraw_\d+"))
    application.add_handler(CallbackQueryHandler(select_withdraw_method, pattern=r"^withdraw_(banking|momo)$"))
    application.add_handler(CallbackQueryHandler(confirm_withdraw_request, pattern=r"^confirm_\d+$"))
    application.add_handler(CallbackQueryHandler(cancel_withdraw_request, pattern=r"^cancel_\d+$"))
    application.add_handler(CallbackQueryHandler(play_game, pattern=r"^bet_"))
    application.add_handler(CallbackQueryHandler(choose_tx, pattern=r"^chon_"))
    application.add_handler(CallbackQueryHandler(show_history, pattern=r"^lich_su$"))



    application.add_handler(CallbackQueryHandler(nohu_start, pattern="^choi_nohu$"))
    application.add_handler(CallbackQueryHandler(nohu_change_bet, pattern="^nohu_(increase|decrease)$"))
    application.add_handler(CallbackQueryHandler(nohu_spin, pattern="^nohu_spin$"))

    application.add_handler(CallbackQueryHandler(blackjack_start, pattern="^bj_start$"))
    application.add_handler(CallbackQueryHandler(blackjack_hit, pattern="^bj_hit$"))
    application.add_handler(CallbackQueryHandler(blackjack_stand, pattern="^bj_stand$"))
    application.add_handler(CallbackQueryHandler(blackjack_increase, pattern="^bj_increase$"))
    application.add_handler(CallbackQueryHandler(blackjack_decrease, pattern="^bj_decrease$"))

    application.add_handler(CallbackQueryHandler(taixiu_start, pattern="^taixiu_start$"))
    application.add_handler(CallbackQueryHandler(taixiu_play, pattern="^taixiu_(tai|xiu)$"))
    application.add_handler(CallbackQueryHandler(taixiu_increase, pattern="^taixiu_increase$"))
    application.add_handler(CallbackQueryHandler(taixiu_decrease, pattern="^taixiu_decrease$"))

    application.add_handler(CallbackQueryHandler(vongquay_start, pattern="^vongquay_start$"))
    application.add_handler(CallbackQueryHandler(vongquay_spin, pattern="^vongquay_spin$"))
    application.add_handler(CallbackQueryHandler(vongquay_increase, pattern="^vongquay_increase$"))
    application.add_handler(CallbackQueryHandler(vongquay_decrease, pattern="^vongquay_decrease$"))


    application.add_handler(CallbackQueryHandler(baucua_start, pattern="^baucua_start$"))
    application.add_handler(CallbackQueryHandler(baucua_play, pattern="^baucua_play$"))
    application.add_handler(CallbackQueryHandler(baucua_toggle, pattern=r"^baucua_toggle_.*$"))
    application.add_handler(CallbackQueryHandler(baucua_increase, pattern="^baucua_increase$"))
    application.add_handler(CallbackQueryHandler(baucua_decrease, pattern="^baucua_decrease$"))

    application.add_handler(CallbackQueryHandler(mines_start, pattern="^mines_start$"))
    application.add_handler(CallbackQueryHandler(mines_cashout, pattern="^mines_cashout$"))
    application.add_handler(CallbackQueryHandler(mines_increase, pattern="^mines_increase$"))
    application.add_handler(CallbackQueryHandler(mines_decrease, pattern="^mines_decrease$"))
    application.add_handler(CallbackQueryHandler(mines_click, pattern=r"^mines_click_\d+$"))

    application.add_handler(CallbackQueryHandler(latbai_start, pattern="^latbai_start$"))
    application.add_handler(CallbackQueryHandler(latbai_pick, pattern=r"^latbai_pick_\d+$"))
    application.add_handler(CallbackQueryHandler(latbai_increase, pattern="^latbai_increase$"))
    application.add_handler(CallbackQueryHandler(latbai_decrease, pattern="^latbai_decrease$"))

    application.add_handler(CallbackQueryHandler(doanso_start, pattern="^doanso_start$"))
    application.add_handler(CallbackQueryHandler(doanso_select, pattern=r"^doanso_select_\d+$"))
    application.add_handler(CallbackQueryHandler(doanso_increase, pattern="^doanso_increase$"))
    application.add_handler(CallbackQueryHandler(doanso_decrease, pattern="^doanso_decrease$"))


    application.add_handler(CallbackQueryHandler(poker_start_game, pattern="^poker_start$"))
    application.add_handler(CallbackQueryHandler(poker_guess, pattern="^poker_(up|down)$"))
    application.add_handler(CallbackQueryHandler(poker_cashout, pattern="^poker_cashout$"))
    application.add_handler(CallbackQueryHandler(poker_increase, pattern="^poker_increase$"))
    application.add_handler(CallbackQueryHandler(poker_decrease, pattern="^poker_decrease$"))

    # ====== Callback Query (thêm vào nhóm admin)
    application.add_handler(CallbackQueryHandler(handle_detail_callback, pattern=r"^detail_\d+$"))  # ✅ mới thêm


        # ====== Setting nhiệm vụ Admin ======
    application.add_handler(conv_add)    # Thêm nhiệm vụ
    application.add_handler(conv_edit)   # Chỉnh sửa nhiệm vụ
    application.add_handler(CallbackQueryHandler(list_nhiemvu, pattern=r"^list_nhiemvu$"))
    application.add_handler(CallbackQueryHandler(admin_menu, pattern=r"^setting_nhiemvu$"))
    application.add_handler(CallbackQueryHandler(delete_nhiemvu, pattern=r"^delete_\d+$"))
    application.add_handler(CallbackQueryHandler(toggle_nhiemvu, pattern=r"^toggle_\d+$"))
    application.add_handler(CallbackQueryHandler(choose_task_to_edit, pattern=r"^edit_\d+$"))
    application.add_handler(CallbackQueryHandler(choose_field_callback, pattern=r"^field_"))

    application.add_handler(CallbackQueryHandler(admin_nhiemvu, pattern=r"^admin_nhiemvu$"))
    
    application.add_handler(CallbackQueryHandler(start_lock_user, pattern="^lock_user$"))
    application.add_handler(CallbackQueryHandler(start_unlock_user, pattern="^unlock_user$"))
    application.add_handler(CallbackQueryHandler(list_locked_users, pattern="^list_locked_users$"))
    application.add_handler(CallbackQueryHandler(unlock_specific_user, pattern=r"^unlock_\d+$"))


    # ====== Fallback Callback ======
    application.add_handler(CallbackQueryHandler(menu_callback))  # fallback cho các callback khác
   # Ảnh và text
    application.add_handler(MessageHandler(filters.PHOTO & ~filters.User(admin_id), receive_photo))
    
    application.add_handler(MessageHandler(filters.TEXT, handle_text))     # User gửi text (giftcode, thông tin...)

    application.run_polling()


if __name__ == "__main__":
    main()




