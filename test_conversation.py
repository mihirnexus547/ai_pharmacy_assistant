from services.conversation import conversation_service

session = "mihir"

while True:

    user = input("You : ")

    if user == "exit":
        break

    response = conversation_service.chat(
        session_id=session,
        message=user,
    )

    print("\nAssistant :", response)