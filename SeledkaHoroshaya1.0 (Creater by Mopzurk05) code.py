import customtkinter as ctk
import psutil
import os
import winreg
import subprocess
import shutil
from tkinter import messagebox

class SeledkaHoroshaya(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("SeledkaHoroshaya1.0")
        self.geometry("1200x850")
        ctk.set_appearance_mode("dark")
        
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.sidebar = ctk.CTkFrame(self, width=220, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        
        ctk.CTkLabel(self.sidebar, text="SELEDKA 1.0", font=("Arial", 20, "bold")).pack(pady=20)

        btns = [
            ("Дашборд", self.show_dashboard),
            ("Автозагрузка+", self.show_startup),
            ("Диспетчер задач", self.show_tasks),
            ("Ограничения", self.show_limits),
            ("Очистка Кэша", self.clean_temp),
            ("FIX Загрузчик", self.show_boot_fix)
        ]
        
        for text, cmd in btns:
            ctk.CTkButton(self.sidebar, text=text, command=cmd).pack(pady=5, padx=20)

        ctk.CTkButton(self.sidebar, text="Restart Explorer", fg_color="#34495E", 
                     command=lambda: os.system("taskkill /f /im explorer.exe & start explorer")).pack(side="bottom", pady=20, padx=20)

        self.main_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        
        self.search_query = ""
        self.show_dashboard()

    def clear(self):
        for w in self.main_frame.winfo_children(): w.destroy()

    def show_dashboard(self):
        self.clear()
        ctk.CTkLabel(self.main_frame, text="Мониторинг ресурсов", font=("Arial", 22, "bold")).pack(pady=20)
        cpu = psutil.cpu_percent()
        ram = psutil.virtual_memory().percent
        for name, val in [("CPU", cpu), ("RAM", ram)]:
            f = ctk.CTkFrame(self.main_frame); f.pack(pady=10, fill="x", padx=20)
            ctk.CTkLabel(f, text=f"{name}: {val}%", font=("Arial", 14)).pack()
            bar = ctk.CTkProgressBar(f, width=500); bar.set(val/100); bar.pack(pady=10)

    def show_startup(self):
        self.clear()
        reg_configs = [
            (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", "HKCU Run"),
            (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\Run", "HKLM Run"),
            (winreg.HKEY_LOCAL_MACHINE, r"Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Run", "HKLM x32 Run")
        ]
        for root, path, label in reg_configs:
            try:
                key = winreg.OpenKey(root, path, 0, winreg.KEY_READ)
                for i in range(winreg.QueryInfoKey(key)[1]):
                    name, val, _ = winreg.EnumValue(key, i)
                    if "Windows" not in str(val):
                        f = ctk.CTkFrame(self.main_frame); f.pack(fill="x", pady=2, padx=5)
                        ctk.CTkLabel(f, text=f"[{label}] {name}").pack(side="left", padx=10, pady=5)
                        ctk.CTkButton(f, text="Удалить", width=80, fg_color="#C0392B", 
                                     command=lambda r=root, p=path, n=name: self.del_reg(r, p, n)).pack(side="right", padx=10)
                winreg.CloseKey(key)
            except: continue

    def del_reg(self, root, path, name):
        try:
            key = winreg.OpenKey(root, path, 0, winreg.KEY_SET_VALUE)
            winreg.DeleteValue(key, name); winreg.CloseKey(key); self.show_startup()
        except: messagebox.showerror("Ошибка", "Нужны права Админа")

    def show_tasks(self):
        self.clear()
        entry = ctk.CTkEntry(self.main_frame, placeholder_text="Поиск...", width=300)
        entry.pack(pady=10); entry.insert(0, self.search_query)
        ctk.CTkButton(self.main_frame, text="Найти", command=lambda: [setattr(self, 'search_query', entry.get()), self.show_tasks()]).pack()
        for proc in psutil.process_iter(['pid', 'name', 'exe', 'status']):
            try:
                p = proc.info
                if p['exe'] and (self.search_query.lower() in p['name'].lower()):
                    f = ctk.CTkFrame(self.main_frame); f.pack(fill="x", pady=2)
                    st = "⏸️" if p['status'] == 'stopped' else "▶️"
                    ctk.CTkLabel(f, text=f"{st} {p['name']} ({p['pid']})\n{p['exe']}", justify="left", font=("Arial", 10)).pack(side="left", padx=10)
                    btn_f = ctk.CTkFrame(f, fg_color="transparent"); btn_f.pack(side="right", padx=5)
                    ctk.CTkButton(btn_f, text="Kill", width=60, fg_color="#C0392B", command=lambda pr=proc: [pr.kill(), self.show_tasks()]).pack(side="right", padx=2)
                    if p['status'] == 'stopped':
                        ctk.CTkButton(btn_f, text="Play", width=60, fg_color="green", command=lambda pr=proc: [pr.resume(), self.show_tasks()]).pack(side="right", padx=2)
                    else:
                        ctk.CTkButton(btn_f, text="Wait", width=60, command=lambda pr=proc: [pr.suspend(), self.show_tasks()]).pack(side="right", padx=2)
            except: continue

    def show_limits(self):
        self.clear()
        ctk.CTkLabel(self.main_frame, text="Активные ограничения системы", font=("Arial", 18, "bold")).pack(pady=10)
        pts = [
            (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Policies\System"),
            (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Policies\Explorer"),
            (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\Policies\System"),
            (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\Policies\Explorer"),
            (winreg.HKEY_USERS, r".DEFAULT\Software\Microsoft\Windows\CurrentVersion\Policies\System")
        ]
        found = False
        for root, p in pts:
            try:
                key = winreg.OpenKey(root, p, 0, winreg.KEY_READ)
                for i in range(winreg.QueryInfoKey(key)[1]):
                    name, val, _ = winreg.EnumValue(key, i)
                    if val == 1:
                        found = True
                        f = ctk.CTkFrame(self.main_frame); f.pack(fill="x", pady=2, padx=10)
                        ctk.CTkLabel(f, text=f"⚠️ {name} (заблокировано)").pack(side="left", padx=10)
                        ctk.CTkButton(f, text="Снять", width=80, command=lambda r=root, path=p, n=name: self.unl(r, path, n)).pack(side="right", padx=10)
                winreg.CloseKey(key)
            except: continue
        if not found: ctk.CTkLabel(self.main_frame, text="Ограничений не найдено", text_color="gray").pack(pady=20)

    def unl(self, root, path, name):
        try:
            key = winreg.OpenKey(root, path, 0, winreg.KEY_SET_VALUE)
            winreg.DeleteValue(key, name); winreg.CloseKey(key); self.show_limits()
        except: messagebox.showerror("Ошибка", "Запустите от имени Администратора")

    def clean_temp(self):
        for d in [os.getenv('TEMP'), r"C:\Windows\Temp"]:
            try:
                for item in os.listdir(d):
                    p = os.path.join(d, item)
                    try:
                        if os.path.isfile(p): os.unlink(p)
                        else: shutil.rmtree(p)
                    except: continue
            except: continue
        messagebox.showinfo("Seledka", "Очистка завершена!")

    def show_boot_fix(self):
        self.clear()
        ctk.CTkButton(self.main_frame, text="Fix MBR", width=300, command=lambda: subprocess.run("bootrec /fixmbr", shell=True)).pack(pady=10)
        ctk.CTkButton(self.main_frame, text="Fix UEFI (BCDBoot)", width=300, command=lambda: subprocess.run("bcdboot C:\\Windows", shell=True)).pack(pady=10)

if __name__ == "__main__":
    SeledkaHoroshaya().mainloop()
