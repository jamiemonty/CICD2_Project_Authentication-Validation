import aio_pika
import asyncio
import json
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from docu_serve.models import User
from dotenv import load_dotenv

load_dotenv()

RABBIT_URL = os.getenv("RABBIT_URL", "amqps://ykvaygzy:Kg8o0HCEw9hRygtPpnQ3bjWv7N9KU0xZ@stingray.rmq.cloudamqp.com/ykvaygzy")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./app.db")

# Create engine and session
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

async def main():
    connection = await aio_pika.connect_robust(RABBIT_URL)
    channel = await connection.channel()

    exchange = await channel.declare_exchange("user_events", aio_pika.ExchangeType.TOPIC, durable=True)

    # Delete old queue and create new one with specific bindings
    queue = await channel.declare_queue("user_sync_queue_v2", durable=True)
    # Only bind to events this service should handle
    await queue.bind(exchange, routing_key="user.deleted")
    await queue.bind(exchange, routing_key="user.updated")
    print("Listening for admin events (user.deleted, user.updated)...")

    async with queue.iterator() as q:
        async for message in q:
            async with message.process():
                data = json.loads(message.body)
                event = message.routing_key
                print(f"Received Event: {event} --> {data}")

                db = SessionLocal()
                try:
                    if event == "user.deleted":
                        user = db.query(User).filter(User.user_id == data["user_id"]).first()
                        if user:
                            db.delete(user)
                            db.commit()
                    
                    elif event == "user.updated":
                        user = db.query(User).filter(User.user_id == data["user_id"]).first()
                        if user:
                            user.name = data["name"]
                            user.email = data["email"]
                            user.age = data["age"]
                            user.role = data["role"]
                            db.commit()
                finally:
                    db.close()

if __name__ == "__main__":
    asyncio.run(main())