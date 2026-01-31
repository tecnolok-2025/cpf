from db import conn, now_iso, log

def list_chambers():
    c = conn()
    rows = c.execute("SELECT * FROM chambers ORDER BY name").fetchall()
    c.close()
    return rows

def create_chamber(actor_user_id, name, province, city):
    c = conn()
    c.execute(
        "INSERT INTO chambers(name, province, city, created_at) VALUES(?,?,?,?)",
        (name.strip(), (province or "").strip(), (city or "").strip(), now_iso())
    )
    c.commit()
    c.close()
    log(actor_user_id, "chamber_created", name)

def update_user_role(actor_user_id, user_id, role):
    c = conn()
    c.execute("UPDATE users SET role=? WHERE id=?", (role, user_id))
    c.commit()
    c.close()
    log(actor_user_id, "role_updated", f"user_id={user_id}, role={role}")

def update_user_chamber(actor_user_id, user_id, chamber_id):
    c = conn()
    c.execute("UPDATE users SET chamber_id=? WHERE id=?", (chamber_id, user_id))
    c.commit()
    c.close()
    log(actor_user_id, "user_chamber_updated", f"user_id={user_id}, chamber_id={chamber_id}")

def deactivate_user(actor_user_id, user_id, is_active):
    c = conn()
    c.execute("UPDATE users SET is_active=? WHERE id=?", (1 if is_active else 0, user_id))
    c.commit()
    c.close()
    log(actor_user_id, "user_activation_updated", f"user_id={user_id}, active={is_active}")

def create_requirement(actor_user_id, user_id, chamber_id, req_type, title, description, tags, category, location, urgency):
    c = conn()
    c.execute(
        """INSERT INTO requirements(user_id, chamber_id, req_type, title, description, tags, category, location, urgency, status, created_at, updated_at)
             VALUES(?,?,?,?,?,?,?,?,?,'open',?,?)""",
        (user_id, chamber_id, req_type, title.strip(), description.strip(), (tags or "").strip(), (category or "").strip(),
         (location or "").strip(), (urgency or "").strip(), now_iso(), now_iso())
    )
    c.commit()
    c.close()
    log(actor_user_id, "requirement_created", f"type={req_type}, title={title[:80]}")

def list_requirements(filters=None):
    filters = filters or {}
    where = ["1=1"]
    params = []
    if filters.get("status"):
        where.append("r.status = ?")
        params.append(filters["status"])
    if filters.get("req_type"):
        where.append("r.req_type = ?")
        params.append(filters["req_type"])
    if filters.get("chamber_id"):
        where.append("r.chamber_id = ?")
        params.append(filters["chamber_id"])
    if filters.get("q"):
        q = f"%{filters['q'].strip()}%"
        where.append("(r.title LIKE ? OR r.description LIKE ? OR r.tags LIKE ? OR u.company LIKE ? OR u.name LIKE ?)")
        params.extend([q, q, q, q, q])
    if filters.get("category"):
        where.append("r.category = ?")
        params.append(filters["category"])
    if filters.get("location"):
        where.append("r.location = ?")
        params.append(filters["location"])

    sql = f"""
        SELECT r.*, u.name as user_name, u.company as company, u.email as email, u.phone as phone,
               c.name as chamber_name, c.province as chamber_province, c.city as chamber_city
        FROM requirements r
        JOIN users u ON u.id = r.user_id
        LEFT JOIN chambers c ON c.id = r.chamber_id
        WHERE {' AND '.join(where)}
        ORDER BY r.created_at DESC
    """
    c = conn()
    rows = c.execute(sql, params).fetchall()
    c.close()
    return rows

def close_requirement(actor_user_id, req_id):
    c = conn()
    c.execute("UPDATE requirements SET status='closed', updated_at=? WHERE id=?", (now_iso(), req_id))
    c.commit()
    c.close()
    log(actor_user_id, "requirement_closed", f"id={req_id}")

def create_contact_request(actor_user_id, from_user_id, to_user_id, requirement_id):
    c = conn()
    existing = c.execute(
        "SELECT * FROM contact_requests WHERE from_user_id=? AND requirement_id=? AND status='pending'",
        (from_user_id, requirement_id)
    ).fetchone()
    if existing:
        c.close()
        return False, "Ya existe una solicitud pendiente para este requerimiento."

    c.execute(
        "INSERT INTO contact_requests(from_user_id, to_user_id, requirement_id, status, created_at) VALUES(?,?,?,?,?)",
        (from_user_id, to_user_id, requirement_id, "pending", now_iso())
    )
    c.commit()
    c.close()
    log(actor_user_id, "contact_request_created", f"req_id={requirement_id}, from={from_user_id}, to={to_user_id}")
    return True, "Solicitud enviada. Queda pendiente de aprobación."

def list_inbox(user_id):
    c = conn()
    rows = c.execute(
        """
        SELECT cr.*, r.title as req_title, r.req_type as req_type,
               uf.name as from_name, uf.company as from_company, uf.email as from_email, uf.phone as from_phone
        FROM contact_requests cr
        JOIN requirements r ON r.id = cr.requirement_id
        JOIN users uf ON uf.id = cr.from_user_id
        WHERE cr.to_user_id = ?
        ORDER BY cr.created_at DESC
        """,
        (user_id,)
    ).fetchall()
    c.close()
    return rows

def list_sent(user_id):
    c = conn()
    rows = c.execute(
        """
        SELECT cr.*, r.title as req_title, r.req_type as req_type,
               ut.name as to_name, ut.company as to_company
        FROM contact_requests cr
        JOIN requirements r ON r.id = cr.requirement_id
        JOIN users ut ON ut.id = cr.to_user_id
        WHERE cr.from_user_id = ?
        ORDER BY cr.created_at DESC
        """,
        (user_id,)
    ).fetchall()
    c.close()
    return rows

def respond_contact_request(actor_user_id, request_id, decision):
    assert decision in ("accepted", "declined")
    c = conn()
    c.execute(
        "UPDATE contact_requests SET status=?, responded_at=? WHERE id=?",
        (decision, now_iso(), request_id)
    )
    c.commit()
    c.close()
    log(actor_user_id, "contact_request_responded", f"id={request_id}, decision={decision}")

def can_view_contact(user_id, other_user_id, requirement_id):
    # Contacto visible si existe una solicitud accepted entre ambas partes para ese requerimiento
    c = conn()
    row = c.execute(
        """
        SELECT 1 FROM contact_requests
        WHERE requirement_id=?
          AND status='accepted'
          AND ((from_user_id=? AND to_user_id=?) OR (from_user_id=? AND to_user_id=?))
        LIMIT 1
        """,
        (requirement_id, user_id, other_user_id, other_user_id, user_id)
    ).fetchone()
    c.close()
    return row is not None

def admin_metrics():
    c = conn()
    out = {}
    out["users_total"] = c.execute("SELECT COUNT(*) as n FROM users").fetchone()["n"]
    out["req_total"] = c.execute("SELECT COUNT(*) as n FROM requirements").fetchone()["n"]
    out["req_open"] = c.execute("SELECT COUNT(*) as n FROM requirements WHERE status='open'").fetchone()["n"]
    out["req_closed"] = c.execute("SELECT COUNT(*) as n FROM requirements WHERE status='closed'").fetchone()["n"]
    out["contact_pending"] = c.execute("SELECT COUNT(*) as n FROM contact_requests WHERE status='pending'").fetchone()["n"]
    out["contact_accepted"] = c.execute("SELECT COUNT(*) as n FROM contact_requests WHERE status='accepted'").fetchone()["n"]
    out["by_chamber"] = c.execute("""
        SELECT COALESCE(c.name,'(Sin cámara)') as chamber, COUNT(r.id) as n
        FROM requirements r
        LEFT JOIN chambers c ON c.id = r.chamber_id
        GROUP BY chamber
        ORDER BY n DESC
    """).fetchall()
    c.close()
    return out
