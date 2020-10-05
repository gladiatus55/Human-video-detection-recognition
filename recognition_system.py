import pickle
import cv2
import tkinter as tk
from tkinter import filedialog
from tkinter import messagebox
from PIL import Image
from PIL import ImageTk
import imutils
import threading
import os
import dlib
import datetime
import numpy as np
import shutil
from imutils import paths
import time
import csv


class MainApplication(tk.Frame):
    def __init__(self, root):
        tk.Frame.__init__(self, root)
        self.parent = root
        self.menu = tk.Menu(root)
        root.config(menu=self.menu)

        self.navbar = Navbar(self, root, self.menu)
        self.toolbar = Toolbar(self, root)

        # Wrapper for settings menu on the Left and video window
        self.main_wrapper = tk.Frame(root)
        self.frame_wrapper = tk.Frame(self.main_wrapper, relief=tk.SUNKEN, borderwidth=1)
        self.video_window = tk.Label(self.main_wrapper, relief=tk.SUNKEN)

        self.main_wrapper.pack(fill=tk.BOTH, expand=True)
        self.frame_wrapper.pack(anchor=tk.CENTER, fill=tk.Y, side=tk.LEFT, expand=False)
        self.video_window.pack(anchor=tk.E, fill=tk.BOTH, expand=True, side=tk.RIGHT)
        # End of main wrapper

        self.statusbar = Statusbar(self, root)
        self.recognizer = Recognizer(self, self.frame_wrapper)
        self.encoder = Encoder(self, self.frame_wrapper)
        self.facesaver = FaceSaver(self, self.frame_wrapper)

        # Set first frame to recognizer
        self.show_recognizer()

    def show_recognizer(self):
        self.encoder.hide()
        self.facesaver.hide()
        self.recognizer.show()
        self.display_frame(None)

    def show_encoder(self):
        self.recognizer.hide()
        self.facesaver.hide()
        self.encoder.show()
        self.display_frame(None)

    def show_facesaver(self):
        self.recognizer.hide()
        self.encoder.hide()
        self.facesaver.show()
        self.display_frame(None)

    def update_statusbar(self, new_text):
        self.statusbar.set_text(new_text)

    def disable_toolbar(self):
        self.toolbar.disable()

    def enable_toolbar(self):
        self.toolbar.enable()

    def ask_exit(self):
        answer = messagebox.askquestion('Exit app?', "Do you really want to exit?")
        if answer == 'yes':
            self.quit()

    def display_frame(self, frame):
        self.video_window.configure(image=frame)
        self.video_window.image = frame

    def get_frame_resolution(self):
        return self.video_window.winfo_width(), self.video_window.winfo_height()


class PersonInfo:
    def __init__(self, name, confidentiality, image, marked_frame, detect_count):
        self.name = name
        self.confidentiality = confidentiality
        self.image = image
        self.marked_frame = marked_frame
        self.detect_count = detect_count
        self.verified = False
        self.attended = False

    def is_verified(self):
        return self.verified

    def is_attended(self):
        return self.attended


class AttendanceChecker:
    def __init__(self, whole_app, attended_students):
        self.whole_app = whole_app
        self.attended_students = attended_students
        self.student_list = list()

        for key in self.attended_students:
            self.student_list.append(key)

        self.student_counter = len(self.student_list)
        self.current_index = 0
        self.current_person = None

        self.window = tk.Toplevel()
        self.window.title("Attendance check")
        self.window.minsize(900, 700)
        tk.Label(self.window, text="Attendance check", font=('Helvetica', 20, 'bold')).pack()

        self.main_frame = tk.Frame(self.window)
        self.main_frame.pack()

        self.label_student_name = tk.Label(self.main_frame, text="No data found", font=('Helvetica', 20, 'bold'))
        self.label_student_name.grid(row=1, columnspan=2)
        self.label_percentage = tk.Label(self.main_frame, text="Percentage: ??%", font=('Helvetica', 12))
        self.label_percentage.grid(row=2, columnspan=2)
        tk.Label(self.main_frame, text="Detected image").grid(row=3, column=0)
        tk.Label(self.main_frame, text="User image").grid(row=3, column=1)

        self.image_window_1 = tk.Label(self.main_frame, relief=tk.SUNKEN)
        self.image_window_2 = tk.Label(self.main_frame, relief=tk.SUNKEN)
        self.positive_button = tk.Button(self.main_frame, text="Yes", command=self.yes_button_clicked)
        self.negative_button = tk.Button(self.main_frame, text="No", command=self.no_button_clicked)
        self.image_window_big = tk.Label(self.main_frame, relief=tk.SUNKEN)

        self.image_window_big.grid(row=0, columnspan=2, sticky='we')
        self.image_window_1.grid(row=4, column=0, padx=(15, 15))
        self.image_window_2.grid(row=4, column=1, padx=(15, 15))
        self.positive_button.grid(row=5, column=0, sticky='we', pady=20)
        self.negative_button.grid(row=5, column=1, sticky='we', pady=20)

        self.display_images()

    def close_window(self):
        self.window.destroy()

    def display_images(self):
        self.current_person = self.get_current_person()

        if self.current_person is None:
            print("[INFO] Results saved! Ending attendance..")
            self.save_attendance_info()
            self.close_window()
            return

        image = self.current_person.image
        image = imutils.resize(image, width=150, height=150)
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        image = Image.fromarray(image)
        image = ImageTk.PhotoImage(image)

        dataset_dir = os.path.join("dataset", self.current_person.name)
        images_list = list(paths.list_images(dataset_dir))

        if len(images_list) != 0:
            image_path = images_list[-1]
            image2 = cv2.imread(image_path)
            image2 = imutils.resize(image2, height=150)
            image2 = cv2.cvtColor(image2, cv2.COLOR_BGR2RGB)
            image2 = Image.fromarray(image2)
        else:
            image2 = Image.new("L", (150, 150), 100)

        image2 = ImageTk.PhotoImage(image2)

        image_big = self.current_person.marked_frame
        image_big = imutils.resize(image_big, width=600)
        image_big = cv2.cvtColor(image_big, cv2.COLOR_BGR2RGB)
        image_big = Image.fromarray(image_big)
        image_big = ImageTk.PhotoImage(image_big)

        self.image_window_1.configure(image=image)
        self.image_window_1.image = image
        self.image_window_2.configure(image=image2)
        self.image_window_2.image = image2
        self.image_window_big.configure(image=image_big)
        self.image_window_big.image = image_big

        name_with_id = self.current_person.name.split("_")
        surname = name_with_id[0]
        firstname = name_with_id[1]
        person_id = name_with_id[-1]

        self.label_student_name.config(text="Name: {} {}, id: {}".format(surname, firstname, person_id))
        self.label_percentage.config(text="Confidentiality: {:.2f}%"
                                     .format(min(self.current_person.confidentiality+0.1, 1) * 100))

    def next_image(self):
        self.current_index += 1
        self.display_images()

    def yes_button_clicked(self):
        self.current_person.verified = True
        self.current_person.attended = True
        self.next_image()

    def no_button_clicked(self):
        self.current_person.verified = True
        self.current_person.attended = False
        self.next_image()

    def get_current_person(self):
        if self.current_index == self.student_counter:
            return None
        name_key = self.student_list[self.current_index]

        return self.attended_students[name_key]

    def save_attendance_info(self):
        date_time = datetime.datetime.now()
        timestamp_str = str(date_time.strftime("%Y-%m-%d_%H-%M"))
        file_path = "output_attendance_csv/output" + timestamp_str + ".csv"
        w = csv.writer(open(file_path, "w", newline=''))

        w.writerow(["Surname", "Name", "ID", "Reliability", "Status"])

        for name, student_info in self.attended_students.items():
            name_with_id = name.split("_")
            surname = name_with_id[0]
            firstname = name_with_id[1]
            person_id = name_with_id[-1]
            percentage = "{:.2f}%".format(min(student_info.confidentiality+0.1, 1) * 100)
            attended = student_info.is_attended()
            verified = student_info.is_verified()
            if verified:
                status = "ATTENDED" if attended else "NOT ATTENDED"
            else:
                status = "NOT VERIFIED"
            w.writerow([surname, firstname, person_id, percentage, status])

        self.whole_app.update_statusbar("[INFO] Attendance saved into file: {}".format(file_path))


class Navbar:
    def __init__(self, whole_app, parent, menu_obj):
        self.navbar = tk.Frame(parent)
        self.navbar.pack(side="left", fill="y")
        self.whole_app = whole_app

        # Top navigation bar
        self.subMenu = tk.Menu(menu_obj, tearoff=0)
        menu_obj.add_cascade(label="File", menu=self.subMenu)
        self.subMenu.add_command(label="Exit", command=self.ask_exit)

    def ask_exit(self):
        self.whole_app.ask_exit()


class Toolbar:
    def __init__(self, whole_app, parent):
        self.whole_app = whole_app
        self.toolbar = tk.Frame(parent)
        self.toolbar.pack()

        # Toolbar buttons for mode switching
        self.button_recognizer = tk.Button(self.toolbar, text="Recognizer", command=self.open_recognizer)
        self.button_recognizer.pack(side=tk.LEFT, padx=2, pady=2)
        self.button_encoder = tk.Button(self.toolbar, text="Encoder", command=self.open_encoder)
        self.button_encoder.pack(side=tk.LEFT, padx=2, pady=2)
        self.button_facesaver = tk.Button(self.toolbar, text="Save new faces", command=self.open_facesaver)
        self.button_facesaver.pack(side=tk.LEFT, padx=2, pady=2)
        self.button_quit = tk.Button(self.toolbar, text="exit", command=self.ask_exit)
        self.button_quit.pack(side=tk.RIGHT)

        self.toolbar.pack(side=tk.TOP, fill=tk.X)

    def open_recognizer(self):
        self.whole_app.show_recognizer()

    def open_encoder(self):
        self.whole_app.show_encoder()

    def open_facesaver(self):
        self.whole_app.show_facesaver()

    def ask_exit(self):
        self.whole_app.ask_exit()

    def disable(self):
        self.button_recognizer.config(state="disabled")
        self.button_encoder.config(state="disabled")
        self.button_facesaver.config(state="disabled")

    def enable(self):
        self.button_recognizer.config(state="normal")
        self.button_encoder.config(state="normal")
        self.button_facesaver.config(state="normal")


class Statusbar:
    def __init__(self, whole_app, parent):
        self.whole_app = whole_app
        # Status bar at the bottom
        self.label_statusbar = tk.Label(parent, text="[INFO] Ready to use", bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.label_statusbar.pack(side=tk.BOTTOM, fill=tk.X)

    def set_text(self, new_text):
        self.label_statusbar.configure(text=new_text)


class Encoder:
    def __init__(self, whole_app, frame_wrapper):
        self.whole_app = whole_app
        self.frame_encoder_main = tk.Frame(frame_wrapper, relief=tk.SUNKEN, borderwidth=1)

        # *** FRAME RADIO BUTTONS ***
        # Radio button wrapper, radios, directory select entry + btn
        self.frame_radio_btn = tk.Frame(self.frame_encoder_main)
        self.frame_radio_btn.grid(row=0, pady=20)

        # Values of radio buttons (default, custom)
        self.rad_values = tk.StringVar()
        self.rad_values.set("default")

        # Label "Dataset location:"
        label_dataset_location = tk.Label(self.frame_radio_btn, text="Dataset location")
        label_dataset_location.editable = True
        label_dataset_location.grid(row=0)

        # Radio buttons for dataset location
        radio_1 = tk.Radiobutton(self.frame_radio_btn, text="Default location (/dataset)", value="default",
                                 variable=self.rad_values,
                                 command=self.radio_event)
        radio_1.editable = True
        radio_1.grid(row=1, sticky=tk.NSEW)
        radio_2 = tk.Radiobutton(self.frame_radio_btn, text="Custom location", value="custom", variable=self.rad_values,
                                 command=self.radio_event)
        radio_2.editable = True
        radio_2.grid(row=2, sticky=tk.NSEW)

        # Entry to visualize selected custom path
        self.entry_selected_path = tk.Entry(self.frame_radio_btn, width=55, state="disabled")
        self.entry_selected_path.editable = False

        # Button that opens file explorer to select directory
        self.button_dataset_dir_select = tk.Button(self.frame_radio_btn, text="Select directory",
                                                   command=self.select_dataset_directory)
        self.button_dataset_dir_select.editable = True
        # *** END FRAME RADIO BUTTONS ***

        # *** FRAME OTHERS ***
        # Frame that contains encoding location
        self.frame_others = tk.Frame(self.frame_encoder_main)
        self.frame_others.grid(row=1)

        # Label "Encodings location:"
        label_encodings_location = tk.Label(self.frame_others, text="Encodings location:")
        label_encodings_location.pack()
        label_encodings_location.editable = True

        # Entry with encoding location, not editable
        self.entry_encodings_location = tk.Entry(self.frame_others, width=55, justify=tk.CENTER)
        self.entry_encodings_location.insert(0, "res/encodings/face_encodings.pickle")
        self.entry_encodings_location.configure(state="disabled")
        self.entry_encodings_location.pack()
        self.entry_encodings_location.editable = False
        # *** END FRAME OTHERS***

        # *** BUTTONS FRAME ***
        # buttons START and STOP, backup checkbox, encoding progress
        self.frame_buttons = tk.Frame(self.frame_encoder_main)
        self.frame_buttons.grid(row=2)

        self.button_start_encodings = tk.Button(self.frame_buttons, text="START Encoding",
                                                command=self.button_start_clicked)
        self.button_start_encodings.grid(row=0, pady=(30, 0))
        self.button_stop_encodings = tk.Button(self.frame_buttons, text="Encoding..", command=self.button_stop_clicked)
        self.button_stop_encodings.configure(state="disabled")

        # Checkbox value (True, False) for backup
        self.backup_encodings_cb_value = tk.BooleanVar()
        self.backup_encodings_checkbox = tk.Checkbutton(self.frame_buttons, text="Backup last encodings",
                                                        variable=self.backup_encodings_cb_value)
        self.backup_encodings_checkbox.grid(row=1)

        # Encoding progress label
        self.label_processed_info = tk.Label(self.frame_buttons)
        self.label_processed_info.grid(row=2)
        # *** END BUTTONS FRAME ***

        self.list_image_paths = None
        self.encodings_list = None
        self.names_list = None
        self.current_index = 0
        self.image_paths_length = 0
        self.encoded_counter = 0
        self.encoding_output_src = ""
        self.encoding_output_txt_src = ""

    def show(self):
        self.frame_encoder_main.pack(pady=20)

    def hide(self):
        self.frame_encoder_main.pack_forget()

    def radio_event(self):
        selected_rad = self.rad_values.get()

        if selected_rad == "default":
            self.entry_selected_path.grid_forget()
            self.button_dataset_dir_select.grid_forget()
            pass
        elif selected_rad == "custom":
            messagebox.showinfo("Warning", "Directory must follow the following structure: "
                                           "\n\ndirectory/surname_name_id/photo!")
            self.entry_selected_path.grid(row=3)
            self.button_dataset_dir_select.grid(row=4)

    def select_dataset_directory(self):
        filename = filedialog.askdirectory()
        self.entry_selected_path.configure(state="normal")
        self.entry_selected_path.delete(0)
        self.entry_selected_path.insert(0, str(filename))
        self.entry_selected_path.configure(state="disabled")

    def button_start_clicked(self):
        backup_bool = self.backup_encodings_cb_value.get()
        selected_radio_btn = self.rad_values.get()
        dataset_dir = self.entry_selected_path.get()

        self.disable_settings()
        self.whole_app.disable_toolbar()

        if selected_radio_btn == "default":
            self.run_encoder(backup=backup_bool)
        elif selected_radio_btn == "custom":
            self.run_encoder(dataset_src=dataset_dir, backup=backup_bool)

    def button_stop_clicked(self):
        self.enable_settings()
        self.whole_app.enable_toolbar()

    def enable_settings(self):
        self.button_stop_encodings.grid_forget()
        self.button_start_encodings.grid(row=0, pady=(30, 0))
        for widget in self.frame_radio_btn.winfo_children():
            if widget.editable:
                widget.config(state="normal")
        for widget in self.frame_others.winfo_children():
            if widget.editable:
                widget.config(state="normal")
        self.backup_encodings_checkbox.config(state="normal")

    def disable_settings(self):
        self.button_start_encodings.grid_forget()
        self.button_stop_encodings.grid(row=0, pady=(30, 0))
        for widget in self.frame_radio_btn.winfo_children():
            if widget.editable:
                widget.config(state="disabled")
        for widget in self.frame_others.winfo_children():
            if widget.editable:
                widget.config(state="disabled")
        self.backup_encodings_checkbox.config(state="disabled")

    def run_encoder(self, dataset_src="dataset", backup=False):
        """
            Encode face images from dataset and serialize encodings into pickle file
            :param dataset_src: path to dataset folder that contains images of known persons
            :param backup: boolean, if true old encoding file is backuped

            :return nothing, void function
        """
        # making encodings file path
        encodings_path = os.path.join("res", "encodings", "face_encodings.pickle")

        # if it exists and backup is checked, old encoding will be duplicated as backup
        # name of the backup file will be "encodings_backup_*date*", *date* is current date YYYY-MM-DD_HH-MM
        if os.path.isfile(encodings_path) and backup is True:
            timestamp = datetime.datetime.now()
            current_date_string = str(timestamp.strftime("%Y-%m-%d_%H-%M"))
            if os.path.isfile(encodings_path):
                backup_src = os.path.join("res", "encodings",
                                          "face_encodings_backup_" + current_date_string + ".pickle")
                shutil.copy(encodings_path, backup_src)
            else:
                message_out = "[INFO] Cannot make backup - encodings not exist!"
                print(message_out)
                self.whole_app.update_statusbar(message_out)

        # initialize lists of image paths, encoding vectors and names
        self.list_image_paths = list(paths.list_images(dataset_src))
        self.encodings_list = []
        self.names_list = []

        # make output file names
        self.encoding_output_src = encodings_path
        self.encoded_counter = 0
        self.current_index = 0
        self.image_paths_length = len(self.list_image_paths)

        if self.image_paths_length == 0:
            message_out = "[INFO] Dataset is empty!"
            print(message_out)
            messagebox.showinfo("Error", "Dataset is empty. Create some training photo first!\n"
                                         "Note: Use the facesaver from the menu")
            self.whole_app.update_statusbar(message_out)
            self.button_stop_clicked()
        else:
            message_out = "[INFO] Encoder started"
            print(message_out)
            self.whole_app.update_statusbar(message_out)
            self.encode_loop()

    def encode_loop(self):

        image_path = self.list_image_paths[self.current_index]

        name = image_path.split(os.path.sep)[-2]

        print("[INFO] processing image {} of {} / (Dir: {})".format(self.current_index + 1,
                                                                    self.image_paths_length, name))
        self.label_processed_info.config(text="Processed {} of {} (Dir: {})".format(self.current_index + 1,
                                                                                    self.image_paths_length, name))

        # load the input image and convert it from BGR (OpenCV order) to RGB
        image = cv2.imread(image_path)
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        # Detect and compute the facial embedding vector for the face
        encodings = face_encodings(rgb_image)

        for encoding in encodings:
            # each encoding and name of person is added to the list of encodings and names
            self.encodings_list.append(encoding)
            self.names_list.append(name)
            self.encoded_counter += 1

        self.current_index += 1

        if self.current_index < self.image_paths_length:
            self.whole_app.video_window.after(20, self.encode_loop)
        else:
            self.end_loop()

    def end_loop(self):
        print(
            "[INFO] Successfully encoded {} of total {} pictures".format(self.encoded_counter, self.image_paths_length))

        print("[INFO] Writing encodings to disk")

        # create dictionary from encodings and names lists
        dict_data = {"encodings": self.encodings_list, "names": self.names_list}

        # write pickle-converted binary dictionary data to disk
        pickle_binary_file = open(self.encoding_output_src, "wb")
        pickle_binary_file.write(pickle.dumps(dict_data))
        pickle_binary_file.close()

        self.label_processed_info.config(text="Successfully encoded {} of total {} pictures!".format(
            self.encoded_counter, self.image_paths_length))

        self.button_stop_clicked()
        message_out = "[INFO] Encoding complete"
        print(message_out)
        self.whole_app.update_statusbar(message_out)


class FaceSaver:
    def __init__(self, whole_app, frame_wrapper):
        self.whole_app = whole_app

        # *** MAIN FACESAVER FRAME ***
        # Include 3 entries -> name, ID and photo count + BUTTON for start face saver
        self.frame_facesaver_main = tk.Frame(frame_wrapper, relief=tk.SUNKEN, borderwidth=1)

        # NAME label + entry
        label_name = tk.Label(self.frame_facesaver_main, text="Name:")
        label_name.grid(row=0, column=0)
        self.entry_name = tk.Entry(self.frame_facesaver_main, width=55, justify=tk.CENTER)
        self.entry_name.grid(row=1)

        label_name = tk.Label(self.frame_facesaver_main, text="Surname:")
        label_name.grid(row=2, column=0)
        self.entry_surname = tk.Entry(self.frame_facesaver_main, width=55, justify=tk.CENTER)
        self.entry_surname.grid(row=3)

        # ID label + entry
        label_id = tk.Label(self.frame_facesaver_main, text="ID: ")
        label_id.grid(row=4)
        self.entry_id = tk.Entry(self.frame_facesaver_main, width=55, justify=tk.CENTER)
        self.entry_id.grid(row=5)

        # PHOTO COUNT label + entry
        label_photo_count = tk.Label(self.frame_facesaver_main, text="Photo count: ")
        label_photo_count.grid(row=6)
        self.entry_photo_count = tk.Entry(self.frame_facesaver_main, width=55, justify=tk.CENTER)
        self.entry_photo_count.insert(tk.END, "30")
        self.entry_photo_count.grid(row=7)

        # CHECKBOX save all without name into 1 unsorted directory
        self.save_all_cb_value = tk.BooleanVar()
        self.save_all_checkbox = tk.Checkbutton(self.frame_facesaver_main,
                                                text="Save without name (unsorted directory)",
                                                variable=self.save_all_cb_value, command=self.cbutton_save_all_clicked)
        self.save_all_checkbox.grid(row=8)

        self.from_video_cb_value = tk.BooleanVar()
        self.from_video_checkbox = tk.Checkbutton(self.frame_facesaver_main,
                                                  text="From video file",
                                                  variable=self.from_video_cb_value,
                                                  command=self.cbutton_from_vid_clicked)

        # SubFRAME for video select button and entry
        self.subframe = tk.Frame(self.frame_facesaver_main)

        # SELECT VIDEO BUTTON
        self.entry_selected_path = tk.Entry(self.subframe, width=55, state="disabled")
        self.entry_selected_path.pack()
        self.button_select_video = tk.Button(self.subframe, text="Select video",
                                             command=self.select_file_video)
        self.button_select_video.pack()

        # START and STOP BUTTON
        self.button_start_facesaver = tk.Button(self.frame_facesaver_main, text="START FaceSaver",
                                                command=self.button_start_clicked)
        self.button_start_facesaver.grid(row=11, pady=(30, 0))
        self.button_stop_facesaver = tk.Button(self.frame_facesaver_main, text="STOP",
                                               command=self.button_stop_clicked)

        self.stream = None
        self.frame = None
        self.thread = None
        self.captured_photos_count = 0
        self.max_photos = 30
        self.current_date_string = ""
        self.person_dataset_dir = ""
        self.videosrc = None
        self.stop_event = threading.Event()
        self.stop_event.set()
        self.stop_count = 0

    def button_start_clicked(self):
        person_name = self.entry_name.get()
        person_surname = self.entry_surname.get()
        person_id = self.entry_id.get()
        save_unsorted = self.save_all_cb_value.get()
        save_from_video = self.from_video_cb_value.get()

        message_out = "[INFO] Face saver started"
        self.whole_app.update_statusbar(message_out)
        print(message_out)

        photo_count = 0
        self.stop_count = 0
        self.videosrc = 0

        if not save_unsorted:
            if person_name == "" or person_surname == "" or person_id == "":
                message_out = "[ERROR] Person name, surname or ID empty!"
                messagebox.showinfo("Error", "Person name, surname or ID is empty! \nPlease fill in all fields")
                print(message_out)
                self.whole_app.update_statusbar(message_out)
                return

            try:
                photo_count = int(self.entry_photo_count.get())
            except ValueError:
                message_out = "[ERROR] Photo count not INTEGER!"
                messagebox.showinfo("Error", "Photo count include non-numeric characters!")
                print(message_out)
                self.whole_app.update_statusbar(message_out)
                return
        else:
            if save_from_video:
                if self.entry_selected_path.get() != "":
                    self.videosrc = self.entry_selected_path.get()
                else:
                    self.videosrc = 0
            else:
                self.videosrc = 0

        self.disable_settings()
        self.button_start_facesaver.grid_forget()
        self.button_stop_facesaver.grid(row=11, pady=(30, 0))
        self.whole_app.disable_toolbar()

        if save_unsorted:
            self.run_facesaver("", "", 0, self.videosrc, 0, save_unsorted)
        elif photo_count > 0:
            self.run_facesaver(person_name, person_surname, person_id, 0, photo_count)
        else:
            self.run_facesaver(person_name, person_surname, person_id, 0)

    def button_stop_clicked(self):
        self.stop_event.set()
        self.enable_settings()
        self.cbutton_save_all_clicked()
        self.button_stop_facesaver.grid_forget()
        self.button_start_facesaver.grid(row=11, pady=(30, 0))
        self.whole_app.enable_toolbar()

    def cbutton_save_all_clicked(self):
        cb_value = self.save_all_cb_value.get()
        if cb_value:
            self.disable_field_settings()
            self.from_video_checkbox.grid(row=9)
            self.cbutton_from_vid_clicked()
        else:
            self.enable_field_settings()
            self.from_video_checkbox.grid_forget()
            self.subframe.grid_forget()

    def cbutton_from_vid_clicked(self):
        cb_value = self.from_video_cb_value.get()
        if cb_value:
            self.subframe.grid(row=10)
        else:
            self.subframe.grid_forget()

    def select_file_video(self):
        path = filedialog.askopenfilename(initialdir="/", title="Select file",
                                          filetypes=(("mp4 files", "*.mp4"), ("avi files", "*.avi")))
        if str(path) is not "":
            self.entry_selected_path.config(state="normal")
            self.entry_selected_path.delete(0, tk.END)
            self.entry_selected_path.insert(0, str(path))
            self.entry_selected_path.config(state="disable")

    def show(self):
        self.frame_facesaver_main.pack(pady=20)

    def hide(self):
        self.frame_facesaver_main.pack_forget()

    def enable_field_settings(self):
        self.entry_name.config(state="normal")
        self.entry_surname.config(state="normal")
        self.entry_id.config(state="normal")
        self.entry_photo_count.config(state="normal")

    def disable_field_settings(self):
        self.entry_name.config(state="disabled")
        self.entry_surname.config(state="disabled")
        self.entry_id.config(state="disabled")
        self.entry_photo_count.config(state="disabled")

    def enable_settings(self):
        self.enable_field_settings()
        self.button_select_video.config(state="normal")
        self.from_video_checkbox.config(state="normal")
        self.save_all_checkbox.config(state="normal")

    def disable_settings(self):
        self.disable_field_settings()
        self.button_select_video.config(state="disabled")
        self.from_video_checkbox.config(state="disabled")
        self.save_all_checkbox.config(state="disabled")

    def run_facesaver(self, person_name, person_surname, person_id, camera_src, number_of_photo=30,
                      save_unsorted=False):
        """
            Capture face images of person and save them to dataset directory
            :param save_unsorted: save unsorted into unsorted-directory
            :param person_name: name of person
            :param person_surname: surname of person
            :param person_id: id of person
            :param camera_src:  a video source, f.e. 0 is webcam, string is path to source
            :param number_of_photo:  number of pictures to be taken, default is 30

            :return nothing, void function
        """

        # Initialize the camera from source
        self.stream = cv2.VideoCapture(camera_src)

        # Building directory where photos will be saved [name_surname_id]
        # spaces filled with underscore "_" + added person id, then placed in /dataset/ directory
        if not save_unsorted:
            person_name = person_name.replace(" ", "_")
            person_surname = person_surname.replace(" ", "_")
            person_directory = "{}_{}_{}".format(person_surname, person_name, person_id)
            dataset_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dataset')
            self.person_dataset_dir = os.path.join(dataset_dir, person_directory)

            # if directory doesn't exists, it will be created
            if not os.path.exists(self.person_dataset_dir):
                print("[INFO] Directory not found. Creating new...")
                os.makedirs(self.person_dataset_dir)
        else:
            self.person_dataset_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dataset_unsorted')

        # variables that count how many photos have been captured, maximum photos to be taken
        # current timestamp is used to create an image filename
        self.captured_photos_count = 0
        self.max_photos = number_of_photo
        timestamp = datetime.datetime.now()
        self.current_date_string = str(timestamp.strftime("%Y-%m-%d_%H-%M-%S_"))

        print("[INFO] Initializing face capturing and detection")
        if self.stop_event.is_set():
            self.stop_event.clear()
            if save_unsorted:
                self.video_loop_unsorted()
            else:
                self.video_loop()

    def video_loop_unsorted(self):
        try:
            if not self.stop_event.is_set():
                # Get current frame from camera
                (grabbed, self.frame) = self.stream.read()

                if grabbed:
                    faces = detect_faces_haar(self.frame, scale_factor=1.3, min_neighbors=5)

                    marked_frame = self.frame.copy()
                    for (x, y, w, h) in faces:
                        x -= 10
                        y -= 10
                        w += 20
                        h += 20

                        # cropped face from color frame
                        subface = self.frame[y:y + h, x:x + w]

                        filtered_face = hog_face_detector(subface, 1)
                        if len(filtered_face) > 0:
                            self.captured_photos_count += 1
                            self.whole_app.update_statusbar(
                                "[INFO] Captured {} photo(s)".format(self.captured_photos_count))
                            photo_name = self.current_date_string + str(self.captured_photos_count) + ".jpg"
                            photo_path = os.path.join(self.person_dataset_dir, photo_name)
                            cv2.imwrite(photo_path, subface)
                            # visualize detected face frame
                            cv2.rectangle(marked_frame, (x, y), (x + w, y + h), (255, 0, 0), 2)

                    show_frame_width, show_frame_height = self.whole_app.get_frame_resolution()

                    if show_frame_width < marked_frame.shape[1] or show_frame_height < marked_frame.shape[0]:
                        marked_frame = imutils.resize(marked_frame, width=show_frame_width, height=show_frame_height)

                    displayed_frame = cv2.cvtColor(marked_frame, cv2.COLOR_BGR2RGB)
                    displayed_frame = Image.fromarray(displayed_frame)
                    displayed_frame = ImageTk.PhotoImage(displayed_frame)

                    self.whole_app.display_frame(displayed_frame)
                else:
                    self.stop_event.set()
            else:
                self.stop_count += 1
        except RuntimeError:
            print("[ERROR] caught a RuntimeError")

        if self.stop_count < 10:
            if self.videosrc == 0:
                self.whole_app.video_window.after(100, self.video_loop_unsorted)
            else:
                self.whole_app.video_window.after(5, self.video_loop_unsorted)
        else:
            print("\n [INFO] Successfully closing camera and cleaning stuff")
            message_out = "[INFO] Face saver ended. images saved to: {}".format(self.person_dataset_dir)
            self.whole_app.update_statusbar(message_out)
            print(message_out)
            cv2.destroyAllWindows()
            self.stream.release()
            self.button_stop_clicked()

    def video_loop(self):
        try:
            if not self.stop_event.is_set():
                # Get current frame from camera
                (grabbed, self.frame) = self.stream.read()

                if grabbed:
                    face = detect_faces_haar(self.frame, scale_factor=1.3, min_neighbors=5)
                    if len(face) == 1:
                        for (x, y, w, h) in face:
                            x -= 10
                            y -= 10
                            w += 20
                            h += 20

                            # cropped face from color frame
                            subface = self.frame[y:y + h, x:x + w]

                            # increment capture counter and save cropped face into dataset
                            self.captured_photos_count += 1
                            message_out = "[INFO] Captured photo {} of max {}".format(self.captured_photos_count,
                                                                                      self.max_photos)
                            print(message_out)
                            self.whole_app.update_statusbar(message_out)
                            photo_name = self.current_date_string + str(self.captured_photos_count) + ".jpg"
                            photo_path = os.path.join(self.person_dataset_dir, photo_name)
                            cv2.imwrite(photo_path, subface)

                            # visualize detected face frame
                            cv2.rectangle(self.frame, (x, y), (x + w, y + h), (255, 0, 0), 2)
                    elif len(face) > 1:
                        self.display_text(self.frame, "Multiple faces detected!", "red")

                    if self.captured_photos_count == self.max_photos:
                        self.display_text(self.frame, "Capture successfully ended", "green")

                    displayed_frame = cv2.cvtColor(self.frame, cv2.COLOR_BGR2RGB)
                    displayed_frame = Image.fromarray(displayed_frame)
                    displayed_frame = ImageTk.PhotoImage(displayed_frame)

                    self.whole_app.display_frame(displayed_frame)
                else:
                    self.stop_event.set()
            else:
                self.stop_count += 1
        except RuntimeError:
            print("[ERROR] caught a RuntimeError")

        if self.stop_count < 10 and self.captured_photos_count < self.max_photos:
            self.whole_app.video_window.after(100, self.video_loop)
        else:
            print("\n [INFO] Successfully closing camera and cleaning stuff")
            message_out = "[INFO] Face saver ended. images saved to: {}".format(self.person_dataset_dir)
            self.whole_app.update_statusbar(message_out)
            print(message_out)
            cv2.destroyAllWindows()
            self.stream.release()
            self.button_stop_clicked()

    def display_text(self, frame, text, color):
        font = cv2.FONT_HERSHEY_SIMPLEX
        text_size = cv2.getTextSize(text, font, 0.75, 2)[0]
        # get coords based on boundary
        text_x = int((frame.shape[1] - text_size[0]) / 2)
        text_y = frame.shape[0] - 20
        # add text centered on image
        if color == "red":
            cv2.putText(frame, text, (text_x, text_y), font, 0.75, (0, 0, 255), 2)
        if color == "green":
            cv2.putText(frame, text, (text_x, text_y), font, 0.75, (0, 255, 0), 2)


class Recognizer:
    def __init__(self, whole_app, frame_wrapper):
        self.whole_app = whole_app

        # *** MAIN FACE RECOGNIZER FRAME ***
        # include radio buttons, attribute settings frames, video source selector
        self.frame_recognizer_main = tk.Frame(frame_wrapper, relief=tk.SUNKEN, borderwidth=1)

        # *** RADIO BUTTONS FRAME ***
        # radio buttons for video or camera select
        self.radio_btn_frame = tk.Frame(self.frame_recognizer_main)
        self.radio_btn_frame.grid(row=0, column=0, sticky=tk.E, padx=20, pady=20)

        # Selected video radio button as first
        self.rad_values = tk.StringVar()
        self.rad_values.set("video")

        # label "Select capture device"
        label_source_choose = tk.Label(self.radio_btn_frame, text="Select capture device")
        label_source_choose.grid(row=0, columnspan=3)

        # Radio buttons video or camera
        radio_1 = tk.Radiobutton(self.radio_btn_frame, text="From video", value="video", variable=self.rad_values,
                                 command=self.radio_event)
        radio_2 = tk.Radiobutton(self.radio_btn_frame, text="From camera", value="camera", variable=self.rad_values,
                                 command=self.radio_event)
        radio_1.grid(row=1, column=0, sticky=tk.W)
        radio_2.grid(row=2, column=0, sticky=tk.W)

        # *** END RADIO BUTTONS FRAME ***

        # Border between radio buttons and attributes
        border = tk.Label(self.frame_recognizer_main, relief=tk.SUNKEN, borderwidth="0.05px", bg="black")
        border.grid(row=0, column=1, sticky=tk.NS)
        # END border

        # *** ATTRIBUTE SETTINGS FRAME ***
        # attributes for recognizer function
        self.attr_settings_frame = tk.Frame(self.frame_recognizer_main)
        self.attr_settings_frame.grid(row=0, column=2, sticky=tk.NSEW, padx=20, pady=20)

        # checkbox values (True, False)
        self.save_video_cb_value = tk.BooleanVar()
        self.save_faces_cb_value = tk.BooleanVar()
        self.save_aligned_cb_value = tk.BooleanVar()

        # Label "Video settings" and checkboxes
        self.settings_label = tk.Label(self.attr_settings_frame, text="Video settings")
        self.save_video_checkbox = tk.Checkbutton(self.attr_settings_frame, text="Save video",
                                                  variable=self.save_video_cb_value)
        self.save_faces_checkbox = tk.Checkbutton(self.attr_settings_frame, text="Save faces?",
                                                  variable=self.save_faces_cb_value)
        self.save_aligned_checkbox = tk.Checkbutton(self.attr_settings_frame, text="Save aligned faces?",
                                                    variable=self.save_aligned_cb_value)

        # Positioning of checkboxes + label
        self.settings_label.grid(row=0)
        self.save_video_checkbox.grid(row=1, column=0, sticky=tk.W)
        self.save_faces_checkbox.grid(row=2, column=0, sticky=tk.W)
        self.save_aligned_checkbox.grid(row=3, column=0, sticky=tk.W)
        # *** END ATTRIBUTE SETTINGS FRAME ***

        # *** VIDEO SRC file explorer selector and START button FRAME ***
        self.frame_videosrc_wrapper = tk.Frame(self.frame_recognizer_main)

        # Video source location, entry disabled
        self.entry_selected_path = tk.Entry(self.frame_videosrc_wrapper, width=55, state="disabled")

        # Select button
        self.button_video_select = tk.Button(self.frame_videosrc_wrapper, text="Select video",
                                             command=self.select_file_video)
        self.label_path_title = tk.Label(self.frame_videosrc_wrapper, text="Source path: ")

        self.button_video_select.visible = False
        self.button_video_select.grid(row=3, padx="10", pady="10", columnspan=3)
        self.entry_selected_path.grid(row=2, column=1)

        # START and STOP buttons
        self.button_start_recognizer = tk.Button(self.frame_videosrc_wrapper, text="START Recognizer",
                                                 command=self.button_start_clicked)
        self.button_start_recognizer.grid(row=4, columnspan=4, pady=(30, 0))

        self.button_stop_recognizer = tk.Button(self.frame_videosrc_wrapper, text="STOP",
                                                command=self.button_stop_clicked)
        # *** END VIDEO SRC file explorer selector FRAME ***

        self.radio_event()

        self.writer = None
        self.start_timestamp = 0
        self.fps = 0
        self.output_src = ""
        self.stream = None
        self.save_video = False
        self.src = None
        self.extracted_data = None
        self.save_faces = None
        self.save_aligned = None
        self.measure_time = False
        self.stop_event = threading.Event()
        self.stop_event.set()
        self.attended_students = None
        self.student_reliability = None
        self.student_pictures = None
        self.date_time = None

    def show(self):
        self.frame_recognizer_main.pack(pady=20)
        self.frame_videosrc_wrapper.grid(row=1, columnspan=3, pady=(20, 0))

    def hide(self):
        self.frame_recognizer_main.pack_forget()
        self.frame_videosrc_wrapper.grid_forget()

    def button_start_clicked(self):
        source_path = self.entry_selected_path.get()
        selected_btn = self.rad_values.get()

        if self.stop_event.is_set():
            self.stop_event.clear()

        self.disable_settings()
        self.whole_app.disable_toolbar()

        if selected_btn == "camera":
            self.run_recognition(0, save_video=self.save_video_cb_value.get(),
                                 save_faces=self.save_faces_cb_value.get(),
                                 save_aligned=self.save_aligned_cb_value.get())

        elif selected_btn == "video":
            if source_path == "":
                self.stop_event.set()
                self.enable_settings()
                self.whole_app.enable_toolbar()
                message_out = "[ERROR] You have to enter video source"
                print(message_out)
                messagebox.showinfo("Error", "Selected recognition from video. \nYou have to enter video source!")
                self.whole_app.update_statusbar(message_out)
                return

            self.run_recognition(source_path, save_video=self.save_video_cb_value.get(),
                                 save_faces=self.save_faces_cb_value.get(),
                                 save_aligned=self.save_aligned_cb_value.get(),
                                 measure_time=True)

        message_out = "[INFO] Recognizer started"
        print(message_out)
        self.whole_app.update_statusbar(message_out)

    def button_stop_clicked(self):
        self.enable_settings()
        self.whole_app.enable_toolbar()
        self.stop_event.set()

    def enable_settings(self):
        self.button_stop_recognizer.grid_forget()
        self.button_start_recognizer.grid(row=4, columnspan=4, pady=(30, 0))
        for widget in self.attr_settings_frame.winfo_children():
            widget.config(state="normal")
        for widget in self.radio_btn_frame.winfo_children():
            widget.config(state="normal")
        self.button_video_select.config(state="normal")

    def disable_settings(self):
        self.button_start_recognizer.grid_forget()
        self.button_stop_recognizer.grid(row=4, columnspan=4, pady=(30, 0))
        for widget in self.attr_settings_frame.winfo_children():
            widget.config(state="disabled")
        for widget in self.radio_btn_frame.winfo_children():
            widget.config(state="disabled")
        self.button_video_select.config(state="disabled")

    def radio_event(self):
        selected_rad = self.rad_values.get()

        if selected_rad == "video":
            self.hide_button(selected_rad)
        elif selected_rad == "camera":
            self.hide_button(selected_rad)

    def select_file_video(self):
        path = filedialog.askopenfilename(initialdir="/", title="Select file",
                                          filetypes=(("mp4 files", "*.mp4"), ("avi files", "*.avi")))
        if str(path) is not "":
            self.entry_selected_path.config(state="normal")
            self.entry_selected_path.delete(0, tk.END)
            self.entry_selected_path.insert(0, str(path))
            self.entry_selected_path.config(state="disable")

    def hide_button(self, button_type):
        video_btn_changed = False

        if button_type == "video":
            if not self.button_video_select.visible:
                self.button_video_select.grid(row=3, columnspan=4, padx="10", pady="10")
                self.label_path_title.grid(row=1)
                video_btn_changed = True
                self.entry_selected_path.grid(row=2, column=0)
        elif button_type == "camera":
            if self.button_video_select.visible:
                self.button_video_select.grid_forget()
                self.entry_selected_path.grid_forget()
                self.label_path_title.grid_forget()
                video_btn_changed = True

        if video_btn_changed:
            self.button_video_select.visible = not self.button_video_select.visible

    def run_recognition(self, src, save_video=False, save_faces=False, save_aligned=False, measure_time=False):
        """
        Recognize faces in video and launch attendance checker after execution.
        :param src: source to video file or camera
        :param save_video: boolean, if true, processed video is saved
        :param save_faces: boolean, if true, detected faces are saved
        :param save_aligned: boolean, if true, aligned detected faces are saved
        :param measure_time: boolean, if true, running time is recorded
        :return: nothing, void function
        """
        self.writer = None
        self.start_timestamp = time.time()
        self.date_time = datetime.datetime.now()
        self.fps = 1
        self.output_src = ""
        self.save_video = save_video
        self.save_faces = save_faces
        self.save_aligned = save_aligned
        self.measure_time = measure_time
        self.attended_students = dict()
        self.student_reliability = dict()
        self.student_pictures = dict()

        encoding_src = "res/encodings/face_encodings.pickle"
        if os.path.isfile(encoding_src):
            self.extracted_data = pickle.loads(open(encoding_src, "rb").read())
        else:
            message_out = "[ERROR] Encodings not found! Make one first."
            print(message_out)
            messagebox.showinfo("Error", "Encodings file was not found. Create one first!\n"
                                         "Note: Use the encoder from the menu")
            self.whole_app.update_statusbar(message_out)
            self.button_stop_clicked()
            return

        if save_video:
            current_date_string = str(self.date_time.strftime("%Y-%m-%d_%H-%M"))
            output_video_name = "video_" + current_date_string + ".mp4"
            self.output_src = "saved_videos/" + output_video_name

        self.stream = cv2.VideoCapture(src)
        if self.stream is None or not self.stream.isOpened():
            messagebox.showinfo("Error", "Error loading source or camera")
            self.button_stop_clicked()
            return

        if self.src is not 0 and self.src is not "0":
            number_of_frames = int(self.stream.get(cv2.CAP_PROP_FRAME_COUNT))
            self.fps = int(self.stream.get(cv2.CAP_PROP_FPS))
            if self.fps != 0:
                video_length = int(number_of_frames / self.fps)
                print("[INFO] Video length: {}s, FPS of video: {}".format(video_length, self.fps))

        self.recognition_loop()

    def recognition_loop(self):
        (grabbed, frame) = self.stream.read()

        if not grabbed or self.stop_event.is_set():
            self.end_loop()
        else:
            marked_frame = process_frame(frame, self.extracted_data, self.attended_students, self.save_faces,
                                         self.save_aligned)

            if self.writer is None and self.save_video is True:
                fourcc = cv2.VideoWriter_fourcc(*"mp4v")
                self.writer = cv2.VideoWriter(self.output_src, fourcc, 30,
                                              (marked_frame.shape[1], marked_frame.shape[0]), True)

            # if the writer is not None, write the frame with recognized faces to disk
            if self.writer is not None and self.save_video is True:
                self.writer.write(marked_frame)

            show_frame_width, show_frame_height = self.whole_app.get_frame_resolution()

            if show_frame_width < marked_frame.shape[1] or show_frame_height < marked_frame.shape[0]:
                marked_frame = imutils.resize(marked_frame, width=show_frame_width, height=show_frame_height)

            displayed_frame = cv2.cvtColor(marked_frame, cv2.COLOR_BGR2RGB)
            displayed_frame = Image.fromarray(displayed_frame)
            displayed_frame = ImageTk.PhotoImage(displayed_frame)

            self.whole_app.display_frame(displayed_frame)
            self.whole_app.video_window.after(10, self.recognition_loop)

    def end_loop(self):
        if self.writer is not None and self.save_video is True:
            self.writer.release()

        message_out = "[INFO] Ending recognition...\n"
        self.whole_app.update_statusbar(message_out)
        print(message_out)

        print("[INFO] Starting attendance checker...")
        AttendanceChecker(self.whole_app, self.attended_students)

        if self.measure_time:
            end_timestamp = time.time()
            running_time = end_timestamp - self.start_timestamp
            message_out = "[INFO] Total execution Time (in seconds) : {:.0f}s".format(running_time)
            self.whole_app.update_statusbar(message_out)
            print(message_out)

        if self.stream is not None:
            self.stream.release()
        self.button_stop_clicked()


def detect_faces_haar(frame, scale_factor=1.2, min_neighbors=4):
    """
    Function will detect faces on image with Viola-Jones algorithm
    :param frame: frame to be processed
    :param scale_factor: specifying how much the image size is reduced at each image scale
    :param min_neighbors: specifying how many neighbors each candidate rectangle should have to retain it
    :return: face locations of detected faces
    """
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    detected_faces_locations = face_cascade.detectMultiScale(gray, scaleFactor=scale_factor, minNeighbors=min_neighbors)

    return detected_faces_locations


def get_face_landmarks(face_image):
    """
    Function will compute face landmarks on image
    :param face_image: image of face
    :return: list of facial landmarks
    """
    cropped_face_locations = hog_face_detector(face_image, 1)
    list_of_landmarks = []
    for face_location in cropped_face_locations:
        list_of_landmarks.append(pose_predictor_68_point(face_image, face_location))

    return list_of_landmarks


def face_encodings(face_image):
    """
    Function will compute the encoding vector from image
    :param face_image: image, where faces will be encoded
    :return: list of encoded faces. Usually there is only one face on the image.
    """
    landmarks_list = get_face_landmarks(face_image)
    list_of_encodings = []
    for landmarks in landmarks_list:
        list_of_encodings.append(np.array(face_encoder.compute_face_descriptor(face_image, landmarks, 1)))

    return list_of_encodings


def process_frame(frame, extracted_data, attended_students, save_tmp=False, save_aligned=False):
    """
        Function process actual frame, detects faces on it, mark the frame with rectangle face locations, update
        attended students list and if user wanted to save faces, it saves cropped recognized face
        :param save_aligned: boolean, determine if save recognized cropped photo
        :param save_tmp: boolean, determine if save recognized photo
        :param attended_students: list of attended students
        :param extracted_data: data that contain face encodings and their names
        :param frame: actual processed frame
        :return: frame with marked names and rectangles of face locations
    """
    frame_height = int(frame.shape[0])
    frame_width = frame.shape[1]
    marked_frame = frame.copy()
    faces = detect_faces_haar(frame)

    for (x, y, w, h) in faces:
        # Ensure that rectangle does not exceed frame width and height
        x = max(x - 15, 0)
        y = max(y - 15, 0)
        w = min(w + 30, frame_width)
        h = min(h + 30, frame_height)

        start_x = x
        start_y = y
        end_x = start_x + w
        end_y = start_y + h
        subface = frame[y:y + h, x:x + w]

        name, percentage = recognize_face(subface, extracted_data)

        if name == "":
            cv2.rectangle(marked_frame, (start_x, start_y), (end_x, end_y),
                          (0, 0, 0), 1)
            continue
        elif name == "Unknown":
            cv2.rectangle(marked_frame, (start_x, start_y), (end_x, end_y),
                          (88, 232, 201), 2)
            cv2.putText(marked_frame, "{}".format(name), (start_x, start_y), cv2.FONT_HERSHEY_SIMPLEX, 0.75,
                        (88, 232, 201), 2)

        else:
            cv2.rectangle(marked_frame, (start_x, start_y), (end_x, end_y),
                          (0, 255, 0), 2)
            name_with_id = name.split("_")
            surname = name_with_id[0]
            firstname = name_with_id[1]
            person_id = name_with_id[-1]

            cv2.putText(marked_frame, "{} {} (id:{})".format(surname, firstname, person_id),
                        (start_x, start_y), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 255, 0), 2)

            frame_marked_student = frame.copy()
            cv2.rectangle(frame_marked_student, (start_x, start_y), (end_x, end_y),
                          (0, 255, 0), 2)
            cv2.putText(frame_marked_student, "{} {}".format(firstname, surname),
                        (start_x, start_y), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 255, 0), 2)

            if attended_students.get(name, None) is None:
                attended_students[name] = PersonInfo(name, percentage, subface, frame_marked_student, 0)
            else:
                student_info = attended_students.get(name, None)
                current_reliability = student_info.confidentiality
                if current_reliability < percentage:
                    student_info.confidentiality = percentage
                    student_info.image = subface
                    student_info.marked_frame = frame_marked_student

                student_info.detect_count += 1

        if save_tmp:
            if save_aligned:
                subface = aligner(frame, (dlib.rectangle(int(start_x), int(start_y), int(end_x), int(end_y))))
            dt = datetime.datetime.now()
            unique_file_number = str(dt.strftime('%Y-%m-%d-%H%M%S')) + str(dt.microsecond)
            img_path = "saved_images/saved_image_" + unique_file_number + ".jpg"
            cv2.imwrite(img_path, subface)

    return marked_frame


def recognize_face(cropped_face, data):
    """"
    Function transform given face image to encoding and compare them to others from pre-trained face encodings
    :param cropped_face: face image
    :param data: deserialized pickle encodings of known faces and their names
    :return: name of recognized person, percentage of similarity
    """
    encoded_face = face_encodings(cropped_face)
    name = ""
    percentage = 0
    for encoding in encoded_face:
        min_index, percentage = compare_faces_get_min(data["encodings"], encoding, tolerance=0.47)
        if min_index == -1:
            name = "Unknown"
        else:
            name = data["names"][min_index]

    return name, percentage


def compare_faces_get_min(known_face_encodings, face_encoding_to_check, tolerance=0.47):
    """
    Minimum distance is the closest face to the given face encoding. Returning percentage of how similar face it is
    :param known_face_encodings: encoding list of known faces
    :param face_encoding_to_check: encoding of the face to be compared with other faces
    :param tolerance: distance tolerance, lower is more strict
    :return: index of face with closest distance and percentage as (1-distance)
    """

    compared_faces = list()
    face_distances = compute_face_distances(known_face_encodings, face_encoding_to_check)
    for distance in face_distances:
        compared_faces.append(distance)

    minimal_distance = min(face_distances)
    min_index = compared_faces.index(minimal_distance)
    percentage = 1 - minimal_distance

    if min(face_distances) > tolerance:
        min_index = -1

    return min_index, percentage


def compute_face_distances(face_encodings_list, face_to_compare):
    """
      Given a list of face encodings, compare them to a known face encoding and get a euclidean distance
    for each comparison face. The distance tells how similar the faces are.

    :param face_encodings_list: List of face encodings to compare
    :param face_to_compare: A face encoding to compare against
    :return: A numpy ndarray with the distance for each face in the same order as the 'faces' array
    """
    if len(face_encodings_list) == 0:
        return np.empty(0)
    return np.linalg.norm(face_encodings_list - face_to_compare, axis=1)


def aligner(img, rect, desired_left_eye=(0.35, 0.35), desired_face_width=256, desired_face_height=256):
    gray = img
    shape_raw = pose_predictor_68_point(gray, rect)

    # initialize the list of (x, y)-coordinates
    shape = np.zeros((68, 2), dtype="int")

    # loop over the 68 facial landmarks and convert them to a 2-tuple of (x, y)-coordinates
    for i in range(0, 68):
        shape[i] = (shape_raw.part(i).x, shape_raw.part(i).y)

    # extract the left and right eye (x, y)-coordinates
    (left_eye_start, left_eye_end) = FACIAL_LANDMARKS_IDXS["left_eye"]
    (right_eye_start, right_eye_end) = FACIAL_LANDMARKS_IDXS["right_eye"]
    left_eye_points = shape[left_eye_start:left_eye_end]
    right_eye_points = shape[right_eye_start:right_eye_end]

    left_eye_center = left_eye_points.mean(axis=0).astype("int")
    right_eye_center = right_eye_points.mean(axis=0).astype("int")

    # compute the angle between the eye centroids
    eye_y = right_eye_center[1] - left_eye_center[1]
    eye_x = right_eye_center[0] - left_eye_center[0]
    angle = np.degrees(np.arctan2(eye_y, eye_x)) - 180

    desired_right_eye_x = 1.0 - desired_left_eye[0]

    # determine the scale of the new resulting image by taking the ratio of the distance between eyes in the current
    # image to the ratio of distance between eyes in the new image
    current_distance = np.sqrt((eye_x ** 2) + (eye_y ** 2))
    desired_distance = (desired_right_eye_x - desired_left_eye[0])
    desired_distance *= desired_face_width
    scale = desired_distance / current_distance

    center_eyes = ((left_eye_center[0] + right_eye_center[0]) // 2,
                   (left_eye_center[1] + right_eye_center[1]) // 2)

    # get the rotation matrix for rotating and scaling the face
    rotation_matrix = cv2.getRotationMatrix2D(center_eyes, angle, scale)

    # update the translation component of the matrix
    translation_x = desired_face_width * 0.5
    translation_y = desired_face_height * desired_left_eye[1]
    rotation_matrix[0, 2] += (translation_x - center_eyes[0])
    rotation_matrix[1, 2] += (translation_y - center_eyes[1])

    # apply the affine transformation
    (w, h) = (desired_face_width, desired_face_height)
    aligned_face = cv2.warpAffine(img, rotation_matrix, (w, h),
                                  flags=cv2.INTER_CUBIC)

    # return the aligned face
    return aligned_face


def create_missing_directories():
    absolute_path = os.path.dirname(os.path.abspath(__file__))

    required_directories = list()
    required_directories.append(os.path.join(absolute_path, 'dataset'))
    required_directories.append(os.path.join(absolute_path, 'dataset_unsorted'))
    required_directories.append(os.path.join(absolute_path, 'output_attendance_csv'))
    required_directories.append(os.path.join(absolute_path, 'res', 'cascades'))
    required_directories.append(os.path.join(absolute_path, 'res', 'cascades', 'haarcascades'))
    required_directories.append(os.path.join(absolute_path, 'res', 'encodings'))
    required_directories.append(os.path.join(absolute_path, 'res', 'models'))
    required_directories.append(os.path.join(absolute_path, 'saved_images'))
    required_directories.append(os.path.join(absolute_path, 'saved_videos'))

    for dir_path in required_directories:
        if not os.path.exists(dir_path):
            print("[INFO] Directory {} not found. Creating new...".format(dir_path.split("/")[-1]))
            os.makedirs(dir_path)


def check_required_files():
    files_ok = True
    missing_files_counter = 0
    absolute_path = os.path.dirname(os.path.abspath(__file__))

    required_files = list()
    required_files.append(os.path.join(absolute_path, 'res', 'models', 'shape_predictor_68_face_landmarks.dat'))
    required_files.append(
        os.path.join(absolute_path, 'res', 'models', 'dlib_face_recognition_resnet_model_v1.dat'))
    required_files.append(
        os.path.join(absolute_path, 'res', 'cascades', 'haarcascades', 'haarcascade_frontalface_default.xml'))

    for file_path in required_files:
        if not os.path.isfile(file_path):
            print("[ERROR] Required file {} not found!".format(file_path.split("/")[-1]))
            files_ok = False
            missing_files_counter += 1

    if not files_ok:
        print("\n*** Running failed, {} error(s) found! See [ERROR] messages ***".format(missing_files_counter))

    return files_ok


FACIAL_LANDMARKS_IDXS = dict([
    ("mouth", (48, 68)),
    ("inner_mouth", (60, 68)),
    ("right_eyebrow", (17, 22)),
    ("left_eyebrow", (22, 27)),
    ("right_eye", (36, 42)),
    ("left_eye", (42, 48)),
    ("nose", (27, 36)),
    ("jaw", (0, 17))
])

predictor_68_point_model = None
pose_predictor_68_point = None
hog_face_detector = None
face_recognition_model = None
face_encoder = None
cascade_src = None
face_cascade = None

if __name__ == "__main__":
    gui_root = tk.Tk()
    gui_root.title("Face recognition")
    gui_root.minsize(1000, 800)
    gui_root.state('zoomed')

    print("[INFO] Face recognizer started\n")
    create_missing_directories()
    print("[INFO] Loading Graphical interface...")

    if check_required_files():
        absolute_project_path = os.path.dirname(os.path.abspath(__file__))
        predictor_68_point_model = os.path.join(absolute_project_path, 'res', 'models',
                                                'shape_predictor_68_face_landmarks.dat')
        pose_predictor_68_point = dlib.shape_predictor(predictor_68_point_model)
        hog_face_detector = dlib.get_frontal_face_detector()
        face_recognition_model = os.path.join(absolute_project_path, 'res', 'models',
                                              'dlib_face_recognition_resnet_model_v1.dat')
        face_encoder = dlib.face_recognition_model_v1(face_recognition_model)
        cascade_src = os.path.join(absolute_project_path, 'res', 'cascades', 'haarcascades',
                                   'haarcascade_frontalface_default.xml')
        face_cascade = cv2.CascadeClassifier(cascade_src)

        MainApplication(gui_root)
        gui_root.mainloop()
    else:
        exit(1)
