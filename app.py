import tkinter as tk
from tkinter import filedialog, Listbox, Scrollbar
from PIL import Image, ImageTk, ImageDraw
import os
import random

class SkeletonDrawer:
    def __init__(self, root):
        self.root = root
        self.root.title("Skeleton Drawer")

        self.image = None
        self.photo = None
        self.canvas = tk.Canvas(root, width=480, height=480, bg="black")
        self.canvas.pack(side=tk.RIGHT)

        self.keypoints = []
        self.connections = []
        self.dragging = None
        self.previous_positions = []
        self.manual_mode = False
        self.delete_mode = False
        
        self.line_thickness = 2
        self.keypoint_size = 5
        self.colors = []

        self.create_buttons()
        self.canvas.bind("<ButtonPress-1>", self.on_press)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)

        self.create_image_list()
        self.create_specific_skeleton()

        self.temp_line = None
        self.start_keypoint = None

    def create_buttons(self):
        button_frame = tk.Frame(self.root)
        button_frame.pack(side=tk.LEFT, fill=tk.Y)

        reset_button = tk.Button(button_frame, text="Reset Skeleton", command=self.reset_skeleton)
        reset_button.pack(fill=tk.X)

        add_skeleton_button = tk.Button(button_frame, text="Add Skeleton", command=self.add_skeleton)
        add_skeleton_button.pack(fill=tk.X)

        add_fingers_button = tk.Button(button_frame, text="Add Fingers", command=self.add_fingers)
        add_fingers_button.pack(fill=tk.X)

        save_button = tk.Button(button_frame, text="Save", command=self.save_image)
        save_button.pack(fill=tk.X)

        undo_button = tk.Button(button_frame, text="Undo", command=self.undo)
        undo_button.pack(fill=tk.X)

        exit_button = tk.Button(button_frame, text="Exit", command=self.root.quit)
        exit_button.pack(fill=tk.X)

        line_thickness_label = tk.Label(button_frame, text="Line Thickness")
        line_thickness_label.pack(fill=tk.X)
        self.line_thickness_slider = tk.Scale(button_frame, from_=1, to=10, orient=tk.HORIZONTAL, command=self.update_line_thickness)
        self.line_thickness_slider.set(self.line_thickness)
        self.line_thickness_slider.pack(fill=tk.X)

        keypoint_size_label = tk.Label(button_frame, text="Keypoint Size")
        keypoint_size_label.pack(fill=tk.X)
        self.keypoint_size_slider = tk.Scale(button_frame, from_=1, to=10, orient=tk.HORIZONTAL, command=self.update_keypoint_size)
        self.keypoint_size_slider.set(self.keypoint_size)
        self.keypoint_size_slider.pack(fill=tk.X)

        self.manual_mode_indicator = tk.Label(button_frame, text="Manual Mode", bg="red", width=15)
        self.manual_mode_indicator.pack(fill=tk.X)
        self.manual_mode_button = tk.Button(button_frame, text="Toggle Manual Mode", command=self.toggle_manual_mode)
        self.manual_mode_button.pack(fill=tk.X)

        self.delete_mode_indicator = tk.Label(button_frame, text="Delete Mode", bg="red", width=15)
        self.delete_mode_indicator.pack(fill=tk.X)
        self.delete_mode_button = tk.Button(button_frame, text="Toggle Delete Mode", command=self.toggle_delete_mode)
        self.delete_mode_button.pack(fill=tk.X)

    def create_image_list(self):
        self.image_listbox = Listbox(self.root, width=20, height=20)
        self.image_listbox.pack(side=tk.RIGHT, fill=tk.Y)

        scrollbar = Scrollbar(self.root, orient="vertical")
        scrollbar.config(command=self.image_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.image_listbox.config(yscrollcommand=scrollbar.set)

        self.image_listbox.bind("<<ListboxSelect>>", self.load_selected_image)

        self.populate_image_list()

    def populate_image_list(self):
        sample_folder = "sample"
        if not os.path.exists(sample_folder):
            os.makedirs(sample_folder)

        for filename in os.listdir(sample_folder):
            if filename.endswith(".png") or filename.endswith(".jpg"):
                self.image_listbox.insert(tk.END, filename)

    def load_selected_image(self, event):
        selected_indices = self.image_listbox.curselection()
        if selected_indices:
            selected_filename = self.image_listbox.get(selected_indices[0])
            file_path = os.path.join("sample", selected_filename)
            self.open_image(file_path)

    def open_image(self, file_path):
        if file_path:
            self.image = Image.open(file_path)
            self.image = self.image.resize((480, 480), Image.Resampling.LANCZOS)
            self.photo = ImageTk.PhotoImage(self.image)
            self.canvas.delete("all")
            self.canvas.create_image(0, 0, anchor=tk.NW, image=self.photo)
            self.draw_skeleton()

    def create_specific_skeleton(self):
        self.keypoints = [
            (240, 50),   # 0: Nose
            (240, 100),  # 1: Neck
            (200, 100),  # 2: Right Shoulder
            (160, 180),  # 3: Right Elbow
            (120, 260),  # 4: Right Wrist
            (280, 100),  # 5: Left Shoulder
            (320, 180),  # 6: Left Elbow
            (360, 260),  # 7: Left Wrist
            (220, 220),  # 8: Right Hip
            (200, 340),  # 9: Right Knee
            (180, 460),  # 10: Right Ankle
            (260, 220),  # 11: Left Hip
            (280, 340),  # 12: Left Knee
            (300, 460),  # 13: Left Ankle
            (220, 30),   # 14: Right Eye
            (260, 30),   # 15: Left Eye
            (200, 40),   # 16: Right Ear
            (280, 40)    # 17: Left Ear
        ]

        self.connections = [
            (0, 1),   # Nose to Neck
            (1, 2),   # Neck to Right Shoulder
            (2, 3),   # Right Shoulder to Right Elbow
            (3, 4),   # Right Elbow to Right Wrist
            (1, 5),   # Neck to Left Shoulder
            (5, 6),   # Left Shoulder to Left Elbow
            (6, 7),   # Left Elbow to Left Wrist
            (1, 8),   # Neck to Right Hip
            (8, 9),   # Right Hip to Right Knee
            (9, 10),  # Right Knee to Right Ankle
            (1, 11),  # Neck to Left Hip
            (11, 12), # Left Hip to Left Knee
            (12, 13), # Left Knee to Left Ankle
            (0, 14),  # Nose to Right Eye
            (0, 15),  # Nose to Left Eye
            (14, 16), # Right Eye to Right Ear
            (15, 17)  # Left Eye to Left Ear
        ]

        self.randomize_colors()
        self.draw_skeleton()

    def add_fingers(self):
        # Add keypoints for fingers
        finger_keypoints = [
            (110, 270), (100, 280), (90, 290),   # Right thumb
            (130, 280), (140, 300), (150, 320),  # Right index finger
            (140, 280), (150, 300), (160, 320),  # Right middle finger
            (150, 280), (160, 300), (170, 320),  # Right ring finger
            (160, 280), (170, 300), (180, 320),  # Right pinky
            (370, 270), (380, 280), (390, 290),  # Left thumb
            (350, 280), (340, 300), (330, 320),  # Left index finger
            (340, 280), (330, 300), (320, 320),  # Left middle finger
            (330, 280), (320, 300), (310, 320),  # Left ring finger
            (320, 280), (310, 300), (300, 320)   # Left pinky
        ]

        # Update keypoints and connections
        start_index = len(self.keypoints)
        self.keypoints.extend(finger_keypoints)

        # Define finger connections
        finger_connections = [
            (4, start_index + 0), (start_index + 0, start_index + 1), (start_index + 1, start_index + 2),  # Right thumb
            (4, start_index + 3), (start_index + 3, start_index + 4), (start_index + 4, start_index + 5),  # Right index
            (4, start_index + 6), (start_index + 6, start_index + 7), (start_index + 7, start_index + 8),  # Right middle
            (4, start_index + 9), (start_index + 9, start_index + 10), (start_index + 10, start_index + 11),  # Right ring
            (4, start_index + 12), (start_index + 12, start_index + 13), (start_index + 13, start_index + 14),  # Right pinky
            (7, start_index + 15), (start_index + 15, start_index + 16), (start_index + 16, start_index + 17),  # Left thumb
            (7, start_index + 18), (start_index + 18, start_index + 19), (start_index + 19, start_index + 20),  # Left index
            (7, start_index + 21), (start_index + 21, start_index + 22), (start_index + 22, start_index + 23),  # Left middle
            (7, start_index + 24), (start_index + 24, start_index + 25), (start_index + 25, start_index + 26),  # Left ring
            (7, start_index + 27), (start_index + 27, start_index + 28), (start_index + 28, start_index + 29)   # Left pinky
        ]

        self.connections.extend(finger_connections)

        self.randomize_colors()
        self.draw_skeleton()

    def add_skeleton(self):
        # Create a new skeleton
        self.create_specific_skeleton()

    def randomize_colors(self):
        self.colors = [self.random_color() for _ in self.connections]

    def random_color(self):
        return "#%06x" % random.randint(0, 0xFFFFFF)

    def draw_skeleton(self):
        if self.image:
            self.canvas.delete("skeleton")

            for i, keypoint in enumerate(self.keypoints):
                x, y = keypoint
                self.canvas.create_oval(x - self.keypoint_size, y - self.keypoint_size, 
                                        x + self.keypoint_size, y + self.keypoint_size, 
                                        fill="white", outline="white", tags="skeleton")
                self.canvas.create_text(x, y - self.keypoint_size - 5, text=str(i), fill="white", tags="skeleton")

            for i, connection in enumerate(self.connections):
                start_idx, end_idx = connection
                start = self.keypoints[start_idx]
                end = self.keypoints[end_idx]
                color = self.colors[i] if i < len(self.colors) else self.random_color()
                self.canvas.create_line(start, end, fill=color, width=self.line_thickness, tags="skeleton")

    def on_press(self, event):
        if self.delete_mode:
            self.delete_keypoint(event.x, event.y)
        elif self.manual_mode:
            self.start_manual_line(event.x, event.y)
        else:
            self.dragging = self.find_closest_keypoint(event.x, event.y)
            if self.dragging is not None:
                self.previous_positions.append((self.dragging, self.keypoints[self.dragging]))

    def on_drag(self, event):
        if self.manual_mode and self.temp_line:
            self.update_temp_line(event.x, event.y)
        elif self.dragging is not None:
            x, y = event.x, event.y
            self.keypoints[self.dragging] = (x, y)
            self.draw_skeleton()

    def on_release(self, event):
        if self.manual_mode and self.temp_line:
            self.finish_manual_line(event.x, event.y)
        self.dragging = None
        self.start_keypoint = None
        self.temp_line = None

    def start_manual_line(self, x, y):
        self.start_keypoint = self.find_closest_keypoint(x, y)
        if self.start_keypoint is None:
            self.start_keypoint = len(self.keypoints)
            self.keypoints.append((x, y))
        start_x, start_y = self.keypoints[self.start_keypoint]
        self.temp_line = self.canvas.create_line(start_x, start_y, x, y, fill="white", width=self.line_thickness, tags="temp_line")

    def update_temp_line(self, x, y):
        if self.temp_line:
            start_x, start_y = self.keypoints[self.start_keypoint]
            self.canvas.coords(self.temp_line, start_x, start_y, x, y)

    def finish_manual_line(self, x, y):
        end_keypoint = self.find_closest_keypoint(x, y)
        if end_keypoint is None:
            end_keypoint = len(self.keypoints)
            self.keypoints.append((x, y))
        
        if self.start_keypoint != end_keypoint:
            self.connections.append((self.start_keypoint, end_keypoint))
            self.colors.append(self.random_color())
        
        self.canvas.delete("temp_line")
        self.draw_skeleton()

    def find_closest_keypoint(self, x, y):
        closest_idx = None
        min_dist = float('inf')
        for i, (kx, ky) in enumerate(self.keypoints):
            dist = ((kx - x) ** 2 + (ky - y) ** 2) ** 0.5
            if dist < self.keypoint_size * 2 and dist < min_dist:
                min_dist = dist
                closest_idx = i
        return closest_idx

    def delete_keypoint(self, x, y):
        closest_idx = self.find_closest_keypoint(x, y)
        if closest_idx is not None:
            # Remove keypoint and associated connections
            self.keypoints.pop(closest_idx)
            self.connections = [(start, end) for start, end in self.connections if start != closest_idx and end != closest_idx]
            self.connections = [(start - 1 if start > closest_idx else start,
                                end - 1 if end > closest_idx else end) for start, end in self.connections]
            self.draw_skeleton()

    def toggle_manual_mode(self):
        self.manual_mode = not self.manual_mode
        self.manual_mode_indicator.config(bg="green" if self.manual_mode else "red")

    def toggle_delete_mode(self):
        self.delete_mode = not self.delete_mode
        self.delete_mode_indicator.config(bg="green" if self.delete_mode else "red")

    def reset_skeleton(self):
        self.keypoints = []
        self.connections = []
        self.colors = []
        self.draw_skeleton()

    def undo(self):
        if self.previous_positions:
            idx, prev_pos = self.previous_positions.pop()
            self.keypoints[idx] = prev_pos
            self.draw_skeleton()

    def update_line_thickness(self, value):
        self.line_thickness = int(value)
        self.draw_skeleton()

    def update_keypoint_size(self, value):
        self.keypoint_size = int(value)
        self.draw_skeleton()

    def save_image(self):
        if self.image:
            output_image = Image.new("RGB", (480, 480), (0, 0, 0))
            draw = ImageDraw.Draw(output_image)
            
            # Draw connections
            for i, connection in enumerate(self.connections):
                start_idx, end_idx = connection
                start = self.keypoints[start_idx]
                end = self.keypoints[end_idx]
                color = self.colors[i] if i < len(self.colors) else self.random_color()
                draw.line([start, end], fill=color, width=self.line_thickness)
            
            # Draw keypoints without numbers
            for keypoint in self.keypoints:
                x, y = keypoint
                draw.ellipse([x - self.keypoint_size, y - self.keypoint_size, 
                              x + self.keypoint_size, y + self.keypoint_size], 
                             fill="white")

            # Create 'result' folder if it doesn't exist
            if not os.path.exists("result"):
                os.makedirs("result")

            # Generate a unique filename
            i = 0
            while True:
                file_path = os.path.join("result", f"skeleton_{i}.png")
                if not os.path.exists(file_path):
                    break
                i += 1

            output_image.save(file_path)
            print(f"Image saved as {file_path}")

if __name__ == "__main__":
    root = tk.Tk()
    app = SkeletonDrawer(root)
    root.mainloop()