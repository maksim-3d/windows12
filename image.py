import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, simpledialog
import webbrowser
import os
import json
import threading
from datetime import datetime
import random
import math
import time
import requests
from PIL import Image, ImageTk, ImageGrab
import io
import base64
import smtplib
import sqlite3
import re
import imaplib
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import decode_header
import ctypes
from ctypes import wintypes

# ==================== ОБЩИЕ УТИЛИТЫ ====================
class Utils:
    @staticmethod
    def load_data(filename, default):
        try:
            if os.path.exists(filename):
                with open(filename, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except: pass
        return default

    @staticmethod
    def save_data(filename, data):
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except: pass

    @staticmethod
    def center_window(window, width, height):
        screen_width = window.winfo_screenwidth()
        screen_height = window.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        window.geometry(f"{width}x{height}+{x}+{y}")

    @staticmethod
    def hex_to_rgb(hex_color):
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

# ==================== STEAM РЕГИСТРАЦИЯ ====================
class AdvancedGmailSteamRegistration:
    def __init__(self, parent):
        self.parent = parent
        self.setup_database()
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587
        self.imap_server = "imap.gmail.com"
        self.sender_gmail = "rogovm700@gmail.com"
        self.sender_password = "kgdtaqesiovnapcq"
        self.current_user_data = {}
        self.verification_code = None
        self.saved_users = Utils.load_data('steam_users.json', {})

    def setup_database(self):
        self.conn = sqlite3.connect('steam_registration.db')
        self.cursor = self.conn.cursor()
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS steam_users (
                username TEXT PRIMARY KEY,
                gmail TEXT,
                steam_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        self.conn.commit()

    def save_user(self, username, gmail, steam_id):
        self.saved_users[username] = {
            'gmail': gmail, 'steam_id': steam_id, 'timestamp': datetime.now().strftime("%d.%m.%Y %H:%M")
        }
        Utils.save_data('steam_users.json', self.saved_users)
        self.cursor.execute('INSERT OR REPLACE INTO steam_users (username, gmail, steam_id) VALUES (?, ?, ?)', 
                          (username, gmail, steam_id))
        self.conn.commit()

    def is_valid_gmail(self, email):
        return re.match(r'^[a-zA-Z0-9._%+-]+@gmail\.com$', email) is not None

    def generate_verification_code(self): 
        return str(random.randint(100000, 999999))

    def generate_steam_id(self): 
        return f"STEAM_0:{random.randint(0,1)}:{random.randint(100000, 9999999)}"

    def send_verification_email(self, receiver_gmail, code):
        try:
            message = MIMEMultipart()
            message["From"] = self.sender_gmail
            message["To"] = receiver_gmail
            message["Subject"] = "Код подтверждения регистрации Steam"
            
            body = f"""
            <html><body style="font-family: Arial; background: #1b2838; color: white; padding: 20px;">
                <div style="max-width: 600px; margin: 0 auto; background: #2a475e; padding: 30px; border-radius: 10px;">
                    <div style="text-align: center; margin-bottom: 30px;">
                        <h1 style="color: #66c0f4;">🎮 STEAM</h1>
                        <p style="color: #c7d5e0;">Регистрация аккаунта</p>
                    </div>
                    <div style="background: #1b2838; padding: 20px; border-radius: 8px; text-align: center;">
                        <h2 style="color: #90ba3c;">🔐 Код подтверждения</h2>
                        <div style="background: #2a475e; padding: 20px; margin: 15px 0; border-radius: 5px;">
                            <div style="font-size: 32px; font-weight: bold; letter-spacing: 8px; color: #ffffff;">{code}</div>
                        </div>
                    </div>
                </div></body></html>"""
            
            message.attach(MIMEText(body, "html"))
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_gmail, self.sender_password)
                server.send_message(message)
            return True
        except Exception as e: 
            print(f"Ошибка отправки: {e}")
            return False

    def clean_gmail_messages(self):
        try:
            mail = imaplib.IMAP4_SSL(self.imap_server)
            mail.login(self.sender_gmail, self.sender_password)
            mail.select("inbox")
            status, messages = mail.search(None, '(SUBJECT "Код подтверждения Steam")')
            email_ids = messages[0].split()
            deleted_count = 0
            for email_id in email_ids:
                try:
                    mail.store(email_id, '+FLAGS', '\\Deleted')
                    deleted_count += 1
                except: continue
            mail.expunge()
            mail.close()
            mail.logout()
            return deleted_count
        except Exception as e: 
            print(f"Ошибка очистки почты: {e}")
            return 0

    def show_registration_window(self):
        self.reg_window = tk.Toplevel(self.parent)
        self.reg_window.title("Регистрация Steam")
        self.reg_window.geometry("500x600")
        self.reg_window.configure(bg='#1b2838')
        self.reg_window.resizable(False, False)
        Utils.center_window(self.reg_window, 500, 600)
        self.show_welcome_screen()

    def clear_reg_window(self):
        for widget in self.reg_window.winfo_children():
            widget.destroy()

    def create_steam_button(self, parent, text, command, bg='#5c7e10', width=20):
        return tk.Button(parent, text=text, font=('Arial', 11), bg=bg, fg='white', 
                       bd=0, cursor='hand2', width=width, pady=8, command=command)

    def create_steam_entry(self, parent, width=30):
        return tk.Entry(parent, font=('Arial', 11), bg='#2a475e', fg='white',
                      insertbackground='white', width=width, relief='solid', bd=1)

    def show_welcome_screen(self):
        self.clear_reg_window()
        title_frame = tk.Frame(self.reg_window, bg='#1b2838')
        title_frame.pack(pady=40)
        
        tk.Label(title_frame, text="🎮", font=('Arial', 48), bg='#1b2838', fg='#66c0f4').pack()
        tk.Label(title_frame, text="STEAM", font=('Arial', 32, 'bold'), bg='#1b2838', fg='#66c0f4').pack(pady=10)
        tk.Label(title_frame, text="Создание учетной записи", font=('Arial', 14), bg='#1b2838', fg='#c7d5e0').pack()
        
        content_frame = tk.Frame(self.reg_window, bg='#1b2838')
        content_frame.pack(pady=30)
        
        self.create_steam_button(content_frame, "📝 Создать аккаунт", self.show_step1).pack(pady=15)
        
        if self.saved_users:
            tk.Label(content_frame, text="Или выберите существующий аккаунт:", 
                    font=('Arial', 10), bg='#1b2838', fg='#8f98a0').pack(pady=20)
            for username, data in self.saved_users.items():
                self.create_steam_button(content_frame, f"👤 {username}",
                    lambda u=username, g=data['gmail'], s=data['steam_id']: self.quick_login(u, g, s),
                    bg='#2a475e', width=25).pack(pady=5)

    def quick_login(self, username, gmail, steam_id):
        self.current_user_data = {'username': username, 'gmail': gmail, 'steam_id': steam_id}
        messagebox.showinfo("Steam", f"Добро пожаловать, {username}!")
        self.reg_window.destroy()
        return self.current_user_data

    def show_step1(self):
        self.clear_reg_window()
        title_frame = tk.Frame(self.reg_window, bg='#1b2838')
        title_frame.pack(pady=20)
        tk.Label(title_frame, text="ШАГ 1: Имя аккаунта", font=('Arial', 16, 'bold'), bg='#1b2838', fg='#66c0f4').pack()
        tk.Label(title_frame, text="Выберите имя для вашего аккаунта Steam", font=('Arial', 11), bg='#1b2838', fg='#c7d5e0').pack(pady=5)
        
        form_frame = tk.Frame(self.reg_window, bg='#1b2838')
        form_frame.pack(pady=30)
        tk.Label(form_frame, text="Имя аккаунта:", font=('Arial', 11), bg='#1b2838', fg='white').pack(pady=5)
        self.username_entry = self.create_steam_entry(form_frame)
        self.username_entry.pack(pady=10)
        self.username_entry.focus()
        
        buttons_frame = tk.Frame(self.reg_window, bg='#1b2838')
        buttons_frame.pack(pady=20)
        tk.Button(buttons_frame, text="← Назад", font=('Arial', 10), bg='#2a475e', fg='white', bd=0, cursor='hand2',
                 command=self.show_welcome_screen).pack(side=tk.LEFT, padx=10)
        self.create_steam_button(buttons_frame, "Далее →", self.process_step1).pack(side=tk.LEFT, padx=10)
        self.reg_window.bind('<Return>', lambda e: self.process_step1())

    def process_step1(self):
        username = self.username_entry.get().strip()
        if not username: 
            messagebox.showerror("Ошибка", "Введите имя аккаунта!")
            return
        if len(username) < 3: 
            messagebox.showerror("Ошибка", "Имя аккаунта должно быть не менее 3 символов!")
            return
        
        if username in self.saved_users:
            if messagebox.askyesno("Аккаунт существует", f"Аккаунт '{username}' уже зарегистрирован.\nХотите войти в этот аккаунт?"):
                data = self.saved_users[username]
                self.quick_login(username, data['gmail'], data['steam_id'])
                return
        
        self.current_user_data['username'] = username
        self.show_step2()

    def show_step2(self):
        self.clear_reg_window()
        title_frame = tk.Frame(self.reg_window, bg='#1b2838')
        title_frame.pack(pady=20)
        tk.Label(title_frame, text="ШАГ 2: Электронная почта", font=('Arial', 16, 'bold'), bg='#1b2838', fg='#66c0f4').pack()
        tk.Label(title_frame, text="Для защиты аккаунта требуется подтверждение email", font=('Arial', 11), bg='#1b2838', fg='#c7d5e0').pack(pady=5)
        
        info_frame = tk.Frame(self.reg_window, bg='#2a475e')
        info_frame.pack(pady=10, padx=50, fill='x')
        tk.Label(info_frame, text=f"Аккаунт: {self.current_user_data['username']}", font=('Arial', 11), bg='#2a475e', fg='#90ba3c').pack(pady=8)
        
        form_frame = tk.Frame(self.reg_window, bg='#1b2838')
        form_frame.pack(pady=30)
        tk.Label(form_frame, text="Адрес Gmail:", font=('Arial', 11), bg='#1b2838', fg='white').pack(pady=5)
        self.gmail_entry = self.create_steam_entry(form_frame)
        self.gmail_entry.pack(pady=10)
        self.gmail_entry.focus()
        
        buttons_frame = tk.Frame(self.reg_window, bg='#1b2838')
        buttons_frame.pack(pady=20)
        tk.Button(buttons_frame, text="← Назад", font=('Arial', 10), bg='#2a475e', fg='white', bd=0, cursor='hand2',
                 command=self.show_step1).pack(side=tk.LEFT, padx=10)
        self.create_steam_button(buttons_frame, "Отправить код →", self.process_step2).pack(side=tk.LEFT, padx=10)
        self.reg_window.bind('<Return>', lambda e: self.process_step2())

    def process_step2(self):
        gmail = self.gmail_entry.get().strip().lower()
        if not gmail: 
            messagebox.showerror("Ошибка", "Введите адрес Gmail!")
            return
        if not self.is_valid_gmail(gmail): 
            messagebox.showerror("Ошибка", "Введите корректный адрес Gmail!")
            return
        
        self.current_user_data['gmail'] = gmail
        cleaned_count = self.clean_gmail_messages()
        if cleaned_count > 0:
            print(f"Очищено {cleaned_count} старых писем с кодами")
        
        self.verification_code = self.generate_verification_code()
        self.show_loading()
        self.reg_window.after(100, self.send_email_and_proceed)

    def show_loading(self):
        self.clear_reg_window()
        tk.Label(self.reg_window, text="📧 Отправка кода подтверждения...", font=('Arial', 14), bg='#1b2838', fg='#66c0f4').pack(pady=40)
        self.progress = ttk.Progressbar(self.reg_window, mode='indeterminate')
        self.progress.pack(pady=20, padx=50, fill=tk.X)
        self.progress.start()

    def send_email_and_proceed(self):
        success = self.send_verification_email(self.current_user_data['gmail'], self.verification_code)
        self.progress.stop()
        self.reg_window.after(100, lambda: self.show_step3(success))

    def show_step3(self, email_sent):
        self.clear_reg_window()
        if email_sent:
            title_frame = tk.Frame(self.reg_window, bg='#1b2838')
            title_frame.pack(pady=20)
            tk.Label(title_frame, text="ШАГ 3: Подтверждение email", font=('Arial', 16, 'bold'), bg='#1b2838', fg='#66c0f4').pack()
            tk.Label(title_frame, text="Введите код из письма, отправленного на вашу почту", font=('Arial', 11), bg='#1b2838', fg='#c7d5e0').pack(pady=5)
            
            info_frame = tk.Frame(self.reg_window, bg='#2a475e')
            info_frame.pack(pady=10, padx=50, fill='x')
            tk.Label(info_frame, text=f"Аккаунт: {self.current_user_data['username']}", font=('Arial', 11), bg='#2a475e', fg='#90ba3c').pack(pady=5)
            tk.Label(info_frame, text=f"Email: {self.current_user_data['gmail']}", font=('Arial', 11), bg='#2a475e', fg='#90ba3c').pack(pady=5)
            
            form_frame = tk.Frame(self.reg_window, bg='#1b2838')
            form_frame.pack(pady=30)
            tk.Label(form_frame, text="Код подтверждения:", font=('Arial', 11), bg='#1b2838', fg='white').pack(pady=10)
            self.code_entry = self.create_steam_entry(form_frame, width=20)
            self.code_entry.config(font=('Arial', 14), justify='center')
            self.code_entry.pack(pady=10)
            self.code_entry.focus()
            
            buttons_frame = tk.Frame(self.reg_window, bg='#1b2838')
            buttons_frame.pack(pady=20)
            tk.Button(buttons_frame, text="← Назад", font=('Arial', 10), bg='#2a475e', fg='white', bd=0, cursor='hand2',
                     command=self.show_step2).pack(side=tk.LEFT, padx=10)
            self.create_steam_button(buttons_frame, "Завершить регистрацию", self.process_step3).pack(side=tk.LEFT, padx=10)
            self.reg_window.bind('<Return>', lambda e: self.process_step3())
        else:
            tk.Label(self.reg_window, text="❌ Ошибка отправки email", font=('Arial', 14), bg='#1b2838', fg='#ff4444').pack(pady=30)
            self.create_steam_button(self.reg_window, "← Попробовать снова", self.show_step2).pack(pady=20)

    def process_step3(self):
        entered_code = self.code_entry.get().strip()
        if not entered_code: 
            messagebox.showerror("Ошибка", "Введите код подтверждения!")
            return
        
        if entered_code == self.verification_code:
            steam_id = self.generate_steam_id()
            self.current_user_data['steam_id'] = steam_id
            self.save_user(self.current_user_data['username'], self.current_user_data['gmail'], steam_id)
            self.show_success_window()
        else: 
            messagebox.showerror("Ошибка", "Неверный код подтверждения!")
            self.code_entry.delete(0, tk.END)
            self.code_entry.focus()

    def show_success_window(self):
        self.clear_reg_window()
        success_frame = tk.Frame(self.reg_window, bg='#1b2838')
        success_frame.pack(expand=True)
        tk.Label(success_frame, text="🎉", font=('Arial', 64), bg='#1b2838', fg='#90ba3c').pack(pady=20)
        tk.Label(success_frame, text="АККАУНТ СОЗДАН!", font=('Arial', 20, 'bold'), bg='#1b2838', fg='#90ba3c').pack(pady=10)
        
        info_frame = tk.Frame(self.reg_window, bg='#2a475e')
        info_frame.pack(fill='x', padx=50, pady=20)
        tk.Label(info_frame, text=f"Имя аккаунта: {self.current_user_data['username']}", font=('Arial', 12), bg='#2a475e', fg='white').pack(pady=5)
        tk.Label(info_frame, text=f"Steam ID: {self.current_user_data['steam_id']}", font=('Arial', 12), bg='#2a475e', fg='white').pack(pady=5)
        tk.Label(info_frame, text=f"Email: {self.current_user_data['gmail']}", font=('Arial', 12), bg='#2a475e', fg='white').pack(pady=5)
        
        self.create_steam_button(self.reg_window, "🚀 Начать использовать Steam", self.finish_registration).pack(pady=30)
        self.reg_window.after(5000, self.finish_registration)

    def finish_registration(self):
        self.reg_window.destroy()
        return self.current_user_data

# ==================== STEAM ПРИЛОЖЕНИЕ ====================
class RealSteamApp:
    def __init__(self, parent, windows_system):
        self.window = tk.Toplevel(parent)
        self.windows_system = windows_system
        self.window.title("Steam")
        self.window.geometry("1200x800")
        self.window.configure(bg='#1b2838')
        self.gmail_registration = AdvancedGmailSteamRegistration(parent)
        self.user_data = {'logged_in': False, 'username': '', 'steam_id': '', 'games': [], 'friends': []}
        self.setup_steam_ui()

    def setup_steam_ui(self):
        if not self.user_data['logged_in']: 
            self.show_login_screen()
        else: 
            self.show_main_interface()

    def show_login_screen(self):
        for widget in self.window.winfo_children():
            widget.destroy()
        
        login_frame = tk.Frame(self.window, bg='#1b2838')
        login_frame.pack(fill='both', expand=True)
        
        logo_frame = tk.Frame(login_frame, bg='#1b2838')
        logo_frame.pack(pady=100)
        tk.Label(logo_frame, text="🎮", font=('Arial', 64), bg='#1b2838', fg='#66c0f4').pack()
        tk.Label(logo_frame, text="STEAM", font=('Arial', 32, 'bold'), bg='#1b2838', fg='#66c0f4').pack(pady=10)
        
        buttons_frame = tk.Frame(login_frame, bg='#1b2838')
        buttons_frame.pack(pady=50)
        tk.Button(buttons_frame, text="📧 Регистрация через Gmail", font=('Arial', 14), bg='#5c7e10', fg='white',
                 padx=30, pady=12, cursor='hand2', bd=0, command=self.start_gmail_registration).pack(pady=15)
        tk.Button(buttons_frame, text="🚀 Демо-режим", font=('Arial', 12), bg='#2a475e', fg='white',
                 padx=20, pady=8, cursor='hand2', bd=0, command=self.demo_login).pack(pady=10)
        
        if self.gmail_registration.saved_users:
            tk.Label(buttons_frame, text="Сохраненные аккаунты:", font=('Arial', 11), bg='#1b2838', fg='#8f98a0').pack(pady=20)
            for username, data in self.gmail_registration.saved_users.items():
                tk.Button(buttons_frame, text=f"👤 {username}", font=('Arial', 11), bg='#2a475e', fg='white',
                         padx=20, pady=6, cursor='hand2', bd=0,
                         command=lambda u=username, g=data['gmail'], s=data['steam_id']: self.login_with_saved(u, g, s)).pack(pady=5)

    def start_gmail_registration(self):
        user_data = self.gmail_registration.show_registration_window()
        if user_data:
            self.user_data.update({
                'logged_in': True, 'username': user_data['username'], 'steam_id': user_data['steam_id'],
                'games': [
                    {'name': 'Counter-Strike 2', 'playtime': '0 часов', 'installed': True},
                    {'name': 'Dota 2', 'playtime': '0 часов', 'installed': True},
                    {'name': 'Team Fortress 2', 'playtime': '0 часов', 'installed': True}
                ],
                'friends': [{'name': 'Steam Support', 'status': 'В сети', 'game': ''}]
            })
            self.show_main_interface()

    def login_with_saved(self, username, gmail, steam_id):
        self.user_data.update({
            'logged_in': True, 'username': username, 'steam_id': steam_id,
            'games': [
                {'name': 'Counter-Strike 2', 'playtime': f'{random.randint(1, 100)} часов', 'installed': True},
                {'name': 'Dota 2', 'playtime': f'{random.randint(1, 50)} часов', 'installed': True},
                {'name': 'Apex Legends', 'playtime': f'{random.randint(1, 30)} часов', 'installed': True}
            ],
            'friends': [
                {'name': 'Alex', 'status': 'В сети', 'game': 'CS2'},
                {'name': 'Maria', 'status': 'В сети', 'game': 'Dota 2'},
                {'name': 'Steam Support', 'status': 'В сети', 'game': ''}
            ]
        })
        self.show_main_interface()

    def demo_login(self):
        self.user_data.update({
            'logged_in': True, 'username': 'DemoUser', 'steam_id': 'STEAM_0:1:1234567',
            'games': [
                {'name': 'Counter-Strike 2', 'playtime': '156 часов', 'installed': True},
                {'name': 'Dota 2', 'playtime': '89 часов', 'installed': True},
                {'name': 'Apex Legends', 'playtime': '45 часов', 'installed': True},
                {'name': 'PUBG: BATTLEGROUNDS', 'playtime': '23 часа', 'installed': False},
                {'name': 'Grand Theft Auto V', 'playtime': '0 часов', 'installed': False}
            ],
            'friends': [
                {'name': 'Alex', 'status': 'В сети', 'game': 'CS2'},
                {'name': 'Maria', 'status': 'В сети', 'game': 'Dota 2'},
                {'name': 'John', 'status': 'Не в сети', 'game': ''},
                {'name': 'Sarah', 'status': 'Занят', 'game': 'Apex'}
            ]
        })
        self.show_main_interface()

    def show_main_interface(self):
        for widget in self.window.winfo_children():
            widget.destroy()
        
        header = tk.Frame(self.window, bg='#171a21', height=50)
        header.pack(fill='x')
        header.pack_propagate(False)
        
        menu_frame = tk.Frame(header, bg='#171a21')
        menu_frame.pack(side='left', padx=10)
        for menu in ["Магазин", "Библиотека", "Сообщество", "Профиль"]:
            tk.Button(menu_frame, text=menu, font=('Arial', 10), bg='#171a21', fg='#b8b6b4', bd=0, cursor='hand2',
                     command=lambda m=menu: self.menu_click(m)).pack(side='left', padx=10)
        
        user_frame = tk.Frame(header, bg='#171a21')
        user_frame.pack(side='right', padx=10)
        tk.Label(user_frame, text=f"👤 {self.user_data['username']}", font=('Arial', 10), bg='#171a21', fg='white').pack(side='left', padx=5)
        tk.Label(user_frame, text=f"ID: {self.user_data['steam_id']}", font=('Arial', 9), bg='#171a21', fg='#8f98a0').pack(side='left', padx=5)
        tk.Button(user_frame, text="Выйти", font=('Arial', 9), bg='#5c7e10', fg='white', cursor='hand2', bd=0,
                 command=self.logout).pack(side='left', padx=5)
        
        self.content_frame = tk.Frame(self.window, bg='#1b2838')
        self.content_frame.pack(fill='both', expand=True)
        self.show_store()

    def menu_click(self, menu):
        if menu == "Магазин": self.show_store()
        elif menu == "Библиотека": self.show_library()
        elif menu == "Сообщество": self.show_community()
        elif menu == "Профиль": self.show_profile()

    def show_store(self):
        self.clear_content()
        banner_frame = tk.Frame(self.content_frame, bg='#2a475e', height=200)
        banner_frame.pack(fill='x')
        banner_frame.pack_propagate(False)
        tk.Label(banner_frame, text="🚀 ДОБРО ПОЖАЛОВАТЬ В STEAM", font=('Arial', 24, 'bold'), bg='#2a475e', fg='white').pack(expand=True)
        tk.Label(banner_frame, text=f"Привет, {self.user_data['username']}!", font=('Arial', 14), bg='#2a475e', fg='#66c0f4').pack()
        
        content = tk.Frame(self.content_frame, bg='#1b2838')
        content.pack(fill='both', expand=True, padx=20, pady=20)
        tk.Label(content, text="🔥 ПОПУЛЯРНЫЕ СЕЙЧАС", font=('Arial', 18, 'bold'), bg='#1b2838', fg='white').pack(anchor='w', pady=10)
        
        games = [
            {"name": "Counter-Strike 2", "price": "Бесплатно", "players": "845,321 онлайн", "discount": 0},
            {"name": "Dota 2", "price": "Бесплатно", "players": "712,654 онлайн", "discount": 0},
            {"name": "Apex Legends", "price": "Бесплатно", "players": "543,210 онлайн", "discount": 0},
            {"name": "Baldur's Gate 3", "price": "2 999 ₽", "players": "98,765 онлайн", "discount": 10},
            {"name": "Cyberpunk 2077", "price": "1 999 ₽", "players": "45,678 онлайн", "discount": 50},
            {"name": "Elden Ring", "price": "3 499 ₽", "players": "67,890 онлайн", "discount": 20}
        ]
        
        games_frame = tk.Frame(content, bg='#1b2838')
        games_frame.pack(fill='both', expand=True)
        for i, game in enumerate(games):
            row, col = i // 3, i % 3
            game_card = tk.Frame(games_frame, bg='#2a475e', relief='flat', bd=1)
            game_card.grid(row=row, column=col, padx=10, pady=10, sticky='nsew')
            tk.Label(game_card, text="🎮", font=('Arial', 32), bg='#2a475e', fg='white', width=10, height=4).pack(pady=10)
            tk.Label(game_card, text=game['name'], font=('Arial', 12, 'bold'), bg='#2a475e', fg='white', wraplength=200).pack(pady=5)
            tk.Label(game_card, text=game['players'], font=('Arial', 9), bg='#2a475e', fg='#66c0f4').pack()
            price_frame = tk.Frame(game_card, bg='#2a475e')
            price_frame.pack(fill='x', pady=10, padx=10)
            tk.Label(price_frame, text=game['price'], font=('Arial', 11, 'bold'), bg='#2a475e', fg='#a4d007').pack(side='left')
            btn_text = "Установить" if game['price'] == "Бесплатно" else "Купить"
            tk.Button(game_card, text=btn_text, font=('Arial', 10), bg='#5c7e10', fg='white', cursor='hand2', bd=0).pack(pady=10)
        
        for i in range(3): games_frame.columnconfigure(i, weight=1)
        for i in range(2): games_frame.rowconfigure(i, weight=1)

    def show_library(self):
        self.clear_content()
        content = tk.Frame(self.content_frame, bg='#1b2838')
        content.pack(fill='both', expand=True, padx=20, pady=20)
        tk.Label(content, text="🎮 МОЯ БИБЛИОТЕКА", font=('Arial', 18, 'bold'), bg='#1b2838', fg='white').pack(anchor='w', pady=10)
        
        for game in self.user_data['games']:
            game_frame = tk.Frame(content, bg='#2a475e', relief='flat', bd=1)
            game_frame.pack(fill='x', pady=5, padx=10)
            info_frame = tk.Frame(game_frame, bg='#2a475e')
            info_frame.pack(fill='x', padx=15, pady=10)
            tk.Label(info_frame, text="🎮", font=('Arial', 24), bg='#2a475e').pack(side='left', padx=10)
            text_frame = tk.Frame(info_frame, bg='#2a475e')
            text_frame.pack(side='left', fill='x', expand=True)
            tk.Label(text_frame, text=game['name'], font=('Arial', 12, 'bold'), bg='#2a475e', fg='white', anchor='w').pack(fill='x')
            tk.Label(text_frame, text=f"Время в игре: {game['playtime']}", font=('Arial', 10), bg='#2a475e', fg='#66c0f4', anchor='w').pack(fill='x')
            if game['installed']:
                tk.Button(info_frame, text="▶ ИГРАТЬ", font=('Arial', 11), bg='#5c7e10', fg='white', cursor='hand2', bd=0).pack(side='right', padx=10)
            else:
                tk.Button(info_frame, text="УСТАНОВИТЬ", font=('Arial', 11), bg='#4c6b22', fg='white', cursor='hand2', bd=0).pack(side='right', padx=10)

    def show_community(self):
        self.clear_content()
        content = tk.Frame(self.content_frame, bg='#1b2838')
        content.pack(fill='both', expand=True, padx=20, pady=20)
        tk.Label(content, text="👥 СООБЩЕСТВО", font=('Arial', 18, 'bold'), bg='#1b2838', fg='white').pack(anchor='w', pady=10)
        
        friends_frame = tk.Frame(content, bg='#2a475e')
        friends_frame.pack(fill='x', pady=10, padx=10)
        tk.Label(friends_frame, text="Друзья", font=('Arial', 14, 'bold'), bg='#2a475e', fg='white').pack(anchor='w', padx=10, pady=10)
        
        for friend in self.user_data['friends']:
            friend_frame = tk.Frame(friends_frame, bg='#2a475e')
            friend_frame.pack(fill='x', padx=10, pady=5)
            status_color = {'В сети': '#90ba3c', 'Не в сети': '#666666', 'Занят': '#a34f25'}.get(friend['status'], '#666666')
            tk.Label(friend_frame, text="●", font=('Arial', 12), bg='#2a475e', fg=status_color).pack(side='left', padx=5)
            tk.Label(friend_frame, text=friend['name'], font=('Arial', 11), bg='#2a475e', fg='white').pack(side='left', padx=5)
            if friend['game']:
                tk.Label(friend_frame, text=f"Играет в {friend['game']}", font=('Arial', 10), bg='#2a475e', fg='#66c0f4').pack(side='right', padx=5)

    def show_profile(self):
        self.clear_content()
        content = tk.Frame(self.content_frame, bg='#1b2838')
        content.pack(fill='both', expand=True, padx=20, pady=20)
        profile_frame = tk.Frame(content, bg='#2a475e')
        profile_frame.pack(fill='x', pady=10, padx=10)
        tk.Label(profile_frame, text="👤", font=('Arial', 48), bg='#2a475e').pack(side='left', padx=20, pady=20)
        info_frame = tk.Frame(profile_frame, bg='#2a475e')
        info_frame.pack(side='left', fill='y', pady=20)
        tk.Label(info_frame, text=self.user_data['username'], font=('Arial', 18, 'bold'), bg='#2a475e', fg='white').pack(anchor='w')
        tk.Label(info_frame, text=f"Steam ID: {self.user_data['steam_id']}", font=('Arial', 12), bg='#2a475e', fg='#66c0f4').pack(anchor='w')
        tk.Label(info_frame, text="Участник Steam", font=('Arial', 12), bg='#2a475e', fg='#8f98a0').pack(anchor='w')
        
        stats_frame = tk.Frame(content, bg='#2a475e')
        stats_frame.pack(fill='x', pady=10, padx=10)
        stats = [
            ("🎮 Игр в библиотеке", len(self.user_data['games'])),
            ("👥 Друзей", len(self.user_data['friends'])),
            ("⭐ Уровень аккаунта", "1"),
            ("📅 На Steam с", "2024")
        ]
        for label, value in stats:
            stat_frame = tk.Frame(stats_frame, bg='#2a475e')
            stat_frame.pack(side='left', expand=True, pady=10)
            tk.Label(stat_frame, text=value, font=('Arial', 16, 'bold'), bg='#2a475e', fg='white').pack()
            tk.Label(stat_frame, text=label, font=('Arial', 10), bg='#2a475e', fg='#66c0f4').pack()

    def clear_content(self):
        for widget in self.content_frame.winfo_children():
            widget.destroy()

    def logout(self):
        self.user_data['logged_in'] = False
        self.show_login_screen()

# ==================== WINDOWS 12 ====================
class Windows12:
    def __init__(self, root):
        self.root = root
        self.root.title("Windows 12 Simulator")
        self.hide_taskbar()
        self.root.attributes('-fullscreen', True)
        self.root.configure(bg='#000000')
        
        self.colors = {
            'primary': '#0078d4', 'primary_light': '#4ca6e8', 'primary_dark': '#005a9e',
            'dark_bg': '#0f0f0f', 'darker_bg': '#1a1a1a', 'taskbar': '#2d2d2d', 
            'taskbar_hover': '#3c3c3c', 'accent': '#005fb8', 'text': '#ffffff', 
            'text_secondary': '#a0a0a0', 'gradient_start': '#0a0a2a', 'gradient_mid': '#1a1a4a', 
            'gradient_end': '#2a2a6a', 'card_bg': '#2d2d2d', 'success': '#107c10', 'danger': '#e74856'
        }
        
        self.recycle_bin = Utils.load_data('recycle_bin.json', [])
        self.screenshots = Utils.load_data('screenshots.json', [])
        self.desktop_items = Utils.load_data('desktop_items.json', [
            {"type": "app", "name": "Браузер", "icon": "🌐", "color": "#0078d4", "x": 100, "y": 100},
            {"type": "app", "name": "Проводник", "icon": "📁", "color": "#4ca6e8", "x": 240, "y": 100},
            {"type": "app", "name": "Параметры", "icon": "⚙️", "color": "#cccccc", "x": 380, "y": 100},
            {"type": "app", "name": "Фотографии", "icon": "🖼️", "color": "#e74856", "x": 520, "y": 100},
            {"type": "app", "name": "Корзина", "icon": "🗑️", "color": "#ffb900", "x": 100, "y": 240},
            {"type": "app", "name": "Steam", "icon": "🎮", "color": "#1b2838", "x": 240, "y": 240}
        ])
        self.folders = Utils.load_data('folders.json', {})
        self.files = Utils.load_data('files.json', {})
        self.open_windows = []
        self.backgrounds = [
            {'name': 'Градиент космос', 'type': 'gradient'},
            {'name': 'Синий кристалл', 'type': 'color', 'color': '#001f3f'},
            {'name': 'Темная сталь', 'type': 'color', 'color': '#2d2d2d'},
            {'name': 'Изумрудный', 'type': 'color', 'color': '#004225'}
        ]
        self.current_background = 0
        self.dragging_item = None
        self.drag_start_x = 0
        self.drag_start_y = 0
        self.drop_target = None
        self.win_r_visible = False
        
        self.setup_styles()
        self.create_ui()
        self.setup_bindings()

    def hide_taskbar(self):
        try:
            taskbar = ctypes.windll.user32.FindWindowW("Shell_TrayWnd", None)
            ctypes.windll.user32.ShowWindow(taskbar, 0)
            start_button = ctypes.windll.user32.FindWindowW("Button", None)
            if start_button: ctypes.windll.user32.ShowWindow(start_button, 0)
        except: pass

    def show_taskbar(self):
        try:
            taskbar = ctypes.windll.user32.FindWindowW("Shell_TrayWnd", None)
            if taskbar: ctypes.windll.user32.ShowWindow(taskbar, 1)
            import subprocess
            subprocess.run('cmd /c taskkill /f /im explorer.exe && start explorer.exe', shell=True, capture_output=True)
        except: 
            try:
                import os
                os.system("cmd /c taskkill /f /im explorer.exe")
                os.system("start explorer.exe")
            except: pass

    def toggle_fullscreen(self, event=None):
        if self.root.attributes('-fullscreen'):
            self.root.attributes('-fullscreen', False)
            self.show_taskbar()
        else:
            self.root.attributes('-fullscreen', True)
            self.hide_taskbar()

    def exit_fullscreen(self, event=None):
        self.root.attributes('-fullscreen', False)
        self.show_taskbar()

    def on_close(self):
        self.root.after(100, self._force_restore_taskbar)

    def _force_restore_taskbar(self):
        try:
            import subprocess
            subprocess.run('cmd /c taskkill /f /im explorer.exe && timeout 1 && start explorer.exe', shell=True, capture_output=True)
        except: pass
        finally: self.root.quit(); self.root.destroy()

    def setup_styles(self):
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.style.configure('Modern.TFrame', background=self.colors['dark_bg'])
        self.style.configure('Taskbar.TFrame', background=self.colors['taskbar'])
        self.style.configure('StartMenu.TFrame', background=self.colors['darker_bg'])
        self.style.configure('Card.TFrame', background=self.colors['card_bg'])

    def create_ui(self):
        self.main_container = ttk.Frame(self.root, style='Modern.TFrame')
        self.main_container.pack(fill='both', expand=True)
        self.setup_desktop()
        self.setup_taskbar()
        self.start_menu_visible = False
        self.start_menu = None

    def setup_desktop(self):
        self.desktop = tk.Canvas(self.main_container, bg=self.colors['dark_bg'], highlightthickness=0, cursor='arrow')
        self.desktop.pack(fill='both', expand=True)
        self.create_modern_background()
        self.create_desktop_icons()

    def create_modern_background(self):
        width = self.root.winfo_screenwidth()
        height = self.root.winfo_screenheight()
        background = self.backgrounds[self.current_background]
        
        if background['type'] == 'gradient':
            steps = 200
            for i in range(steps):
                ratio = i / steps
                if ratio < 0.33: r1, g1, b1 = Utils.hex_to_rgb(self.colors['gradient_start']); r2, g2, b2 = Utils.hex_to_rgb(self.colors['gradient_mid']); local_ratio = ratio * 3
                elif ratio < 0.66: r1, g1, b1 = Utils.hex_to_rgb(self.colors['gradient_mid']); r2, g2, b2 = Utils.hex_to_rgb(self.colors['gradient_end']); local_ratio = (ratio - 0.33) * 3
                else: r1, g1, b1 = Utils.hex_to_rgb(self.colors['gradient_end']); r2, g2, b2 = Utils.hex_to_rgb(self.colors['gradient_start']); local_ratio = (ratio - 0.66) * 3
                
                r = int(r1 + (r2 - r1) * local_ratio); g = int(g1 + (g2 - g1) * local_ratio); b = int(b1 + (b2 - b1) * local_ratio)
                color = f'#{r:02x}{g:02x}{b:02x}'
                y_start = int(height * ratio); y_end = int(height * (ratio + 1/steps))
                self.desktop.create_rectangle(0, y_start, width, y_end, fill=color, outline='')
            
            self.create_background_elements()
        else: self.desktop.configure(bg=background['color'])
        
    def create_background_elements(self):
        width = self.root.winfo_screenwidth(); height = self.root.winfo_screenheight()
        for i in range(0, width, 80): self.desktop.create_line(i, 0, i, height, fill='#1a1a2a', width=0.5, dash=(2, 4))
        for i in range(0, height, 80): self.desktop.create_line(0, i, width, i, fill='#1a1a2a', width=0.5, dash=(2, 4))
        for _ in range(12):
            x = random.randint(-100, width + 100); y = random.randint(-100, height + 100); size = random.randint(120, 300)
            for j in range(size, 0, -10):
                ratio = j / size
                r = int(26 + (42 - 26) * ratio); g = int(42 + (82 - 42) * ratio); b = int(96 + (152 - 96) * ratio)
                color = f'#{r:02x}{g:02x}{b:02x}'
                self.desktop.create_oval(x + (size-j)//2, y + (size-j)//2, x + (size+j)//2, y + (size+j)//2, fill=color, outline='', width=0)

    def create_desktop_icons(self):
        for item in self.desktop_items: self.create_desktop_icon(item)

    def create_desktop_icon(self, item):
        icon_card = tk.Frame(self.desktop, bg=self.colors['card_bg'], relief='flat', bd=0)
        icon_card.item_data = item
        window_id = self.desktop.create_window(item['x'], item['y'], window=icon_card)
        
        icon_btn = tk.Button(icon_card, text=item['icon'], font=('Segoe UI', 24), bg=self.colors['card_bg'], fg=item['color'], 
                           bd=0, cursor='hand2', command=lambda: self.open_desktop_item(item['name'], item['type']))
        icon_btn.pack(pady=(10, 5))
        
        icon_label = tk.Label(icon_card, text=item['name'], bg=self.colors['card_bg'], fg=self.colors['text'], font=('Segoe UI', 9), cursor='hand2')
        icon_label.pack(pady=(0, 10))
        icon_label.bind('<Double-Button-1>', lambda e: self.open_desktop_item(item['name'], item['type']))
        
        context_menu = self.create_context_menu(item)
        for widget in [icon_btn, icon_label, icon_card]:
            widget.bind('<Button-3>', lambda e: context_menu.tk_popup(e.x_root, e.y_root))
        
        self.bind_drag_events(icon_card, window_id)

    def bind_drag_events(self, icon_card, window_id):
        for widget in [icon_card] + list(icon_card.winfo_children()):
            widget.bind('<Button-1>', lambda e: self.start_drag(e, icon_card, window_id))
            widget.bind('<B1-Motion>', lambda e: self.do_drag(e, icon_card, window_id))
            widget.bind('<ButtonRelease-1>', lambda e: self.stop_drag(e, icon_card))

    def create_context_menu(self, item):
        context_menu = tk.Menu(self.root, tearoff=0, bg='#2d2d2d', fg='white')
        context_menu.add_command(label="Открыть", command=lambda: self.open_desktop_item(item['name'], item['type']))
        if item['type'] in ['folder', 'file']:
            context_menu.add_command(label="Переименовать", command=lambda: self.rename_item(item['name'], item['type']))
            context_menu.add_command(label="Удалить", command=lambda: self.delete_desktop_item(item['name']))
        context_menu.add_separator()
        context_menu.add_command(label="Создать папку", command=self.create_new_folder)
        context_menu.add_command(label="Создать текстовый файл", command=self.create_text_file)
        return context_menu

    def start_drag(self, event, icon_card, window_id):
        self.dragging_item = (icon_card, window_id)
        self.drag_start_x = event.x_root; self.drag_start_y = event.y_root
        self.desktop.tag_raise(window_id)

    def do_drag(self, event, icon_card, window_id):
        if self.dragging_item:
            dx = event.x_root - self.drag_start_x; dy = event.y_root - self.drag_start_y
            current_x, current_y = self.desktop.coords(window_id)
            new_x = current_x + dx; new_y = current_y + dy
            self.desktop.coords(window_id, new_x, new_y)
            self.drag_start_x = event.x_root; self.drag_start_y = event.y_root
            item_data = icon_card.item_data; item_data['x'] = new_x; item_data['y'] = new_y
            self.check_drop_target(new_x, new_y, item_data)

    def check_drop_target(self, x, y, dragged_item):
        if self.drop_target: self.highlight_drop_target(self.drop_target, False); self.drop_target = None
        for item in self.desktop_items:
            if item['type'] == 'folder' and dragged_item['type'] in ['file']:
                item_x, item_y = item['x'], item['y']
                if (abs(x - item_x) < 50 and abs(y - item_y) < 50):
                    self.drop_target = item; self.highlight_drop_target(item, True); break

    def highlight_drop_target(self, item, highlight):
        for window_id in self.desktop.find_withtag("window"):
            coords = self.desktop.coords(window_id)
            if len(coords) >= 2:
                window_x, window_y = coords[0], coords[1]
                if abs(window_x - item['x']) < 5 and abs(window_y - item['y']) < 5:
                    if highlight: self.desktop.itemconfig(window_id, outline='#0078d4', width=3)
                    else: self.desktop.itemconfig(window_id, outline='', width=1)
                    break

    def stop_drag(self, event, icon_card):
        item_data = icon_card.item_data
        if self.drop_target and item_data['type'] in ['file']:
            self.move_to_folder(item_data['name'], item_data['type'], self.drop_target['name'])
        if self.drop_target: self.highlight_drop_target(self.drop_target, False); self.drop_target = None
        self.dragging_item = None
        Utils.save_data('desktop_items.json', self.desktop_items)

    def open_desktop_item(self, name, item_type):
        if item_type == 'app': self.open_app(name)
        elif item_type == 'folder': self.open_folder(name)
        elif item_type == 'file': self.open_file(name)

    def create_new_folder(self):
        folder_name = f"Новая папка ({len([x for x in self.desktop_items if x['type'] == 'folder']) + 1})"
        new_folder = {"type": "folder", "name": folder_name, "icon": "📁", "color": "#ffb900",
                     "x": random.randint(100, 800), "y": random.randint(100, 500), "content": []}
        self.desktop_items.append(new_folder); self.folders[folder_name] = new_folder
        Utils.save_data('desktop_items.json', self.desktop_items); Utils.save_data('folders.json', self.folders)
        self.create_desktop_icon(new_folder)
        messagebox.showinfo("Создание папки", f"Папка '{folder_name}' создана на рабочем столе!")

    def create_text_file(self):
        file_name = f"Новый текстовый документ ({len([x for x in self.desktop_items if x['type'] == 'file']) + 1}).txt"
        new_file = {"type": "file", "name": file_name, "icon": "📄", "color": "#0078d4",
                   "x": random.randint(100, 800), "y": random.randint(100, 500), "content": "",
                   "created_date": datetime.now().strftime("%d.%m.%Y %H:%M"), "location": "desktop"}
        self.desktop_items.append(new_file); self.files[file_name] = new_file
        Utils.save_data('desktop_items.json', self.desktop_items); Utils.save_data('files.json', self.files)
        self.create_desktop_icon(new_file)
        messagebox.showinfo("Создание файла", f"Файл '{file_name}' создан на рабочем столе!")

    def rename_item(self, old_name, item_type):
        new_name = simpledialog.askstring("Переименование", f"Введите новое название для {old_name}:", initialvalue=old_name)
        if new_name and new_name != old_name:
            for item in self.desktop_items:
                if item['name'] == old_name and item['type'] == item_type: item['name'] = new_name; break
            if item_type == 'file' and old_name in self.files: self.files[new_name] = self.files.pop(old_name); self.files[new_name]['name'] = new_name
            if item_type == 'folder' and old_name in self.folders: 
                self.folders[new_name] = self.folders.pop(old_name); self.folders[new_name]['name'] = new_name
                for file_name, file_data in self.files.items():
                    if file_data.get('location') == old_name: file_data['location'] = new_name
            Utils.save_data('desktop_items.json', self.desktop_items); Utils.save_data('files.json', self.files); Utils.save_data('folders.json', self.folders)
            self.refresh_desktop()
            messagebox.showinfo("Переименование", f"Успешно переименовано в '{new_name}'")

    def move_to_folder(self, item_name, item_type, folder_name):
        item_to_move = next((item for item in self.desktop_items if item['name'] == item_name and item['type'] == item_type), None)
        if item_to_move and folder_name in self.folders:
            self.desktop_items = [item for item in self.desktop_items if not (item['name'] == item_name and item['type'] == item_type)]
            if item_name not in self.folders[folder_name]['content']: self.folders[folder_name]['content'].append({'name': item_name, 'type': item_type})
            if item_type == 'file' and item_name in self.files: self.files[item_name]['location'] = folder_name
            Utils.save_data('desktop_items.json', self.desktop_items); Utils.save_data('folders.json', self.folders); Utils.save_data('files.json', self.files)
            self.refresh_desktop()
            messagebox.showinfo("Перемещение", f"{item_name} перемещен в папку '{folder_name}'")

    def delete_desktop_item(self, name):
        item = next((x for x in self.desktop_items if x['name'] == name and x['type'] == 'folder'), None)
        if item:
            if name in self.folders: del self.folders[name]
            self.desktop_items.remove(item)
            Utils.save_data('desktop_items.json', self.desktop_items); Utils.save_data('folders.json', self.folders)
            self.refresh_desktop()
            messagebox.showinfo("Удаление", f"Папка '{name}' удалена!")

    def delete_file(self, name):
        item = next((x for x in self.desktop_items if x['name'] == name and x['type'] == 'file'), None)
        if item:
            self.desktop_items.remove(item)
            if name in self.files: del self.files[name]
            Utils.save_data('desktop_items.json', self.desktop_items); Utils.save_data('files.json', self.files)
            self.refresh_desktop()
            messagebox.showinfo("Удаление", f"Файл '{name}' удален!")

    def open_folder(self, name):
        if name in self.folders:
            folder_data = self.folders[name]
            folder_window = FolderWindow(self.root, self, folder_data)
            self.add_window_to_taskbar(folder_window.window, name)
        else: messagebox.showerror("Ошибка", f"Папка {name} не найдена!")

    def open_file(self, name):
        if name in self.files:
            file_data = self.files[name]
            text_editor = TextEditor(self.root, self, file_data)
            self.add_window_to_taskbar(text_editor.window, name)
        else: messagebox.showerror("Ошибка", f"Файл {name} не найден!")

    def setup_taskbar(self):
        self.taskbar = tk.Frame(self.main_container, bg=self.colors['taskbar'], height=52)
        self.taskbar.pack(side='bottom', fill='x'); self.taskbar.pack_propagate(False)
        
        start_btn = tk.Button(self.taskbar, text="⊞", font=('Segoe UI', 16, 'bold'), bg=self.colors['taskbar'], fg=self.colors['text'],
                            bd=0, cursor='hand2', width=3, command=self.toggle_start_menu)
        start_btn.pack(side='left', padx=8)
        
        self.windows_frame = tk.Frame(self.taskbar, bg=self.colors['taskbar'])
        self.windows_frame.pack(side='left', fill='x', expand=True, padx=10)
        
        right_frame = tk.Frame(self.taskbar, bg=self.colors['taskbar'])
        right_frame.pack(side='right', padx=20)
        self.time_label = tk.Label(right_frame, font=('Segoe UI', 10), bg=self.colors['taskbar'], fg=self.colors['text'])
        self.time_label.pack(side='right', padx=10); self.update_time()
        self.update_taskbar_windows()

    def update_taskbar_windows(self):
        for widget in self.windows_frame.winfo_children(): widget.destroy()
        for i, window_info in enumerate(self.open_windows):
            if i >= 8: break
            tk.Button(self.windows_frame, text=window_info['name'], font=('Segoe UI', 9), bg=self.colors['taskbar'], fg=self.colors['text'],
                     bd=0, cursor='hand2', activebackground=self.colors['taskbar_hover'],
                     command=lambda w=window_info: self.focus_window(w)).pack(side='left', padx=2)

    def add_window_to_taskbar(self, window, name):
        window_info = {'window': window, 'name': name}
        for existing in self.open_windows:
            if existing['window'] == window: return
        self.open_windows.append(window_info); self.update_taskbar_windows()
        def on_close():
            if window_info in self.open_windows: self.open_windows.remove(window_info); self.update_taskbar_windows()
            window.destroy()
        window.protocol("WM_DELETE_WINDOW", on_close)
        window.bind('<Map>', lambda e: self.update_taskbar_windows())
        window.bind('<Unmap>', lambda e: self.update_taskbar_windows())

    def focus_window(self, window_info):
        try:
            window = window_info['window']
            if window.state() == 'iconic': window.deiconify()
            window.focus_set(); window.lift()
        except:
            if window_info in self.open_windows: self.open_windows.remove(window_info); self.update_taskbar_windows()

    def toggle_start_menu(self):
        if self.start_menu_visible: self.hide_start_menu()
        else: self.show_start_menu()

    def show_start_menu(self):
        if self.start_menu: self.start_menu.destroy()
        self.start_menu = tk.Frame(self.main_container, bg=self.colors['darker_bg'], width=480, height=680)
        self.start_menu.place(x=60, y=self.root.winfo_screenheight() - 740)
        
        header_frame = tk.Frame(self.start_menu, bg=self.colors['primary_dark'], height=80)
        header_frame.pack(fill='x'); header_frame.pack_propagate(False)
        tk.Label(header_frame, text="Windows 12", font=('Segoe UI', 20, 'bold'), bg=self.colors['primary_dark'], fg='white').pack(expand=True)
        
        search_frame = tk.Frame(self.start_menu, bg=self.colors['darker_bg'])
        search_frame.pack(fill='x', padx=25, pady=20)
        search_entry = tk.Entry(search_frame, font=('Segoe UI', 11), bg=self.colors['card_bg'], fg=self.colors['text'],
                              insertbackground=self.colors['text'], relief='flat', bd=0)
        search_entry.insert(0, "🔍 Поиск в Windows"); search_entry.pack(fill='x', ipady=10)
        
        apps_frame = tk.Frame(self.start_menu, bg=self.colors['darker_bg'])
        apps_frame.pack(fill='both', expand=True, padx=25, pady=10)
        start_menu_items = [item for item in self.desktop_items if item['type'] in ['app', 'folder', 'file']]
        
        for i, item in enumerate(start_menu_items):
            row, col = i // 4, i % 4
            app_card = tk.Frame(apps_frame, bg=self.colors['card_bg'], relief='flat', bd=0)
            app_card.grid(row=row, column=col, padx=8, pady=8, sticky='nsew')
            tk.Button(app_card, text=f"{item['icon']}\n{item['name']}", font=('Segoe UI', 9), justify='center',
                     bg=self.colors['card_bg'], fg=self.colors['text'], bd=0, cursor='hand2', activebackground='#3c3c3c',
                     command=lambda n=item['name'], t=item['type']: self.open_desktop_item(n, t)).pack(fill='both', expand=True, padx=10, pady=10)
        
        for i in range(4): apps_frame.columnconfigure(i, weight=1)
        rows_needed = (len(start_menu_items) + 3) // 4
        for i in range(rows_needed): apps_frame.rowconfigure(i, weight=1)
        self.start_menu_visible = True

    def hide_start_menu(self):
        if self.start_menu: self.start_menu.destroy(); self.start_menu = None
        self.start_menu_visible = False

    def open_app(self, app_name):
        self.hide_start_menu()
        if app_name == "Браузер": browser = ModernBrowserWindow(self.root, self); self.add_window_to_taskbar(browser.window, "Браузер")
        elif app_name == "Проводник": explorer = ModernFileExplorer(self.root, self); self.add_window_to_taskbar(explorer.window, "Проводник")
        elif app_name == "Фотографии": photos = PhotosApp(self.root, self); self.add_window_to_taskbar(photos.window, "Фотографии")
        elif app_name == "Корзина": recycle_bin = RecycleBinApp(self.root, self); self.add_window_to_taskbar(recycle_bin.window, "Корзина")
        elif app_name == "Параметры": settings = SettingsApp(self.root, self); self.add_window_to_taskbar(settings.window, "Параметры")
        elif app_name == "Steam": steam = RealSteamApp(self.root, self); self.add_window_to_taskbar(steam.window, "Steam")
        else: messagebox.showinfo(app_name, f"Приложение {app_name} запущено!")

    def change_background(self, background_index):
        self.current_background = background_index; self.refresh_desktop()

    def update_time(self):
        current_time = datetime.now().strftime("%H:%M\n%d.%m.%Y")
        self.time_label.configure(text=current_time); self.root.after(1000, self.update_time)

    def setup_bindings(self):
        self.root.bind('<Button-1>', self.hide_menus_on_click)
        self.root.bind('<Super_L>', lambda e: self.toggle_start_menu())
        self.root.bind('<Print>', lambda e: self.take_screenshot())
        self.root.bind('<Control-R>', lambda e: self.toggle_win_r())
        self.root.bind('<Control-r>', lambda e: self.toggle_win_r())
        self.desktop.bind('<Button-3>', self.show_desktop_context_menu)

    def toggle_win_r(self):
        if self.win_r_visible: self.hide_win_r()
        else: self.show_win_r()

    def show_win_r(self):
        if hasattr(self, 'win_r_window') and self.win_r_window: self.win_r_window.destroy()
        self.win_r_window = tk.Toplevel(self.root); self.win_r_window.title("Выполнить"); self.win_r_window.overrideredirect(True)
        self.win_r_window.configure(bg='#2d2d2d')
        width, height = 400, 180; screen_width = self.root.winfo_screenwidth(); screen_height = self.root.winfo_screenheight()
        x = (screen_width - width) // 2; y = (screen_height - height) // 3; self.win_r_window.geometry(f"{width}x{height}+{x}+{y}")
        
        main_frame = tk.Frame(self.win_r_window, bg='#2d2d2d', bd=0); main_frame.pack(fill='both', expand=True, padx=1, pady=1)
        header_frame = tk.Frame(main_frame, bg='#1a1a1a', height=40); header_frame.pack(fill='x', padx=10, pady=(10, 5)); header_frame.pack_propagate(False)
        tk.Label(header_frame, text="Выполнить", font=('Segoe UI', 11, 'bold'), bg='#1a1a1a', fg='white').pack(side='left', padx=15, pady=10)
        tk.Button(header_frame, text="×", font=('Arial', 14), bg='#1a1a1a', fg='white', bd=0, cursor='hand2', command=self.hide_win_r).pack(side='right', padx=10)
        
        content_frame = tk.Frame(main_frame, bg='#2d2d2d'); content_frame.pack(fill='both', expand=True, padx=20, pady=10)
        tk.Label(content_frame, text="Введите имя программы, папки, документа или ресурса\nИнтернета, которые следует открыть.",
                font=('Segoe UI', 9), bg='#2d2d2d', fg='#cccccc', justify='left').pack(anchor='w', pady=(0, 10))
        tk.Label(content_frame, text="Открыть:", font=('Segoe UI', 9), bg='#2d2d2d', fg='white').pack(anchor='w')
        
        input_frame = tk.Frame(content_frame, bg='#1a1a1a', relief='solid', bd=1); input_frame.pack(fill='x', pady=5)
        self.win_r_entry = tk.Entry(input_frame, font=('Segoe UI', 10), bg='#1a1a1a', fg='white', insertbackground='white', relief='flat', bd=0)
        self.win_r_entry.pack(fill='x', padx=10, pady=8); self.win_r_entry.focus_set(); self.win_r_entry.bind('<Return>', self.execute_win_r_command)
        
        buttons_frame = tk.Frame(content_frame, bg='#2d2d2d'); buttons_frame.pack(fill='x', pady=10)
        tk.Button(buttons_frame, text="ОК", font=('Segoe UI', 9), bg='#0078d4', fg='white', bd=0, cursor='hand2', padx=20,
                 command=self.execute_win_r_command).pack(side='right', padx=5)
        tk.Button(buttons_frame, text="Отмена", font=('Segoe UI', 9), bg='#5c5c5c', fg='white', bd=0, cursor='hand2', padx=15,
                 command=self.hide_win_r).pack(side='right', padx=5)
        tk.Button(buttons_frame, text="Обзор...", font=('Segoe UI', 9), bg='#5c5c5c', fg='white', bd=0, cursor='hand2', padx=15,
                 command=self.browse_files).pack(side='right', padx=5)
        self.win_r_visible = True
        self.win_r_window.bind('<FocusOut>', lambda e: self.win_r_window.after(100, self.check_focus))

    def check_focus(self):
        if (self.win_r_visible and hasattr(self, 'win_r_window') and self.win_r_window and not self.win_r_window.focus_get()):
            self.hide_win_r()

    def hide_win_r(self):
        if hasattr(self, 'win_r_window') and self.win_r_window: self.win_r_window.destroy(); self.win_r_window = None
        self.win_r_visible = False

    def execute_win_r_command(self, event=None):
        command = self.win_r_entry.get().strip(); self.hide_win_r()
        commands = {'cmd': 'Командная строка', 'notepad': 'Блокнот', 'calc': 'Калькулятор', 'explorer': 'Проводник',
                   'browser': 'Браузер', 'steam': 'Steam', 'photos': 'Фотографии', 'settings': 'Параметры'}
        if command in commands: self.open_app(commands[command])
        elif command.startswith('http://') or command.startswith('https://'): webbrowser.open(command)
        else: messagebox.showinfo("Выполнить", f"Выполняется команда: {command}")

    def browse_files(self): self.hide_win_r(); self.open_app("Проводник")

    def show_desktop_context_menu(self, event):
        context_menu = tk.Menu(self.root, tearoff=0, bg='#2d2d2d', fg='white')
        context_menu.add_command(label="Создать папку", command=self.create_new_folder)
        context_menu.add_command(label="Создать текстовый файл", command=self.create_text_file)
        context_menu.add_separator()
        context_menu.add_command(label="Обновить", command=self.refresh_desktop)
        context_menu.add_command(label="Параметры", command=lambda: self.open_app("Параметры"))
        context_menu.add_command(label="Выполнить (Win+R)", command=self.show_win_r)
        context_menu.tk_popup(event.x_root, event.y_root)

    def hide_menus_on_click(self, event):
        if (self.start_menu_visible and self.start_menu and not self.start_menu.winfo_containing(event.x_root, event.y_root)):
            self.hide_start_menu()
        if (self.win_r_visible and hasattr(self, 'win_r_window') and self.win_r_window and not self.win_r_window.winfo_containing(event.x_root, event.y_root)):
            self.hide_win_r()

    def take_screenshot(self):
        try:
            x = self.root.winfo_rootx(); y = self.root.winfo_rooty(); width = self.root.winfo_width(); height = self.root.winfo_height()
            screenshot = ImageGrab.grab(bbox=(x, y, x + width, y + height))
            buffered = io.BytesIO(); screenshot.save(buffered, format="PNG")
            img_str = base64.b64encode(buffered.getvalue()).decode()
            screenshot_data = {'id': len(self.screenshots), 'data': img_str, 'date': datetime.now().strftime("%d.%m.%Y %H:%M"),
                             'name': f"Скриншот_{len(self.screenshots) + 1}.png"}
            self.screenshots.append(screenshot_data); Utils.save_data('screenshots.json', self.screenshots)
            messagebox.showinfo("Скриншот", "Скриншот сохранен в приложении 'Фотографии'!")
        except Exception as e: messagebox.showerror("Ошибка", f"Не удалось сделать скриншот: {str(e)}")

    def refresh_desktop(self):
        self.desktop.delete("all"); self.create_modern_background(); self.create_desktop_icons()

# ==================== ДОПОЛНИТЕЛЬНЫЕ ПРИЛОЖЕНИЯ ====================
class FolderWindow:
    def __init__(self, parent, windows_system, folder_data):
        self.window = tk.Toplevel(parent); self.windows_system = windows_system; self.folder_data = folder_data
        self.window.title(f"{folder_data['name']} - Проводник"); self.window.geometry("800x600"); self.window.configure(bg='#f3f3f3')
        self.setup_folder_ui()

    def setup_folder_ui(self):
        header = tk.Frame(self.window, bg='#ffffff', height=60); header.pack(fill='x'); header.pack_propagate(False)
        tk.Label(header, text=f"📁 {self.folder_data['name']}", font=('Segoe UI', 14, 'bold'), bg='#ffffff').pack(side='left', padx=20, pady=10)
        content = tk.Frame(self.window, bg='#f3f3f3'); content.pack(fill='both', expand=True, padx=20, pady=20)
        items_frame = tk.Frame(content, bg='#f3f3f3'); items_frame.pack(fill='both', expand=True)
        
        folder_items = []
        for item_ref in self.folder_data.get('content', []):
            if item_ref['type'] == 'file' and item_ref['name'] in self.windows_system.files:
                file_data = self.windows_system.files[item_ref['name']]
                folder_items.append({"type": "file", "name": file_data['name'], "icon": "📄", "color": "#0078d4"})
        
        if not folder_items:
            empty_frame = tk.Frame(content, bg='#f3f3f3'); empty_frame.place(relx=0.5, rely=0.5, anchor='center')
            tk.Label(empty_frame, text="📁", font=('Segoe UI', 64), bg='#f3f3f3', fg='#cccccc').pack(pady=10)
            tk.Label(empty_frame, text="Папка пуста", font=('Segoe UI', 16), bg='#f3f3f3').pack(pady=5)
            tk.Label(empty_frame, text="Перетащите сюда файлы с рабочего стола", font=('Segoe UI', 11), bg='#f3f3f3', fg='#666666').pack(pady=5)
        else:
            for i, item in enumerate(folder_items):
                row, col = i // 4, i % 4
                item_card = tk.Frame(items_frame, bg='white', relief='solid', bd=1); item_card.grid(row=row, column=col, padx=10, pady=10, sticky='nsew')
                tk.Label(item_card, text=item['icon'], font=('Segoe UI', 32), bg='white', fg=item['color']).pack(pady=(20, 10))
                tk.Label(item_card, text=item['name'], font=('Segoe UI', 10), bg='white', wraplength=120).pack(pady=(0, 15))
            for i in range(4): items_frame.columnconfigure(i, weight=1)
            for i in range(3): items_frame.rowconfigure(i, weight=1)

class TextEditor:
    def __init__(self, parent, windows_system, file_data):
        self.window = tk.Toplevel(parent); self.windows_system = windows_system; self.file_data = file_data
        self.window.title(f"{file_data['name']} - Блокнот"); self.window.geometry("800x600"); self.window.configure(bg='#f3f3f3')
        self.setup_editor_ui()

    def setup_editor_ui(self):
        header = tk.Frame(self.window, bg='#ffffff', height=60); header.pack(fill='x'); header.pack_propagate(False)
        tk.Label(header, text=f"📄 {self.file_data['name']}", font=('Segoe UI', 14, 'bold'), bg='#ffffff').pack(side='left', padx=20, pady=10)
        buttons_frame = tk.Frame(header, bg='#ffffff'); buttons_frame.pack(side='right', padx=20)
        tk.Button(buttons_frame, text="💾 Сохранить", font=('Segoe UI', 11), bg='#0078d4', fg='white', bd=0, cursor='hand2', padx=15,
                 command=self.save_file).pack(side='left', padx=5)
        tk.Button(buttons_frame, text="💾 Сохранить как", font=('Segoe UI', 11), bg='#107c10', fg='white', bd=0, cursor='hand2', padx=15,
                 command=self.save_file_as).pack(side='left', padx=5)
        
        text_frame = tk.Frame(self.window, bg='#ffffff'); text_frame.pack(fill='both', expand=True, padx=20, pady=20)
        self.text_area = scrolledtext.ScrolledText(text_frame, font=('Consolas', 12), bg='#ffffff', fg='#000000', wrap=tk.WORD)
        self.text_area.pack(fill='both', expand=True); self.text_area.insert('1.0', self.file_data.get('content', ''))

    def save_file(self):
        content = self.text_area.get('1.0', tk.END); self.file_data['content'] = content
        self.file_data['modified_date'] = datetime.now().strftime("%d.%m.%Y %H:%M")
        self.windows_system.files[self.file_data['name']] = self.file_data; Utils.save_data('files.json', self.windows_system.files)
        messagebox.showinfo("Сохранение", f"Файл '{self.file_data['name']}' сохранен!")

    def save_file_as(self):
        new_name = simpledialog.askstring("Сохранить как", "Введите новое название файла:", initialvalue=self.file_data['name'])
        if new_name:
            content = self.text_area.get('1.0', tk.END)
            new_file = {"type": "file", "name": new_name, "icon": "📄", "color": "#0078d4", "x": random.randint(100, 800), "y": random.randint(100, 500),
                       "content": content, "created_date": datetime.now().strftime("%d.%m.%Y %H:%M"), "location": "desktop"}
            self.windows_system.desktop_items.append(new_file); self.windows_system.files[new_name] = new_file
            Utils.save_data('desktop_items.json', self.windows_system.desktop_items); Utils.save_data('files.json', self.windows_system.files)
            self.windows_system.refresh_desktop()
            messagebox.showinfo("Сохранение", f"Файл сохранен как '{new_name}'!")

class SettingsApp:
    def __init__(self, parent, windows_system):
        self.window = tk.Toplevel(parent); self.windows_system = windows_system
        self.window.title("Параметры - Windows 12"); self.window.geometry("600x500"); self.window.configure(bg='#f3f3f3')
        self.setup_settings_ui()

    def setup_settings_ui(self):
        header = tk.Frame(self.window, bg='#ffffff', height=60); header.pack(fill='x'); header.pack_propagate(False)
        tk.Label(header, text="⚙️ Параметры", font=('Segoe UI', 16, 'bold'), bg='#ffffff').pack(side='left', padx=20)
        content = tk.Frame(self.window, bg='#f3f3f3'); content.pack(fill='both', expand=True, padx=20, pady=20)
        
        personalization_frame = tk.Frame(content, bg='white', relief='solid', bd=1); personalization_frame.pack(fill='x', pady=10)
        tk.Label(personalization_frame, text="🎨 Персонализация", font=('Segoe UI', 14, 'bold'), bg='white').pack(anchor='w', padx=15, pady=10)
        bg_frame = tk.Frame(personalization_frame, bg='white'); bg_frame.pack(fill='x', padx=15, pady=10)
        tk.Label(bg_frame, text="Фон рабочего стола", font=('Segoe UI', 12), bg='white').pack(anchor='w')
        backgrounds_frame = tk.Frame(bg_frame, bg='white'); backgrounds_frame.pack(fill='x', pady=10)
        for i, bg in enumerate(self.windows_system.backgrounds):
            tk.Button(backgrounds_frame, text=bg['name'], font=('Segoe UI', 10), bg='#0078d4', fg='white', bd=0, cursor='hand2', padx=15, pady=8,
                     command=lambda idx=i: self.windows_system.change_background(idx)).pack(side='left', padx=5)
        
        system_frame = tk.Frame(content, bg='white', relief='solid', bd=1); system_frame.pack(fill='x', pady=10)
        tk.Label(system_frame, text="💻 Система", font=('Segoe UI', 14, 'bold'), bg='white').pack(anchor='w', padx=15, pady=10)
        info_frame = tk.Frame(system_frame, bg='white'); info_frame.pack(fill='x', padx=15, pady=10)
        system_info = [("Версия ОС:", "Windows 12 Simulator"), ("Сборка:", "22621.1928"),
                      ("Скриншоты:", f"{len(self.windows_system.screenshots)} шт."), ("Объекты в корзине:", f"{len(self.windows_system.recycle_bin)} шт.")]
        for label, value in system_info:
            row_frame = tk.Frame(info_frame, bg='white'); row_frame.pack(fill='x', pady=2)
            tk.Label(row_frame, text=label, font=('Segoe UI', 10), bg='white', width=20, anchor='w').pack(side='left')
            tk.Label(row_frame, text=value, font=('Segoe UI', 10), bg='white', fg='#666666').pack(side='left')

class ModernBrowserWindow:
    def __init__(self, parent, windows_system):
        self.window = tk.Toplevel(parent); self.windows_system = windows_system
        self.window.title("Microsoft Edge - Windows 12"); self.window.geometry("1300x800"); self.window.configure(bg='#ffffff')
        self.window.protocol("WM_DELETE_WINDOW", self.on_close); self.setup_browser_ui()

    def on_close(self):
        for window_info in self.windows_system.open_windows[:]:
            if window_info['window'] == self.window: self.windows_system.open_windows.remove(window_info); break
        self.window.destroy()

    def setup_browser_ui(self):
        self.tab_frame = tk.Frame(self.window, bg='#2d2d2d', height=40); self.tab_frame.pack(fill='x'); self.tab_frame.pack_propagate(False)
        nav_frame = tk.Frame(self.window, bg='#f8f9fa', height=60); nav_frame.pack(fill='x'); nav_frame.pack_propagate(False)
        
        nav_buttons = tk.Frame(nav_frame, bg='#f8f9fa'); nav_buttons.pack(side='left', padx=10)
        for btn_text in ["←", "→", "↻"]: 
            tk.Button(nav_buttons, text=btn_text, font=('Segoe UI', 12), bg='#f8f9fa', fg='#5f6368', bd=0, cursor='hand2', width=3).pack(side='left', padx=2)
        
        self.search_frame = tk.Frame(nav_frame, bg='#f8f9fa'); self.search_frame.pack(side='left', fill='x', expand=True, padx=10, pady=10)
        self.search_var = tk.StringVar()
        self.search_entry = tk.Entry(self.search_frame, textvariable=self.search_var, font=('Segoe UI', 11), bg='white', relief='solid', bd=1)
        self.search_entry.pack(fill='x', ipady=8); self.search_entry.insert(0, "Введите запрос или URL...")
        self.search_entry.bind('<Return>', self.perform_search); self.search_entry.bind('<FocusIn>', self.clear_placeholder)
        
        tk.Button(nav_frame, text="🔍", font=('Segoe UI', 12), bg='#0078d4', fg='white', bd=0, cursor='hand2', command=self.perform_search).pack(side='right', padx=10)
        self.content_frame = tk.Frame(self.window, bg='white'); self.content_frame.pack(fill='both', expand=True)
        self.show_google_homepage()

    def clear_placeholder(self, event):
        if self.search_entry.get() == "Введите запрос или URL...": self.search_entry.delete(0, tk.END)

    def perform_search(self, event=None):
        query = self.search_var.get()
        if not query or query == "Введите запрос или URL...": return
        self.search_history.append(query)
        if query.startswith(('http://', 'https://')): self.show_web_content(query)
        else: self.search_google(query)

    def search_google(self, query):
        self.clear_content()
        loading_frame = tk.Frame(self.content_frame, bg='white'); loading_frame.pack(expand=True)
        tk.Label(loading_frame, text="🔍 Поиск в Google...", font=('Arial', 16), bg='white').pack(pady=20)
        threading.Thread(target=self._perform_google_search, args=(query,), daemon=True).start()

    def _perform_google_search(self, query):
        try:
            time.sleep(1)
            results = self.get_real_google_results(query)
            self.window.after(0, self.show_search_results, query, results)
        except Exception as e: self.window.after(0, self.show_error, f"Ошибка поиска: {str(e)}")

    def get_real_google_results(self, query):
        try:
            results = [{"title": f"{query} - Википедия", "url": f"https://ru.wikipedia.org/wiki/{query.replace(' ', '_')}",
                       "description": f"Узнайте больше о {query} на Википедии - свободной энциклопедии с миллионами статей на разных языках."},
                      {"title": f"{query} - Новости", "url": f"https://news.google.com/search?q={query}",
                       "description": f"Последние новости о {query}. Актуальные события и статьи от ведущих мировых изданий."},
                      {"title": f"Что такое {query}?", "url": f"https://www.google.com/search?q={query}",
                       "description": f"Полная информация о {query}. Определение, особенности и применение."}]
            if "погода" in query.lower(): results.insert(0, {"title": f"Погода {query} - Яндекс.Погода", "url": f"https://yandex.ru/pogoda/{query}",
                       "description": f"Точный прогноз погоды для {query}. Температура, осадки, давление и влажность."})
            if "курс" in query.lower(): results.insert(0, {"title": f"Курсы валют - {query}", "url": "https://www.cbr.ru/currency_base/daily/",
                       "description": f"Актуальные курсы валют ЦБ РФ. {query} на сегодняшний день."})
            return results
        except: return [{"title": f"{query} - Поиск в Google", "url": f"https://www.google.com/search?q={query}",
                        "description": f"Найдено около 15,000,000 результатов по запросу {query}"}]

    def show_search_results(self, query, results):
        self.clear_content()
        results_frame = tk.Frame(self.content_frame, bg='white'); results_frame.pack(fill='both', expand=True, padx=100, pady=20)
        stats_frame = tk.Frame(results_frame, bg='white'); stats_frame.pack(fill='x', pady=10)
        tk.Label(stats_frame, text=f"Результатов: примерно {len(results) * 1580000:,} (0.45 сек.)", font=('Arial', 12), bg='white', fg='#70757a').pack(anchor='w')
        
        search_result_frame = tk.Frame(results_frame, bg='white'); search_result_frame.pack(fill='x', pady=10)
        result_search = tk.Entry(search_result_frame, font=('Arial', 14), width=60, relief='solid', bd=1)
        result_search.insert(0, query); result_search.pack(ipady=8)
        result_search.bind('<Return>', lambda e: self.search_var.set(result_search.get()) or self.perform_search())
        
        for result in results:
            result_card = tk.Frame(results_frame, bg='white'); result_card.pack(fill='x', pady=15)
            title_label = tk.Label(result_card, text=result["title"], font=('Arial', 16), bg='white', fg='#1a0dab', cursor='hand2')
            title_label.pack(anchor='w'); title_label.bind('<Button-1>', lambda e, url=result["url"]: self.show_web_page(url))
            url_label = tk.Label(result_card, text=result["url"], font=('Arial', 12), bg='white', fg='#006621', cursor='hand2')
            url_label.pack(anchor='w'); url_label.bind('<Button-1>', lambda e, url=result["url"]: self.show_web_page(url))
            desc_label = tk.Label(result_card, text=result["description"], font=('Arial', 12), bg='white', fg='#3c4043', wraplength=800, justify='left')
            desc_label.pack(anchor='w')

    def show_web_page(self, url):
        self.clear_content()
        web_frame = tk.Frame(self.content_frame, bg='white'); web_frame.pack(fill='both', expand=True, padx=20, pady=20)
        tk.Label(web_frame, text=f"🌐 Загрузка страницы: {url}", font=('Arial', 14), bg='white').pack(pady=20)
        
        if "wikipedia" in url: self.show_wikipedia_page(web_frame, url)
        elif "news" in url: self.show_news_page(web_frame, url)
        else: tk.Label(web_frame, text="Это имитация веб-браузера. В реальном приложении\nздесь отображалась бы веб-страница.", 
                      font=('Arial', 12), bg='white', fg='#666').pack(pady=10)
        
        tk.Button(web_frame, text="📖 Открыть в настоящем браузере", font=('Arial', 12), bg='#0078d4', fg='white',
                 command=lambda: webbrowser.open(url)).pack(pady=10)

    def show_wikipedia_page(self, parent, url):
        content_frame = tk.Frame(parent, bg='white'); content_frame.pack(fill='both', expand=True)
        title = url.split('/')[-1].replace('_', ' ')
        tk.Label(content_frame, text=title, font=('Arial', 24, 'bold'), bg='white').pack(pady=10)
        article_text = f"{title} - это тема, о которой можно найти много информации в интернете.\n\nВ реальной Википедии здесь была бы подробная статья..."
        text_widget = scrolledtext.ScrolledText(content_frame, font=('Arial', 12), bg='white', wrap=tk.WORD, height=15)
        text_widget.pack(fill='both', expand=True, padx=20, pady=10); text_widget.insert('1.0', article_text); text_widget.config(state='disabled')

    def show_news_page(self, parent, url):
        content_frame = tk.Frame(parent, bg='white'); content_frame.pack(fill='both', expand=True)
        tk.Label(content_frame, text="📰 Новостная лента", font=('Arial', 20, 'bold'), bg='white').pack(pady=10)
        news_items = [{"title": "Важные мировые события", "time": "Только что", "source": "Reuters"},
                     {"title": "Технологические новости", "time": "2 часа назад", "source": "TechCrunch"},
                     {"title": "Спортивные результаты", "time": "5 часов назад", "source": "ESPN"},
                     {"title": "Культурные мероприятия", "time": "Вчера", "source": "Culture News"}]
        for news in news_items:
            news_frame = tk.Frame(content_frame, bg='#f8f9fa', relief='solid', bd=1); news_frame.pack(fill='x', padx=20, pady=5)
            tk.Label(news_frame, text=news["title"], font=('Arial', 12, 'bold'), bg='#f8f9fa').pack(anchor='w', padx=10, pady=5)
            info_frame = tk.Frame(news_frame, bg='#f8f9fa'); info_frame.pack(fill='x', padx=10, pady=5)
            tk.Label(info_frame, text=news["time"], font=('Arial', 10), bg='#f8f9fa', fg='#666').pack(side='left')
            tk.Label(info_frame, text=news["source"], font=('Arial', 10), bg='#f8f9fa', fg='#006621').pack(side='right')

    def show_web_content(self, url): self.show_web_page(url)

    def show_google_homepage(self):
        self.clear_content()
        center_frame = tk.Frame(self.content_frame, bg='white'); center_frame.place(relx=0.5, rely=0.4, anchor='center')
        tk.Label(center_frame, text="Google", font=('Arial', 56, 'bold'), bg='white').pack(pady=30)
        search_frame = tk.Frame(center_frame, bg='white'); search_frame.pack(pady=20)
        home_search = tk.Entry(search_frame, font=('Arial', 14), width=60, relief='solid', bd=1); home_search.pack(ipady=10)
        home_search.bind('<Return>', lambda e: self.search_var.set(home_search.get()) or self.perform_search())

    def show_error(self, message): messagebox.showerror("Ошибка браузера", message)

    def clear_content(self):
        for widget in self.content_frame.winfo_children(): widget.destroy()

class ModernFileExplorer:
    def __init__(self, parent, windows_system):
        self.window = tk.Toplevel(parent); self.windows_system = windows_system
        self.window.title("Проводник - Windows 12"); self.window.geometry("1000x700"); self.window.configure(bg='#f3f3f3')
        self.window.protocol("WM_DELETE_WINDOW", self.on_close); self.setup_explorer_ui()

    def on_close(self):
        for window_info in self.windows_system.open_windows[:]:
            if window_info['window'] == self.window: self.windows_system.open_windows.remove(window_info); break
        self.window.destroy()

    def setup_explorer_ui(self):
        top_frame = tk.Frame(self.window, bg='#ffffff', height=60); top_frame.pack(fill='x'); top_frame.pack_propagate(False)
        tk.Label(top_frame, text="⚡ Быстрый доступ", font=('Segoe UI', 12, 'bold'), bg='#ffffff').pack(side='left', padx=20, pady=10)
        
        main_frame = tk.Frame(self.window, bg='#f3f3f3'); main_frame.pack(fill='both', expand=True, padx=20, pady=20)
        folders_grid = tk.Frame(main_frame, bg='#f3f3f3'); folders_grid.pack(fill='both', expand=True)
        
        folders = [("📁", "Документы", "124 файла", "#0078d4"), ("🖼️", "Изображения", f"{len(self.windows_system.screenshots)} фото", "#e74856"),
                  ("🎵", "Музыка", "347 треков", "#107c10"), ("📥", "Загрузки", "48 файлов", "#008575"),
                  ("🏠", "Рабочий стол", f"{len(self.windows_system.desktop_items)} элементов", "#6b69d6"),
                  ("🗑️", "Корзина", f"{len(self.windows_system.recycle_bin)} объектов", "#a0a0a0")]
        
        for i, (icon, name, info, color) in enumerate(folders):
            row, col = i // 3, i % 3
            folder_card = tk.Frame(folders_grid, bg='white', relief='flat', bd=1); folder_card.grid(row=row, column=col, padx=10, pady=10, sticky='nsew')
            folder_card.bind('<Double-Button-1>', lambda e, n=name: self.open_folder(n))
            tk.Label(folder_card, text=icon, font=('Segoe UI', 32), bg='white', fg=color).pack(pady=(20, 10))
            tk.Label(folder_card, text=name, font=('Segoe UI', 11, 'bold'), bg='white').pack()
            tk.Label(folder_card, text=info, font=('Segoe UI', 9), bg='white', fg='#666666').pack(pady=(0, 15))
        
        for i in range(3): folders_grid.columnconfigure(i, weight=1)
        for i in range(2): folders_grid.rowconfigure(i, weight=1)

    def open_folder(self, folder_name):
        if folder_name == "Корзина": RecycleBinApp(self.window, self.windows_system)
        elif folder_name == "Изображения": PhotosApp(self.window, self.windows_system)
        else: messagebox.showinfo("Проводник", f"Открыта папка: {folder_name}")

class PhotosApp:
    def __init__(self, parent, windows_system):
        self.window = tk.Toplevel(parent); self.windows_system = windows_system
        self.window.title("Фотографии - Windows 12"); self.window.geometry("1200x800"); self.window.configure(bg='#1a1a1a')
        self.window.protocol("WM_DELETE_WINDOW", self.on_close); self.setup_photos_ui()

    def on_close(self):
        for window_info in self.windows_system.open_windows[:]:
            if window_info['window'] == self.window: self.windows_system.open_windows.remove(window_info); break
        self.window.destroy()

    def setup_photos_ui(self):
        header = tk.Frame(self.window, bg='#2d2d2d', height=60); header.pack(fill='x'); header.pack_propagate(False)
        tk.Label(header, text="🖼️ Фотографии", font=('Segoe UI', 16, 'bold'), bg='#2d2d2d', fg='white').pack(side='left', padx=20)
        tk.Button(header, text="📸 Сделать скриншот", font=('Segoe UI', 11), bg='#0078d4', fg='white', bd=0, cursor='hand2', padx=15, pady=8,
                 command=self.windows_system.take_screenshot).pack(side='right', padx=20)
        
        content = tk.Frame(self.window, bg='#1a1a1a'); content.pack(fill='both', expand=True, padx=20, pady=20)
        if not self.windows_system.screenshots:
            empty_frame = tk.Frame(content, bg='#1a1a1a'); empty_frame.place(relx=0.5, rely=0.5, anchor='center')
            tk.Label(empty_frame, text="🖼️", font=('Segoe UI', 64), bg='#1a1a1a', fg='#666666').pack(pady=10)
            tk.Label(empty_frame, text="Здесь пока нет фотографий", font=('Segoe UI', 16), bg='#1a1a1a', fg='white').pack(pady=5)
            tk.Label(empty_frame, text="Сделайте скриншот с помощью кнопки выше или клавиши Print Screen", 
                    font=('Segoe UI', 11), bg='#1a1a1a', fg='#666666').pack(pady=5)
        else: self.setup_photos_grid(content)

    def setup_photos_grid(self, parent):
        canvas = tk.Canvas(parent, bg='#1a1a1a', highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw"); canvas.configure(yscrollcommand=scrollbar.set)
        
        for i, screenshot in enumerate(reversed(self.windows_system.screenshots)):
            row, col = i // 4, i % 4
            photo_frame = tk.Frame(scrollable_frame, bg='#2d2d2d', relief='flat', bd=1); photo_frame.grid(row=row, column=col, padx=10, pady=10, sticky='nsew')
            try:
                img_data = base64.b64decode(screenshot['data']); image = Image.open(io.BytesIO(img_data)); image.thumbnail((150, 150))
                photo = ImageTk.PhotoImage(image); thumbnail = tk.Label(photo_frame, image=photo, bg='#2d2d2d', cursor='hand2')
                thumbnail.image = photo; thumbnail.pack(pady=10); thumbnail.bind('<Button-1>', lambda e, s=screenshot: self.view_photo(s))
            except:
                thumbnail = tk.Label(photo_frame, text="🖼️", font=('Segoe UI', 48), bg='#2d2d2d', fg='white', cursor='hand2')
                thumbnail.pack(pady=20); thumbnail.bind('<Button-1>', lambda e, s=screenshot: self.view_photo(s))
            
            info_frame = tk.Frame(photo_frame, bg='#2d2d2d'); info_frame.pack(fill='x', padx=10, pady=10)
            tk.Label(info_frame, text=screenshot['name'], font=('Segoe UI', 10, 'bold'), bg='#2d2d2d', fg='white', anchor='w').pack(fill='x')
            tk.Label(info_frame, text=screenshot['date'], font=('Segoe UI', 9), bg='#2d2d2d', fg='#aaaaaa', anchor='w').pack(fill='x')
            tk.Button(info_frame, text="🗑️", font=('Segoe UI', 10), bg='#e74856', fg='white', bd=0, cursor='hand2', width=3,
                     command=lambda s=screenshot: self.delete_photo(s)).pack(side='right')
        
        for i in range(4): scrollable_frame.columnconfigure(i, weight=1)
        canvas.pack(side="left", fill="both", expand=True); scrollbar.pack(side="right", fill="y")

    def view_photo(self, screenshot):
        view_window = tk.Toplevel(self.window); view_window.title(f"Фотографии - {screenshot['name']}"); view_window.geometry("900x700"); view_window.configure(bg='black')
        try:
            img_data = base64.b64decode(screenshot['data']); image = Image.open(io.BytesIO(img_data))
            width, height = image.size; max_size = 800
            if width > max_size or height > max_size:
                ratio = min(max_size/width, max_size/height); new_size = (int(width * ratio), int(height * ratio))
                image = image.resize(new_size, Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(image); image_label = tk.Label(view_window, image=photo, bg='black')
            image_label.image = photo; image_label.pack(expand=True, padx=20, pady=20)
        except: tk.Label(view_window, text="🖼️", font=('Segoe UI', 120), bg='black', fg='white').pack(expand=True)
        
        info_frame = tk.Frame(view_window, bg='#2d2d2d'); info_frame.pack(fill='x', pady=10)
        tk.Label(info_frame, text=screenshot['name'], font=('Segoe UI', 12, 'bold'), bg='#2d2d2d', fg='white').pack(pady=5)
        tk.Label(info_frame, text=f"Создан: {screenshot['date']}", font=('Segoe UI', 10), bg='#2d2d2d', fg='#aaaaaa').pack(pady=2)

    def delete_photo(self, screenshot):
        if messagebox.askyesno("Удаление", f"Удалить {screenshot['name']}?"):
            self.windows_system.screenshots = [s for s in self.windows_system.screenshots if s['id'] != screenshot['id']]
            Utils.save_data('screenshots.json', self.windows_system.screenshots)
            self.window.destroy(); PhotosApp(self.window, self.windows_system)

class RecycleBinApp:
    def __init__(self, parent, windows_system):
        self.window = tk.Toplevel(parent); self.windows_system = windows_system
        self.window.title("Корзина - Windows 12"); self.window.geometry("800x600"); self.window.configure(bg='#f3f3f3')
        self.window.protocol("WM_DELETE_WINDOW", self.on_close); self.setup_bin_ui()

    def on_close(self):
        for window_info in self.windows_system.open_windows[:]:
            if window_info['window'] == self.window: self.windows_system.open_windows.remove(window_info); break
        self.window.destroy()

    def setup_bin_ui(self):
        header = tk.Frame(self.window, bg='#ffffff', height=60); header.pack(fill='x'); header.pack_propagate(False)
        tk.Label(header, text="🗑️ Корзина", font=('Segoe UI', 16, 'bold'), bg='#ffffff').pack(side='left', padx=20)
        buttons_frame = tk.Frame(header, bg='#ffffff'); buttons_frame.pack(side='right', padx=20)
        tk.Button(buttons_frame, text="Восстановить все", font=('Segoe UI', 11), bg='#0078d4', fg='white', bd=0, cursor='hand2', padx=15,
                 command=self.restore_all).pack(side='left', padx=5)
        tk.Button(buttons_frame, text="Очистить корзину", font=('Segoe UI', 11), bg='#e74856', fg='white', bd=0, cursor='hand2', padx=15,
                 command=self.empty_bin).pack(side='left', padx=5)
        
        content = tk.Frame(self.window, bg='#f3f3f3'); content.pack(fill='both', expand=True, padx=20, pady=20)
        if not self.windows_system.recycle_bin:
            empty_frame = tk.Frame(content, bg='#f3f3f3'); empty_frame.place(relx=0.5, rely=0.5, anchor='center')
            tk.Label(empty_frame, text="🗑️", font=('Segoe UI', 64), bg='#f3f3f3', fg='#cccccc').pack(pady=10)
            tk.Label(empty_frame, text="Корзина пуста", font=('Segoe UI', 16), bg='#f3f3f3').pack(pady=5)
            tk.Label(empty_frame, text="Удаленные файлы появятся здесь", font=('Segoe UI', 11), bg='#f3f3f3', fg='#666666').pack(pady=5)
        else: self.setup_bin_list(content)

    def setup_bin_list(self, parent):
        canvas = tk.Canvas(parent, bg='#f3f3f3', highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw"); canvas.configure(yscrollcommand=scrollbar.set)
        
        for i, item in enumerate(self.windows_system.recycle_bin):
            item_frame = tk.Frame(scrollable_frame, bg='white', relief='solid', bd=1); item_frame.pack(fill='x', pady=5, padx=10)
            info_frame = tk.Frame(item_frame, bg='white'); info_frame.pack(fill='x', padx=15, pady=10)
            tk.Label(info_frame, text="📄", font=('Segoe UI', 20), bg='white').pack(side='left', padx=(0, 15))
            text_frame = tk.Frame(info_frame, bg='white'); text_frame.pack(side='left', fill='x', expand=True)
            tk.Label(text_frame, text=item['name'], font=('Segoe UI', 12, 'bold'), bg='white', anchor='w').pack(fill='x')
            tk.Label(text_frame, text=f"Удален: {item['deleted_date']} | Тип: {item['type']}", font=('Segoe UI', 10), bg='white', fg='#666666', anchor='w').pack(fill='x')
            
            action_frame = tk.Frame(info_frame, bg='white'); action_frame.pack(side='right')
            tk.Button(action_frame, text="Восстановить", font=('Segoe UI', 10), bg='#0078d4', fg='white', bd=0, cursor='hand2',
                     command=lambda i=item: self.restore_item(i)).pack(side='left', padx=5)
            tk.Button(action_frame, text="Удалить навсегда", font=('Segoe UI', 10), bg='#e74856', fg='white', bd=0, cursor='hand2',
                     command=lambda i=item: self.delete_permanently(i)).pack(side='left', padx=5)
        
        canvas.pack(side="left", fill="both", expand=True); scrollbar.pack(side="right", fill="y")

    def restore_all(self):
        if messagebox.askyesno("Восстановление", "Восстановить все объекты из корзины?"):
            for item in self.windows_system.recycle_bin[:]: self.restore_item(item, show_message=False)
            messagebox.showinfo("Корзина", "Все объекты восстановлены!"); self.window.destroy()

    def empty_bin(self):
        if messagebox.askyesno("Очистка", "Очистить корзину? Это действие нельзя отменить."):
            self.windows_system.recycle_bin.clear(); Utils.save_data('recycle_bin.json', self.windows_system.recycle_bin)
            messagebox.showinfo("Корзина", "Корзина очищена!"); self.window.destroy()

    def restore_item(self, item, show_message=True):
        if item['type'] == 'file':
            if not any(i['name'] == item['name'] for i in self.windows_system.desktop_items):
                new_item = {"type": "file", "name": item['name'], "icon": "📄", "color": "#0078d4", "x": random.randint(100, 800), "y": random.randint(100, 500)}
                self.windows_system.desktop_items.append(new_item); Utils.save_data('desktop_items.json', self.windows_system.desktop_items)
        self.windows_system.recycle_bin.remove(item); Utils.save_data('recycle_bin.json', self.windows_system.recycle_bin)
        if show_message: messagebox.showinfo("Восстановление", f"Объект '{item['name']}' восстановлен!"); self.window.destroy(); RecycleBinApp(self.window, self.windows_system)

    def delete_permanently(self, item):
        if messagebox.askyesno("Удаление", f"Удалить '{item['name']}' навсегда? Это действие нельзя отменить."):
            self.windows_system.recycle_bin.remove(item); Utils.save_data('recycle_bin.json', self.windows_system.recycle_bin)
            messagebox.showinfo("Удаление", "Объект удален навсегда!"); self.window.destroy(); RecycleBinApp(self.window, self.windows_system)

def main():
    root = tk.Tk(); windows12 = Windows12(root)
    print("🚀 Windows 12 Simulator запущен!")
    print("✨ Все функции работают:")
    print("   📁 РЕАЛЬНОЕ перемещение файлов в папки")
    print("   🖱️  Перетаскивание файлов на папки") 
    print("   📄 Файлы исчезают с рабочего стола при перемещении")
    print("   📂 Папки показывают реальное содержимое")
    print("   💾 Сохранение файлов")
    print("   🌐 Браузер с поиском")
    print("   🖼️ Фотографии со скриншотами")
    print("   ⚙️ Параметры системы")
    print("   🗑️ Корзина с восстановлением")
    print("   🎮 Steam с РЕАЛЬНОЙ регистрацией через Gmail")
    print("   🪟 Win+R с закругленным дизайном")
    
    try: root.mainloop()
    except Exception as e: print(f"❌ Ошибка в основном цикле: {e}")
    finally:
        print("🔄 Принудительное восстановление панели задач...")
        try:
            import subprocess
            subprocess.run('cmd /c taskkill /f /im explorer.exe && start explorer.exe', shell=True, capture_output=True)
            print("✅ Панель задач восстановлена в блоке finally")
        except Exception as e: print(f"❌ Ошибка в блоке finally: {e}")

if __name__ == "__main__":
    main()