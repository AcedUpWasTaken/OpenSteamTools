import os
import shutil
import requests
import zipfile
import datetime
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
        tb.Label(self.root, text="Workshop File Mover", font=("Segoe UI", 20, "bold")).pack(pady=20)
        tb.Label(self.root, text="Drag and drop files here:").pack(pady=10)
        self.root.drop_target_register(DND_FILES)
        self.root.dnd_bind("<<Drop>>", self.drop)

    def drop(self, event):
        for file in event.data.split():
            target_dir = None
            if file.endswith('.manifest'):
                target_dir = self.MANIFEST_DIR
            elif file.endswith('.lua'):
                target_dir = self.LUA_ST_DIR
            if target_dir:
                try:
                    shutil.move(file, target_dir)
                    self._log(f"Moved {file} → {target_dir}")
                except Exception as e:
                    self._log(f"Error moving {file}: {e}")

    # ----------------- Uninstaller -----------------
    def uninstaller(self):
        self.add_return_arrow()
        tb.Label(self.root, text="Uninstaller", font=("Segoe UI", 20, "bold")).pack(pady=20)

        # Game count
        self.game_count_label = tb.Label(self.root, text="Scanning...", font=("Segoe UI", 12))
        self.game_count_label.pack(pady=5)

        # Dropdown
        tb.Label(self.root, text="Select App ID:").pack(pady=5)
        self.appid_var = tk.StringVar()
        self.appid_combo = tb.Combobox(self.root, textvariable=self.appid_var, state="readonly", width=25)
        self.appid_combo.pack(pady=5)

        tb.Button(self.root, text="Uninstall Selected",
                  bootstyle="danger outline", width=20,
                  command=self.on_uninstall).pack(pady=10, ipadx=10, ipady=8)

        # Search box
        tb.Label(self.root, text="Search App ID:").pack(pady=5)
        self.search_var = tk.StringVar()
        self.search_entry = tb.Entry(self.root, textvariable=self.search_var, width=25)
        self.search_entry.pack(pady=5)

        tb.Button(self.root, text="Search",
                  bootstyle="info outline", width=20,
                  command=self.on_search_uninstall).pack(pady=10, ipadx=10, ipady=8)

        self.search_listbox = tk.Listbox(
            self.root, width=40, height=8,
            bg="#2b2b2b", fg="white",
            selectbackground="#dc3545", selectforeground="white",
            highlightbackground="#444"
        )
        self.search_listbox.pack(pady=5)

        tb.Button(self.root, text="Uninstall From Search",
                  bootstyle="danger outline", width=20,
                  command=self.on_search_uninstall_delete).pack(pady=10, ipadx=10, ipady=8)

        self.populate_appids()

    def populate_appids(self):
        try:
            appids = []
            for file in os.listdir(self.LUA_ST_DIR):
                if file.endswith(".lua"):
                    appid = file[:-4]
                    if appid.isdigit():
                        appids.append(int(appid))
                    else:
                        appids.append(appid)
            appids = sorted(appids, key=lambda x: (isinstance(x, str), x))
            appids_str = [str(a) for a in appids]
            self.appid_combo["values"] = appids_str
            if appids_str:
                self.appid_combo.current(0)
            self.game_count_label.config(text=f"{len(appids_str)} games installed")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to scan App IDs: {e}")

    def on_uninstall(self):
        appid = self.appid_var.get()
        if not appid:
            messagebox.showwarning("Warning", "No App ID selected")
            return
        self._uninstall_by_appid(appid)

    def on_search_uninstall(self):
        query = self.search_var.get().strip()
        self.search_listbox.delete(0, "end")
        if not query:
            return
        results = []
        try:
            for file in os.listdir(self.LUA_ST_DIR):
                if file.endswith(".lua"):
                    aid = file[:-4]
                    if query in aid:
                        results.append(aid)
            results = sorted(results, key=lambda x: int(x) if x.isdigit() else x)
            for appid in results:
                self.search_listbox.insert("end", appid)
        except Exception as e:
            messagebox.showerror("Error", f"Search failed: {e}")

    def on_search_uninstall_delete(self):
        sel = self.search_listbox.curselection()
        if not sel:
            messagebox.showwarning("Warning", "No App ID selected from search results")
            return
        appid = self.search_listbox.get(sel[0])
        self._uninstall_by_appid(appid)

    def _uninstall_by_appid(self, appid):
        filename = f"{appid}.lua"
        filepath = os.path.join(self.LUA_ST_DIR, filename)
        if not os.path.exists(filepath):
            messagebox.showerror("Error", f"{filename} not found")
            return
        try:
            os.remove(filepath)
            self._log(f"🗑️ Uninstalled {filename} from {self.LUA_ST_DIR}")
            messagebox.showinfo("Success", f"Uninstalled {filename}")
            self.populate_appids()
            self.on_search_uninstall()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to uninstall {filename}: {e}")

    # ----------------- Credits -----------------
    def credits_screen(self):
        self.add_return_arrow()
        self.credits_label = tb.Label(self.root, text="Meng (This took a LONG time)",
                                      font=("Segoe UI", 20, "bold"))
        self.credits_label.place(relx=0.5, rely=0.5, anchor="center")

        self.current_rgb = (255, 0, 0)
        self.target_rgb = (255, 127, 0)
        self.color_index = 1
        self.fade_step = 0
        self.animate_rainbow_fade()

    def rgb_to_hex(self, rgb):
        return "#%02x%02x%02x" % rgb

    def animate_rainbow_fade(self):
        r1, g1, b1 = self.current_rgb
        r2, g2, b2 = self.target_rgb
        step_fraction = self.fade_step / 15
        r = int(r1 + (r2 - r1) * step_fraction)
        g = int(g1 + (g2 - g1) * step_fraction)
        b = int(b1 + (b2 - b1) * step_fraction)
        if hasattr(self, "credits_label"):
            self.credits_label.config(foreground=self.rgb_to_hex((r, g, b)))
        if self.fade_step < 15:
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


# ----------------- Run App -----------------
if __name__ == "__main__":
    root = TkinterDnD.Tk()
    root.title("Mod Downloader and File Manager")
    root.geometry("700x500")
    app = ModDownloader(root)
    root.mainloop()
