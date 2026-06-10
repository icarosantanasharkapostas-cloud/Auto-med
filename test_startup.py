import asyncio

async def test_bot_startup():
    from bot.client_manager import manager
    print("Manager is ready")
    client_data = {
        "id": 1,
        "nome": "Test",
        "token": "test",
        "email": "test@test.com",
        "senha_email": "test"
    }
    print("Trying to start client")
    try:
        success = await manager.start_client(client_data)
        print(f"Start client result: {success}")
        # Wait a bit
        await asyncio.sleep(2)
        print(f"Is running: {manager.is_running(1)}")
        await manager.stop_client(1)
        print("Test complete")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_bot_startup())