import discord
from discord.ext import commands
import customtkinter as ctk
import threading
import asyncio
from datetime import datetime, timedelta
import time
import psutil
import random
import os  # Dosya işlemleri için eklendi

# ==========================================
# CORE - CONFIG
# ==========================================
SABIT_DURUM = "Core Aktif" 
TOKEN_FILE = "token.core" # Tokenın saklanacağı dosya adı
# ==========================================

ctk.set_appearance_mode("dark")

class CoreApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Core")
        self.attributes("-fullscreen", True)
        self.configure(fg_color="#000000")
        
        self.bind("<F11>", self.toggle_fullscreen)
        self.bind("<Escape>", lambda e: self.attributes("-fullscreen", False))

        self.start_time = time.time()
        self.bot_instance = None
        self.is_running = False
        self.processed_messages = set() 
        self.user_cooldowns = {} 

        self.draw_brackets()

        # --- SİSTEM VERİLERİ ---
        self.stats_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.stats_frame.place(x=40, y=100)
        
        self.uptime_label = self.add_stat("RUNTIME: 00:00:00")
        self.ping_label = self.add_stat("NET PING: -- ms")
        self.cpu_label = self.add_stat("CPU LOAD: -- %")
        self.mem_label = self.add_stat("MEM LOAD: -- %")
        self.socket_label = self.add_stat("SOCKET: DISCONNECTED")

        # --- ANA BAŞLIK ---
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.pack(pady=(80, 5))
        
        self.header = ctk.CTkLabel(self.header_frame, text="CORE", font=("Impact", 160), text_color="#FFFFFF")
        self.header.grid(row=0, column=0)
        
        self.status_led = ctk.CTkLabel(self.header_frame, text="■", font=("Arial", 25), text_color="#333333")
        self.status_led.grid(row=0, column=1, sticky="n", padx=10, pady=40)

        # --- GİRİŞ ALANLARI ---
        self.token_entry = ctk.CTkEntry(self, placeholder_text="DISCORD TOKENINIZI BURAYA GIRIN...", 
                                         width=500, height=35, fg_color="#111111", border_color="#333333", 
                                         text_color="#FFFFFF", font=("Consolas", 12), border_width=1, corner_radius=0)
        self.token_entry.pack(pady=5)

        self.reason_entry = ctk.CTkEntry(self, placeholder_text="DURUM NOTUNU YAZIN...", 
                                         width=500, height=50, fg_color="#000000", border_color="#FFFFFF", 
                                         text_color="#FFFFFF", font=("Arial", 16), border_width=1, corner_radius=0)
        self.reason_entry.pack(pady=10)

        self.action_button = ctk.CTkButton(self, text="SİSTEMİ BAŞLAT", command=self.toggle_system, 
                                          fg_color="#FFFFFF", text_color="#000000", hover_color="#888888", 
                                          font=("Impact", 22), width=300, height=60, corner_radius=0)
        self.action_button.pack()

        # --- LOG KUTUSU ---
        self.log_box = ctk.CTkTextbox(self, width=1000, height=300, fg_color="#000000", border_color="#333333", 
                                     border_width=1, text_color="#FFFFFF", font=("Consolas", 14), corner_radius=0)
        self.log_box.pack(pady=(30, 10))

        # --- BAŞLANGIÇ AYARLARI ---
        self.load_saved_token() # Kayıtlı tokenı yükle
        self.update_system_metrics()
        self.pulse_led()

    def load_saved_token(self):
        """Uygulama açıldığında kayıtlı token varsa kutuya yazar."""
        if os.path.exists(TOKEN_FILE):
            try:
                with open(TOKEN_FILE, "r") as f:
                    saved_token = f.read().strip()
                    if saved_token:
                        self.token_entry.insert(0, saved_token)
                        self.log("SİSTEM: Kayıtlı token otomatik yüklendi.")
            except:
                self.log("HATA: Kayıtlı token dosyası okunamadı.")

    def save_token(self, token):
        """Tokenı yerel dosyaya kaydeder."""
        try:
            with open(TOKEN_FILE, "w") as f:
                f.write(token)
        except Exception as e:
            self.log(f"HATA: Token kaydedilemedi: {e}")

    def toggle_fullscreen(self, event=None):
        is_fs = self.attributes("-fullscreen")
        self.attributes("-fullscreen", not is_fs)

    def draw_brackets(self):
        c = "#FFFFFF"
        ctk.CTkLabel(self, text="┌", font=("Arial", 40), text_color=c).place(x=20, y=20)
        ctk.CTkLabel(self, text="┐", font=("Arial", 40), text_color=c).place(relx=1.0, x=-45, y=20)
        ctk.CTkLabel(self, text="└", font=("Arial", 40), text_color=c).place(x=20, rely=1.0, y=-65)
        ctk.CTkLabel(self, text="┘", font=("Arial", 40), text_color=c).place(relx=1.0, x=-45, rely=1.0, y=-65)

    def add_stat(self, text):
        lbl = ctk.CTkLabel(self.stats_frame, text=text, font=("Consolas", 12, "bold"), text_color="#444444", anchor="w")
        lbl.pack(pady=2, anchor="w")
        return lbl

    def update_system_metrics(self):
        if self.is_running:
            uptime = time.time() - self.start_time
            m, s = divmod(int(uptime), 60)
            h, m = divmod(m, 60)
            self.uptime_label.configure(text=f"RUNTIME: {h:02d}:{m:02d}:{s:02d}", text_color="#FFFFFF")
            if self.bot_instance and self.bot_instance.latency:
                ping = round(self.bot_instance.latency * 1000)
                self.ping_label.configure(text=f"NET PING: {ping} ms", text_color="#00FF00" if ping < 150 else "#FF0000")
        
        self.cpu_label.configure(text=f"CPU LOAD: {psutil.cpu_percent()}%", text_color="#FFFFFF")
        self.mem_label.configure(text=f"MEM LOAD: {psutil.virtual_memory().percent}%", text_color="#FFFFFF")
        self.after(2000, self.update_system_metrics)

    def pulse_led(self):
        if self.is_running:
            current_color = self.status_led.cget("text_color")
            new_color = "#FFFFFF" if current_color == "#333333" else "#333333"
            self.status_led.configure(text_color=new_color)
        else:
            self.status_led.configure(text_color="#333333")
        self.after(800, self.pulse_led)

    def log(self, msg):
        t = datetime.now().strftime("%H:%M:%S")
        self.log_box.insert("end", f"[{t}] >>> {msg}\n")
        self.log_box.see("end")

    def toggle_system(self):
        if not self.is_running: self.start_system()
        else: self.stop_system()

    def start_system(self):
        token = self.token_entry.get().strip()
        if not token:
            self.log("HATA: Lütfen önce bir Token girin.")
            return

        # Başarılı girişte tokenı kaydet
        self.save_token(token)

        self.is_running = True
        self.start_time = time.time()
        self.action_button.configure(text="SİSTEMİ DURDUR", fg_color="#FF0000", text_color="#FFFFFF")
        self.socket_label.configure(text="SOCKET: CONNECTED", text_color="#00FF00")
        
        self.bot_instance = commands.Bot(command_prefix=".", self_bot=True)

        @self.bot_instance.event
        async def on_ready():
            await self.bot_instance.change_presence(activity=discord.Game(name=SABIT_DURUM))
            self.log(f"Core Protokolü Aktif: {self.bot_instance.user}")

        @self.bot_instance.event
        async def on_message(message):
            if not self.is_running or message.author == self.bot_instance.user:
                return

            if isinstance(message.channel, discord.DMChannel) or self.bot_instance.user.mentioned_in(message):
                user_id = message.author.id
                now = datetime.now()
                if user_id in self.user_cooldowns:
                    if now < self.user_cooldowns[user_id]:
                        return 
                
                self.user_cooldowns[user_id] = now + timedelta(minutes=5)
                self.log(f"MESAJ: {message.author} -> Analiz ediliyor...")
                
                async with message.channel.typing():
                    wait_time = random.uniform(2, 5)
                    await asyncio.sleep(wait_time)
                    
                    panel_notu = self.reason_entry.get() or "Sistem Aktif"
                    
                    cevap = (
                        "**Core Kişisel Asistan**\n\n"
                        "Selam! Şu an bilgisayar başında değilim.\n"
                        f"**Durum:** {panel_notu}\n\n"
                        "Müsait olduğumda döneceğim."
                    )
                    
                    await message.channel.send(cevap)
                    self.log(f"YANIT: {message.author} kişisine iletildi.")

        def run_bot():
            try:
                self.bot_instance.run(token)
            except Exception as e:
                self.log(f"BAGLANTI HATASI: {e}")
                self.stop_system()

        threading.Thread(target=run_bot, daemon=True).start()
        self.log("Protokoller yükleniyor...")

    def stop_system(self):
        self.is_running = False
        self.action_button.configure(text="SİSTEMİ BAŞLAT", fg_color="#FFFFFF", text_color="#000000")
        self.socket_label.configure(text="SOCKET: DISCONNECTED", text_color="#444444")
        self.log("Sistem devre dışı.")

if __name__ == "__main__":
    app = CoreApp()
    app.mainloop()