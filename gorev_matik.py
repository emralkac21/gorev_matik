import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from ttkthemes import ThemedTk
import sqlite3
from datetime import datetime
from PIL import Image, ImageTk
import pandas as pd
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from tkcalendar import DateEntry
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
import os

# --- VERİTABANI İŞLEMLERİ ---

def veritabani_kur():
    """Veritabanını ve gerekli tabloları oluşturur."""
    conn = sqlite3.connect('okul_veritabani.db')
    cursor = conn.cursor()
    # Öğretmenler Tablosu
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Ogretmenler (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ad_soyad TEXT NOT NULL UNIQUE,
        brans TEXT NOT NULL,
        toplam_gorev_sayisi INTEGER DEFAULT 0
    )
    ''')
    # Dersler Tablosu
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Dersler (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ders_adi TEXT NOT NULL UNIQUE
    )
    ''')
    # Sınav Görevleri Tablosu
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS SinavGorevleri (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ders_adi TEXT NOT NULL,
        komisyon_uyesi TEXT NOT NULL,
        uye_yardimcisi TEXT NOT NULL,
        gozcu TEXT NOT NULL,
        sinav_tarihi TEXT NOT NULL
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS OgretmenDersYetkinlikleri (
        ogretmen_id INTEGER NOT NULL,
        ders_id INTEGER NOT NULL,
        FOREIGN KEY (ogretmen_id) REFERENCES Ogretmenler(id) ON DELETE CASCADE,
        FOREIGN KEY (ders_id) REFERENCES Dersler(id) ON DELETE CASCADE,
        PRIMARY KEY (ogretmen_id, ders_id)
    )
    ''')
    
    # Öğrenci Tablosu
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Ogrenciler (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ad TEXT NOT NULL,
        soyad TEXT NOT NULL,
        sinif TEXT,
        sorumlu_ders_id INTEGER NOT NULL,
        ders_sinif_duzeyi INTEGER NOT NULL,
        FOREIGN KEY (sorumlu_ders_id) REFERENCES Dersler(id) ON DELETE CASCADE
    )
    ''')

    conn.commit()
    conn.close()

# --- ANA UYGULAMA SINIFI ---

class SinavGorevUygulamasi:
    def __init__(self, root):
        self.root = root
        self.root.title("Sınavmatik")
        self.root.geometry("1200x800")
        self.root.minsize(1000, 700)

        # Tema ve stil
        self.style = ttk.Style()
        self.style.configure("Menu.TButton", padding=(20, 10), font=('Arial', 11), anchor="w")
        self.style.configure("Header.TLabel", font=('Arial', 18, 'bold'), foreground="#999")
        
        # DEĞİŞTİRİLDİ: Buton stilini daha güvenilir bir yöntemle ayarla
        # Bu yöntem, temanın butonun arka planını ve yazı rengini ezmesini engeller.
        self.style.map("Accent.TButton",
            foreground=[('pressed', 'red'), ('active', 'black'), ('!disabled', 'black')],
            background=[('pressed', '!focus', "#009e42"), ('active', '#006cc1'), ('!disabled', '#0078D7')]
        )

        # Ana Arayüz Yapısı
        self.paned_window = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        self.paned_window.pack(fill=tk.BOTH, expand=True)

        self.menu_frame = ttk.Frame(self.paned_window, width=220)
        self.paned_window.add(self.menu_frame, weight=1)

        self.content_frame = ttk.Frame(self.paned_window)
        self.paned_window.add(self.content_frame, weight=5)

        self.ikonlari_yukle()
        self.menu_olustur()
        
        self.gorev_atama_ekranini_goster()

    def ikonlari_yukle(self):
        """İkonları yükle (yoksa boş bırak)"""
        try:
            # İkon dosyalarınızın bulunduğu klasörün adını "icons" olarak varsayıyoruz.
            self.icon_assign = ImageTk.PhotoImage(Image.open("icons/assign.png").resize((20, 20)))
            self.icon_teacher = ImageTk.PhotoImage(Image.open("icons/add_user.png").resize((20, 20)))
            self.icon_student = ImageTk.PhotoImage(Image.open("icons/student.png").resize((20, 20)))
            self.icon_lesson = ImageTk.PhotoImage(Image.open("icons/add_book.png").resize((20, 20)))
            self.icon_history = ImageTk.PhotoImage(Image.open("icons/history.png").resize((20, 20)))
            self.root.iconphoto(False, ImageTk.PhotoImage(Image.open("icons/main_icon.png")))
        except Exception as e:
            print(f"İkonlar yüklenemedi: {e}. İkonlar olmadan devam edilecek.")
            self.icon_assign = self.icon_teacher = self.icon_lesson = self.icon_history = self.icon_student = None

    def menu_olustur(self):
        """Sol menü butonlarını oluştur"""
        ttk.Button(self.menu_frame, text=" Sınav Görevi Ata", 
                  image=self.icon_assign, compound="left", style="Menu.TButton", 
                  command=self.gorev_atama_ekranini_goster).pack(fill='x', padx=5, pady=5)
        
        ttk.Button(self.menu_frame, text=" Görev Geçmişi", 
                  image=self.icon_history, compound="left", style="Menu.TButton", 
                  command=self.gorev_gecmisi_ekranini_goster).pack(fill='x', padx=5, pady=5)
        
        ttk.Button(self.menu_frame, text=" Öğretmen Yönetimi", 
                  image=self.icon_teacher, compound="left", style="Menu.TButton", 
                  command=self.ogretmen_yonetim_ekranini_goster).pack(fill='x', padx=5, pady=5)
        
        ttk.Button(self.menu_frame, text=" Öğrenci Yönetimi", 
                  image=self.icon_student, compound="left", style="Menu.TButton", 
                  command=self.ogrenci_yonetim_ekranini_goster).pack(fill='x', padx=5, pady=5)
        
        ttk.Button(self.menu_frame, text=" Ders Yönetimi", 
                  image=self.icon_lesson, compound="left", style="Menu.TButton", 
                  command=self.ders_yonetim_ekranini_goster).pack(fill='x', padx=5, pady=5)
    
    def icerik_alanini_temizle(self):
        """İçerik alanındaki tüm widget'ları temizle"""
        for widget in self.content_frame.winfo_children():
            widget.destroy()
    
    def gorev_atama_ekranini_goster(self):
        self.icerik_alanini_temizle()
        frame = ttk.Frame(self.content_frame, padding=20)
        frame.pack(fill="both", expand=True)
        
        ttk.Label(frame, text="Sınav Görevi Atama", style="Header.TLabel").pack(pady=(0, 20))
        
        conn = sqlite3.connect('okul_veritabani.db')
        cursor = conn.cursor()
        cursor.execute("SELECT ders_adi FROM Dersler ORDER BY ders_adi")
        dersler = [row[0] for row in cursor.fetchall()]
        
        cursor.execute("SELECT ad_soyad FROM Ogretmenler ORDER BY ad_soyad")
        ogretmenler = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        if not dersler or len(ogretmenler) < 3:
            ttk.Label(frame, text="Atama yapmak için sistemde kayıtlı en az 1 ders ve 3 öğretmen olmalıdır.", 
                     foreground="red").pack(pady=10)
            return

        bilgi_frame = ttk.LabelFrame(frame, text="1. Sınav Bilgilerini Seçin")
        bilgi_frame.pack(fill="x", pady=10, padx=20)

        ttk.Label(bilgi_frame, text="Ders:").grid(row=0, column=0, padx=10, pady=10, sticky="w")
        self.secilen_ders = tk.StringVar()
        ders_combobox = ttk.Combobox(bilgi_frame, textvariable=self.secilen_ders, values=dersler, 
                                    state="readonly", font=('Arial', 12), width=30)
        ders_combobox.grid(row=0, column=1, padx=10, pady=10)
        
        ttk.Label(bilgi_frame, text="Sınav Tarihi:").grid(row=1, column=0, padx=10, pady=10, sticky="w")
        self.sinav_tarihi = DateEntry(bilgi_frame, width=12, background='darkblue',
                                     foreground='white', borderwidth=2, locale='tr_TR', 
                                     date_pattern='dd/MM/yyyy')
        self.sinav_tarihi.grid(row=1, column=1, padx=10, pady=10, sticky="w")

        ttk.Label(bilgi_frame, text="Sınav Saati:").grid(row=2, column=0, padx=10, pady=10, sticky="w")
        saat_frame = ttk.Frame(bilgi_frame)
        saat_frame.grid(row=2, column=1, padx=10, pady=10, sticky="w")
        
        self.saat = ttk.Spinbox(saat_frame, from_=8, to=17, width=5, format="%02.0f")
        self.saat.set("09")
        self.saat.pack(side="left")
        ttk.Label(saat_frame, text=":").pack(side="left", padx=5)
        self.dakika = ttk.Spinbox(saat_frame, from_=0, to=59, increment=15, width=5, format="%02.0f")
        self.dakika.set("00")
        self.dakika.pack(side="left")
        
        manuel_frame = ttk.LabelFrame(frame, text="2. Manuel Görev Atama")
        manuel_frame.pack(fill="x", pady=20, padx=20)

        ttk.Label(manuel_frame, text="Komisyon Üyesi:").grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.komisyon_uyesi_combo = ttk.Combobox(manuel_frame, values=ogretmenler, state="readonly", width=30)
        self.komisyon_uyesi_combo.grid(row=0, column=1, padx=10, pady=5)
        
        ttk.Label(manuel_frame, text="Üye Yardımcısı:").grid(row=1, column=0, padx=10, pady=5, sticky="w")
        self.uye_yardimcisi_combo = ttk.Combobox(manuel_frame, values=ogretmenler, state="readonly", width=30)
        self.uye_yardimcisi_combo.grid(row=1, column=1, padx=10, pady=5)
        
        ttk.Label(manuel_frame, text="Gözcü:").grid(row=2, column=0, padx=10, pady=5, sticky="w")
        self.gozcu_combo = ttk.Combobox(manuel_frame, values=ogretmenler, state="readonly", width=30)
        self.gozcu_combo.grid(row=2, column=1, padx=10, pady=5)
        
        ttk.Button(manuel_frame, text="Manuel Görevi Kaydet", 
                  command=self.manuel_gorevi_kaydet).grid(row=3, columnspan=2, pady=15)

        otomatik_frame = ttk.LabelFrame(frame, text="Veya Otomatik Görev Ata")
        otomatik_frame.pack(fill="x", pady=10, padx=20)
        
        ttk.Button(otomatik_frame, text="Görevleri Otomatik Ata", 
                  command=self.gorevleri_ata, style="Accent.TButton").pack(pady=15)
        
    def manuel_gorevi_kaydet(self):
        secili_ders = self.secilen_ders.get()
        komisyon_uyesi = self.komisyon_uyesi_combo.get()
        uye_yardimcisi = self.uye_yardimcisi_combo.get()
        gozcu = self.gozcu_combo.get()

        if not secili_ders: messagebox.showwarning("Uyarı", "Lütfen bir ders seçin."); return
        try:
            secilen_tarih = self.sinav_tarihi.get_date()
            tam_tarih = f"{secilen_tarih.strftime('%d/%m/%Y')} {self.saat.get()}:{self.dakika.get()}"
        except Exception: messagebox.showerror("Hata", "Lütfen geçerli bir tarih ve saat girin."); return

        if not all([komisyon_uyesi, uye_yardimcisi, gozcu]): messagebox.showwarning("Uyarı", "Lütfen tüm görevler için bir öğretmen seçin."); return
        if len(set([komisyon_uyesi, uye_yardimcisi, gozcu])) != 3: messagebox.showwarning("Hata", "Bir öğretmen aynı sınavda birden fazla görev alamaz."); return

        conn = sqlite3.connect('okul_veritabani.db'); cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO SinavGorevleri (ders_adi, komisyon_uyesi, uye_yardimcisi, gozcu, sinav_tarihi) VALUES (?, ?, ?, ?, ?)", (secili_ders, komisyon_uyesi, uye_yardimcisi, gozcu, tam_tarih))
            for ogretmen_adi in [komisyon_uyesi, uye_yardimcisi, gozcu]:
                cursor.execute("UPDATE Ogretmenler SET toplam_gorev_sayisi = toplam_gorev_sayisi + 1 WHERE ad_soyad = ?", (ogretmen_adi,))
            conn.commit()
            messagebox.showinfo("Başarılı", "Görev ataması başarıyla kaydedildi.")
            self.secilen_ders.set(''); self.komisyon_uyesi_combo.set(''); self.uye_yardimcisi_combo.set(''); self.gozcu_combo.set('')
        except Exception as e: conn.rollback(); messagebox.showerror("Veritabanı Hatası", f"Kayıt sırasında bir hata oluştu: {e}")
        finally: conn.close()

    def gorev_gecmisi_ekranini_goster(self):
        self.icerik_alanini_temizle()
        frame = ttk.Frame(self.content_frame, padding=10); frame.pack(fill="both", expand=True)
        ust_frame = ttk.Frame(frame); ust_frame.pack(fill='x', pady=(0, 10))
        ttk.Label(ust_frame, text="Sınav Görev Geçmişi", style="Header.TLabel").pack(side="left")

        button_frame = ttk.Frame(ust_frame); button_frame.pack(side="right")
        ttk.Button(button_frame, text="Sorumlu Öğrencileri Aktar", command=self.sorumlu_ogrencileri_aktar, style="Accent.TButton").pack(side="right", padx=5)
        ttk.Button(button_frame, text="Excel'e Aktar", command=self.excel_aktar).pack(side="right", padx=5)
        ttk.Button(button_frame, text="PDF'e Aktar", command=self.pdf_aktar).pack(side="right", padx=5)
        ttk.Button(button_frame, text="Seçili Kaydı Sil", command=self.gorev_kaydini_sil).pack(side="right", padx=5)
        
        arama_frame = ttk.LabelFrame(frame, text="Filtrele (Öğretmen veya Ders Adına Göre)"); arama_frame.pack(fill='x', padx=10, pady=10)
        self.arama_entry = ttk.Entry(arama_frame); self.arama_entry.pack(side='left', fill='x', expand=True, padx=5, pady=5); self.arama_entry.bind("<KeyRelease>", self.gorev_gecmisini_guncelle)

        tree_frame = ttk.Frame(frame); tree_frame.pack(fill="both", expand=True, padx=10, pady=10)
        self.gorev_tree = ttk.Treeview(tree_frame, columns=("id", "ders_adi", "komisyon_uye", "uye_yardimci", "gozcu", "tarih"), show="headings")
        self.gorev_tree.heading("id", text="ID"); self.gorev_tree.heading("ders_adi", text="Ders Adı"); self.gorev_tree.heading("komisyon_uye", text="Komisyon Üyesi"); self.gorev_tree.heading("uye_yardimci", text="Üye Yardımcısı"); self.gorev_tree.heading("gozcu", text="Gözcü"); self.gorev_tree.heading("tarih", text="Sınav Tarihi")
        self.gorev_tree.column("id", width=40, anchor="center"); self.gorev_tree.pack(side="left", fill="both", expand=True)
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.gorev_tree.yview); self.gorev_tree.configure(yscrollcommand=scrollbar.set); scrollbar.pack(side="right", fill="y")
        self.gorev_gecmisini_guncelle()

    def gorev_gecmisini_guncelle(self, event=None):
        arama_terimi = self.arama_entry.get().strip() if hasattr(self, 'arama_entry') else ""
        for i in self.gorev_tree.get_children(): self.gorev_tree.delete(i)
        conn = sqlite3.connect('okul_veritabani.db'); cursor = conn.cursor()
        query = "SELECT id, ders_adi, komisyon_uyesi, uye_yardimcisi, gozcu, sinav_tarihi FROM SinavGorevleri"
        params = []
        if arama_terimi:
            query += " WHERE ders_adi LIKE ? OR komisyon_uyesi LIKE ? OR uye_yardimcisi LIKE ? OR gozcu LIKE ?"
            params = [f'%{arama_terimi}%'] * 4
        query += " ORDER BY sinav_tarihi DESC"
        cursor.execute(query, params)
        for row in cursor.fetchall(): self.gorev_tree.insert("", "end", values=row)
        conn.close()

    def sorumlu_ogrencileri_aktar(self):
        selected_item = self.gorev_tree.selection()
        if not selected_item: messagebox.showwarning("Uyarı", "Lütfen bir sınav kaydı seçin."); return
        secili_sinav_dersi = self.gorev_tree.item(selected_item[0], 'values')[1]

        try:
            conn = sqlite3.connect('okul_veritabani.db')
            query = """
            SELECT o.ad as 'Öğrenci Adı', o.soyad as 'Öğrenci Soyadı', o.sinif as 'Sınıfı', o.ders_sinif_duzeyi as 'Sorumlu Olduğu Sınıf Düzeyi'
            FROM Ogrenciler o JOIN Dersler d ON o.sorumlu_ders_id = d.id
            WHERE d.ders_adi = ? ORDER BY o.sinif, o.soyad, o.ad
            """
            df = pd.read_sql_query(query, conn, params=(secili_sinav_dersi,)); conn.close()
            if df.empty: messagebox.showinfo("Bilgi", f"'{secili_sinav_dersi}' dersinden sorumlu öğrenci bulunamadı."); return
            
            dosya_yolu = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel dosyaları", "*.xlsx")], title=f"{secili_sinav_dersi} Sorumlu Öğrenci Listesi", initialfile=f"{secili_sinav_dersi}_sorumlu_ogrenciler.xlsx")
            if dosya_yolu: df.to_excel(dosya_yolu, index=False); messagebox.showinfo("Başarılı", f"Öğrenci listesi başarıyla aktarıldı.")
        except Exception as e: messagebox.showerror("Hata", f"Excel'e aktarma sırasında hata: {e}")

    def excel_aktar(self):
        try:
            conn = sqlite3.connect('okul_veritabani.db')
            df = pd.read_sql_query("SELECT ders_adi as 'Ders', komisyon_uyesi as 'Komisyon Üyesi', uye_yardimcisi as 'Üye Yardımcısı', gozcu as 'Gözcü', sinav_tarihi as 'Sınav Tarihi' FROM SinavGorevleri ORDER BY sinav_tarihi DESC", conn); conn.close()
            dosya_yolu = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel dosyaları", "*.xlsx")], title="Excel dosyasını kaydet")
            if dosya_yolu: df.to_excel(dosya_yolu, index=False); messagebox.showinfo("Başarılı", f"Veriler başarıyla aktarıldı.")
        except Exception as e: messagebox.showerror("Hata", f"Excel aktarımı sırasında hata: {e}")

    def pdf_aktar(self):
        dosya_yolu = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF dosyaları", "*.pdf")], title="PDF dosyasını kaydet")
        if not dosya_yolu: return
        try:
            pdfmetrics.registerFont(TTFont('DejaVu', 'DejaVuSans.ttf'))
            conn = sqlite3.connect('okul_veritabani.db'); cursor = conn.cursor()
            cursor.execute("SELECT ders_adi, komisyon_uyesi, uye_yardimcisi, gozcu, sinav_tarihi FROM SinavGorevleri ORDER BY sinav_tarihi DESC"); veriler = cursor.fetchall(); conn.close()
            doc = SimpleDocTemplate(dosya_yolu, pagesize=A4); styles = getSampleStyleSheet()
            style_title = ParagraphStyle(name='TitleStyle', parent=styles['h2'], fontName='DejaVu', alignment=TA_LEFT)
            style_body = ParagraphStyle(name='BodyStyle', parent=styles['Normal'], fontName='DejaVu', alignment=TA_CENTER)
            flowables = [Paragraph("Sınav Görev Dağıtım Listesi", style_title), Paragraph(f"Tarih: {datetime.now().strftime('%d/%m/%Y')}", styles['Normal']), Spacer(1, 20)]
            data = [["Ders", "Komisyon Üyesi", "Üye Yardımcısı", "Gözcü", "Sınav Tarihi"]]; data.extend([[Paragraph(str(cell), style_body) for cell in row] for row in veriler])
            table = Table(data, colWidths=[100, 100, 100, 100, 80])
            table.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), colors.orange), ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke), ('ALIGN', (0, 0), (-1, -1), 'CENTER'), ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'), ('FONTNAME', (0, 0), (-1, 0), 'DejaVu'), ('FONTNAME', (0, 1), (-1, -1), 'DejaVu'), ('BOTTOMPADDING', (0, 0), (-1, 0), 12), ('GRID', (0, 0), (-1, -1), 1, colors.black)]))
            flowables.append(table); doc.build(flowables)
            messagebox.showinfo("Başarılı", f"PDF başarıyla kaydedildi.")
        except FileNotFoundError: messagebox.showerror("Hata", "Font dosyası bulunamadı! 'DejaVuSans.ttf' dosyasının programla aynı klasörde olduğundan emin olun.")
        except Exception as e: messagebox.showerror("Hata", f"PDF oluşturma hatası: {e}")

    def gorev_kaydini_sil(self):
        selected_item = self.gorev_tree.selection()
        if not selected_item: messagebox.showwarning("Uyarı", "Lütfen silmek için bir görev kaydı seçin."); return
        if messagebox.askyesno("Onay", "Seçili kaydı silmek istediğinizden emin misiniz?\n(İlgili öğretmenlerin görev sayısı 1 azaltılacaktır.)"):
            conn = sqlite3.connect('okul_veritabani.db'); cursor = conn.cursor()
            try:
                values = self.gorev_tree.item(selected_item[0], 'values'); gorev_id = values[0]
                ogretmenler_listesi = values[2:5] # Komisyon üyesi, yardımcısı ve gözcü
                for ogretmen_adi in ogretmenler_listesi:
                    cursor.execute("UPDATE Ogretmenler SET toplam_gorev_sayisi = toplam_gorev_sayisi - 1 WHERE ad_soyad = ? AND toplam_gorev_sayisi > 0", (ogretmen_adi,))
                cursor.execute("DELETE FROM SinavGorevleri WHERE id = ?", (gorev_id,)); conn.commit()
                messagebox.showinfo("Başarılı", "Kayıt silindi ve görev sayıları güncellendi.")
            except Exception as e: conn.rollback(); messagebox.showerror("Hata", f"Silme işlemi hatası: {e}")
            finally: conn.close(); self.gorev_gecmisini_guncelle()

    def ogretmen_yonetim_ekranini_goster(self):
        self.icerik_alanini_temizle(); frame = ttk.Frame(self.content_frame, padding=10); frame.pack(fill="both", expand=True)
        form_frame = ttk.LabelFrame(frame, text="Yeni Öğretmen Ekle / Güncelle"); form_frame.pack(fill="x", pady=10, padx=10)
        ttk.Label(form_frame, text="Ad Soyad:").grid(row=0, column=0, padx=5, pady=5, sticky="w"); self.ogretmen_ad_entry = ttk.Entry(form_frame, width=30); self.ogretmen_ad_entry.grid(row=0, column=1, padx=5, pady=5)
        ttk.Label(form_frame, text="Branş:").grid(row=1, column=0, padx=5, pady=5, sticky="w"); self.ogretmen_brans_entry = ttk.Entry(form_frame, width=30); self.ogretmen_brans_entry.grid(row=1, column=1, padx=5, pady=5)
        btn_frame = ttk.Frame(form_frame); btn_frame.grid(row=2, columnspan=2, pady=10)
        ttk.Button(btn_frame, text="Ekle", command=self.ogretmen_ekle).pack(side="left", padx=5); ttk.Button(btn_frame, text="Güncelle", command=self.ogretmen_guncelle).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Sil", command=self.ogretmen_sil).pack(side="left", padx=5); ttk.Button(btn_frame, text="Formu Temizle", command=self.ogretmen_formu_temizle).pack(side="left", padx=5)
        ders_yonetim_frame = ttk.LabelFrame(frame, text="Görev Alabileceği Dersleri Yönet"); ders_yonetim_frame.pack(fill="x", expand=True, padx=10, pady=10)
        sol_frame = ttk.Frame(ders_yonetim_frame); sol_frame.pack(side="left", fill="both", expand=True, padx=5, pady=5); ttk.Label(sol_frame, text="Tüm Dersler").pack(); self.tum_dersler_listbox = tk.Listbox(sol_frame, selectmode=tk.EXTENDED, exportselection=False); self.tum_dersler_listbox.pack(fill="both", expand=True)
        orta_frame = ttk.Frame(ders_yonetim_frame); orta_frame.pack(side="left", fill="y", padx=5); ttk.Button(orta_frame, text="Ekle >>", command=self.ders_ata).pack(pady=10); ttk.Button(orta_frame, text="<< Çıkar", command=self.ders_cikar).pack(pady=10)
        sag_frame = ttk.Frame(ders_yonetim_frame); sag_frame.pack(side="left", fill="both", expand=True, padx=5, pady=5); ttk.Label(sag_frame, text="Atanan Dersler").pack(); self.atanan_dersler_listbox = tk.Listbox(sag_frame, selectmode=tk.EXTENDED, exportselection=False); self.atanan_dersler_listbox.pack(fill="both", expand=True)
        tree_frame = ttk.Frame(frame); tree_frame.pack(fill="both", expand=True, padx=10, pady=10); self.ogretmen_tree = ttk.Treeview(tree_frame, columns=("id", "ad_soyad", "brans", "gorev_sayisi"), show="headings"); self.ogretmen_tree.heading("id", text="ID"); self.ogretmen_tree.heading("ad_soyad", text="Ad Soyad"); self.ogretmen_tree.heading("brans", text="Branş"); self.ogretmen_tree.heading("gorev_sayisi", text="Görev Sayısı"); self.ogretmen_tree.column("id", width=50, anchor="center"); self.ogretmen_tree.column("gorev_sayisi", width=100, anchor="center"); self.ogretmen_tree.pack(side="left", fill="both", expand=True)
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.ogretmen_tree.yview); self.ogretmen_tree.configure(yscrollcommand=scrollbar.set); scrollbar.pack(side="right", fill="y")
        self.ogretmen_tree.bind("<<TreeviewSelect>>", self.ogretmen_sec); self.ogretmen_listesini_guncelle()
        
    def ders_ata(self):
        for i in reversed(self.tum_dersler_listbox.curselection()): self.atanan_dersler_listbox.insert(tk.END, self.tum_dersler_listbox.get(i)); self.tum_dersler_listbox.delete(i)
    def ders_cikar(self):
        for i in reversed(self.atanan_dersler_listbox.curselection()): self.tum_dersler_listbox.insert(tk.END, self.atanan_dersler_listbox.get(i)); self.atanan_dersler_listbox.delete(i)
    def ogretmen_formu_temizle(self):
        self.ogretmen_ad_entry.delete(0, 'end'); self.ogretmen_brans_entry.delete(0, 'end'); self.tum_dersler_listbox.delete(0, 'end'); self.atanan_dersler_listbox.delete(0, 'end')
        if self.ogretmen_tree.selection(): self.ogretmen_tree.selection_remove(self.ogretmen_tree.selection()[0])
    def ogretmen_sec(self, event):
        if not self.ogretmen_tree.selection(): return
        values = self.ogretmen_tree.item(self.ogretmen_tree.selection()[0], 'values')
        self.ogretmen_ad_entry.delete(0, 'end'); self.ogretmen_ad_entry.insert(0, values[1]); self.ogretmen_brans_entry.delete(0, 'end'); self.ogretmen_brans_entry.insert(0, values[2])
        self.tum_dersler_listbox.delete(0, 'end'); self.atanan_dersler_listbox.delete(0, 'end')
        conn = sqlite3.connect('okul_veritabani.db'); cursor = conn.cursor()
        cursor.execute("SELECT id, ders_adi FROM Dersler ORDER BY ders_adi"); tum_dersler = cursor.fetchall(); self.ders_id_map = {ders_adi: ders_id for ders_id, ders_adi in tum_dersler}
        cursor.execute("SELECT ders_id FROM OgretmenDersYetkinlikleri WHERE ogretmen_id = ?", (values[0],)); atanan_ders_idler = {row[0] for row in cursor.fetchall()}; conn.close()
        for ders_id, ders_adi in tum_dersler: (self.atanan_dersler_listbox if ders_id in atanan_ders_idler else self.tum_dersler_listbox).insert(tk.END, ders_adi)
    def ogretmen_listesini_guncelle(self):
        for i in self.ogretmen_tree.get_children(): self.ogretmen_tree.delete(i)
        conn = sqlite3.connect('okul_veritabani.db'); cursor = conn.cursor(); cursor.execute("SELECT * FROM Ogretmenler ORDER BY ad_soyad")
        for row in cursor.fetchall(): self.ogretmen_tree.insert("", "end", values=row)
        conn.close()
    def ogretmen_ekle(self):
        ad = self.ogretmen_ad_entry.get().strip(); brans = self.ogretmen_brans_entry.get().strip()
        if not ad or not brans: messagebox.showwarning("Uyarı", "Ad Soyad ve Branş boş bırakılamaz!"); return
        try: conn = sqlite3.connect('okul_veritabani.db'); cursor = conn.cursor(); cursor.execute("INSERT INTO Ogretmenler (ad_soyad, brans) VALUES (?, ?)", (ad, brans)); conn.commit(); conn.close(); messagebox.showinfo("Başarılı", "Öğretmen eklendi."); self.ogretmen_listesini_guncelle(); self.ogretmen_formu_temizle()
        except sqlite3.IntegrityError: messagebox.showerror("Hata", "Bu isimde bir öğretmen zaten mevcut!")
    def ogretmen_guncelle(self):
        if not self.ogretmen_tree.selection(): messagebox.showwarning("Uyarı", "Lütfen bir öğretmen seçin."); return
        ogretmen_id = self.ogretmen_tree.item(self.ogretmen_tree.selection()[0], 'values')[0]; ad = self.ogretmen_ad_entry.get().strip(); brans = self.ogretmen_brans_entry.get().strip()
        conn = sqlite3.connect('okul_veritabani.db'); cursor = conn.cursor()
        try:
            cursor.execute("UPDATE Ogretmenler SET ad_soyad = ?, brans = ? WHERE id = ?", (ad, brans, ogretmen_id)); cursor.execute("DELETE FROM OgretmenDersYetkinlikleri WHERE ogretmen_id = ?", (ogretmen_id,))
            for ders_adi in self.atanan_dersler_listbox.get(0, tk.END):
                if ders_id := self.ders_id_map.get(ders_adi): cursor.execute("INSERT INTO OgretmenDersYetkinlikleri (ogretmen_id, ders_id) VALUES (?, ?)", (ogretmen_id, ders_id))
            conn.commit(); messagebox.showinfo("Başarılı", "Öğretmen bilgileri güncellendi.")
        except Exception as e: conn.rollback(); messagebox.showerror("Hata", f"Güncelleme hatası: {e}")
        finally: conn.close(); self.ogretmen_listesini_guncelle(); self.ogretmen_formu_temizle()
    def ogretmen_sil(self):
        if not self.ogretmen_tree.selection(): messagebox.showwarning("Uyarı", "Lütfen bir öğretmen seçin."); return
        if messagebox.askyesno("Onay", "Seçili öğretmeni silmek istediğinizden emin misiniz?"):
            ogretmen_id = self.ogretmen_tree.item(self.ogretmen_tree.selection()[0], 'values')[0]; conn = sqlite3.connect('okul_veritabani.db'); cursor = conn.cursor(); cursor.execute("DELETE FROM Ogretmenler WHERE id = ?", (ogretmen_id,)); conn.commit(); conn.close(); self.ogretmen_listesini_guncelle(); self.ogretmen_formu_temizle()

    def ogrenci_yonetim_ekranini_goster(self):
        self.icerik_alanini_temizle(); frame = ttk.Frame(self.content_frame, padding=10); frame.pack(fill="both", expand=True)
        form_frame = ttk.LabelFrame(frame, text="Yeni Öğrenci Ekle / Güncelle"); form_frame.pack(fill="x", pady=10, padx=10)
        ttk.Label(form_frame, text="Ad:").grid(row=0, column=0, padx=5, pady=5, sticky="w"); self.ogrenci_ad_entry = ttk.Entry(form_frame, width=30); self.ogrenci_ad_entry.grid(row=0, column=1, padx=5, pady=5)
        ttk.Label(form_frame, text="Soyad:").grid(row=0, column=2, padx=5, pady=5, sticky="w"); self.ogrenci_soyad_entry = ttk.Entry(form_frame, width=30); self.ogrenci_soyad_entry.grid(row=0, column=3, padx=5, pady=5)
        ttk.Label(form_frame, text="Sınıfı:").grid(row=1, column=0, padx=5, pady=5, sticky="w"); self.ogrenci_sinif_entry = ttk.Entry(form_frame, width=30); self.ogrenci_sinif_entry.grid(row=1, column=1, padx=5, pady=5)
        conn = sqlite3.connect('okul_veritabani.db'); cursor = conn.cursor(); cursor.execute("SELECT id, ders_adi FROM Dersler ORDER BY ders_adi"); dersler_data = cursor.fetchall(); self.ogrenci_ders_map = {ders_adi: ders_id for ders_id, ders_adi in dersler_data}; ders_adlari = [ders[1] for ders in dersler_data]; conn.close()
        ttk.Label(form_frame, text="Sorumlu Olduğu Ders:").grid(row=2, column=0, padx=5, pady=5, sticky="w"); self.ogrenci_ders_combo = ttk.Combobox(form_frame, values=ders_adlari, state="readonly", width=28); self.ogrenci_ders_combo.grid(row=2, column=1, padx=5, pady=5)
        ttk.Label(form_frame, text="Dersin Sınıf Düzeyi:").grid(row=2, column=2, padx=5, pady=5, sticky="w"); self.ogrenci_ders_duzey_combo = ttk.Combobox(form_frame, values=[9, 10, 11, 12], state="readonly", width=28); self.ogrenci_ders_duzey_combo.grid(row=2, column=3, padx=5, pady=5)
        btn_frame = ttk.Frame(form_frame); btn_frame.grid(row=3, columnspan=4, pady=10)
        ttk.Button(btn_frame, text="Ekle", command=self.ogrenci_ekle).pack(side="left", padx=5); ttk.Button(btn_frame, text="Güncelle", command=self.ogrenci_guncelle).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Sil", command=self.ogrenci_sil).pack(side="left", padx=5); ttk.Button(btn_frame, text="Formu Temizle", command=self.ogrenci_formu_temizle).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Excel'den Öğrenci Aktar", command=self.excelden_ogrenci_aktar, style="Accent.TButton").pack(side="left", padx=15)
        tree_frame = ttk.Frame(frame); tree_frame.pack(fill="both", expand=True, padx=10, pady=10)
        self.ogrenci_tree = ttk.Treeview(tree_frame, columns=("id", "ad", "soyad", "sinif", "sorumlu_ders", "ders_duzeyi"), show="headings")
        self.ogrenci_tree.heading("id", text="ID"); self.ogrenci_tree.heading("ad", text="Ad"); self.ogrenci_tree.heading("soyad", text="Soyad"); self.ogrenci_tree.heading("sinif", text="Sınıfı"); self.ogrenci_tree.heading("sorumlu_ders", text="Sorumlu Olduğu Ders"); self.ogrenci_tree.heading("ders_duzeyi", text="Ders Sınıf Düzeyi")
        self.ogrenci_tree.column("id", width=40, anchor="center"); self.ogrenci_tree.column("sinif", width=80, anchor="center"); self.ogrenci_tree.column("ders_duzeyi", width=120, anchor="center"); self.ogrenci_tree.pack(side="left", fill="both", expand=True)
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.ogrenci_tree.yview); self.ogrenci_tree.configure(yscrollcommand=scrollbar.set); scrollbar.pack(side="right", fill="y")
        self.ogrenci_tree.bind("<<TreeviewSelect>>", self.ogrenci_sec); self.ogrenci_listesini_guncelle()

    def excelden_ogrenci_aktar(self):
        dosya_yolu = filedialog.askopenfilename(title="Öğrenci Listesi İçeren Excel Dosyasını Seçin", filetypes=[("Excel Dosyaları", "*.xlsx")])
        if not dosya_yolu: return
        try:
            df = pd.read_excel(dosya_yolu); gerekli_sutunlar = ['Ad', 'Soyad', 'Sınıf', 'Sorumlu Ders', 'Ders Sınıf Düzeyi']
            if not all(sutun in df.columns for sutun in gerekli_sutunlar): messagebox.showerror("Hata", f"Excel'de gerekli sütunlar bulunamadı!\nBeklenen: {gerekli_sutunlar}"); return
            conn = sqlite3.connect('okul_veritabani.db'); cursor = conn.cursor(); eklenen, atlanan = 0, []
            for index, row in df.iterrows():
                ad, soyad, sinif, ders_adi, duzey = row['Ad'], row['Soyad'], row['Sınıf'], row['Sorumlu Ders'], row['Ders Sınıf Düzeyi']
                if pd.isna(ad) or pd.isna(soyad) or pd.isna(ders_adi) or pd.isna(duzey) or ders_adi not in self.ogrenci_ders_map: atlanan.append(index + 2); continue
                cursor.execute("INSERT INTO Ogrenciler (ad, soyad, sinif, sorumlu_ders_id, ders_sinif_duzeyi) VALUES (?, ?, ?, ?, ?)", (str(ad), str(soyad), str(sinif), self.ogrenci_ders_map[ders_adi], int(duzey))); eklenen += 1
            conn.commit(); conn.close()
            mesaj = f"{eklenen} öğrenci eklendi." + (f"\n\n{len(atlanan)} satır atlandı (hatalı/boş veri).\nSatırlar: {', '.join(map(str, atlanan))}" if atlanan else "")
            messagebox.showinfo("İşlem Tamamlandı", mesaj); self.ogrenci_listesini_guncelle()
        except Exception as e: messagebox.showerror("Hata", f"Dosya işlenirken hata oluştu:\n{e}")
    
    def ogrenci_listesini_guncelle(self):
        for i in self.ogrenci_tree.get_children(): self.ogrenci_tree.delete(i)
        conn = sqlite3.connect('okul_veritabani.db'); cursor = conn.cursor()
        cursor.execute("SELECT o.id, o.ad, o.soyad, o.sinif, d.ders_adi, o.ders_sinif_duzeyi FROM Ogrenciler o LEFT JOIN Dersler d ON o.sorumlu_ders_id = d.id ORDER BY o.soyad, o.ad")
        for row in cursor.fetchall(): self.ogrenci_tree.insert("", "end", values=row)
        conn.close()
    def ogrenci_formu_temizle(self):
        self.ogrenci_ad_entry.delete(0, 'end'); self.ogrenci_soyad_entry.delete(0, 'end'); self.ogrenci_sinif_entry.delete(0, 'end'); self.ogrenci_ders_combo.set(''); self.ogrenci_ders_duzey_combo.set('')
        if self.ogrenci_tree.selection(): self.ogrenci_tree.selection_remove(self.ogrenci_tree.selection()[0])
    def ogrenci_sec(self, event):
        if not self.ogrenci_tree.selection(): return
        values = self.ogrenci_tree.item(self.ogrenci_tree.selection()[0], 'values')
        self.ogrenci_formu_temizle(); self.ogrenci_ad_entry.insert(0, values[1]); self.ogrenci_soyad_entry.insert(0, values[2]); self.ogrenci_sinif_entry.insert(0, values[3]); self.ogrenci_ders_combo.set(values[4]); self.ogrenci_ders_duzey_combo.set(values[5])
    def ogrenci_ekle(self):
        ad, soyad, sinif, ders, duzey = self.ogrenci_ad_entry.get().strip(), self.ogrenci_soyad_entry.get().strip(), self.ogrenci_sinif_entry.get().strip(), self.ogrenci_ders_combo.get(), self.ogrenci_ders_duzey_combo.get()
        if not all([ad, soyad, ders, duzey]): messagebox.showwarning("Uyarı", "Ad, Soyad, Sorumlu Ders ve Ders Düzeyi zorunludur!"); return
        try: conn = sqlite3.connect('okul_veritabani.db'); cursor = conn.cursor(); cursor.execute("INSERT INTO Ogrenciler (ad, soyad, sinif, sorumlu_ders_id, ders_sinif_duzeyi) VALUES (?, ?, ?, ?, ?)", (ad, soyad, sinif, self.ogrenci_ders_map[ders], int(duzey))); conn.commit(); conn.close(); messagebox.showinfo("Başarılı", "Öğrenci eklendi."); self.ogrenci_listesini_guncelle(); self.ogrenci_formu_temizle()
        except Exception as e: messagebox.showerror("Hata", f"Öğrenci eklenirken hata: {e}")
    def ogrenci_guncelle(self):
        if not self.ogrenci_tree.selection(): messagebox.showwarning("Uyarı", "Lütfen güncellenecek öğrenciyi seçin."); return
        ogrenci_id = self.ogrenci_tree.item(self.ogrenci_tree.selection()[0], 'values')[0]; ad, soyad, sinif, ders, duzey = self.ogrenci_ad_entry.get().strip(), self.ogrenci_soyad_entry.get().strip(), self.ogrenci_sinif_entry.get().strip(), self.ogrenci_ders_combo.get(), self.ogrenci_ders_duzey_combo.get()
        if not all([ad, soyad, ders, duzey]): messagebox.showwarning("Uyarı", "Gerekli alanlar boş bırakılamaz!"); return
        try: conn = sqlite3.connect('okul_veritabani.db'); cursor = conn.cursor(); cursor.execute("UPDATE Ogrenciler SET ad = ?, soyad = ?, sinif = ?, sorumlu_ders_id = ?, ders_sinif_duzeyi = ? WHERE id = ?", (ad, soyad, sinif, self.ogrenci_ders_map[ders], int(duzey), ogrenci_id)); conn.commit(); conn.close(); messagebox.showinfo("Başarılı", "Öğrenci bilgileri güncellendi."); self.ogrenci_listesini_guncelle(); self.ogrenci_formu_temizle()
        except Exception as e: messagebox.showerror("Hata", f"Güncelleme sırasında hata: {e}")
    def ogrenci_sil(self):
        if not self.ogrenci_tree.selection(): messagebox.showwarning("Uyarı", "Lütfen silinecek öğrenciyi seçin."); return
        if messagebox.askyesno("Onay", "Seçili öğrenci kaydını silmek istediğinizden emin misiniz?"):
            try: ogrenci_id = self.ogrenci_tree.item(self.ogrenci_tree.selection()[0], 'values')[0]; conn = sqlite3.connect('okul_veritabani.db'); cursor = conn.cursor(); cursor.execute("DELETE FROM Ogrenciler WHERE id = ?", (ogrenci_id,)); conn.commit(); conn.close(); self.ogrenci_listesini_guncelle(); self.ogrenci_formu_temizle()
            except Exception as e: messagebox.showerror("Hata", f"Silme işlemi sırasında hata: {e}")

    def ders_yonetim_ekranini_goster(self):
        self.icerik_alanini_temizle(); frame = ttk.Frame(self.content_frame, padding=10); frame.pack(fill="both", expand=True)
        form_frame = ttk.LabelFrame(frame, text="Yeni Ders Ekle"); form_frame.pack(fill="x", pady=10, padx=10)
        ttk.Label(form_frame, text="Ders Adı:").pack(side="left", padx=10); self.ders_ad_entry = ttk.Entry(form_frame, width=40); self.ders_ad_entry.pack(side="left", padx=10, pady=10, fill="x", expand=True)
        ttk.Button(form_frame, text="Ekle", command=self.ders_ekle).pack(side="left", padx=10)
        tree_frame = ttk.Frame(frame); tree_frame.pack(fill="both", expand=True, padx=10, pady=10)
        self.ders_tree = ttk.Treeview(tree_frame, columns=("id", "ders_adi"), show="headings"); self.ders_tree.heading("id", text="ID"); self.ders_tree.heading("ders_adi", text="Ders Adı"); self.ders_tree.column("id", width=50); self.ders_tree.pack(fill="both", expand=True, side="left")
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.ders_tree.yview); self.ders_tree.configure(yscrollcommand=scrollbar.set); scrollbar.pack(side="right", fill="y")
        ttk.Button(frame, text="Seçili Dersi Sil", command=self.ders_sil).pack(pady=5); self.ders_listesini_guncelle()
    def ders_listesini_guncelle(self):
        for i in self.ders_tree.get_children(): self.ders_tree.delete(i)
        conn = sqlite3.connect('okul_veritabani.db'); cursor = conn.cursor(); cursor.execute("SELECT * FROM Dersler ORDER BY ders_adi"); 
        for row in cursor.fetchall(): self.ders_tree.insert("", "end", values=row)
        conn.close()
    def ders_ekle(self):
        ders_adi = self.ders_ad_entry.get().strip()
        if not ders_adi: messagebox.showwarning("Uyarı", "Ders adı boş bırakılamaz!"); return
        try: conn = sqlite3.connect('okul_veritabani.db'); cursor = conn.cursor(); cursor.execute("INSERT INTO Dersler (ders_adi) VALUES (?)", (ders_adi,)); conn.commit(); conn.close(); self.ders_listesini_guncelle(); self.ders_ad_entry.delete(0, 'end'); messagebox.showinfo("Başarılı", "Ders eklendi.")
        except sqlite3.IntegrityError: messagebox.showerror("Hata", "Bu isimde bir ders zaten mevcut!")
    def ders_sil(self):
        if not self.ders_tree.selection(): messagebox.showwarning("Uyarı", "Lütfen bir ders seçin."); return
        if messagebox.askyesno("Onay", "Seçili dersi silmek, bu dersten sorumlu TÜM ÖĞRENCİLERİ de silecektir. Emin misiniz?"):
            ders_id = self.ders_tree.item(self.ders_tree.selection()[0], 'values')[0]; conn = sqlite3.connect('okul_veritabani.db'); cursor = conn.cursor(); cursor.execute("PRAGMA foreign_keys = ON;"); cursor.execute("DELETE FROM Dersler WHERE id = ?", (ders_id,)); conn.commit(); conn.close(); self.ders_listesini_guncelle()

    def gorevleri_ata(self):
        secili_ders_adi = self.secilen_ders.get()
        if not secili_ders_adi: messagebox.showwarning("Uyarı", "Lütfen bir ders seçin."); return
        try: tam_tarih = f"{self.sinav_tarihi.get_date().strftime('%d/%m/%Y')} {self.saat.get()}:{self.dakika.get()}"
        except: messagebox.showerror("Hata", "Lütfen geçerli bir tarih ve saat seçin."); return

        conn = sqlite3.connect('okul_veritabani.db'); cursor = conn.cursor()
        cursor.execute("SELECT id FROM Dersler WHERE ders_adi = ?", (secili_ders_adi,)); ders_id_result = cursor.fetchone()
        if not ders_id_result: messagebox.showerror("Hata", "Ders bulunamadı."); conn.close(); return
        ders_id = ders_id_result[0]
        cursor.execute("SELECT o.id, o.ad_soyad, o.brans, o.toplam_gorev_sayisi FROM Ogretmenler o JOIN OgretmenDersYetkinlikleri y ON o.id = y.ogretmen_id WHERE y.ders_id = ? ORDER BY o.toplam_gorev_sayisi ASC, RANDOM()", (ders_id,)); yetkin_ogretmenler = cursor.fetchall()
        cursor.execute("SELECT id, ad_soyad, brans, toplam_gorev_sayisi FROM Ogretmenler WHERE id NOT IN (SELECT ogretmen_id FROM OgretmenDersYetkinlikleri WHERE ders_id = ?) ORDER BY toplam_gorev_sayisi ASC, RANDOM()", (ders_id,)); diger_ogretmenler = cursor.fetchall()
        tum_ogretmenler = yetkin_ogretmenler + diger_ogretmenler

        if len(tum_ogretmenler) < 3: messagebox.showerror("Hata", "Görev ataması için en az 3 öğretmen olmalıdır."); conn.close(); return
        komisyon_uyesi, uye_yardimcisi, gozcu, atanan_idler = None, None, None, set()
        if yetkin_ogretmenler: komisyon_uyesi = yetkin_ogretmenler.pop(0); atanan_idler.add(komisyon_uyesi[0])
        if yetkin_ogretmenler: uye_yardimcisi = yetkin_ogretmenler.pop(0); atanan_idler.add(uye_yardimcisi[0])
        kalan = [ogr for ogr in tum_ogretmenler if ogr[0] not in atanan_idler]
        if not komisyon_uyesi and kalan: komisyon_uyesi = kalan.pop(0); atanan_idler.add(komisyon_uyesi[0])
        if not uye_yardimcisi and kalan: uye_yardimcisi = kalan.pop(0); atanan_idler.add(uye_yardimcisi[0])
        if kalan: gozcu = kalan[0]; atanan_idler.add(gozcu[0])
        if not all([komisyon_uyesi, uye_yardimcisi, gozcu]): messagebox.showerror("Atama Hatası", "Yeterli sayıda öğretmen bulunamadı."); conn.close(); return
        
        mesaj = f"Ders: {secili_ders_adi}\nTarih: {tam_tarih}\n\nKomisyon Üyesi: {komisyon_uyesi[1]}\nÜye Yardımcısı: {uye_yardimcisi[1]}\nGözcü: {gozcu[1]}\n\nOnaylıyor musunuz?"
        if messagebox.askyesno("Atama Onayı", mesaj):
            try:
                cursor.execute("INSERT INTO SinavGorevleri (ders_adi, komisyon_uyesi, uye_yardimcisi, gozcu, sinav_tarihi) VALUES (?, ?, ?, ?, ?)", (secili_ders_adi, komisyon_uyesi[1], uye_yardimcisi[1], gozcu[1], tam_tarih))
                for ogretmen_id in atanan_idler: cursor.execute("UPDATE Ogretmenler SET toplam_gorev_sayisi = toplam_gorev_sayisi + 1 WHERE id = ?", (ogretmen_id,))
                conn.commit(); messagebox.showinfo("Başarılı", "Görev ataması kaydedildi.")
            except Exception as e: conn.rollback(); messagebox.showerror("Veritabanı Hatası", f"Hata: {e}")
            finally: conn.close()
        else: conn.close()

# --- ANA PROGRAM ---
if __name__ == "__main__":
    try:
        import pandas as pd
        import reportlab
        from tkcalendar import DateEntry
    except ImportError as e:
        print(f"Eksik kütüphane: {e}\nLütfen 'pip install pandas openpyxl reportlab tkcalendar ttkthemes Pillow' komutu ile eksik kütüphaneleri yükleyin.")
        exit()
    
    veritabani_kur()
    root = ThemedTk(theme="arc")
    app = SinavGorevUygulamasi(root)
    root.mainloop()
