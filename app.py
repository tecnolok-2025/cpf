import streamlit as st
import pandas as pd

from db import init_db
from auth import any_admin_exists, create_user, authenticate, get_user_by_email
import services as svc
from matching import top_matches

st.set_page_config(page_title="CPF – Requerimientos", layout="wide")

init_db()

if "user" not in st.session_state:
    st.session_state.user = None

def logout():
    st.session_state.user = None
    st.rerun()

def chamber_label(c):
    parts = [c["name"]]
    if c["province"] or c["city"]:
        parts.append(" - ".join([p for p in [c["city"], c["province"]] if p]))
    return " ".join(parts)

st.title("CPF – Sistema de Requerimientos (sin precios)")
st.caption("Prototipo: publicar OFERTAS/NECESIDADES, navegar, buscar y solicitar contacto. Negociación y precio: fuera del sistema.")

# Onboarding admin
if not any_admin_exists():
    st.warning("No existe usuario Admin. Creá el Admin inicial para habilitar el sistema.")
    with st.form("create_admin"):
        email = st.text_input("Email (Admin)")
        password = st.text_input("Contraseña", type="password")
        name = st.text_input("Nombre y Apellido")
        company = st.text_input("Empresa")
        phone = st.text_input("Teléfono (opcional)")
        submitted = st.form_submit_button("Crear Admin")
    if submitted:
        if not email or not password or not name or not company:
            st.error("Completá email, contraseña, nombre y empresa.")
        else:
            try:
                create_user(email=email, password=password, name=name, company=company, phone=phone, chamber_id=None, role="admin")
                st.success("Admin creado. Ahora podés iniciar sesión.")
                st.rerun()
            except Exception as e:
                st.error(f"No se pudo crear Admin: {e}")
    st.stop()

# Login / Register
if st.session_state.user is None:
    col1, col2 = st.columns([1,1])
    with col1:
        st.subheader("Iniciar sesión")
        with st.form("login"):
            email = st.text_input("Email", key="login_email")
            password = st.text_input("Contraseña", type="password", key="login_pass")
            ok = st.form_submit_button("Ingresar")
        if ok:
            u = authenticate(email, password)
            if u is None:
                st.error("Credenciales inválidas o usuario inactivo.")
            else:
                st.session_state.user = dict(u)
                st.success("Ingreso correcto.")
                st.rerun()
    with col2:
        st.subheader("Registrarse")
        chambers = svc.list_chambers()
        chamber_options = ["(Sin cámara por ahora)"] + [chamber_label(c) for c in chambers]
        with st.form("register"):
            r_email = st.text_input("Email", key="reg_email")
            r_pass = st.text_input("Contraseña", type="password", key="reg_pass")
            r_name = st.text_input("Nombre y Apellido", key="reg_name")
            r_company = st.text_input("Empresa", key="reg_company")
            r_phone = st.text_input("Teléfono (opcional)", key="reg_phone")
            chamber_pick = st.selectbox("Cámara (opcional)", chamber_options, key="reg_chamber")
            submit_reg = st.form_submit_button("Crear cuenta")
        if submit_reg:
            if not r_email or not r_pass or not r_name or not r_company:
                st.error("Completá email, contraseña, nombre y empresa.")
            else:
                try:
                    chamber_id = None
                    if chamber_pick != "(Sin cámara por ahora)":
                        idx = chamber_options.index(chamber_pick) - 1
                        chamber_id = chambers[idx]["id"]
                    create_user(r_email, r_pass, r_name, r_company, r_phone, chamber_id, role="user")
                    st.success("Cuenta creada. Ahora iniciá sesión.")
                except Exception as e:
                    st.error(f"No se pudo registrar: {e}")
    st.stop()

user = st.session_state.user
role = user["role"]

# Sidebar
st.sidebar.write(f"**Usuario:** {user['name']}")
st.sidebar.write(f"**Empresa:** {user['company']}")
st.sidebar.write(f"**Rol:** {role}")
if st.sidebar.button("Cerrar sesión"):
    logout()

tabs = ["Navegar", "Publicar", "Bandeja", "Panel"]
if role == "admin":
    tabs.append("Administración")
if role == "chamber_admin":
    tabs.append("Gestión Cámara")

t = st.tabs(tabs)

# Navegar
with t[0]:
    st.subheader("Navegar requerimientos")
    chambers = svc.list_chambers()
    chamber_map = {"(Todas)": None}
    for c in chambers:
        chamber_map[chamber_label(c)] = c["id"]
    colf1, colf2, colf3, colf4 = st.columns([2,1,1,1])
    with colf1:
        q = st.text_input("Buscar (producto/keyword/empresa/persona/tags)", "")
    with colf2:
        req_type = st.selectbox("Tipo", ["(Todos)", "OFERTA", "NECESIDAD"])
    with colf3:
        status = st.selectbox("Estado", ["open", "closed"])
    with colf4:
        chamber_pick = st.selectbox("Cámara", list(chamber_map.keys()))

    f = {"q": q, "status": status}
    if req_type == "OFERTA":
        f["req_type"] = "offer"
    elif req_type == "NECESIDAD":
        f["req_type"] = "need"
    if chamber_map[chamber_pick] is not None:
        f["chamber_id"] = chamber_map[chamber_pick]

    rows = svc.list_requirements(f)
    if not rows:
        st.info("No hay requerimientos con esos filtros.")
    else:
        df = pd.DataFrame([dict(r) for r in rows])
        show_cols = ["id","req_type","title","company","chamber_name","location","category","urgency","status","created_at"]
        df = df[show_cols].rename(columns={
            "req_type":"tipo",
            "title":"título",
            "company":"empresa",
            "chamber_name":"cámara",
            "location":"ubicación",
            "category":"categoría",
            "urgency":"urgencia",
            "created_at":"creado",
        })
        st.dataframe(df, use_container_width=True, hide_index=True)

        st.divider()
        pick = st.number_input("Ver detalle por ID", min_value=int(df["id"].min()), max_value=int(df["id"].max()), step=1)
        chosen = None
        for r in rows:
            if r["id"] == pick:
                chosen = r
                break
        if chosen:
            st.markdown(f"### {chosen['title']}")
            st.write(f"**Tipo:** {'OFERTA' if chosen['req_type']=='offer' else 'NECESIDAD'}")
            st.write(f"**Empresa:** {chosen['company']}")
            st.write(f"**Cámara:** {chosen['chamber_name'] or '(Sin cámara)'}")
            st.write(f"**Ubicación:** {chosen['location'] or '-'} | **Categoría:** {chosen['category'] or '-'} | **Urgencia:** {chosen['urgency'] or '-'}")
            st.write(f"**Estado:** {chosen['status']} | **Creado:** {chosen['created_at']}")
            st.write("**Descripción:**")
            st.write(chosen["description"])
            if chosen.get("tags"):
                st.write(f"**Tags:** {chosen['tags']}")

            # Matching inteligente: buscar del tipo opuesto
            opposite = "need" if chosen["req_type"]=="offer" else "offer"
            candidates = [r for r in svc.list_requirements({"status":"open","req_type":opposite}) if r["id"] != chosen["id"]]
            matches = top_matches(chosen, candidates, top_k=5)
            st.subheader("Sugerencias (matching inteligente)")
            if not matches:
                st.info("Sin sugerencias por el momento.")
            else:
                for mr, score in matches:
                    st.write(f"- **{mr['title']}** ({'NECESIDAD' if mr['req_type']=='need' else 'OFERTA'}) – {mr['company']} | score={score:.2f}")

            # Contact workflow
            st.subheader("Contacto (se habilita con aceptación)")
            if chosen["user_id"] == user["id"]:
                st.info("Este requerimiento es tuyo.")
                if chosen["status"] == "open" and st.button("Cerrar requerimiento"):
                    svc.close_requirement(user["id"], chosen["id"])
                    st.success("Requerimiento cerrado.")
                    st.rerun()
            else:
                can_view = svc.can_view_contact(user["id"], chosen["user_id"], chosen["id"])
                if can_view:
                    st.success("Contacto habilitado.")
                    st.write(f"**Nombre:** {chosen['user_name']}")
                    st.write(f"**Email:** {chosen['email']}")
                    st.write(f"**Teléfono:** {chosen['phone'] or '-'}")
                else:
                    if st.button("Solicitar contacto"):
                        ok, msg = svc.create_contact_request(user["id"], user["id"], chosen["user_id"], chosen["id"])
                        if ok:
                            st.success(msg)
                        else:
                            st.warning(msg)

# Publicar
with t[1]:
    st.subheader("Publicar requerimiento")
    chambers = svc.list_chambers()
    chamber_map = {"(Mi cámara actual)": user.get("chamber_id")}
    for c in chambers:
        chamber_map[chamber_label(c)] = c["id"]
    with st.form("new_req"):
        tipo = st.selectbox("Tipo", ["OFERTA (tengo / puedo proveer)", "NECESIDAD (busco / necesito)"])
        title = st.text_input("Título (corto y claro)")
        description = st.text_area("Descripción (sin precios; incluí especificaciones, plazos, etc.)", height=140)
        tags = st.text_input("Tags (separadas por coma)", "")
        category = st.text_input("Categoría (opcional)", "")
        location = st.text_input("Ubicación (ciudad/provincia)", "")
        urgency = st.selectbox("Urgencia", ["Baja", "Media", "Alta", "Crítica"])
        chamber_pick = st.selectbox("Cámara asociada al requerimiento", list(chamber_map.keys()))
        submit = st.form_submit_button("Publicar")
    if submit:
        if not title or not description:
            st.error("Completá título y descripción.")
        else:
            req_type = "offer" if tipo.startswith("OFERTA") else "need"
            chamber_id = chamber_map[chamber_pick]
            svc.create_requirement(user["id"], user["id"], chamber_id, req_type, title, description, tags, category, location, urgency)
            st.success("Publicado.")
            st.rerun()

# Bandeja
with t[2]:
    st.subheader("Bandeja de solicitudes de contacto")
    colA, colB = st.columns(2)
    with colA:
        st.markdown("#### Recibidas")
        inbox = svc.list_inbox(user["id"])
        if not inbox:
            st.info("No tenés solicitudes recibidas.")
        else:
            for r in inbox:
                st.write(f"**#{r['id']}** – {r['from_company']} / {r['from_name']} | Req: {r['req_title']} | Estado: {r['status']}")
                if r["status"] == "pending":
                    c1, c2 = st.columns(2)
                    with c1:
                        if st.button(f"Aceptar #{r['id']}", key=f"acc_{r['id']}"):
                            svc.respond_contact_request(user["id"], r["id"], "accepted")
                            st.success("Aceptada. El contacto queda habilitado.")
                            st.rerun()
                    with c2:
                        if st.button(f"Rechazar #{r['id']}", key=f"dec_{r['id']}"):
                            svc.respond_contact_request(user["id"], r["id"], "declined")
                            st.warning("Rechazada.")
                            st.rerun()
    with colB:
        st.markdown("#### Enviadas")
        sent = svc.list_sent(user["id"])
        if not sent:
            st.info("No enviaste solicitudes.")
        else:
            for r in sent:
                st.write(f"**#{r['id']}** – a {r['to_company']} / {r['to_name']} | Req: {r['req_title']} | Estado: {r['status']}")

# Panel
with t[3]:
    st.subheader("Panel de control")
    m = svc.admin_metrics()
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Usuarios", m["users_total"])
    col2.metric("Requerimientos", m["req_total"])
    col3.metric("Abiertos", m["req_open"])
    col4.metric("Contactos aceptados", m["contact_accepted"])

    st.markdown("### Requerimientos por cámara")
    df = pd.DataFrame([dict(r) for r in m["by_chamber"]])
    if not df.empty:
        st.dataframe(df.rename(columns={"chamber":"cámara","n":"cantidad"}), use_container_width=True, hide_index=True)

# Administración
if "Administración" in tabs:
    with t[tabs.index("Administración")]:
        st.subheader("Administración (solo Admin)")
        if role != "admin":
            st.error("Acceso denegado.")
        else:
            st.markdown("### Cámaras")
            chambers = svc.list_chambers()
            if chambers:
                st.dataframe(pd.DataFrame([dict(c) for c in chambers]), use_container_width=True, hide_index=True)
            with st.form("add_chamber"):
                name = st.text_input("Nombre de cámara")
                province = st.text_input("Provincia (opcional)")
                city = st.text_input("Ciudad (opcional)")
                ok = st.form_submit_button("Crear cámara")
            if ok:
                if not name:
                    st.error("Nombre requerido.")
                else:
                    svc.create_chamber(user["id"], name, province, city)
                    st.success("Cámara creada.")
                    st.rerun()

            st.divider()
            st.markdown("### Usuarios")
            # Simple user list
            from db import conn
            c = conn()
            users = c.execute("""
                SELECT u.*, COALESCE(ch.name,'(Sin cámara)') as chamber_name
                FROM users u
                LEFT JOIN chambers ch ON ch.id = u.chamber_id
                ORDER BY u.created_at DESC
            """).fetchall()
            c.close()
            udf = pd.DataFrame([dict(u) for u in users])
            st.dataframe(udf[["id","email","name","company","role","is_active","chamber_name","created_at"]], use_container_width=True, hide_index=True)

            st.markdown("#### Cambiar rol / cámara / estado")
            colA, colB, colC = st.columns(3)
            with colA:
                uid = st.number_input("User ID", min_value=1, step=1)
            with colB:
                new_role = st.selectbox("Rol", ["user","chamber_admin","admin"])
            with colC:
                active = st.selectbox("Activo", ["Sí","No"])
            chambers = svc.list_chambers()
            chamber_opts = ["(Sin cámara)"] + [chamber_label(ch) for ch in chambers]
            chamber_pick = st.selectbox("Asignar cámara", chamber_opts)
            if st.button("Aplicar cambios"):
                if chamber_pick == "(Sin cámara)":
                    chamber_id = None
                else:
                    chamber_id = chambers[chamber_opts.index(chamber_pick)-1]["id"]
                svc.update_user_role(user["id"], int(uid), new_role)
                svc.update_user_chamber(user["id"], int(uid), chamber_id)
                svc.deactivate_user(user["id"], int(uid), is_active=(active=="Sí"))
                st.success("Actualizado.")
                st.rerun()

# Gestión Cámara
if "Gestión Cámara" in tabs:
    with t[tabs.index("Gestión Cámara")]:
        st.subheader("Gestión de Cámara (Chamber Admin)")
        if role != "chamber_admin":
            st.error("Acceso denegado.")
        else:
            st.write("Gestión básica: usuarios y requerimientos de tu cámara.")
            my_ch = user.get("chamber_id")
            if not my_ch:
                st.warning("No tenés cámara asignada. Pedí al Admin que te asigne una cámara.")
            else:
                from db import conn
                c = conn()
                users = c.execute("""
                    SELECT u.*, COALESCE(ch.name,'(Sin cámara)') as chamber_name
                    FROM users u
                    LEFT JOIN chambers ch ON ch.id = u.chamber_id
                    WHERE u.chamber_id = ?
                    ORDER BY u.created_at DESC
                """, (my_ch,)).fetchall()
                c.close()
                udf = pd.DataFrame([dict(u) for u in users])
                st.dataframe(udf[["id","email","name","company","role","is_active","created_at"]], use_container_width=True, hide_index=True)
                st.markdown("### Requerimientos de la cámara")
                reqs = svc.list_requirements({"status":"open","chamber_id":my_ch})
                if reqs:
                    st.dataframe(pd.DataFrame([dict(r) for r in reqs])[["id","req_type","title","company","created_at","status"]],
                                 use_container_width=True, hide_index=True)
                else:
                    st.info("No hay requerimientos abiertos en tu cámara.")
