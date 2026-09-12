import io
from datetime import datetime
import requests
import streamlit as st
from PIL import Image, ImageDraw

# ==========================================
# CONFIGURASI APLIKASI
# ==========================================
st.set_page_config(
    page_title="Gold Promo Generator",
    page_icon="🪙",
    layout="wide"
)

# ==========================================
# HELPER / UTILITY FUNCTIONS
# ==========================================
def format_rupiah(val: float) -> str:
    """Format angka menjadi string Rupiah (misal: Rp 1.000.000)"""
    return f"Rp {val:,.0f}".replace(",", ".")

def clean_phone_number(phone: str) -> str:
    """Konversi nomor WA lokal (08xx) ke format internasional (628xx)"""
    cleaned = "".join(filter(str.isdigit, phone))
    if cleaned.startswith("0"):
        cleaned = "62" + cleaned[1:]
    return cleaned

@st.cache_data(ttl=3600)
def fetch_online_background(width: int, height: int, keyword: str = "gold,luxury") -> Image.Image:
    """Mengambil gambar latar belakang acak dari Unsplash berdasarkan keyword"""
    try:
        url = f"https://source.unsplash.com/featured/{width}x{height}/?{keyword}"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            return Image.open(io.BytesIO(response.content)).convert("RGBA")
    except Exception:
        pass
    # Fallback jika koneksi internet/API gagal
    return Image.new("RGBA", (width, height), (20, 20, 20, 255))

def create_base_image(
    mode: str, 
    template: str, 
    uploaded_file, 
    width: int, 
    height: int
) -> Image.Image:
    """Membuat latar belakang gambar berdasarkan pilihan mode/template"""
    
    # 1. Mode Upload Manual
    if mode == "Upload Manual" and uploaded_file is not None:
        base_img = Image.open(uploaded_file).convert("RGBA").resize((width, height))
        overlay = Image.new("RGBA", (width, height), (0, 0, 0, 140))
        return Image.alpha_composite(base_img, overlay)

    # 2. Mode Auto (Random dari Internet)
    if mode == "Auto (Random dari Internet)":
        base_img = fetch_online_background(width, height, keyword="gold,background")
        overlay = Image.new("RGBA", (width, height), (0, 0, 0, 160)) # Overlay gelap agar teks terbaca
        img = Image.alpha_composite(base_img, overlay)
        draw = ImageDraw.Draw(img)
        draw.rectangle([30, 30, width - 30, height - 30], outline="#FFD700", width=4)
        return img

    # 3. Mode Auto Template Warna (Solid/Gradasi)
    if template == "Luxury Gold":
        bg_color = (20, 18, 15, 255)
        border_color = (212, 175, 55, 255)
    elif template == "Clean Minimalist":
        bg_color = (248, 249, 250, 255)
        border_color = (180, 180, 180, 255)
    else:  # Elegant Dark
        bg_color = (15, 23, 42, 255)
        border_color = (234, 179, 8, 255)

    img = Image.new("RGBA", (width, height), bg_color)
    draw = ImageDraw.Draw(img)
    draw.rectangle([30, 30, width - 30, height - 30], outline=border_color, width=4)
    draw.rectangle([42, 42, width - 42, height - 42], outline=border_color, width=1)
    return img

def render_promo_poster(
    brand: str,
    tanggal_str: str,
    harga_dict: dict,
    mode_gambar: str,
    template: str,
    uploaded_image,
    nama_toko: str,
    no_wa: str
) -> Image.Image:
    """Render poster promosi emas ke dalam objek PIL Image"""
    width, height = 1080, 1080
    img = create_base_image(mode_gambar, template, uploaded_image, width, height)
    draw = ImageDraw.Draw(img)

    # Warna teks
    is_minimalist = (mode_gambar == "Auto Template" and template == "Clean Minimalist")
    c_primary = "#1E293B" if is_minimalist else "#FFFFFF"
    c_gold = "#B45309" if is_minimalist else "#FFD700"
    c_muted = "#64748B" if is_minimalist else "#CBD5E1"
    c_line = "#CBD5E1" if is_minimalist else "#EAB308"

    # Header
    draw.text((width // 2, 75), nama_toko.upper(), fill=c_gold, anchor="mm")
    draw.text((width // 2, 125), f"HARGA EMAS {brand.upper()}", fill=c_primary, anchor="mm")
    draw.text((width // 2, 165), tanggal_str, fill=c_muted, anchor="mm")

    # Pembatas
    draw.line([(100, 195), (width - 100, 195)], fill=c_line, width=2)

    # Layout Tabel Harga (2 Kolom)
    valid_items = {g: h for g, h in harga_dict.items() if h > 0}
    items_per_col = 5
    col1_x, col2_x = 180, 620
    y_start = 240

    for i, (gram, harga) in enumerate(valid_items.items()):
        curr_x = col1_x if i < items_per_col else col2_x
        curr_y = y_start + ((i % items_per_col) * 70)

        draw.text((curr_x, curr_y), f"{gram} Gram", fill=c_primary)
        draw.text((curr_x + 200, curr_y), format_rupiah(harga), fill=c_gold)

    # Footer
    draw.line([(100, 950), (width - 100, 950)], fill=c_line, width=2)
    draw.text((width // 2, 990), f"Pemesanan WhatsApp: {no_wa}", fill=c_primary, anchor="mm")

    return img.convert("RGB")


# ==========================================
# APPLICATION LAYOUT & CONTROLLER
# ==========================================
st.title("🪙 Gold Promo & Broadcast Generator")
st.caption("Aplikasi Pembuat Grafis Promosi & Teks Broadcast Sales Emas")

# --- SIDEBAR INPUT ---
st.sidebar.header("📋 Input Data & Pengaturan")

brand_emas = st.sidebar.selectbox(
    "Merek Emas",
    ["Antam", "UBS", "Galeri24", "Lotus Archi", "PAMP Suisse", "Lainnya"]
)

tanggal = st.sidebar.date_input("Tanggal", datetime.now())
formatted_date = tanggal.strftime("%d %B %Y")

st.sidebar.subheader("💰 Daftar Harga Emas (Rp)")
gramasi_list = [0.5, 1, 2, 3, 5, 10, 25, 50, 100]
harga_dict = {}

col_in1, col_in2 = st.sidebar.columns(2)
for idx, g in enumerate(gramasi_list):
    target_col = col_in1 if idx % 2 == 0 else col_in2
    harga_dict[g] = target_col.number_input(
        f"{g} Gram", min_value=0, value=0, step=5000, key=f"gram_{g}"
    )

st.sidebar.subheader("🖼️ Desain Gambar")
mode_gambar = st.sidebar.radio(
    "Pilihan Latar:", 
    ["Auto (Random dari Internet)", "Auto Template", "Upload Manual"]
)

template_style = "Elegant Dark"
uploaded_image = None

if mode_gambar == "Auto Template":
    template_style = st.sidebar.selectbox(
        "Pilih Template Warna:",
        ["Elegant Dark", "Luxury Gold", "Clean Minimalist"]
    )
elif mode_gambar == "Upload Manual":
    uploaded_image = st.sidebar.file_uploader("Upload Gambar Latar (PNG/JPG)", type=["png", "jpg", "jpeg"])

st.sidebar.subheader("📞 Informasi Toko / Admin")
nama_toko = st.sidebar.text_input("Nama Toko/Sales", "Logam Mulia Gold")
no_wa = st.sidebar.text_input("No. WhatsApp", "08123456789")


# --- MAIN CONTENT TABS ---
tab1, tab2 = st.tabs(["🖼️ Gambar Iklan (Poster)", "📱 Teks Broadcast WA"])

# --- TAB 1: POSTER GENERATOR ---
with tab1:
    st.subheader(f"Preview Poster - {brand_emas}")

    if mode_gambar == "Auto (Random dari Internet)":
        if st.button("🔄 Ganti Gambar Latar Lain"):
            st.cache_data.clear()

    poster_img = render_promo_poster(
        brand=brand_emas,
        tanggal_str=formatted_date,
        harga_dict=harga_dict,
        mode_gambar=mode_gambar,
        template=template_style,
        uploaded_image=uploaded_image,
        nama_toko=nama_toko,
        no_wa=no_wa
    )

    st.image(poster_img, caption="Preview Gambar Poster", use_container_width=True)

    buf = io.BytesIO()
    poster_img.save(buf, format="JPEG", quality=95)
    st.download_button(
        label="📥 Download Gambar Promo (JPG)",
        data=buf.getvalue(),
        file_name=f"Harga_Emas_{brand_emas}_{tanggal.strftime('%Y%m%d')}.jpg",
        mime="image/jpeg"
    )

# --- TAB 2: BROADCAST WA GENERATOR ---
with tab2:
    st.subheader("Format Teks untuk Broadcast WhatsApp")

    wa_clean = clean_phone_number("081286435267")
    wa_direct_link = f"https://wa.me/{wa_clean}"

    wa_text = f"✨ *HARGA EMAS {brand_emas.upper()} HARI INI* ✨\n"
    wa_text += f"📅 *{formatted_date}*\n\n"
    wa_text += f"Halo Sahabat Investasi! Berikut update harga emas terupdate dari *{nama_toko}*:\n\n"

    has_price = False
    for g, h in harga_dict.items():
        if h > 0:
            has_price = True
            wa_text += f"🔹 *{g} Gram* : {format_rupiah(h)}\n"

    if not has_price:
        wa_text += "_Silakan isi harga emas di sidebar terlebih dahulu._\n"

    wa_text += f"\n📌 *Catatan:*\n"
    wa_text += f"- Harga dapat berubah sewaktu-waktu.\n"
    wa_text += f"- Dijamin 100% Asli & Bersertifikat.\n"
    wa_text += f"- Melayani COD & Pengiriman Aman.\n\n"
    wa_text += f"📲 *Order / Tanya-Tanya Langsung Klik Link WA:* \n"
    wa_text += f"{wa_direct_link}"

    st.text_area("Salin teks di bawah ini:", value=wa_text, height=350)

    st.markdown(
        f"""
        <a href="{wa_direct_link}" target="_blank">
            <button style="
                background-color: #25D366;
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 8px;
                font-size: 16px;
                cursor: pointer;
                font-weight: bold;
            ">
                💬 Buka Chat WhatsApp Langsung
            </button>
        </a>
        """,
        unsafe_allow_html=True
    )
