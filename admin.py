import streamlit as st
import pandas as pd
import auth 
import time 

def show_admin_page():
    st.title("🛡️ Admin Dashboard")
    st.markdown("---")

    # --- SIDEBAR LOGOUT ---
    with st.sidebar:
        st.write("Login sebagai: **Admin**")
        if st.button("Logout Admin", type="primary"):
            st.session_state['logged_in'] = False
            st.session_state['username'] = ''
            st.rerun()

    # --- BAGIAN 1: TABEL USER ---
    st.subheader("👥 Daftar Pengguna")
    
    # Ambil data terbaru
    user_result = auth.view_all_users()
    
    # Masukkan ke Pandas DataFrame
    df = pd.DataFrame(user_result, columns=["Username", "Email", "Password Hash"])
    
    # TRICK AGAR INDEX SELALU 1, 2, 3 (Tidak bolong-bolong)
    if not df.empty:
        df.index = range(1, len(df) + 1) # Reset index mulai dari 1
        st.dataframe(df, use_container_width=True)
    else:
        st.info("Belum ada user yang terdaftar.")

    st.markdown("---")

    # --- BAGIAN 2: EDIT & DELETE (MANAJEMEN DATA) ---
    st.subheader("⚙️ Kelola Data User")
    
    # FILTER LOGIC: Ambil username user TAPI 'admin' jangan dimasukkan
    # i[0] adalah username. Kita filter: jika i[0] TIDAK SAMA DENGAN 'admin'
    list_of_users = [i[0] for i in user_result if i[0] != 'admin']

    # Cek apakah ada user lain selain admin
    if list_of_users:
        selected_user = st.selectbox("Pilih User untuk Diedit/Dihapus", list_of_users)

        if selected_user:
            # Cari data user yang dipilih
            current_data = [x for x in user_result if x[0] == selected_user][0]
            current_email = current_data[1]

            col1, col2 = st.columns([2, 1])

            # === KOLOM EDIT ===
            with col1:
                with st.form("edit_form"):
                    st.write(f"📝 Edit Data: **{selected_user}**")
                    new_username = st.text_input("Edit Username", value=selected_user)
                    new_email = st.text_input("Edit Email", value=current_email)
                    
                    if st.form_submit_button("Simpan Perubahan"):
                        # Memanggil fungsi yang tadi kita tambahkan di auth.py
                        auth.update_user_data(new_username, new_email, selected_user)
                        st.success(f"Data {selected_user} berhasil diperbarui!")
                        time.sleep(1) # Jeda sedikit biar notif terbaca
                        st.rerun()

            # === KOLOM HAPUS ===
            with col2:                
                if "confirm_delete" not in st.session_state:
                    st.session_state.confirm_delete = False

                if st.button("Hapus User Ini", type="primary"):
                    st.session_state.confirm_delete = True
                
                if st.session_state.confirm_delete:
                    st.warning(f"Yakin hapus **{selected_user}**?")
                    col_yes, col_no = st.columns(2)
                    
                    if col_yes.button("YA"):
                        auth.delete_user(selected_user)
                        st.success(f"User dihapus.")
                        st.session_state.confirm_delete = False
                        st.rerun()
                    
                    if col_no.button("Batal"):
                        st.session_state.confirm_delete = False
                        st.rerun()
    else:
        st.info("Belum ada user user lain yang terdaftar (Hanya Admin).")