from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
import re
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError, AuthKeyUnregisteredError
from sqlite3 import OperationalError

# Hardcoded API constants
API_ID = 27477637
API_HASH = '059ef651932df7a0a1998e5db5148127'

# Fixed directory for session files
SESSIONS_DIR = "C:\\Users\\admin\\PycharmProjects\\FastAPIProject\\sessions\\"
os.makedirs(SESSIONS_DIR, exist_ok=True)

# FastAPI app initialization
app = FastAPI()


class TelegramBot:
    def __init__(self, session_name):
        self.session_file = os.path.join(SESSIONS_DIR, f"{session_name}.session")
        self.client = TelegramClient(self.session_file, API_ID, API_HASH)

    async def connect(self):
        """Connects the Telegram client."""
        try:
            await self.client.connect()
            if not await self.client.is_user_authorized():
                raise HTTPException(status_code=401, detail="Session is not authorized. Please log in again.")
        except SessionPasswordNeededError:
            raise HTTPException(status_code=401, detail="2FA password required. Unable to proceed.")
        except AuthKeyUnregisteredError:
            raise HTTPException(status_code=401, detail="Auth key is unregistered. Session file might be invalid.")
        except OperationalError as e:
            raise HTTPException(status_code=500, detail=f"SQLite sessions error: {str(e)}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Unexpected connection error: {str(e)}")

    async def get_latest_telegram_message(self, limit=1):
        """Fetches the latest message from the sender named 'Telegram'."""
        try:
            dialogs = await self.client.get_dialogs()
            for dialog in dialogs:
                try:
                    messages = await self.client.get_messages(dialog.entity, limit=limit)
                    for msg in messages:
                        sender = await msg.get_sender()
                        if sender and getattr(sender, "first_name", "").lower() == "telegram":
                            match = re.search(r'\b\d{5,6}\b', msg.text)
                            if match:
                                return {"message": int(match.group())}
                except Exception as msg_error:
                    print(f"Error processing message: {msg_error}")
            return {"message": None}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error fetching messages: {str(e)}")

    async def close(self):
        """Disconnects the Telegram client."""
        await self.client.disconnect()



@app.get("/api/{phone_number}/tokenSession")
async def get_last_message(phone_number: str):
    session_file = os.path.join(SESSIONS_DIR, f"{phone_number}.session")
    if not os.path.exists(session_file):
        raise HTTPException(status_code=400, detail="Session file does not exist. Please provide a valid phone number.")

    bot = TelegramBot(phone_number)

    async def fetch_last_message():
        try:
            await bot.connect()
            result = await bot.get_latest_telegram_message()
            return result
        except HTTPException as http_err:
            raise http_err
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
        finally:
            await bot.close()

    return await fetch_last_message()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
