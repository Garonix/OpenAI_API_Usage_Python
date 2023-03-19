import requests
import sys
import json
from PyQt5.QtWidgets import QApplication, QWidget, QTextEdit, QPushButton, QLabel, QVBoxLayout, QHBoxLayout, QFileDialog
from PyQt5.QtCore import QThread
from PyQt5.QtWidgets import QTextBrowser

# The URL to access
url = "https://api.openai.com/dashboard/billing/credit_grants"

proxyDict = {
              "http"  : None,    # example: "http":"http://ip:port"
              "https" : None     # example: "https":"http://ip:port"
            }

class RequestThread(QThread):
    def __init__(self, key, index):
        super().__init__()
        self.key = key # The key to use for the request
        self.index = index # The index of the key in the input text edit

    def run(self):
        # The headers to send with the request
        headers = {
            "Authorization": f"Bearer {self.key}"
        }

        # Send a GET request and get the response
        response = requests.get(url, headers=headers, proxies=proxyDict)

        # Get the status code and the content of the response
        status_code = response.status_code
        
        content = response.content

        # Parse the content as JSON and get only the fields we need 
        data = json.loads(content) 
        total_granted = data.get("total_granted") 
        total_granted = "{:.2f}".format(float(total_granted))
        total_used = data.get("total_used") 
        total_used = "{:.2f}".format(float(total_used))
        total_available = data.get("total_available") 
        total_available = "{:.2f}".format(float(total_available))

        # Format them as a string using f-strings 
        result = f"{self.index} Total granted: {total_granted}\nTotal used: {total_used}\nTotal available: {total_available}"

        # Append the result to a global dictionary (defined later), using the key as the key
        results[self.key] = result

class MyApp(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        
        # Create a text edit for entering the keys
        self.key_edit = QTextEdit() # Use QTextEdit instead of QLineEdit
        self.key_edit.setPlaceholderText("请输入你的key, 用回车分隔")
        # Set the size
        self.key_edit.setFixedSize(600, 100)

        # set a default txt
        try: 
            file_name = "./key.txt"
            if file_name:
                # Open the file in read mode and get its content
                with open(file_name, "r") as f:
                    content = f.read()

                # Set the content to the text edit
                self.key_edit.setText(content)
        
        except: pass

        # Create a button for sending the requests
        self.send_btn = QPushButton("查询")
        self.send_btn.clicked.connect(self.send_requests)

        # Create a button for importing data from a file
        self.import_btn = QPushButton("导入")
        self.import_btn.clicked.connect(self.import_data)

        # Create a horizontal layout and add the buttons
        hbox = QHBoxLayout()
        hbox.addWidget(self.send_btn)
        hbox.addWidget(self.import_btn)

        # Create a text browser for displaying the responses
        self.response_browser = QTextBrowser() # Use QTextBrowser instead of QLabel
        # Set the size
        self.response_browser.setFixedSize(600, 300)
        # Create a vertical layout and add the widgets
        vbox = QVBoxLayout()
        vbox.addWidget(self.key_edit)
        vbox.addLayout(hbox) # Add the horizontal layout with the buttons
        vbox.addWidget(self.response_browser)

        # Set the layout and window title
        self.setLayout(vbox)
        self.setWindowTitle("api key余额查询")

    def send_requests(self):
        
        # Get the keys from the text edit and split them by ;
        keys = self.key_edit.toPlainText().split("\n")

        # Check if the keys are not empty
        if keys:
            # Create a global dictionary to store the results, keyed by the original input order
            global results
            results = {}
            index = 1 # The index of the key in the input text edit

            # Create a global list to store the threads
            global threads 
            threads = []

            # Loop through each key and create a thread for it
            for key in keys:
                thread = RequestThread(key, index) # Create a thread object with the key and the index
                thread.finished.connect(self.update_browser) # Connect the finished signal to a slot function
                threads.append(thread) # Append the thread to the list
                index += 1

            # Loop through each thread and start it
            for thread in threads:
                thread.start()

    def update_browser(self):
        # Clear the old results from the browser
        self.response_browser.clear()
        # Check if all the threads are finished
        if all(thread.isFinished() for thread in threads):
            # Sort the results by their input order
            sorted_results = [results[key] for key in self.key_edit.toPlainText().split("\n")]

            # Add the results and the indices to the final string
            output_string = ""
            index = 1
            for result in sorted_results:
                output_string += f"{result}<br>"
                index += 1

            # Use HTML tags to set different colors for each field
            output_string = output_string.replace("Total granted:", "<font color='red'>总额:</font>\n")
            output_string = output_string.replace("Total used:", "<font color='green'>已用:</font>\n")
            output_string = output_string.replace("Total available:", "<font color='blue'>可用:</font>\n")

            # Display the final string in the text browser
            self.response_browser.setText(output_string)
        
    def import_data(self):
        # Open a file dialog and get the selected file name
        file_name = QFileDialog.getOpenFileName(self, "打开文件", "", "Text Files (*.txt)")[0]

        # Check if the file name is not empty
        if file_name:
            # Open the file in read mode and get its content
            with open(file_name, "r") as f:
                content = f.read()

            # Set the content to the text edit
            self.key_edit.setText(content)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    ex = MyApp()
    ex.show()
    sys.exit(app.exec_())