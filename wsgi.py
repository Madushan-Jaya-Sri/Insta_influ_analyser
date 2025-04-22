from run import create_app

app = create_app()

if __name__ == "__main__":
    # This part is typically not used by Gunicorn but good for direct execution if needed
    app.run() 