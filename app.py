from flask import Flask, request, send_file, render_template, jsonify
import pandas as pd
import plotly.express as px
from weasyprint import HTML
import io
import logging
import os
from datetime import datetime
import tempfile
import gc  # For memory management on Pi
from config import get_config

# Get configuration
config_class = get_config()
config_instance = config_class()

# Configure logging
logging.basicConfig(
    level=getattr(logging, config_instance.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config.from_object(config_instance)

# Use configurable school palette
school_palette = config_instance.SCHOOL_PALETTE

@app.route("/health")
def health_check():
    """Health check endpoint for container monitoring"""
    return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()})

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        try:
            logger.info("Processing CSV upload request")
            files = request.files.getlist("csvfile")
            
            if not files or files[0].filename == '':
                logger.warning("No files provided")
                return "No files provided", 400
            
            # Validate file types
            for file in files:
                if not file.filename.lower().endswith('.csv'):
                    logger.warning(f"Invalid file type: {file.filename}")
                    return f"Invalid file type: {file.filename}. Only CSV files are allowed.", 400
            
            # Read and validate CSV files
            dfs = []
            for file in files:
                try:
                    df = pd.read_csv(file)
                    if df.empty:
                        logger.warning(f"Empty CSV file: {file.filename}")
                        return f"Empty CSV file: {file.filename}", 400
                    dfs.append(df)
                except Exception as e:
                    logger.error(f"Error reading CSV file {file.filename}: {str(e)}")
                    return f"Error reading CSV file {file.filename}: {str(e)}", 400
            
            df = pd.concat(dfs, ignore_index=True)
            logger.info(f"Successfully loaded {len(df)} rows from {len(files)} files")

            required = {"Name", "Steps", "Demerits", "Attendance"}
            if not required.issubset(df.columns):
                missing_cols = required - set(df.columns)
                logger.error(f"Missing required columns: {missing_cols}")
                return f"Missing required columns: {missing_cols}", 400

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

            # Merge into one PDF with memory optimization for Pi
            logger.info("Generating PDF report")
            pdf_bytes = b"".join(part.write_pdf() for part in pdf_parts)
            
            # Force garbage collection to free memory (important for Pi)
            del pdf_parts, df, dfs
            gc.collect()
            
            logger.info(f"PDF generated successfully, size: {len(pdf_bytes)} bytes")
            
            return send_file(
                io.BytesIO(pdf_bytes),
                mimetype="application/pdf",
                as_attachment=True,
                download_name=f"progress_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            )
            
        except Exception as e:
            logger.error(f"Error processing request: {str(e)}")
            return f"Error processing request: {str(e)}", 500

    return '''
    <h1>Upload Weekly CSV(s)</h1>
    <form method="post" enctype="multipart/form-data">
        <input type="file" name="csvfile" accept=".csv" multiple required>
        <button type="submit">Generate Report</button>
    </form>
    '''

@app.errorhandler(413)
def too_large(e):
    logger.warning("File too large uploaded")
    return "File is too large (max 16MB)", 413

@app.errorhandler(500)
def internal_error(e):
    logger.error(f"Internal server error: {str(e)}")
    return "Internal server error. Please check your CSV format and try again.", 500

if __name__ == "__main__":
    logger.info(f"Starting application on {config_instance.HOST}:{config_instance.PORT}")
    logger.info(f"Debug mode: {config_instance.DEBUG}")
    logger.info(f"Max file size: {config_instance.MAX_CONTENT_LENGTH / (1024*1024):.1f}MB")
    logger.info(f"School: {config_instance.SCHOOL_NAME}")
    
    app.run(
        host=config_instance.HOST, 
        port=config_instance.PORT, 
        debug=config_instance.DEBUG
    )