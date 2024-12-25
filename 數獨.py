import os
import random
import numpy as np
from PIL import Image, ImageTk
import tkinter as tk
from tkinter import simpledialog, messagebox
import time

# 照片資料夾
PHOTO_FOLDER = "photos"

def process_photo(photo_path):
    """
    將照片切割為9x9格子,並提取每個小方塊。
    :param photo_path: 照片的檔案路徑
    :return: 9x9的小方塊圖像和原始照片對象
    """
    image = Image.open(photo_path).convert("RGB")
    width, height = image.size

    # 計算每個小方塊的寬度與高度
    cell_width = width / 9
    cell_height = height / 9

    grid = []
    for row in range(9):
        grid_row = []
        for col in range(9):
            left = int(col * cell_width)
            upper = int(row * cell_height)
            right = int((col + 1) * cell_width)
            lower = int((row + 1) * cell_height)
            cell = image.crop((left, upper, right, lower))
            grid_row.append(cell)
        grid.append(grid_row)
    return grid, image

def generate_sudoku(difficulty="medium"):
    """
    生成符合數獨規則的初始盤面。
    :param difficulty: 數獨難度 ("easy", "medium", "hard")
    :return: 數獨初始盤面和答案
    """
    sudoku = np.zeros((9, 9), dtype=int)

    def fill_diagonal_blocks():
        for i in range(0, 9, 3):
            numbers = np.random.permutation(range(1, 10))
            sudoku[i:i+3, i:i+3] = numbers.reshape((3, 3))

    def can_place(row, col, num):
        if num in sudoku[row, :]:
            return False
        if num in sudoku[:, col]:
            return False
        box_row, box_col = 3 * (row // 3), 3 * (col // 3)
        if num in sudoku[box_row:box_row+3, box_col:box_col+3]:
            return False
        return True

    def fill_remaining_cells(row, col):
        if col >= 9:
            row += 1
            col = 0
        if row >= 9:
            return True
        if sudoku[row, col] != 0:
            return fill_remaining_cells(row, col + 1)
        for num in np.random.permutation(range(1, 10)):
            if can_place(row, col, num):
                sudoku[row, col] = num
                if fill_remaining_cells(row, col + 1):
                    return True
                sudoku[row, col] = 0
        return False

    fill_diagonal_blocks()
    fill_remaining_cells(0, 0)

    solution = sudoku.copy()

    difficulty_levels = {"easy": 30, "medium": 40, "hard": 50}
    num_holes = difficulty_levels.get(difficulty, 40)

    for _ in range(num_holes):
        row, col = random.randint(0, 8), random.randint(0, 8)
        while sudoku[row, col] == 0:
            row, col = random.randint(0, 8), random.randint(0, 8)
        sudoku[row, col] = 0

    return sudoku, solution

class SudokuGame:
    def __init__(self, root, sudoku, solution, grid, original_image):
        self.root = root
        self.sudoku = sudoku
        self.solution = solution
        self.grid = grid
        self.original_image = original_image
        self.cells = {}
        self.errors = 0
        self.start_time = time.time()

        self.photo_width, self.photo_height = self.original_image.size

        # 計算縮放比例，使照片縮放後佔螢幕的約 1/1.5
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        scale_factor = min(screen_width / 1.5 / self.photo_width, screen_height / 1.5 / self.photo_height)
        self.photo_width = int(self.photo_width * scale_factor)
        self.photo_height = int(self.photo_height * scale_factor)

        self.cell_width = self.photo_width / 9
        self.cell_height = self.photo_height / 9

        self.create_game_board()
        self.show_sudoku()

    def create_game_board(self):
        self.canvas = tk.Canvas(self.root, width=self.photo_width, height=self.photo_height + 50, bg="white")
        self.canvas.pack()

        # 添加標題
        self.canvas.create_text(self.photo_width / 2, 20, text="數.讀回憶", font=("KaiTi", 18), fill="blue")

        # 顯示時間與錯誤次數
        self.time_label = tk.Label(self.root, text="用時: 0 分 0 秒", font=("KaiTi", 12))
        self.time_label.pack()
        self.error_label = tk.Label(self.root, text="錯誤次數: 0", font=("KaiTi", 12))
        self.error_label.pack()

        # 繪製網格
        for i in range(10):
            line_width = 3 if i % 3 == 0 else 1
            self.canvas.create_line(self.cell_width * i, 50, self.cell_width * i, self.photo_height + 50, width=line_width)
            self.canvas.create_line(0, 50 + self.cell_height * i, self.photo_width, 50 + self.cell_height * i, width=line_width)

        # 建立每個數字的輸入框
        for row in range(9):
            for col in range(9):
                x1 = col * self.cell_width
                y1 = row * self.cell_height + 50
                entry = tk.Entry(self.root, justify="center", font=("KaiTi", 14))
                entry.place(x=x1 + 2, y=y1 + 2, width=self.cell_width - 4, height=self.cell_height - 4)
                entry.bind("<FocusOut>", lambda e, r=row, c=col: self.check_input(r, c))
                self.cells[(row, col)] = entry

        # 添加完成按鈕
        self.complete_button = tk.Button(self.root, text="完成", font=("KaiTi", 12), command=self.show_final_animation)
        self.complete_button.pack(pady=10)

        # 更新時間顯示
        self.update_timer()

    def update_timer(self):
        elapsed_time = int(time.time() - self.start_time)
        minutes, seconds = divmod(elapsed_time, 60)
        self.time_label.config(text=f"用時: {minutes} 分 {seconds} 秒")
        self.root.after(1000, self.update_timer)

    def get_cell_color(self, row, col):
        color = np.array(self.grid[row][col].resize((1, 1)).getpixel((0, 0))) / 255
        return self.rgb_to_hex(color)

    def show_sudoku(self):
        for row in range(9):
            for col in range(9):
                if self.sudoku[row, col] != 0:
                    entry = self.cells[(row, col)]
                    entry.insert(0, str(self.sudoku[row, col]))
                    entry.config(state="disabled", disabledforeground="black")

    def check_input(self, row, col):
        entry = self.cells[(row, col)]
        value = entry.get().strip()
        if not value.isdigit() or not (1 <= int(value) <= 9):
            entry.delete(0, tk.END)
            return

        value = int(value)
        if value == self.solution[row, col]:
            entry.config(state="disabled", disabledforeground="green")
            self.check_and_fill_regions(row, col)
            if self.is_game_complete():
                self.complete_button.config(state="normal")
        else:
            self.errors += 1
            self.error_label.config(text=f"錯誤次數: {self.errors}")
            messagebox.showerror("錯誤", "數字不正確，請再試一次！")
            entry.delete(0, tk.END)

    def check_and_fill_regions(self, row, col):
        if all(self.cells[(row, c)].get().isdigit() and int(self.cells[(row, c)].get()) == self.solution[row, c] for c in range(9)):
            for c in range(9):
                self.fill_color(row, c)
        if all(self.cells[(r, col)].get().isdigit() and int(self.cells[(r, col)].get()) == self.solution[r, col] for r in range(9)):
            for r in range(9):
                self.fill_color(r, col)
        box_row, box_col = 3 * (row // 3), 3 * (col // 3)
        if all(self.cells[(r, c)].get().isdigit() and int(self.cells[(r, c)].get()) == self.solution[r, c] for r in range(box_row, box_row + 3) for c in range(box_col, box_col + 3)):
            for r in range(box_row, box_row + 3):
                for c in range(box_col, box_col + 3):
                    self.fill_color(r, c)

    def fill_color(self, row, col):
        color = self.get_cell_color(row, col)
        x1 = col * self.cell_width
        y1 = row * self.cell_height + 50
        x2 = x1 + self.cell_width
        y2 = y1 + self.cell_height
        self.canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="")
        entry = self.cells[(row, col)]
        entry.config(bg=color, disabledbackground=color)

    def rgb_to_hex(self, rgb):
        return "#{:02x}{:02x}{:02x}".format(int(rgb[0] * 255), int(rgb[1] * 255), int(rgb[2] * 255))

    def is_game_complete(self):
        for row in range(9):
            for col in range(9):
                entry = self.cells[(row, col)]
                if entry.get().strip() == "" or int(entry.get()) != self.solution[row, col]:
                    return False
        return True

    def show_final_animation(self):
        # 清除所有數字與格線，僅顯示色塊
        self.canvas.delete("all")
        for row in range(9):
            for col in range(9):
                color = np.array(self.grid[row][col].resize((1, 1)).getpixel((0, 0))) / 255
                x1 = col * self.cell_width
                y1 = row * self.cell_height + 50
                x2 = x1 + self.cell_width
                y2 = y1 + self.cell_height
                self.canvas.create_rectangle(x1, y1, x2, y2, fill=self.rgb_to_hex(color), outline="")
        self.root.update()
        time.sleep(0.2)

        # 動畫轉場顯示原始照片 (新視窗顯示)
        self.root.destroy()
        top = tk.Tk()
        top.title("完成！原始圖片")
        top.geometry(f"{self.photo_width}x{self.photo_height + 100}")
        top_canvas = tk.Canvas(top, width=self.photo_width, height=self.photo_height + 100, bg="black")
        top_canvas.pack()

        # 顯示圖片
        resized_image = self.original_image.resize((self.photo_width, self.photo_height))
        img_tk = ImageTk.PhotoImage(resized_image)
        top_canvas.create_image(0, 50, anchor="nw", image=img_tk)

        # 標題文字
        top_canvas.create_text(self.photo_width / 2, 20, text="恭喜你獲得一片回憶碎片！", font=("KaiTi", 18), fill="white")

        top.mainloop()

if __name__ == "__main__":
    if not os.path.exists(PHOTO_FOLDER):
        os.makedirs(PHOTO_FOLDER)
        print(f"已建立資料夾 '{PHOTO_FOLDER}'，請放入照片後重新執行程式。")
        exit()

    photo_files = [f for f in os.listdir(PHOTO_FOLDER) if f.endswith((".jpg", ".png"))]
    if not photo_files:
        print(f"資料夾 '{PHOTO_FOLDER}' 中沒有找到照片，請放入至少一張照片。")
        exit()

    selected_photo = random.choice(photo_files)
    grid, original_image = process_photo(os.path.join(PHOTO_FOLDER, selected_photo))

    # 提供難度選擇
    root = tk.Tk()
    root.withdraw()
    difficulty = simpledialog.askstring("選擇難度", "請選擇難度: easy, medium, 或 hard", initialvalue="medium")
    if difficulty not in {"easy", "medium", "hard"}:
        difficulty = "medium"
    root.deiconify()

    sudoku, solution = generate_sudoku(difficulty)

    root.title("數獨遊戲")
    SudokuGame(root, sudoku, solution, grid, original_image)
    root.mainloop()
