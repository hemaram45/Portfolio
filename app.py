from flask import Flask, render_template, request, redirect, session
import sqlite3

app = Flask(__name__)
app.secret_key = "secret123"

# ---------------- DATABASE SETUP ----------------
def init_db():
    conn = sqlite3.connect("database.db")
    cur = conn.cursor()

    # contacts table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS contacts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        email TEXT UNIQUE,
        message TEXT,
        reply TEXT,
        status TEXT DEFAULT 'unread'
    )
    """)

    # chats table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS chats (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        contact_id INTEGER,
        sender TEXT,
        message TEXT
    )
    """)

    conn.commit()
    conn.close()

init_db()

# ---------------- HOME ----------------
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/projects")
def projects():
    return render_template("projects.html")

@app.route("/contact")
def contact():
    return render_template("contact.html")

# ---------------- SUBMIT ----------------
@app.route("/submit", methods=["POST"])
def submit():
    name = request.form.get("name")
    email = request.form.get("email")
    message = request.form.get("message")

    conn = sqlite3.connect("database.db")
    cur = conn.cursor()

    # check existing user
    cur.execute("SELECT id FROM contacts WHERE email=?", (email,))
    existing = cur.fetchone()

    if existing:
        contact_id = existing[0]

        # mark unread again
        cur.execute("UPDATE contacts SET status='unread' WHERE id=?", (contact_id,))
    else:
        cur.execute("INSERT INTO contacts (name,email,message,status) VALUES (?,?,?,?)",
                    (name, email, message, "unread"))
        contact_id = cur.lastrowid

    # save chat message
    cur.execute("INSERT INTO chats (contact_id, sender, message) VALUES (?, ?, ?)",
                (contact_id, "user", message))

    conn.commit()
    conn.close()

    return redirect("/contact")

# ---------------- LOGIN ----------------
@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if username == "hemaram" and password == "hemu45":
            session["admin"] = True
            return redirect("/admin")

    return render_template("login.html")

# ---------------- ADMIN ----------------
@app.route("/admin")
def admin():
    if not session.get("admin"):
        return redirect("/login")

    search = request.args.get("search", "")

    conn = sqlite3.connect("database.db")
    cur = conn.cursor()

    if search:
        cur.execute("""
            SELECT * FROM contacts 
            WHERE name LIKE ? OR email LIKE ?
        """, ('%'+search+'%', '%'+search+'%'))
    else:
        cur.execute("SELECT * FROM contacts")

    data = cur.fetchall()

    # counts
    cur.execute("SELECT COUNT(*) FROM contacts")
    total_users = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM contacts WHERE status='unread'")
    unread_count = cur.fetchone()[0]

    conn.close()

    return render_template("admin.html",
                           data=data,
                           total_users=total_users,
                           total_messages=total_users,
                           today_messages=0,
                           unread_count=unread_count)

# ---------------- GRAPH (🔥 FIXED) ----------------
@app.route("/graph")
def graph():
    conn = sqlite3.connect("database.db")
    cur = conn.cursor()

    # 🔥 correct query (chats table)
    cur.execute("""
        SELECT contacts.name, COUNT(chats.id)
        FROM chats
        JOIN contacts ON contacts.id = chats.contact_id
        GROUP BY contacts.name
    """)

    data = cur.fetchall()
    conn.close()

    names = [row[0] for row in data]
    counts = [row[1] for row in data]

    return render_template("graph.html", names=names, counts=counts)

# ---------------- REPLY ----------------
@app.route("/reply/<int:id>", methods=["GET", "POST"])
def reply(id):
    conn = sqlite3.connect("database.db")
    cur = conn.cursor()

    # mark as read
    cur.execute("UPDATE contacts SET status='read' WHERE id=?", (id,))
    conn.commit()

    if request.method == "POST":
        reply_msg = request.form.get("reply")

        cur.execute("INSERT INTO chats (contact_id, sender, message) VALUES (?, ?, ?)",
                    (id, "admin", reply_msg))

        conn.commit()
        conn.close()

        return redirect("/reply/" + str(id))

    # contact data
    cur.execute("SELECT * FROM contacts WHERE id=?", (id,))
    data = cur.fetchone()

    # chat history
    cur.execute("SELECT sender, message FROM chats WHERE contact_id=?", (id,))
    chats = cur.fetchall()

    conn.close()

    return render_template("reply.html", data=data, chats=chats)

# ---------------- REMOVE ----------------
@app.route("/remove/<int:id>")
def remove(id):
    if not session.get("admin"):
        return redirect("/login")

    conn = sqlite3.connect("database.db")
    cur = conn.cursor()

    cur.execute("DELETE FROM contacts WHERE id=?", (id,))
    cur.execute("DELETE FROM chats WHERE contact_id=?", (id,))

    conn.commit()
    conn.close()

    return redirect("/admin")

# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.pop("admin", None)
    return redirect("/")

if __name__ == "__main__":
    app.run(debug=True)