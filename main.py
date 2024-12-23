import logging

from telegram import Update, ForceReply, InlineKeyboardMarkup, InlineKeyboardButton, ParseMode, InputMediaPhoto
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, CallbackQueryHandler
import os
import re

logger = logging.getLogger(__name__)


# Pre-assign menu text
MAIN_MENU = "<b>Welcome to FrameCube SG's Store! ☀️</b>\n\nPlace an order, check out our promos, view your orders, or contact support here."
ORDER_MENU = "<b>🛒 Order 🛒</b>\n\nBrowse our products and place an order here!"
CONTACT_SUPPORT_MENU = "<b>📞 Contact Support 📞</b>\n\nContact our support team for assistance. \n\nWe are working hard to bring seamless live support into our bot. In the meantime, feel free to drop us a DM on Instagram <a href='https://www.instagram.com/framecube.sg/'>here</a>."

# Pre-assign button text
ORDER_BUTTON = "🛒 Place an Order"
PROMOS_BUTTON = "🎉 View Ongoing Promos"
VIEW_ORDERS_BUTTON = "📦 View your Orders"
CONTACT_SUPPORT_BUTTON = "📞 Contact Support"
ARROW_LEFT_BUTTON = "⬅️"
ARROW_RIGHT_BUTTON = "➡️"
BACK_BUTTON = "Back to Main Menu"

# List of promos
PROMOS = [
    ["[1/3] Christmas Sale", "https://picsum.photos/200"],
    ["[2/3] Opening Sale", "https://picsum.photos/300"],
    ["[3/3] Bundle Sale", "https://picsum.photos/400"]
]

def validate_discount_code(code):
    # Example validation logic
    DISCOUNT_CODES = {
        "CHRISTMAS": "-$1",
        "OPENING": "-$2",
        "BUNDLE": "-$1"
    }
    return DISCOUNT_CODES.get(code.upper(), "0")



# Build keyboards
MAIN_MENU_MARKUP = InlineKeyboardMarkup([
    [InlineKeyboardButton(ORDER_BUTTON, callback_data=ORDER_BUTTON)],
    [InlineKeyboardButton(PROMOS_BUTTON, callback_data=PROMOS_BUTTON)],
    [InlineKeyboardButton(VIEW_ORDERS_BUTTON, callback_data=VIEW_ORDERS_BUTTON)],
    [InlineKeyboardButton(CONTACT_SUPPORT_BUTTON, callback_data=CONTACT_SUPPORT_BUTTON)],
])
ORDER_MENU_MARKUP = InlineKeyboardMarkup([
    [InlineKeyboardButton("Fully Customised Frame & Photo (Starting at $2)", callback_data="custom")],
    #[InlineKeyboardButton("Chirstmas Bundle ($20)", callback_data="christmas")],
    [InlineKeyboardButton(BACK_BUTTON, callback_data=BACK_BUTTON)]
])
PROMOS_MENU_MARKUP = InlineKeyboardMarkup([
    [
        InlineKeyboardButton(ARROW_LEFT_BUTTON, callback_data=ARROW_LEFT_BUTTON),
        InlineKeyboardButton(ARROW_RIGHT_BUTTON, callback_data=ARROW_RIGHT_BUTTON),
        InlineKeyboardButton(BACK_BUTTON, callback_data=BACK_BUTTON)
    ]
])
VIEW_ORDERS_MENU_MARKUP = InlineKeyboardMarkup([
    [InlineKeyboardButton(BACK_BUTTON, callback_data=BACK_BUTTON)]
])
CONTACT_SUPPORT_MENU_MARKUP = InlineKeyboardMarkup([
    [InlineKeyboardButton(BACK_BUTTON, callback_data=BACK_BUTTON)]
])
FRAME_SELECTION_MENU_MARKUP = InlineKeyboardMarkup([
    [InlineKeyboardButton("Frameless (+$0)", callback_data="frameless")],
    [InlineKeyboardButton("Standing Frame (+$1)", callback_data="standing_frame")],
])

TYPE_SELECTION_MENU_MARKUP = InlineKeyboardMarkup([
    [InlineKeyboardButton("Instax Mini Polaroid (+$5)", callback_data="mini_polaroid")],
])
CUSTOMISATION_MENU_MARKUP = InlineKeyboardMarkup([
    [InlineKeyboardButton("None (+$0)", callback_data="none")],
    [InlineKeyboardButton("Text (+$3)", callback_data="text")],
    [InlineKeyboardButton("3D (Design 1) (+$5)", callback_data="design1")],
    [InlineKeyboardButton("3D (Design 2) (+$5)", callback_data="design2")],
    [InlineKeyboardButton("3D (Custom) (+$15)", callback_data="customdesign")],
])

CONFIRM_MENU_MARKUP = InlineKeyboardMarkup([
    [InlineKeyboardButton("Confirm Order", callback_data="confirm")],
    [InlineKeyboardButton(BACK_BUTTON, callback_data=BACK_BUTTON)]
])

DATE_MENU_MARKUP = InlineKeyboardMarkup([
    [InlineKeyboardButton("ASAP (+$0)", callback_data="asap")],
    [InlineKeyboardButton("After 14 Days (-$2)", callback_data="specific_date")],
])

DELIVERY_MENU_MARKUP = InlineKeyboardMarkup([
    [InlineKeyboardButton("Self Pickup (+$0)", callback_data="self_pickup")],
    [InlineKeyboardButton("Registered Mail (+$3)", callback_data="registered_mail")],
])

DISCOUNT_MENU_MARKUP = InlineKeyboardMarkup([
    [InlineKeyboardButton("Apply Discount", callback_data="apply_discount")],
    [InlineKeyboardButton("NONE", callback_data="nodiscount")]
])


# Store current promo image index
current_promo_index = 0

def start(update: Update, context: CallbackContext) -> None:
    """
    This function handles the /start command
    """
    update.message.reply_text(MAIN_MENU, reply_markup=MAIN_MENU_MARKUP, parse_mode=ParseMode.HTML)

def promo_menu(update: Update, context: CallbackContext) -> None:
    """
    This function handles the promo menu
    """
    query = update.callback_query
    query.answer()
    try:
        query.edit_message_media(
            media=InputMediaPhoto(
                media=PROMOS[current_promo_index][1],
                caption=f"<b>{PROMOS[current_promo_index][0]}</b>",
                parse_mode=ParseMode.HTML
            ),
            reply_markup=PROMOS_MENU_MARKUP
        )
    except Exception as e:
        logger.error(f"Error updating promo menu: {e}")

def button(update: Update, context: CallbackContext) -> None:
    """
    This function handles button presses
    """
    global current_promo_index
    query = update.callback_query
    query.answer()
    if query.data == ORDER_BUTTON:
        query.edit_message_text(ORDER_MENU, reply_markup=ORDER_MENU_MARKUP, parse_mode=ParseMode.HTML)
    elif query.data == PROMOS_BUTTON:
        promo_menu(update, context)
    elif query.data == VIEW_ORDERS_BUTTON:
        view_order(update, context)
    elif query.data == CONTACT_SUPPORT_BUTTON:
        query.edit_message_text(CONTACT_SUPPORT_MENU, reply_markup=CONTACT_SUPPORT_MENU_MARKUP, parse_mode=ParseMode.HTML)
    elif query.data == ARROW_LEFT_BUTTON or query.data == ARROW_RIGHT_BUTTON:
        if query.data == ARROW_LEFT_BUTTON:
            current_promo_index = (current_promo_index - 1) % len(PROMOS)
        elif query.data == ARROW_RIGHT_BUTTON:
            current_promo_index = (current_promo_index + 1) % len(PROMOS)
        promo_menu(update, context)
    elif query.data == BACK_BUTTON:
        query.delete_message()
        query.message.reply_text(MAIN_MENU, reply_markup=MAIN_MENU_MARKUP, parse_mode=ParseMode.HTML)
    elif query.data == "custom":
        query.edit_message_text("Fully-Customised Frame & Photo (Starting at $2).\n\nChoose a frame:", reply_markup=FRAME_SELECTION_MENU_MARKUP, parse_mode=ParseMode.HTML)
    elif query.data == "frameless":
        query.edit_message_text(query.message.text.split('Choose a frame:')[0] + "Frame: Frameless Frame (+$0)\n\nChoose a print type:", reply_markup=TYPE_SELECTION_MENU_MARKUP, parse_mode=ParseMode.HTML)
    elif query.data == "standing_frame":
        query.edit_message_text(query.message.text.split('Choose a frame:')[0] + "Frame: Standing Frame (+$1)\n\nChoose a print type:", reply_markup=TYPE_SELECTION_MENU_MARKUP, parse_mode=ParseMode.HTML)
    elif query.data == "mini_polaroid":
        query.edit_message_text(query.message.text.split('\nChoose a print type:')[0] + "Print Type: Instax Mini Polaroid (+$5)\n\nChoose a customisation:", reply_markup=CUSTOMISATION_MENU_MARKUP, parse_mode=ParseMode.HTML)
    elif query.data == "none":
        query.edit_message_text(query.message.text.split('\nChoose a customisation:')[0] + "Customisation: None (+$0)" + "\n\nChoose your delivery date:", reply_markup=DATE_MENU_MARKUP, parse_mode=ParseMode.HTML)
    elif query.data == "text":
        query.edit_message_text(query.message.text.split('\nChoose a customisation:')[0] + "Customisation: Text (+$3)" + "\n\nChoose your delivery date:", reply_markup=DATE_MENU_MARKUP, parse_mode=ParseMode.HTML)
    elif query.data == "design1":
        query.edit_message_text(query.message.text.split('\nChoose a customisation:')[0] + "Customisation: 3D (Design 1) (+$5)" + "\n\nChoose your delivery date:", reply_markup=DATE_MENU_MARKUP, parse_mode=ParseMode.HTML)
    elif query.data == "design2":
        query.edit_message_text(query.message.text.split('\nChoose a customisation:')[0] + "Customisation: 3D (Design 2) (+$5)" + "\n\nChoose your delivery date:", reply_markup=DATE_MENU_MARKUP, parse_mode=ParseMode.HTML)
    elif query.data == "customdesign":
        query.edit_message_text(query.message.text.split('\nChoose a customisation:')[0] + "Customisation: 3D (Custom) (+$15)" + "\n\nChoose your delivery date:", reply_markup=DATE_MENU_MARKUP, parse_mode=ParseMode.HTML)
    elif query.data == "asap":
        query.edit_message_text(query.message.text.split('\nChoose your delivery date:')[0] + "Delivery Date: ASAP (+$0)" + "\n\nChoose your delivery method:", reply_markup=DELIVERY_MENU_MARKUP, parse_mode=ParseMode.HTML)
    elif query.data == "specific_date":
        query.edit_message_text(query.message.text.split('\nChoose your delivery date:')[0] + "Delivery Date: After 14 Days (-$2)" + "\n\nChoose your delivery method:", reply_markup=DELIVERY_MENU_MARKUP, parse_mode=ParseMode.HTML)
    elif query.data == "self_pickup":
        query.edit_message_text(query.message.text.split('\nChoose your delivery method:')[0] + "Delivery Method: Self Pickup (+$0)" + '\n\nEnter a discount code, or click "NONE".', reply_markup=DISCOUNT_MENU_MARKUP, parse_mode=ParseMode.HTML)
        context.user_data['awaiting_discount_code'] = True
    elif query.data == "registered_mail":
        query.edit_message_text(query.message.text.split('\nChoose your delivery method:')[0] + "Delivery Method: Registered Mail (+$3)" + '\n\nEnter a discount code, or click "NONE".', reply_markup=DISCOUNT_MENU_MARKUP, parse_mode=ParseMode.HTML)
        context.user_data['awaiting_discount_code'] = True
    elif query.data == "nodiscount":
        context.user_data['awaiting_discount_code'] = False
        discount_amount = "0"
        query.edit_message_text(query.message.text.split('\nEnter a discount code, or click "NONE".')[0] + f"Discount code: None (-$0)" + "\n\nTotal:" + totalSum(query.message.text, discount_amount) + "\n\nPlease confirm your order, or return to main menu to cancel.", reply_markup=CONFIRM_MENU_MARKUP, parse_mode=ParseMode.HTML)
    elif query.data == "apply_discount":
        context.user_data['awaiting_discount_code'] = False
        discount_code = context.user_data.get('discount_code', '')
        discount_amount = validate_discount_code(discount_code)
        if discount_amount != "0":
            query.edit_message_text(query.message.text.split('\nEnter a discount code, or click "NONE".')[0] + f"Discount code: {discount_code} ({discount_amount})" + "\n\nTotal:" + totalSum(query.message.text, discount_amount) + "\n\nPlease confirm your order, or return to main menu to cancel.", reply_markup=CONFIRM_MENU_MARKUP, parse_mode=ParseMode.HTML)
        else:
            query.message.reply_text("Invalid discount code. Please try again.")
            context.user_data['awaiting_discount_code'] = True
    elif query.data == "christmas":
        query.edit_message_text("You selected the Christmas Bundle ($20).", parse_mode=ParseMode.HTML)
    elif query.data == "confirm":
        user_id = query.from_user.id
        create_order(update, context, query.message.text)
        order_existing = lastOrderNumber(user_id)
        query.edit_message_text(query.message.text.split('\n\nPlease confirm your order, or return to main menu to cancel.')[0] + f'\nTimestamp: {query.message.date}' + f"\nStatus: Created")
        query.message.reply_text(f'ORDER ID: [{user_id}-{order_existing}] Your order has been confirmed! 🎉 For added security purposes, please complete your order by submitting your personal information through the link by clicking <a href="https://forms.gle/D1KW83rGxDzQXXvM7">here</a>. Once you have done so, a confirmation message and payment request will be sent through Whatsapp to your number once your order has been processed. Thank you for placing an order with us!', parse_mode=ParseMode.HTML)



def extract_dollar_add(text):
    return re.findall(r'\+\$(\d+)', text)

def extract_dollar_minus(text):
    return re.findall(r'\-\$(\d+)', text)

def totalSum(text, discount_amount):
    amounts = extract_dollar_add(text)
    amounts_minus = extract_dollar_minus(text)
    discount_value = int(discount_amount.replace("-$", ""))
    total = sum(int(amount) for amount in amounts) - sum(int(amount) for amount in amounts_minus) - discount_value
    return f" ${total}"

# Add a handler to capture the discount code input
def handle_discount_code(update: Update, context: CallbackContext) -> None:
    if context.user_data.get('awaiting_discount_code', True):
        discount_amount = validate_discount_code(update.message.text)
        if discount_amount == "0":
            update.message.reply_text("Invalid discount code. Please try again.")
            return
        context.user_data['discount_code'] = update.message.text
        context.user_data['awaiting_discount_code'] = False
        update.message.reply_text("Discount code applied. Please click apply discount to continue.")

def create_order(update: Update, context: CallbackContext, order_details) -> None:
    """
    This function handles the /create_order command
    """
    query = update.callback_query
    user_id = query.from_user.id
    order_details = order_details.split('\n\nPlease confirm your order, or return to main menu to cancel.')[0] + f'\nTimestamp: {query.message.date}' + f"\nStatus: Created"
    
    # Save the order details to a database or a file (this is a placeholder)
    if not os.path.exists("orders"):
        os.makedirs("orders")
    
    orders_existing = lastOrderNumber(user_id)
    orders_file_path = f"orders/{user_id}.txt"
    with open(orders_file_path, "a") as file:
        file.write(f"[{orders_existing + 1} / ORDER ID: {user_id}-{orders_existing + 1}] {order_details}\n\n")


    # Notify the private group about the new order
    context.bot.send_message(
        chat_id="-4542609069",
        text=f"New order created by user {user_id}:\n{order_details}",
        parse_mode=ParseMode.HTML
    )

def lastOrderNumber(user_id):
    orders_existing = 0
    
    orders_file_path = f"orders/{user_id}.txt"
    if os.path.exists(orders_file_path):
        with open(orders_file_path, "r") as file:
            orders_existing = (len(file.readlines())) // 12

    return orders_existing

def view_order(update: Update, context: CallbackContext) -> None:
    """
    This function handles the view orders menu
    """
    query = update.callback_query
    user_id = query.from_user.id
    
    try:
        with open(f"orders/{user_id}.txt", "r") as file:
            orders = file.read()
        query.edit_message_text(f"Your orders:\n{orders}", reply_markup=VIEW_ORDERS_MENU_MARKUP, parse_mode=ParseMode.HTML)
    except FileNotFoundError:
        query.edit_message_text("You have no orders.", reply_markup=VIEW_ORDERS_MENU_MARKUP, parse_mode=ParseMode.HTML)

def announce(update: Update, context: CallbackContext) -> None:
    """
    This function handles the /announce command
    """
    admin_user_ids = [2005680918, 832267056]

    if update.message.from_user.id not in admin_user_ids:
        update.message.reply_text("An error was encountered when running this command. If you think this is a mistake, contact the bot's owner with error code: NOT_AUTHORIZED")
        return

    content = update.message.text.replace("/announce", "").strip()
    context.bot.send_message(
    chat_id="@framecubesg",
    text=content,
    parse_mode=ParseMode.HTML,
    reply_markup=InlineKeyboardMarkup([
        [InlineKeyboardButton("Visit our shop", url="https://t.me/framecubesg_bot?start=telegram")]
    ])
)

def view_all_orders(update: Update, context: CallbackContext) -> None:
    """
    This function handles the /view_all_orders command for admins
    """
    admin_user_ids = [2005680918, 832267056]

    if update.message.from_user.id not in admin_user_ids:
        update.message.reply_text("You are not authorized to view all orders.")
        return

    orders = ""
    for filename in os.listdir("orders"):
        with open(f"orders/{filename}", "r") as file:
            orders += f"User {filename.replace('.txt', '')}:\n{file.read()}\n"
    
    update.message.reply_text(f"All orders:\n{orders}")

def view_all_orders(update: Update, context: CallbackContext) -> None:
    """
    This function handles the /view_all_orders command for admins
    """
    admin_user_ids = [2005680918, 832267056]

    if update.message.from_user.id not in admin_user_ids:
        update.message.reply_text("You are not authorized to view all orders.")
        return

    orders = ""
    for filename in os.listdir("orders"):
        with open(f"orders/{filename}", "r") as file:
            orders += f"User {filename.replace('.txt', '')}:\n{file.read()}\n"
    
    update.message.reply_text(f"All orders:\n{orders}")

def update_order_status(update: Update, context: CallbackContext) -> None:
    """
    This function handles the /update_order_status command for admins
    """
    admin_user_ids = [2005680918, 832267056]

    if update.message.from_user.id not in admin_user_ids:
        update.message.reply_text("You are not authorized to update order status.")
        return

    command_parts = update.message.text.replace("/update_order_status", "").strip().split(" ", 2)
    if len(command_parts) < 3:
        update.message.reply_text("Usage: /update_order_status <user_id> <order_index> <new_status>")
        return

    user_id, order_index, new_status = command_parts
    order_index = int(order_index)*12 - 2

    try:
        with open(f"orders/{user_id}.txt", "r") as file:
            orders = file.readlines()
        
        if order_index < 0 or order_index >= len(orders):
            update.message.reply_text("Invalid order index.")
            return
        
        orders[order_index] = f"{orders[order_index].split('Status: ')[0].strip()}Status: {new_status}\n"
        
        with open(f"orders/{user_id}.txt", "w") as file:
            file.writelines(orders)
        
        update.message.reply_text("Order status updated successfully.")
    except FileNotFoundError:
        update.message.reply_text("User has no orders.")

def main() -> None:
    """Start the bot."""
    updater = Updater("7788508509:AAFHFBF5OlnOkOW5YiJrhJau5sGobXOs35U")
    #Main: 7788508509:AAFHFBF5OlnOkOW5YiJrhJau5sGobXOs35U
    #Demo: 5368248109:AAFIg3yYmxhBPFcP0OjiNPuAFuHjI4__ShA

    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("announce", announce))
    dispatcher.add_handler(CommandHandler("view_all_orders", view_all_orders))
    dispatcher.add_handler(CommandHandler("update_order_status", update_order_status))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_discount_code))

    dispatcher.add_handler(CallbackQueryHandler(button))

    updater.start_polling()

    updater.idle()

if __name__ == '__main__':
    main()