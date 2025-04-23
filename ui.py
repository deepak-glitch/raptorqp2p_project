from flask import Flask, render_template, request, redirect, url_for
import os, subprocess

app = Flask(__name__)
os.makedirs("seeds", exist_ok=True)
os.makedirs("downloads", exist_ok=True)

@app.route("/", methods=["GET","POST"])
def index():
    if request.method=="POST":
        mode = request.form["mode"]
        if mode=="seed":
            f = request.files["file"]
            path = os.path.join("seeds", f.filename)
            f.save(path)
            subprocess.Popen(["python","torrent_peer.py","--seed", path])
        else:
            info_hash = request.form["info_hash"]
            subprocess.Popen(["python","torrent_peer.py","--leech", info_hash])
        return redirect(url_for("index"))
    return render_template("index.html")

if __name__=="__main__":
    app.run(debug=True)
