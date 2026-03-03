import os
import pymongo
from flask import Flask, jsonify
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

# MongoDB Configuration
MONGO_URL = os.environ.get("MONGO_URL") or "mongodb+srv://New_user_adi:radharani@atlascluster.tt1eq.mongodb.net/"
mongo_client = pymongo.MongoClient(MONGO_URL)
db = mongo_client["mangal_hardware"]
collection = db["categories"]

# Initialize Flask app (optional if you want to run it as a web server)
app = Flask(__name__)

# Global variable to hold user state
user_data = {}

def start(update: Update, context: CallbackContext):
    update.message.reply_text("Welcome! Use /add to add a category or /delete <index> to delete a category.")

def add_category(update: Update, context: CallbackContext):
    update.message.reply_text("Please send me the category name.")
    return "NAME"

def receive_name(update: Update, context: CallbackContext):
    user_data[update.message.chat_id] = {"name": update.message.text}
    update.message.reply_text("Now send me the image URL.")
    return "IMAGE"

def receive_image(update: Update, context: CallbackContext):
    user_data[update.message.chat_id]["image"] = update.message.text
    
    # Append the new category to the MongoDB collection
    new_category = {
        "name": user_data[update.message.chat_id]["name"],
        "image": user_data[update.message.chat_id]["image"],
        "products": []
    }
    
    # Update the database
    collection.update_one({}, {"$push": {"category": new_category}}, upsert=True)
    
    update.message.reply_text(f"Category '{new_category['name']}' added successfully!")
    
    # Clean up user data
    del user_data[update.message.chat_id]
    
def delete_category(update: Update, context: CallbackContext):
    try:
        index = int(context.args[0])
        # Find the current categories
        category_data = collection.find_one({}, {"_id": 0})
        
        if category_data and 0 <= index < len(category_data.get("category", [])):
            # Remove the specified category
            collection.update_one({}, {"$pull": {"category": {"name": category_data["category"][index]["name"]}}})
            update.message.reply_text(f"Category '{category_data['category'][index]['name']}' deleted successfully!")
        else:
            update.message.reply_text("Invalid index provided.")
    except (IndexError, ValueError):
        update.message.reply_text("Please provide a valid index after /delete command.")

def main():
    # Create the Updater and pass it your bot's token.
    updater = Updater("7728650601:AAHn1QxRambFq3yGsbuDAcYewXxHGjR-IdA") 
    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # Register command handlers
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("add", add_category))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, receive_name), group=1)
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, receive_image), group=2)
    dp.add_handler(CommandHandler("delete", delete_category))

    # Start the Bot
    updater.start_polling()

    # Run the bot until you send a signal to stop (Ctrl+C)
    updater.idle()

if __name__ == "__main__":
    main()