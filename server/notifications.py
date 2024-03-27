# Create desktop notifications
from notifypy import Notify

notification = Notify()


# TODO: change to sms or email
def send_notification(drone_id: int):
    notification.title = "Upcoming Schedule"
    notification.message = f"Drone with id {drone_id} is about to departure"
    notification.icon = "drone.png"

    # Display the notification
    notification.send()
