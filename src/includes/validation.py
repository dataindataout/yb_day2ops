def command_confirmed(confirmation_text):
    response = input(f"{confirmation_text} (y/n): ").strip().lower()
    if response == "y":
        return True
    elif response == "n":
        return False
    else:
        print("Please enter 'y' or 'n'.")
        return command_confirmed(confirmation_text)  # force a valid response
