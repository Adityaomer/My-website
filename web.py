import os
import pymongo
from telethon import TelegramClient, events

# MongoDB Configuration
MONGO_URL = os.environ.get("MONGO_URL") or "mongodb+srv://New_user_adi:radharani@atlascluster.tt1eq.mongodb.net/"
mongo_client = pymongo.MongoClient(MONGO_URL)
db = mongo_client["mangal_hardware"]
collection = db["categories"]

# Telethon Configuration
API_ID = os.environ.get("API_ID")  # Your API ID
API_HASH = os.environ.get("API_HASH")  # Your API Hash
BOT_TOKEN = os.environ.get("BOT_TOKEN")  # Your bot token

# Initialize the Telethon client
client = TelegramClient('bot', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

# Global variable to hold user state
user_data = {}

@client.on(events.NewMessage(pattern='/start'))
async def start(event):
    await event.respond("Welcome! Use /add to add a category or /delete <index> to delete a category.")

@client.on(events.NewMessage(pattern='/add'))
async def add_category(event):
    await event.respond("Please send me the category name.")
    user_data[event.chat_id] = {"step": "name"}

@client.on(events.NewMessage())
async def receive_name(event):
    if event.chat_id in user_data and user_data[event.chat_id]["step"] == "name":
        user_data[event.chat_id]["name"] = event.message.message
        await event.respond("Now send me the image URL.")
        user_data[event.chat_id]["step"] = "image"

@client.on(events.NewMessage())
async def receive_image(event):
    if event.chat_id in user_data and user_data[event.chat_id]["step"] == "image":
        user_data[event.chat_id]["image"] = event.message.message
        
        # Append the new category to the MongoDB collection
        new_category = {
            "name": user_data[event.chat_id]["name"],
            "image": user_data[event.chat_id]["image"],
            "products": []
        }
        
        # Update the database
        collection.update_one({}, {"$push": {"category": new_category}}, upsert=True)
        
        await event.respond(f"Category '{new_category['name']}' added successfully!")
        
        # Clean up user data
        del user_data[event.chat_id]

@client.on(events.NewMessage(pattern='/delete'))
async def delete_category(event):
    try:
        index = int(event.message.message.split()[1])  # Get the index from the command
        # Find the current categories
        category_data = collection.find_one({}, {"_id": 0})
        
        if category_data and 0 <= index < len(category_data.get("category", [])):
            # Remove the specified category
            collection.update_one({}, {"$pull": {"category": {"name": category_data["category"][index]["name"]}}})
            await event.respond(f"Category '{category_data['category'][index]['name']}' deleted successfully!")
        else:
            await event.respond("Invalid index provided.")
    except (IndexError, ValueError):
        await event.respond("Please provide a valid index after /delete command.")

# Start the client
if __name__ == "__main__":
    client.run_until_disconnected()