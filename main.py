import logging
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    CallbackContext,
    CallbackQueryHandler,
    ContextTypes,
)
from telegram.constants import ParseMode
import os
import re
import json
from dataclasses import dataclass
from typing import Dict, List, Tuple

logger = logging.getLogger(__name__)

# ======================
# CONFIGURATION SECTION
# ======================

@dataclass
class Product:
    name: str
    base_price: float
    options: Dict[str, Dict[str, Tuple[str, float]]]
    flow: List[str]

PRODUCTS = {
    "custom": Product(
        name="Fully Customised Frame & Photo",
        base_price=2.0,
        options={
            "frame": {
                "frameless": ("Frameless", 0),
                "standing_frame": ("Standing Frame", 1)
            },
            "print_type": {
                "mini_polaroid": ("Instax Mini Polaroid", 5)
            },
            "customization": {
                "none": ("None", 0),
                "text": ("Text", 3),
                "design1": ("3D Design 1", 5),
                "design2": ("3D Design 2", 5),
                "customdesign": ("3D Custom Design", 15)
            }
        },
        flow=["frame", "print_type", "customization", "delivery_date", "delivery_method"]
    )
}

DISCOUNT_CODES = {
    "CHRISTMAS": 1.0,
    "OPENING": 2.0,
    "BUNDLE": 1.0
}

PROMOS = [
    {"title": "[1/3] Christmas Sale", "image": "https://picsum.photos/200"},
    {"title": "[2/3] Opening Sale", "image": "https://picsum.photos/300"},
    {"title": "[3/3] Bundle Sale", "image": "https://picsum.photos/400"}
]

DELIVERY_OPTIONS = {
    "delivery_date": {
        "asap": ("ASAP", 0),
        "specific_date": ("After 14 Days", -2)
    },
    "delivery_method": {
        "self_pickup": ("Self Pickup", 0),
        "registered_mail": ("Registered Mail", 3)
    }
}

# ======================
# CORE BOT LOGIC
# ======================

class BotState:
    def __init__(self):
        self.current_promo_index = 0
        self.user_states = {}

    def get_user_state(self, user_id: int) -> Dict:
        return self.user_states.setdefault(user_id, {
            "current_product": None,
            "selected_options": {},
            "current_step": 0,
            "awaiting_discount": False
        })

bot_state = BotState()

def build_menu(buttons, items_per_row=1):
    return [buttons[i:i+items_per_row] for i in range(0, len(buttons), items_per_row)]

def main_menu_markup():
    buttons = [
        InlineKeyboardButton("🛒 Place an Order", callback_data="order"),
        InlineKeyboardButton("🎉 View Promos", callback_data="promos"),
        InlineKeyboardButton("📦 View Orders", callback_data="view_orders"),
        InlineKeyboardButton("📞 Contact Support", callback_data="contact_support")
    ]
    return InlineKeyboardMarkup(build_menu(buttons, 1))

def back_button():
    return [InlineKeyboardButton("🔙 Back", callback_data="main_menu")]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Welcome to FrameCube SG's Store! ☀️",
        reply_markup=main_menu_markup(),
        parse_mode=ParseMode.HTML
    )

async def handle_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = query.data
    state = bot_state.get_user_state(user_id)

    if data == "main_menu":
        await show_main_menu(query)
        state.clear()
        return

    if data == "order":
        await show_products_menu(query)
    elif data == "promos":
        await show_promos(query)
    elif data == "view_orders":
        await show_orders(query)
    elif data == "contact_support":
        await show_contact_support(query)
    elif data in PRODUCTS:
        await start_product_flow(query, state)
    elif data in ["prev_promo", "next_promo"]:
        await handle_promo_navigation(query, data)
    elif data == "apply_discount":
        await handle_discount_application(query, state)
    elif data == "confirm_order":
        await confirm_order(query, state)
    else:
        await handle_product_selection(query, state, data)

async def show_main_menu(query):
    await query.edit_message_text(
        "Main Menu",
        reply_markup=main_menu_markup(),
        parse_mode=ParseMode.HTML
    )

async def show_products_menu(query):
    products = [InlineKeyboardButton(p.name, callback_data=pid) for pid, p in PRODUCTS.items()]
    await query.edit_message_text(
        "Select a product:",
        reply_markup=InlineKeyboardMarkup(build_menu(products) + [back_button()])
    )

async def show_promos(query):
    state = bot_state.get_user_state(query.from_user.id)
    promo = PROMOS[state.current_promo_index]
    keyboard = [
        [
            InlineKeyboardButton("⬅️", callback_data="prev_promo"),
            InlineKeyboardButton("➡️", callback_data="next_promo")
        ],
        back_button()
    ]
    await query.edit_message_media(
        InputMediaPhoto(media=promo["image"], caption=promo["title"]),
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def handle_promo_navigation(query, action):
    state = bot_state.get_user_state(query.from_user.id)
    if action == "prev_promo":
        state.current_promo_index = (state.current_promo_index - 1) % len(PROMOS)
    else:
        state.current_promo_index = (state.current_promo_index + 1) % len(PROMOS)
    await show_promos(query)

async def show_contact_support(query):
    text = "📞 Contact Support\n\nContact us on Instagram: framecube.sg"
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup([back_button()]))

async def start_product_flow(query, state):
    state["current_product"] = query.data
    state["current_step"] = 0
    state["selected_options"] = {}
    await show_next_step(query, state)

async def show_next_step(query, state):
    product = PRODUCTS[state["current_product"]]
    step = product.flow[state["current_step"]]
    
    if step in product.options:
        options = product.options[step]
    else:
        options = DELIVERY_OPTIONS[step]
    
    buttons = []
    for opt_id, (name, price) in options.items():
        price_text = f"+${price}" if price >= 0 else f"-${abs(price)}"
        buttons.append(InlineKeyboardButton(f"{name} ({price_text})", callback_data=opt_id))
    
    keyboard = build_menu(buttons) + [back_button()]
    await query.edit_message_text(
        f"Select {step.replace('_', ' ')}:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def handle_product_selection(query, state, option_id):
    product = PRODUCTS[state["current_product"]]
    current_step = product.flow[state["current_step"]]
    
    if current_step in product.options:
        options = product.options[current_step]
    else:
        options = DELIVERY_OPTIONS[current_step]
    
    if option_id in options:
        name, price = options[option_id]
        state["selected_options"][current_step] = (name, price)
        state["current_step"] += 1
        
        if state["current_step"] < len(product.flow):
            await show_next_step(query, state)
        else:
            await show_order_summary(query, state)

async def show_order_summary(query, state):
    total = sum(price for _, price in state["selected_options"].values())
    summary = "Order Summary:\n"
    for step, (name, price) in state["selected_options"].items():
        summary += f"- {step.replace('_', ' ').title()}: {name} (${price})\n"
    
    keyboard = [
        [InlineKeyboardButton("Apply Discount", callback_data="apply_discount")],
        [InlineKeyboardButton("Confirm Order", callback_data="confirm_order")],
        back_button()
    ]
    await query.edit_message_text(
        f"{summary}\nTotal: ${total}",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def handle_discount_application(query, state):
    state["awaiting_discount"] = True
    await query.message.reply_text("Please enter your discount code:")

async def confirm_order(query, state):
    total = sum(price for _, price in state["selected_options"].values())
    discount = state.get("discount", 0)
    final_total = total - discount
    await query.edit_message_text(
        f"Order confirmed!\nTotal: ${final_total:.2f}",
        reply_markup=InlineKeyboardMarkup([back_button()])
    )
    state.clear()

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    state = bot_state.get_user_state(user_id)
    
    if state.get("awaiting_discount"):
        code = update.message.text.upper()
        discount = DISCOUNT_CODES.get(code, 0)
        if discount:
            state["discount"] = discount
            state["awaiting_discount"] = False
            await update.message.reply_text(f"Discount applied! -${discount:.2f}")
            await show_order_summary(update.message, state)
        else:
            await update.message.reply_text("Invalid discount code. Try again.")

def main():
    application = Application.builder().token("7788508509:AAFHFBF5OlnOkOW5YiJrhJau5sGobXOs35U").build()
    
    #Main: 7788508509:AAFHFBF5OlnOkOW5YiJrhJau5sGobXOs35U
    #Demo: 5368248109:AAFIg3yYmxhBPFcP0OjiNPuAFuHjI4__ShA
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(handle_button))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    application.run_polling()

if __name__ == "__main__":
    main()