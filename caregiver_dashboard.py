

# IMPORT LIBRARIES
# ------------------------------
import time
import tkinter as tk
from datetime import datetime
import threading
from twilio.rest import Client
import pill_detect
# ------------------------------


class care_giver_dashboard():

    def __init__(self, root):
        self.root = root
        root.title("Caregiver's Dashboard")
        root.geometry("500x700")
        root.configure(bg="#2c3e50")

        self.dose_taken_today = False
        self.ignore_logged_today = False

        #twilio
        self.account_sid = "YOUR_TWILIO_ACCOUNT_SID"
        self.auth_token = "YOUR_TWILIO_AUTH_TOKEN"
        self.twilio_num = '+16205221963'
        self.my_num = '+16475134211'

        #status display
        self.status_frame = tk.Frame(root, bg="red", height=150)
        self.status_frame.pack(fill="x")
        self.status_text = tk.Label(self.status_frame, text="MEDICATION LATE", fg="white", bg="red", font=("Arial", 24, "bold"))
        self.status_text.pack(pady=40)

        #system log
        tk.Label(root, text="System Log:", font=("Arial", 12, "bold")).pack(pady=10)
        self.log = tk.Text(root, height=12, width=50, bg="#f0f0f0")
        self.log.pack(padx=20, pady=5)

        #buttons
        #simulates the camera signal if hardware isn't connected
        self.test_btn = tk.Button(root, text="Simulate Camera Signal", command=self.record_dose, height=2, width=25)
        self.test_btn.pack(pady=10)

        self.reset_btn = tk.Button(root, text="Manual Reset", command=self.reset_system, font=("Arial", 10))
        self.reset_btn.pack(pady=5)

        self.listen_thread = threading.Thread(target=self.listen_for_hardware, daemon=True)
        self.listen_thread.start()

    def listen_for_hardware(self):
        # initialize cam images
        pill_detect.initialize_images()

        while True:
            # midnight reset
            now_time = datetime.now().strftime("%H:%M")
            if now_time == "00:00":
                self.root.after(0, self.reset_system)

            pill_found = pill_detect.check_for_pill()

            if pill_found:
                self.root.after(0, self.record_dose)

            time.sleep(1)

    def send_sms(self, timestamp):
        try:
            client = Client(self.account_sid, self.auth_token)
            message = client.messages.create(
                body=f"Med-Check Alert: Medication recorded at {timestamp}.",
                from_=self.twilio_num,
                to=self.my_num
            )
            self.root.after(0, lambda: self.log.insert(tk.END, f">>> SMS SENT: {message.sid[:8]}\n"))
        except Exception as e:
            self.root.after(0, lambda: self.log.insert(tk.END, f">>> SMS ERROR: Check internet/keys\n"))

    def record_dose(self):

        #if meds not already taken 
        if not self.dose_taken_today:
            self.dose_taken_today = True
            self.ignore_logged_today = False
            # pill_detect.pill_taken_today = True
            timestamp = datetime.now().strftime("%H:%M:%S")
            
            #ui update
            self.status_frame.config(bg="green")
            self.status_text.config(text="MEDICATION TAKEN", bg="green")
            self.log.insert(tk.END, f"[{timestamp}] - Dose Detected & Processed\n")
            
            #disable test button to prevent spamming during demo
            self.test_btn.config(state="disabled")
            
            self.save_to_file(timestamp) #save to log
            threading.Thread(target=self.send_sms, args=(timestamp,), daemon=True).start() #text
        else:
            if not self.ignore_logged_today:
                self.log.insert(tk.END, "Note: Additional motion ignored.\n")
                self.ignore_logged_today = True

    def save_to_file(self, time_string):
        with open("med_history.txt", "a") as file:
            file.write(f"Medication taken at: {time_string}\n")
            
    def reset_system(self):
        # pill_detect.detection_enabled = False
        self.dose_taken_today = False
        self.ignore_logged_today = False

        # pill_detect.reset_daily_state()
        pill_detect.initialize_images()
        # time.sleep(1)

        # pill_detect.detection_enabled = True
        self.test_btn.config(state="normal") #reenable button
        self.status_frame.config(bg="red")
        self.status_text.config(text="MEDICATION LATE", bg="red")
        self.log.insert(tk.END, f"--- System Reset: {datetime.now().strftime('%m/%d')} ---\n")

if __name__ == "__main__":
    root = tk.Tk()
    app = care_giver_dashboard(root)
    root.mainloop()

