import os
import shutil
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote_plus
from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import tkinter as tk
from tkinter import messagebox
from tkinterdnd2 import DND_FILES, TkinterDnD
import zipfile


class ModDownloader:
    def __init__(self, root):
        self.root = root
        self.MANIFEST_DIR = r"C:\Program Files (x86)\Steam\config\depotcache"
        self.LUA_ST_DIR = r"C:\Program Files (x86)\Steam\config\stplug-in"
        self.driver_path = os.path.join(os.path.expanduser("~"), "Downloads", "geckodriver.exe")
        self.options = webdriver.FirefoxOptions()
        self.options.binary_location = r"C:\Program Files\Mozilla Firefox\firefox.exe"
        self.options.add_argument("--headless")
        self.service = Service(self.driver_path)
        self.window_stack = []
        self.current_mode = None
        self.app_id = "383980"  # default app ID

        self.main_menu()

    def main_menu(self):
        self.clear_window()
        self.window_stack = []
        self.current_mode = "main_menu"
        tk.Label(self.root, text="Main Menu", font=("Arial", 24), bg="#2E2E2E", fg="white").pack(pady=20)
        tk.Button(self.root, text="Mod Downloader", command=self.mod_downloader).pack(pady=10)
        tk.Button(self.root, text="Lua & Manifest Mode", command=self.workshop_file_mover).pack(pady=10)
        tk.Button(self.root, text="Credits", command=self.credits_screen).pack(pady=10)

    def add_return_arrow(self):
        arrow_btn = tk.Button(self.root, text="←", command=self.return_to_previous,
                              font=("Arial", 14), bg="#2E2E2E", fg="white", bd=0)
        arrow_btn.place(x=10, y=10)

    def mod_downloader(self):
        self.clear_window()
        self.window_stack.append(self.mod_downloader)
        self.current_mode = "mod_downloader"

        self.add_return_arrow()

        self.search_label = tk.Label(self.root, text="Search for Mods:", bg="#2E2E2E", fg="white")
        self.search_label.pack(pady=10)
        self.search_entry = tk.Entry(self.root, width=50)
        self.search_entry.pack(pady=5)

        self.app_id_label = tk.Label(self.root, text="App ID:", bg="#2E2E2E", fg="white")
        self.app_id_label.pack(pady=5)
        self.app_id_entry = tk.Entry(self.root, width=10)
        self.app_id_entry.insert(0, self.app_id)
        self.app_id_entry.pack(pady=5)

        self.search_button = tk.Button(self.root, text="Search", command=self.on_search, bg="#4CAF50", fg="white")
        self.search_button.pack(pady=10)

        self.link_list = tk.Listbox(self.root, width=80, height=10)
        self.link_list.pack(pady=10)

        self.install_button = tk.Button(self.root, text="Install Selected Mod",
                                        command=self.on_install, bg="#2196F3", fg="white")
        self.install_button.pack(pady=10)

    def workshop_file_mover(self):
        self.clear_window()
        self.window_stack.append(self.workshop_file_mover)
        self.current_mode = "workshop_file_mover"

        self.add_return_arrow()

        tk.Label(self.root, text="Workshop File Mover", font=("Arial", 24),
                 bg="#2E2E2E", fg="white").pack(pady=20)
        tk.Label(self.root, text="Drag and drop files here:", bg="#2E2E2E", fg="white").pack(pady=10)
        self.drop_frame = tk.Frame(self.root, bg="#2E2E2E")
        self.drop_frame.pack(pady=10)
        self.root.drop_target_register(DND_FILES)
        self.root.dnd_bind("<<Drop>>", self.drop)

    def credits_screen(self):
        self.clear_window()
        self.window_stack.append(self.credits_screen)
        self.current_mode = "credits"

        self.add_return_arrow()

        credits_frame = tk.Frame(self.root, bg="#2E2E2E")
        credits_frame.pack(expand=True, fill="both")

        self.credits_label = tk.Label(
            credits_frame,
            text="Meng (This took a LONG time)",
            font=("Arial", 20, "bold"),
            bg="#2E2E2E"
        )
        self.credits_label.place(relx=0.5, rely=0.5, anchor="center")

        # rainbow fade setup
        self.current_rgb = (255, 0, 0)
        self.target_rgb = (255, 127, 0)
        self.color_index = 1
        self.fade_step = 0
        self.animate_rainbow_fade()

    def rgb_to_hex(self, rgb):
        return "#%02x%02x%02x" % rgb

    def animate_rainbow_fade(self):
        if self.current_mode == "credits":
            r1, g1, b1 = self.current_rgb
            r2, g2, b2 = self.target_rgb
            step_fraction = self.fade_step / 15  # faster fade (was 30)
            r = int(r1 + (r2 - r1) * step_fraction)
            g = int(g1 + (g2 - g1) * step_fraction)
            b = int(b1 + (b2 - b1) * step_fraction)

            self.credits_label.config(fg=self.rgb_to_hex((r, g, b)))

            if self.fade_step < 15:  # faster cycle (was 30)
                self.fade_step += 1
            else:
                self.fade_step = 0
                self.current_rgb = self.target_rgb
                rainbow_colors = [
                    (255, 0, 0), (255, 127, 0), (255, 255, 0),
                    (0, 255, 0), (0, 0, 255), (75, 0, 130), (148, 0, 211)
                ]
                self.color_index = (self.color_index + 1) % len(rainbow_colors)
                self.target_rgb = rainbow_colors[self.color_index]

            self.root.after(50, self.animate_rainbow_fade)

    def drop(self, event):
        if self.current_mode == "workshop_file_mover":
            for file in event.data.split():
                target_dir = None
                if file.endswith('.manifest'):
                    target_dir = self.MANIFEST_DIR
                elif file.endswith(('.lua', '.st')):
                    target_dir = self.LUA_ST_DIR

                if target_dir:
                    try:
                        shutil.move(file, target_dir)
                        print(f"Moved: {file} to {target_dir}")
                    except Exception as e:
                        print(f"Error moving file {file}: {e}")

    def return_to_previous(self):
        if self.window_stack:
            self.window_stack.pop()
            if self.window_stack:
                self.window_stack[-1]()
            else:
                self.main_menu()

    def clear_window(self):
        for widget in self.root.winfo_children():
            widget.destroy()

    def search_smods(self, query):
        self.app_id = self.app_id_entry.get()
        base_url = "https://catalogue.smods.ru/?s="
        app_id = f"&app={self.app_id}"
        search_url = f"{base_url}{quote_plus(query)}{app_id}"
        response = requests.get(search_url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            return [link['href'] for link in soup.find_all('a', class_='skymods-excerpt-btn')
                    if "modsbase.com" in link['href']]
        return []

    def extract_download_link(self, download_url):
        driver = None
        try:
            driver = webdriver.Firefox(service=self.service, options=self.options)
            driver.get(download_url)
            WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.ID, 'downloadbtn')))
            download_button = driver.find_element(By.ID, 'downloadbtn')
            driver.execute_script("arguments[0].scrollIntoView(true);", download_button)
            WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.ID, 'downloadbtn')))
            download_button.click()
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'a[href*="cgi-bin/dl.cgi"]')))
            download_link = driver.find_element(By.CSS_SELECTOR, 'a[href*="cgi-bin/dl.cgi"]').get_attribute('href')
            return download_link
        except Exception as e:
            print(f"Error extracting download link: {e}")
        finally:
            if driver:
                driver.quit()
        return None

    def on_search(self):
        query = self.search_entry.get()
        links = self.search_smods(query)
        self.link_list.delete(0, tk.END)
        for link in links:
            self.link_list.insert(tk.END, link)

    def on_install(self):
        selected_index = self.link_list.curselection()
        if selected_index:
            download_url = self.link_list.get(selected_index)
            download_link = self.extract_download_link(download_url)
            if download_link:
                if not os.path.exists("workshop_mod"):
                    os.makedirs("workshop_mod")
                zip_path = os.path.join("workshop_mod", "mod.zip")
                with open(zip_path, 'wb') as file:
                    file.write(requests.get(download_link).content)
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall("workshop_mod")
                os.remove(zip_path)
                messagebox.showinfo("Success", "Mod installed successfully!")
            else:
                messagebox.showerror("Error", "Failed to install mod.")


root = TkinterDnD.Tk()
root.title("Mod Downloader and File Checker")
root.geometry("600x400")
root.configure(bg="#2E2E2E")

app = ModDownloader(root)
root.mainloop()

