# Sportoto Quant Cockpit & Multi-Covering Portfolio Engine

Institutional quantitative sports prediction portfolio optimization and live tracking system for Spor Toto 15-match programs.

## 🚀 3-Adımda Streamlit Community Cloud Dağıtımı (Deployment)

1. **GitHub Deponuzu Bağlayın**:
   - Kodları GitHub reponuza push edin:
     ```bash
     git add .
     git commit -m "feat: institutional quant engine and live tracker"
     git push origin main
     ```

2. **Streamlit Community Cloud'a Giriş Yapın**:
   - [share.streamlit.io](https://share.streamlit.io/) adresine gidin.
   - **"New app"** butonuna tıklayın ve GitHub deponuzu seçin.

3. **Uygulama Ayarlarını Girin & Deploy Edin**:
   - **Repository**: `kullanici_adiniz/sportoto`
   - **Branch**: `main`
   - **Main file path**: `app.py`
   - **Deploy!** butonuna tıklayın. Gerekli kütüphaneler `requirements.txt` üzerinden otomatik kurulacaktır.

---

## 🔬 Matematiksel Garanti Seviyeleri (Covering Radii)

- **13G Garanti ($R = 2$)**: Hamming yarıçapı $R \le 2$ küre kalkanı. Ham kartezyen uzayında $13$ isabet + $3\text{--}6 \times 12$ basamaklı ikramiye teminatı.
- **14G Garanti ($R = 1$)**: Hamming yarıçapı $R \le 1$ küre kalkanı. $14$ isabet + çoklu $13$ ve $12$ basamaklı teminat.
- **15G Tam Kapsama ($R = 0$)**: Sıfır hata ile tüm olasılıkların kapsanması.

---

## 🛠️ Yerel Geliştirme (Local Development)

```bash
pip install -r requirements.txt
python -m streamlit run app.py
```

### Test Paketini Çalıştırma
```bash
python test_system_invariants.py
python test_outcome_balance.py
```
