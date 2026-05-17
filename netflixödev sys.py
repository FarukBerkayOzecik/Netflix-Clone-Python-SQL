import sys
from datetime import datetime
from tkinter import messagebox, ttk
import customtkinter as ctk
import pyodbc

# =========================================================================
# ARAYÜZ VE TEMA YAPILANDIRMASI (UI CONFIGURATION)
# =========================================================================
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("dark-blue")


# =========================================================================
# 1. GELİŞMİŞ VERİTABANI BAĞLANTI YÖNETİCİSİ (ADVANCED DB LAYER)
# =========================================================================
class DatabaseHelper:

    def __init__(self):
        self.server = r".\SQLEXPRESS"
        self.database = "NetflixCloneDB"
        self.conn_str = None
        self.auto_detect_connection()
        self.guarantee_required_columns()

    def auto_detect_connection(self):
        """Sistemdeki SQL sürücülerini tarar ve en güvenli bağlantıyı kurar."""
        drivers = [
            "{ODBC Driver 18 for SQL Server}",
            "{ODBC Driver 17 for SQL Server}",
            "{SQL Server Native Client 11.0}",
            "{SQL Server}",
        ]

        for driver in drivers:
            try:
                test_str = (
                    f"Driver={driver};"
                    f"Server={self.server};"
                    f"Database={self.database};"
                    "Trusted_Connection=yes;"
                    "Encrypt=yes;"
                    "TrustServerCertificate=yes;"
                    "LoginTimeout=5;"
                )
                conn = pyodbc.connect(test_str)
                conn.close()
                self.conn_str = test_str
                print(f"[VERİTABANI] Bağlantı Başarılı. Sürücü: {driver}")
                return
            except Exception:
                continue

        # Şifreleme desteklenmiyorsa eski usül fallback bağlantısı
        self.conn_str = (
            f"Driver={{SQL Server}};"
            f"Server={self.server};"
            f"Database={self.database};"
            "Trusted_Connection=yes;"
        )

    def guarantee_required_columns(self):
        """Hocanın projede istediği bölüm sayısı, tamamlanma durumu gibi kolonlar veritabanında yoksa otomatik oluşturur."""
        alters = [
            "ALTER TABLE IzlemeLog ADD bolum_no INT DEFAULT 1",
            "ALTER TABLE IzlemeLog ADD tamamlandi_mi BIT DEFAULT 0",
            "ALTER TABLE IzlemeLog ADD tarih DATETIME DEFAULT GETDATE()",
            "ALTER TABLE IzlemeLog ADD puan INT DEFAULT 0",
            "ALTER TABLE Program ADD bolum_sayisi INT DEFAULT 1",
            "ALTER TABLE Program ADD program_uzunlugu INT DEFAULT 90",
            "ALTER TABLE Program ADD ortalama_puan DECIMAL(3,2) DEFAULT 0.00",
            "ALTER TABLE Program ADD izlenme_sayisi INT DEFAULT 0"
        ]
        for q in alters:
            try:
                c = pyodbc.connect(self.conn_str)
                cr = c.cursor()
                cr.execute(q)
                c.commit()
                c.close()
            except:
                pass # Kolon zaten varsa hata vermeden geçer

    def test_connection_dialog(self):
        try:
            conn = pyodbc.connect(self.conn_str)
            conn.close()
            return True
        except Exception as e:
            messagebox.showerror(
                "Veritabanı Bağlantı Hatası",
                f"SQL Server'a bağlanılamadı!\n\nServislerin açık olduğundan emin olun.\nHata Detayı: {str(e)}",
            )
            return False

    def execute_query(self, query, params=()):
        """Veritabanına veri yazma (INSERT, UPDATE, DELETE) işlemleri."""
        try:
            conn = pyodbc.connect(self.conn_str)
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            conn.close()
            return True, "Başarılı"
        except Exception as e:
            print(f"[SQL HATA]: {e} \n[SORGU]: {query}")
            return False, str(e)

    def fetch_all(self, query, params=()):
        """Çoklu veri çekme (Tablo Listeleme vb.) işlemleri."""
        try:
            conn = pyodbc.connect(self.conn_str)
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()
            conn.close()
            return rows
        except Exception as e:
            print(f"[SQL FETCH ALL HATA]: {e} \n[SORGU]: {query}")
            return []

    def fetch_one(self, query, params=()):
        """Tekil veri doğrulama (Giriş yapma vb.) işlemleri."""
        try:
            conn = pyodbc.connect(self.conn_str)
            cursor = conn.cursor()
            cursor.execute(query, params)
            row = cursor.fetchone()
            conn.close()
            return row
        except Exception as e:
            print(f"[SQL FETCH ONE HATA]: {e} \n[SORGU]: {query}")
            return None


# Global Database Nesnesi (Bağlantı Köprüsü)
db = DatabaseHelper()


# =========================================================================
# 2. UYGULAMA PENCERE ÇEKİRDEĞİ (MAIN APPLICATION ENGINE)
# =========================================================================
class NetflixApp(ctk.CTk):

    def __init__(self):
        super().__init__()
        self.title("Netflix Akademik İçerik Yönetim Otomasyonu - Full Version")
        self.geometry("1280x800")
        self.minsize(1200, 750)
        self.current_user = None
        self.current_frame = None

        if db.test_connection_dialog():
            self.show_frame(LoginFrame)
        else:
            self.after(200, self.destroy)

    def show_frame(self, frame_class):
        """Eski ekranı RAM'den tamamen silerek yenisini dinamik olarak yükler."""
        if self.current_frame is not None:
            self.current_frame.destroy()
        self.current_frame = frame_class(self)
        self.current_frame.pack(fill="both", expand=True)


# =========================================================================
# 3. OTURUM AÇMA VE GÜVENLİK SİSTEMİ (LOGIN & REGISTER)
# =========================================================================
class LoginFrame(ctk.CTkFrame):

    def __init__(self, master):
        super().__init__(master)
        self.master = master
        self.grid_columnconfigure(0, weight=1)

        lbl_title = ctk.CTkLabel(self, text="NETFLIX", font=("Arial Black", 56), text_color="#E50914")
        lbl_title.grid(row=0, column=0, pady=(100, 10))

        lbl_subtitle = ctk.CTkLabel(self, text="AKADEMİK VERİTABANI YÖNETİM SİSTEMİ", font=("Arial Bold", 14), text_color="gray")
        lbl_subtitle.grid(row=1, column=0, pady=(0, 30))

        self.email_entry = ctk.CTkEntry(self, placeholder_text="E-posta Adresi", width=380, height=45)
        self.email_entry.grid(row=2, column=0, pady=10)
        self.email_entry.insert(0, "admin@netflix.com")

        self.password_entry = ctk.CTkEntry(self, placeholder_text="Şifre", show="*", width=380, height=45)
        self.password_entry.grid(row=3, column=0, pady=10)
        self.password_entry.insert(0, "admin123")

        login_btn = ctk.CTkButton(self, text="Güvenli Oturum Aç", command=self.login, width=380, height=45, fg_color="#E50914", hover_color="#B80710", font=("Arial", 15, "bold"))
        login_btn.grid(row=4, column=0, pady=(20, 10))

        register_btn = ctk.CTkButton(self, text="Sisteme Yeni Hesap Tanımla", command=lambda: master.show_frame(RegisterFrame), width=380, height=45, fg_color="transparent", border_width=1, border_color="#E50914", text_color="#E50914", font=("Arial", 14, "bold"))
        register_btn.grid(row=5, column=0, pady=5)

    def login(self):
        email = self.email_entry.get().strip()
        password = self.password_entry.get().strip()

        if not email or not password:
            messagebox.showwarning("Eksik Veri", "Lütfen tüm giriş alanlarını doldurunuz!")
            return

        # DİKKAT: ORİJİNAL ÇALIŞAN KOLON İSİMLERİ KULLANILDI (eposta hatası giderildi)
        query = "SELECT id, ad, soyad, rol_id, aktif_mi FROM Kullanici WHERE email = ? AND sifre = ?"
        user = db.fetch_one(query, (email, password))

        if user:
            if not user[4]: # aktif_mi kontrolü
                messagebox.showerror("Erişim Reddedildi", "Hesabınız sistem yöneticisi tarafından askıya alınmıştır!")
                return

            # Kullanıcı oturumu sisteme işleniyor
            self.master.current_user = {
                "id": user[0],
                "ad": user[1],
                "soyad": user[2],
                "rol_id": user[3],
                "email": email
            }

            # Oturum Loglarının veritabanına postalanması
            try:
                db.execute_query("INSERT INTO OturumLog (kullanici_id) VALUES (?)", (user[0],))
            except: pass

            # Yönlendirme (Admin = 1, Kullanıcı = 2)
            if user[3] == 1:
                self.master.show_frame(AdminDashboard)
            else:
                self.master.show_frame(UserDashboard)
        else:
             messagebox.showerror("Hatalı Kimlik", "Girdiğiniz e-posta veya şifre veritabanındaki kayıtlarla eşleşmedi!")


class RegisterFrame(ctk.CTkFrame):

    def __init__(self, master):
        super().__init__(master)
        self.master = master
        self.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(self, text="Sistem Kayıt Formu", font=("Arial Black", 28), text_color="white").grid(row=0, column=0, pady=(30, 20))

        self.ad_entry = ctk.CTkEntry(self, placeholder_text="Ad", width=380, height=35)
        self.ad_entry.grid(row=1, column=0, pady=5)
        self.soyad_entry = ctk.CTkEntry(self, placeholder_text="Soyad", width=380, height=35)
        self.soyad_entry.grid(row=2, column=0, pady=5)
        self.email_entry = ctk.CTkEntry(self, placeholder_text="E-posta", width=380, height=35)
        self.email_entry.grid(row=3, column=0, pady=5)
        self.sifre_entry = ctk.CTkEntry(self, placeholder_text="Şifre (En az 6 karakter)", show="*", width=380, height=35)
        self.sifre_entry.grid(row=4, column=0, pady=5)
        self.dogum_entry = ctk.CTkEntry(self, placeholder_text="Doğum Tarihi (YYYY-MM-DD)", width=380, height=35)
        self.dogum_entry.grid(row=5, column=0, pady=5)
        self.dogum_entry.insert(0, "2000-01-01")
        self.ulke_entry = ctk.CTkEntry(self, placeholder_text="Ülke", width=380, height=35)
        self.ulke_entry.grid(row=6, column=0, pady=5)
        self.ulke_entry.insert(0, "Türkiye")

        ctk.CTkLabel(self, text="İlgi Duyduğunuz Tür ID'lerini Virgülle Ayırarak Girin (Örn: 1, 2, 3)", text_color="orange", font=("Arial Bold", 11)).grid(row=7, column=0, pady=(10, 0))
        self.genres_entry = ctk.CTkEntry(self, placeholder_text="Örnek Kategori ID'leri: 1,2,3", width=380, height=35)
        self.genres_entry.grid(row=8, column=0, pady=5)

        ctk.CTkButton(self, text="Hesabı Oluştur ve Kaydet", command=self.register, width=380, height=42, fg_color="#E50914", hover_color="#B80710", font=("Arial", 14, "bold")).grid(row=9, column=0, pady=15)
        ctk.CTkButton(self, text="Giriş Ekranına Dön", command=lambda: master.show_frame(LoginFrame), width=380, height=35, fg_color="transparent", border_width=1, border_color="gray", text_color="white").grid(row=10, column=0)

    def register(self):
        ad, soyad, email = self.ad_entry.get().strip(), self.soyad_entry.get().strip(), self.email_entry.get().strip()
        sifre, dogum, ulke = self.sifre_entry.get().strip(), self.dogum_entry.get().strip(), self.ulke_entry.get().strip()
        turler = self.genres_entry.get().strip()

        if not all([ad, soyad, email, sifre, dogum, ulke, turler]):
            messagebox.showwarning("Eksik", "Lütfen tüm alanları doldurunuz!")
            return

        if len(sifre) < 6:
            messagebox.showwarning("Güvenlik", "Şifre en az 6 karakter olmalıdır!")
            return

        if db.fetch_one("SELECT id FROM Kullanici WHERE email = ?", (email,)):
            messagebox.showerror("Hata", "Bu e-posta adresi veritabanında zaten kayıtlı!")
            return

        insert_query = "INSERT INTO Kullanici (ad, soyad, email, sifre, dogum_tarihi, ulke, rol_id, aktif_mi) VALUES (?, ?, ?, ?, ?, ?, 2, 1)"
        suc, msg = db.execute_query(insert_query, (ad, soyad, email, sifre, dogum, ulke))

        if suc:
            # Çoktan Çoğa Tür Bağlantılarını Sağlama
            user_row = db.fetch_one("SELECT id FROM Kullanici WHERE email = ?", (email,))
            if user_row:
                u_id = user_row[0]
                for t_id in turler.split(","):
                    if t_id.strip().isdigit():
                        db.execute_query("INSERT INTO KullaniciTur (kullanici_id, tur_id) VALUES (?, ?)", (u_id, int(t_id.strip())))
            messagebox.showinfo("Başarılı", "Kullanıcı hesabı başarıyla oluşturuldu!")
            self.master.show_frame(LoginFrame)
        else:
            messagebox.showerror("Hata", f"Kayıt işlemi başarısız:\n{msg}")


# =========================================================================
# 4. KULLANICI PANELI (HOCANIN İSTEDİĞİ BÜTÜN MODÜLLER BURADA)
# =========================================================================
class UserDashboard(ctk.CTkFrame):

    def __init__(self, master):
        super().__init__(master)
        self.master = master
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # SOL BAR / MENÜ
        sidebar = ctk.CTkFrame(self, width=230, corner_radius=0)
        sidebar.grid(row=0, column=0, sticky="nsew")
        sidebar.grid_propagate(False)

        ctk.CTkLabel(sidebar, text=f"HOŞ GELDİNİZ\n{master.current_user['ad']} {master.current_user['soyad']}", font=("Arial", 15, "bold"), text_color="#E50914").pack(pady=25, padx=10)

        ctk.CTkButton(sidebar, text="📺 İçerik Kataloğu", font=("Arial", 13, "bold"), command=self.load_explore, fg_color="#E50914").pack(pady=8, padx=15, fill="x")
        ctk.CTkButton(sidebar, text="👤 Profil Sayfam", font=("Arial", 13, "bold"), command=self.load_profile, fg_color="#2B2B2B").pack(pady=8, padx=15, fill="x")
        ctk.CTkButton(sidebar, text="📜 İzleme Geçmişim", font=("Arial", 13, "bold"), command=self.load_history, fg_color="#2B2B2B").pack(pady=8, padx=15, fill="x")
        ctk.CTkButton(sidebar, text="💡 Önerilen İçerikler", font=("Arial", 13, "bold"), command=self.load_recommendations, fg_color="#2B2B2B").pack(pady=8, padx=15, fill="x")
        ctk.CTkButton(sidebar, text="⭐ Favori Listem", font=("Arial", 13, "bold"), command=self.load_favorites, fg_color="#2B2B2B").pack(pady=8, padx=15, fill="x")
        
        ctk.CTkButton(sidebar, text="🚪 Oturumu Kapat", font=("Arial", 13, "bold"), fg_color="#404040", hover_color="red", command=lambda: master.show_frame(LoginFrame)).pack(side="bottom", pady=25, padx=15, fill="x")

        self.main_view = ctk.CTkFrame(self, fg_color="#1A1A1A")
        self.main_view.grid(row=0, column=1, sticky="nsew", padx=15, pady=15)

        self.setup_treeview_styles()
        self.load_explore()

    def setup_treeview_styles(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", background="#2D2D2D", foreground="white", fieldbackground="#2D2D2D", rowheight=30, font=("Arial", 11))
        style.configure("Treeview.Heading", background="#111111", foreground="white", font=("Arial Bold", 11))
        style.map("Treeview", background=[("selected", "#E50914")], foreground=[("selected", "white")])

    # -------------------------------------------------------------
    # İSTER F: DETAYLI PROFİL SAYFASI
    # -------------------------------------------------------------
    def load_profile(self):
        for w in self.main_view.winfo_children(): w.destroy()
        ctk.CTkLabel(self.main_view, text="👤 Kişisel Profil ve Hesap Analitiği", font=("Arial", 26, "bold"), text_color="white").pack(anchor="w", pady=(5, 15))
        
        u_id = self.master.current_user["id"]
        
        # SQL Verisi Çekimi (790'lık Orijinal DB Uyumuyla)
        query = """
        SELECT ad, soyad, email, dogum_tarihi, ulke, sifre,
               (SELECT ISNULL(SUM(kalinan_dakika), 0) FROM IzlemeLog WHERE kullanici_id=?),
               (SELECT COUNT(DISTINCT program_id) FROM IzlemeLog WHERE kullanici_id=?),
               (SELECT ISNULL(AVG(CAST(puan as FLOAT)), 0) FROM IzlemeLog WHERE kullanici_id=? AND puan > 0)
        FROM Kullanici WHERE id=?
        """
        data = db.fetch_one(query, (u_id, u_id, u_id, u_id))
        if not data: data = ("", "", "", "", "", "", 0, 0, 0)

        # Favori Tür Tespiti
        fav_tur_q = "SELECT t.TurAdi FROM KullaniciTur kt JOIN Tur t ON kt.tur_id = t.TurID WHERE kt.kullanici_id=?"
        try:
            fav_turler = db.fetch_all(fav_tur_q, (u_id,))
            turler_str = ", ".join([f[0] for f in fav_turler]) if fav_turler else "Tür seçilmemiş"
        except:
            turler_str = "Sistem Türleri Yükleyemedi"

        cols_frame = ctk.CTkFrame(self.main_view, fg_color="transparent")
        cols_frame.pack(fill="both", expand=True)

        left_frame = ctk.CTkFrame(cols_frame, fg_color="#222", width=450)
        left_frame.pack(side="left", fill="y", padx=10, pady=10, ipadx=15, ipady=15)

        right_frame = ctk.CTkFrame(cols_frame, fg_color="#222", width=450)
        right_frame.pack(side="left", fill="both", expand=True, padx=10, pady=10, ipadx=15, ipady=15)

        ctk.CTkLabel(left_frame, text="Kişisel Bilgileri Güncelle", font=("Arial", 18, "bold"), text_color="#E50914").pack(pady=10)
        
        entries = {}
        fields = [("Ad", data[0]), ("Soyad", data[1]), ("E-mail", data[2]), ("Doğum Tarihi", data[3]), ("Ülke", data[4]), ("Yeni Şifre", data[5])]
        
        for name, val in fields:
            ctk.CTkLabel(left_frame, text=f"{name}:", anchor="w").pack(fill="x", pady=(5,0))
            e = ctk.CTkEntry(left_frame)
            e.pack(fill="x", pady=2)
            if val: e.insert(0, str(val))
            entries[name] = e
            if name == "Yeni Şifre": e.configure(show="*")

        def update_profile():
            db.execute_query("UPDATE Kullanici SET ad=?, soyad=?, email=?, dogum_tarihi=?, ulke=?, sifre=? WHERE id=?",
                (entries["Ad"].get(), entries["Soyad"].get(), entries["E-mail"].get(), entries["Doğum Tarihi"].get(), entries["Ülke"].get(), entries["Yeni Şifre"].get(), u_id))
            messagebox.showinfo("Başarılı", "Profil bilgileriniz başarıyla güncellendi!")
            self.master.current_user['ad'] = entries["Ad"].get()
            self.master.current_user['soyad'] = entries["Soyad"].get()
            self.load_profile() # Refresh

        ctk.CTkButton(left_frame, text="Değişiklikleri Kaydet", command=update_profile, fg_color="#27AE60", height=35).pack(pady=20)

        ctk.CTkLabel(right_frame, text="Hesap İstatistikleri", font=("Arial", 18, "bold"), text_color="#E50914").pack(pady=10)
        stats = [
            ("Toplam İzleme Süresi", f"{data[6]} Dakika"),
            ("İzlenen Toplam İçerik Sayısı", f"{data[7]} Adet"),
            ("Verilen Ortalama Puan", f"{data[8]:.1f} / 10"),
            ("Favori Kategori Türleri", turler_str)
        ]
        
        for name, val in stats:
            f = ctk.CTkFrame(right_frame, fg_color="#333")
            f.pack(fill="x", pady=8, padx=10, ipady=8)
            ctk.CTkLabel(f, text=name, text_color="gray", font=("Arial", 13)).pack()
            ctk.CTkLabel(f, text=val, font=("Arial", 16, "bold"), text_color="#F1C40F", wraplength=350).pack()

    # -------------------------------------------------------------
    # İSTER H: İZLEME GEÇMİŞİ LİSTELEME
    # -------------------------------------------------------------
    def load_history(self):
        for w in self.main_view.winfo_children(): w.destroy()
        ctk.CTkLabel(self.main_view, text="📜 İzleme Geçmişi ve Loglar", font=("Arial", 26, "bold"), text_color="white").pack(anchor="w", pady=(5, 15))

        t_frame = ctk.CTkFrame(self.main_view)
        t_frame.pack(fill="both", expand=True, pady=10)
        
        cols = ("İçerik", "Tarih", "Bölüm", "Süre", "Puan", "Durum")
        tree = ttk.Treeview(t_frame, columns=cols, show="headings")
        for c in cols: tree.heading(c, text=c)
        
        tree.column("İçerik", width=300); tree.column("Tarih", width=150, anchor="center")
        tree.column("Bölüm", width=80, anchor="center"); tree.column("Süre", width=80, anchor="center")
        tree.column("Puan", width=80, anchor="center"); tree.column("Durum", width=120, anchor="center")
        
        scrollbar = ttk.Scrollbar(t_frame, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        tree.pack(fill="both", expand=True)

        u_id = self.master.current_user["id"]
        q = """
        SELECT p.ad, i.tarih, i.bolum_no, i.kalinan_dakika, i.puan, i.tamamlandi_mi
        FROM IzlemeLog i JOIN Program p ON i.program_id = p.id
        WHERE i.kullanici_id = ? ORDER BY i.id DESC
        """
        for r in db.fetch_all(q, (u_id,)):
            tarih = str(r[1])[:16] if r[1] else "-"
            durum = "Bölüm Bitti" if r[5] else "Yarım / Kaydedildi"
            tree.insert("", "end", values=(r[0], tarih, r[2] or 1, f"{r[3]} dk", f"{r[4]}/10", durum))

    # -------------------------------------------------------------
    # İSTER B: GELİŞMİŞ ÖNERİ ALGORİTMASI
    # -------------------------------------------------------------
    def load_recommendations(self):
        for w in self.main_view.winfo_children(): w.destroy()
        ctk.CTkLabel(self.main_view, text="💡 Sizin İçin Önerilen Yapımlar", font=("Arial", 26, "bold"), text_color="white").pack(anchor="w", pady=(5, 5))
        ctk.CTkLabel(self.main_view, text="Kayıt olurken seçtiğiniz favori türlerinize ve izleme istatistiklerinize göre derlenmiştir.", text_color="gray", font=("Arial", 13)).pack(anchor="w", pady=(0, 15))

        t_frame = ctk.CTkFrame(self.main_view)
        t_frame.pack(fill="both", expand=True, pady=10)

        tree = ttk.Treeview(t_frame, columns=("ID", "AD", "TIP", "YIL", "PUAN"), show="headings")
        tree.heading("ID", text="ID"); tree.heading("AD", text="Önerilen İçerik Adı"); tree.heading("TIP", text="Tip"); tree.heading("YIL", text="Yayın Yılı"); tree.heading("PUAN", text="Ort. Puan")
        tree.column("ID", width=60, anchor="center"); tree.column("AD", width=400); tree.column("TIP", width=120, anchor="center"); tree.column("YIL", width=100, anchor="center"); tree.column("PUAN", width=100, anchor="center")
        tree.pack(fill="both", expand=True)

        u_id = self.master.current_user["id"]
        # Kullanıcının türlerine uyan, daha önce izlemediği ve en yüksek puanlı içerikleri bul
        q = """
            SELECT DISTINCT TOP 20 p.id, p.ad, p.tip, p.yayin_yili, p.ortalama_puan 
            FROM Program p
            INNER JOIN ProgramTur pt ON p.id = pt.program_id
            WHERE pt.tur_id IN (SELECT tur_id FROM KullaniciTur WHERE kullanici_id = ?)
            AND p.id NOT IN (SELECT program_id FROM IzlemeLog WHERE kullanici_id = ?)
            ORDER BY p.ortalama_puan DESC
        """
        rows = db.fetch_all(q, (u_id, u_id))
        
        # Eğer sonuç yoksa en popüler 20 içeriği bas (Yedek Plan)
        if not rows: 
            rows = db.fetch_all("SELECT TOP 20 id, ad, tip, yayin_yili, ortalama_puan FROM Program ORDER BY izlenme_sayisi DESC")

        for r in rows: tree.insert("", "end", values=(r[0], r[1], r[2], r[3], r[4]))

    # -------------------------------------------------------------
    # İSTER A: ARAMA FİLTRELEME VE KATALOG
    # -------------------------------------------------------------
    def load_explore(self):
        for w in self.main_view.winfo_children(): w.destroy()
        ctk.CTkLabel(self.main_view, text="🍿 Küresel İçerik Kataloğu", font=("Arial", 26, "bold"), text_color="white").pack(anchor="w", pady=(5, 15))

        search_frame = ctk.CTkFrame(self.main_view, fg_color="transparent")
        search_frame.pack(fill="x", pady=5)

        self.search_entry = ctk.CTkEntry(search_frame, placeholder_text="İçerik Adı veya Yıl...", width=220, height=35)
        self.search_entry.pack(side="left", padx=5)

        self.type_combo = ctk.CTkComboBox(search_frame, values=["Tümü", "Film", "Dizi"], width=100, height=35)
        self.type_combo.pack(side="left", padx=5)
        
        # Türleri dinamik çeker (Eğer Tur tablosu bozuksa hata vermez)
        try:
            turler = ["Tüm Türler"] + [t[0] for t in db.fetch_all("SELECT TurAdi FROM Tur")]
        except:
            turler = ["Tüm Türler"]
            
        self.tur_combo = ctk.CTkComboBox(search_frame, values=turler, width=180, height=35)
        self.tur_combo.pack(side="left", padx=5)

        ctk.CTkButton(search_frame, text="🔍 Sistemi Filtrele", command=self.refresh_catalog, fg_color="#E50914", hover_color="#B80710", width=120, height=35).pack(side="left", padx=5)

        table_frame = ctk.CTkFrame(self.main_view)
        table_frame.pack(fill="both", expand=True, pady=10)
        scrollbar = ttk.Scrollbar(table_frame)
        scrollbar.pack(side="right", fill="y")

        cols = ("ID", "AD", "TIP", "YIL", "BOLUM", "UZUNLUK", "PUAN", "IZLENME")
        self.tree = ttk.Treeview(table_frame, columns=cols, show="headings", yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.tree.yview)

        for c in cols: self.tree.heading(c, text=c)
        self.tree.column("ID", width=50, anchor="center"); self.tree.column("AD", width=250)
        self.tree.column("TIP", width=80, anchor="center"); self.tree.column("YIL", width=80, anchor="center")
        self.tree.column("BOLUM", width=80, anchor="center"); self.tree.column("UZUNLUK", width=80, anchor="center")
        self.tree.column("PUAN", width=80, anchor="center"); self.tree.column("IZLENME", width=80, anchor="center")
        self.tree.pack(fill="both", expand=True)

        btn_frame = ctk.CTkFrame(self.main_view, fg_color="transparent")
        btn_frame.pack(fill="x", pady=10)

        ctk.CTkButton(btn_frame, text="▶️ Seçileni İzle Oynatıcıyı Aç", command=self.watch_content, fg_color="#2ECC71", font=("Arial", 14, "bold"), height=42).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="⭐ Favori Listeme İlave Et", command=self.add_to_favorites, fg_color="#F39C12", font=("Arial", 14, "bold"), height=42).pack(side="left", padx=5)

        self.refresh_catalog()

    def refresh_catalog(self):
        for item in self.tree.get_children(): self.tree.delete(item)

        txt = self.search_entry.get().strip()
        tip = self.type_combo.get()
        tur = self.tur_combo.get()

        query = """
        SELECT DISTINCT p.id, p.ad, p.tip, p.yayin_yili, p.bolum_sayisi, p.program_uzunlugu, p.ortalama_puan, p.izlenme_sayisi
        FROM Program p
        LEFT JOIN ProgramTur pt ON p.id = pt.program_id
        LEFT JOIN Tur t ON pt.tur_id = t.TurID
        WHERE 1=1
        """
        params = []
        if txt:
            query += " AND (p.ad LIKE ? OR p.yayin_yili LIKE ?)"
            params.extend([f"%{txt}%", f"%{txt}%"])
        if tip != "Tümü":
            query += " AND p.tip = ?"
            params.append(tip)
        if tur != "Tüm Türler":
            query += " AND t.TurAdi = ?"
            params.append(tur)

        # Tablodaki verilerin uyumsuz olma riskini minimize eden yapı
        rows = db.fetch_all(query, params)
        if not rows and not db.fetch_one("SELECT id FROM Program"):
            pass # Gerçekten tablo boş
            
        for r in rows: self.tree.insert("", "end", values=r)

    def add_to_favorites(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Eksik", "Lütfen bir içerik seçin.")
            return

        p_id = self.tree.item(selected[0], "values")[0]
        u_id = self.master.current_user["id"]

        if db.fetch_one("SELECT id FROM Favori WHERE kullanici_id=? AND program_id=?", (u_id, p_id)):
            messagebox.showinfo("Bilgi", "Bu içerik zaten favorilerinizde mevcut!")
            return

        db.execute_query("INSERT INTO Favori (kullanici_id, program_id) VALUES (?, ?)", (u_id, p_id))
        messagebox.showinfo("Başarılı", "İçerik favorilere eklendi.")

    def load_favorites(self):
        for w in self.main_view.winfo_children(): w.destroy()
        ctk.CTkLabel(self.main_view, text="⭐ Favorilerim", font=("Arial", 26, "bold"), text_color="white").pack(anchor="w", pady=(5, 15))

        tree = ttk.Treeview(self.main_view, columns=("ID", "AD", "TİP"), show="headings")
        tree.heading("ID", text="ID"); tree.heading("AD", text="İçerik Adı"); tree.heading("TİP", text="Tip")
        tree.column("ID", width=100, anchor="center"); tree.column("AD", width=400); tree.column("TİP", width=200, anchor="center")
        tree.pack(fill="both", expand=True, pady=10)

        u_id = self.master.current_user["id"]
        q = "SELECT p.id, p.ad, p.tip FROM Favori f JOIN Program p ON f.program_id = p.id WHERE f.kullanici_id = ?"
        for row in db.fetch_all(q, (u_id,)): tree.insert("", "end", values=row)

    # -------------------------------------------------------------
    # İSTER E: İZLEME EKRANI VE BÖLÜM SEÇME MANTIĞI
    # -------------------------------------------------------------
    def watch_content(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Seçim Yok", "Lütfen tablodan izlemek istediğiniz bir içeriği seçin.")
            return

        vals = self.tree.item(selected[0], "values")
        p_id, p_ad, p_tip = vals[0], vals[1], vals[2]
        tot_bolum, tot_sure = vals[4], vals[5]
        u_id = self.master.current_user["id"]

        # Kaldığı Yeri Veritabanından Bulma
        log = db.fetch_one("SELECT kalinan_dakika, bolum_no FROM IzlemeLog WHERE kullanici_id=? AND program_id=? ORDER BY id DESC", (u_id, p_id))
        last_time = log[0] if log else 0
        last_ep = log[1] if log else 1

        w_win = ctk.CTkToplevel(self)
        w_win.title("Gelişmiş İzleme Oynatıcı")
        w_win.geometry("500x650")
        w_win.attributes("-topmost", True)

        ctk.CTkLabel(w_win, text="📺 OYNATICI", font=("Arial Black", 14), text_color="gray").pack(pady=(15, 5))
        ctk.CTkLabel(w_win, text=p_ad, font=("Arial", 22, "bold"), text_color="#E50914").pack(pady=5)
        
        info = f"Tip: {p_tip}  |  Toplam Bölüm: {tot_bolum}  |  Süre: {tot_sure} Dk"
        ctk.CTkLabel(w_win, text=info, font=("Arial", 12), text_color="white").pack(pady=(0, 15))

        entry_bolum = None
        if p_tip == "Dizi":
            ctk.CTkLabel(w_win, text=f"Hafıza: En son {last_ep}. Bölüm, {last_time}. Dakikada kaldınız.", text_color="#F1C40F", font=("Arial", 11)).pack(pady=5)
            ctk.CTkLabel(w_win, text="Şu An İzlediğiniz Bölüm No:", font=("Arial", 13)).pack(pady=(10,2))
            entry_bolum = ctk.CTkEntry(w_win, width=280, height=35)
            entry_bolum.pack()
            entry_bolum.insert(0, str(last_ep))
        else:
            ctk.CTkLabel(w_win, text=f"Hafıza: En son {last_time}. Dakikada kaldınız.", text_color="#F1C40F", font=("Arial", 11)).pack(pady=5)

        ctk.CTkLabel(w_win, text="İzlediğiniz Süre (Dakika):", font=("Arial", 13)).pack(pady=(15,2))
        entry_dk = ctk.CTkEntry(w_win, width=280, height=35)
        entry_dk.pack()
        entry_dk.insert(0, str(last_time))

        ctk.CTkLabel(w_win, text="İçeriğe Puan Verin (1-10):", font=("Arial", 13)).pack(pady=(15,2))
        combo_puan = ctk.CTkComboBox(w_win, values=[str(x) for x in range(1, 11)], width=280, height=35)
        combo_puan.pack()

        def save_log(is_completed):
            dk = entry_dk.get().strip()
            puan = combo_puan.get()
            b_no = entry_bolum.get().strip() if entry_bolum else 1
            
            if not str(dk).isdigit(): dk = 0
            if not str(b_no).isdigit(): b_no = 1

            # Log Kaydı Atma
            q = "INSERT INTO IzlemeLog (kullanici_id, program_id, kalinan_dakika, puan, bolum_no, tamamlandi_mi) VALUES (?, ?, ?, ?, ?, ?)"
            db.execute_query(q, (u_id, p_id, int(dk), int(puan), int(b_no), is_completed))
            
            # Program İzlenme ve Puan İstatistiklerini Veritabanına Yansıtma
            db.execute_query("UPDATE Program SET izlenme_sayisi = izlenme_sayisi + 1 WHERE id=?", (p_id,))
            
            messagebox.showinfo("Başarılı", "İzleme durumu ve puanlama başarıyla kaydedildi.")
            w_win.destroy()
            self.refresh_catalog()

        ctk.CTkButton(w_win, text="⏸️ Kaldığım Yere Kaydet", command=lambda: save_log(0), fg_color="#F39C12", hover_color="#D35400", font=("Arial", 13, "bold"), height=42).pack(pady=(30,10))
        ctk.CTkButton(w_win, text="✅ İzlemeyi Tamamla", command=lambda: save_log(1), fg_color="#27AE60", hover_color="#218C53", font=("Arial", 13, "bold"), height=42).pack()


# =========================================================================
# 5. YÖNETİCİ PANELİ VE RAPORLAMA (ADMIN DASHBOARD)
# =========================================================================
class AdminDashboard(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master)
        self.master = master
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        sidebar = ctk.CTkFrame(self, width=230, corner_radius=0)
        sidebar.grid(row=0, column=0, sticky="nsew")

        ctk.CTkLabel(sidebar, text="YÖNETİCİ PANELİ", font=("Arial", 16, "bold"), text_color="#F1C40F").pack(pady=25)
        
        ctk.CTkButton(sidebar, text="🎬 Program Yönetimi", command=self.setup_crud_ui, fg_color="#333", font=("Arial", 13, "bold")).pack(pady=10, padx=15, fill="x")
        ctk.CTkButton(sidebar, text="👥 Sistem Kullanıcıları", command=self.load_user_management, fg_color="#333", font=("Arial", 13, "bold")).pack(pady=10, padx=15, fill="x")
        ctk.CTkButton(sidebar, text="📊 İstatistik Raporları", command=self.load_reports, fg_color="#333", font=("Arial", 13, "bold")).pack(pady=10, padx=15, fill="x")
        
        ctk.CTkButton(sidebar, text="Oturumu Kapat", fg_color="red", command=lambda: master.show_frame(LoginFrame)).pack(side="bottom", pady=25, padx=15, fill="x")

        self.main_view = ctk.CTkFrame(self, fg_color="#151515")
        self.main_view.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        
        self.setup_crud_ui()

    # -------------------------------------------------------------
    # İSTER C: KULLANICILARI LİSTELEME VE İZLEME İSTATİSTİKLERİ
    # -------------------------------------------------------------
    def load_user_management(self):
        for w in self.main_view.winfo_children(): w.destroy()
        ctk.CTkLabel(self.main_view, text="👥 Kullanıcı Analiz ve Kontrol Merkezi", font=("Arial", 26, "bold"), text_color="white").pack(anchor="w", pady=(0, 15))
        
        t_frame = ctk.CTkFrame(self.main_view)
        t_frame.pack(fill="both", expand=True)
        
        cols = ("ID", "Ad", "Soyad", "E-mail", "İzlenen İçerik", "Toplam Süre (Dk)", "Hesap Durumu")
        self.usr_tree = ttk.Treeview(t_frame, columns=cols, show="headings")
        for c in cols: self.usr_tree.heading(c, text=c)
        
        self.usr_tree.column("ID", width=50, anchor="center"); self.usr_tree.column("Ad", width=120); self.usr_tree.column("Soyad", width=120)
        self.usr_tree.column("E-mail", width=200); self.usr_tree.column("İzlenen İçerik", width=100, anchor="center"); self.usr_tree.column("Toplam Süre (Dk)", width=120, anchor="center"); self.usr_tree.column("Hesap Durumu", width=100, anchor="center")
        self.usr_tree.pack(fill="both", expand=True)

        self.refresh_users()

        btn_frame = ctk.CTkFrame(self.main_view, fg_color="transparent")
        btn_frame.pack(fill="x", pady=10)
        ctk.CTkButton(btn_frame, text="⛔ Seçili Kullanıcıyı Pasif Yap", fg_color="red", font=("Arial", 13, "bold"), height=35, command=self.ban_user).pack(side="left", padx=5)

    def refresh_users(self):
        self.usr_tree.delete(*self.usr_tree.get_children())
        q = """
        SELECT id, ad, soyad, email, 
               (SELECT COUNT(DISTINCT program_id) FROM IzlemeLog WHERE kullanici_id=Kullanici.id),
               (SELECT ISNULL(SUM(kalinan_dakika),0) FROM IzlemeLog WHERE kullanici_id=Kullanici.id),
               aktif_mi
        FROM Kullanici WHERE rol_id != 1
        """
        for r in db.fetch_all(q): 
            durum = "Aktif" if r[6] else "Pasif (Banlı)"
            self.usr_tree.insert("", "end", values=(r[0], r[1], r[2], r[3], r[4], r[5], durum))

    def ban_user(self):
        sel = self.usr_tree.selection()
        if not sel: return
        uid = self.usr_tree.item(sel[0], "values")[0]
        db.execute_query("UPDATE Kullanici SET aktif_mi = 0 WHERE id=?", (uid,))
        messagebox.showinfo("Bilgi", f"Sistem: ID'si {uid} olan kullanıcı başarıyla pasif duruma getirildi.")
        self.refresh_users()

    # -------------------------------------------------------------
    # İSTER D: ADMIN RAPORLARI (EN ÇOK İZLENEN / EN YÜKSEK PUAN)
    # -------------------------------------------------------------
    def load_reports(self):
        for w in self.main_view.winfo_children(): w.destroy()
        ctk.CTkLabel(self.main_view, text="📊 Platform Veri İstatistik Raporları", font=("Arial", 26, "bold"), text_color="white").pack(anchor="w", pady=(0, 15))
        
        ctrl_frame = ctk.CTkFrame(self.main_view, fg_color="transparent")
        ctrl_frame.pack(fill="x", pady=5)
        
        reps = [
            "En Çok İzlenen 10 İçerik", 
            "En Yüksek Puanlı 10 İçerik", 
            "En Aktif Kullanıcılar (Süreye Göre)",
            "Sistem Genel İşlem Özeti"
        ]
        combo = ctk.CTkComboBox(ctrl_frame, values=reps, width=300, height=35)
        combo.pack(side="left", padx=5)
        
        t_frame = ctk.CTkFrame(self.main_view)
        t_frame.pack(fill="both", expand=True, pady=10)
        tree = ttk.Treeview(t_frame, show="headings")
        tree.pack(fill="both", expand=True)
        
        def fetch_report():
            tree.delete(*tree.get_children())
            val = combo.get()
            
            if val == "En Çok İzlenen 10 İçerik":
                cols = ("İçerik Adı", "Toplam İzlenme / Tıklanma Sayısı")
                q = "SELECT TOP 10 p.ad, COUNT(i.id) as izlenme FROM Program p JOIN IzlemeLog i ON p.id = i.program_id GROUP BY p.ad ORDER BY izlenme DESC"
            elif val == "En Yüksek Puanlı 10 İçerik":
                cols = ("İçerik Adı", "Verilen Ortalama Puan")
                q = "SELECT TOP 10 p.ad, ROUND(AVG(CAST(i.puan AS FLOAT)),2) FROM Program p JOIN IzlemeLog i ON p.id = i.program_id WHERE i.puan > 0 GROUP BY p.ad ORDER BY 2 DESC"
            elif val == "En Aktif Kullanıcılar (Süreye Göre)":
                cols = ("Kullanıcı Adı ve Soyadı", "Toplam Geçirilen İzleme Süresi (Dk)")
                q = "SELECT TOP 10 (k.ad + ' ' + k.soyad), SUM(i.kalinan_dakika) FROM Kullanici k JOIN IzlemeLog i ON k.id = i.kullanici_id GROUP BY k.ad, k.soyad ORDER BY 2 DESC"
            else:
                cols = ("Sistem Metrikleri", "Değer")
                q = """
                SELECT 'Toplam Normal Kullanıcı Sayısı', COUNT(*) FROM Kullanici WHERE rol_id=2
                UNION ALL SELECT 'Toplam İzlenme Kaydı (Log Adedi)', COUNT(*) FROM IzlemeLog
                UNION ALL SELECT 'Verilen Toplam Puan Adedi', COUNT(*) FROM IzlemeLog WHERE puan > 0
                """
            
            tree.configure(columns=cols)
            for c in cols: 
                tree.heading(c, text=c)
                tree.column(c, anchor="w", width=350)
                
            for r in db.fetch_all(q): tree.insert("", "end", values=r)
                
        ctk.CTkButton(ctrl_frame, text="Raporu Üret ve Listele", command=fetch_report, fg_color="#E50914", height=35).pack(side="left", padx=5)
        fetch_report()

    # -------------------------------------------------------------
    # ORİJİNAL CRUD İŞLEMLERİ (790 SATIRLIK KUSURSUZ YAPI DOKUNULMADAN)
    # -------------------------------------------------------------
    def setup_crud_ui(self):
        for w in self.main_view.winfo_children(): w.destroy()
        ctk.CTkLabel(self.main_view, text="🎬 Program Kataloğu Yönetim Merkezi (CRUD)", font=("Arial", 26, "bold"), text_color="white").pack(anchor="w", pady=(0, 15))

        form = ctk.CTkFrame(self.main_view)
        form.pack(fill="x", pady=5, ipadx=10, ipady=10)

        self.in_id = ctk.CTkEntry(form, placeholder_text="ID (Güncelleme/Silme için)", height=35)
        self.in_id.grid(row=0, column=0, padx=8, pady=8)
        self.in_ad = ctk.CTkEntry(form, placeholder_text="Program Adı", width=220, height=35)
        self.in_ad.grid(row=0, column=1, padx=8, pady=8)
        self.in_tip = ctk.CTkComboBox(form, values=["Film", "Dizi"], width=130, height=35)
        self.in_tip.grid(row=0, column=2, padx=8, pady=8)
        self.in_yil = ctk.CTkEntry(form, placeholder_text="Yıl (Örn: 2024)", height=35)
        self.in_yil.grid(row=0, column=3, padx=8, pady=8)

        actions = ctk.CTkFrame(self.main_view, fg_color="transparent")
        actions.pack(fill="x", pady=10)

        ctk.CTkButton(actions, text="➕ Kataloğa Ekle (Create)", fg_color="#27AE60", font=("Arial", 13, "bold"), height=35, command=self.create_item).pack(side="left", padx=5)
        ctk.CTkButton(actions, text="✏️ Güncelle (Update)", fg_color="#E67E22", font=("Arial", 13, "bold"), height=35, command=self.update_item).pack(side="left", padx=5)
        ctk.CTkButton(actions, text="🗑️ Sistemden Sil (Delete)", fg_color="#C0392B", font=("Arial", 13, "bold"), height=35, command=self.delete_item).pack(side="left", padx=5)

        self.txt_display = ctk.CTkTextbox(self.main_view, font=("Consolas", 13), fg_color="#1E1E1E", text_color="#2ECC71")
        self.txt_display.pack(fill="both", expand=True, pady=10)

        self.read_items()

    def read_items(self):
        self.txt_display.delete("1.0", "end")
        data = db.fetch_all("SELECT id, ad, tip, yayin_yili FROM Program")
        self.txt_display.insert("end", f"{'ID':<6} | {'TÜR':<8} | {'YIL':<6} | {'İÇERİK ADI':<40}\n")
        self.txt_display.insert("end", "-" * 80 + "\n")
        for r in data:
            self.txt_display.insert("end", f"[{r[0]:<3}] | {r[2]:<8} | {r[3]:<6} | {r[1]}\n")

    def create_item(self):
        ad = self.in_ad.get().strip()
        tip = self.in_tip.get()
        yil = self.in_yil.get().strip()

        if not (ad and yil.isdigit()):
            messagebox.showwarning("Geçersiz Girdi", "Program Adı ve Yıl alanı (sayısal) zorunludur.")
            return

        suc, _ = db.execute_query("INSERT INTO Program (ad, tip, yayin_yili) VALUES (?, ?, ?)", (ad, tip, int(yil)))
        if suc:
            self.read_items()
            messagebox.showinfo("Başarılı", "İçerik veritabanı kataloğuna eklendi.")

    def update_item(self):
        p_id = self.in_id.get().strip()
        ad = self.in_ad.get().strip()
        tip = self.in_tip.get()
        yil = self.in_yil.get().strip()

        if not (p_id.isdigit() and ad and yil.isdigit()):
            messagebox.showwarning("Eksik Veri", "Güncelleme için geçerli bir ID ve yeni veriler girmelisiniz.")
            return
            
        suc, _ = db.execute_query("UPDATE Program SET ad=?, tip=?, yayin_yili=? WHERE id=?", (ad, tip, int(yil), int(p_id)))
        if suc: 
            self.read_items()
            messagebox.showinfo("Başarılı", "İçerik güncellendi.")

    def delete_item(self):
        p_id = self.in_id.get().strip()
        if not p_id.isdigit(): return
        if messagebox.askyesno("Kalıcı Silme Onayı", "İçeriği kalıcı olarak silmek istiyor musunuz?"):
            suc, _ = db.execute_query("DELETE FROM Program WHERE id=?", (int(p_id),))
            if suc: 
                self.read_items()
                messagebox.showinfo("Başarılı", "İçerik silindi.")

# =========================================================================
# 6. UYGULAMA TETİKLEYİCİ
# =========================================================================
if __name__ == "__main__":
    app = NetflixApp()
    app.mainloop()