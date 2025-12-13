import aio_pika
import asyncio
import json
import os
import sqlite3

RABBIT_URL=os.getenv("RABBIT_URL")

async def main():
    connection = await aio_pika.connect_robust(RABBIT_URL)
    channel = await connection.channel()

    exchange = await channel.declare_exchange("user_events", aio_pika.ExchangeType.TOPIC, durable=True)

    queue = await channel.declare_queue("user_sync_queue", durable=True)
    await queue.bind(exchange, routing_key="user.*")
    print("Listening for admin events...")

    async with queue.iterator() as q:
        async for message in q:
            async with message.process():
                data = json.loads(message.body)
                event = message.routing_key
                print(f"Received Event: {event} --> {data}")

                conn = sqlite3.connect("users.db")
                cur = conn.cursor()

                if event == "user.deleted":
                    cur.execute("DELETE FROM users WHERE user_id=?", (data["user_id"],))
                    conn.commit()
                
                elif event == "user.updated":
                    cur.execute("""
                        UPDATE users
                        SET name=?, email=?, age=?, role=?
                        WHERE user_id=?
                    """, (data["name"], data["email"], data["age"], data["role"], data["user_id"]))

                    conn.commit()
                conn.close()

if __name__ == "__main__":
    asyncio.run(main())