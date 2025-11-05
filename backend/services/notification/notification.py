def send_to_contacts(message: str, contacts: list[str]) -> None:
    """
    Sends a notification message to a list of contacts.

    Args:
        message (str): The notification message to send.
        contacts (list[str]): A list of contact identifiers (e.g., email addresses, phone numbers).
    """

    for contact in contacts:
        send_notification(contact, message)

def send_notification(contact: str, message: str) -> None:
    """
    Sends a notification message to a single contact.

    Args:
        contact (str): The contact identifier (e.g., email address, phone number).
        message (str): The notification message to send.
    """
    pass
