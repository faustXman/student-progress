from flask import Flask, request, send_file, render_template
import pandas as pd
import plotly.express as px
from weasyprint import HTML
import io

app = Flask(__name__)

school_palette = ["#002147", "#6AB023", "#4F81BD"]

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        files = request.files.getlist("csvfile")
        dfs = [pd.read_csv(f) for f in files]
        df = pd.concat(dfs, ignore_index=True)

        required = {"Name", "Steps", "Demerits", "Attendance"}
        if not required.issubset(df.columns):
            return f"Missing required columns: {required - set(df.columns)}", 400

        if "Week" in df.columns:
            df["Week"] = pd.to_datetime(df["Week"], errors="coerce")
            df = df.sort_values(["Name", "Week"])

        # Class-level charts
        fig_steps = px.histogram(df, x="Steps", nbins=10,
                                 color_discrete_sequence=[school_palette[0]])
        fig_steps.update_traces(mode="lines+markers")
        steps_html = fig_steps.to_html(full_html=False, include_plotlyjs="cdn")

        fig_demerits = px.histogram(df, x="Demerits", nbins=10,
                                    color_discrete_sequence=[school_palette[1]])
        fig_demerits.update_traces(mode="lines+markers")
        demerits_html = fig_demerits.to_html(full_html=False, include_plotlyjs=False)

        attendance_html = ""
        if "Week" in df.columns:
            fig_att = px.line(df, x="Week", y="Attendance", color="Name",
                              markers=True, color_discrete_sequence=school_palette)
            attendance_html = fig_att.to_html(full_html=False, include_plotlyjs=False)

        # Overlay polygons
        overlay_html = ""
        if "Week" in df.columns and df["Week"].nunique() > 1:
            latest_week = df["Week"].max()
            prev_week = sorted(df["Week"].unique())[-2]
            fig_overlay = px.histogram(df[df["Week"] == latest_week], x="Steps", nbins=10,
                                       opacity=0.5, color_discrete_sequence=[school_palette[0]])
            fig_overlay.add_histogram(x=df[df["Week"] == prev_week]["Steps"], nbins=10,
                                      opacity=0.5, marker_color=school_palette[1])
            overlay_html = fig_overlay.to_html(full_html=False, include_plotlyjs=False)

        # Render class report
        html_report = render_template(
            "report.html",
            table=df.to_html(index=False),
            chart_steps=steps_html,
            chart_demerits=demerits_html,
            chart_attendance=attendance_html,
            chart_overlay=overlay_html
        )

        # Build PDF parts
        pdf_parts = [HTML(string=html_report).render()]

        # Per-student pages
        for student in df["Name"].unique():
            sdata = df[df["Name"] == student]
            fig_s_steps = px.line(sdata, x="Week", y="Steps", markers=True,
                                  title=f"{student} - Steps",
                                  color_discrete_sequence=[school_palette[0]])
            fig_s_demerits = px.line(sdata, x="Week", y="Demerits", markers=True,
                                     title=f"{student} - Demerits",
                                     color_discrete_sequence=[school_palette[1]])
            fig_s_att = px.line(sdata, x="Week", y="Attendance", markers=True,
                                title=f"{student} - Attendance",
                                color_discrete_sequence=[school_palette[2]])

            student_html = render_template(
                "student_page.html",
                name=student,
                chart_steps=fig_s_steps.to_html(full_html=False, include_plotlyjs=False),
                chart_demerits=fig_s_demerits.to_html(full_html=False, include_plotlyjs=False),
                chart_attendance=fig_s_att.to_html(full_html=False, include_plotlyjs=False)
            )
            pdf_parts.append(HTML(string=student_html).render())

        # Merge into one PDF
        pdf_bytes = b"".join(part.write_pdf() for part in pdf_parts)

        return send_file(
            io.BytesIO(pdf_bytes),
            mimetype="application/pdf",
            as_attachment=True,
            download_name="progress_report.pdf"
        )

    return '''
    <h1>Upload Weekly CSV(s)</h1>
    <form method="post" enctype="multipart/form-data">
        <input type="file" name="csvfile" accept=".csv" multiple required>
        <button type="submit">Generate Report</button>
    </form>
    '''

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)