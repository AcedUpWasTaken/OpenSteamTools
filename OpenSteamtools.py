import os
import shutil
import requests
import zipfile
import datetime
import math
from bs4 import BeautifulSoup
from urllib.parse import quote_plus
from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import ttkbootstrap as tb
from ttkbootstrap.constants import *
import tkinter as tk
from tkinter import messagebox
from tkinterdnd2 import TkinterDnD, DND_FILES


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
        self.window_stack = []  # will hold screen function references
        self.app_id = "383980"  # default app ID

        # Style
        self.style = tb.Style("cyborg")

        # Start main menu
        self.show_screen(self.main_menu)

    # ----------------- Navigation -----------------
    def show_screen(self, screen_func):
        """Push a screen onto the stack and display it."""
        self.window_stack.append(screen_func)
        self.clear_window()
        screen_func()

    def return_to_previous(self):
        """Pop current screen and show previous."""
        if len(self.window_stack) > 1:
            self.window_stack.pop()
            prev = self.window_stack[-1]
            self.clear_window()
            prev()
        else:
            self.clear_window()
            self.show_screen(self.main_menu)

    def add_return_arrow(self):
        tb.Button(self.root, text="← Back", bootstyle="secondary outline",
                  command=self.return_to_previous).place(x=10, y=10)

    def clear_window(self):
        for widget in self.root.winfo_children():
            widget.destroy()

    # ----------------- Logger -----------------
    def _log(self, message):
        os.makedirs("workshop_mod", exist_ok=True)
        log_file = os.path.join("workshop_mod", "log.txt")
        timestamp = datetime.datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"{timestamp} {message}\n")

    def view_log(self):
        self.add_return_arrow()
        tb.Label(self.root, text="Installation Log", font=("Segoe UI", 20, "bold")).pack(pady=20)
        log_file = os.path.join("workshop_mod", "log.txt")
        text_box = tb.ScrolledText(self.root, width=80, height=15)
        text_box.pack(pady=10)
        if os.path.exists(log_file):
            with open(log_file, "r", encoding="utf-8") as f:
                text_box.insert("1.0", f.read())
        else:
            text_box.insert("1.0", "No logs yet.")

    # ----------------- Main Menu -----------------
    def main_menu(self):
        tb.Label(self.root, text="Main Menu", font=("Segoe UI", 24, "bold")).pack(pady=20)

        tb.Button(self.root, text="Mod Downloader",
                  bootstyle="primary outline", width=20,
                  command=lambda: self.show_screen(self.mod_downloader)).pack(pady=10, ipadx=12, ipady=12)

        tb.Button(self.root, text="Lua & Manifest Mode",
                  bootstyle="info outline", width=20,
                  command=lambda: self.show_screen(self.workshop_file_mover)).pack(pady=10, ipadx=12, ipady=12)

        tb.Button(self.root, text="Uninstaller",
                  bootstyle="danger outline", width=20,
                  command=lambda: self.show_screen(self.uninstaller)).pack(pady=10, ipadx=12, ipady=12)

        tb.Button(self.root, text="View Log",
                  bootstyle="warning outline", width=20,
                  command=lambda: self.show_screen(self.view_log)).pack(pady=10, ipadx=12, ipady=12)

        tb.Button(self.root, text="Credits",
                  bootstyle="success outline", width=20,
                  command=lambda: self.show_screen(self.credits_screen)).pack(pady=10, ipadx=12, ipady=12)

    # ----------------- Downloader -----------------
    def mod_downloader(self):
        self.add_return_arrow()

        tb.Label(self.root, text="Search for Mods:", font=("Segoe UI", 14)).pack(pady=10)
        self.search_entry = tb.Entry(self.root, width=50)
        self.search_entry.pack(pady=5)

        tb.Label(self.root, text="App ID:").pack(pady=5)
        self.app_id_entry = tb.Entry(self.root, width=10)
        self.app_id_entry.insert(0, self.app_id)
        self.app_id_entry.pack(pady=5)

        tb.Button(self.root, text="Search",
                  bootstyle="primary outline", command=self.on_search).pack(pady=10, ipadx=10, ipady=8)

        self.link_list = tk.Listbox(
            self.root, width=80, height=10,
            bg="#2b2b2b", fg="white",
            selectbackground="#0d6efd", selectforeground="white",
            highlightbackground="#444"
        )
        self.link_list.pack(pady=10)

        tb.Button(self.root, text="Install Selected Mod",
                  bootstyle="success outline",
                  command=self.on_install).pack(pady=10, ipadx=10, ipady=8)

    def search_smods(self, query):
        self.app_id = self.app_id_entry.get()
        base_url = "https://catalogue.smods.ru/?s="
        app_id = f"&app={self.app_id}"
        search_url = f"{base_url}{quote_plus(query)}{app_id}"
        try:
            response = requests.get(search_url, timeout=15)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                return [link['href'] for link in soup.find_all('a', class_='skymods-excerpt-btn')
                        if "modsbase.com" in link.get('href', "")]
        except Exception as e:
            self._log(f"❌ search_smods error: {e}")
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
            self._log(f"❌ Error extracting link: {e}")
        finally:
            if driver:
                driver.quit()
        return None

    def on_search(self):
        query = self.search_entry.get()
        links = self.search_smods(query)
        self.link_list.delete(0, "end")
        for link in links:
            self.link_list.insert("end", link)

    def on_install(self):
        selected = self.link_list.curselection()
        if not selected:
            messagebox.showwarning("Warning", "No mod selected")
            return
        url = self.link_list.get(selected[0])
        self._log(f"Starting install from {url}")
        download_link = self.extract_download_link(url)
        if download_link:
            os.makedirs("workshop_mod", exist_ok=True)
            zip_path = os.path.join("workshop_mod", "mod.zip")
            try:
                with requests.get(download_link, stream=True, timeout=60) as r:
                    r.raise_for_status()
                    with open(zip_path, "wb") as f:
                        for chunk in r.iter_content(chunk_size=8192):
                            f.write(chunk)
                with zipfile.ZipFile(zip_path, "r") as zip_ref:
                    zip_ref.extractall("workshop_mod")
                os.remove(zip_path)
                self._log(f"✅ Installed mod from {url} ({download_link})")
                messagebox.showinfo("Success", "Mod installed successfully!")
            except Exception as e:
                self._log(f"❌ Install failed for {url}: {e}")
                messagebox.showerror("Error", f"Install failed: {e}")
        else:
            messagebox.showerror("Error", "Failed to get download link.")

    # ----------------- File Mover -----------------
    def workshop_file_mover(self):
        self.add_return_arrow()
        tb.Label(self.root, text="Move Lua & Manifest Files", font=("Segoe UI", 20, "bold")).pack(pady=20)

    # ----------------- Uninstaller -----------------
    def uninstaller(self):
        self.add_return_arrow()
        tb.Label(self.root, text="Uninstall Mods", font=("Segoe UI", 20, "bold")).pack(pady=20)

    # ----------------- Credits -----------------
    def credits_screen(self):
        self.add_return_arrow()

        # Main credits labels with rainbow effect
        self.credits_label1 = tb.Label(self.root, text="Meng (This took a LONG time)", font=("Segoe UI", 20, "bold"))
        self.credits_label1.place(relx=0.5, rely=0.2, anchor="center")

        self.credits_label2 = tb.Label(self.root, text="Spade for testing",
                                       font=("Segoe UI", 14))
        self.credits_label2.place(relx=0.5, rely=0.4, anchor="center")

        self.credits_label3 = tb.Label(self.root, text="Soldy for also testing",
                                       font=("Segoe UI", 14))
        self.credits_label3.place(relx=0.5, rely=0.6, anchor="center")

        # Rainbow palette
        self.rainbow_colors = [
            (255, 0, 0), (255, 127, 0), (255, 255, 0),
            (0, 255, 0), (0, 0, 255), (75, 0, 130), (148, 0, 211)
        ]

        # Animation states
        self.fade_step = [0, 5, 10]      # staggered starts
        self.color_index = [0, 2, 4]     # each label starts at different color
        self.direction = [1, 1, 1]       # 1 = forward, -1 = backward
        self.pulse_step = 0              # global pulse step

        self.animate_rainbow_fade()

    def animate_rainbow_fade(self):
        # Pulse brightness factor (oscillates 0.85 → 1.15)
        brightness = 1 + 0.15 * math.sin(math.radians(self.pulse_step))
        self.pulse_step = (self.pulse_step + 5) % 360  # smooth sine wave loop

        for i, label in enumerate([self.credits_label1, self.credits_label2, self.credits_label3]):
            step_fraction = self.fade_step[i] / 15

            # Current & target based on direction
            current_idx = self.color_index[i]
            target_idx = current_idx + self.direction[i]

            if target_idx >= len(self.rainbow_colors):
                target_idx = len(self.rainbow_colors) - 2
                self.direction[i] = -1
            elif target_idx < 0:
                target_idx = 1
                self.direction[i] = 1

            current = self.rainbow_colors[current_idx]
            target = self.rainbow_colors[target_idx]

            # Interpolate
            r = int(current[0] + (target[0] - current[0]) * step_fraction)
            g = int(current[1] + (target[1] - current[1]) * step_fraction)
            b = int(current[2] + (target[2] - current[2]) * step_fraction)

            # Apply glow (brightness scaling)
            r = max(0, min(int(r * brightness), 255))
            g = max(0, min(int(g * brightness), 255))
            b = max(0, min(int(b * brightness), 255))

            # Apply color to label
            label.config(foreground=self.rgb_to_hex((r, g, b)))

            # Update fade progress
            if self.fade_step[i] < 15:
                self.fade_step[i] += 1
            else:
                self.fade_step[i] = 0
                self.color_index[i] += self.direction[i]

        # Schedule next update
        self.root.after(50, self.animate_rainbow_fade)

    def rgb_to_hex(self, rgb):
        return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"


if __name__ == "__main__":
    root = TkinterDnD.Tk()
    root.geometry("700x500")
    root.title("Mod Downloader")
    app = ModDownloader(root)
    root.mainloop()
