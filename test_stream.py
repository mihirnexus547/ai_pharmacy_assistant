from services.conversation import conversation_service

print("Streaming...\n")

for chunk in conversation_service.stream_chat(
    session_id="test",
    message="Hello, how are you?"
):
    print(chunk)