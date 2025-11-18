from flask import Flask, render_template, request, send_file, redirect, url_for, flash
import numpy as np
import sympy as sp
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io, base64

app = Flask(__name__)
app.secret_key = "secret123"   # Needed for flash messages

# Store last plot in memory
last_plot_bytes = None


@app.route('/')
def index():
    return render_template("index.html")


@app.route('/plot')
def plot():
    global last_plot_bytes

    mode = request.args.get("mode")
    xmin = request.args.get("xmin")
    xmax = request.args.get("xmax")
    points = request.args.get("points")

    # Default safe values
    xmin = float(xmin) if xmin else -10
    xmax = float(xmax) if xmax else 10
    points = int(points) if points else 1000

    xs = np.linspace(xmin, xmax, points)

    # Prepare figure
    fig, ax = plt.subplots(figsize=(6, 4), dpi=120)

    try:
        if mode == "function":
            expr_x = request.args.get("expr_x")
            x = sp.symbols("x")
            expr = sp.sympify(expr_x)
            f = sp.lambdify(x, expr, "numpy")
            ys = f(xs)
            ax.plot(xs, ys, linewidth=2)

        elif mode == "parametric":
            expr_x = request.args.get("expr_x")
            expr_y = request.args.get("expr_y")
            t = sp.symbols("t")
            xt = sp.lambdify(t, sp.sympify(expr_x), "numpy")
            yt = sp.lambdify(t, sp.sympify(expr_y), "numpy")
            ts = xs
            ax.plot(xt(ts), yt(ts), linewidth=2)

        elif mode == "polar":
            expr_r = request.args.get("expr_r")
            theta = np.linspace(0, 2*np.pi, points)
            r = sp.lambdify(sp.symbols("t"), sp.sympify(expr_r), "numpy")
            r_vals = r(theta)
            ax = plt.subplot(111, projection='polar')
            ax.plot(theta, r_vals, linewidth=2)

        else:
            flash("Invalid mode selected.")
            return redirect(url_for("index"))

    except Exception as e:
        flash("Error in expression: " + str(e))
        return redirect(url_for("index"))

    ax.grid(True)

    # Save plot to memory
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight")
    buf.seek(0)

    last_plot_bytes = buf.getvalue()  # store raw PNG bytes

    # Convert to base64 for HTML display
    img_b64 = base64.b64encode(last_plot_bytes).decode("ascii")

    return render_template("index.html", plot_b64=img_b64)


@app.route('/download')
def download():
    global last_plot_bytes

    if last_plot_bytes is None:
        flash("No plot available to download.")
        return redirect(url_for("index"))

    return send_file(
        io.BytesIO(last_plot_bytes),
        mimetype="image/png",
        as_attachment=True,
        download_name="plot.png"
    )


if __name__ == "__main__":
    app.run(debug=True)